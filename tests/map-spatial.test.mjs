import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { contains } from '../lib/map-spatial.ts';
import {
  responsibilitySummary,
  mapPane,
  areaEvidenceLabel,
} from '../lib/map-presentation.ts';
const data = JSON.parse(
  readFileSync(
    new URL('../public/data/responsibilities.json', import.meta.url),
    'utf8',
  ),
);
const boundary = JSON.parse(
  readFileSync(
    new URL('../public/data/parish.geojson', import.meta.url),
    'utf8',
  ),
);
const feature = (id) => data.features.find((f) => f.properties.id === id);
const contacts = (p, category) =>
  data.features
    .filter((f) => contains(f, p) && !f.properties.context)
    .flatMap((f) =>
      f.properties.responsibilities
        .filter((r) => r.categories.includes(category))
        .map((r) => r.org),
    );
test('opposite lake estates route water issues to their separately published contacts', () => {
  assert(contacts([0.066365, 52.286729], 'water').includes('aw'));
  assert(contacts([0.07395, 52.278393], 'water').includes('he'));
  assert(!contacts([0.07395, 52.278393], 'water').includes('aw'));
});
test('H4 preserves both open-space and street-tree enquiry scopes', () => {
  const f = feature('parcel-H4');
  assert.deepEqual(
    new Set(
      f.properties.responsibilities
        .filter((r) => r.categories.includes('green'))
        .map((r) => r.org),
    ),
    new Set(['greenbelt', 'vistry']),
  );
  assert(
    f.properties.responsibilities.some((r) =>
      r.caveat.includes('street trees'),
    ),
  );
  assert.equal(f.properties.status, 'uncertain');
});
test('sports pitch is excluded from the surrounding Greenbelt landscape geometry', () => {
  const p = [0.049161, 52.28476];
  assert(contacts(p, 'play').includes('elite'));
  assert(contacts(p, 'green').includes('elite'));
  assert.equal(contains(feature('way-725827725'), p), false);
});
test('prospective adoption is never labelled completed adoption', () => {
  const future = data.features.filter((f) =>
    f.properties.id.startsWith('Section38Streets.'),
  );
  assert.equal(future.length, 2);
  for (const f of future) {
    assert.equal(f.properties.status, 'uncertain');
    assert.match(f.properties.name, /prospective adoption/);
  }
  assert.equal(
    data.features.filter((f) => f.properties.id.startsWith('AdoptedRoads.'))
      .length,
    6,
  );
});
test('exact county light and gully points are returned without expanding ownership across the parish', () => {
  const lights = data.features.filter((f) =>
    f.properties.id.startsWith('StreetLights.'),
  );
  assert.equal(lights.length, 50);
  for (const f of lights) {
    assert(contains(f, f.geometry.coordinates));
    assert(
      !contains(f, [
        f.geometry.coordinates[0] + 0.002,
        f.geometry.coordinates[1],
      ]),
    );
  }
  assert.equal(
    data.features.filter((f) => f.properties.id.startsWith('Gullies.')).length,
    176,
  );
  assert.equal(feature('parish-highways').properties.status, 'uncertain');
});
test('register has unique IDs, sources, categories and a usable contact for every responsibility', () => {
  const ids = data.features.map((f) => f.properties.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const f of data.features)
    for (const r of f.properties.responsibilities) {
      const o = data.organisations[r.org];
      assert(o, f.properties.name);
      assert(o.reportUrl || o.email || o.phone);
      assert(r.sources.length);
      for (const id of r.sources) assert(data.sources[id], id);
      for (const c of r.categories)
        assert(
          [
            'green',
            'water',
            'roads',
            'lighting',
            'play',
            'bins',
            'waste',
            'facilities',
          ].includes(c),
        );
    }
  assert.equal(data.audit.counts.features, data.features.length);
  assert.equal(data.organisations.ntc.email, 'admin@northstowe-tc.gov.uk');
  assert.equal(data.organisations.uc.email, 'Northstowe@urbanandcivic.com');
});

test('hover summaries show only selected tasks and organisations, preserving overlapping scopes', () => {
  const lake = feature('way-725827723').properties;
  const rows = responsibilitySummary(lake, ['roads'], 'aw');
  assert.equal(rows.length, 1);
  assert.equal(rows[0].org, 'aw');
  assert.deepEqual(rows[0].tasks, ['Paths around Bug Hunter Waters']);
  assert.equal(responsibilitySummary(lake, ['roads'], 'he').length, 0);
  const h4 = responsibilitySummary(feature('parcel-H4').properties, ['green']);
  assert.deepEqual(
    new Set(h4.map((r) => r.org)),
    new Set(['greenbelt', 'vistry']),
  );
});

test('public bin emptying is separate and historical/unconfirmed service is labelled honestly', () => {
  const aw = feature('bins-bughunter').properties;
  assert.equal(responsibilitySummary(aw, ['waste']).length, 0);
  assert.match(responsibilitySummary(aw, ['bins'])[0].label, /confirm scope/);
  assert.match(responsibilitySummary(aw, ['bins'])[0].caveat, /March 2025/);
  const unknown = data.features.filter((f) =>
    f.properties.id.startsWith('bin-node-'),
  );
  assert.equal(unknown.length, 5);
  for (const f of unknown)
    assert.equal(
      responsibilitySummary(f.properties, ['bins'])[0].label,
      'Enquiry contact for',
    );
});

test('Homes England main roads have road-layer geometry and a published contact with adoption caveat', () => {
  for (const id of ['stirling-phase2', 'southern-access-road']) {
    const f = feature(id);
    assert.equal(
      mapPane(f.geometry.type, f.properties.context),
      'responsibilityRoads',
    );
    assert(
      f.properties.responsibilities.some(
        (r) => r.org === 'he' && r.categories.includes('roads'),
      ),
    );
    assert.match(f.properties.responsibilities[0].caveat, /adoption/);
  }
  assert.equal(mapPane('Polygon', true), 'enquiryAreas');
  assert.equal(mapPane('Polygon'), 'responsibilityAreas');
  assert.equal(mapPane('Point'), 'responsibilityPoints');
});
test('official parish outline includes western Phase 3B and distinguishes locations beyond the boundary', () => {
  assert(contains(boundary.features[0], [0.043, 52.292]));
  assert(!contains(boundary.features[0], [0.02, 52.285]));
  assert.equal(boundary.features[0].geometry.coordinates[0].length, 574);
  assert.equal(feature('phase3b').properties.context, true);
});

test('Western Park ownership and task maintenance remain distinct', () => {
  const mini = feature('way-952350386').properties;
  assert.equal(mini.landOwner, 'scdc');
  assert.equal(mini.operator, 'elite');
  assert.deepEqual(
    responsibilitySummary(mini, ['play']).map((r) => r.org),
    ['elite'],
  );
  const pitch = feature('way-725332121').properties;
  assert.deepEqual(
    responsibilitySummary(pitch, ['play'], 'all', 'pitch-base').map(
      (r) => r.org,
    ),
    ['scdc'],
  );
  assert.deepEqual(
    responsibilitySummary(pitch, ['play'], 'all', 'playing-surface').map(
      (r) => r.org,
    ),
    ['elite'],
  );
  assert.equal(
    responsibilitySummary(pitch, ['play'], 'elite', 'pitch-base').length,
    0,
  );
  assert.match(areaEvidenceLabel(pitch, ['bins']), /unconfirmed/);
  assert.match(responsibilitySummary(pitch, ['bins'])[0].label, /Enquiry/);
});

test('car-park routine care, structural repairs and EV maintenance have separate contacts', () => {
  const park = feature('western-carpark');
  assert.deepEqual(
    responsibilitySummary(
      park.properties,
      ['roads'],
      'all',
      'carpark-care',
    ).map((r) => r.org),
    ['elite'],
  );
  assert.deepEqual(
    responsibilitySummary(
      park.properties,
      ['roads'],
      'all',
      'carpark-surface',
    ).map((r) => r.org),
    ['scdc'],
  );
  assert.deepEqual(
    responsibilitySummary(
      park.properties,
      ['facilities'],
      'all',
      'ev-charging',
    ).map((r) => r.org),
    ['scdc'],
  );
  assert.equal(
    contains(feature('way-725827725'), park.properties.anchor),
    false,
  );
  assert.equal(
    contains(feature('bins-western'), park.properties.anchor),
    false,
  );
});

test('Homes England broad land scope excludes each named estate/campus exception', () => {
  const he = data.features.filter(
    (f) =>
      f.properties.context &&
      f.properties.responsibilities.some((r) => r.org === 'he'),
  );
  for (const id of ['inholm', 'way-905770539', 'education-campus']) {
    const estate = feature(id);
    for (const f of he)
      assert(
        !contains(f, estate.properties.anchor),
        `${f.properties.id} incorrectly includes ${id}`,
      );
  }
  const phase = feature('way-603146096').properties;
  assert.equal(phase.responsibilities[0].evidence, 'confirmed-land');
  assert.match(responsibilitySummary(phase, ['bins'])[0].label, /Land contact/);
  assert.match(
    responsibilitySummary(phase, ['bins'])[0].evidenceText,
    /service details pending/,
  );
  assert.equal(
    feature('education-campus').properties.responsibilities[0].evidence,
    'confirmed-operator',
  );
  assert.equal(
    feature('inholm').properties.responsibilities[0].evidence,
    'enquiry',
  );
});

test('supplied bin records retain duplicate descriptions and never invent locations or operators', () => {
  const bins = data.binRegister.records;
  assert.equal(bins.length, 48);
  assert.equal(new Set(bins.map((r) => r.id)).size, 48);
  assert(new Set(bins.map((r) => r.locationDescription)).size < 48);
  assert.equal(bins.filter((r) => r.collectionDay === 'Wednesday').length, 46);
  assert.equal(bins.filter((r) => r.collectionDay === 'Thursday').length, 2);
  assert.deepEqual(
    new Set(bins.filter((r) => r.binNumber).map((r) => r.binNumber)),
    new Set(['1899', '9']),
  );
  for (const r of bins)
    for (const k of [
      'coordinates',
      'collector',
      'repairContact',
      'collectionFrequency',
    ])
      assert.equal(r[k], null);
  assert.deepEqual(
    JSON.parse(
      readFileSync(
        new URL('../public/data/bin-register.json', import.meta.url),
        'utf8',
      ),
    ),
    data.binRegister,
  );
});

test('pending transfers and register ownership are not prematurely confirmed', () => {
  assert.equal(data.transfers.length, 3);
  for (const t of data.transfers) {
    assert.equal(t.status, 'Transfer pending');
    assert.equal(t.asOf, '2026-09-15');
    assert.notEqual(t.currentContact, 'scdc');
  }
  assert.equal(data.governance.owner, null);
  assert(data.reviews.every((r) => r.status === 'Suggested review'));
});

test('public evidence summaries exclude received emails, restricted title-plan images and staff routing addresses', () => {
  const json = JSON.stringify(data);
  assert.doesNotMatch(
    json,
    /\.msg|Thomas\.parker@|Kate\.Swan@|Lia\.Howlett@|CB478514/i,
  );
  for (const id of [
    'response-scdc',
    'response-he',
    'response-bins',
    'response-western',
  ])
    assert.equal(data.sources[id].url, null);
  assert.equal(data.audit.countyDate, '2026-10-13');
  for (const f of data.features.filter((f) => f.properties.sourceAttributes)) {
    assert.equal(f.properties.checked, data.audit.countyDate);
    assert.equal(f.properties.id, f.properties.sourceAttributes.source_id);
  }
});
