"use client";

import { useCodingSessionStore } from "@/stores/coding-session-store";
import { usePrediction } from "@/hooks/use-prediction";
import { WorkspaceHeader } from "./workspace-header";
import { DischargeTextInput } from "@/components/discharge-text/discharge-text-input";
import { DischargeTextViewer } from "@/components/discharge-text/discharge-text-viewer";
import { PredictionPanel } from "@/components/predictions/prediction-panel";
import { SimilarPatientsPanel } from "@/components/similar-patients/similar-patients-panel";
import { ChunksSkeleton } from "@/components/shared/loading-skeleton";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";

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
      <ResizablePanelGroup orientation="horizontal" className="flex-1">
        <ResizablePanel defaultSize={45} minSize={25}>
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
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={55} minSize={30}>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel defaultSize={60} minSize={20}>
              <PredictionPanel isLoading={prediction.isPending} />
            </ResizablePanel>

            <ResizableHandle withHandle />

            <ResizablePanel defaultSize={40} minSize={15}>
              <SimilarPatientsPanel />
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
