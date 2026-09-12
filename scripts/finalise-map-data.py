"""Run after build-map-data.py and extend-map-data.py to add authoritative snapshots."""
from pathlib import Path
import json,sys,xml.etree.ElementTree as ET,copy,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape,mapping,Point,Polygon
from shapely.ops import unary_union
out=ROOT/'public/data';d=json.loads((out/'responsibilities.json').read_text(encoding='utf-8'));fs=d['features'];orgs=d['organisations'];sources=d['sources'];d['checked']='2026-09-12'
def source(id,title,publisher,url,date='Checked 12 September 2026'):sources[id]=dict(title=title,publisher=publisher,url=url,date=date)
source('contacts','Northstowe partner contacts and Estates helpdesk','Homes England / Northstowe','https://www.northstowe.com/contact')
source('county-wfs','County mapped highway and asset records','Cambridgeshire County Council','https://maps.cambridgeshire.gov.uk/getows.ashx?MapSource=CCC/AllMaps&service=WFS&version=1.1.0&request=GetCapabilities','Downloaded 12 September 2026; no individual update dates supplied')
source('row','Public rights of way and fault reporting','Cambridgeshire County Council','https://www.cambridgeshire.gov.uk/residents/libraries-leisure-culture/countryside-access/rights-of-way')
source('pe','Northstowe sports-facility operator and contact','P&E Sports','https://pandesports.com/northstowe-college')
source('gbcontact','Greenbelt customer contact and service plans','Greenbelt','https://www.greenbelt.co.uk/contact-us/')
orgs['uc'].update(email='Northstowe@urbanandcivic.com',source='contacts',description='Phase 1 master developer, formerly L&Q Estates. Local development enquiries; individual parcel assets may remain with housebuilders. The forum gives 01223 622533 for local roadworks enquiries.')
orgs['he']['source']='contacts';orgs['ntc']['email']='admin@northstowe-tc.gov.uk';orgs['ntc']['source']='contacts';orgs['greenbelt']['source']='gbcontact'
orgs['aw']['reportUrl']='https://www.anglianwater.co.uk/issue'
orgs['barratt']['reportUrl']=None  # Keep the published local email; web endpoint unverified.
orgs['pe']=dict(name='P&E Sports',shortName='P&E Sports',color='#a73777',description='Operator of community sports facilities at Northstowe Secondary College. Report facility defects to the operator; school and external highway assets may have different contacts.',reportUrl=sources['pe']['url'],email='northstowe@pandesports.com',phone='01527 529496',source='pe')
def r(o,c,n,s,cv=None):return dict(org=o,categories=c,note=n,sources=s,caveat=cv)
def add(id,name,g,rs,**kw):
 assert g.is_valid and not g.is_empty,id
 p=dict(id=id,name=name,responsibilities=rs,status='published',geometryStatus='official',geometryNote='County source geometry. Full features at the parish edge may extend outside Northstowe.',context=False,anchor=list(g.representative_point().coords[0]),checked='2026-09-12')
 p.update(kw);fs.append(dict(type='Feature',geometry=mapping(g),properties=p));return fs[-1]
def county(layer):return json.loads((ROOT/f'research-boundaries/county-{layer}.geojson').read_text(encoding='utf-8'))['features']
for f in county('AdoptedRoads'):
 p=f['properties'];add(p['source_id'],p['street'].title()+' — adopted highway',shape(f['geometry']),[r('ccc',['roads'],'Shown in the county’s adopted-highway layer. Report highway-surface faults to the County Council.',['county-wfs','highways','highreport'],'The line does not show the full highway width or establish who owns adjacent land, trees, lights or drains.')],geometryUrl=p['source_url'],recordLabel='County adopted-highway record',geometryNote='Official county centreline; display width is for visibility. Some records cross parish boundaries and should not be used for legal highway-extent decisions.')
for f in county('Section38Streets'):
 p=f['properties'];existing=next((x for x in fs if x['properties']['id']=='road-'+p['street'].lower().replace(' ','-')),None)
 if existing:fs.remove(existing)
 add(p['source_id'],p['street'].title()+' — prospective adoption',shape(f['geometry']),[r('uc',['roads','lighting'],'Raise Phase 1 finishing-work or retained-asset enquiries with Urban & Civic.',['report','forum'],'County mapping lists this road under Section 38 (prospective adoption). Confirm the exact section and maintenance-period obligations before treating it as adopted.'),r('ccc',['roads'],'The County Council is the enquiry route for the current adoption record.',['county-wfs','highways'],'Prospective adoption is not evidence of completed adoption or current county maintenance.')],status='uncertain',geometryUrl=p['source_url'],recordLabel='County prospective-adoption record')
for f in county('StreetLights'):
 p=f['properties'];assert p['owner']=='Cambridgeshire County Council'
 add(p['source_id'],p['street'].title()+' — light '+p['unit_no'],shape(f['geometry']),[r('lights',['lighting'],f"County-owned {p['unit_type'].lower()}; quote column {p['unit_no']} and {p['street'].title()} when reporting.",['county-wfs','streetlights'],'Check the code on the actual column; map points and your device location can differ.')],geometryUrl=p['source_url'],assetId=p['unit_no'],pointRadius=12,detail=True,recordLabel='County-owned lighting asset')
for f in county('Gullies'):
 p=f['properties'];add(p['source_id'],p['road_name'].title()+' — gully '+p['ogc_fid'],shape(f['geometry']),[r('ccc',['water'],f"Drainage gully in the county’s public asset map. Quote map record {p['ogc_fid']} and the road when reporting a blockage.",['county-wfs','highreport'],'This identifies a highway-drainage reporting route; it does not map or establish ownership of the connecting sewer, pond or watercourse.')],geometryUrl=p['source_url'],assetId=p['ogc_fid'],pointRadius=8,detail=True,recordLabel='County gully record')
for f in county('row'):
 p=f['properties'];add(p['source_id'],p['parish']+' '+p['status'].lower()+' '+p['pathno'],shape(f['geometry']),[r('ccc',['roads'],f"Public-right-of-way reference {p['name']}. Use the county fault form for surface, access or signposting problems.",['county-wfs','row'],'This is a reporting route. Responsibility for gates, hedges and other adjoining assets can fall to the landowner. Consult the Definitive Map for legal alignment.')],geometryUrl=p['source_url'],recordLabel='County public-right-of-way record')
# District property polygons retrieved nearby are small residential holdings; exclude
# them from the public-realm map because a property holding is not a maintenance contract.
# Phase 3B was tagged place=proposed, so not present in the physical-asset extract.
root=ET.parse(ROOT/'research-boundaries/northstowe-osm-map.osm').getroot();nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
w=next(w for w in root.findall('way') if w.attrib['id']=='1210527345');refs=[n.attrib['ref'] for n in w.findall('nd')];assert refs[0]==refs[-1]
add('phase3b','Phase 3B — broad Homes England enquiry area',Polygon([nodes[n] for n in refs]),[r('he',['green','water','roads','lighting','play','waste','facilities'],'Homes England leads Phase 3 and is the enquiry route for retained development land.',['faq','master'],'This indicative phase outline does not establish ownership or maintenance of individual fields, roads, properties or assets.')],context=True,status='uncertain',geometryStatus='indicative',geometryNote='OpenStreetMap proposed development outline, way 1210527345. Not a legal ownership or management boundary.',geometryUrl='https://www.openstreetmap.org/way/1210527345')
raw=[]
for name in ['assets-polygons','buildings','highways']:raw+=json.loads((ROOT/f'research-boundaries/northstowe-osm-{name}.geojson').read_text(encoding='utf-8'))['features']
byid={f['id']:f for f in raw}
school=byid['way/725332129'];g=shape(school['geometry'])
add('college-sports','Northstowe Secondary College — community sports enquiry',Point(g.representative_point()),[r('pe',['play','lighting','facilities'],'P&E Sports manages the community sports facilities at the college.',['pe','common'])],geometryStatus='footprint',geometryNote='Location marker at the college; does not define the sports operator’s full maintenance boundary.',geometryUrl=school['properties']['osm_url'])
# Preserve specific sports and allotment exceptions in the surrounding landscape layer.
western=next(f for f in fs if f['properties']['id']=='way-725827725')
exclusions=unary_union([shape(byid['way/'+id]['geometry']) for id in ['725332125','725332121','952350385','1030629199','952350386','929650245','952646465','952646466']])
newg=shape(western['geometry']).difference(exclusions)
western['geometry']=mapping(newg);western['properties']['anchor']=list(newg.representative_point().coords[0]);western['properties']['geometryNote']+=' Separately mapped sports facilities and allotments are excluded.'
# The path-lighting exception has no surveyed footprint. Show a clearly marked
# enquiry marker, rather than colouring the entire lake estate as a lighting area.
awland=next(f for f in fs if f['properties']['id']=='way-725827723');exception=awland['properties']['responsibilities'].pop()
awland['properties']['responsibilities'][0]['caveat']='Lights on the Park & Ride–Stirling Road path have a separately published Urban & Civic contact; see the lighting enquiry marker. Exact estate and path boundaries need confirmation.'
park=shape(byid['way/65047447']['geometry']) if 'way/65047447' in byid else None
if park:
 add('park-and-ride','Longstanton Park & Ride — site enquiry',park,[r('ccc',['roads','water','lighting','waste','facilities'],'County Council enquiry for Park & Ride infrastructure. County gully points are mapped individually.',['county-wfs','highways'],'The detailed split between site contracts, lights and operators has not been established.')],status='uncertain',geometryStatus='footprint',geometryUrl='https://www.openstreetmap.org/way/65047447')
add('bughunter-path-lights','Park & Ride–Stirling Road path lights — enquiry marker',Point(.0574,52.2900),[exception],status='uncertain',geometryStatus='indicative',geometryNote='Approximate orientation marker near the path. The light locations and maintenance extent have not been published; this is not a complete lighting boundary.',pointRadius=30)
for f in fs:
 p=f['properties']
 if p['id'] in ['way-725332125','way-725332121','way-952350385']:
  p['responsibilities'][0]['categories'].append('green')
 if p['context']:p['status']='uncertain'
 # Replace obsolete/blocked March-plan attribution with the downloaded September plan.
 for item in p['responsibilities']:item['sources']=['greenbelt' if x=='greenplan' else x for x in item['sources']]
for o in orgs.values():
 if o.get('source')=='greenplan':o['source']='greenbelt'
sources.pop('greenplan',None)
for gap in d['gaps']:
 if gap['id']=='highways':gap['detail']='County centreline, Section 38, lighting and gully snapshots are now included (12 September 2026). Still needed: signed adoption and maintenance-period records, exact highway widths, developer light inventories and later transfers. Absence from a county layer is not proof of private ownership.'
 if gap['id']=='phase3':gap['detail']='An indicative Phase 3B outline is included. Still needed: current ownership and maintenance polygons for each retained, sold or transferred plot, including fields and paths west of Phase 1.'
d['audit']=dict(counts=dict(features=len(fs),organisations=len(orgs),adopted_records=6,prospective_records=2,county_lights=50,gullies=176,rights_of_way=11),countyDate='2026-09-12',note='County map snapshot is not live. Absence from a source layer is not evidence that an asset is privately maintained. Small residential district-property holdings excluded from public-realm scope.')
(out/'responsibilities.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(out/'responsibility-areas.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=fs),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
notes=['# Northstowe responsibility map — research and gap register','Research checked 11–12 September 2026.','', 'The complete ONS parish boundary is displayed. Responsibility evidence remains incomplete. A public source identifying an organisation is distinct from a surveyed maintenance boundary. OSM outlines locate assets; they do not establish ownership. County snapshots are dated downloads, not a live feed.','', '## Public records added', '6 adopted-highway records, 2 prospective-adoption records, 50 explicitly county-owned lights, 176 mapped gullies and 11 rights-of-way records intersect the parish. Complete edge features may extend beyond the parish. The four district property records returned relate to small residential holdings and are not treated as public-realm maintenance areas.','', '## Remaining information gaps']
for g in d['gaps']:notes += [f"### {g['title']}",g['detail'],f"Information holder: {g['holder']}",'']
notes+=['## Method and attribution','ONS: December 2025 full-resolution parish E04013120; 4.719 km². Boundary unchanged. © Crown copyright and database right 2025, OS and ONS.','County: public WFS CCC/AllMaps, downloaded 12 September 2026 in EPSG:27700; exact parish intersection in that CRS, projected to WGS84 with PROJ. © Crown copyright and database rights 2026 OS AC0000822131. Source centreline width is not highway extent.','OpenStreetMap contributors © ODbL; snapshot 11 September 2026. Physical features retain source IDs. Phase 3B proposed outline extracted separately from original OSM XML.','House parcels H1–H11: unsurveyed hand digitisation of Greenbelt’s 10 September 2025 slide 10, aligned by three approximate identifiable centres. This alignment is for orientation and is not title or asset-boundary accuracy. H12/H13 use OSM footprints. Source presentation copyright remains with its publisher.','All dates in each source entry refer to that document or retrieval; an old expectation of transfer is never treated as completion. Exact handovers and contractor scopes remain open questions.','', '## Contacts']
for o in orgs.values():notes += [f"### {o['name']}",o['description'],' | '.join(x for x in [o.get('email'),o.get('phone'),o.get('reportUrl')] if x),'']
notes+=['## Sources']
for id,s in sources.items():notes += [f"- {id}: [{s['title']}]({s['url']}) — {s['publisher']}; {s['date']}"]
notes+=['','## Feature register']
for f in fs:
 p=f['properties'];notes += [f"### {p['name']}",f"Evidence: {p['status']}. {p['geometryNote']}"]
 for x in p['responsibilities']:notes += [f"- {orgs[x['org']]['name']}: {', '.join(x['categories'])}. {x['note']} {x.get('caveat') or ''} Sources: {', '.join(x['sources'])}."]
(out/'research-notes.md').write_text('\n'.join(notes),encoding='utf-8')
print(json.dumps(d['audit'],indent=2))
