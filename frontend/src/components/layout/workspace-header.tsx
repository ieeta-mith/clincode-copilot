"use client";

import { Button } from "@/components/ui/button";
import { HealthIndicator } from "@/components/shared/health-indicator";
import { useCodingSessionStore } from "@/stores/coding-session-store";
import { Stethoscope, Trash2 } from "lucide-react";

export function WorkspaceHeader() {
  const clearSession = useCodingSessionStore((s) => s.clearSession);
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);

  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <div className="flex items-center gap-3">
        <Stethoscope className="h-5 w-5" />
        <h1 className="text-lg font-semibold">ClinCode Copilot</h1>
      </div>
      <div className="flex items-center gap-3">
        <HealthIndicator />
        {predictionResult && (
          <Button variant="ghost" size="sm" onClick={clearSession}>
            <Trash2 className="h-4 w-4" />
            Clear
          </Button>
        )}
      </div>
    </header>
  );
}
