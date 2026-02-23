from abc import ABC, abstractmethod

from transformers import PreTrainedTokenizer


class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, tokenizer: PreTrainedTokenizer) -> list[str]:
        pass


class OverlappingWindowChunker(ChunkingStrategy):
    def __init__(
        self,
        max_length: int = 512,
        overlap: int = 128,
        add_special_tokens: bool = True,
    ):
        self.max_length = max_length
        self.overlap = overlap
        self.add_special_tokens = add_special_tokens
        self._special_token_count = 2 if add_special_tokens else 0

    def chunk(self, text: str, tokenizer: PreTrainedTokenizer) -> list[str]:
        tokens = tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=False,
        )

        effective_max = self.max_length - self._special_token_count
        stride = effective_max - self.overlap

        if stride <= 0:
            stride = effective_max // 2

        chunks = []

        for start in range(0, len(tokens), stride):
            end = min(start + effective_max, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)

            if end >= len(tokens):
                break

        return chunks if chunks else [text]
