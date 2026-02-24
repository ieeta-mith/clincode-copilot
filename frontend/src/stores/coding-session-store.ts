import { create } from "zustand";
import type { DetailedPredictionResponse } from "@/lib/api-types";

interface CodingSessionState {
  dischargeText: string;
  predictionResult: DetailedPredictionResponse | null;
  selectedCode: string | null;

  setDischargeText: (text: string) => void;
  setPredictionResult: (result: DetailedPredictionResponse | null) => void;
  selectCode: (code: string | null) => void;
  clearSession: () => void;
}

export const useCodingSessionStore = create<CodingSessionState>((set) => ({
  dischargeText: "",
  predictionResult: null,
  selectedCode: null,

  setDischargeText: (text) => set({ dischargeText: text }),

  setPredictionResult: (result) =>
    set({
      predictionResult: result,
      selectedCode: result?.predictions[0]?.code ?? null,
    }),

  selectCode: (code) => set({ selectedCode: code }),

  clearSession: () =>
    set({
      dischargeText: "",
      predictionResult: null,
      selectedCode: null,
    }),
}));
