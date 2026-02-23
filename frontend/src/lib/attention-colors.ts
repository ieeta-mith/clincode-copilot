export function attentionToHsl(weight: number, maxWeight: number): string {
  if (maxWeight <= 0) return "transparent";
  const normalized = Math.min(weight / maxWeight, 1);
  const hue = 45;
  const saturation = 90;
  const lightness = 100 - normalized * 40;
  const alpha = normalized * 0.6;
  return `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`;
}

export function attentionToClass(weight: number, maxWeight: number): string {
  if (maxWeight <= 0) return "";
  const normalized = Math.min(weight / maxWeight, 1);
  if (normalized < 0.2) return "bg-amber-50";
  if (normalized < 0.4) return "bg-amber-100";
  if (normalized < 0.6) return "bg-amber-200";
  if (normalized < 0.8) return "bg-amber-300";
  return "bg-amber-400";
}
