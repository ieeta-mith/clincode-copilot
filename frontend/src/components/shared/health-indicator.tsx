"use client";

import { useHealth } from "@/hooks/use-health";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function HealthIndicator() {
  const { data, isError } = useHealth();

  const isHealthy = data?.status === "ok" && data.model_loaded;
  const label = isError
    ? "Backend unreachable"
    : isHealthy
      ? `Healthy — ${data.code_count} codes loaded`
      : "Backend loading...";

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div
            className={`h-2.5 w-2.5 rounded-full ${
              isError
                ? "bg-red-500"
                : isHealthy
                  ? "bg-emerald-500"
                  : "bg-amber-500 animate-pulse"
            }`}
          />
          <span className="hidden sm:inline">
            {isError ? "Offline" : isHealthy ? "Healthy" : "Loading"}
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}
