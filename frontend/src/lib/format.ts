export function formatScore(score: number): string {
  return (score * 100).toFixed(1) + "%";
}

export function formatSimilarity(similarity: number): string {
  return (similarity * 100).toFixed(0) + "%";
}
