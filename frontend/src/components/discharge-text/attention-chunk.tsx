import { attentionToHsl } from "@/lib/attention-colors";

interface AttentionChunkProps {
  text: string;
  weight: number;
  maxWeight: number;
  index: number;
}

export function AttentionChunk({
  text,
  weight,
  maxWeight,
  index,
}: AttentionChunkProps) {
  const bgColor = attentionToHsl(weight, maxWeight);

  return (
    <div className="group relative">
      {index > 0 && (
        <div className="mx-auto my-1 h-px w-3/4 bg-border" />
      )}
      <div
        className="rounded px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap transition-colors"
        style={{ backgroundColor: bgColor }}
      >
        {text}
      </div>
    </div>
  );
}
