"""Apply dated September correspondence to the public snapshot, without publishing emails."""
from pathlib import Path
import json,sys,copy,xml.etree.ElementTree as ET,collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape,mapping,Point,LineString,Polygon
from shapely.ops import unary_union,transform
from pyproj import Transformer
from docx import Document

out=ROOT/'public/data'
d=json.loads((out/'responsibilities.json').read_text(encoding='utf8'))
fs=d['features'];src=d['sources'];orgs=d['organisations']
fs[:]=[f for f in fs if not f['properties'].get('responseAddition')]

# Refresh existing county records only after a complete, validated fetch. A changed
# inventory needs reconciliation rather than silently retaining/deleting asset IDs.
county_provenance=json.loads((ROOT/'research/county-provenance.json').read_text(encoding='utf8'))
county_date=county_provenance['retrieved']
county_counts={}
for layer,count_key in [('AdoptedRoads','adopted_records'),('Section38Streets','prospective_records'),('StreetLights','county_lights'),('Gullies','gullies'),('row','rights_of_way')]:
 records=json.loads((ROOT/f'research-boundaries/county-{layer}.geojson').read_text(encoding='utf8'))['features']
 existing={f['properties']['id']:f for f in fs if f['properties']['id'].startswith(layer+'.')}
 if layer in ['AdoptedRoads','Section38Streets']:
  # WFS road row IDs changed between downloads. Reconcile the unchanged named
  # inventory, then retain the current source ID and geometry (never infer adoption).
  suffix=' — adopted highway' if layer=='AdoptedRoads' else ' — prospective adoption'
  named={f['properties']['name'].removesuffix(suffix).upper():f for f in existing.values()}
  assert len(named)==len(existing)==len(records)
  assert set(named)=={f['properties']['street'].upper() for f in records}
  existing={record['properties']['source_id']:named[record['properties']['street'].upper()] for record in records}
 elif layer=='StreetLights':
  named={f['properties']['name']:f for f in existing.values()}
  names={r['properties']['street'].title()+' — light '+r['properties']['unit_no'] for r in records}
  assert len(named)==len(existing)==len(records) and set(named)==names,'Reconcile changed lighting inventory'
  existing={r['properties']['source_id']:named[r['properties']['street'].title()+' — light '+r['properties']['unit_no']] for r in records}
 else:
  assert set(existing)=={f['properties']['source_id'] for f in records},f'{layer}: reconcile changed inventory before publishing'
 county_counts[count_key]=len(records)
 for record in records:
  attrs=record['properties'];f=existing[attrs['source_id']];g=shape(record['geometry'])
  assert attrs['retrieved']==county_date
  assert g.is_valid and not g.is_empty
  if layer=='StreetLights':assert attrs['owner']=='Cambridgeshire County Council'
  f['geometry']=record['geometry'];p=f['properties']
  p.update(id=attrs['source_id'],anchor=list(g.representative_point().coords[0]),checked=county_date,geometryUrl=attrs['source_url'],sourceAttributes={k:v for k,v in attrs.items() if k not in ['source_url','retrieved']})
  if layer in ['AdoptedRoads','Section38Streets']:p['name']=attrs['street'].title()+(' — adopted highway' if layer=='AdoptedRoads' else ' — prospective adoption')
  elif layer=='StreetLights':
   p.update(name=attrs['street'].title()+' — light '+attrs['unit_no'],assetId=attrs['unit_no'])
   p['responsibilities'][0]['note']=f"County-owned {attrs['unit_type'].lower()}; quote column {attrs['unit_no']} and {attrs['street'].title()} when reporting."
  elif layer=='Gullies':p.update(name=attrs['road_name'].title()+' — gully '+attrs['ogc_fid'],assetId=attrs['ogc_fid'])
  else:p['name']=attrs['parish']+' '+attrs['status'].lower()+' '+attrs['pathno']
src['county-wfs']['date']='Downloaded '+county_date+'; individual adoption/update dates not supplied'
d['audit']['countyDate']=county_date
d['audit']['counts'].update(county_counts)
d['audit']['roadsRechecked']=county_date+': refreshed complete county inventory; 6 adopted and 2 prospective records intersect the parish.'
def feature(id):return next(f for f in fs if f['properties']['id']==id)
def source(id,title,publisher,date,url=None,kind='organisation-response',note=None):
 src[id]=dict(title=title,publisher=publisher,date=date,url=url,kind=kind,note=note or 'Dated confirmation supplied to the councillor. Original correspondence is held privately; this guide publishes a summary.')
source('response-scdc','District council: Western Park, ownership and pending transfers','South Cambridgeshire District Council','Reply received 15 September 2026')
source('response-western','Western Park maintenance responsibilities plan','South Cambridgeshire District Council','Plan dated 28 June 2023; supplied with 15 September 2026 confirmation',kind='supplied-plan')
source('response-he','Homes England retained land and exceptions','Homes England','Reply received 17 September 2026')
source('response-phasing','Northstowe indicative phasing plan','Homes England','Plan dated 2 January 2024; supplied 17 September 2026',kind='supplied-plan',note='Used to interpret development phases. The plan is indicative; proposed facilities and roads are not completed transfers.')
source('response-lights','County lighting adoption and reporting advice','Cambridgeshire County Council','Reply received 15 September 2026')
source('response-bins','Supplied Northstowe bin register','Supplied document','Reviewed 13 October 2026; service effective date not supplied',kind='supplied-register',note='48 records with bin type and listed collection day. No coordinates; provider, repair responsibility and service effective date need confirmation.')
source('meridian-contact','Northstowe Learning Community contact','Northstowe Learning Community / Meridian Trust','Checked 13 October 2026','https://www.northstowe.education/contact-us',kind='public-web',note='Official school office enquiry route; ask to be directed to the campus estates team.')
source('light-report','Report an adopted county streetlight fault','Balfour Beatty Living Places','Reporting route confirmed by county reply, 15 September 2026','https://lightingcambridgeshire.com/report-a-fault/',kind='public-web')
orgs['elite'].update(name='Elite Sports / E.S.C.D. UK Ltd',shortName='Elite Sports',email='westernpark@elitesportsuk.com',source='response-scdc',description='Western Park sports operator under district council lease and service contract. Playing surfaces, fences and routine car-park care differ from the district’s pitch-base, parking-surface and EV maintenance. Ask about the actual task and current contract.')
orgs['he']['description']='Retained-land contact for Phases 2, 3A and 3B, with Inholm, Stirling Fields / Phase 2B and the Education Campus excluded. Exact service contracts, road extents and bin arrangements await Estates confirmation.'
orgs['nha']['description']='Operates the SCDC-owned allotment and orchard land under licence. Confirm the exact maintenance and access scope; the map uses existing OSM footprints.'
orgs['lights'].update(reportUrl=src['light-report']['url'],reportLabel='Report an adopted light fault',source='response-lights',hours='Telephone: Monday–Friday, 9am–5pm. Out-of-hours emergency support is available on the same number.',description='Balfour Beatty handles faults on adopted county lighting. Check current MyMaps and quote the actual column number; the map retains a dated '+county_date+' asset snapshot.')
orgs['hdm']=dict(name='County Highways Development Management',shortName='Developer-light enquiries',color='#987224',description='County team that can identify the relevant developer for lights not yet adopted. Ask about the actual asset; absence from this dated snapshot is not a current adoption decision.',email='Highwaysdevelopment.management@cambridgeshire.gov.uk',phone=None,reportUrl='https://maps.cambridgeshire.gov.uk/mycambs.aspx',reportLabel='Check current county MyMaps',source='response-lights')
orgs['meridian']=dict(name='Meridian Trust / Northstowe Learning Community',shortName='Meridian Trust',color='#297b93',description='Education Campus land/operator enquiry. Homes England identifies the campus as an exception to its retained-land responsibility. Community sports services have a separate P&E Sports contact.',email='office@northstowe.education',phone='01223 343800',reportUrl=src['meridian-contact']['url'],reportLabel='Contact the campus office',source='meridian-contact')

def r(org,cats,note,labels=None,tags=None,evidence='confirmed',caveat=None,date='2026-09-15',sources=None,scopeType='maintenance'):
 return dict(org=org,categories=cats,note=note,scopeLabels=labels or {},detailTags=tags or [],evidence=evidence,confirmedAt=date if evidence in ['confirmed','confirmed-land','confirmed-operator'] else None,scopeType=scopeType,sources=sources or ['response-scdc','response-western'],caveat=caveat,reviewDue='2026-12-01' if org in ['elite','scdc','bowls'] else '2027-01-13')
def bins_enquiry(org,sources):return r(org,['bins'],'Ask the site contact to identify the collection contractor for the actual bin.',evidence='enquiry',date=None,sources=sources,caveat='The maintenance/lease evidence does not identify who empties or repairs individual public bins.',scopeType='enquiry')
def add(id,name,g,rs,**kw):
 if not g.is_valid:g=g.buffer(0)
 assert not g.is_empty and g.is_valid,id
 p=dict(id=id,name=name,status='published',geometryStatus='footprint',geometryNote='OpenStreetMap physical footprint used for orientation, not a surveyed ownership or contract boundary.',context=False,anchor=list(g.representative_point().coords[0]),responsibilities=rs,checked='2026-10-13',responseAddition=True)
 p.update(kw);f=dict(type='Feature',geometry=mapping(g),properties=p);fs.append(f);return f
raw=[]
for name in ['assets-polygons','buildings','highways']:
 raw+=json.loads((ROOT/f'research-boundaries/northstowe-osm-{name}.geojson').read_text())['features']
byid={f['id']:f for f in raw}
xml=ET.parse(ROOT/'research-boundaries/northstowe-osm-map.osm').getroot()
nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in xml.findall('node')}
ways={w.attrib['id']:w for w in xml.findall('way')}
def way_geometry(id):
 w=ways[id];refs=[n.attrib['ref'] for n in w.findall('nd')];coords=[nodes[n] for n in refs]
 return Polygon(coords) if refs[0]==refs[-1] else LineString(coords)

# Complete the H12 enquiry coverage using the same plan/control transform as H1–H11.
# The OSM residential outline alone omits Warren Way. This remains an interpretation
# of a published parcel plan, not confirmation of current ownership or service duties.
h12_pixels=[[723,649],[741,680],[758,708],[783,751],[806,785],[809,804],[802,837],[777,904],[737,890],[698,917],[721,946],[666,984],[619,883],[651,861],[635,830],[618,829],[622,765],[624,734],[632,710],[648,693]]
plan_transform=json.loads((ROOT/'research/plan-transform.json').read_text(encoding='utf8'))
h12_plan=Polygon([[x*plan_transform[0][0]+y*plan_transform[1][0]+plan_transform[2][0],x*plan_transform[0][1]+y*plan_transform[1][1]+plan_transform[2][1]] for x,y in h12_pixels])
h12_osm=shape(byid['way/1187799861']['geometry'])
protected=unary_union([shape(feature(id)['geometry']) for id in ['way-725827724','way-725827723']])
h12_shape=unary_union([h12_osm,h12_plan.difference(protected)])
assert h12_shape.is_valid and not h12_shape.is_empty
h12=feature('way-1187799861');h12['geometry']=mapping(h12_shape)
h12['properties'].update(name='H12 / Warren Way — Linden / Vistry developer enquiry',subtitle='Current maintenance and transfers to be confirmed',
 status='uncertain',geometryStatus='indicative',checked='2026-10-15',anchor=list(h12_shape.representative_point().coords[0]),
 geometryNote='Indicative H12 outline hand-digitised from Greenbelt’s 10 September 2025 parcel plan using the existing approximate plan alignment, combined with OSM way 1187799861. Extends enquiry coverage around Warren Way. Separately mapped Southern Greenway and Bug Hunter Waters land are excluded from the extension. Not a surveyed ownership, highway-adoption or maintenance boundary.',
 geometryUrl=src['greenbelt']['url'],recordLabel='Developer enquiry; current service unconfirmed',
 responsibilities=[r('vistry',['green','water','roads','lighting','play','bins','waste','facilities'],
 'Linden Homes / Vistry is the developer enquiry route for H12, including Warren Way, as located using the published parcel plan.',
 evidence='enquiry',date=None,sources=['greenbelt','report'],scopeType='developer-contact',
 caveat='Current maintenance contracts and subsequent handovers are unconfirmed. This enquiry area does not establish current landownership, highway adoption or responsibility for every private property, tree or bin.')],
 geometryInterpretation=dict(source='greenbelt',method='Hand-digitised H12 outline; existing affine control fit; union with original OSM residential footprint; separate greenway/lake land excluded from extension',pixelOutline=h12_pixels,transform=plan_transform))

# The councillor identified this existing OSM parcel on 15 October. The district
# reply establishes the landowner, not every service contract or a completed transfer.
faith=add('way-725332128','Faith / community land — Urban & Civic enquiry',shape(byid['way/725332128']['geometry']),[
 r('uc',['green','water','roads','lighting','play','bins','waste','facilities'],
   'Urban & Civic is the landowner and enquiry contact for this plot, according to the district council reply of 15 September 2026.',
   evidence='confirmed-land',date='2026-09-15',sources=['response-scdc','osm','contacts'],scopeType='land-contact',
   caveat='Transfer to SCDC and a subsequent faith/community lease were proposed; completion has not been confirmed. Individual maintenance contracts, including bin emptying, remain unconfirmed.')],
 status='uncertain',geometryStatus='indicative',
 geometryNote='Existing OpenStreetMap outline, way 725332128, labelled Faith / community land. Identified by the councillor on 15 October 2026. Used for orientation, not a surveyed ownership or maintenance boundary.',
 geometryUrl='https://www.openstreetmap.org/way/725332128',landOwner='uc',ownershipConfirmedAt='2026-09-15',ownershipSource='response-scdc',
 transferStatus='Transfer pending',proposedRecipient='scdc',checked='2026-10-15',
 recordLabel='Landowner confirmed; transfer pending',roleNote='Urban & Civic landownership confirmed in the September reply. Proposed transfer to SCDC remains unconfirmed; contact Urban & Civic about the land and the relevant service.')

# Task-specific Western Park scopes. Ownership does not duplicate repair responsibility.
western_ids=['way-725332125','way-725332121','way-952350385','way-1030629199','way-952350386','way-929650245']
for id in western_ids:
 p=feature(id)['properties'];p.update(landOwner='scdc',ownershipConfirmedAt='2026-09-15',ownershipSource='response-scdc',operator='bowls' if id=='way-929650245' else 'elite',operatorConfirmedAt='2026-09-15',checked='2026-10-13',recordLabel='Task-specific confirmation from district council')
 p['status']='published'
 if id=='way-725332121':
  p['responsibilities']=[r('elite',['play','green','facilities'],'Elite Sports maintains the playing turf and perimeter fence.',{'play':'Playing turf and perimeter fence','green':'Playing-turf upkeep','facilities':'Pitch fence'},['playing-surface']),r('scdc',['play','facilities'],'SCDC retains maintenance of the shock pads and underlying pitch layers.',{'play':'Shock pads and pitch sublayers','facilities':'Underlying pitch structure'},['pitch-base']),bins_enquiry('elite',['response-scdc'])]
 elif id=='way-952350385':
  p['responsibilities']=[r('elite',['play','facilities'],'Elite Sports manages and maintains the MUGA, fence and adjacent equipment-storage container.',{'play':'MUGA and perimeter fence','facilities':'MUGA fence and storage container'},['sports-equipment','playing-surface']),bins_enquiry('elite',['response-scdc'])]
 elif id=='way-1030629199':
  p['responsibilities']=[r('elite',['facilities','green','play'],'Elite Sports has full internal and external pavilion management and maintenance, including hard and soft landscaping in its leased scope.',{'facilities':'Pavilion, internal and external repairs','green':'Pavilion hard and soft landscaping','play':'Pavilion facilities'},['facility-grounds','sports-equipment'],caveat='The displayed building footprint does not show the complete surrounding leased-landscaping boundary.'),bins_enquiry('elite',['response-scdc'])]
 elif id=='way-929650245':
  p['responsibilities']=[r('bowls',['play','green','facilities'],'Longstanton Bowls Club maintains the bowling green and its fence under licence to SCDC.',{'play':'Bowling green and fence','green':'Bowling-green upkeep','facilities':'Bowling-green fence'},['playing-surface','sports-equipment']),bins_enquiry('bowls',['response-scdc'])]
 else:
  p['responsibilities']=[r('elite',['play','green'],'Elite Sports manages and maintains these grass sports pitches.',{'play':'Grass sports-pitch maintenance','green':'Pitch grass upkeep'},['playing-surface']),bins_enquiry('elite',['response-scdc'])]
carpark=shape(byid['way/725332120']['geometry'])
add('western-carpark','Western Park — car park',carpark,[
 r('elite',['roads','waste','facilities'],'Elite Sports handles car-park general maintenance, cleaning and management.',{'roads':'Car-park routine care','waste':'Car-park cleaning','facilities':'Car-park management'},['carpark-care']),
 r('scdc',['roads','facilities'],'SCDC handles car-park surface repairs and relining.',{'roads':'Car-park surface repairs and markings','facilities':'Parking-surface repairs and relining'},['carpark-surface']),
 r('scdc',['facilities'],'SCDC retains responsibility for the car-park EV charge points.',{'facilities':'EV charge-point maintenance'},['ev-charging']),bins_enquiry('elite',['response-scdc'])],landOwner='scdc',operator='elite',ownershipConfirmedAt='2026-09-15',operatorConfirmedAt='2026-09-15',ownershipSource='response-scdc',geometryUrl='https://www.openstreetmap.org/way/725332120')
access=LineString([(.04920,52.28592),(.04970,52.28579)])
add('western-access','Western Park — accessway enquiry',access,[r('uc',['roads'],'The 2023 responsibilities plan assigns the accessway to L&Q. Urban & Civic is the current successor enquiry route; confirm the present contract and exact accessway extent.',{'roads':'Accessway management and maintenance'},['accessway'],evidence='historical',date=None,sources=['response-western','contacts'],caveat='The plan uses the historic L&Q name. Current responsibility and exact alignment need confirmation.',scopeType='enquiry')],status='uncertain',geometryStatus='indicative',geometryNote='Approximate orientation line at the pavilion/car-park approach, interpreted from the supplied plan. Not a surveyed accessway boundary.')
western=feature('way-725827725')
excluded=unary_union([shape(feature(id)['geometry']) for id in western_ids+['way-952646465','way-952646466']]+[carpark])
western['geometry']=mapping(shape(byid['way/725827725']['geometry']).difference(excluded))
western['properties']['geometryNote']='OSM park footprint with separately mapped sports, pavilion, car-park, allotment and orchard areas excluded. The supplied 2023 plan does not distinguish every current L&Q/Greenbelt contract boundary.'
western['properties']['responsibilities'][0]['sources']=['greenbelt','response-western']
western['properties']['responsibilities'][0]['caveat']='Surrounding landscape is labelled L&Q/Greenbelt in the plan. Confirm the current contract and boundary paths; sports and car-park responsibilities differ.'
feature('bins-western')['geometry']=copy.deepcopy(western['geometry'])
bp=feature('bins-western')['properties']['responsibilities'][0]
suffix=' The new 48-record bin document does not identify its service provider or geolocate its entries; those records have not been assigned to this area.'
if suffix not in bp['caveat']:bp['caveat']+=suffix

# Public OSM campus footprint and an explicitly indicative Inholm orientation envelope.
campus=way_geometry('686098809')
add('education-campus','Education Campus — Meridian Trust',campus,[r('meridian',['green','water','roads','lighting','play','facilities','waste'],'Homes England identifies the Education Campus as occupied and managed by Meridian Trust, outside its general retained-land responsibility.',evidence='confirmed-operator',date='2026-09-17',sources=['response-he','meridian-contact'],scopeType='operator-contact',caveat='This confirms a campus/operator enquiry route. Exact repair contracts and the split with P&E Sports need confirmation.'),bins_enquiry('meridian',['response-he'])],operator='meridian',operatorConfirmedAt='2026-09-17',geometryStatus='indicative',geometryNote='OSM Education Campus outline, way 686098809. Used to display the exception; it is not a verified Meridian maintenance or ownership boundary.',geometryUrl='https://www.openstreetmap.org/way/686098809')
to_bng=Transformer.from_crs(4326,27700,always_xy=True).transform
to_wgs=Transformer.from_crs(27700,4326,always_xy=True).transform
lockhart=[]
for w in ways.values():
 tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')}
 if tags.get('name')=='Lockhart Way':lockhart.append(transform(to_bng,way_geometry(w.attrib['id'])))
inholm=transform(to_wgs,unary_union(lockhart).convex_hull.buffer(35)).difference(campus)
ip=feature('inholm')['properties']
ip.update(name='Inholm / Lockhart Way — estate-manager enquiry',geometryStatus='indicative',geometryNote='Indicative orientation envelope around mapped Lockhart Way streets (35 m buffer), checked against the supplied phasing plan. Full estate/management boundaries are still needed.',anchor=list(inholm.representative_point().coords[0]),excludedFromHomesEngland=True,exclusionConfirmedAt='2026-09-17',checked='2026-10-13')
feature('inholm')['geometry']=mapping(inholm)
ip['responsibilities'][0].update(evidence='enquiry',scopeType='operator-contact',sources=['report','rmg','response-he'],caveat='Homes England confirms Inholm is an exception. Its reply does not confirm RMG’s current appointment or the exact estate maintenance boundary.')
ip['responsibilities']=[q for q in ip['responsibilities'] if not q.get('responseAddition')]
q=bins_enquiry('rmg',['response-he','report']);q['responseAddition']=True;ip['responsibilities'].append(q)
keepmoat=feature('way-905770539')
keepmoat['properties'].update(excludedFromHomesEngland=True,exclusionConfirmedAt='2026-09-17',checked='2026-10-13')
for q in keepmoat['properties']['responsibilities']:
 q['sources']=list(dict.fromkeys(q['sources']+['response-he']));q['evidence']='enquiry'
 q['caveat']='Homes England confirms Stirling Fields / Phase 2B is an exception. Keepmoat is the developer enquiry route; the current estate-manager appointment and individual services remain unconfirmed.'
exceptions=unary_union([campus,inholm,shape(keepmoat['geometry'])])
for id,osm_id,label in [('way-603146096','603146096','Phase 2'),('way-603146095','603146095','Phase 3A'),('phase3b','1210527345','Phase 3B')]:
 f=feature(id);p=f['properties'];g=way_geometry(osm_id)
 if label=='Phase 2':g=g.difference(exceptions)
 f['geometry']=mapping(g);p['anchor']=list(g.representative_point().coords[0])
 p.update(name=label+' — Homes England retained-land contact',geometryStatus='indicative',checked='2026-10-13',recordLabel='Land responsibility confirmed; service details pending')
 p['geometryNote']='OSM development outline used for orientation. Homes England confirms its retained-land role on 17 September 2026. The Phase 2 overlay excludes the mapped campus, Stirling Fields and indicative Inholm area; precise boundaries still need GIS confirmation.'
 p['responsibilities']=[r('he',['green','water','roads','lighting','play','waste','facilities','bins'],'Homes England confirms responsibility for the remaining land in Phases 2, 3A and 3B. Ask its Estates team about the specific maintenance service.',evidence='confirmed-land',date='2026-09-17',sources=['response-he','response-phasing'],scopeType='land-contact',caveat='The general land contact is confirmed; exact road adoption, bin contractors and asset maintenance schedules are still awaited.')]
for f in fs:
 p=f['properties']
 if p.get('context') and any(q['org']=='he' for q in p['responsibilities']) and p['id'] not in ['way-603146096','way-603146095','phase3b']:
  g=shape(f['geometry'])
  if g.intersection(exceptions).area>0:f['geometry']=mapping(g.difference(exceptions).normalize())
  suffix=' The mapped campus, Stirling Fields and indicative Inholm exceptions are excluded.'
  if suffix not in p['geometryNote']:p['geometryNote']+=suffix
for id in ['way-952646465','way-952646466']:
 p=feature(id)['properties'];p.update(landOwner='scdc',operator='nha',ownershipConfirmedAt='2026-09-15',operatorConfirmedAt='2026-09-15',ownershipSource='response-scdc',checked='2026-10-13',roleNote='SCDC freehold; Northstowe Horticultural Association operates under a licence dated 28 August 2020, renewable annually with three months’ notice.')
 suffix=' Ownership/operator roles are confirmed by the district reply. The supplied title plan shows general boundaries and carries reuse restrictions; its outline has not been republished or digitised into this guide.'
 if suffix not in p['geometryNote']:p['geometryNote']+=suffix
 p['responsibilities'][0].update(sources=['nha','directory','response-scdc'],scopeType='operator-contact',evidence='confirmed-operator',confirmedAt='2026-09-15',caveat='Operation under licence is confirmed. Exact maintenance obligations, access boundaries and bin contracts need the licence schedule or an NHA confirmation.')
for f in fs:
 p=f['properties']
 if 'unity centre' in p['name'].lower():p.update(landOwner='scdc',operator='ntc',ownershipConfirmedAt='2026-09-15',operatorConfirmedAt='2026-09-15',ownershipSource='response-scdc',roleNote='Town Council leasehold occupies part of Local Centre Parcel 6; lease extent needs its own scope plan.')
 if p['id'].startswith('StreetLights.'):
  for q in p['responsibilities']:q['sources']=list(dict.fromkeys(q['sources']+['response-lights']))
parish=feature('parish-highways')['properties']
parish['responsibilities']=[q for q in parish['responsibilities'] if not q.get('responseAddition')]
q=r('hdm',['lighting'],'Check current MyMaps first. If a light is not adopted, this team can identify the relevant developer.',evidence='enquiry',date=None,sources=['response-lights'],scopeType='enquiry',caveat='The county confirms developers remain responsible until lighting adoption. Absence from our dated county snapshot does not prove the current status.');q['responseAddition']=True;parish['responsibilities'].append(q)

rows=Document(ROOT/'Northstowe emails/Northstowe Bin Data.docx').tables[0].rows
bins=[]
for row in rows[1:]:
 c=[cell.text.strip() for cell in row.cells]
 if not c[1]:continue
 bins.append(dict(id=f'supplied-bin-{len(bins)+1:02d}',locationDescription=c[0],binType=c[4],binNumber=c[2] or None,collectionDay={'Wed':'Wednesday','Thu':'Thursday'}.get(c[3],c[3] or None),collectionFrequency=None,collector=None,repairContact=None,coordinates=None,locationStatus='Coordinates and unique asset match needed',evidenceStatus='Schedule listed; operator and location unverified',source='response-bins'))
assert len(bins)==48
d['binRegister']=dict(records=bins,source='response-bins',reviewedAt='2026-10-13',serviceEffectiveDate=None,note='The supplied document lists 48 separate records. Repeated descriptions are retained. Collection days are transcribed; a weekday is not confirmation of frequency or contractor. Coordinates and the covering service confirmation are still needed.',counts=dict(total=48,Wednesday=46,Thursday=2,geolocated=0,numbered=2))
d['transfers']=[
 dict(id='faith-community',name='Phase 1 Faith and Community Land',currentContact='uc',proposedRecipient='SCDC, then the selected faith/community organisation',status='Transfer pending',asOf='2026-09-15',note='District reply says the land remained with Urban & Civic; a future SCDC transfer/lease was expected. The existing OSM footprint is now mapped as a landowner enquiry.',geometryStatus='Indicative OSM footprint mapped; not a surveyed ownership boundary',featureId='way-725332128',source='response-scdc'),
 dict(id='eastern-sports',name='Eastern Sports Hub',currentContact='he',proposedRecipient='South Cambridgeshire District Council',status='Transfer pending',asOf='2026-09-15',note='Homes England remained responsible until the land transfer completed.',geometryStatus='Proposed location only; transfer extent not supplied',source='response-scdc'),
 dict(id='town-hub',name='Town Hub',currentContact='he',proposedRecipient='South Cambridgeshire District Council',status='Transfer pending',asOf='2026-09-15',note='The future Town Hub is distinct from the existing Unity Centre lease. No completed transfer was reported.',geometryStatus='No confirmed boundary supplied',source='response-scdc')]
d['unmappedAssets']=[dict(name='Local Centre and Enterprise Zone',owner='scdc',note='District council confirms land holdings. Its Commercial Assets team must supply public-realm boundaries, contracts and bin arrangements.',source='response-scdc'),dict(name='Unity Centre lease extent / Parcel 6',owner='scdc',operator='ntc',note='Town Council leasehold is part of Local Centre Parcel 6. A lease scope plan is needed for surrounding assets.',source='response-scdc')]
d['governance']=dict(owner=None,status='Register owner to be agreed',proposedOwner='A nominated Town Council map editor, with partner organisations confirming their records',reviewFrequency='Quarterly review proposed; not yet agreed',note='The district Communities Team says it cannot resource a complete maintained register. No organisation has been assigned that duty by this guide.')
d['reviews']=[dict(id='elite-contract',title='Western Park operator contract and licence review',due='2026-12-01',status='Suggested review',note='Lease began 3 January 2024 for five years; the operator contract has an initial three-year term plus optional extensions. Confirm contract dates and renewal before January 2027; early contract termination also ends the lease.',source='response-scdc'),dict(id='handover-review',title='Pending handovers and estate boundaries',due='2027-01-13',status='Suggested review',note='Reconfirm the dated transfer positions and obtain Estates/GIS boundaries.',source='response-he'),dict(id='bins-review',title='Public-bin location and contractor register',due='2026-11-13',status='Suggested review',note='Obtain coordinates, identifiers, collection contractor/frequency and repair responsibility.',source='response-bins')]
gaps={g['id']:g for g in d['gaps']}
gaps['transfers']['detail']='Western Park task splits and general Homes England exceptions are now supported by dated replies. Exact current GIS handover boundaries remain outstanding; pending transfers are listed separately.'
gaps['highways']['detail']='County lighting confirms MyMaps and Balfour Beatty reporting, with Highways Development Management for developer identification. County records refreshed '+county_date+'; individual adoption dates, exact highway extents and developer inventories remain needed.'
gaps['phase3']['detail']='Homes England confirmed its retained-land role in Phases 2, 3A and 3B on 17 September, excluding Inholm, Stirling Fields and the Education Campus. Exact GIS extents and detailed maintenance contracts are awaited.'
gaps['bins']['detail']='48 supplied bin records are now searchable, with 46 Wednesday and 2 Thursday entries. Coordinates, most bin IDs, the service provider, repair contact, frequency and effective date remain unconfirmed.'
gaps['estate']['detail']='The HE exceptions are mapped indicatively. Current RMG/Keepmoat estate appointments and maintenance schedules still need confirmation; Meridian’s campus enquiry is distinct from P&E Sports services.'
gaps['review']['detail']='The district Communities Team cannot maintain the register. Agree a nominated Town Council editor and partner review process; proposed review dates are displayed but not agreed obligations.'
d['checked']='2026-10-15';d['responseUpdateVersion']=3
d['audit']['counts'].update(features=len(fs),organisations=len(orgs));d['audit']['binRegisterRecords']=48;d['audit']['correspondenceDates']=['2026-09-15','2026-09-17'];d['audit']['responseReviewed']='2026-10-13'
d['audit']['faithCommunityMapped']='2026-10-15'
d['audit']['warrenWayMapped']='2026-10-15'
d['audit']['note']='Correspondence reviewed 13 October 2026. County records refreshed '+county_date+'; OSM remains the 11 September snapshot. Confirmation of a landowner or operator does not establish every maintenance contract; exact boundaries and current transfers remain subject to review.'
(out/'responsibilities.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(out/'responsibility-areas.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=fs),ensure_ascii=False,separators=(',',':')),encoding='utf8')
(out/'bin-register.json').write_text(json.dumps(d['binRegister'],ensure_ascii=False,indent=2),encoding='utf8')
notes=['# Northstowe responsibility register','Updated from organisation replies: 13 October 2026. County records refreshed '+county_date+'; OSM physical footprints remain the 11 September snapshot.','','## Confirmations','Western Park: operator and district repair scopes are separate. Mini/grass pitches route to Elite Sports; shock pads/sublayers and car-park surface/EV assets route to SCDC. Surrounding landscaping and the historical L&Q accessway still need exact current boundaries.','Homes England: retained land in Phases 2, 3A and 3B, with explicit Inholm, Stirling Fields and Education Campus exceptions. This is a confirmed land contact, not a verified inventory of every maintenance service.','Lighting: county MyMaps identifies adopted assets; Balfour Beatty reporting and HDM escalation are recorded. The refreshed inventory retains 50 explicitly county-owned light points, 6 adopted-highway records, 2 prospective records, 176 gullies and 11 rights-of-way records.','Bins: 48 unlocated schedule records; 46 Wednesday, 2 Thursday; only 2 supplied bin numbers. No contractor or repair responsibility inferred.','','## Ownership, contracts and transfers','SCDC owns the identified Western Park sports facilities and allotment/orchard land. NHA operates the allotment/orchard under licence. The title-plan image or traced boundary is not republished. Pending Faith/Community, Eastern Sports Hub and Town Hub transfers retain their last confirmed contacts.','','## Remaining gaps']
notes[2:2]=['Faith / community land added 15 October 2026 using existing OSM way 725332128, identified by the councillor. Urban & Civic is the confirmed landowner/enquiry contact in the 15 September reply; SCDC transfer remains pending. Service contracts and the surveyed boundary are not established by this footprint.']
notes[3:3]=['H12 / Warren Way enquiry coverage extended 15 October 2026 by interpreting the published Greenbelt parcel plan. Linden/Vistry is a developer enquiry route; current ownership, individual maintenance services and later transfers remain unconfirmed. The original OSM footprint is retained; separately mapped greenway and Anglian Water land are excluded from the extension.']
for g in d['gaps']:notes += [f"### {g['title']}",g['detail'],'Information holder: '+g['holder']]
notes+=['','## Sources']
for id,s in src.items():notes.append(f"- {id}: {s['title']} — {s['publisher']}; {s['date']}. "+(s['url'] if s.get('url') else 'Original evidence held privately; public summary only.'))
notes+=['','## Feature register']
for f in fs:
 p=f['properties'];notes += ['### '+p['name'],p['geometryNote']]
 for q in p['responsibilities']:notes.append(f"- {orgs[q['org']]['name']}: {q['note']} {q.get('caveat') or ''} Evidence: {q.get('evidence','published source')}; confirmed: {q.get('confirmedAt') or 'not supplied'}. Sources: {', '.join(q['sources'])}.")
notes+=['','## Attribution','Parish boundary: ONS/OS, December 2025, © Crown copyright and database right. County mapping: © Crown copyright and database rights 2026 OS AC0000822131. Geometry: © OpenStreetMap contributors, ODbL. Approximate estate/access interpretations are for orientation. Source publishers retain their rights; raw private correspondence and supplied title-plan images are excluded from the public app.']
(out/'research-notes.md').write_text('\n'.join(notes)+'\n',encoding='utf8')
print('Applied response updates:',len(fs),'features;',len(orgs),'organisations; 48 bin-register records, 0 guessed bin locations.')
