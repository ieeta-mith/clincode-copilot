from fastapi import APIRouter, Depends

from app.dependencies import AppState, get_app_state
from app.schemas import SimilarPatientsRequest, SimilarPatientsResponse
from app.services.neighbor_lookup import find_similar_patients_per_code

router = APIRouter(tags=["similar-patients"])


@router.post("/similar-patients", response_model=SimilarPatientsResponse)
def similar_patients(
    request: SimilarPatientsRequest,
    state: AppState = Depends(get_app_state),
) -> SimilarPatientsResponse:
    return find_similar_patients_per_code(state, request)
