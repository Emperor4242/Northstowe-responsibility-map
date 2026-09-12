"""Indicative parcel digitisation from Greenbelt's published September 2025 plan.
Control points are approximate identifiable plan features, not survey control.
Pixel coordinates use research/parcel-plan-detail.png, crop (700,20,1200,630)
of slide image7.png, scaled 2x. No land-title accuracy is implied.
"""
from pathlib import Path
import json,sys,numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape,mapping,Polygon,Point,LineString
from shapely.ops import unary_union
out=ROOT/'public/data';data=json.loads((out/'responsibilities.json').read_text(encoding='utf-8'));features=data['features'];orgs=data['organisations'];sources=data['sources']
raw=[]
for kind in ['assets-polygons','highways','buildings','assets-points']:raw+=json.loads((ROOT/f'research-boundaries/northstowe-osm-{kind}.geojson').read_text(encoding='utf-8'))['features']
byid={f['id']:f for f in raw}
T=np.array(json.loads((ROOT/'research/plan-transform.json').read_text()))
parcels={
 'H1':('bloor',[[667,164],[779,112],[821,254],[710,250],[688,239]]),
 'H2':('barratt',[[525,239],[591,123],[624,110],[686,272],[682,337],[571,340],[550,315]]),
 'H3':('taylor',[[608,354],[665,354],[657,457],[638,468],[611,422]]),
 'H4':('vistry',[[678,381],[789,385],[772,489],[667,462]]),
 'H5':('vistry',[[659,490],[782,507],[761,606],[732,626]]),
 'H6':('vistry',[[797,514],[941,541],[877,705],[856,716],[838,763],[812,751],[758,635],[783,580]]),
 'H7':('barratt',[[254,424],[372,351],[435,327],[505,287],[549,342],[477,379],[281,477]]),
 'H8':('barratt',[[413,421],[554,364],[627,495],[491,566]]),
 'H9':('barratt',[[286,492],[400,432],[475,573],[381,626]]),
 'H10':('taylor',[[435,615],[484,584],[558,716],[587,761],[607,766],[599,835]]),
 'H11':('taylor',[[495,578],[650,489],[712,636],[638,678],[617,723],[614,753],[579,750]])
}
def r(org,cats,note,src,caveat=None):return dict(org=org,categories=cats,note=note,sources=src,caveat=caveat)
def add(id,name,g,rs,context=False,note='Indicative outline; confirm the exact asset and boundary.',status='uncertain',url=None):
 assert g.is_valid and not g.is_empty,(id,'invalid')
 p=dict(id=id,name=name,responsibilities=rs,status=status,geometryStatus='indicative',geometryNote=note,geometryUrl=url,context=context,anchor=list(g.representative_point().coords[0]),checked='2026-09-11')
 features.append(dict(type='Feature',geometry=mapping(g),properties=p))
geoms={}
for h,(o,xy) in parcels.items():
 ll=np.c_[np.array(xy),np.ones(len(xy))]@T;g=Polygon(ll);geoms[h]=g
 rs=[r(o,['roads','lighting','water','green','play','waste'],'Housebuilder enquiry for assets retained within this parcel.',['greenbelt','report'],'Street adoption and later transfers must be checked. The whole parcel is not necessarily maintained by one party.')]
 if h in ['H1','H2','H4','H7','H8']:
  rs.insert(0,r('greenbelt',['green','play','waste'],'Greenbelt lists this parcel for open-space maintenance in its September 2025 presentation.',['greenbelt'],'This covers transferred communal open spaces, not every garden, road or asset.' if h!='H4' else 'H4 street trees were separately described as the developer’s responsibility. Confirm the specific tree or space.'))
 add('parcel-'+h,h+' — '+orgs[o]['name'],g,rs,note='Approximate parcel outline digitised from Greenbelt’s 10 September 2025 presentation. Unsurveyed: allow for boundary errors and confirm edge locations.',url=sources['greenbelt']['url'])
 # Cross-check geographic placement using original street geometry. Keep record for reproducibility.
 nearby=[]
 for f in raw:
  if f['geometry']['type']=='LineString' and f['properties'].get('name') and f['properties'].get('highway'):
   line=shape(f['geometry']);overlap=line.intersection(g)
   if not overlap.is_empty and overlap.length/line.length>.5:nearby.append(f['properties']['name'])
 print(h,sorted(set(nearby)))

# Household parcel edges form an orientation area only. Do not use this hull for ownership.
phase1=unary_union(list(geoms.values())+[shape(byid['way/725805927']['geometry']),shape(byid['way/1187799861']['geometry']),shape(byid['way/725827725']['geometry']),shape(byid['way/725827723']['geometry'])]).convex_hull
# Retain as reference for clipping source road lines; no hull is published as a title boundary.
stirling=[f for f in raw if f['geometry']['type']=='LineString' and f['properties'].get('name')=='Stirling Road']
roads=unary_union([shape(f['geometry']) for f in stirling]);p1=roads.intersection(phase1);p2=roads.difference(phase1)
for id,g,o,name in [('stirling-phase1',p1,'uc','Stirling Road — Phase 1 sections'),('stirling-phase2',p2,'he','Stirling Road — Phase 2 / access sections')]:
 if not g.is_empty:add(id,name,g,[r(o,['roads','lighting'],'Master-developer enquiry for this road section.',['report','forum'],'Indicative split between phases. Current highway and lighting adoption has not been certified.')],note='OpenStreetMap centreline split using an indicative development envelope. The phase break and highway extent need confirmation.')
sar=unary_union([shape(f['geometry']) for f in raw if f['geometry']['type']=='LineString' and f['properties'].get('name')=='Southern Access Road'])
if not sar.is_empty:add('southern-access-road','Southern Access Road / Northstowe Avenue',sar,[r('he',['roads','lighting'],'Homes England is the published access-road contact.',['report'],'Check the current adoption record and precise section, including areas beyond the parish.')],note='Source road centreline; full line may extend outside the parish.')
# Inholm only a named street location, avoiding an invented estate management polygon.
inholm=unary_union([shape(f['geometry']) for f in raw if f['geometry']['type']=='LineString' and f['properties'].get('name')=='Lockhart Way'])
add('inholm','Inholm / Lockhart Way — RMG enquiry',Point(inholm.centroid.coords[0]),[r('rmg',['green','roads','lighting','waste','facilities'],'Estate manager identified by the Town Council’s legacy reporting guide.',['report','rmg'],'Confirm the current management contract. This marker does not define RMG’s land or asset boundary.')],note='Location marker at Lockhart Way, not an estate boundary.')
# H4 street-tree responsibility is shown in the same category as open-space maintenance,
# because a resident must see both contacts and the scope distinction.
sources['streetlights']=dict(title='County street lighting and fault reporting',publisher='Cambridgeshire County Council',date='Checked 11 September 2026',url='https://www.cambridgeshire.gov.uk/residents/travel-roads-and-parking/roads-and-pathways/streetlighting')
orgs['lights']=dict(name='Balfour Beatty / County street lighting',shortName='County street lighting',color='#a27919',description='Faults on county-owned streetlights. Match the column ID to the county map; developer and estate lights have other contacts.',reportUrl=sources['streetlights']['url'],reportLabel='Find / report a county light',phone='0800 783 8247',email='street.lighting@cambridgeshire.gov.uk',source='streetlights')
orgs['ntc']['email']='admin@northstowe-tc.gov.uk'
# The current official contact page is downloaded and separately checked before retaining this email.
sources['towncontact']=dict(title='Current Town Council contact page',publisher='Northstowe Town Council',date='Checked 11 September 2026',url='https://www.northstowe-tc.gov.uk/contact/')
orgs['ntc']['source']='towncontact'
for f in features:
 if f['properties']['id']=='parish-highways':
  f['properties']['responsibilities'][0]['categories']=['roads']
  f['properties']['responsibilities'].append(r('lights',['lighting'],'Use the county lighting map and column number to establish whether Balfour Beatty maintains a light.',['streetlights'],'The parish overlay is an enquiry area. It is not evidence that every light is county-owned.'))

provenance=dict(method='Affine fit between approximate plan feature centres and corresponding OSM feature centres; hand-digitised parcel outlines; indicative only.',source_url=sources['greenbelt']['url'],image='image7.png, source presentation slide 10',control_image='research/parcel-plan-detail.png',transform=T.tolist(),control_points=[dict(label='The Green centre',pixel=[724,281],lonlat=[.050201,52.288413]),dict(label='Kingfisher Pond centre',pixel=[459,291],lonlat=[.050099,52.285183]),dict(label='H13 parcel centre',pixel=[562,974],lonlat=[.064312,52.286082])],check='4G pitch centre [423,245] projects approximately 4 m from the OSM centroid; this local check is not a parcel-boundary accuracy guarantee.',parcels_pixel=parcels)
(ROOT/'research/parcel-digitisation-provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
(out/'responsibilities.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(out/'responsibility-areas.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('Feature count:',len(features))
