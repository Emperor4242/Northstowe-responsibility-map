import test from 'node:test';
import assert from 'node:assert/strict';
const base = process.env.NORTHSTOWE_TEST_URL || 'http://127.0.0.1:4173';
test('production page and its compiled assets load', async () => {
  const page = await fetch(base + '/');
  assert.equal(page.status, 200);
  const html = await page.text();
  assert.match(html, /Northstowe/);
  const assets = [...html.matchAll(/(?:src|href)="(\/assets\/[^"]+)"/g)].map(
    (m) => m[1],
  );
  assert(assets.length >= 2);
  for (const url of assets) {
    const r = await fetch(base + url);
    assert.equal(r.status, 200, url);
    assert((await r.arrayBuffer()).byteLength > 0);
  }
});
test('served register contains reviewed roads, bin scopes and current contact additions', async () => {
  const r = await fetch(base + '/data/responsibilities.json');
  assert.equal(r.status, 200);
  const d = await r.json();
  assert.equal(d.features.length, 317);
  const faith = d.features.find((f) => f.properties.id === 'way-725332128');
  assert.equal(faith.properties.landOwner, 'uc');
  assert.equal(faith.properties.transferStatus, 'Transfer pending');
  assert.equal(d.organisations.elite.email, 'westernpark@elitesportsuk.com');
  assert(d.features.some((f) => f.properties.id === 'bins-bughunter'));
  assert(d.features.some((f) => f.properties.id === 'western-carpark'));
  assert(d.features.some((f) => f.properties.id === 'education-campus'));
  assert.equal(d.binRegister.records.length, 48);
  const bins = await fetch(base + '/data/bin-register.json');
  assert.equal(bins.status, 200);
  assert.deepEqual((await bins.json()).records, d.binRegister.records);
  assert.equal(
    d.features.filter((f) => f.properties.id.startsWith('AdoptedRoads.'))
      .length,
    6,
  );
  assert.equal(
    d.features.find((f) => f.properties.id === 'stirling-phase2').properties
      .roadClass,
    'developer',
  );
});
test('private review pack, source code and dot paths are not served', async () => {
  for (const url of [
    '/email-drafts/index.html',
    '/email-drafts/follow-ups/index.html',
    '/email-drafts/drafts.json',
    '/Northstowe%20emails/adopted%20map.png',
    '/scripts/prepare-email-drafts.py',
    '/.local-runtime/processes.json',
    '/research/',
    '/data/%2e%2e/%2e%2e/email-drafts/index.html',
    '/%2e%2e%5cemail-drafts%5cindex.html',
  ]) {
    const r = await fetch(base + url);
    assert.equal(r.status, 404, url);
  }
  const post = await fetch(base + '/', { method: 'POST', body: 'test' });
  assert.equal(post.status, 405);
  const head = await fetch(base + '/', { method: 'HEAD' });
  assert.equal(head.status, 200);
  assert.equal(await head.text(), '');
});
