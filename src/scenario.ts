/* POLIS scenario — S Kedzie Ave corridor, Little Village, Chicago (real coordinates). */
import type { LngLat } from './geo';

export type Role = 'elder' | 'wheel' | 'family' | 'commuter' | 'bike';

export interface Need {
  id: string;
  pos: LngLat;
  type: Role;
  label: string;
  cost: number;            // $M
  baseAccess: number;      // current access level 0..1
  protected: boolean;
  window: [number, number]; // construction window (years)
  gainShade: number;
  gainSeat: number;
}

export interface HeatZone { center: LngLat; rx: number; ry: number; severity: number }

export const SCENARIO = {
  name: 'Chicago · S Kedzie Ave corridor (Little Village)',
  center: [-87.7047, 41.8452] as LngLat,

  heat: [
    { center: [-87.705, 41.8476], rx: 240, ry: 170, severity: 0.92 },
    { center: [-87.7052, 41.8437], rx: 230, ry: 160, severity: 0.74 },
    { center: [-87.7005, 41.8434], rx: 170, ry: 120, severity: 0.58 },
  ] as HeatZone[],

  vul: [
    { center: [-87.7063, 41.8471], rx: 180, ry: 120, severity: 0.85 },
    { center: [-87.7072, 41.8441], rx: 190, ry: 140, severity: 0.95 },
    { center: [-87.7004, 41.8439], rx: 150, ry: 100, severity: 0.72 },
  ] as HeatZone[],

  needs: [
    { id: 'R1', pos: [-87.7056, 41.8478], type: 'elder', label: 'Shade', cost: 8.4, baseAccess: 0.46, protected: true, window: [2027, 2029], gainShade: 0.9, gainSeat: 0.6 },
    { id: 'R2', pos: [-87.7059, 41.8444], type: 'wheel', label: 'Access', cost: 6.2, baseAccess: 0.38, protected: true, window: [2027, 2028], gainShade: 0.3, gainSeat: 0.4 },
    { id: 'R3', pos: [-87.701, 41.8437], type: 'family', label: 'Green access', cost: 9.8, baseAccess: 0.61, protected: false, window: [2028, 2030], gainShade: 0.6, gainSeat: 0.5 },
    { id: 'R4', pos: [-87.7054, 41.8461], type: 'family', label: 'Safe crossing', cost: 5.6, baseAccess: 0.57, protected: false, window: [2027, 2028], gainShade: 0.2, gainSeat: 0.2 },
  ] as Need[],

  // approved greenway down Kedzie
  route: [
    [-87.7054, 41.8496], [-87.70544, 41.8478], [-87.70548, 41.846],
    [-87.70552, 41.8442], [-87.70556, 41.8424], [-87.70558, 41.8414],
  ] as LngLat[],

  // as-built route, shifted ~18 m west of the approved alignment
  implemented: [
    [-87.70562, 41.8495], [-87.70566, 41.8477], [-87.7057, 41.8459],
    [-87.70574, 41.8441], [-87.70578, 41.8423], [-87.7058, 41.8414],
  ] as LngLat[],

  designPoints: [
    [-87.70533, 41.8488], [-87.70557, 41.8477], [-87.70534, 41.8466],
    [-87.70558, 41.8455], [-87.70535, 41.8444], [-87.70559, 41.8433],
    [-87.70546, 41.842],
  ] as LngLat[],

  benches: [
    [-87.7053, 41.84775], [-87.70532, 41.8464], [-87.70535, 41.8448],
  ] as LngLat[],

  spatialThreshold: 330, // metres under which two records compete for the same street space
  review: 'Built route alignment is shifted west of the approved greenway.',
};

export const PED_PATHS: LngLat[][] = [
  // Kedzie west sidewalk (N–S)
  [[-87.70578, 41.85], [-87.70582, 41.847], [-87.70586, 41.844], [-87.7059, 41.8412]],
  // Kedzie east sidewalk (S–N)
  [[-87.70502, 41.8412], [-87.70506, 41.8445], [-87.7051, 41.8475], [-87.70514, 41.85]],
  // W 24th St sidewalk (W–E)
  [[-87.71, 41.84788], [-87.705, 41.84782], [-87.7, 41.84776]],
  // W 26th St sidewalk (E–W)
  [[-87.7, 41.84448], [-87.705, 41.84442], [-87.71, 41.84436]],
  // W 25th St crosswalk over Kedzie
  [[-87.7064, 41.84612], [-87.7044, 41.84608]],
  // park approach (SE)
  [[-87.7016, 41.843], [-87.7008, 41.8438], [-87.7002, 41.8444]],
  // crossing near the 26th St station
  [[-87.706, 41.8442], [-87.7058, 41.84465]],
];

export const CAR_PATHS: LngLat[][] = [
  [[-87.70528, 41.841], [-87.70524, 41.845], [-87.7052, 41.85]],   // Kedzie NB
  [[-87.70552, 41.85], [-87.70556, 41.845], [-87.7056, 41.841]],   // Kedzie SB
  [[-87.71, 41.848], [-87.7, 41.84788]],                            // W 24th St
  [[-87.7, 41.8443], [-87.71, 41.84418]],                           // W 26th St
];

/** Crosswalk zones: cars brake when a pedestrian is inside. */
export const CROSSWALK_ZONES: LngLat[] = [
  [-87.7054, 41.8461],
  [-87.7059, 41.8444],
];

// role utility weights for route choice: shade gain, seating gain, detour penalty
export const UTILITY: Record<Role, { shade: number; seat: number; detour: number }> = {
  elder: { shade: 0.9, seat: 0.65, detour: 0.15 },
  wheel: { shade: 0.55, seat: 0.45, detour: 0.1 },
  family: { shade: 0.6, seat: 0.4, detour: 0.3 },
  commuter: { shade: 0.2, seat: 0.05, detour: 0.85 },
  bike: { shade: 0.3, seat: 0.05, detour: 0.75 },
};

// metres per second
export const ROLE_SPEED: Record<Role, number> = {
  elder: 0.9, wheel: 1.0, family: 1.1, commuter: 1.45, bike: 3.4,
};

export const ROLE_LABEL: Record<Role, string> = {
  elder: 'Elder resident', wheel: 'Wheelchair user', family: 'Family',
  commuter: 'Commuter', bike: 'Cyclist',
};
