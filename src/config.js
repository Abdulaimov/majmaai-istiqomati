// The residential complex «Маҷмааи истиқоматӣ» (Dushanbe): eleven blocks on the genplan. Block К is
// built in full (exterior), the others stand as white models of their size until they are made.
// Placement, heights and the site's lamps, trees, cars and people come from the Blender build
// (model/complex.json, blender/build_mi.py).
import complex from './model/complex.json';

export const MODEL_URL = `${import.meta.env.BASE_URL}models/mi.glb`;

// Site plan coordinates (metres, x east, y north) -> scene (x, z) with the site centre at the origin.
const [CX, CY] = complex.site_centre;
export const toScene = (x, y) => ({ x: x - CX, z: -(y - CY) });

export const TOWERS = complex.towers;
export const towerByKey = Object.fromEntries(TOWERS.map((t) => [t.key, t]));
export const TREES = { protos: complex.tree_protos ?? [], list: complex.trees ?? [], placed: complex.trees_placed ?? [] };
export const CARS = complex.cars ?? [];
export const PEOPLE = complex.people ?? [];
export const PLACES = complex.labels ?? [];
export const LAMPS = complex.lamps ?? [];
export const SHOPS = complex.shops ?? [];
// the modelled ground [x0, y0, x1, y1] (site metres): the city round it stays off it (world.js)
export const REGION = complex.region ?? [-300, -150, 150, 330];
// the order of the blocks on the genplan: the row along the street, the row along the inner street, Л, М
export const ORDER = ['A', 'B', 'V', 'G', 'D', 'E', 'J', 'I', 'K', 'L', 'M'];
