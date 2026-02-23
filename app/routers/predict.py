from fastapi import APIRouter, Depends

from app.dependencies import AppState, get_app_state
from app.schemas import (
    PredictionRequest,
    PredictionResponse,
    DetailedPredictionResponse,
)
from app.services.prediction import run_prediction, run_detailed_prediction

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    request: PredictionRequest,
    state: AppState = Depends(get_app_state),
) -> PredictionResponse:
    return run_prediction(state, request.text, request.min_freq)


@router.post("/predict/detailed", response_model=DetailedPredictionResponse)
def predict_detailed(
    request: PredictionRequest,
    state: AppState = Depends(get_app_state),
) -> DetailedPredictionResponse:
    return run_detailed_prediction(state, request.text, request.min_freq)
