import numpy as np

from icd_hybrid.data.text_preprocessor import normalize_clinical_text

from app.dependencies import AppState
from app.schemas import (
    SimilarPatientsRequest,
    SimilarPatientsResponse,
    PerCodeNeighbors,
    SimilarPatient,
)


def find_similar_patients_per_code(
    state: AppState,
    request: SimilarPatientsRequest,
) -> SimilarPatientsResponse:
    text_clean = normalize_clinical_text(request.text, handle_phi=True)

    chunks = state.predictor.chunker.chunk(text_clean, state.predictor.encoder.tokenizer)
    chunks = chunks[:state.predictor.max_chunks]

    chunk_embeddings = state.predictor.encoder.encode(
        chunks, batch_size=32, show_progress=False
    )
    mean_embedding = np.mean(chunk_embeddings, axis=0)

    neighbors = state.predictor.knn.get_neighbors(
        mean_embedding, k=request.neighbor_count
    )

    target_codes = request.codes
    if not target_codes:
        raw_predictions = state.predictor.predict(request.text, min_freq=request.min_freq)
        target_codes = [p["code"] for p in raw_predictions]

    target_code_set = set(target_codes)

    per_code_results = []
    for code in target_codes:
        matching_neighbors = [n for n in neighbors if code in n.codes]

        similar_patients = [
            SimilarPatient(
                admission_id=n.admission_id,
                similarity=n.similarity,
                shared_codes=[c for c in n.codes if c in target_code_set],
            )
            for n in matching_neighbors
        ]

        per_code_results.append(
            PerCodeNeighbors(
                code=code,
                description=state.icd_dictionary.get_description(code),
                similar_patients=similar_patients,
            )
        )

    return SimilarPatientsResponse(per_code_neighbors=per_code_results)
