from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_dir: Path = Path("models")
    icd_dictionary_path: Path = Path("models/icd_dictionary.json")
    device: str = "cpu"
    max_chunks: int = 20
    max_length: int = 128
    chunk_overlap: int = 32
    neighbor_count: int = 50
    default_min_freq: int = 0
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_prefix": "CLINCODE_"}
