"""Convert the public county WFS snapshot, retaining source attributes and IDs."""
from pathlib import Path
import sys,json,xml.etree.ElementTree as ET,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape,mapping,Point,LineString,MultiLineString,Polygon,MultiPolygon
from shapely.ops import transform
from pyproj import Transformer
ns={'g':'http://www.opengis.net/gml','m':'http://mapserver.gis.umn.edu/mapserver'}
parish=json.loads((ROOT/'research-boundaries/northstowe-parish-ons-dec2025-epsg27700.esrijson').read_text(encoding='utf-8-sig'))
pg=Polygon(parish['features'][0]['geometry']['rings'][0]);trans=Transformer.from_crs(27700,4326,always_xy=True)
def coords(e):
 a=list(map(float,e.text.split()));return list(zip(a[::2],a[1::2]))
def geometry(e):
 t=e.tag.split('}')[-1]
 if t=='Point':return Point(coords(e.find('g:pos',ns))[0])
 if t=='LineString':return LineString(coords(e.find('g:posList',ns)))
 if t=='MultiCurve':return MultiLineString([geometry(x[0]) for x in e])
 if t=='Polygon':return Polygon(coords(e.find('g:exterior/g:LinearRing/g:posList',ns)),[coords(x) for x in e.findall('g:interior/g:LinearRing/g:posList',ns)])
 if t=='MultiSurface':return MultiPolygon([geometry(x[0]) for x in e])
 raise ValueError(t)
stats={}
fetch_status=ROOT/'research/county-fetch-status.json'
retrieved='2026-09-12'
if fetch_status.exists():
 status=json.loads(fetch_status.read_text(encoding='utf8'))
 assert all(r['success'] for r in status['results']),'Do not date a partial refresh as a complete snapshot'
 retrieved=status['retrieved'][:10]
for layer in ['AdoptedRoads','Section38Streets','StreetLights','row','Gullies','SouthCambsDCAssets']:
 root=ET.parse(ROOT/f'research/county-{layer}.gml').getroot();members=root.findall('g:featureMember',ns)
 assert len(members)<10000,'Potentially truncated WFS result'
 fs=[]
 for member in members:
  record=member[0];g=geometry(record.find('m:msGeometry',ns)[0]);attrs={x.tag.split('}')[-1]:(x.text or '') for x in record if x.tag.startswith('{'+ns['m']+'}') and x.tag.split('}')[-1]!='msGeometry'}
  if not g.intersects(pg):continue
  assert g.is_valid,(layer,attrs)
  # Keep complete features at parish edges, with intersections tested in native BNG.
  attrs.update(source_id=record.attrib['{'+ns['g']+'}id'],source_layer=layer,source_url=(ROOT/f'research/county-{layer}-url.txt').read_text(),retrieved=retrieved)
  fs.append(dict(type='Feature',geometry=mapping(transform(trans.transform,g)),properties=attrs))
 (ROOT/f'research-boundaries/county-{layer}.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=fs),ensure_ascii=False),encoding='utf-8')
 stats[layer]=dict(returned=len(members),intersect_parish=len(fs),names=sorted(set(f['properties'].get('street') or f['properties'].get('name') or f['properties'].get('road_name') or f['properties'].get('property_name') for f in fs)))
 if layer=='StreetLights':stats[layer]['owners']=dict(collections.Counter(f['properties']['owner'] for f in fs))
print(json.dumps(stats,indent=2))
(ROOT/'research/county-provenance.json').write_text(json.dumps(dict(retrieved=retrieved,stats=stats,method='WFS 1.1.0 bbox in BNG; exact intersects with official ONS parish polygon in BNG; retain full source feature at edges; PROJ conversion EPSG:27700 to EPSG:4326, always_xy.',transform=trans.description,accuracy_m=trans.accuracy,attribution='© Crown copyright and database rights 2026 OS AC0000822131'),indent=2),encoding='utf-8')
