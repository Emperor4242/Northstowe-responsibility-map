import booleanPointInPolygon from '@turf/boolean-point-in-polygon';
import type { Feature, Geometry, Position } from 'geojson';

export type SpatialFeature = Feature<Geometry, { pointRadius?: number } | null>;
function segmentDistance(p: Position, a: Position, b: Position) {
  const dx = (b[0] - a[0]) * 68000,
    dy = (b[1] - a[1]) * 111000;
  const px = (p[0] - a[0]) * 68000,
    py = (p[1] - a[1]) * 111000;
  const t = Math.max(
    0,
    Math.min(1, (px * dx + py * dy) / (dx * dx + dy * dy || 1)),
  );
  return Math.hypot(px - t * dx, py - t * dy);
}
/** Geographic matching, not an assertion of legal extent. Line tolerance is 14 m. */
export function contains(f: SpatialFeature, p: Position): boolean {
  const g = f.geometry;
  if (g.type === 'Polygon' || g.type === 'MultiPolygon')
    return booleanPointInPolygon(p, g);
  if (g.type === 'Point')
    return (
      Math.hypot(
        (g.coordinates[0] - p[0]) * 68000,
        (g.coordinates[1] - p[1]) * 111000,
      ) < (f.properties?.pointRadius || 25)
    );
  const lines =
    g.type === 'MultiLineString'
      ? g.coordinates
      : g.type === 'LineString'
        ? [g.coordinates]
        : [];
  return lines.some((line) =>
    line.slice(1).some((b, i) => segmentDistance(p, line[i], b) < 14),
  );
}
