'use strict';
const steps=[
 ['census',30,30,'Census evidence','2021 · 211 STPUGs','INPUT','2021 Census A503 and STPUG boundaries provide population counts and age composition.','211 areas',['60+ is derived from 60–64 plus 65+.','75+ is derived from 65+ minus 65–69 and 70–74.','Keep group codes as strings and verify joined totals.']],
 ['sites',390,30,'Facility locations','NEC + DECC · November 2026','INPUT','The official SWD snapshot was retrieved on 2 November 2026. Coincident coordinates are deduplicated, while sub-bases are retained.','215 NEC / 62 DECC',['216 original NEC records become 215 unique locations.','Location counts are not independent service units.','Capacity and utilisation data are unavailable.']],
 ['land',750,30,'Residential land','2021 · 10 m grid','INPUT','Private residential, public residential and rural settlement classes define the land relevant to the proximity calculation.','792,049 cells',['Use the centres of 10 m cells.','109 source cells could not be assigned to a group.','Exclude mountains, airports and other non-residential land.']],
 ['prepare',30,205,'Join and validate','Identifiers · age counts · CRS','PROCESS','Join age counts by STPUG code, verify published totals and align the spatial evidence in Hong Kong 1980 Grid.','EPSG:2326',['Distances are measured in metres.','Retain original data and transformation records.','210 groups can be assessed; group 295 lacks residential support.']],
 ['distance',390,205,'Measure proximity','Nearest · second-nearest · choices','PROCESS','Measure planar distances from residential-cell centres to facility locations. Overlay dissolved buffers as an explanatory and consistency check.','500 / 800 / 1,000 m',['Nearest and second-nearest NEC distances.','Count distinct NEC sites within 800 m.','Summarise by STPUG, district and residential class.']],
 ['population',30,380,'Population condition','Relative scale of potential demand','CONDITION','Select the upper quartile of assessed groups using the count of residents aged 60+.','≥ 14,695',['P75 among 210 assessed groups.','Use counts rather than the elderly proportion.','Alternative age definitions use their own P75 thresholds.']],
 ['coverage',390,380,'Coverage condition','Residential land beyond reach','CONDITION','For each group, divide residential cells beyond 800 m from the nearest NEC by all assigned residential cells in that group.','> 50% beyond 800 m',['Equal cell areas allow a residential-area proportion.','This is not the proportion of residents without service.','800 m is a screening scenario, not a legal standard.']],
 ['binary',390,555,'Apply the Binary rule','Population AND coverage','MODEL','A group is selected only when both conditions hold. Other assessed groups receive 0; groups without residential data remain unassessed.','4 selected groups',['524 Eastern Yuen Long; 628 Southern Fanling.','833 Tiu Keng Leng; 950S Tung Chung / Chek Lap Kok.','Together they contain 78,526 residents aged 60+, not 78,526 unserved residents.']],
 ['checks',750,555,'Test the definitions','Thresholds · ages · facility scope','SENSITIVITY','Cross population P60/P75/P90, 500/800/1,000 m and uncovered shares of 25/50/75%, giving 27 threshold scenarios.','27 scenarios',['Repeat with age 65+ and 75+.','Compare NEC-only with NEC + DECC.','Compare residential support with centroid distance.','Frequency is not a probability or a weighted score.']],
 ['cases',30,730,'Read local cases','Matched spatial comparisons','INTERPRETATION','Use four cases to examine which assumptions alter the shortlist and which residential patches warrant further review.','4 local comparisons',['Keep map extents and legends aligned.','Use Swipe for NEC versus NEC + DECC.','Do not interpret non-residential area as demand.']],
 ['review',390,730,'Inform further review','Evidence, uncertainty and limits','OUTPUT','The result is a transparent shortlist for community-support review, not proof of unmet demand or a proposed new-centre site.','Review, not prescription',['Roads, slopes and accessible entrances are not modelled.','Residential area does not represent equal population density.','2021 population and land use are paired with 2026 premises.']]
].map(([id,x,y,title,subtitle,stage,description,metric,details])=>({id,x,y,title,subtitle,stage,description,metric,details}));
const links=[['census','prepare'],['sites','distance'],['land','distance'],['prepare','population'],['prepare','distance'],['distance','coverage'],['population','binary'],['coverage','binary'],['binary','checks'],['binary','cases'],['binary','review'],['checks','review']];
const $=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';let selected=-1,scale=1,tx=0,ty=0,timer=null;
function svg(tag,attrs,parent){const e=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
const palette={INPUT:'#245cb6',PROCESS:'#7050a4',CONDITION:'#9d570e',MODEL:'#007e68',SENSITIVITY:'#a14065',INTERPRETATION:'#334e61',OUTPUT:'#334e61'};
const legendCategories=[
 {label:'Data sources',stages:['INPUT']},
 {label:'Processing',stages:['PROCESS']},
 {label:'Screening conditions',stages:['CONDITION']},
 {label:'Binary model',stages:['MODEL']},
 {label:'Sensitivity',stages:['SENSITIVITY']},
 {label:'Interpretation & output',stages:['INTERPRETATION','OUTPUT']}
].map(c=>({...c,colour:palette[c.stages[0]],count:steps.filter(n=>c.stages.includes(n.stage)).length}));
const legend=document.createElement('section');legend.id='legend';legend.setAttribute('aria-label','Workflow colour legend');
const legendTitle=document.createElement('h2');legendTitle.textContent='Legend';legend.append(legendTitle);
const legendList=document.createElement('ul');legend.append(legendList);
for(const category of legendCategories){
 const item=document.createElement('li');item.style.setProperty('--legend-colour',category.colour);
 const swatch=document.createElement('span');swatch.className='legend-swatch';swatch.setAttribute('aria-hidden','true');
 const count=document.createElement('span');count.className='legend-count';count.textContent=category.count;count.setAttribute('aria-label',category.count+' steps');
 item.append(swatch,document.createTextNode(category.label),count);legendList.append(item);
}
$('canvas').closest('main').after(legend);
function sizeChrome(){const nav=document.querySelector('nav');if(!nav||!legend.isConnected)return;document.documentElement.style.setProperty('--chrome-height',(nav.offsetHeight+legend.offsetHeight)+'px')}
new ResizeObserver(sizeChrome).observe(legend);new ResizeObserver(sizeChrome).observe(document.querySelector('nav'));sizeChrome();
const icons={INPUT:'M2 4h18v14H2z M6 1v6 M16 1v6 M2 9h18',PROCESS:'M4 3h12v5H4z M4 14h12v5H4z M10 8v6',CONDITION:'M10 1l9 9-9 9-9-9z M10 6v5 M10 14v1',MODEL:'M3 3h14v14H3z M6 10l3 3 6-7',SENSITIVITY:'M2 5h16 M2 10h16 M2 15h16 M6 2v6 M14 7v6 M8 12v6',INTERPRETATION:'M8 2a6 6 0 1 0 0 12 6 6 0 0 0 0-12 M12 12l6 6',OUTPUT:'M3 17h14V7 M10 13V1 M6 5l4-4 4 4'};
const band=svg('g',{id:'architecture-layers'},$('viewport'));$('viewport').insertBefore(band,$('edges'));
for(const [i,label]of ['DATA SOURCES','PREPARATION & SPATIAL MEASURES','SCREENING CONDITIONS','BINARY MODEL & SENSITIVITY','INTERPRETATION & REVIEW'].entries()){svg('rect',{x:8,y:i*175,width:1054,height:155,rx:12,fill:'#fff',stroke:'#dce4e2','stroke-width':1},band);svg('text',{x:25,y:i*175+19,fill:'#435b51','font-size':10,'font-family':'Arial','font-weight':600,'letter-spacing':1.3},band).textContent=String(i+1).padStart(2,'0')+' / '+label}
for(const n of steps)n.y+=5;
for(const [from,to]of links){
 const a=steps.find(n=>n.id===from),b=steps.find(n=>n.id===to);
 const incoming=links.filter(([f,t])=>t===to&&steps.find(n=>n.id===f).y<b.y),outgoing=links.filter(([f,t])=>f===from&&steps.find(n=>n.id===t).y>a.y);
 const sourceIndex=outgoing.findIndex(([f,t])=>t===to),targetIndex=incoming.findIndex(([f])=>f===from);
 const x1=a.x+290*(sourceIndex+1)/(outgoing.length+1),y1=a.y+96,x2=b.x+290*(targetIndex+1)/(incoming.length+1),y2=b.y;
 let d=a.y===b.y?`M${a.x+290},${a.y+48} L${b.x},${b.y+48}`:`M${x1},${y1} C${x1},${(y1+y2)/2} ${x2},${(y1+y2)/2} ${x2},${y2}`;
 svg('path',{d,class:'edge','data-from':from,'data-to':to},$('edges'));
 const pulse=svg('path',{d,class:'edge-flow',pathLength:1,'data-from':from,'data-to':to,'aria-hidden':'true'},$('edges'));
 // A dash period equals exactly one route length. The end and start frames
 // are identical, so the next packet enters as the previous one leaves.
 // Fade by position at the ports, never by the age of the whole packet.
 const length=pulse.getTotalLength(),start=pulse.getPointAtLength(0),end=pulse.getPointAtLength(length);
 const gradientId='flow-'+from+'-'+to;
 const gradient=svg('linearGradient',{id:gradientId,gradientUnits:'userSpaceOnUse',x1:start.x,y1:start.y,x2:end.x,y2:end.y},$('diagram').querySelector('defs'));
 for(const [offset,opacity]of [[0,0],[.06,1],[.94,1],[1,0]])svg('stop',{offset,'stop-color':'#00e5a8','stop-opacity':opacity},gradient);
 pulse.style.stroke='url(#'+gradientId+')';
 const fraction=Math.min(48,Math.max(14,length*.2))/length;
 pulse.style.strokeDasharray=fraction+' '+(1-fraction);
 pulse.style.setProperty('--flow-duration',(length/105)+'s');
 pulse.style.setProperty('--flow-phase',(-links.findIndex(([f,t])=>f===from&&t===to)*.19)+'s');
}
for(const n of steps){const colour=palette[n.stage],g=svg('g',{transform:`translate(${n.x},${n.y})`,class:'node',id:'node-'+n.id,tabindex:0,role:'button','aria-label':n.title,style:'--category:'+colour},$('nodes'));svg('rect',{width:290,height:96},g);svg('path',{d:'M0 12V84',stroke:colour,'stroke-width':3,fill:'none'},g);const icon=svg('g',{transform:'translate(18 12) scale(.7)',fill:'none',stroke:colour,'stroke-width':1.7,'stroke-linecap':'round','stroke-linejoin':'round'},g);svg('path',{d:icons[n.stage]},icon);svg('text',{x:40,y:25,class:'subtitle stage-label',style:'fill:'+colour},g).textContent=n.stage;svg('text',{x:18,y:49,class:'title'},g).textContent=n.title;svg('text',{x:18,y:72,class:'subtitle'},g).textContent=n.subtitle;g.addEventListener('click',()=>select(steps.indexOf(n)));g.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();select(steps.indexOf(n))}})}
function select(i){if(!timer)document.body.classList.remove('flow-paused');selected=(i+steps.length)%steps.length;const n=steps[selected],connected=new Set([n.id]);for(const[a,b]of links)if(a===n.id||b===n.id){connected.add(a);connected.add(b)}document.querySelectorAll('.node').forEach(e=>{e.classList.toggle('selected',e.id==='node-'+n.id);e.classList.toggle('dim',!connected.has(e.id.slice(5)))});document.querySelectorAll('.edge,.edge-flow').forEach(e=>{const active=e.classList.contains('edge-flow')?e.dataset.from===n.id:e.dataset.from===n.id||e.dataset.to===n.id;e.classList.toggle('active',active);e.classList.toggle('dim',!active)});$('detail').innerHTML=`<span class="tag">${n.stage} / ${selected+1} OF ${steps.length}</span><h2>${n.title}</h2><p>${n.description}</p><div class="metric">${n.metric}</div><ul>${n.details.map(x=>'<li>'+x+'</li>').join('')}</ul>`;if($('canvas').clientWidth<760)focusStep(n);window.__workflow={steps,links,select,selected:n.id}}
function focusStep(n){const w=$('canvas').clientWidth;scale=Math.max(.95,Math.min(1.3,w/330));tx=(w-290*scale)/2-n.x*scale;ty=52-n.y*scale;transform()}
function fit(){const c=$('canvas');if(!c)return;const w=c.clientWidth,h=c.clientHeight;$('diagram').setAttribute('viewBox',`0 0 ${w} ${h}`);if(w<760&&selected>=0){focusStep(steps[selected]);return}scale=Math.min(w/1080,(h-16)/850);tx=(w-1080*scale)/2;ty=8;transform()}
function transform(){$('viewport').setAttribute('transform',`translate(${tx} ${ty}) scale(${scale})`)}
function zoom(delta){scale=Math.max(.55,Math.min(2.8,scale*delta));transform()}
$('plus').onclick=()=>zoom(1.15);$('minus').onclick=()=>zoom(1/1.15);$('reset').onclick=reset;$('next').onclick=()=>select(selected+1);$('previous').onclick=()=>select(selected<0?steps.length-1:selected-1);
function pause(){if(timer)clearInterval(timer);timer=null;document.body.classList.add('flow-paused');$('play').textContent='Resume';$('play').setAttribute('aria-pressed','false')}
function reset(){pause();selected=-1;$('search').value='';document.querySelectorAll('.selected,.active,.dim').forEach(e=>e.classList.remove('selected','active','dim'));$('detail').innerHTML='<h2>Analytical workflow</h2><p>Select a step to inspect its inputs and outputs, or play the walkthrough.</p>';$('play').textContent='Play walkthrough';window.__workflow={steps,links,select,reset,selected:null};fit()}
$('play').onclick=()=>{if(timer){pause();return}document.body.classList.remove('flow-paused');if(selected<0||selected===steps.length-1)select(0);timer=setInterval(()=>{if(selected===steps.length-1){pause();$('play').textContent='Play walkthrough'}else select(selected+1)},3500);$('play').textContent='Pause';$('play').setAttribute('aria-pressed','true')};
$('search').oninput=e=>{const q=e.target.value.trim().toLowerCase();if(!q){reset();return}const i=steps.findIndex(n=>(n.title+' '+n.description+' '+n.metric).toLowerCase().includes(q));if(i>=0)select(i)};
let drag=null;$('diagram').addEventListener('pointerdown',e=>{if(e.target.closest('.node'))return;drag={x:e.clientX,y:e.clientY,tx,ty};$('diagram').setPointerCapture(e.pointerId)});$('diagram').addEventListener('pointermove',e=>{if(!drag)return;const r=$('diagram').getBoundingClientRect();tx=drag.tx+(e.clientX-drag.x);ty=drag.ty+(e.clientY-drag.y);transform()});$('diagram').addEventListener('pointerup',()=>drag=null);$('diagram').addEventListener('pointercancel',()=>drag=null);$('diagram').addEventListener('wheel',e=>{e.preventDefault();zoom(e.deltaY<0?1.07:1/1.07)},{passive:false});
reset();

new ResizeObserver(fit).observe($('canvas'));fit();
