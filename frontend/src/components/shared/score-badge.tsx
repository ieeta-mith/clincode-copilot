import { Badge } from "@/components/ui/badge";
import { formatScore } from "@/lib/format";
import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

export function ScoreBadge({ score, className }: ScoreBadgeProps) {
  return (
    <Badge
      variant="secondary"
      className={cn("font-mono tabular-nums", className)}
    >
      {formatScore(score)}
    </Badge>
  );
}
