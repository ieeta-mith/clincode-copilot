from dataclasses import dataclass

from fastapi import Request

from icd_hybrid.predictor import ICDPredictor

from app.config import Settings
from app.services.icd_dictionary import ICDDictionaryService


@dataclass
class AppState:
    predictor: ICDPredictor
    icd_dictionary: ICDDictionaryService
    settings: Settings

    @classmethod
    def load(cls, settings: Settings) -> "AppState":
        predictor = ICDPredictor(
            model_dir=str(settings.model_dir),
            device=settings.device,
            max_chunks=settings.max_chunks,
        )

        icd_dictionary = ICDDictionaryService.load(settings.icd_dictionary_path)

        return cls(
            predictor=predictor,
            icd_dictionary=icd_dictionary,
            settings=settings,
        )


def get_app_state(request: Request) -> AppState:
    state = request.app.state.app_state
    if state is None:
        from app.errors import ClinCodeError
        raise ClinCodeError("Models not loaded", status_code=503)
    return state
