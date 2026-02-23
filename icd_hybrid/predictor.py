import json
from pathlib import Path

import numpy as np

from icd_hybrid.data.text_preprocessor import normalize_clinical_text
from icd_hybrid.data.chunking import OverlappingWindowChunker
from icd_hybrid.data.label_encoder import MultiLabelICDEncoder
from icd_hybrid.embeddings.clinical_bert import ProjectedClinicalBERTEncoder
from icd_hybrid.classifiers.knn_faiss_classifier import KNNFAISSClassifier
from icd_hybrid.classifiers.label_attention import LabelAttentionWrapper


class ICDPredictor:
    def __init__(
        self,
        model_dir: str = "models",
        device: str = "cpu",
        max_chunks: int = 10,
    ):
        self.device = device
        self.max_chunks = max_chunks

        model_path = Path(model_dir)

        self.encoder = ProjectedClinicalBERTEncoder.load_finetuned(
            str(model_path / "embedding_model"), device=device,
        )
        self.knn = KNNFAISSClassifier.load(str(model_path / "knn"))
        self.la = LabelAttentionWrapper.load(
            str(model_path / "label_attention"), device=device,
        )
        self.label_encoder = MultiLabelICDEncoder.load(
            str(model_path / "ensemble" / "label_encoder.json"),
        )
        self.chunker = OverlappingWindowChunker(max_length=512, overlap=128)

        with open(model_path / "ensemble" / "ensemble_config.json") as f:
            self.ensemble_config = json.load(f)

        self.code_names = list(self.label_encoder.code_to_idx.keys())

    def predict(self, text: str, min_freq: int = 0) -> list[dict]:
        text_clean = normalize_clinical_text(text, handle_phi=True)

        chunks = self.chunker.chunk(text_clean, self.encoder.tokenizer)
        chunks = chunks[:self.max_chunks]
        n_chunks = len(chunks)

        chunk_embeddings = self.encoder.encode(chunks, batch_size=32, show_progress=False)

        mean_embedding = np.mean(chunk_embeddings, axis=0).reshape(1, -1)
        knn_scores = self.knn.predict_scores_batch(mean_embedding, self.code_names)[0]

        embedding_dim = chunk_embeddings.shape[1]
        chunks_padded = np.zeros((1, self.max_chunks, embedding_dim), dtype=np.float32)
        chunks_padded[0, :n_chunks, :] = chunk_embeddings
        chunk_counts = np.array([n_chunks])
        la_scores = self.la.predict_scores_batch(chunks_padded, chunk_counts, self.code_names)[0]

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

        chunks = self.chunker.chunk(text_clean, self.encoder.tokenizer)
        chunks = chunks[:self.max_chunks]
        n_chunks = len(chunks)

        chunk_embeddings = self.encoder.encode(chunks, batch_size=32, show_progress=False)

        mean_embedding = np.mean(chunk_embeddings, axis=0).reshape(1, -1)
        knn_scores = self.knn.predict_scores_batch(mean_embedding, self.code_names)[0]

        embedding_dim = chunk_embeddings.shape[1]
        chunks_padded = np.zeros((1, self.max_chunks, embedding_dim), dtype=np.float32)
        chunks_padded[0, :n_chunks, :] = chunk_embeddings
        chunk_counts = np.array([n_chunks])
        la_scores = self.la.predict_scores_batch(chunks_padded, chunk_counts, self.code_names)[0]

        attn_weights = self.la.predict_attention_weights(chunks_padded, chunk_counts)[0]

        la_weight = self.ensemble_config["la_weight"]
        knn_weight = self.ensemble_config["knn_weight"]
        threshold = self.ensemble_config["best_threshold"]
        combined = la_weight * la_scores + knn_weight * knn_scores

        freq_filter = set()
        if min_freq > 0:
            freq_filter = self.label_encoder.get_frequent_codes(min_freq)

        code_to_la_idx = {c: i for i, c in enumerate(self.la.code_names)}

        predictions = []
        for i, code in enumerate(self.code_names):
            if min_freq > 0 and code not in freq_filter:
                continue
            if combined[i] >= threshold:
                la_idx = code_to_la_idx.get(code)
                chunk_attention = None
                if la_idx is not None:
                    chunk_attention = attn_weights[la_idx, :n_chunks].tolist()

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
            "n_chunks": n_chunks,
            "chunk_texts": chunks,
            "mean_embedding": mean_embedding,
        }
