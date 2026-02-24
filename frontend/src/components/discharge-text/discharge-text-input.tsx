"use client";

import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { FileText, Loader2 } from "lucide-react";
import { useCodingSessionStore } from "@/stores/coding-session-store";

interface DischargeTextInputProps {
  onAnalyze: () => void;
  isLoading: boolean;
}

export function DischargeTextInput({
  onAnalyze,
  isLoading,
}: DischargeTextInputProps) {
  const dischargeText = useCodingSessionStore((s) => s.dischargeText);
  const setDischargeText = useCodingSessionStore((s) => s.setDischargeText);

  const canAnalyze = dischargeText.trim().length >= 50 && !isLoading;

  return (
    <div className="flex h-full flex-col gap-3 overflow-hidden p-4">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <FileText className="h-4 w-4" />
        DISCHARGE SUMMARY
      </div>
      <Textarea
        placeholder="Paste discharge summary text here (minimum 50 characters)..."
        value={dischargeText}
        onChange={(e) => setDischargeText(e.target.value)}
        className="min-h-0 flex-1 resize-none overflow-auto font-mono text-sm"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {dischargeText.length} characters
        </span>
        <Button onClick={onAnalyze} disabled={!canAnalyze}>
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            "Analyze"
          )}
        </Button>
      </div>
    </div>
  );
}
