import { attentionToHsl } from "@/lib/attention-colors";

interface AttentionChunkProps {
  text: string;
  weight: number;
  maxWeight: number;
}

export function AttentionChunk({
  text,
  weight,
  maxWeight,
}: AttentionChunkProps) {
  const bgColor = attentionToHsl(weight, maxWeight);

  return (
    <span
      className="rounded-sm transition-colors"
      style={{ backgroundColor: bgColor }}
    >
      {text}
    </span>
  );
}
