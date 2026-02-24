"use client";

import { useEffect } from "react";
import { useCodingSessionStore } from "@/stores/coding-session-store";
import { useSimilarPatients } from "@/hooks/use-similar-patients";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SimilarPatientCard } from "./similar-patient-card";
import { SimilarPatientsSkeleton } from "@/components/shared/loading-skeleton";
import { Users } from "lucide-react";

export function SimilarPatientsPanel() {
  const selectedCode = useCodingSessionStore((s) => s.selectedCode);
  const dischargeText = useCodingSessionStore((s) => s.dischargeText);
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);

  const { mutate, data, isPending, reset } = useSimilarPatients();

  useEffect(() => {
    if (selectedCode && dischargeText && predictionResult) {
      mutate({ text: dischargeText, codes: [selectedCode] });
    } else {
      reset();
    }
  }, [selectedCode, dischargeText, predictionResult, mutate, reset]);

  const neighbors = data?.per_code_neighbors?.[0];

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-medium text-muted-foreground">
        <Users className="h-4 w-4" />
        SIMILAR PATIENTS
        {selectedCode && (
          <span className="ml-auto text-xs">
            for <span className="font-mono font-semibold text-foreground">{selectedCode}</span>
          </span>
        )}
      </div>

      {isPending ? (
        <SimilarPatientsSkeleton />
      ) : !selectedCode || !predictionResult ? (
        <div className="flex flex-1 items-center justify-center p-4 text-center text-sm text-muted-foreground">
          Select a predicted code to see similar patients.
        </div>
      ) : !neighbors || neighbors.similar_patients.length === 0 ? (
        <div className="flex flex-1 items-center justify-center p-4 text-center text-sm text-muted-foreground">
          No similar patients found for {selectedCode}.
        </div>
      ) : (
        <ScrollArea className="flex-1 min-h-0">
          <div className="space-y-2 p-4">
            {neighbors.similar_patients.map((patient, i) => (
              <SimilarPatientCard key={i} patient={patient} />
            ))}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
