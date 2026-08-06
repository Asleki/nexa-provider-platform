/** Human-readable coordinate labels derived from numeric grid values. */
export function formatLongitude(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < -180 || number > 180) throw new RangeError("longitude label value is invalid");
  if (Object.is(number, -0) || number === 0) return "0°";
  return `${Math.abs(number)}°${number < 0 ? "W" : "E"}`;
}

export function formatLatitude(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < -90 || number > 90) throw new RangeError("latitude label value is invalid");
  if (Object.is(number, -0) || number === 0) return "0°";
  return `${Math.abs(number)}°${number < 0 ? "S" : "N"}`;
}
