from pathlib import Path
import json

import numpy as np
import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm


class ClinicalBERTEncoder(nn.Module):
    def __init__(
        self,
        model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        device: str = "cuda",
        pooling_strategy: str = "mean",
        multi_layer: bool = False,
        n_fuse_layers: int = 4,
    ):
        super().__init__()
        self.model_name = model_name
        self.device = device
        self.pooling_strategy = pooling_strategy
        self.multi_layer = multi_layer
        self.n_fuse_layers = n_fuse_layers

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(device)

        self.embedding_dim = self.model.config.hidden_size

        if multi_layer:
            self.layer_weights = nn.Parameter(torch.ones(n_fuse_layers))

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        if self.multi_layer:
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
            )
            all_hidden = outputs.hidden_states
            fuse_layers = all_hidden[-self.n_fuse_layers:]
            weights = torch.softmax(self.layer_weights, dim=0)
            hidden_states = sum(w * h for w, h in zip(weights, fuse_layers))
        else:
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            hidden_states = outputs.last_hidden_state

        if self.pooling_strategy == "cls":
            return hidden_states[:, 0, :]
        elif self.pooling_strategy == "mean":
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size())
            sum_hidden = torch.sum(hidden_states * mask_expanded, dim=1)
            sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
            return sum_hidden / sum_mask
        elif self.pooling_strategy == "max":
            mask_expanded = attention_mask.unsqueeze(-1).expand(hidden_states.size())
            hidden_states[mask_expanded == 0] = -1e9
            return torch.max(hidden_states, dim=1)[0]
        else:
            raise ValueError(f"Unknown pooling strategy: {self.pooling_strategy}")

    def encode_batch(
        self,
        texts: list[str],
        max_length: int = 512,
        show_progress: bool = False,
    ) -> np.ndarray:
        self.model.eval()

        encoding = self.tokenizer(
            texts,
            max_length=max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            embeddings = self.forward(input_ids, attention_mask)

        return embeddings.cpu().numpy()

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_length: int = 512,
        show_progress: bool = True,
    ) -> np.ndarray:
        self.model.eval()
        all_embeddings = []

        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]

        iterator = tqdm(batches, desc="Encoding") if show_progress else batches

        for batch in iterator:
            embeddings = self.encode_batch(batch, max_length=max_length)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def encode_single(self, text: str, max_length: int = 512) -> np.ndarray:
        return self.encode_batch([text], max_length=max_length)[0]


class ProjectedClinicalBERTEncoder(nn.Module):
    def __init__(
        self,
        model_name: str = "emilyalsentzer/Bio_ClinicalBERT",
        device: str = "cuda",
        pooling_strategy: str = "mean",
        projection_dim: int = 256,
    ):
        super().__init__()
        self.base_encoder = ClinicalBERTEncoder(
            model_name=model_name,
            device=device,
            pooling_strategy=pooling_strategy,
        )
        self.projection = nn.Linear(
            self.base_encoder.embedding_dim, projection_dim
        ).to(device)
        self.projection_dim = projection_dim
        self.device = device

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        base_embeddings = self.base_encoder(input_ids, attention_mask)
        projected = self.projection(base_embeddings)
        return nn.functional.normalize(projected, p=2, dim=-1)

    def encode_batch(
        self,
        texts: list[str],
        max_length: int = 512,
    ) -> np.ndarray:
        self.eval()

        encoding = self.base_encoder.tokenizer(
            texts,
            max_length=max_length,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )

        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            embeddings = self.forward(input_ids, attention_mask)

        return embeddings.cpu().numpy()

    def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_length: int = 512,
        show_progress: bool = True,
    ) -> np.ndarray:
        self.eval()
        all_embeddings = []

        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        iterator = tqdm(batches, desc="Encoding") if show_progress else batches

        for batch in iterator:
            embeddings = self.encode_batch(batch, max_length=max_length)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    @property
    def tokenizer(self):
        return self.base_encoder.tokenizer

    @property
    def embedding_dim(self) -> int:
        return self.projection_dim

    @classmethod
    def load_finetuned(
        cls, checkpoint_dir: str, device: str = "cuda"
    ) -> "ProjectedClinicalBERTEncoder":
        checkpoint_path = Path(checkpoint_dir)

        with open(checkpoint_path / "config.json") as f:
            config = json.load(f)

        encoder = cls(
            model_name=config["model_name"],
            device=device,
            pooling_strategy=config.get("pooling_strategy", "mean"),
            projection_dim=config["projection_dim"],
        )

        checkpoint = torch.load(
            checkpoint_path / "best_encoder.pt",
            map_location=device,
            weights_only=False,
        )
        encoder.load_state_dict(checkpoint["model_state_dict"])
        encoder.to(device)
        encoder.eval()

        return encoder
