"""Build a reproducible public-source guide. OSM shapes never establish maintenance rights."""
from pathlib import Path
import json, sys, re, collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape, mapping, Polygon
from shapely.ops import unary_union
OUT=ROOT/'public/data';OUT.mkdir(exist_ok=True,parents=True)
def read(group):return json.loads((ROOT/f'research-boundaries/northstowe-osm-{group}.geojson').read_text(encoding='utf-8'))['features']
polys=read('assets-polygons');buildings=read('buildings');roads=read('highways');points=read('assets-points');byid={f['id']:f for f in polys+buildings+roads+points}
parish=json.loads((OUT/'parish.geojson').read_text(encoding='utf-8-sig'));parish_shape=shape(parish['features'][0]['geometry'])
sources={}
def source(id,title,publisher,date,url):sources[id]=dict(title=title,publisher=publisher,date=date,url=url)
source('report','Town Council reporting guide','Northstowe Town Council','Legacy page; contains 2024–25 information','https://www.northstowetowncouncil.gov.uk/Report_it_42970.aspx')
source('greenbelt','Greenbelt maintenance presentation, slides 9–12','Greenbelt / SCDC','10 September 2025','https://www.scambs.gov.uk/media/gohlif3m/greenbelt-sep-25.pptx')
source('greenplan','Greenbelt greenspace plan','Greenbelt / Town Council','March 2025; filename 2 April 2025','https://www.northstowetowncouncil.gov.uk/_UserFiles/Files/3772%20Greenspace%20Plan%20Master%2002.04.2025.pdf')
source('faq','Who manages public spaces?','Homes England / Northstowe','Undated; checked 11 September 2026','https://www.northstowe.com/faqs')
source('forum','Community Forum updates','South Cambridgeshire District Council','Archive December 2024–July 2026; dates vary','https://www.scambs.gov.uk/community-and-people/community-forums/northstowe-community-forum')
source('common','Community facilities and roadworks','South Cambridgeshire District Council','Reviewed 7 September 2026','https://www.scambs.gov.uk/community-and-people/northstowe/common-northstowe-questions')
source('highways','Highway records and current adoption map','Cambridgeshire County Council','Checked 11 September 2026','https://www.cambridgeshire.gov.uk/residents/travel-roads-and-parking/roads-and-pathways/highway-records')
source('highreport','Report a highway fault','Cambridgeshire County Council','Live reporting service','https://highwaysreporting.cambridgeshire.gov.uk/')
source('waste','Report a fly-tip in South Cambridgeshire','Greater Cambridge Shared Waste','Reviewed 1 September 2025','https://www.greatercambridgewaste.org/litter-in-public-spaces/report-a-fly-tip-south-cambs/')
source('aw','Water and sewerage problems','Anglian Water','Checked 11 September 2026','https://www.anglianwater.co.uk/global-faq/where-can-i-report-an-emergency')
source('uc','Urban & Civic contact details','Urban & Civic','Checked 11 September 2026','https://www.urbanandcivic.com/contact/')
source('rmg','RMG contact and repair reporting','Residential Management Group','Checked 11 September 2026','https://www.rmguk.com/contact-rmg/')
source('nha','Community orchard and allotments','Homes England / Northstowe','Checked 11 September 2026','https://www.northstowe.com/wellbeing-sustainability')
source('directory','Community contact directory','Homes England / Northstowe','Checked 11 September 2026','https://www.northstowe.com/community-resources')
source('master','Northstowe phase map','Homes England / Northstowe','February 2025; illustrative, not to scale','https://www.northstowe.com/s/NORTHSTOWE-MASTER-MAP-25-v4.pdf')
source('ons','Northstowe civil parish boundary (E04013120)','Office for National Statistics','December 2025 boundary edition','https://www.data.gov.uk/dataset/9e2e964d-c6c0-4c1f-a8c9-83cbf662ebf0/parishes-and-non-civil-parished-areas-december-2025-boundaries-ew-bfe')
source('osm','Geographic footprints and street centrelines','OpenStreetMap contributors','Downloaded 11 September 2026','https://www.openstreetmap.org/copyright')
orgs={}
def org(id,name,color,description,reportUrl=None,email=None,phone=None,sourceid=None,shortName=None,reportLabel=None):orgs[id]=dict(name=name,color=color,description=description,reportUrl=reportUrl,email=email,phone=phone,source=sourceid,shortName=shortName,reportLabel=reportLabel)
org('greenbelt','Greenbelt','#23815d','Transferred Phase 1 open spaces. House-parcel transfers and individual assets need checking.', 'https://www.greenbelt.co.uk/contact-us/','customercare@greenbelt.co.uk','0800 028 1749','greenbelt')
org('aw','Anglian Water','#1674b5','Bug Hunter Waters and associated land; water and sewerage faults. Other lakes have different contacts.', 'https://www.anglianwater.co.uk/help-and-advice/report-an-issue/','CustService@anglianwater.co.uk','03457 145 145','report')
org('uc','Urban & Civic','#ad6824','Phase 1 master developer, formerly L&Q Estates. The forum gives 01223 622533 for local roadworks enquiries. The email is the corporate enquiry route.', 'https://www.urbanandcivic.com/contact/','info@urbanandcivic.com','01223 622533','forum')
org('he','Homes England','#7458a4','Open-space and land enquiries for Phases 2 and 3. Estates number published by Northstowe.com.', 'https://www.northstowe.com/contact','northstowe2@homesengland.gov.uk','01925 844057','faq')
org('ccc','Cambridgeshire County Council','#315b80','Adopted highways and their assets. Check the current adoption record before assuming a new road is publicly maintained.', 'https://highwaysreporting.cambridgeshire.gov.uk/',None,None,'highways','County Council','Report highway fault')
org('scdc','South Cambridgeshire District Council','#b84d61','District land and community-facility enquiries. The community team can help identify the correct contact where responsibility remains unclear.', 'https://www.scambs.gov.uk/contact-us','northstowe.community@scambs.gov.uk',None,'directory','District Council','Contact the district council')
org('waste','Greater Cambridge Shared Waste','#6d7680','Fly-tipping reports for South Cambridgeshire. Reporting an incident does not establish who must clear private land.',sources['waste']['url'],None,None,'waste','Waste reporting','Report fly-tipping')
org('ntc','Northstowe Town Council','#087d89','Unity Centre operations and Town Council enquiries. The Town Council does not maintain every public space.', 'https://www.northstowe-tc.gov.uk/contact/',None,None,'faq','Town Council')
org('elite','Elite Sports UK','#ba4e87','Operator of Western Park Pavilion and sports pitches for the district council.', 'https://elitesportsuk.com/contact/',None,None,'common','Elite Sports')
org('bowls','Longstanton Bowls Club','#9a5165','Operator of the Western Park bowling green.', 'https://www.northstowe.com/community-resources',None,None,'common','Bowls Club','Find club contact')
org('nha','Northstowe Horticultural Association','#688227','Community orchard and allotment enquiries.',None,'northstoweallotments@gmail.com',None,'directory','Horticultural Association')
org('vistry','Vistry / Bovis / Linden Homes','#d27730','Housebuilder enquiry route for Bovis and Linden parcels. The exact maintenance scope depends on completed transfers.', 'https://www.bovishomes.co.uk/contact-us','CustomerService.EastAnglia@vistry.co.uk',None,'report','Vistry')
org('barratt','Barratt / David Wilson Homes','#9b5f47','Housebuilder enquiry route for Barratt and David Wilson parcels. Greenbelt maintains certain transferred green spaces.', 'https://www.dwh.co.uk/customer-service/','easterncounties@newhomecare.co.uk',None,'report','Barratt / DWH')
org('bloor','Bloor Homes','#897045','Housebuilder enquiry route for parcel H1; Greenbelt is listed for transferred open space.', 'https://bloorhomes.com/contact-us',None,None,'greenbelt','Bloor')
org('taylor','Taylor Wimpey','#a44f40','Housebuilder enquiry route for H3, H10, H11 and H13. Verify the specific street or asset and any subsequent transfer.', 'https://www.taylorwimpey.co.uk/support/contact-us',None,None,'greenplan','Taylor Wimpey')
org('keepmoat','Keepmoat','#6b61a6','Stirling Fields housebuilder enquiries. Confirm the responsible estate manager for each communal asset.', 'https://www.keepmoat.com/contact-us',None,None,'faq','Keepmoat')
org('rmg','Residential Management Group (RMG)','#725380','Inholm estate management, as identified by the legacy Town Council guide. Confirm that RMG still manages the particular asset.', 'https://www.rmguk.com/contact-rmg/','customerservice@rmguk.com','0345 002 4444','rmg','RMG')
features=[]
def responsibility(o,c,n,s,caveat=None):return dict(org=o,categories=c,note=n,sources=s,caveat=caveat)
def add(id,name,geometry,rs,status='published',geometryStatus='footprint',geometryNote='OpenStreetMap footprint: locates the asset, not its legal maintenance boundary.',geometryUrl=None,context=False,subtitle=None):
    g=shape(geometry)
    # Keep full footprints, including context outside the parish, and state that explicitly.
    if g.is_empty or not g.is_valid:raise ValueError((id,'invalid geometry'))
    anchor=g.representative_point()
    f=dict(type='Feature',geometry=mapping(g),properties=dict(id=id,name=name,responsibilities=rs,status=status,geometryStatus=geometryStatus,geometryNote=geometryNote,geometryUrl=geometryUrl,context=context,subtitle=subtitle,anchor=list(anchor.coords[0]),checked='2026-09-11'))
    features.append(f);return f
def asset(osmid,name,rs,**kw):
    f=byid[osmid];return add(osmid.replace('/','-'),name,f['geometry'],rs,geometryUrl=f['properties']['osm_url'],**kw)
gb=responsibility('greenbelt',['green','roads','waste'],'Greenbelt is the published contact for the transferred open space and its landscape assets.',['greenbelt'], 'Confirm the precise asset on the current maintenance plan, especially boundary paths and bins.')
names={'way/693284884':'The Green','way/701110565':'Pioneer Park','way/725827725':'Western Park — landscape areas','way/725807711':'Central Greenway','way/725827724':'Southern Greenway','way/725827726':'Western green corridor','way/725827727':'Northern Greenway','way/725827728':'Greenway by LEAP 1','way/725827729':'Greenway by Kingfisher Pond','way/1254885079':'Greenway by H10 / H11'}
for id,name in names.items():asset(id,name,[gb],geometryStatus='indicative',geometryNote='OpenStreetMap park footprint matched to Greenbelt’s September 2025 plan. Exact transferred boundaries need confirmation.')
asset('way/161965235','Kingfisher Pond',[responsibility('greenbelt',['water','green','waste'],'Published Greenbelt landscape plan includes Kingfisher Pond.',['greenbelt'])])
for id,name in [('way/703060917','LEAP 1 — play area'),('way/703060918','LEAP 2 — play area'),('way/1013344672','LEAP 3 — play area by H9')]:asset(id,name,[responsibility('greenbelt',['play','green','waste'],'Play area shown within Greenbelt’s managed landscape.',['greenbelt'])])
asset('way/562586195','Bug Hunter Waters — lake',[responsibility('aw',['water','waste'],'Lake maintenance and faults: Anglian Water.',['report','aw'])])
asset('way/725827723','Bug Hunter Waters — surrounding land',[responsibility('aw',['green','roads','waste'],'The Town Council identifies Anglian Water for the lake’s surrounding land.',['report']),responsibility('uc',['lighting'],'The P&R–Stirling Road path lights are separately listed under Urban & Civic.',['report'],'This exception applies only to that path, not every light inside this area. Current transfer status needs checking.')],geometryStatus='indicative',geometryNote='OpenStreetMap water-park outline. The exact Anglian Water estate boundary and lighting inventory are unavailable.')
for id,name in [('relation/16915052','Unity Lake'),('way/725827721','Halcyon Mere'),('way/1212262050','Phase 2 water park')]:asset(id,name,[responsibility('he',['water','green','roads','waste'],'Homes England is the published contact for Phase 2 lakes and surrounding open space.',['faq','report'])])
asset('relation/53634','Airfield Lake — Phase 3 enquiry',[responsibility('he',['water','green','waste'],'Ask Homes England to confirm responsibility for this asset within the Phase 3 development area.',['faq','master'],'No asset-specific maintenance or handover record was located.')],status='uncertain')
asset('way/1419227309','Pump track / BMX track',[responsibility('he',['play','waste'],'Homes England delivered the track; use the Estates team to confirm the current maintenance operator.',['forum','faq'],'Construction delivery does not itself establish the current maintenance contract.')],status='uncertain')
for id,name in [('way/725332125','Western Park — grass sports pitches'),('way/725332121','Western Park — 4G pitch'),('way/952350385','Western Park — MUGA / tennis'),('way/1030629199','Western Park Pavilion')]:asset(id,name,[responsibility('elite',['play','lighting','facilities','waste'],'Contact the sports-facility operator for defects within the managed facility.',['common'])])
asset('way/952350386','Western Park — mini football pitches',[responsibility('scdc',['play','waste'],'Confirm which maintenance contract covers these open mini pitches.',['common','greenbelt'],'The public sources do not define the dividing line between the landscape and sports contracts.')],status='uncertain')
asset('way/929650245','Western Park — bowling green',[responsibility('bowls',['play','green','facilities','waste'],'Bowling green operator: Longstanton Bowls Club.',['common'])])
for id,name in [('way/952646465','Phase 1 allotments'),('way/952646466','Community Orchard')]:asset(id,name,[responsibility('nha',['green','facilities','waste'],'Community orchard and allotment management.',['nha','directory'])])
for id,name in [('way/1427479242','Unity Centre — building'),('way/1427479243','Unity Centre — garden')]:asset(id,name,[responsibility('ntc',['facilities','lighting','green','waste'],'The Town Council operates the Unity Centre, handed over in March 2026.',['common','faq'])])
for id,name in [('way/603146096','Phase 2 — broad Homes England enquiry area'),('way/603146095','Phase 3A — broad Homes England enquiry area'),('way/905770538','Future town centre — Homes England enquiry')]:asset(id,name,[responsibility('he',['green','water','roads','lighting','play','waste','facilities'],'Homes England can identify the relevant retained-land or development contact.',['faq','master'],'Individual sold plots, school sites and estate assets may be another party’s responsibility.')],status='uncertain',context=True,geometryStatus='indicative',geometryNote='Community-mapped development footprint for orientation only. Not a complete phase, ownership or maintenance boundary.')
asset('way/905770539','Stirling Fields — Keepmoat enquiry',[responsibility('keepmoat',['green','roads','lighting','play','waste'],'Housebuilder enquiry for the Stirling Fields development.',['faq'],'An asset-by-asset estate maintenance schedule was not found.')],status='uncertain',geometryStatus='indicative',geometryNote='OpenStreetMap development footprint, which may exclude completed sections. Confirm the individual address.')
asset('way/725805927','H13 — Taylor Wimpey',[responsibility('taylor',['green','roads','lighting','play','waste'],'Housebuilder contact for this parcel pending confirmation of subsequent transfers.',['greenplan','report'])],status='uncertain',geometryStatus='indicative')
asset('way/1187799861','H12 — Linden / The Boulevards',[responsibility('vistry',['green','roads','lighting','play','waste'],'Housebuilder contact for this parcel pending confirmation of subsequent transfers.',['greenplan','report'])],status='uncertain',geometryStatus='indicative')
# A parish-wide reporting layer is a service area, not an ownership assertion.
add('parish-waste','Fly-tipping reporting — whole parish',parish['features'][0]['geometry'],[responsibility('waste',['waste'],'Report fly-tipping here, including its location and photographs.',['waste'],'Clearance on private land must also be raised with the relevant landowner or manager.')],context=True,geometryStatus='official',geometryNote='ONS civil parish boundary used as a reporting-service area only.')
add('parish-highways','Highway adoption checks — whole parish',parish['features'][0]['geometry'],[responsibility('ccc',['roads','lighting'],'Use the county adoption map to check whether a particular road is publicly maintained.',['highways'],'This overlay does not mean that all Northstowe roads or lights are adopted.')],context=True,geometryStatus='official',geometryNote='Parish-wide enquiry coverage only; not an adopted-highway boundary.')
# Main road lines are grouped for usable search, with current adoption explicitly unresolved.
for name in ['Pathfinder Way','Links Lane','Wellington Road','Eagle Way']:
    fs=[f for f in roads if f['properties'].get('name')==name and f['properties']['intersects_official_parish']]
    if fs:add('road-'+name.lower().replace(' ','-'),name+' — main road',mapping(unary_union([shape(f['geometry']) for f in fs])),[responsibility('uc',['roads','lighting'],'Phase 1 distributor-road enquiry; July 2026 updates still describe finishing works.',['forum','report'],'Finishing works are not proof of adoption. Check the county’s current record for the exact section.')],status='uncertain',geometryStatus='indicative',geometryNote='OpenStreetMap road centrelines. Highlight width is for visibility, not the highway extent.')
gaps=[
 dict(id='transfers',title='Exact maintenance and transfer boundaries',detail='Current GIS polygons and dated handover schedules for Greenbelt, Urban & Civic, Anglian Water and every house parcel. The public plans mix existing and proposed management.',holder='Greenbelt, Urban & Civic, Anglian Water and housebuilders'),
 dict(id='highways',title='Current road, footpath and lighting adoption',detail='Segment-level adoption dates, Section 38 plans, responsibility during the maintenance period and a lighting asset list. The 2025 adoption expectation is not treated as completed.',holder='Cambridgeshire County Council and developers'),
 dict(id='h4',title='H4 trees and parcel-specific exceptions',detail='Greenbelt listed H4 open space in September 2025, but the same forum separately said H4 street trees remain with the developer. Identify the exact trees and scope.',holder='Greenbelt and Vistry'),
 dict(id='hatton',title='Hatton Road drainage ponds',detail='December 2024 forum notes say Urban & Civic retained maintenance. A later completed-transfer record has not been located. Parts lie outside Northstowe parish.',holder='Urban & Civic and Greenbelt'),
 dict(id='phase3',title='Phase 3B and remaining development land',detail='The OSM Phase 3 polygon is not the full Phase 3B area. Obtain the current phase, ownership and maintenance polygons, including land west of Phase 1.',holder='Homes England and development partners'),
 dict(id='bins',title='Bins, benches, play equipment and street furniture',detail='Asset identifiers, precise points and the split between emptying, cleansing, repair and replacement contracts. A park-level contact cannot resolve every bin or light.',holder='Councils, Greenbelt and land managers'),
 dict(id='estate',title='Inholm and Stirling Fields estate schedules',detail='Current estate-manager appointment, scope plans, retained developer assets and transfers; these may differ from the development footprint.',holder='RMG, Homes England, Keepmoat and estate companies'),
 dict(id='review',title='Named owner of the maintained register',detail='Agree a council contact to approve corrections and record changes when assets transfer. No requests have been sent as part of this research.',holder='Town Council and partner organisations')]
search=[]
for name,fs in __import__('itertools').groupby(sorted([f for f in roads if f['properties'].get('name') and f['properties']['intersects_official_parish']],key=lambda f:f['properties']['name']),key=lambda f:f['properties']['name']):
    fs=list(fs);g=unary_union([shape(f['geometry']) for f in fs]);search.append(dict(type='Feature',geometry=mapping(g),properties=dict(id='search-'+name,name=name,searchOnly=True,anchor=list(shape(fs[0]['geometry']).interpolate(.5,normalized=True).coords[0]))))
data=dict(checked='2026-09-11',organisations=orgs,sources=sources,features=features,searchPlaces=search,gaps=gaps)
(OUT/'responsibilities.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'responsibility-areas.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
notes=['# Northstowe responsibility map — research register','Checked: 11 September 2026','', 'Full parish coverage means the complete official parish boundary is shown. It does not mean every maintenance responsibility has been established. OSM geometry is not ownership evidence.','', '## Gaps']
for g in gaps:notes += [f"### {g['title']}",g['detail'],f"Information holder: {g['holder']}",'']
notes+=['## Sources']
for s in sources.values():notes += [f"- [{s['title']}]({s['url']}) — {s['publisher']}; {s['date']}"]
notes+=['','## Feature register']
for f in features:
 p=f['properties'];notes += [f"### {p['name']}",f"Evidence: {p['status']}. Geometry: {p['geometryNote']}"]
 for r in p['responsibilities']:notes += [f"- {orgs[r['org']]['name']}: {', '.join(r['categories'])}. {r['note']} {r.get('caveat') or ''} Sources: {', '.join(r['sources'])}."]
(OUT/'research-notes.md').write_text('\n'.join(notes),encoding='utf-8')
print(json.dumps(dict(features=len(features),searchable_streets=len(search),organisations=len(orgs),sources=len(sources))))
