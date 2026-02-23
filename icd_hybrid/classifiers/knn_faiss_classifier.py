from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import pickle

import numpy as np
import scipy.sparse as sp
import faiss
from tqdm import tqdm

from icd_hybrid.config import FAISSConfig
from icd_hybrid.classifiers.base import (
    BaseClassifier,
    ClassifierPrediction,
    ClassifierResult,
)


@dataclass
class NeighborInfo:
    index: int
    admission_id: Optional[int]
    distance: float
    similarity: float
    codes: list[str]


class KNNFAISSClassifier(BaseClassifier):
    def __init__(self, config: FAISSConfig):
        self.config = config
        self.index: Optional[faiss.Index] = None
        self.labels: Optional[sp.csr_matrix] = None
        self.code_names: list[str] = []
        self.admission_ids: Optional[np.ndarray] = None
        self.embedding_dim: int = 0
        self._fitted = False

    def fit(
        self,
        embeddings: np.ndarray,
        labels: sp.csr_matrix,
        code_names: Optional[list[str]] = None,
        admission_ids: Optional[np.ndarray] = None,
    ) -> None:
        if code_names is not None:
            self.code_names = code_names
        else:
            self.code_names = [str(i) for i in range(labels.shape[1])]

        self.labels = labels
        self.admission_ids = admission_ids
        self.embedding_dim = embeddings.shape[1]

        embeddings = embeddings.astype(np.float32)
        embeddings = self._normalize(embeddings)

        self._build_index(embeddings)
        self._fitted = True

    def _normalize(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def _build_index(self, embeddings: np.ndarray) -> None:
        n_samples, dim = embeddings.shape

        if self.config.index_type == "Flat":
            self.index = faiss.IndexFlatIP(dim)
        elif self.config.index_type == "IVFFlat":
            n_list = min(self.config.n_list, n_samples // 10)
            n_list = max(n_list, 1)

            quantizer = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIVFFlat(quantizer, dim, n_list)
            self.index.train(embeddings)
            self.index.nprobe = self.config.n_probe
        elif self.config.index_type == "IVFPQ":
            n_list = min(self.config.n_list, n_samples // 10)
            n_list = max(n_list, 1)
            m = min(8, dim // 4)

            quantizer = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIVFPQ(quantizer, dim, n_list, m, 8)
            self.index.train(embeddings)
            self.index.nprobe = self.config.n_probe
        else:
            raise ValueError(f"Unknown index type: {self.config.index_type}")

        self.index.add(embeddings)

    def get_neighbors(
        self, embedding: np.ndarray, k: Optional[int] = None
    ) -> list[NeighborInfo]:
        if not self._fitted:
            raise RuntimeError("Classifier must be fitted before prediction")

        k = k or self.config.n_neighbors

        query = embedding.astype(np.float32).reshape(1, -1)
        query = self._normalize(query)

        similarities, indices = self.index.search(query, k)
        similarities = similarities[0]
        indices = indices[0]

        neighbors = []
        for i, (idx, sim) in enumerate(zip(indices, similarities)):
            if idx == -1:
                continue

            codes = []
            row = self.labels.getrow(idx)
            for code_idx in row.indices:
                codes.append(self.code_names[code_idx])

            admission_id = None
            if self.admission_ids is not None:
                admission_id = int(self.admission_ids[idx])

            neighbors.append(
                NeighborInfo(
                    index=int(idx),
                    admission_id=admission_id,
                    distance=float(1 - sim),
                    similarity=float(sim),
                    codes=codes,
                )
            )

        return neighbors

    def predict(self, embedding: np.ndarray) -> ClassifierResult:
        neighbors = self.get_neighbors(embedding)

        code_scores: dict[str, float] = {}
        code_counts: dict[str, int] = {}

        for neighbor in neighbors:
            neighbor_code_count = len(neighbor.codes)
            for code in neighbor.codes:
                if code not in code_scores:
                    code_scores[code] = 0.0
                    code_counts[code] = 0
                code_scores[code] += neighbor.similarity / neighbor_code_count
                code_counts[code] += 1

        total_similarity = sum(n.similarity for n in neighbors)
        if total_similarity > 0:
            code_probs = {
                code: score / total_similarity for code, score in code_scores.items()
            }
        else:
            code_probs = code_scores

        predictions = []
        for code, prob in code_probs.items():
            count = code_counts[code]
            avg_sim = code_scores[code] / count if count > 0 else 0

            supporting_neighbors = [
                f"#{n.index}({n.similarity:.2f})" for n in neighbors if code in n.codes
            ][:3]

            explanation = (
                f"Found in {count}/{len(neighbors)} neighbors, "
                f"avg similarity: {avg_sim:.3f}, "
                f"neighbors: {', '.join(supporting_neighbors)}"
            )

            predictions.append(
                ClassifierPrediction(
                    code=code,
                    probability=prob,
                    explanation=explanation,
                    confidence=count / len(neighbors),
                    method="knn",
                    raw_score=code_scores[code],
                )
            )

        predictions.sort(key=lambda x: x.probability, reverse=True)

        return ClassifierResult(
            predictions=predictions,
            embedding=embedding,
            is_outlier=False,
            outlier_score=0.0,
            raw_output={"neighbors": neighbors},
        )

    def predict_proba(self, embedding: np.ndarray) -> dict[str, float]:
        result = self.predict(embedding)
        return {p.code: p.probability for p in result.predictions}

    def predict_batch(self, embeddings: np.ndarray) -> list[ClassifierResult]:
        results = []
        for emb in tqdm(embeddings, desc="KNN predictions"):
            results.append(self.predict(emb))
        return results

    def predict_scores_batch(
        self,
        embeddings: np.ndarray,
        code_list: list[str],
    ) -> np.ndarray:
        queries = embeddings.astype(np.float32)
        queries = self._normalize(queries)

        similarities, indices = self.index.search(queries, self.config.n_neighbors)

        code_to_idx = {code: i for i, code in enumerate(code_list)}
        n_samples = len(embeddings)
        n_codes = len(code_list)
        scores = np.zeros((n_samples, n_codes), dtype=np.float32)

        for i in range(n_samples):
            total_sim = 0.0
            code_sims: dict[int, float] = {}

            for j in range(self.config.n_neighbors):
                idx = indices[i, j]
                sim = similarities[i, j]

                if idx == -1:
                    continue

                total_sim += sim
                row = self.labels.getrow(idx)
                neighbor_code_count = row.nnz

                for code_idx in row.indices:
                    if code_idx not in code_sims:
                        code_sims[code_idx] = 0.0
                    code_sims[code_idx] += sim / neighbor_code_count

            if total_sim > 0:
                for code_idx, sim_sum in code_sims.items():
                    code = self.code_names[code_idx]
                    if code in code_to_idx:
                        scores[i, code_to_idx[code]] = sim_sum / total_sim

        return scores

    def get_neighbor_explanation(
        self, embedding: np.ndarray, max_neighbors: int = 5
    ) -> str:
        neighbors = self.get_neighbors(embedding, k=max_neighbors)

        lines = ["Similar patients:"]
        for i, neighbor in enumerate(neighbors, 1):
            admission_str = (
                f"admission {neighbor.admission_id}"
                if neighbor.admission_id
                else f"index {neighbor.index}"
            )
            codes_str = ", ".join(neighbor.codes[:5])
            if len(neighbor.codes) > 5:
                codes_str += f", ... (+{len(neighbor.codes) - 5})"

            lines.append(
                f"  {i}. {admission_str} (similarity: {neighbor.similarity:.3f}) - "
                f"Codes: {codes_str}"
            )

        return "\n".join(lines)

    def save(self, path: str) -> None:
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(save_path / "faiss.index"))

        state = {
            "config": self.config,
            "labels": self.labels,
            "code_names": self.code_names,
            "admission_ids": self.admission_ids,
            "embedding_dim": self.embedding_dim,
        }

        with open(save_path / "knn_metadata.pkl", "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, path: str) -> "KNNFAISSClassifier":
        load_path = Path(path)

        with open(load_path / "knn_metadata.pkl", "rb") as f:
            state = pickle.load(f)

        classifier = cls(config=state["config"])
        classifier.labels = state["labels"]
        classifier.code_names = state["code_names"]
        classifier.admission_ids = state["admission_ids"]
        classifier.embedding_dim = state["embedding_dim"]
        classifier.index = faiss.read_index(str(load_path / "faiss.index"))
        classifier._fitted = True

        return classifier
