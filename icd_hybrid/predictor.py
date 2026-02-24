import json
from pathlib import Path

import numpy as np
import torch
from transformers import AutoTokenizer

from icd_hybrid.data.text_preprocessor import normalize_clinical_text
from icd_hybrid.data.chunking import OverlappingWindowChunker
from icd_hybrid.data.label_encoder import MultiLabelICDEncoder
from icd_hybrid.classifiers.knn_faiss_classifier import KNNFAISSClassifier
from icd_hybrid.models.end_to_end import EndToEndLabelAttention


class ICDPredictor:
    def __init__(
        self,
        model_dir: str = "models",
        device: str = "cpu",
        max_chunks: int = 10,
        max_length: int = 128,
        chunk_overlap: int = 32,
    ):
        self.device = device
        self.max_chunks = max_chunks
        self.max_length = max_length

        model_path = Path(model_dir)

        self.e2e_model = EndToEndLabelAttention.load(
            str(model_path / "end_to_end"), device=device,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.e2e_model.model_name)
        self.knn = KNNFAISSClassifier.load(str(model_path / "knn_chunks"))
        self.label_encoder = MultiLabelICDEncoder.load(
            str(model_path / "ensemble" / "label_encoder.json"),
        )
        self.chunker = OverlappingWindowChunker(max_length=max_length, overlap=chunk_overlap)

        with open(model_path / "ensemble" / "ensemble_config.json") as f:
            self.ensemble_config = json.load(f)

        self.code_names = list(self.label_encoder.code_to_idx.keys())

        checkpoint = torch.load(
            model_path / "end_to_end" / "end_to_end.pt",
            map_location=device,
            weights_only=False,
        )
        self.e2e_code_names: list[str] = checkpoint["config"]["code_names"]
        self._e2e_to_full = np.array(
            [self.label_encoder.code_to_idx[c] for c in self.e2e_code_names],
            dtype=np.intp,
        )

    def _tokenize_chunks(self, chunks: list[str]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        n_chunks = len(chunks)

        encoded = self.tokenizer(
            chunks,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        input_ids = torch.zeros(1, self.max_chunks, self.max_length, dtype=torch.long)
        attention_mask = torch.zeros(1, self.max_chunks, self.max_length, dtype=torch.long)
        input_ids[0, :n_chunks] = encoded["input_ids"]
        attention_mask[0, :n_chunks] = encoded["attention_mask"]
        chunk_counts = torch.tensor([n_chunks], dtype=torch.long)

        return (
            input_ids.to(self.device),
            attention_mask.to(self.device),
            chunk_counts.to(self.device),
        )

    def _expand_to_full(self, e2e_scores: np.ndarray) -> np.ndarray:
        full = np.zeros(len(self.code_names), dtype=e2e_scores.dtype)
        full[self._e2e_to_full] = e2e_scores
        return full

    def _expand_attn_to_full(self, attn_weights: np.ndarray) -> np.ndarray:
        n_e2e, n_chunks = attn_weights.shape
        full = np.zeros((len(self.code_names), n_chunks), dtype=attn_weights.dtype)
        full[self._e2e_to_full] = attn_weights
        return full

    def _run_e2e(self, chunks: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        input_ids, attention_mask, chunk_counts = self._tokenize_chunks(chunks)
        n_chunks = len(chunks)

        with torch.no_grad():
            logits, attn_weights, chunk_embeddings = self.e2e_model(
                input_ids, attention_mask, chunk_counts,
            )

        la_scores_e2e = torch.sigmoid(logits).cpu().numpy()[0]
        attn_weights_e2e = attn_weights.cpu().numpy()[0]
        mean_embedding = chunk_embeddings[0, :n_chunks].mean(dim=0).cpu().numpy().reshape(1, -1)
        chunk_embs_np = chunk_embeddings.cpu().numpy()

        la_scores = self._expand_to_full(la_scores_e2e)
        attn_weights_full = self._expand_attn_to_full(attn_weights_e2e)

        return la_scores, attn_weights_full, mean_embedding, chunk_embs_np, n_chunks

    def _encode_all_chunks(self, all_chunks: list[str]) -> tuple[np.ndarray, list[np.ndarray], np.ndarray, int]:
        embeddings = []
        la_scores_parts = []
        attn_parts = []
        for start in range(0, len(all_chunks), self.max_chunks):
            batch = all_chunks[start:start + self.max_chunks]
            la, attn, _, chunk_embs, n = self._run_e2e(batch)
            embeddings.append(chunk_embs[0, :n])
            la_scores_parts.append(la)
            attn_parts.append(attn[:, :n])
        all_embs = np.concatenate(embeddings, axis=0)
        la_scores = np.stack(la_scores_parts).max(axis=0)
        attn_weights = np.concatenate([a for a in attn_parts], axis=1)
        return la_scores, attn_weights, all_embs, len(all_chunks)

    def predict(self, text: str, min_freq: int = 0) -> list[dict]:
        text_clean = normalize_clinical_text(text, handle_phi=True)

        all_chunks = self.chunker.chunk(text_clean, self.tokenizer)
        la_scores, _, all_embs, total_chunks = self._encode_all_chunks(all_chunks)
        knn_embs = all_embs.reshape(1, total_chunks, -1)
        knn_scores = self.knn.predict_scores_batch_chunks(knn_embs, np.array([total_chunks]), self.code_names)[0]

        la_weight = self.ensemble_config["la_weight"]
        knn_weight = self.ensemble_config["knn_weight"]
        threshold = self.ensemble_config["best_threshold"]
        combined = la_weight * la_scores + knn_weight * knn_scores

        freq_filter = set()
        if min_freq > 0:
            freq_filter = self.label_encoder.get_frequent_codes(min_freq)

        results = []
        for i, code in enumerate(self.code_names):
            if min_freq > 0 and code not in freq_filter:
                continue
            if combined[i] >= threshold:
                results.append({
                    "code": code,
                    "score": float(combined[i]),
                    "la_score": float(la_scores[i]),
                    "knn_score": float(knn_scores[i]),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        for rank, r in enumerate(results, 1):
            r["rank"] = rank

        return results

    def predict_with_attention(self, text: str, min_freq: int = 0) -> dict:
        text_clean = normalize_clinical_text(text, handle_phi=True)

        all_chunks, chunk_spans = self.chunker.chunk_with_spans(text_clean, self.tokenizer)

        la_scores, attn_weights, all_embs, total_chunks = self._encode_all_chunks(all_chunks)
        knn_embs = all_embs.reshape(1, total_chunks, -1)
        knn_scores = self.knn.predict_scores_batch_chunks(knn_embs, np.array([total_chunks]), self.code_names)[0]

        la_weight = self.ensemble_config["la_weight"]
        knn_weight = self.ensemble_config["knn_weight"]
        threshold = self.ensemble_config["best_threshold"]
        combined = la_weight * la_scores + knn_weight * knn_scores

        freq_filter = set()
        if min_freq > 0:
            freq_filter = self.label_encoder.get_frequent_codes(min_freq)

        predictions = []
        for i, code in enumerate(self.code_names):
            if min_freq > 0 and code not in freq_filter:
                continue
            if combined[i] >= threshold:
                chunk_attention = attn_weights[i].tolist()

                predictions.append({
                    "code": code,
                    "score": float(combined[i]),
                    "la_score": float(la_scores[i]),
                    "knn_score": float(knn_scores[i]),
                    "chunk_attention": chunk_attention,
                })

        predictions.sort(key=lambda x: x["score"], reverse=True)
        for rank, p in enumerate(predictions, 1):
            p["rank"] = rank

        return {
            "predictions": predictions,
            "n_chunks": total_chunks,
            "chunk_texts": all_chunks,
            "original_text": text_clean,
            "chunk_char_spans": chunk_spans,
        }

    def encode_chunks(self, text: str) -> tuple[np.ndarray, int]:
        text_clean = normalize_clinical_text(text, handle_phi=True)
        all_chunks = self.chunker.chunk(text_clean, self.tokenizer)
        _, _, all_embs, total_chunks = self._encode_all_chunks(all_chunks)
        return all_embs, total_chunks
