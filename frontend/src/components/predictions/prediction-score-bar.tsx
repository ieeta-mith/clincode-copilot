import { cn } from "@/lib/utils";

interface PredictionScoreBarProps {
  score: number;
  className?: string;
}

export function PredictionScoreBar({
  score,
  className,
}: PredictionScoreBarProps) {
  const widthPercent = Math.min(score * 100, 100);

  return (
    <div className={cn("h-1.5 w-full rounded-full bg-secondary", className)}>
      <div
        className="h-full rounded-full bg-primary transition-all"
        style={{ width: `${widthPercent}%` }}
      />
    </div>
  );
}
