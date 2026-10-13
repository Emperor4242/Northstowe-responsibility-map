export const problemTypes = [
  ['green', 'Grass, trees & planting'],
  ['water', 'Lakes & drainage'],
  ['roads', 'Roads & paths'],
  ['lighting', 'Lighting'],
  ['play', 'Play & sports'],
  ['bins', 'Emptying public bins'],
  ['waste', 'Litter & fly-tipping'],
  ['facilities', 'Community facilities'],
];
export type Scope = {
  org: string;
  categories: string[];
  note: string;
  caveat?: string | null;
  evidence?: string;
  scopeLabels?: Record<string, string>;
  detailTags?: string[];
  confirmedAt?: string | null;
  scopeType?: string;
  reviewDue?: string;
};
export const detailOptions = [
  ['all', 'All tasks'],
  ['playing-surface', 'Playing turf / sports fences'],
  ['pitch-base', 'Pitch base / shock pads'],
  ['carpark-care', 'Car-park routine care / cleaning'],
  ['carpark-surface', 'Car-park surface / markings'],
  ['ev-charging', 'EV charge points'],
  ['facility-grounds', 'Pavilion and its landscaping'],
  ['sports-equipment', 'Sports equipment / structures'],
  ['accessway', 'Western Park accessway'],
];
export function scopeMatches(
  r: Scope,
  issues: string[],
  org = 'all',
  detail = 'all',
) {
  return (
    (org === 'all' || r.org === org) &&
    r.categories.some((c) => issues.includes(c)) &&
    (detail === 'all' || !!r.detailTags?.includes(detail))
  );
}
export function displayDate(date: string) {
  return new Date(date + 'T12:00:00Z').toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}
export function evidenceText(r: Scope) {
  const label =
    r.evidence === 'confirmed'
      ? 'Organisation-confirmed scope'
      : r.evidence === 'confirmed-land'
        ? 'Land contact confirmed; service details pending'
        : r.evidence === 'confirmed-operator'
          ? 'Operator confirmed; service scope to check'
          : r.evidence === 'historical'
            ? 'Historical record; confirm current scope'
            : r.evidence === 'enquiry'
              ? 'Enquiry contact; service unconfirmed'
              : 'Responsibility identified in published source';
  return label + (r.confirmedAt ? ' · ' + displayDate(r.confirmedAt) : '');
}
export type AreaSummary = {
  name: string;
  status: string;
  context?: boolean;
  responsibilities: Scope[];
};
export function responsibilitySummary(
  area: AreaSummary,
  issues: string[],
  org = 'all',
  detail = 'all',
) {
  return area.responsibilities
    .filter((r) => scopeMatches(r, issues, org, detail))
    .map((r) => ({
      org: r.org,
      label:
        r.evidence === 'confirmed-land'
          ? 'Land contact; ask about'
          : r.evidence === 'confirmed-operator'
            ? 'Operator contact for'
            : area.context || r.evidence === 'enquiry'
              ? 'Enquiry contact for'
              : area.status === 'uncertain' || r.evidence === 'historical'
                ? 'Published contact — confirm scope'
                : 'Responsible for',
      tasks: r.categories
        .filter((c) => issues.includes(c))
        .map(
          (c) =>
            r.scopeLabels?.[c] ||
            problemTypes.find((p) => p[0] === c)?.[1] ||
            c,
        ),
      caveat: r.caveat,
      evidenceText: evidenceText(r),
      confirmedAt: r.confirmedAt,
    }));
}
export function areaEvidenceLabel(
  area: AreaSummary,
  issues: string[],
  org = 'all',
  detail = 'all',
) {
  const rows = area.responsibilities.filter((r) =>
    scopeMatches(r, issues, org, detail),
  );
  if (rows.length && rows.every((r) => r.evidence === 'confirmed'))
    return 'Organisation-confirmed task scope';
  if (rows.some((r) => r.evidence === 'confirmed'))
    return 'Mixed evidence — check each task';
  if (rows.length && rows.every((r) => r.evidence === 'confirmed-land'))
    return 'Land contact confirmed; services pending';
  if (rows.length && rows.every((r) => r.evidence === 'enquiry'))
    return 'Enquiry route; service unconfirmed';
  if (rows.some((r) => r.evidence === 'confirmed-operator'))
    return 'Operator role confirmed; check service scope';
  return area.context
    ? 'Broad enquiry area'
    : area.status === 'published'
      ? 'Responsibility identified in source'
      : 'Confirmation needed';
}
/** Separate panes ensure road strokes stay visible above land-area polygons. */
export function mapPane(geometryType: string, context = false) {
  return context
    ? 'enquiryAreas'
    : geometryType.includes('Line')
      ? 'responsibilityRoads'
      : geometryType.includes('Point')
        ? 'responsibilityPoints'
        : 'responsibilityAreas';
}
