from dataclasses import dataclass


@dataclass
class FAISSConfig:
    index_type: str = "IVFFlat"
    n_neighbors: int = 10
    n_list: int = 100
    n_probe: int = 32
    use_gpu: bool = False
