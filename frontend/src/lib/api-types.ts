export interface PredictionRequest {
  text: string;
  min_freq?: number;
}

export interface ICDPrediction {
  code: string;
  description: string;
  score: number;
  la_score: number;
  knn_score: number;
  rank: number;
}

export interface PredictionResponse {
  predictions: ICDPrediction[];
  prediction_count: number;
}

export interface ChunkAttention {
  chunk_index: number;
  chunk_text: string;
  attention_weight: number;
}

export interface DetailedICDPrediction {
  code: string;
  description: string;
  score: number;
  la_score: number;
  knn_score: number;
  rank: number;
  chunk_attentions: ChunkAttention[] | null;
}

export interface DetailedPredictionResponse {
  predictions: DetailedICDPrediction[];
  prediction_count: number;
  chunk_count: number;
  chunk_texts: string[];
}

export interface SimilarPatient {
  admission_id: number | null;
  similarity: number;
  shared_codes: string[];
}

export interface PerCodeNeighbors {
  code: string;
  description: string;
  similar_patients: SimilarPatient[];
}

export interface SimilarPatientsRequest {
  text: string;
  codes?: string[];
  min_freq?: number;
  neighbor_count?: number;
}

export interface SimilarPatientsResponse {
  per_code_neighbors: PerCodeNeighbors[];
}

export interface ICDCode {
  code: string;
  description: string;
}

export interface ICDCodeSearchResponse {
  codes: ICDCode[];
  total: number;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  code_count: number;
}
