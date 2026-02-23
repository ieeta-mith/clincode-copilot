import type {
  PredictionRequest,
  DetailedPredictionResponse,
  SimilarPatientsRequest,
  SimilarPatientsResponse,
  ICDCodeSearchResponse,
  HealthResponse,
} from "./api-types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export function predictDetailed(
  body: PredictionRequest
): Promise<DetailedPredictionResponse> {
  return request("/api/predict/detailed", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function fetchSimilarPatients(
  body: SimilarPatientsRequest
): Promise<SimilarPatientsResponse> {
  return request("/api/similar-patients", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function searchCodes(query: string): Promise<ICDCodeSearchResponse> {
  return request(`/api/codes?q=${encodeURIComponent(query)}`);
}

export function fetchHealth(): Promise<HealthResponse> {
  return request("/health");
}
