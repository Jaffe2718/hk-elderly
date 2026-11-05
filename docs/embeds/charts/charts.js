'use strict';
const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg',COLORS=['#b9afd0','#adc9d6'];
let data,view='housing',table=false,page=0;
// Each embed owns one task. Hash changes may switch tabs within that task only.
const initialHash=location.hash.slice(1),requestedGroup=new URLSearchParams(location.search).get('group');
const group=requestedGroup==='sensitivity'||(!requestedGroup&&['sensitivity','distance','age'].includes(initialHash))?'sensitivity':'coverage';
const allowedViews=group==='coverage'?['housing','districts']:['sensitivity','distance','age'];
document.querySelectorAll('[data-view]').forEach(button=>{button.hidden=!allowedViews.includes(button.dataset.view)});
const titles={housing:'Coverage by residential type',districts:'Coverage by district',distance:'Distance sensitivity',age:'Age-definition sensitivity',sensitivity:'Sensitivity to distance and age'};
function el(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e}
function label(parent,x,y,s,attrs={}){const e=el('text',{x,y,...attrs},parent);e.textContent=s;return e}
function inspect(e,text,colour='#00ccb3'){
 e.setAttribute('tabindex',0);e.setAttribute('aria-label',text);e.style.setProperty('--highlight',colour);
 const show=()=>{$('detail').textContent=text};e.addEventListener('pointerenter',show);e.addEventListener('focus',show);
 e.addEventListener('click',()=>{document.querySelectorAll('.picked').forEach(n=>n.classList.remove('picked'));e.classList.add('picked');show()});
 e.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();e.dispatchEvent(new Event('click'))}});
}
function matrix(kind,parent){
 const ds=data[kind],panel=document.createElement('section');panel.className='matrix-panel '+kind;parent.append(panel);
 const title=document.createElement('h2');title.textContent=kind==='distance'?'A · Distance threshold':'B · Age definition';panel.append(title);
 const headers=kind==='distance'?['500 m','800 m','1,000 m']:['60+','65+','75+'];
 const grid=document.createElement('div');grid.className='matrix';grid.style.gridTemplateRows=`24px repeat(${ds.rows.length}, minmax(14px,1fr))`;panel.append(grid);
 for(const text of ['STPUG',...headers]){const h=document.createElement('span');h.className='matrix-label';h.textContent=text;grid.append(h)}
 for(const row of ds.rows){const name=document.createElement('span');name.className='matrix-label';name.textContent=row[0];grid.append(name);for(let i=1;i<=3;i++){const yes=+row[i]===1,cell=document.createElement('button');cell.type='button';cell.className='cell '+(yes?'yes':'no');cell.textContent=row[i];inspect(cell,`Group ${row[0]} · ${headers[i-1]}: ${yes?'Selected (1)':'Not selected (0)'}`);grid.append(cell)}}
 const note=document.createElement('p');note.className='panel-note';note.textContent=kind==='distance'?'11 / 4 / 2 groups selected; other cutoffs fixed.':'Main 60+ shortlist; each cohort uses its own P75.';panel.append(note);
}
function bars(rows,parent){
 const subset=view==='districts'?rows.slice(page*6,page*6+6):rows;
 const width=Math.max(320,parent.clientWidth-16),left=width<600?128:210,right=width<600?58:95,top=24,rowHeight=53,height=top+subset.length*rowHeight+35;
 const svg=el('svg',{viewBox:`0 0 ${width} ${height}`,preserveAspectRatio:'xMidYMid meet',role:'img','aria-label':titles[view]},parent);el('title',{},svg).textContent=titles[view];
 const span=width-left-right;
 for(const tick of [0,25,50,75,100]){const x=left+span*tick/100;el('line',{x1:x,x2:x,y1:top-12,y2:height-30,stroke:'#dce7eb'},svg);label(svg,x,height-7,tick+'%',{'text-anchor':'middle'})}
 const scope=$('scope').value,series=[1,2].filter(i=>scope==='both'||i===(scope==='nec'?1:2));
 subset.forEach((r,j)=>{const y=top+j*rowHeight;label(svg,left-14,y+22,r[0],{'text-anchor':'end'});series.forEach((i,k)=>{const val=+r[i],cy=y+k*21,e=el('rect',{x:left,y:cy,width:span*val/100,height:15,rx:3,fill:COLORS[i-1],class:'bar',role:'button'},svg);inspect(e,`${r[0]} · ${i===1?'NEC only':'NEC + DECC'}: ${val.toFixed(3)}% of residential area within 800 m`,i===1?'#00ccb3':'#5aaeff');label(svg,left+span*val/100+9,cy+13,val.toFixed(1)+'%')})});
 svg.querySelectorAll('text').forEach(e=>e.style.pointerEvents='none');
}
function draw(){
 const isMatrix=['distance','age','sensitivity'].includes(view),ds=data[view==='sensitivity'?'distance':view],scope=$('scope').value;let rows=ds.rows.map(r=>r.slice());
 if(!isMatrix&&$('sort').value!=='source'){const index=scope==='combined'?2:1;rows.sort((a,b)=>(+a[index]-+b[index])*($('sort').value==='descending'?-1:1))}
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.view===view));$('scope-label').hidden=isMatrix;$('sort-label').hidden=isMatrix;
 $('heading').textContent=titles[view];$('description').textContent=isMatrix?'Binary selection: 1 = selected; 0 = not selected.':'Residential ground area within 800 m. Select a bar for its exact value.';
 $('note').textContent=isMatrix?'Screening scenarios are not probabilities or official service standards.':'Area coverage is not the percentage of older residents served. NEC and DECC differ in function and capacity.';
 $('legend').replaceChildren();$('chart').replaceChildren();$('table').replaceChildren();$('detail').textContent='Select a '+(isMatrix?'cell':'bar')+' to inspect its value.';
 if(isMatrix){$('legend').innerHTML='<span><i class="key yes-key"></i>Selected (1)</span><span><i class="key no-key"></i>Not selected (0)</span>'}
 else for(const i of [1,2].filter(i=>scope==='both'||i===(scope==='nec'?1:2))){const key=document.createElement('span'),swatch=document.createElement('i');swatch.className='key';swatch.style.background=COLORS[i-1];key.append(swatch,document.createTextNode(i===1?'NEC only':'NEC + DECC'));$('legend').append(key)}
 $('chart').className=isMatrix?'matrices'+(view==='sensitivity'?' paired':''):'bars';
 if(isMatrix)for(const kind of view==='sensitivity'?['distance','age']:[view])matrix(kind,$('chart'));else bars(rows,$('chart'));
 const sets=view==='sensitivity'?['distance','age']:[view];
 for(const kind of sets){const source=data[kind],t=document.createElement('table'),head=t.createTHead().insertRow();source.columns.forEach(c=>{const th=document.createElement('th');th.textContent=c;head.append(th)});const body=t.createTBody();(kind===view?rows:source.rows).forEach(r=>{const tr=body.insertRow();r.forEach(v=>tr.insertCell().textContent=v)});$('table').append(t)}
 $('chart').hidden=table;$('table').hidden=!table;$('table-toggle').setAttribute('aria-pressed',table);
 $('pager').hidden=view!=='districts'||table;$('page-label').textContent=`${page*6+1}–${Math.min(page*6+6,rows.length)} of ${rows.length}`;$('page-back').disabled=page===0;$('page-next').disabled=page*6+6>=rows.length;
 window.__charts={view,rows,draw};
}
function route(){const hash=location.hash.slice(1);view=allowedViews.includes(hash)?hash:allowedViews[0];page=0;draw()}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{location.hash=b.dataset.view});$('scope').onchange=draw;$('sort').onchange=()=>{page=0;draw()};$('table-toggle').onclick=()=>{table=!table;draw()};
$('page-back').onclick=()=>{page--;draw()};$('page-next').onclick=()=>{page++;draw()};
fetch('data.json').then(r=>{if(!r.ok)throw Error('Chart data unavailable');return r.json()}).then(d=>{data=d;route();window.addEventListener('hashchange',route)}).catch(e=>{$('detail').textContent=e.message});
