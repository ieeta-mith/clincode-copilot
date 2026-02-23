from fastapi import APIRouter, Depends, Query

from app.dependencies import AppState, get_app_state
from app.errors import ClinCodeError
from app.schemas import ICDCode, ICDCodeSearchResponse

router = APIRouter(tags=["codes"])


@router.get("/codes", response_model=ICDCodeSearchResponse)
def list_codes(
    q: str = Query(default="", description="Search term for code or description"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    state: AppState = Depends(get_app_state),
) -> ICDCodeSearchResponse:
    if q:
        items, total = state.icd_dictionary.search(q, offset, limit)
    else:
        items, total = state.icd_dictionary.get_all(offset, limit)

    codes = [ICDCode(code=code, description=desc) for code, desc in items]
    return ICDCodeSearchResponse(codes=codes, total=total)


@router.get("/codes/{code}", response_model=ICDCode)
def get_code(code: str, state: AppState = Depends(get_app_state)) -> ICDCode:
    description = state.icd_dictionary.get_description(code)
    if description == "Unknown code":
        raise ClinCodeError(f"ICD code '{code}' not found", status_code=404)
    return ICDCode(code=code, description=description)
