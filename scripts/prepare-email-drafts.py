"""Generate a private review pack and unsent email files; never sends messages."""
from pathlib import Path
from email.message import EmailMessage
from email.policy import SMTP
from html import escape
import json,csv

root=Path(__file__).resolve().parents[1]
data=json.loads((root/'public/data/responsibilities.json').read_text(encoding='utf-8'))
out=root/'email-drafts';out.mkdir(exist_ok=True)
highways='https://www.cambridgeshire.gov.uk/residents/travel-roads-and-parking/roads-and-pathways/highway-records'
form_urls={'bloor':'https://bloorhomes.com/contact-us','taylor':'https://www.taylorwimpey.co.uk/support/contact-us','keepmoat':'https://www.keepmoat.com/contact-us/customer-care'}
requests={
'greenbelt': ('Phase 1 transfers, H4 trees and public bins', [
 'Please supply your current Northstowe maintenance boundaries and a dated schedule of completed transfers, including the house-parcel open spaces. Distinguish existing contracts from proposed or pending transfers.',
 'Please identify which H4 trees and planted areas you maintain and which remain with Vistry. Can you provide tree or asset IDs and the relevant plan?',
 'Please confirm the current Western Park litter/dog-bin emptying arrangements, exact bin locations, collection frequency and repair/replacement contact. Draft March 2022 steering-group notes mention your contractors; is that still correct?',
 'Please clarify the current responsibility for Hatton Road drainage ponds, connecting paths, greenways, play areas and furniture, including any exceptions or leased areas.'
 ],['greenbelt','bins-western'],'First wave'),
'aw': ('Bug Hunter Waters, paths, drainage and dog bins', [
 'Please provide the exact maintenance boundary around Bug Hunter Waters, separating the water/drainage infrastructure from banks, vegetation, paths and other surrounding land.',
 'For each part, please identify responsibility for path repairs, grounds maintenance, litter and fly-tipping clearance, furniture and lighting. Please clarify exceptions along the park-and-ride to Stirling Road path.',
 'The 25 March 2025 Open Space Steering Group minutes refer to dog-bin collections arranged by Anglian Water. Please confirm the current contractor, collection frequency, bin locations/IDs and who repairs or replaces those bins.',
 'Please confirm the most suitable resident reporting route for these estate issues and whether any land or assets have since transferred.'
 ],['bins-aw','report'],'First wave'),
'uc': ('Phase 1 roads, retained land, ponds and bin transfers', [
 'Please provide your current Phase 1 maintenance plan and asset register, including retained roads and paths, drainage, trees, lights, furniture and bins, with parcel/developer exceptions.',
 'Please confirm the exact extent of your responsibility along Stirling Road, Pathfinder Way and Links Lane, and any other main roads. Identify completed highway adoption by segment and date, and who handles defects while adoption is pending.',
 'Please confirm the present position for the Hatton Road drainage ponds and the path/lighting between the park-and-ride and Stirling Road.',
 'The December 2024 community forum described an intended transfer of new street-furniture/bin maintenance to Greenbelt. Please identify which transfers actually completed, their dates, the bin-emptying contractor and current service areas.'
 ],['contacts','forum'],'First wave'),
'he': ('Phase 2/3 roads, water park, public bins and Phase 3B', [
 'Please supply current maintenance boundaries for Phases 2 and 3, including Phase 3B land west of Phase 1, with retained, sold and transferred plots distinguished.',
 'Northstowe.com gives your Estates team as the contact for the new access road and Phase 2 water park. Please confirm the exact road segments, phase break on Stirling Road, associated paths/verges/drainage and any completed highway adoption dates.',
 'Please identify the current operators for grounds, paths, lakes/drainage, lights, play assets, litter clearance and public-bin emptying. A bin inventory with coordinates, labels/IDs, collection frequency and repair contact would be particularly useful.',
 'Please clarify the boundaries between your retained responsibilities and Inholm/RMG, Stirling Fields/Keepmoat or any appointed estate company. Who should receive resident reports where an asset is not yet handed over?'
 ],['contacts','faq'],'First wave'),
'ccc': ('Current adopted highway extents and adoption records', [
 'Please provide the latest available Northstowe highway-maintenance extents and adoption records, including roads, footways, cycle paths, verges, gullies and public rights of way, with asset IDs and effective dates where held.',
 'Our 12 September 2026 public county-map snapshot contains adopted records for Rampton Road, Station Road, Rampton Drift, Longstanton Bypass and two associated footpath records. Please confirm the exact adopted extents and identify later changes or additional publicly maintained streets.',
 'Eagle Way and Wellington Road appear in the prospective Section 38 layer. Please distinguish completed adoption from an agreement, construction stage or maintenance period, and confirm the current responsible party for each outstanding section.',
 'Please clarify the boundaries with Homes England and Urban & Civic on the main roads and access road. Centreline geometry alone does not establish the full highway width; is a reusable extent plan available?'
 ],['highways','county-wfs'],'First wave'),
'lights': ('County and developer streetlight responsibilities', [
 'Please supply the current list and locations of county-maintained streetlights within Northstowe parish, with column IDs, effective adoption dates and the resident fault-reporting contact.',
 'Our 12 September 2026 county-map snapshot identifies 50 county-owned lighting records. Please confirm any missing, changed or recently adopted assets.',
 'Please distinguish developer/estate lights from county lights, including lights on connecting paths. Where you hold information, please identify the current maintainer of the excluded assets and any pending handover.',
 'Please clarify any distinction between electricity supply, routine servicing and repair/replacement responsibility that residents need to understand.'
 ],['streetlights'],'First wave'),
'waste': ('Public-bin register, emptying service and street cleansing', [
 'Please provide the Northstowe public litter/dog-bin inventory for bins serviced by your team, including locations, bin IDs/stickers, emptying frequency, contractor and repair/replacement responsibility.',
 'Your street-care page explains how council-service stickers identify bins. Please confirm how residents should report an overflowing or damaged bin, and how you identify an unmarked bin whose operator is unclear.',
 'Please identify the exact streets/areas covered by your street-cleansing service and any special agreements on unadopted developer or estate land. Please distinguish bin emptying from litter clearance and household refuse collection.',
 'Please clarify the reporting and clearance arrangements for fly-tipping on council-serviced areas versus private/developer land, including how reports are passed to the responsible land manager.'
 ],['streetcare','streetcontact'],'First wave'),
'scdc': ('District assets, facility contracts and partner handovers', [
 'Please supply the district council public-realm/facility maintenance boundaries in Northstowe, with current operator contracts or scope plans that can be shared publicly.',
 'Please distinguish council and operator responsibilities at Western Park and other community assets, including the pavilion/pitches, bowling green, access paths, landscaping and external furniture.',
 'Please identify who empties and who repairs each public bin within your sites, and any street-cleansing or litter-clearance arrangements with other land managers.',
 'Can the community team help obtain current partner handover schedules and nominate an officer to resolve conflicting boundaries and keep the resident-facing register current?'
 ],['contacts','common'],'First wave'),
'ntc': ('Town assets and maintaining a shared responsibility register', [
 'Please confirm the Town Council assets and current maintenance boundaries, including the Unity Centre and any surrounding paths, planting, furniture or bins.',
 'Please identify responsibility for public-bin emptying, repair/replacement and litter clearance at those sites, and any services delivered on behalf of another organisation.',
 'Can you share the latest Open Space Steering Group responsibility plans, bin schedules and completed-handover records, particularly documents that supersede older published minutes?',
 'Please identify a suitable council role to approve map corrections and receive transfer updates. I would welcome agreement on a simple review process with a date, source and responsible organisation for each change.'
 ],['contacts'],'First wave'),
'vistry': ('Bovis/Linden parcels and the H4 street-tree exception', [
 'Please supply the current public-realm maintenance scope for your Northstowe Bovis/Linden parcels, including retained roads/paths, street trees, planted areas, drainage, lights, furniture and bins.',
 'The September 2025 community-forum material distinguishes H4 open-space management from street trees retained by the developer. Please identify those trees and the exact split using asset IDs or a marked plan.',
 'Please give dated records of completed transfers to Greenbelt, the county council or another manager, and separately identify outstanding or proposed transfers.',
 'Please confirm the resident reporting contact and public-bin emptying/repair arrangements for each retained area, or identify the appointed estate manager.'
 ],['greenbelt','report'],'Parcel follow-up'),
'barratt': ('Barratt/David Wilson retained parcel assets and transfers', [
 'Please supply the current maintenance boundaries and asset schedule for your Northstowe parcels, separating developer-retained assets from transferred Greenbelt open space.',
 'Please cover roads, footways, street trees, drainage, lighting, play/furniture and bins, including small strips or individual assets that differ from the surrounding land.',
 'Please identify completed transfers and dates, pending highway adoption and the current defect-reporting contact during each maintenance period.',
 'Who currently empties, repairs and replaces public litter/dog bins within your retained scope, and what is the exact collection area/frequency?'
 ],['report','greenbelt'],'Parcel follow-up'),
'bloor': ('H1 retained assets and Greenbelt handover boundaries', [
 'Please provide the current Bloor maintenance scope for Northstowe parcel H1 and identify any other Northstowe areas that remain your responsibility.',
 'Please distinguish transferred Greenbelt open space from retained roads, paths, trees, drainage, lighting, bins and other furniture. A dated plan and completed transfer schedule would help resolve boundary cases.',
 'Please confirm current bin-emptying and bin repair/replacement arrangements in your retained areas and the resident reporting route.',
 'If an estate management company now holds these responsibilities, please provide its public contact and the date/scope of the appointment.'
 ],['greenbelt'],'Parcel follow-up'),
'taylor': ('Northstowe parcel maintenance and estate management', [
 'Please identify your current maintenance boundaries in Northstowe, including the areas labelled H3, H10, H11 and H13 in the public-source plans, and correct any parcel references that are out of date.',
 'Please distinguish retained roads/paths, street trees, drainage, lights, play assets, furniture and bins from completed transfers to a council, Greenbelt or another manager.',
 'Please provide completed handover dates and identify the current maintainer during pending adoption or contractual maintenance periods.',
 'Please confirm public-bin emptying, repair/replacement and litter-clearance contacts and the correct resident reporting route for each retained or managed area.'
 ],['greenbelt'],'Parcel follow-up'),
'keepmoat': ('Stirling Fields communal assets and estate manager', [
 'Please provide the current Stirling Fields maintenance plan, separating Keepmoat-retained public/communal assets from Homes England land, adopted highway and assets managed by an estate company.',
 'Please identify the appointed management company, its resident contact and the actual appointment/handover dates and scope.',
 'Please cover roads/paths, planting/trees, drainage, lighting, play/furniture and bins. Who empties each public litter/dog bin and who repairs or replaces it?',
 'Please provide any completed or pending transfer schedule and confirm who receives reports while an asset remains in the developer maintenance period.'
 ],['faq'],'Parcel follow-up'),
'rmg': ('Inholm management boundary and retained developer assets', [
 'The Town Council legacy reporting guide names RMG for Inholm. Please confirm your current appointment and provide the exact estate maintenance boundary and asset schedule.',
 'Please distinguish management-company responsibilities from Homes England, developer-retained and adopted county assets, including roads/paths, drainage, trees, lighting and street furniture.',
 'Please identify who empties public/communal litter or dog bins, their locations and frequency, and who repairs/replaces them. Please distinguish these from residential communal refuse stores.',
 'Please confirm the current resident reporting route and dated changes or transfers that supersede the older guide. If another company now manages the estate, please direct me to its public contact.'
 ],['rmg','report'],'Parcel follow-up'),
'elite': ('Western Park pavilion/pitches and public-bin service', [
 'Please provide the current boundary of your Western Park operational and maintenance responsibilities, including the pavilion, sports pitches and associated access areas.',
 'Please distinguish your scope from district council, Greenbelt and bowling-club responsibilities for grounds, paths, fences, lighting and furniture.',
 'Please identify the litter/dog bins you empty, collection frequency, and who repairs/replaces the bins. Are any bins within or beside the sports facilities covered by a different contractor?',
 'Please confirm the best resident contact for defects or overflowing bins and the effective date of the current arrangement.'
 ],['common'],'Facility follow-up'),
'bowls': ('Bowling green boundary and associated maintenance', [
 'Please confirm the current boundary of the bowling club maintenance area at Western Park and identify the appropriate committee/grounds contact for this enquiry.',
 'Please distinguish responsibility for the green, surrounds, fencing, access paths, lighting, furniture and any bins from the district council, Elite Sports or Greenbelt.',
 'If bins are present, who empties them, how often, and who repairs/replaces them? Please provide locations or a marked plan.',
 'Please confirm a public role-based reporting contact that the map may publish, and identify any recent change to the arrangement.'
 ],['common'],'Facility follow-up'),
'nha': ('Allotments, orchard and boundary maintenance', [
 'Please provide the current allotment and community-orchard maintenance boundary, with any different responsibilities for the access path, perimeter, drainage, fences and nearby planting.',
 'Please identify which assets the Association maintains and which remain with a council, Greenbelt or developer, including any completed or pending transfers.',
 'If litter/dog or communal bins are provided, please identify who empties and repairs them, their location and collection arrangement.',
 'Please confirm the public contact to show on the map for maintenance enquiries and the date of the current arrangement.'
 ],['directory'],'Facility follow-up'),
'pe': ('College community sports facilities and external assets', [
 'Please provide the boundary of your community sports-facility maintenance responsibilities at Northstowe Secondary College.',
 'Please distinguish your scope from school, developer and county responsibilities for external access paths, courts/pitches, lighting, fencing, planting and furniture.',
 'Please identify who empties and who repairs/replaces litter bins within that scope, and whether external bins or litter clearance fall under another contract.',
 'Please confirm the public reporting contact and effective date of the current arrangement, or identify the facilities/estate team that holds the records.'
 ],['pe'],'Facility follow-up')
}

records=[]
for i,(key,(topic,asks,source_ids,priority)) in enumerate(requests.items(),1):
 o=data['organisations'][key]
 recipient=o.get('email')
 contact_url=data['sources'][o['source']]['url']
 contact_note='Published contact; checked against public sources on 12 September 2026. Delivery and responsibility have not been confirmed by the recipient.'
 if key=='ccc':
  recipient='searches@cambridgeshire.gov.uk';contact_url=highways
  contact_note='Published Highway Records team email. The current page directs general records enquiries to its online enquiry form; use that form if the team redirects this email. No paid search is being ordered.'
 if key in form_urls:
  recipient=None;contact_url=form_urls[key]
  contact_note='No suitable direct email verified. Use the official contact/customer-care page to request the right Northstowe team, then paste this draft. Do not guess a regional email address.'
 if key in ['aw','vistry','barratt']:
  contact_note='Email published in the legacy Town Council reporting guide, checked 12 September 2026. Current delivery has not been verified; please review this older contact before sending.'
 if key=='bowls':contact_note='Role email published in the Northstowe Hub club listing. Ask the membership team to forward to the committee/grounds contact.'
 if key=='waste':contact_url=data['sources']['streetcontact']['url']
 if key=='ntc':contact_url=data['sources']['towncontact']['url']
 sources=[]
 for sid in source_ids:
  if sid in data['sources']:
   s=data['sources'][sid];sources.append((s['title'],s['url']))
 greeting=f"Dear {o.get('shortName') or o['name']} team,"
 body=greeting+'\n\nI am a councillor helping develop an interactive public-realm responsibility map for residents of Northstowe parish. Residents often struggle to identify the correct organisation for repairs, litter or overflowing bins. I would be grateful for your help checking the part of the map relating to your organisation.\n\n'
 body+='Could you please help with the following?\n\n'+'\n\n'.join(f'{n}. {ask}' for n,ask in enumerate(asks,1))
 body+='\n\nExisting GIS files (GeoJSON or shapefile), an asset spreadsheet with coordinates, or a clearly marked PDF would all help. Please distinguish land ownership from the organisation carrying out each maintenance service, and give the date the information applies from. If a record is unavailable, a partial response and the correct information holder would still be useful.\n\nPlease confirm which boundaries, service details and role-based contact information we may reproduce in the public map, with the attribution and any conditions required. We do not need residents’ personal information. Please let me know before undertaking any chargeable work.\n\nIf another colleague holds these records, would you please forward this enquiry or provide their public contact? Thank you for helping us give residents a clearer reporting route.\n\nKind regards,\n[Councillor name]\n[Council / ward]\n[Reply email and optional telephone]'
 subject='Northstowe responsibility map: '+topic
 stem=f'{i:02d}-{key}'
 (out/(stem+'.txt')).write_text('DRAFT — NOT SENT\nTo: '+(recipient or 'CONTACT ROUTE TO CONFIRM')+'\nSubject: '+subject+'\n\n'+body,encoding='utf-8')
 msg=EmailMessage(policy=SMTP)
 if recipient:msg['To']=recipient
 msg['Subject']=subject;msg['X-Unsent']='1';msg.set_content(body)
 (out/(stem+'.eml')).write_bytes(msg.as_bytes())
 records.append(dict(number=i,key=key,name=o['name'],recipient=recipient,contact_url=contact_url,contact_note=contact_note,phone=o.get('phone'),priority=priority,subject=subject,body=body,sources=sources,stem=stem))

(out/'drafts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
with (out/'contact-and-request-register.csv').open('w',newline='',encoding='utf-8-sig') as fp:
 writer=csv.writer(fp);writer.writerow(['Organisation','Priority','Email','Contact URL','Phone','Verification note','Request topic','Status'])
 for r in records:writer.writerow([r['name'],r['priority'],r['recipient'] or 'Not verified',r['contact_url'],r['phone'] or '',r['contact_note'],r['subject'],'Draft only — not sent'])
intro='19 tailored drafts for councillor review · 12 September 2026 · Nothing sent'
md=['# Northstowe information-request emails',intro,'','Replace the signature placeholders and review each recipient. Three drafts need the correct email obtained through the official contact page. Older contact details are explicitly marked. No fee, attachment, sending or account access is authorised by these drafts.','','Suggested first wave: land managers, both county teams, waste service and the two councils. Parcel and facility requests can then clarify the remaining boundaries.','']
nav=[];cards=[]
for r in records:
 nav.append(f'<a href="#{r["key"]}">{r["number"]:02d} {escape(r["name"])}</a>')
 links=' · '.join(f'<a href="{escape(url,quote=True)}" target="_blank" rel="noreferrer">{escape(title)}</a>' for title,url in r['sources'])
 cards.append(f'''<details id="{r['key']}"><summary><span class="number">{r['number']:02d}</span><span>{escape(r['name'])}<small>{escape(r['priority'])}</small></span></summary><div class="draft"><h2>{escape(r['subject'])}</h2><div class="contact"><b>To: {escape(r['recipient'] or 'Email to be confirmed via official contact page')}</b><p>{escape(r['contact_note'])}</p><a href="{escape(r['contact_url'],quote=True)}" target="_blank" rel="noreferrer">Verify contact / open contact page</a>{(' · '+escape(r['phone'])) if r['phone'] else ''}</div><p class="actions"><button type="button" data-copy="body-{r['key']}">Copy draft</button><a href="{r['stem']}.eml" download>Download unsent email</a><a href="{r['stem']}.txt" download>Plain text</a></p><textarea aria-label="Draft email to {escape(r['name'],quote=True)}" id="body-{r['key']}" spellcheck="true">{escape('Subject: '+r['subject']+'\n\n'+r['body'])}</textarea><p class="sources"><b>Research for this request:</b> {links}</p></div></details>''')
 md += [f"## {r['number']:02d}. {r['name']}",f"To: {r['recipient'] or 'Email not verified; use official contact page'}",r['contact_note'],f"[Contact source]({r['contact_url']})",f"Subject: {r['subject']}",'',r['body'],'','Research sources: '+', '.join(f'[{t}]({u})' for t,u in r['sources']),'']
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Northstowe — email drafts for review</title><style>
*{box-sizing:border-box}body{margin:0;background:#f2f5f3;color:#173a3c;font:16px/1.55 system-ui,sans-serif}header{background:#123f43;color:white;padding:42px max(24px,calc((100vw - 1180px)/2))}header p{max-width:800px;color:#cde2df}h1{font-size:clamp(28px,4vw,42px);line-height:1.15;margin:10px 0}header .tag{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#bee9d0}main{max-width:1228px;padding:30px 24px;margin:auto;display:grid;grid-template-columns:255px 1fr;gap:30px}nav{align-self:start;position:sticky;top:18px;font-size:13px;max-height:90vh;overflow:auto}nav a{display:block;padding:7px;color:#245f61;text-decoration:none;border-bottom:1px solid #d9e3df}a{color:#086b73}details{background:white;border:1px solid #d3e0da;border-radius:12px;margin-bottom:12px;scroll-margin-top:20px}summary{cursor:pointer;padding:20px;display:flex;align-items:center;gap:15px;font-weight:650}summary:after{content:'+';margin-left:auto;font-size:24px}details[open] summary:after{content:'−'}summary small{display:block;color:#5f7473;font-size:12px;font-weight:400}.number{color:#7d9992;font-size:13px}.draft{padding:0 24px 24px}h2{font-size:19px}.contact{background:#edf5f1;border-left:3px solid #3d9271;padding:15px;font-size:14px;overflow-wrap:anywhere}.contact p{margin:8px 0}.actions{display:flex;align-items:center;flex-wrap:wrap;gap:16px;font-size:13px}button{background:#176b65;border:0;border-radius:6px;padding:10px 15px;color:white;cursor:pointer}textarea{display:block;resize:vertical;width:100%;height:700px;font:15px/1.65 system-ui,sans-serif;border:1px solid #becfc8;border-radius:7px;padding:18px;color:#183c3b;background:#fff}.sources{font-size:12px;color:#536e67}.note{background:#e3ece7;padding:16px;border-radius:9px;margin:0 0 22px;font-size:14px}footer{font-size:13px;padding:25px;text-align:center}#feedback{position:fixed;bottom:20px;right:20px;background:#123f43;color:white;padding:12px;border-radius:8px;display:none}@media(max-width:760px){main{display:block;padding:20px 14px}nav{position:static;max-height:180px;margin-bottom:22px}summary{padding:15px}.draft{padding:0 15px 20px}textarea{height:780px}}@media print{nav,.actions,footer,textarea{display:none}main{display:block}details{break-inside:avoid}details>summary{list-style:none}.print-body{white-space:pre-wrap;font-size:11px}}@media screen{.print-body{display:none}}
</style><header><div class="tag">Private review pack · Drafts only</div><h1>A clearer answer for every place.</h1><p>CONTACT requests for the Northstowe responsibility map. Review the recipients and wording, replace the signature placeholders, then choose what to send yourself. Nothing has been sent.</p></header><main><nav>NAV</nav><section><p class="note">INTRO<br><b>16 published email contacts; 3 contact-page routes.</b> Older addresses are flagged. Start with land managers and councils, then resolve parcel and facility exceptions.<br>Edits in these text boxes last only until this page is closed or reloaded; copy them to your email application to keep them. Download links contain the original draft. These files are excluded from the public map.</p>CARDS</section></main><footer><a href="draft-emails.md">All drafts as Markdown</a> · <a href="contact-and-request-register.csv">Contact and request register (CSV)</a></footer><div id="feedback" role="status"></div><script>
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{const t=document.getElementById(b.dataset.copy);t.focus();t.select();try{await navigator.clipboard.writeText(t.value)}catch{document.execCommand('copy')}const f=document.getElementById('feedback');f.textContent='Draft copied for review';f.style.display='block';setTimeout(()=>f.style.display='none',2200)}));
function reveal(){const d=document.getElementById(location.hash.slice(1));if(d?.tagName==='DETAILS')d.open=true}window.addEventListener('hashchange',reveal);reveal();
window.addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>{d.open=true;let p=d.querySelector('.print-body');if(!p){p=document.createElement('p');p.className='print-body';d.querySelector('.draft').appendChild(p)}p.textContent=d.querySelector('textarea').value}));
</script></html>'''.replace('NAV',''.join(nav)).replace('INTRO',intro).replace('CARDS',''.join(cards)).replace('CONTACT requests','Information requests')
(out/'index.html').write_text(html,encoding='utf-8');(out/'draft-emails.md').write_text('\n'.join(md),encoding='utf-8')
assert len(records)==19 and sum(bool(r['recipient']) for r in records)==16
print(f'Prepared {len(records)} unsent drafts, 16 email recipients and 3 contact-page routes: {out}')
