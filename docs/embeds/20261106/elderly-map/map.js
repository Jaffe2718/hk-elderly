'use strict';
const $=id=>document.getElementById(id),nf=new Intl.NumberFormat('en-GB'),pct=v=>v==null?'Not assessed':Number(v).toFixed(2)+'%';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
Promise.all(['data.json','study-outline.geojson','theme.json'].map(path=>fetch(path+'?v=20261106-green').then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json()}))).then(([data,outline,theme])=>start({...data,outline,theme})).catch(e=>{$('loading').textContent='Unable to load map. Please refresh.';console.error(e)});
function start(D){
 $('loading').remove();let radius=800,areas;const map=L.map('map',{zoomControl:false,minZoom:8,maxZoom:18});L.control.zoom({position:'topright'}).addTo(map);L.control.scale({imperial:false}).addTo(map);
 const basemap=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,maxNativeZoom:16,className:'context-tiles',attribution:'Tiles &copy; Esri, HERE, Garmin',crossOrigin:true}).addTo(map);
 const bg=L.geoJSON(D.groups,{style:{stroke:false,fillColor:'#f7f9f8',fillOpacity:.1},interactive:false}).addTo(map);map.fitBounds(bg.getBounds());
 const outline=L.geoJSON(D.outline,{style:{color:D.theme.outline,weight:1.3},interactive:false}).addTo(map),groupLayers={};
 const site=(fc,type,color)=>L.geoJSON(fc,{pointToLayer:(f,ll)=>L.marker(ll,{icon:L.divIcon({className:'facility-marker',iconSize:[10,10],iconAnchor:[5,5],html:`<svg width="10" height="10" viewBox="0 0 10 10"><path d="${type==='NEC'?'M5 0 L10 5 L5 10 L0 5 Z':'M5 0 L10 10 L0 10 Z'}" fill="${color}" stroke="white" stroke-width=".8"/></svg>`})}),onEachFeature:(f,l)=>l.bindPopup(`<b>${esc(f.properties.name_en||type+' premises')}</b><p>${type} premises. Location does not indicate capacity.</p>`)});
 const layers={nec:site(D.centres.nec,'NEC',D.theme.facility).addTo(map),decc:site(D.centres.decc,'DECC',D.theme.decc)};
 const size=n=>n<=2500?4:n<=5000?6.7:n<=10000?10:n<=20000?14:18;
 layers.population=L.geoJSON(D.population,{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:size(f.properties.pop_65plus),fillColor:D.theme.interactive_population||D.theme.population,color:'white',weight:.7,fillOpacity:.65}),onEachFeature:(f,l)=>l.bindPopup(`${nf.format(f.properties.pop_65plus)} residents aged 65+. This symbol represents the entire statistical area, not people at this point.`)});
 const legend=L.control({position:'bottomright'});legend.onAdd=()=>{legend.el=L.DomUtil.create('div','map-key');L.DomEvent.disableClickPropagation(legend.el);return legend.el};legend.addTo(map);
 const home=L.control({position:'topright'});home.onAdd=()=>{const b=L.DomUtil.create('button');b.textContent='All Hong Kong';b.onclick=()=>map.fitBounds(bg.getBounds());L.DomEvent.disableClickPropagation(b);return b};home.addTo(map);
 const row=(a,b)=>`<div class="popup-row"><span>${a}</span><strong>${b}</strong></div>`;
 function decision(p){if(!p.assessed)return null;if($('view').value==='fixed')return p.fixed_priority;if($('combined').checked)return p.nec_decc_priority_800;return $('age').value==='65'?p['priority_'+radius]:p['priority_age'+$('age').value]}
 function popup(p){return `<b>${esc(p.place_en)}</b>${row('STPUG',esc(p.stpug_id))}${row('All residents (2021)',nf.format(p.pop_total))}${row('Residents aged 65+',nf.format(p.pop_65plus))}${row('Age 65+ share',pct(p.pct65))}${row('Residential cells',nf.format(p.res_cells))}${row('Residential land',Number(p.res_area_km2*100).toFixed(2)+' ha')}${row('Beyond NEC 800 m',pct(p.out800_pct))}${row('Selected scenarios',p.assessed?p.scenario_hits+' / 27':'Not assessed')}<p class="popup-note">2021 Census and residential land; 2026 premises. Straight-line distance, not walking time. Residential land coverage, not people served.</p>`}
 function update(){
  const view=$('view').value,fixed=view==='fixed';if(fixed){$('age').value='65';$('combined').checked=false}if($('combined').checked)$('age').value='65';
  const alternative=$('age').value!=='65'||$('combined').checked||fixed;if(alternative)radius=800;
  $('age').disabled=$('combined').checked||fixed;$('combined').disabled=fixed;
  document.querySelectorAll('[data-distance]').forEach(b=>{b.disabled=alternative&&b.dataset.distance!=='800';b.setAttribute('aria-pressed',Number(b.dataset.distance)===radius)});
  if(areas)map.removeLayer(areas);const pal=D.theme.sequential,percentLabels=['0%','>0–25%','>25–50%','>50–75%','>75–100%'],freqLabels=['0','1–3','4–9','10–18','19–27'];
  function fill(p){if(!p.assessed)return D.theme.not_assessed;if(view==='priority'||fixed)return decision(p)===1?D.theme.selected:D.theme.not_selected;if(view==='age'){const v=p['pct'+$('age').value];return D.theme.age_share[v<=15?0:v<=20?1:v<=25?2:3]}if(view==='sensitivity'){const v=p.scenario_hits;return pal[v===0?0:v<=3?1:v<=9?2:v<=18?3:4]}const v=$('combined').checked?p.any_out800_pct:p['out_share_'+radius]*100;return pal[v===0?0:v<=25?1:v<=50?2:v<=75?3:4]}
  areas=L.geoJSON(D.groups,{style:f=>({color:'#c3bacb',weight:.5,fillColor:fill(f.properties),fillOpacity:1}),onEachFeature:(f,l)=>{groupLayers[f.properties.stpug_id]=l;l.bindPopup(()=>popup(f.properties));l.on('mouseover',()=>l.setStyle({weight:2,color:'#00cbb0'}));l.on('mouseout',()=>areas.resetStyle(l))}}).addTo(map);
  if($('population').checked)layers.population.bringToFront();outline.bringToFront();const count=D.groups.features.filter(f=>decision(f.properties)===1).length;$('count').textContent=count;
  let title={priority:'P60 priority screen',fixed:'Fixed 20% / 30% screen',age:'Residents aged '+$('age').value+'+ (%)',coverage:'Residential land beyond '+radius.toLocaleString()+' m (%)',sensitivity:'Selections across 27 scenarios'}[view];
  const key=(c,t)=>`<div><i class="swatch" style="background:${c}"></i>${t}</div>`;
  legend.el.innerHTML='<b>'+title+'</b>'+((view==='priority'||fixed)?key(D.theme.selected,'Selected for review')+key(D.theme.not_selected,'Not selected'):(view==='age'?D.theme.age_share:pal).map((c,i)=>key(c,view==='age'?['0–15%','>15–20%','>20–25%','>25%'][i]:view==='sensitivity'?freqLabels[i]:percentLabels[i])).join(''))+key(D.theme.not_assessed,'Not assessed');
  if($('nec').checked)legend.el.innerHTML+='<div class="legend-facility"><i class="legend-nec"></i>NEC premises</div>';
  if($('decc').checked)legend.el.innerHTML+='<div class="legend-facility"><i class="legend-decc"></i>DECC premises</div>';
  if($('population').checked){legend.el.innerHTML+='<b>Residents aged 65+</b>';for(const [n,label]of [[2500,'0–2,500'],[5000,'2,501–5,000'],[10000,'5,001–10,000'],[20000,'10,001–20,000'],[20001,'>20,000']])legend.el.innerHTML+=`<div><i style="display:inline-block;width:${size(n)}px;height:${size(n)}px;background:${D.theme.interactive_population||D.theme.population};border-radius:50%;margin-right:10px"></i>${label}</div>`;}
  $('status').textContent=fixed?'Comparison only: age 65+ ≥20% AND residential gap ≥30%; 800 m.':'Main rule: age '+$('age').value+'+ ≥ cohort P60 AND gap ≥30.758%; unrounded cutoffs, ties included. Not service capacity.';
  window.__mapReview={map,basemap,data:D,setView:v=>{$('view').value=v;update()},selectedCount:count,groupLayers};
 }
 for(const id of ['nec','decc','population'])$(id).addEventListener('change',e=>{e.target.checked?layers[id].addTo(map):map.removeLayer(layers[id]);update()});
 for(const id of ['view','age','combined'])$(id).addEventListener('change',update);
 document.querySelectorAll('[data-distance]').forEach(b=>b.onclick=()=>{radius=Number(b.dataset.distance);update()});
 for(const id of D.cases){const b=document.createElement('button');b.innerHTML=`${id}<small>${esc(D.names[id])}</small>`;b.onclick=()=>{map.fitBounds(groupLayers[id].getBounds().pad(.2));groupLayers[id].openPopup()};$('cases').append(b)}
 update();new ResizeObserver(()=>map.invalidateSize()).observe($('map'));
}
