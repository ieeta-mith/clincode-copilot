from app.dependencies import AppState
from app.schemas import (
    PredictionResponse,
    ICDPrediction,
    DetailedPredictionResponse,
    DetailedICDPrediction,
    ChunkAttention,
)


def run_prediction(state: AppState, text: str, min_freq: int) -> PredictionResponse:
    raw_predictions = state.predictor.predict(text, min_freq=min_freq)

    predictions = [
        ICDPrediction(
            code=p["code"],
            description=state.icd_dictionary.get_description(p["code"]),
            score=p["score"],
            la_score=p["la_score"],
            knn_score=p["knn_score"],
            rank=p["rank"],
        )
        for p in raw_predictions
    ]

    return PredictionResponse(
        predictions=predictions,
        prediction_count=len(predictions),
    )


def run_detailed_prediction(
    state: AppState, text: str, min_freq: int
) -> DetailedPredictionResponse:
    raw_result = state.predictor.predict_with_attention(text, min_freq=min_freq)

    predictions = []
    for p in raw_result["predictions"]:
        chunk_attentions = None
        if p["chunk_attention"] is not None:
            chunk_attentions = [
                ChunkAttention(
                    chunk_index=i,
                    chunk_text=raw_result["chunk_texts"][i],
                    attention_weight=w,
                )
                for i, w in enumerate(p["chunk_attention"])
            ]

        predictions.append(
            DetailedICDPrediction(
                code=p["code"],
                description=state.icd_dictionary.get_description(p["code"]),
                score=p["score"],
                la_score=p["la_score"],
                knn_score=p["knn_score"],
                rank=p["rank"],
                chunk_attentions=chunk_attentions,
            )
        )

    return DetailedPredictionResponse(
        predictions=predictions,
        prediction_count=len(predictions),
        chunk_count=raw_result["n_chunks"],
        chunk_texts=raw_result["chunk_texts"],
    )
