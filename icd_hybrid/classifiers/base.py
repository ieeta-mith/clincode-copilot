from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np
import scipy.sparse as sp


@dataclass
class ClassifierPrediction:
    code: str
    probability: float
    explanation: str
    confidence: float
    method: str
    raw_score: Optional[float] = None


@dataclass
class ClassifierResult:
    predictions: list[ClassifierPrediction]
    embedding: np.ndarray
    is_outlier: bool = False
    outlier_score: float = 0.0
    raw_output: Optional[dict] = None


class BaseClassifier(ABC):
    @abstractmethod
    def fit(
        self,
        embeddings: np.ndarray,
        labels: sp.csr_matrix,
        code_names: Optional[list[str]] = None,
    ) -> None:
        pass

    @abstractmethod
    def predict(self, embedding: np.ndarray) -> ClassifierResult:
        pass

    @abstractmethod
    def predict_proba(self, embedding: np.ndarray) -> dict[str, float]:
        pass

    @abstractmethod
    def predict_batch(self, embeddings: np.ndarray) -> list[ClassifierResult]:
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "BaseClassifier":
        pass

    def get_top_k_predictions(
        self,
        embedding: np.ndarray,
        k: int = 10,
        threshold: float = 0.0,
    ) -> list[ClassifierPrediction]:
        result = self.predict(embedding)
        filtered = [p for p in result.predictions if p.probability >= threshold]
        sorted_predictions = sorted(filtered, key=lambda x: x.probability, reverse=True)
        return sorted_predictions[:k]
