from pathlib import Path
import json,urllib.request,urllib.parse,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'research-boundaries/northstowe-parish-ons-dec2025-epsg27700.esrijson').read_text(encoding='utf-8-sig'))['features'][0]['geometry']['rings'][0]
box=[min(x[0] for x in p)-100,min(x[1] for x in p)-100,max(x[0] for x in p)+100,max(x[1] for x in p)+100]
def fetch(layer):
 params=dict(MapSource='CCC/AllMaps',service='WFS',version='1.1.0',request='GetFeature',typeName=layer,srsName='EPSG:27700',bbox=','.join(map(str,box))+',EPSG:27700',maxFeatures=10000)
 url='https://maps.cambridgeshire.gov.uk/getows.ashx?'+urllib.parse.urlencode(params)
 try:
  data=urllib.request.urlopen(url,timeout=50).read();(ROOT/f'research/county-{layer}.gml').write_bytes(data)
  (ROOT/f'research/county-{layer}-url.txt').write_text(url)
  return layer,len(data),data[:220].decode()
 except Exception as e:return layer,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for result in pool.map(fetch,['AdoptedRoads','Section38Streets','StreetLights','row','Gullies','SouthCambsDCAssets']):print(result)
