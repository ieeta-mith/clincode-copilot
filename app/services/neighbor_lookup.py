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
    chunk_embs, n_chunks = state.predictor.encode_chunks(request.text)

    best_by_idx = {}
    for i in range(n_chunks):
        for n in state.predictor.knn.get_neighbors(chunk_embs[i], k=request.neighbor_count):
            prev = best_by_idx.get(n.index)
            if prev is None or n.similarity > prev.similarity:
                best_by_idx[n.index] = n

    neighbors = sorted(best_by_idx.values(), key=lambda n: n.similarity, reverse=True)

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
