from pathlib import Path
from typing import Optional
import json

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


class ChunkEmbeddingDataset(Dataset):
    def __init__(
        self,
        chunks: np.ndarray,
        chunk_counts: np.ndarray,
        labels: np.ndarray,
    ):
        self.chunks = torch.tensor(chunks, dtype=torch.float32)
        self.chunk_counts = torch.tensor(chunk_counts, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.chunks)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.chunks[idx], self.chunk_counts[idx], self.labels[idx]


class LabelAttentionClassifier(nn.Module):
    def __init__(
        self,
        n_codes: int,
        embedding_dim: int = 256,
        dropout: float = 0.1,
        code_description_embeddings: Optional[torch.Tensor] = None,
    ):
        super().__init__()
        self.n_codes = n_codes
        self.embedding_dim = embedding_dim

        if code_description_embeddings is not None:
            self.code_queries = nn.Parameter(code_description_embeddings.clone())
            self.classification_weights = nn.Parameter(code_description_embeddings.clone())
        else:
            self.code_queries = nn.Parameter(
                torch.randn(n_codes, embedding_dim) * 0.02
            )
            self.classification_weights = nn.Parameter(
                torch.randn(n_codes, embedding_dim) * 0.02
            )
        self.dropout = nn.Dropout(dropout)
        self.scale = embedding_dim ** 0.5

    def forward(
        self,
        chunk_embeddings: torch.Tensor,
        chunk_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        attention_logits = torch.matmul(
            self.code_queries.unsqueeze(0),
            chunk_embeddings.transpose(1, 2),
        ) / self.scale

        mask_expanded = chunk_mask.unsqueeze(1).expand_as(attention_logits)
        attention_logits = attention_logits.masked_fill(~mask_expanded, float('-inf'))

        attention_weights = torch.softmax(attention_logits, dim=-1)
        attention_weights = self.dropout(attention_weights)

        code_embeddings = torch.matmul(attention_weights, chunk_embeddings)

        logits = (code_embeddings * self.classification_weights.unsqueeze(0)).sum(dim=-1)

        return logits, attention_weights


class LabelAttentionWrapper:
    def __init__(
        self,
        embedding_dim: int = 256,
        lr: float = 1e-3,
        epochs: int = 80,
        batch_size: int = 64,
        gamma_neg: float = 4.0,
        gamma_pos: float = 0.0,
        clip_margin: float = 0.05,
        dropout: float = 0.1,
        loss_type: str = "asymmetric",
        pu_prior_weight: float = 1.0,
        prior_cap: float = 0.5,
        device: str = "cuda",
    ):
        self.embedding_dim = embedding_dim
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.gamma_neg = gamma_neg
        self.gamma_pos = gamma_pos
        self.clip_margin = clip_margin
        self.dropout = dropout
        self.loss_type = loss_type
        self.pu_prior_weight = pu_prior_weight
        self.prior_cap = prior_cap
        self.device = device
        self.model = None
        self.code_names = None
        self.n_codes = 0

    def _build_mask(self, chunk_counts: torch.Tensor, max_chunks: int) -> torch.Tensor:
        return torch.arange(max_chunks, device=chunk_counts.device).unsqueeze(0) < chunk_counts.unsqueeze(1)

    def _predict_scores_np(self, chunks: np.ndarray, chunk_counts: np.ndarray) -> np.ndarray:
        self.model.eval()
        max_chunks = chunks.shape[1]
        all_scores = []

        dataset = ChunkEmbeddingDataset(
            chunks, chunk_counts, np.zeros((len(chunks), self.n_codes), dtype=np.float32)
        )
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False, num_workers=2, pin_memory=True)

        with torch.no_grad():
            for batch_chunks, batch_counts, _ in loader:
                batch_chunks = batch_chunks.to(self.device)
                batch_counts = batch_counts.to(self.device)
                mask = self._build_mask(batch_counts, max_chunks)
                logits, _ = self.model(batch_chunks, mask)
                probs = torch.sigmoid(logits)
                all_scores.append(probs.cpu().numpy())

        return np.vstack(all_scores)

    def predict_scores_batch(
        self,
        chunks: np.ndarray,
        chunk_counts: np.ndarray,
        code_list: list[str],
    ) -> np.ndarray:
        all_scores = self._predict_scores_np(chunks, chunk_counts)

        if code_list == self.code_names:
            return all_scores

        code_to_idx = {c: i for i, c in enumerate(self.code_names)}
        result = np.zeros((len(chunks), len(code_list)), dtype=np.float32)
        for i, code in enumerate(code_list):
            if code in code_to_idx:
                result[:, i] = all_scores[:, code_to_idx[code]]
        return result

    def predict_attention_weights(
        self,
        chunks: np.ndarray,
        chunk_counts: np.ndarray,
    ) -> np.ndarray:
        self.model.eval()
        max_chunks = chunks.shape[1]
        all_weights = []

        with torch.no_grad():
            for i in range(0, len(chunks), self.batch_size):
                batch_chunks = torch.tensor(
                    chunks[i:i + self.batch_size], dtype=torch.float32
                ).to(self.device)
                batch_counts = torch.tensor(
                    chunk_counts[i:i + self.batch_size], dtype=torch.long
                ).to(self.device)
                mask = self._build_mask(batch_counts, max_chunks)
                _, attn_weights = self.model(batch_chunks, mask)
                all_weights.append(attn_weights.cpu().numpy())

        return np.vstack(all_weights)

    def save(self, path: str) -> None:
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        torch.save(self.model.state_dict(), save_path / "label_attention.pt")

        config = {
            "embedding_dim": self.embedding_dim,
            "n_codes": self.n_codes,
            "code_names": self.code_names,
            "dropout": self.dropout,
            "gamma_neg": self.gamma_neg,
            "gamma_pos": self.gamma_pos,
            "clip_margin": self.clip_margin,
            "loss_type": self.loss_type,
            "pu_prior_weight": self.pu_prior_weight,
            "prior_cap": self.prior_cap,
        }
        with open(save_path / "label_attention_config.json", "w") as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load(cls, path: str, device: str = "cuda") -> "LabelAttentionWrapper":
        load_path = Path(path)

        with open(load_path / "label_attention_config.json") as f:
            config = json.load(f)

        wrapper = cls(
            embedding_dim=config["embedding_dim"],
            dropout=config.get("dropout", 0.1),
            gamma_neg=config.get("gamma_neg", 4.0),
            gamma_pos=config.get("gamma_pos", 0.0),
            clip_margin=config.get("clip_margin", 0.05),
            loss_type=config.get("loss_type", "asymmetric"),
            pu_prior_weight=config.get("pu_prior_weight", 1.0),
            prior_cap=config.get("prior_cap", 0.5),
            device=device,
        )
        wrapper.n_codes = config["n_codes"]
        wrapper.code_names = config["code_names"]

        wrapper.model = LabelAttentionClassifier(
            n_codes=config["n_codes"],
            embedding_dim=config["embedding_dim"],
            dropout=config.get("dropout", 0.1),
        )
        state_dict = torch.load(load_path / "label_attention.pt", map_location=device, weights_only=False)
        if "classification_weights" not in state_dict:
            state_dict["classification_weights"] = state_dict["code_queries"].clone()
        wrapper.model.load_state_dict(state_dict)
        wrapper.model.to(device)
        wrapper.model.eval()

        return wrapper
