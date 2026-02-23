import { create } from "zustand";
import type { DetailedPredictionResponse } from "@/lib/api-types";

interface CodingSessionState {
  dischargeText: string;
  predictionResult: DetailedPredictionResponse | null;
  selectedCode: string | null;
  acceptedCodes: Set<string>;
  rejectedCodes: Set<string>;

  setDischargeText: (text: string) => void;
  setPredictionResult: (result: DetailedPredictionResponse | null) => void;
  selectCode: (code: string | null) => void;
  acceptCode: (code: string) => void;
  rejectCode: (code: string) => void;
  resetCodeDecision: (code: string) => void;
  clearSession: () => void;
}

export const useCodingSessionStore = create<CodingSessionState>((set) => ({
  dischargeText: "",
  predictionResult: null,
  selectedCode: null,
  acceptedCodes: new Set(),
  rejectedCodes: new Set(),

  setDischargeText: (text) => set({ dischargeText: text }),

  setPredictionResult: (result) =>
    set({
      predictionResult: result,
      selectedCode: result?.predictions[0]?.code ?? null,
      acceptedCodes: new Set(),
      rejectedCodes: new Set(),
    }),

  selectCode: (code) => set({ selectedCode: code }),

  acceptCode: (code) =>
    set((state) => {
      const accepted = new Set(state.acceptedCodes);
      const rejected = new Set(state.rejectedCodes);
      accepted.add(code);
      rejected.delete(code);
      return { acceptedCodes: accepted, rejectedCodes: rejected };
    }),

  rejectCode: (code) =>
    set((state) => {
      const accepted = new Set(state.acceptedCodes);
      const rejected = new Set(state.rejectedCodes);
      rejected.add(code);
      accepted.delete(code);
      return { acceptedCodes: accepted, rejectedCodes: rejected };
    }),

  resetCodeDecision: (code) =>
    set((state) => {
      const accepted = new Set(state.acceptedCodes);
      const rejected = new Set(state.rejectedCodes);
      accepted.delete(code);
      rejected.delete(code);
      return { acceptedCodes: accepted, rejectedCodes: rejected };
    }),

  clearSession: () =>
    set({
      dischargeText: "",
      predictionResult: null,
      selectedCode: null,
      acceptedCodes: new Set(),
      rejectedCodes: new Set(),
    }),
}));
