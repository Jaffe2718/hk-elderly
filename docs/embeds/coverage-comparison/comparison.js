'use strict';
fetch('data.json').then(r=>{if(!r.ok)throw Error('Comparison data unavailable');return r.json()}).then(start).catch(e=>document.getElementById('sync').textContent=e.message);
function start(data){
 const maps=['left','right'].map(id=>L.map(id,{zoomControl:false,attributionControl:true,zoomSnap:0,minZoom:8,maxZoom:18}));let syncing=false,selected=2,timer;
 maps.forEach((map,i)=>{L.control.zoom({position:i?'topright':'topleft'}).addTo(map);L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,maxNativeZoom:16,className:'context-tiles',attribution:'Tiles &copy; Esri, HERE, Garmin',crossOrigin:true}).addTo(map);map.attributionControl.addAttribution('Group 13 · supplied 2021 land / 2026 premises');L.geoJSON(data.land,{style:{stroke:false,fillColor:'#f7f9f8',fillOpacity:.18},interactive:false}).addTo(map);
  const palette=i?['#f5eee7','#ceb39c']:['#eee8f6','#b8a6d1'];
  L.geoJSON(data.panels[i].residential,{style:f=>({fillColor:palette[+f.properties[data.panels[i].field]===1?1:0],color:'#fff',weight:.5,fillOpacity:1}),onEachFeature:(f,l)=>l.bindPopup('STPUG '+f.properties.stpug_id+'<br>'+((+f.properties[data.panels[i].field]===1)?'Beyond':'Within')+' 800 m')}).addTo(map);
  L.geoJSON(data.outline,{style:{color:'#802835',weight:1.2},interactive:false}).addTo(map);
  for(const key of i?['nec_sites','decc_sites']:['nec_sites'])L.geoJSON(data[key],{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:key==='nec_sites'?3.5:4.5,fillColor:key==='nec_sites'?'#145341':'#fff',color:key==='nec_sites'?'#fff':'#145341',weight:key==='nec_sites'?.8:1.8,fillOpacity:1}),onEachFeature:(f,l)=>l.bindPopup(f.properties.name_en||key.replace('_sites','').toUpperCase()+' site')}).addTo(map);
  map.on('move',()=>{if(syncing)return;syncing=true;maps[1-i].setView(map.getCenter(),map.getZoom(),{animate:false});syncing=false});
 });
 const selector=document.getElementById('case');data.cases.forEach((c,i)=>{const option=document.createElement('option');option.value=i;option.textContent=c.name;selector.append(option)});
 function select(i){selected=(i+data.cases.length)%data.cases.length;selector.value=selected;const e=data.cases[selected].extent,bounds=[[e.ymin,e.xmin],[e.ymax,e.xmax]],zoom=Math.min(...maps.map(m=>m.getBoundsZoom(bounds,false,[24,24]))),center=L.latLngBounds(bounds).getCenter();syncing=true;for(const map of maps)map.setView(center,zoom,{animate:false});syncing=false}
 selector.onchange=()=>select(+selector.value);document.getElementById('previous').onclick=()=>select(selected-1);document.getElementById('next').onclick=()=>select(selected+1);document.getElementById('play').onclick=e=>{if(timer){clearInterval(timer);timer=null;e.target.textContent='Play case tour'}else{timer=setInterval(()=>select(selected+1),6500);e.target.textContent='Pause tour'}};
 new ResizeObserver(()=>{syncing=true;maps.forEach(m=>m.invalidateSize({pan:false}));syncing=false;select(selected)}).observe(document.querySelector('main'));select(2);window.__comparison={maps,data,select};
}
