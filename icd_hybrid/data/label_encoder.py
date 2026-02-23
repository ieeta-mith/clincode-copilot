from collections import Counter

import numpy as np
import scipy.sparse as sp


class MultiLabelICDEncoder:
    def __init__(self, min_frequency: int = 0):
        self.min_frequency = min_frequency
        self.code_to_idx: dict[str, int] = {}
        self.idx_to_code: dict[int, str] = {}
        self.code_frequencies: Counter = Counter()
        self.n_codes: int = 0
        self._fitted: bool = False

    def fit(self, code_lists: list[list[str]]) -> "MultiLabelICDEncoder":
        all_codes = [code for codes in code_lists for code in codes]
        self.code_frequencies = Counter(all_codes)

        filtered_codes = sorted(
            code
            for code, freq in self.code_frequencies.items()
            if freq >= self.min_frequency
        )

        self.code_to_idx = {code: idx for idx, code in enumerate(filtered_codes)}
        self.idx_to_code = {idx: code for code, idx in self.code_to_idx.items()}
        self.n_codes = len(filtered_codes)
        self._fitted = True

        return self

    def transform(self, code_lists: list[list[str]]) -> sp.csr_matrix:
        if not self._fitted:
            raise RuntimeError("Encoder must be fitted before transform")

        rows = []
        cols = []
        data = []

        for row_idx, codes in enumerate(code_lists):
            for code in codes:
                if code in self.code_to_idx:
                    rows.append(row_idx)
                    cols.append(self.code_to_idx[code])
                    data.append(1)

        matrix = sp.csr_matrix(
            (data, (rows, cols)),
            shape=(len(code_lists), self.n_codes),
            dtype=np.float32,
        )

        return matrix

    def fit_transform(self, code_lists: list[list[str]]) -> sp.csr_matrix:
        self.fit(code_lists)
        return self.transform(code_lists)

    def inverse_transform(self, matrix: sp.csr_matrix) -> list[list[str]]:
        if not self._fitted:
            raise RuntimeError("Encoder must be fitted before inverse_transform")

        result = []

        for row_idx in range(matrix.shape[0]):
            row = matrix.getrow(row_idx)
            codes = [self.idx_to_code[col] for col in row.indices]
            result.append(codes)

        return result

    def get_code_frequencies(self) -> dict[str, int]:
        return dict(self.code_frequencies)

    def get_rare_codes(self, threshold: int) -> set[str]:
        return {
            code
            for code, freq in self.code_frequencies.items()
            if freq < threshold and code in self.code_to_idx
        }

    def get_frequent_codes(self, threshold: int) -> set[str]:
        return {
            code
            for code, freq in self.code_frequencies.items()
            if freq >= threshold and code in self.code_to_idx
        }

    def get_icd_category(self, code: str) -> str:
        if len(code) >= 3:
            return code[:3]
        return code

    def group_by_category(self) -> dict[str, list[str]]:
        categories: dict[str, list[str]] = {}

        for code in self.code_to_idx:
            category = self.get_icd_category(code)
            if category not in categories:
                categories[category] = []
            categories[category].append(code)

        return categories

    def save(self, path: str) -> None:
        import json

        state = {
            "code_to_idx": self.code_to_idx,
            "code_frequencies": dict(self.code_frequencies),
            "min_frequency": self.min_frequency,
        }

        with open(path, "w") as f:
            json.dump(state, f)

    @classmethod
    def load(cls, path: str) -> "MultiLabelICDEncoder":
        import json

        with open(path, "r") as f:
            state = json.load(f)

        encoder = cls(min_frequency=state["min_frequency"])
        encoder.code_to_idx = state["code_to_idx"]
        encoder.idx_to_code = {int(k): v for v, k in encoder.code_to_idx.items()}
        encoder.code_frequencies = Counter(state["code_frequencies"])
        encoder.n_codes = len(encoder.code_to_idx)
        encoder._fitted = True

        return encoder
