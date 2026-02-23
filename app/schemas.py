from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=50)
    min_freq: int = Field(default=0, ge=0)


class ICDPrediction(BaseModel):
    code: str
    description: str
    score: float
    la_score: float
    knn_score: float
    rank: int


class PredictionResponse(BaseModel):
    predictions: list[ICDPrediction]
    prediction_count: int


class ChunkAttention(BaseModel):
    chunk_index: int
    chunk_text: str
    attention_weight: float


class DetailedICDPrediction(BaseModel):
    code: str
    description: str
    score: float
    la_score: float
    knn_score: float
    rank: int
    chunk_attentions: list[ChunkAttention] | None


class DetailedPredictionResponse(BaseModel):
    predictions: list[DetailedICDPrediction]
    prediction_count: int
    chunk_count: int
    chunk_texts: list[str]


class SimilarPatient(BaseModel):
    admission_id: int | None
    similarity: float
    shared_codes: list[str]


class PerCodeNeighbors(BaseModel):
    code: str
    description: str
    similar_patients: list[SimilarPatient]


class SimilarPatientsRequest(BaseModel):
    text: str = Field(..., min_length=50)
    codes: list[str] = Field(default_factory=list)
    min_freq: int = Field(default=0, ge=0)
    neighbor_count: int = Field(default=50, ge=1, le=200)


class SimilarPatientsResponse(BaseModel):
    per_code_neighbors: list[PerCodeNeighbors]


class ICDCode(BaseModel):
    code: str
    description: str


class ICDCodeSearchResponse(BaseModel):
    codes: list[ICDCode]
    total: int


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    code_count: int
