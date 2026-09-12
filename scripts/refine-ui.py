from pathlib import Path
p=Path('app/responsibility-map.tsx');s=p.read_text(encoding='utf-8')
def replace(a,b):
 global s
 assert a in s,a[:80]
 s=s.replace(a,b)
replace('11 September 2026','12 September 2026')
replace("const focus=(f:F)=>{const L=", "const focus=(f:F)=>{if(f.properties.detail)setDetails(true);const L=")
replace('Include broad enquiry areas</label>','Include broad enquiry areas</label><label className="context-toggle"><Checkbox checked={showDetails} onCheckedChange={v=>setDetails(!!v)} disabled={issues.length===1&&[\'lighting\',\'water\'].includes(issues[0])}/>Show individual lights and drains</label>')
replace("{point&&shown.map", "{point&&shown.length>0&&shown.every((f:F)=>f.properties.context)&&<div className=\"notice\"><strong>No asset-level maintainer confirmed</strong><p>Only broad enquiry routes match this location and these filters. Confirm the particular asset before reporting a repair.</p></div>}{point&&<p className=\"geometry-note\">Lines match within about 14 m. Nearby point matches are approximate; check the asset number on site.</p>}{point&&shown.map")
replace("{f.properties.status==='published'?'Published responsibility':f.properties.context?'Enquiry route only':'Confirmation needed'}", "{f.properties.recordLabel||(f.properties.context?'Enquiry route only':f.properties.status==='published'?'Responsibility identified in source':'Confirmation needed')}")
replace('A guide awaiting verification</strong>', 'Evidence coverage</strong>')
replace('Broad development areas provide enquiry routes only.</p>', 'Broad development areas provide enquiry routes only. The county snapshot adds 50 owned lights, 176 gully records, 6 adopted highway records, 2 prospective-adoption records and 11 rights-of-way records.</p>')
replace('Geographic features © OpenStreetMap contributors, ODbL.', 'County assets: © Crown copyright and database rights 2026 OS AC0000822131. Geographic features © OpenStreetMap contributors, ODbL.')
replace("function segment(p:number[]", "function REMOVEDsegment(p:number[]")
s=s[:s.index('function REMOVEDsegment')]
# Feature-detect the optional read-only browser tool. Ordinary browsers need no support.
replace(" const focus=(f:F)", """ useEffect(()=>{
  const context=(document as Document & {modelContext?:{registerTool:(tool:unknown,options:{signal:AbortSignal})=>unknown}}).modelContext;
  if(!data||!context?.registerTool)return;
  const lifecycle=new AbortController();
  try{void Promise.resolve(context.registerTool({
   name:'find_responsible_contacts',title:'Find Northstowe maintenance contacts',
   description:'Read all matching contacts and evidence for a Northstowe location and problem. Does not submit a report or certify ownership.',
   inputSchema:{type:'object',properties:{latitude:{type:'number'},longitude:{type:'number'},category:{type:'string',enum:all}},required:['latitude','longitude','category'],additionalProperties:false},
   annotations:{readOnlyHint:true,untrustedContentHint:true},
   execute(input:unknown){
    const x=input as {latitude?:number;longitude?:number;category?:string};
    if(!x||typeof x.latitude!=='number'||typeof x.longitude!=='number'||!Number.isFinite(x.latitude)||!Number.isFinite(x.longitude)||x.latitude< -90||x.latitude>90||x.longitude< -180||x.longitude>180||!all.includes(x.category||''))throw Error('Provide valid latitude, longitude and a supported problem category.');
    const location=[x.longitude,x.latitude];
    return {checked:data.checked,insideParish:data.boundary.features.some((f:F)=>booleanPointInPolygon(location,f)),notice:'Approximate geographic matches; read scope and boundary caveats. No report has been submitted.',matches:data.features.filter((f:F)=>contains(f,location)).flatMap((f:F)=>f.properties.responsibilities.filter((r:any)=>r.categories.includes(x.category)).map((r:any)=>({place:f.properties.name,status:f.properties.status,geometryNote:f.properties.geometryNote,organisation:data.organisations[r.org],scope:r.note,caveat:r.caveat,sources:r.sources.map((id:string)=>data.sources[id])})))};
   }
  },{signal:lifecycle.signal})).catch(()=>{});}catch{/* Optional API; map remains fully usable. */}
  return()=>lifecycle.abort();
 },[data]);
 const focus=(f:F)""")
p.write_text(s,encoding='utf-8')
