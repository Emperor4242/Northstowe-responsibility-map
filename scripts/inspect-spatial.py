from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'research-boundaries/_deps'))
from shapely.geometry import shape
from PIL import Image,ImageDraw
raw=json.loads((ROOT/'research-boundaries/northstowe-osm-assets-polygons.geojson').read_text(encoding='utf-8'))['features']
for f in raw:
 if '3b' in f['properties'].get('name','').lower():print('PHASE3B',f['id'],f['properties'],shape(f['geometry']).bounds)
s=(ROOT/'research/town-contact.html').read_text(encoding='utf-8')
for h in re.findall(r'data-cfemail="([a-f0-9]+)"',s):
 b=bytes.fromhex(h);print('TOWN EMAIL:',bytes(c^b[0] for c in b[1:]).decode())
d=json.loads((ROOT/'public/data/responsibilities.json').read_text(encoding='utf-8'));p=shape(json.loads((ROOT/'public/data/parish.geojson').read_text(encoding='utf-8'))['features'][0]['geometry'])
im=Image.new('RGB',(1300,1500),'#ffffff');draw=ImageDraw.Draw(im,'RGBA')
def xy(coords):return [(int((x-.032)/.048*1250+25),int((52.299-y)/.039*1450+25)) for x,y in coords]
for f in json.loads((ROOT/'research-boundaries/northstowe-osm-highways.geojson').read_text(encoding='utf-8'))['features']:
 g=shape(f['geometry']);draw.line(xy(g.coords),fill='#bcc4c9',width=1)
for f in d['features']:
 prop=f['properties'];g=shape(f['geometry']);color=d['organisations'][prop['responsibilities'][0]['org']]['color']
 if prop['context']:continue
 if g.geom_type=='Polygon':
  c=tuple(bytes.fromhex(color[1:]));draw.polygon(xy(g.exterior.coords),fill=c+(55,),outline=c+(255,))
  if prop['id'].startswith('parcel-') or prop['name'] in ['The Green','Pioneer Park','Kingfisher Pond','Bug Hunter Waters — lake']:
   c=g.representative_point();draw.text(xy([(c.x,c.y)])[0],prop['id'].replace('parcel-','') if prop['id'].startswith('parcel-') else prop['name'],fill='black')
draw.line(xy(p.exterior.coords),fill='black',width=2);im.save(ROOT/'research/spatial-check.png')
