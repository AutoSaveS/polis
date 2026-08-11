/* POLIS case-workflow demonstrator — selected New ERA Trail segment, Chicago.
   The alignment is frozen OSM way 624189839; analytical records are illustrative. */
import type { LngLat } from './geo';

export type Role = 'elder' | 'wheel' | 'family' | 'commuter' | 'bike';

export interface Need {
  id: string;
  pos: LngLat;
  type: Role;
  label: string;
  cost: number;             // illustrative $M scenario value
  baseAccess: number;       // internal workflow state, 0..1
  protected: boolean;
  window: [number, number]; // illustrative construction window (years)
  gainShade: number;
  gainSeat: number;
}

export interface HeatZone { center: LngLat; rx: number; ry: number; severity: number }

/** Frozen geometry from OpenStreetMap way 624189839 (retrieved 10 Aug 2026). */
const NEW_ERA_ALIGNMENT: LngLat[] = [
  [-87.6764078, 41.7876116], [-87.6742425, 41.7876362],
  [-87.6740119, 41.7876387], [-87.6730422, 41.7876506],
  [-87.6727942, 41.7876537], [-87.6718300, 41.7876680],
  [-87.6715805, 41.7876717], [-87.6706096, 41.7876837],
  [-87.6703681, 41.7876867], [-87.6693932, 41.7877019],
  [-87.6691531, 41.7877057], [-87.6669712, 41.7877363],
  [-87.6667311, 41.7877397], [-87.6646016, 41.7877635],
];

export const SCENARIO = {
  name: 'Chicago · selected New ERA Trail corridor',
  center: [-87.67050, 41.78769] as LngLat,
  source: 'OpenStreetMap way 624189839',
  analyticalEnvelopeM: 40,

  // Frozen demonstrator fields, not observed resident or Experiment 1 outcomes.
  heat: [
    { center: [-87.67445, 41.78765], rx: 235, ry: 125, severity: 0.92 },
    { center: [-87.67055, 41.78769], rx: 225, ry: 115, severity: 0.74 },
    { center: [-87.66655, 41.78774], rx: 190, ry: 105, severity: 0.58 },
  ] as HeatZone[],

  vul: [
    { center: [-87.67410, 41.78764], rx: 180, ry: 100, severity: 0.85 },
    { center: [-87.67015, 41.78770], rx: 195, ry: 105, severity: 0.95 },
    { center: [-87.66615, 41.78775], rx: 160, ry: 95, severity: 0.72 },
  ] as HeatZone[],

  needs: [
    { id: 'R1', pos: [-87.67424, 41.78764], type: 'elder', label: 'Shade', cost: 8.4, baseAccess: 0.46, protected: true, window: [2027, 2029], gainShade: 0.9, gainSeat: 0.6 },
    { id: 'R2', pos: [-87.67061, 41.78768], type: 'wheel', label: 'Access', cost: 6.2, baseAccess: 0.38, protected: true, window: [2027, 2028], gainShade: 0.3, gainSeat: 0.4 },
    { id: 'R3', pos: [-87.66673, 41.78774], type: 'family', label: 'Green access', cost: 9.8, baseAccess: 0.61, protected: false, window: [2028, 2030], gainShade: 0.6, gainSeat: 0.5 },
    { id: 'R4', pos: [-87.67158, 41.78767], type: 'family', label: 'Safe crossing', cost: 5.6, baseAccess: 0.57, protected: false, window: [2027, 2028], gainShade: 0.2, gainSeat: 0.2 },
  ] as Need[],

  route: NEW_ERA_ALIGNMENT,

  // Controlled implementation-deviation case used only to demonstrate review.
  implemented: NEW_ERA_ALIGNMENT.map(([lng, lat]) => [lng, lat + 0.00016] as LngLat),
  reviewPoint: [-87.67061, 41.78784] as LngLat,

  designPoints: [
    [-87.67535, 41.78762], [-87.67304, 41.78765],
    [-87.67158, 41.78767], [-87.67037, 41.78769],
    [-87.66915, 41.78771], [-87.66697, 41.78774],
    [-87.66535, 41.78776],
  ] as LngLat[],

  benches: [
    [-87.67355, 41.78764], [-87.67061, 41.78768], [-87.66775, 41.78773],
  ] as LngLat[],

  spatialThreshold: 330,
  review: 'Controlled implementation alignment exceeds the demonstrator tolerance.',
};

/** Nearby movement network from OSM street geometry around the selected segment. */
export const PED_PATHS: LngLat[][] = [
  // West 58th Street, north of the proposed trail.
  [[-87.6741459, 41.7884472], [-87.6729482, 41.7884675], [-87.6705166, 41.7884926], [-87.6680979, 41.7885228], [-87.6656513, 41.7885534], [-87.6645036, 41.7885678]],
  // West 59th Street, south of the proposed trail.
  [[-87.6766852, 41.7865990], [-87.6740971, 41.7866255], [-87.6716800, 41.7866577], [-87.6692682, 41.7866898], [-87.6668322, 41.7867222], [-87.6643306, 41.7867557]],
  // South Damen Avenue.
  [[-87.6740507, 41.7848896], [-87.6740971, 41.7866255], [-87.6741217, 41.7875466], [-87.6741459, 41.7884472], [-87.6741807, 41.7897448]],
  // South Wood Street.
  [[-87.6692131, 41.7847931], [-87.6692506, 41.7862348], [-87.6692682, 41.7866898], [-87.66929, 41.78770], [-87.66932, 41.78851]],
  // South Paulina Street.
  [[-87.6667829, 41.7848222], [-87.6668202, 41.7862610], [-87.6668322, 41.7867222], [-87.66686, 41.78774], [-87.66688, 41.78854]],
  // South Marshfield Avenue.
  [[-87.6655731, 41.7849982], [-87.6656036, 41.7862742], [-87.6656147, 41.7867384], [-87.66565, 41.78775], [-87.6656513, 41.7885534]],
  // Short connector used by mobility actors at the west access.
  [[-87.6741459, 41.7884472], [-87.67414, 41.78805], [-87.67413, 41.78768], [-87.67410, 41.7866255]],
];

export const CAR_PATHS: LngLat[][] = [
  PED_PATHS[0], PED_PATHS[1], PED_PATHS[2], PED_PATHS[5],
];

/** Cars brake at the two mapped Damen/58th and Damen/59th crossings. */
export const CROSSWALK_ZONES: LngLat[] = [
  [-87.6741459, 41.7884472],
  [-87.6740971, 41.7866255],
];

export const UTILITY: Record<Role, { shade: number; seat: number; detour: number }> = {
  elder: { shade: 0.9, seat: 0.65, detour: 0.15 },
  wheel: { shade: 0.55, seat: 0.45, detour: 0.1 },
  family: { shade: 0.6, seat: 0.4, detour: 0.3 },
  commuter: { shade: 0.2, seat: 0.05, detour: 0.85 },
  bike: { shade: 0.3, seat: 0.05, detour: 0.75 },
};

export const ROLE_SPEED: Record<Role, number> = {
  elder: 0.9, wheel: 1.0, family: 1.1, commuter: 1.45, bike: 3.4,
};

export const ROLE_LABEL: Record<Role, string> = {
  elder: 'Elder resident', wheel: 'Wheelchair user', family: 'Family',
  commuter: 'Commuter', bike: 'Cyclist',
};
