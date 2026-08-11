/* POLIS case-workflow demonstrator — three frozen study sites.
   Chicago: New ERA Trail corridor (OSM way 624189839) with live movement.
   London: Mitre Yard brownfield (OSM way 49601059), multi-constraint case.
   Suzhou: pocket retrofit parcel (OSM way 741252447), low-complexity anchor.
   All analytical records are illustrative demonstrator values. */
import type { LngLat } from './geo';

export type Role = 'elder' | 'wheel' | 'family' | 'commuter' | 'bike';
export type CaseId = 'suzhou' | 'london' | 'chicago';

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

export interface StepView { longitude: number; latitude: number; zoom: number; pitch: number; bearing: number }

export interface Scenario {
  id: CaseId;
  name: string;
  chip: string;
  source: string;
  center: LngLat;
  analyticalEnvelopeM: number;
  sizeScale: number;         // scales built geometry for small sites
  hasMovement: boolean;
  heat: HeatZone[];
  vul: HeatZone[];
  needs: Need[];
  route: LngLat[];
  implemented: LngLat[];
  reviewPoint: LngLat;
  designPoints: LngLat[];
  benches: LngLat[];
  spatialThreshold: number;
  review: string;
  views: StepView[];         // one camera per pipeline step
  contextView: StepView;
  closingView: StepView;
}

/* ---------------- Chicago · New ERA Trail (frozen OSM way 624189839) ---------------- */

const NEW_ERA_ALIGNMENT: LngLat[] = [
  [-87.6764078, 41.7876116], [-87.6742425, 41.7876362],
  [-87.6740119, 41.7876387], [-87.6730422, 41.7876506],
  [-87.6727942, 41.7876537], [-87.6718300, 41.7876680],
  [-87.6715805, 41.7876717], [-87.6706096, 41.7876837],
  [-87.6703681, 41.7876867], [-87.6693932, 41.7877019],
  [-87.6691531, 41.7877057], [-87.6669712, 41.7877363],
  [-87.6667311, 41.7877397], [-87.6646016, 41.7877635],
];

const CHICAGO: Scenario = {
  id: 'chicago',
  name: 'Chicago · selected New ERA Trail corridor',
  chip: 'Chicago · New ERA Trail',
  source: 'OpenStreetMap way 624189839',
  center: [-87.67050, 41.78769],
  analyticalEnvelopeM: 40,
  sizeScale: 1,
  hasMovement: true,

  heat: [
    { center: [-87.67445, 41.78765], rx: 235, ry: 125, severity: 0.92 },
    { center: [-87.67055, 41.78769], rx: 225, ry: 115, severity: 0.74 },
    { center: [-87.66655, 41.78774], rx: 190, ry: 105, severity: 0.58 },
  ],
  vul: [
    { center: [-87.67410, 41.78764], rx: 180, ry: 100, severity: 0.85 },
    { center: [-87.67015, 41.78770], rx: 195, ry: 105, severity: 0.95 },
    { center: [-87.66615, 41.78775], rx: 160, ry: 95, severity: 0.72 },
  ],
  needs: [
    { id: 'R1', pos: [-87.67424, 41.78764], type: 'elder', label: 'Shade', cost: 8.4, baseAccess: 0.46, protected: true, window: [2027, 2029], gainShade: 0.9, gainSeat: 0.6 },
    { id: 'R2', pos: [-87.67061, 41.78768], type: 'wheel', label: 'Access', cost: 6.2, baseAccess: 0.38, protected: true, window: [2027, 2028], gainShade: 0.3, gainSeat: 0.4 },
    { id: 'R3', pos: [-87.66673, 41.78774], type: 'family', label: 'Green access', cost: 9.8, baseAccess: 0.61, protected: false, window: [2028, 2030], gainShade: 0.6, gainSeat: 0.5 },
    { id: 'R4', pos: [-87.67158, 41.78767], type: 'family', label: 'Safe crossing', cost: 5.6, baseAccess: 0.57, protected: false, window: [2027, 2028], gainShade: 0.2, gainSeat: 0.2 },
  ],
  route: NEW_ERA_ALIGNMENT,
  implemented: NEW_ERA_ALIGNMENT.map(([lng, lat]) => [lng, lat + 0.00016] as LngLat),
  reviewPoint: [-87.67061, 41.78784],
  designPoints: [
    [-87.67535, 41.78762], [-87.67304, 41.78765],
    [-87.67158, 41.78767], [-87.67037, 41.78769],
    [-87.66915, 41.78771], [-87.66697, 41.78774],
    [-87.66535, 41.78776],
  ],
  benches: [
    [-87.67355, 41.78764], [-87.67061, 41.78768], [-87.66775, 41.78773],
  ],
  spatialThreshold: 330,
  review: 'Controlled implementation alignment exceeds the demonstrator tolerance.',
  views: [
    { longitude: -87.67050, latitude: 41.78769, zoom: 15.05, pitch: 52, bearing: -24 },
    { longitude: -87.67200, latitude: 41.78770, zoom: 15.25, pitch: 50, bearing: -24 },
    { longitude: -87.67190, latitude: 41.78771, zoom: 15.08, pitch: 47, bearing: -24 },
    { longitude: -87.67240, latitude: 41.78770, zoom: 15.50, pitch: 48, bearing: -26 },
    { longitude: -87.67100, latitude: 41.78770, zoom: 15.20, pitch: 50, bearing: -24 },
    { longitude: -87.67000, latitude: 41.78771, zoom: 15.60, pitch: 57, bearing: -30 },
    { longitude: -87.66950, latitude: 41.78772, zoom: 15.45, pitch: 56, bearing: -26 },
    { longitude: -87.67060, latitude: 41.78785, zoom: 15.55, pitch: 38, bearing: -18 },
  ],
  contextView: { longitude: -87.67050, latitude: 41.78769, zoom: 14.90, pitch: 50, bearing: -24 },
  closingView: { longitude: -87.67050, latitude: 41.78769, zoom: 14.50, pitch: 45, bearing: -28 },
};

/* ---------------- London · Mitre Yard brownfield (frozen OSM way 49601059) ---------------- */

const MITRE_YARD_RING: LngLat[] = [
  [-0.2357765, 51.5267289], [-0.2362448, 51.5272779], [-0.2361130, 51.5273155],
  [-0.2359363, 51.5273693], [-0.2357046, 51.5274322], [-0.2355709, 51.5274057],
  [-0.2351276, 51.5268428], [-0.2350316, 51.5267072], [-0.2346966, 51.5263327],
  [-0.2352048, 51.5261679], [-0.2351354, 51.5261548], [-0.2352387, 51.5261272],
  [-0.2357765, 51.5267289],
];

const LONDON: Scenario = {
  id: 'london',
  name: 'London · Mitre Yard brownfield',
  chip: 'London · Mitre Yard',
  source: 'OpenStreetMap way 49601059',
  center: [-0.23552, 51.52679],
  analyticalEnvelopeM: 16,
  sizeScale: 0.42,
  hasMovement: false,

  heat: [
    { center: [-0.23570, 51.52700], rx: 85, ry: 70, severity: 0.88 },
    { center: [-0.23520, 51.52650], rx: 75, ry: 60, severity: 0.72 },
  ],
  vul: [
    { center: [-0.23585, 51.52710], rx: 70, ry: 55, severity: 0.9 },
    { center: [-0.23510, 51.52645], rx: 65, ry: 55, severity: 0.78 },
  ],
  needs: [
    { id: 'R1', pos: [-0.23578, 51.52673], type: 'elder', label: 'Shade', cost: 8.9, baseAccess: 0.44, protected: true, window: [2027, 2029], gainShade: 0.85, gainSeat: 0.55 },
    { id: 'R2', pos: [-0.23560, 51.52740], type: 'wheel', label: 'Step-free access', cost: 7.1, baseAccess: 0.36, protected: true, window: [2027, 2028], gainShade: 0.3, gainSeat: 0.4 },
    { id: 'R3', pos: [-0.23495, 51.52643], type: 'family', label: 'Green access', cost: 10.4, baseAccess: 0.58, protected: false, window: [2028, 2030], gainShade: 0.6, gainSeat: 0.5 },
    { id: 'R4', pos: [-0.23525, 51.52681], type: 'family', label: 'Safe crossing', cost: 6.3, baseAccess: 0.55, protected: false, window: [2027, 2028], gainShade: 0.2, gainSeat: 0.25 },
  ],
  route: MITRE_YARD_RING,
  implemented: MITRE_YARD_RING.map(([lng, lat]) => [lng + 0.00010, lat + 0.00007] as LngLat),
  reviewPoint: [-0.23560, 51.52740],
  designPoints: [
    [-0.23590, 51.52705], [-0.23575, 51.52732], [-0.23545, 51.52715],
    [-0.23525, 51.52685], [-0.23505, 51.52655], [-0.23520, 51.52628],
  ],
  benches: [
    [-0.23570, 51.52690], [-0.23535, 51.52700], [-0.23510, 51.52640],
  ],
  spatialThreshold: 120,
  review: 'Controlled implementation alignment exceeds the demonstrator tolerance.',
  views: [
    { longitude: -0.23552, latitude: 51.52679, zoom: 16.65, pitch: 52, bearing: -32 },
    { longitude: -0.23560, latitude: 51.52690, zoom: 17.15, pitch: 50, bearing: -32 },
    { longitude: -0.23548, latitude: 51.52684, zoom: 16.95, pitch: 47, bearing: -32 },
    { longitude: -0.23565, latitude: 51.52700, zoom: 17.15, pitch: 48, bearing: -34 },
    { longitude: -0.23550, latitude: 51.52682, zoom: 17.00, pitch: 50, bearing: -32 },
    { longitude: -0.23548, latitude: 51.52680, zoom: 17.35, pitch: 57, bearing: -38 },
    { longitude: -0.23545, latitude: 51.52683, zoom: 17.15, pitch: 56, bearing: -34 },
    { longitude: -0.23552, latitude: 51.52695, zoom: 17.30, pitch: 38, bearing: -26 },
  ],
  contextView: { longitude: -0.23552, latitude: 51.52679, zoom: 16.45, pitch: 50, bearing: -32 },
  closingView: { longitude: -0.23552, latitude: 51.52679, zoom: 16.05, pitch: 45, bearing: -36 },
};

/* ---------------- Suzhou · pocket retrofit parcel (frozen OSM way 741252447) ---------------- */

const SUZHOU_RING: LngLat[] = [
  [120.5868226, 31.2868580], [120.5865920, 31.2866861], [120.5865611, 31.2866918],
  [120.5862071, 31.2871033], [120.5861802, 31.2871560], [120.5861688, 31.2871909],
  [120.5861601, 31.2872328], [120.5861548, 31.2872786], [120.5861541, 31.2873055],
  [120.5861588, 31.2873290], [120.5861977, 31.2874219], [120.5862245, 31.2874505],
  [120.5862540, 31.2874620], [120.5862808, 31.2874620], [120.5863090, 31.2874585],
  [120.5863318, 31.2874436], [120.5868226, 31.2868580],
];

const SUZHOU: Scenario = {
  id: 'suzhou',
  name: 'Suzhou · pocket retrofit parcel',
  chip: 'Suzhou · pocket retrofit',
  source: 'OpenStreetMap way 741252447',
  center: [120.58648, 31.28709],
  analyticalEnvelopeM: 14,
  sizeScale: 0.36,
  hasMovement: false,

  heat: [
    { center: [120.58660, 31.28695], rx: 65, ry: 55, severity: 0.66 },
    { center: [120.58628, 31.28727], rx: 55, ry: 48, severity: 0.52 },
  ],
  vul: [
    { center: [120.58668, 31.28690], rx: 60, ry: 50, severity: 0.74 },
    { center: [120.58622, 31.28732], rx: 50, ry: 45, severity: 0.6 },
  ],
  needs: [
    { id: 'R1', pos: [120.58663, 31.28689], type: 'elder', label: 'Shade', cost: 7.2, baseAccess: 0.52, protected: true, window: [2027, 2027], gainShade: 0.9, gainSeat: 0.6 },
    { id: 'R2', pos: [120.58623, 31.28715], type: 'wheel', label: 'Access', cost: 5.4, baseAccess: 0.41, protected: true, window: [2028, 2028], gainShade: 0.35, gainSeat: 0.45 },
    { id: 'R3', pos: [120.58626, 31.28743], type: 'family', label: 'Play space', cost: 8.6, baseAccess: 0.63, protected: false, window: [2029, 2029], gainShade: 0.55, gainSeat: 0.5 },
    { id: 'R4', pos: [120.58670, 31.28687], type: 'commuter', label: 'Cool route', cost: 4.8, baseAccess: 0.66, protected: false, window: [2027, 2027], gainShade: 0.3, gainSeat: 0.2 },
  ],
  route: SUZHOU_RING,
  implemented: SUZHOU_RING.map(([lng, lat]) => [lng + 0.00008, lat + 0.00006] as LngLat),
  reviewPoint: [120.58622, 31.28733],
  designPoints: [
    [120.58666, 31.28685], [120.58650, 31.28700], [120.58636, 31.28715],
    [120.58625, 31.28728], [120.58628, 31.28742],
  ],
  benches: [
    [120.58658, 31.28692], [120.58630, 31.28722], [120.58630, 31.28740],
  ],
  spatialThreshold: 40,
  review: 'Controlled implementation alignment exceeds the demonstrator tolerance.',
  views: [
    { longitude: 120.58648, latitude: 31.28709, zoom: 17.20, pitch: 52, bearing: -28 },
    { longitude: 120.58644, latitude: 31.28712, zoom: 17.70, pitch: 50, bearing: -28 },
    { longitude: 120.58648, latitude: 31.28710, zoom: 17.50, pitch: 47, bearing: -28 },
    { longitude: 120.58638, latitude: 31.28718, zoom: 17.70, pitch: 48, bearing: -30 },
    { longitude: 120.58648, latitude: 31.28710, zoom: 17.55, pitch: 50, bearing: -28 },
    { longitude: 120.58646, latitude: 31.28708, zoom: 17.90, pitch: 57, bearing: -34 },
    { longitude: 120.58645, latitude: 31.28711, zoom: 17.70, pitch: 56, bearing: -30 },
    { longitude: 120.58640, latitude: 31.28722, zoom: 17.85, pitch: 38, bearing: -22 },
  ],
  contextView: { longitude: 120.58648, latitude: 31.28709, zoom: 17.00, pitch: 50, bearing: -28 },
  closingView: { longitude: 120.58648, latitude: 31.28709, zoom: 16.60, pitch: 45, bearing: -32 },
};

export const CASES: Record<CaseId, Scenario> = { suzhou: SUZHOU, london: LONDON, chicago: CHICAGO };
export const CASE_ORDER: CaseId[] = ['suzhou', 'london', 'chicago'];

/* ---------------- Chicago movement network (live simulation runs on this case only) ---------------- */

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
