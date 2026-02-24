from pathlib import Path
import json

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm

from icd_hybrid.data.chunking import OverlappingWindowChunker


class EndToEndLabelAttention(nn.Module):
    def __init__(
        self,
        n_codes: int,
        model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        projection_dim: int = 256,
        dropout: float = 0.1,
        freeze_layers: int = 8,
        gradient_checkpointing: bool = True,
    ):
        super().__init__()
        self.n_codes = n_codes
        self.projection_dim = projection_dim
        self.model_name = model_name

        self.bert = AutoModel.from_pretrained(model_name)
        self.projection = nn.Linear(self.bert.config.hidden_size, projection_dim)

        self.code_queries = nn.Parameter(torch.randn(n_codes, projection_dim) * 0.02)
        self.classification_weights = nn.Parameter(torch.randn(n_codes, projection_dim) * 0.02)
        self.attention_dropout = nn.Dropout(dropout)
        self.scale = projection_dim ** 0.5

        if freeze_layers > 0:
            for param in self.bert.embeddings.parameters():
                param.requires_grad = False
            for i in range(min(freeze_layers, len(self.bert.encoder.layer))):
                for param in self.bert.encoder.layer[i].parameters():
                    param.requires_grad = False

        if gradient_checkpointing:
            self.bert.gradient_checkpointing_enable()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        chunk_counts: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        batch_size, max_chunks, seq_len = input_ids.shape

        chunk_mask = (
            torch.arange(max_chunks, device=chunk_counts.device).unsqueeze(0)
            < chunk_counts.unsqueeze(1)
        )

        flat_ids = input_ids.view(-1, seq_len)
        flat_attn = attention_mask.view(-1, seq_len)

        bert_out = self.bert(input_ids=flat_ids, attention_mask=flat_attn)
        hidden = bert_out.last_hidden_state

        mask_exp = flat_attn.unsqueeze(-1).float()
        pooled = (hidden * mask_exp).sum(dim=1) / mask_exp.sum(dim=1).clamp(min=1e-9)

        projected = self.projection(pooled)
        projected = F.normalize(projected, p=2, dim=-1)

        chunk_embeddings = projected.view(batch_size, max_chunks, -1)

        attn_logits = torch.matmul(
            self.code_queries.unsqueeze(0),
            chunk_embeddings.transpose(1, 2),
        ) / self.scale

        mask_expanded = chunk_mask.unsqueeze(1).expand_as(attn_logits)
        attn_logits = attn_logits.masked_fill(~mask_expanded, float('-inf'))
        attn_weights = torch.softmax(attn_logits, dim=-1)
        attn_weights = self.attention_dropout(attn_weights)

        code_repr = torch.matmul(attn_weights, chunk_embeddings)
        logits = (code_repr * self.classification_weights.unsqueeze(0)).sum(dim=-1)

        return logits, attn_weights, chunk_embeddings

    def save(self, path: str, config: dict) -> None:
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state_dict": self.state_dict(),
            "config": config,
        }, save_path / "end_to_end.pt")

    @classmethod
    def load(cls, path: str, device: str = "cuda") -> "EndToEndLabelAttention":
        load_path = Path(path)
        checkpoint = torch.load(
            load_path / "end_to_end.pt",
            map_location=device,
            weights_only=False,
        )
        config = checkpoint["config"]

        model = cls(
            n_codes=config["n_codes"],
            model_name=config["model_name"],
            projection_dim=config["projection_dim"],
            dropout=config.get("dropout", 0.1),
            freeze_layers=config.get("freeze_layers", 8),
            gradient_checkpointing=False,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()
        return model
