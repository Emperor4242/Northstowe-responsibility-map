from pathlib import Path
import json,urllib.request,urllib.parse,concurrent.futures,datetime,xml.etree.ElementTree as ET,sys
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'research-boundaries/northstowe-parish-ons-dec2025-epsg27700.esrijson').read_text(encoding='utf-8-sig'))['features'][0]['geometry']['rings'][0]
box=[min(x[0] for x in p)-100,min(x[1] for x in p)-100,max(x[0] for x in p)+100,max(x[1] for x in p)+100]
def fetch(layer):
 params=dict(MapSource='CCC/AllMaps',service='WFS',version='1.1.0',request='GetFeature',typeName=layer,srsName='EPSG:27700',bbox=','.join(map(str,box))+',EPSG:27700',maxFeatures=10000)
 url='https://maps.cambridgeshire.gov.uk/getows.ashx?'+urllib.parse.urlencode(params)
 try:
  data=urllib.request.urlopen(url,timeout=50).read()
  document=ET.fromstring(data)
  if not document.tag.endswith('FeatureCollection'):raise ValueError('Not a WFS FeatureCollection; previous snapshot preserved')
  (ROOT/f'research/county-{layer}.gml').write_bytes(data)
  (ROOT/f'research/county-{layer}-url.txt').write_text(url)
  return dict(layer=layer,bytes=len(data),url=url,success=True)
 except Exception as e:return dict(layer=layer,error=str(e),success=False)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 results=list(pool.map(fetch,['AdoptedRoads','Section38Streets','StreetLights','row','Gullies','SouthCambsDCAssets']))
 for result in results:print(result['layer'],result.get('bytes') or result.get('error'))
 (ROOT/'research/county-fetch-status.json').write_text(json.dumps(dict(retrieved=datetime.datetime.now(datetime.timezone.utc).isoformat(),results=results),indent=2),encoding='utf8')
 if not all(r['success'] for r in results):sys.exit(1)
