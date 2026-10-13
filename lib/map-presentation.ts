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
};
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
) {
  return area.responsibilities
    .filter(
      (r) =>
        (org === 'all' || r.org === org) &&
        r.categories.some((c) => issues.includes(c)),
    )
    .map((r) => ({
      org: r.org,
      label:
        area.context || r.evidence === 'enquiry'
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
    }));
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
