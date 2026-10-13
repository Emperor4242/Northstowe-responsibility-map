import test from 'node:test';
import assert from 'node:assert/strict';
const base = process.env.NORTHSTOWE_TEST_URL || 'http://127.0.0.1:4173';

test('production page and compiled assets load', async () => {
  const page = await fetch(base + '/');
  assert.equal(page.status, 200);
  const html = await page.text();
  assert.match(html, /Northstowe/);
  const assets = [...html.matchAll(/(?:src|href)="(\/assets\/[^"]+)"/g)].map((m) => m[1]);
  assert(assets.length >= 2);
  for (const url of assets) {
    const response = await fetch(base + url);
    assert.equal(response.status, 200, url);
    assert((await response.arrayBuffer()).byteLength > 0);
  }
});

test('served register contains reviewed roads, bin scopes and current contact additions', async () => {
  const response = await fetch(base + '/data/responsibilities.json');
  assert.equal(response.status, 200);
  const data = await response.json();
  assert.equal(data.features.length, 313);
  assert.equal(data.organisations.elite.email, 'westernpark@elitesportsuk.com');
  assert(data.features.some((f) => f.properties.id === 'bins-bughunter'));
  assert.equal(data.features.filter((f) => f.properties.id.startsWith('AdoptedRoads.')).length, 6);
});

test('private files and source code are excluded and the server only accepts reads', async () => {
  for (const url of ['/email-drafts/index.html', '/Northstowe%20emails/adopted%20map.png', '/scripts/local-server.mjs', '/.local-runtime/processes.json', '/research/', '/%2e%2e%5cemail-drafts%5cindex.html']) {
    assert.equal((await fetch(base + url)).status, 404, url);
  }
  assert.equal((await fetch(base + '/', { method: 'POST', body: 'test' })).status, 405);
  const head = await fetch(base + '/', { method: 'HEAD' });
  assert.equal(head.status, 200);
  assert.equal(await head.text(), '');
});
