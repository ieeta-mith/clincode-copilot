"use client";

import { useMemo } from "react";
import { useCodingSessionStore } from "@/stores/coding-session-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AttentionChunk } from "./attention-chunk";
import { FileText } from "lucide-react";

interface TextSegment {
  text: string;
  weight: number;
}

function buildAttentionSegments(
  originalText: string,
  chunkSpans: [number, number][],
  chunkWeights: number[]
): TextSegment[] {
  if (originalText.length === 0) return [];

  const charWeights = new Float64Array(originalText.length);

  for (let i = 0; i < chunkSpans.length; i++) {
    const [start, end] = chunkSpans[i];
    const weight = chunkWeights[i];
    for (let j = start; j < end && j < originalText.length; j++) {
      charWeights[j] = Math.max(charWeights[j], weight);
    }
  }

  const segments: TextSegment[] = [];
  let segStart = 0;

  for (let i = 1; i <= originalText.length; i++) {
    if (
      i === originalText.length ||
      Math.abs(charWeights[i] - charWeights[segStart]) > 1e-9
    ) {
      segments.push({
        text: originalText.slice(segStart, i),
        weight: charWeights[segStart],
      });
      segStart = i;
    }
  }

  return segments;
}

export function DischargeTextViewer() {
  const predictionResult = useCodingSessionStore((s) => s.predictionResult);
  const selectedCode = useCodingSessionStore((s) => s.selectedCode);

  const selectedPrediction = predictionResult?.predictions.find(
    (p) => p.code === selectedCode
  );

  const chunkWeights = useMemo(() => {
    if (!predictionResult) return [];
    return predictionResult.chunk_texts.map((_, i) => {
      if (!selectedPrediction?.chunk_attentions) return 0;
      const attention = selectedPrediction.chunk_attentions.find(
        (a) => a.chunk_index === i
      );
      return attention?.attention_weight ?? 0;
    });
  }, [predictionResult, selectedPrediction]);

  const maxWeight = useMemo(
    () => Math.max(...chunkWeights, 0),
    [chunkWeights]
  );

  const segments = useMemo(() => {
    if (!predictionResult) return [];
    return buildAttentionSegments(
      predictionResult.original_text,
      predictionResult.chunk_char_spans,
      chunkWeights
    );
  }, [predictionResult, chunkWeights]);

  if (!predictionResult) return null;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-medium text-muted-foreground">
        <FileText className="h-4 w-4" />
        DISCHARGE SUMMARY
        <span className="ml-auto text-xs">
          {predictionResult.chunk_count} chunks
          {selectedCode && (
            <>
              {" "}
              — highlighting for{" "}
              <span className="font-mono font-semibold text-foreground">
                {selectedCode}
              </span>
            </>
          )}
        </span>
      </div>
      <ScrollArea className="min-h-0 flex-1">
        <div className="whitespace-pre-wrap break-words p-4 text-sm leading-relaxed">
          {segments.map((segment, i) => (
            <AttentionChunk
              key={i}
              text={segment.text}
              weight={segment.weight}
              maxWeight={maxWeight}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
