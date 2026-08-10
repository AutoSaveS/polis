/* Geo helpers — flat-earth approximation, fine at neighbourhood scale (~41.845°N). */
export type LngLat = [number, number];

export const M_LAT = 111132;               // metres per degree latitude
export const M_LNG = 82920;                // metres per degree longitude at 41.845°N

export function distM(a: LngLat, b: LngLat): number {
  const dx = (a[0] - b[0]) * M_LNG;
  const dy = (a[1] - b[1]) * M_LAT;
  return Math.hypot(dx, dy);
}

export function offsetM(p: LngLat, eastM: number, northM: number): LngLat {
  return [p[0] + eastM / M_LNG, p[1] + northM / M_LAT];
}

export function ellipse(center: LngLat, rxM: number, ryM: number, n = 48): LngLat[] {
  const pts: LngLat[] = [];
  for (let i = 0; i <= n; i++) {
    const a = (i / n) * Math.PI * 2;
    pts.push([center[0] + (Math.cos(a) * rxM) / M_LNG, center[1] + (Math.sin(a) * ryM) / M_LAT]);
  }
  return pts;
}

/** Deterministic PRNG so heat scatter doesn't flicker between re-renders. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Polyline with metre-based arc length parametrisation. */
export class GeoPath {
  readonly pts: LngLat[];
  readonly cum: number[];
  readonly total: number;

  constructor(pts: LngLat[]) {
    this.pts = pts;
    this.cum = [0];
    for (let i = 1; i < pts.length; i++) this.cum.push(this.cum[i - 1] + distM(pts[i - 1], pts[i]));
    this.total = this.cum[this.cum.length - 1];
  }

  pointAt(d: number): LngLat {
    const dd = Math.max(0, Math.min(this.total, d));
    let i = 1;
    while (i < this.cum.length - 1 && this.cum[i] < dd) i++;
    const d0 = this.cum[i - 1], d1 = this.cum[i];
    const t = d1 > d0 ? (dd - d0) / (d1 - d0) : 0;
    const a = this.pts[i - 1], b = this.pts[i];
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  }
}
