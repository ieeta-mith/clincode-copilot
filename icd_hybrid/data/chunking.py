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

    def _compute_windows(self, n_tokens: int) -> list[tuple[int, int]]:
        effective_max = self.max_length - self._special_token_count
        stride = effective_max - self.overlap

        if stride <= 0:
            stride = effective_max // 2

        windows = []
        for start in range(0, n_tokens, stride):
            end = min(start + effective_max, n_tokens)
            windows.append((start, end))
            if end >= n_tokens:
                break

        return windows

    def chunk(self, text: str, tokenizer: PreTrainedTokenizer) -> list[str]:
        tokens = tokenizer.encode(
            text,
            add_special_tokens=False,
            truncation=False,
        )

        windows = self._compute_windows(len(tokens))

        chunks = []
        for start, end in windows:
            chunk_text = tokenizer.decode(tokens[start:end], skip_special_tokens=True)
            chunks.append(chunk_text)

        return chunks if chunks else [text]

    def chunk_with_spans(
        self, text: str, tokenizer: PreTrainedTokenizer
    ) -> tuple[list[str], list[tuple[int, int]]]:
        encoded = tokenizer(
            text,
            add_special_tokens=False,
            truncation=False,
            return_offsets_mapping=True,
        )

        tokens = encoded["input_ids"]
        offsets = encoded["offset_mapping"]
        windows = self._compute_windows(len(tokens))

        chunks = []
        spans = []
        for start, end in windows:
            chunk_text = tokenizer.decode(tokens[start:end], skip_special_tokens=True)
            char_start = offsets[start][0]
            char_end = offsets[end - 1][1]
            chunks.append(chunk_text)
            spans.append((char_start, char_end))

        if not chunks:
            return [text], [(0, len(text))]

        return chunks, spans
