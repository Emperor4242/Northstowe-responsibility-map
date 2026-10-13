"""Apply the councillor's road/bin review after finalise-map-data.py. Idempotent."""
from pathlib import Path
import json,sys,copy
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape,mapping
d=json.loads((ROOT/'public/data/responsibilities.json').read_text(encoding='utf-8'));fs=d['features'];src=d['sources'];orgs=d['organisations']
def source(id,title,publisher,url,date):src[id]=dict(title=title,publisher=publisher,url=url,date=date)
source('bins-aw','Open Space Steering Group: Anglian Water dog-bin collections','Northstowe Town Council','https://www.northstowetowncouncil.gov.uk/_UserFiles/Files/53_250325%20OpenSpacesSG%20NTC.pdf','Meeting 25 March 2025, item 5.2; checked 12 September 2026')
source('bins-western','Open Space Steering Group: Western Park bin contractor','Northstowe Town Council','https://www.northstowetowncouncil.gov.uk/_UserFiles/Files/14_240322%20Open%20Space%20Steering%20Group%20Minutes%20-%20Town%20Council.pdf','Draft notes, meeting 24 March 2022, item 4.1; historical evidence')
source('streetcare','Council-serviced public bins: identification and overflow reports','Greater Cambridge Shared Waste','https://greatercambridgewaste.org/litter-in-public-spaces/street-care-and-cleaning-south-cambs','Checked 12 September 2026')
source('streetcontact','Street-care team email contact','Greater Cambridge Shared Waste','https://www.greatercambridgewaste.org/residents/what-goes-in-which-bin','Checked 12 September 2026')
orgs['waste']['email']='streets@scambs.gov.uk'
source('elitecontact','Western Park contact','Elite Sports UK','https://elitesportsuk.com/contact/','Checked 12 September 2026')
source('bowlscontact','Longstanton Bowls Club contact listing','Northstowe Hub','https://northstowehub.org/community/longstanton-bowls-club/','Checked 12 September 2026')
orgs['elite'].update(email='westernpark@elitesportsuk.com',source='elitecontact')
orgs['bowls'].update(email='membership@Longstanton-Bowls-Club.co.uk',reportUrl='https://northstowehub.org/community/longstanton-bowls-club/',source='bowlscontact')
orgs['keepmoat']['reportUrl']='https://www.keepmoat.com/contact-us/customer-care'
orgs['waste']['description']='Fly-tipping reporting and enquiries about council-serviced litter or dog bins. A council bin sticker identifies its collection service; other estate bins have separate operators.'
def r(o,n,s,c=None,e='enquiry'):return dict(org=o,categories=['bins'],note=n,sources=s,caveat=c,evidence=e)
# Remove only this script's prior additions before regenerating.
fs[:]=[f for f in fs if not f['properties'].get('reviewAddition')]
for f in fs:
 p=f['properties'];p['responsibilities']=[r for r in p['responsibilities'] if r.get('reviewAddition')!=True]
 if p['id'] in ['stirling-phase2','southern-access-road']:
  p['recordLabel']='Homes England road contact';p['roadClass']='developer';p['roadPriority']=True
  p['responsibilities'][0]['sources']=['contacts','report']
  p['responsibilities'][0]['note']='Homes England is the published contact for Phase 2 main roads and the new access road from the B1050. Report road defects to its Estates helpdesk.'
  p['responsibilities'][0]['caveat']='The precise phase break and any subsequent adoption need confirmation. The highlighted line locates the road and does not define highway width.'
 if p['id'].startswith('AdoptedRoads.'):
  p['roadClass']='adopted';p['roadPriority']=True
 if p['id'].startswith('Section38Streets.'):p['roadClass']='prospective';p['roadPriority']=True
 if p['id'] in ['road-pathfinder-way','road-links-lane','stirling-phase1']:p['roadClass']='developer';p['roadPriority']=True
 for rs in p['responsibilities']:
  if rs['org']=='aw' and 'roads' in rs['categories']:rs['scopeLabels']={'roads':'Paths around Bug Hunter Waters','green':'Grounds and planting','waste':'Litter / fly-tipping enquiry'}
def binarea(baseid,newid,name,rs):
 f=copy.deepcopy(next(f for f in fs if f['properties']['id']==baseid));p=f['properties'];p.update(id=newid,name=name,responsibilities=[rs],status='uncertain',recordLabel='Bin-emptying evidence — confirm current scope',reviewAddition=True)
 fs.append(f)
binarea('way-725827723','bins-bughunter','Bug Hunter Waters — dog-bin emptying',r('aw','Anglian Water reported arranging the dog-bin collection service around its lake.',['bins-aw'],'The March 2025 minutes describe fortnightly collections. The current frequency, contractor and exact bin inventory need confirmation. This does not identify every bin on the wider estate.','historical'))
binarea('way-725827725','bins-western','Western Park landscape — public-bin emptying',r('greenbelt','The March 2022 steering-group notes identify Greenbelt’s contractors for Western Park bins.',['bins-western'],'Historical, area-level evidence. Verify the current service and exact bins; bins within leased sports facilities may use a different arrangement.','historical'))
# Generic park/estate maintenance does not prove that organisation empties every bin.
for f in list(fs):
 p=f['properties']
 if p.get('reviewAddition') or p['id'] in ['parish-waste','parish-highways'] or p['id'].startswith(('AdoptedRoads.','Section38Streets.','row.')):continue
 if f['geometry']['type'] not in ['Polygon','MultiPolygon'] or p['id'] in ['way-562586195','way-161965235','relation-16915052','way-725827721','relation-53634']:continue
 if p['id'] in ['way-725827723','way-725827725']:continue # Evidence-specific overlays above.
 seen=set()
 for rs in list(p['responsibilities']):
  if rs['org'] in seen or not any(c in rs['categories'] for c in ['green','facilities','play']):continue
  seen.add(rs['org'])
  q=r(rs['org'],'Enquire about the bin at this location. The publicly available records identify a land or facility contact, but do not establish who empties each bin.',rs['sources'],'Bin-emptying contractor and exact service area are unconfirmed. Please provide a photo, bin label/ID and location.');q['reviewAddition']=True;p['responsibilities'].append(q)
parish=copy.deepcopy(next(f for f in fs if f['properties']['id']=='parish-waste'));parish['properties'].update(id='bins-council-check',name='Council-sticker public bins — identification and reporting',reviewAddition=True,status='uncertain',responsibilities=[r('waste','The waste service says its marked litter/dog bins are emptied by its street-care service.',['streetcare'],'Check the sticker on the actual bin. This parish-wide enquiry area does not mean every bin is council-serviced.')]);fs.append(parish)
for f in json.loads((ROOT/'research-boundaries/northstowe-osm-assets-points.geojson').read_text(encoding='utf-8'))['features']:
 p=f['properties']
 if p.get('amenity') not in ['waste_basket','waste_disposal'] or not p['intersects_official_parish']:continue
 ident=f['id'].replace('/','-');g=shape(f['geometry']);q=dict(id='bin-'+ident,name='Mapped public bin — service not confirmed ('+f['id'].split('/')[-1]+')',status='uncertain',recordLabel='Bin location; emptying service unconfirmed',geometryStatus='footprint',geometryNote='OpenStreetMap bin point, not an operator or contract record. Check that the bin is still present.',geometryUrl=p['osm_url'],context=False,anchor=list(g.coords[0]),pointRadius=12,reviewAddition=True,responsibilities=[r('he','This bin point is in the Phase 2 area. Ask Homes England to identify the collection service.',['osm','faq'],'Location is mapped; the emptying contractor and bin identifier are not verified.')]);fs.append(dict(type='Feature',geometry=f['geometry'],properties=q))
for g in d['gaps']:
 if g['id']=='bins':g['detail']='The bin-emptying layer now distinguishes historical AW dog-bin and Western Park contractor evidence from unconfirmed estate enquiries. Obtain a geolocated bin register with owner, emptying contractor, frequency, repair/replacement contact and dated transfers. Council stickers should be checked on site.'
d['audit']['counts']['features']=len(fs);d['audit']['binPoints']=5;d['audit']['roadsRechecked']='12 September 2026: 6 adopted records and 2 prospective records, unchanged on repeat county query.'
out=ROOT/'public/data'
(out/'responsibilities.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(out/'responsibility-areas.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=fs),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
notes=['# Northstowe responsibility map — updated evidence register','Reviewed 12 September 2026. The parish outline is complete. Exact responsibilities and current handovers remain incomplete.','', '## Road review','Homes England: Phase 2 main roads and the access road from B1050, per the current Northstowe contact page and the Town Council reporting guide. County: 6 adopted road/path records intersect the parish; Eagle Way and Wellington Road are in the prospective Section 38 layer. The repeat county query returned the same records. Road colour represents a contact/scope, not legal width or a blanket claim about adjacent land.','', '## Public-bin emptying','Anglian Water dog-bin collections are recorded in March 2025 minutes; Greenbelt’s Western Park contractors are recorded in draft March 2022 notes. Both are historical evidence, not verified current schedules. Five OSM bin points in Phase 2 have no recorded operator. Elsewhere only a land/facility enquiry route is shown. Check council service stickers and obtain the actual bin inventory.','', '## Remaining information']
for g in d['gaps']:notes += [f"### {g['title']}",g['detail'],f"Information holder: {g['holder']}"]
notes+=['','## Sources']
for id,s in src.items():notes += [f"- {id}: [{s['title']}]({s['url']}) — {s['publisher']}; {s['date']}"]
notes+=['','## Feature and contact register']
for f in fs:
 p=f['properties'];notes += [f"### {p['name']}",p['geometryNote']]
 for rs in p['responsibilities']:
  o=orgs[rs['org']];notes += [f"- {o['name']}: {', '.join(rs['categories'])}. {rs['note']} {rs.get('caveat') or ''} Sources: {', '.join(rs['sources'])}."]
notes+=['','## Attribution and methods','ONS parish E04013120, full-resolution December 2025 boundary; © Crown copyright and database right 2025, OS and ONS. County WFS snapshot EPSG:27700 reprojected to WGS84 with PROJ; © Crown copyright and database rights 2026 OS AC0000822131. OSM geography © OpenStreetMap contributors, ODbL. House parcels H1–H11 are unsurveyed digitisation of Greenbelt’s September 2025 slide 10; H12/H13 and phase outlines use OSM. None of these outlines establishes a title or exact maintenance boundary. Source publishers retain their rights.']
(out/'research-notes.md').write_text('\n'.join(notes),encoding='utf-8')
print('Updated map:',len(fs),'features; bin-emptying separated from litter/fly-tipping.')
