from fastapi import APIRouter, Depends

from app.dependencies import AppState, get_app_state
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(state: AppState = Depends(get_app_state)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=state.predictor is not None,
        code_count=state.icd_dictionary.code_count,
    )
