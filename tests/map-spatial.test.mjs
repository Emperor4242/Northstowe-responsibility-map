import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {contains} from '../lib/map-spatial.ts';
const data=JSON.parse(readFileSync(new URL('../public/data/responsibilities.json',import.meta.url),'utf8'));
const boundary=JSON.parse(readFileSync(new URL('../public/data/parish.geojson',import.meta.url),'utf8'));
const feature=id=>data.features.find(f=>f.properties.id===id);
const contacts=(p,category)=>data.features.filter(f=>contains(f,p)&&!f.properties.context).flatMap(f=>f.properties.responsibilities.filter(r=>r.categories.includes(category)).map(r=>r.org));
test('opposite lake estates route water issues to their separately published contacts',()=>{
 assert(contacts([.066365,52.286729],'water').includes('aw'));
 assert(contacts([.07395,52.278393],'water').includes('he'));
 assert(!contacts([.07395,52.278393],'water').includes('aw'));
});
test('H4 preserves both open-space and street-tree enquiry scopes',()=>{
 const f=feature('parcel-H4');
 assert.deepEqual(new Set(f.properties.responsibilities.filter(r=>r.categories.includes('green')).map(r=>r.org)),new Set(['greenbelt','vistry']));
 assert(f.properties.responsibilities.some(r=>r.caveat.includes('street trees')));
 assert.equal(f.properties.status,'uncertain');
});
test('sports pitch is excluded from the surrounding Greenbelt landscape geometry',()=>{
 const p=[.049161,52.284760];
 assert(contacts(p,'play').includes('elite'));
 assert(contacts(p,'green').includes('elite'));
 assert.equal(contains(feature('way-725827725'),p),false);
});
test('prospective adoption is never labelled completed adoption',()=>{
 const future=data.features.filter(f=>f.properties.id.startsWith('Section38Streets.'));
 assert.equal(future.length,2);
 for(const f of future){assert.equal(f.properties.status,'uncertain');assert.match(f.properties.name,/prospective adoption/);}
 assert.equal(data.features.filter(f=>f.properties.id.startsWith('AdoptedRoads.')).length,6);
});
test('exact county light and gully points are returned without expanding ownership across the parish',()=>{
 const lights=data.features.filter(f=>f.properties.id.startsWith('StreetLights.'));
 assert.equal(lights.length,50);
 for(const f of lights){assert(contains(f,f.geometry.coordinates));assert(!contains(f,[f.geometry.coordinates[0]+.002,f.geometry.coordinates[1]]));}
 assert.equal(data.features.filter(f=>f.properties.id.startsWith('Gullies.')).length,176);
 assert.equal(feature('parish-highways').properties.status,'uncertain');
});
test('register has unique IDs, sources, categories and a usable contact for every responsibility',()=>{
 const ids=data.features.map(f=>f.properties.id);assert.equal(new Set(ids).size,ids.length);
 for(const f of data.features)for(const r of f.properties.responsibilities){
  const o=data.organisations[r.org];assert(o,f.properties.name);
  assert(o.reportUrl||o.email||o.phone);assert(r.sources.length);
  for(const id of r.sources)assert(data.sources[id],id);
  for(const c of r.categories)assert(['green','water','roads','lighting','play','waste','facilities'].includes(c));
 }
 assert.equal(data.audit.counts.features,data.features.length);
 assert.equal(data.organisations.ntc.email,'admin@northstowe-tc.gov.uk');
 assert.equal(data.organisations.uc.email,'Northstowe@urbanandcivic.com');
});
test('official parish outline includes western Phase 3B and distinguishes locations beyond the boundary',()=>{
 assert(contains(boundary.features[0],[.043,52.292]));
 assert(!contains(boundary.features[0],[.02,52.285]));
 assert.equal(boundary.features[0].geometry.coordinates[0].length,574);
 assert.equal(feature('phase3b').properties.context,true);
});
