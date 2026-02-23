"use client";

import { useCodingSessionStore } from "@/stores/coding-session-store";
import { usePrediction } from "@/hooks/use-prediction";
import { WorkspaceHeader } from "./workspace-header";
import { DischargeTextInput } from "@/components/discharge-text/discharge-text-input";
import { DischargeTextViewer } from "@/components/discharge-text/discharge-text-viewer";
import { PredictionPanel } from "@/components/predictions/prediction-panel";
import { SimilarPatientsPanel } from "@/components/similar-patients/similar-patients-panel";
import { ChunksSkeleton } from "@/components/shared/loading-skeleton";

export function WorkspaceLayout() {
  const dischargeText = useCodingSessionStore((s) => s.dischargeText);
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);
  const setPredictionResult = useCodingSessionStore(
    (s) => s.setPredictionResult
  );

  const prediction = usePrediction();

  function handleAnalyze() {
    prediction.mutate(
      { text: dischargeText },
      { onSuccess: (data) => setPredictionResult(data) }
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <WorkspaceHeader />
      <div className="grid flex-1 grid-cols-[45fr_55fr] overflow-hidden">
        <div className="border-r overflow-hidden">
          {predictionResult ? (
            prediction.isPending ? (
              <ChunksSkeleton />
            ) : (
              <DischargeTextViewer />
            )
          ) : (
            <DischargeTextInput
              onAnalyze={handleAnalyze}
              isLoading={prediction.isPending}
            />
          )}
        </div>

        <div className="grid grid-rows-[3fr_2fr] overflow-hidden">
          <div className="overflow-hidden border-b">
            <PredictionPanel isLoading={prediction.isPending} />
          </div>
          <div className="overflow-hidden">
            <SimilarPatientsPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
