"use strict";
require(['esri/Map','esri/views/MapView','esri/layers/GeoJSONLayer','esri/layers/VectorTileLayer','esri/Basemap','esri/widgets/Swipe','esri/widgets/Home','esri/widgets/Fullscreen','esri/geometry/Extent'],(Map,MapView,GeoJSONLayer,VectorTileLayer,Basemap,Swipe,Home,Fullscreen,Extent)=>{
 async function start(){
  const response=await fetch('data-v2.json');if(!response.ok)throw Error('Comparison data unavailable');const data=await response.json();
  const urls=[];function geo(fc,title,renderer){const url=URL.createObjectURL(new Blob([JSON.stringify(fc)],{type:'application/geo+json'}));urls.push(url);return new GeoJSONLayer({url,title,renderer,outFields:['*'],copyright:'GEOG7302 Group 13 · 2021 housing / 2026 premises',popupTemplate:{title,content:[{type:'fields',fieldInfos:[{fieldName:'patch_ha',label:'Residential ground area (ha)'},{fieldName:'A_status',label:'After model A'},{fieldName:'venue_status',label:'After community venue'},{fieldName:'name_en',label:'Location'},{fieldName:'address_en',label:'Address'},{fieldName:'added_800_ha',label:'Newly covered residential land (ha)'}].filter(f=>Object.hasOwn(fc.features[0]?.properties||{},f.fieldName))}]}});}
  const fill=c=>({type:'simple-fill',color:c,outline:{color:'#fff',width:.4}});
  const land=geo(data.land,'Study area',{type:'simple',symbol:fill('#f7f9f8')});
  const point=(fc,title,style,color,size)=>geo(fc,title,{type:'simple',symbol:{type:'simple-marker',style,color,size,outline:{color:'white',width:.7}}});
  const nec=point(data.centres.nec,'Existing NEC premises','diamond','#145341',5.5);
  const caseLayers=data.cases.map((c,i)=>{
   const areas=['A_status','venue_status'].map((field,side)=>geo(c.coverage,side?'After using a community venue':'After adding model A',{type:'unique-value',field,uniqueValueInfos:[['Already covered','#e7e9e8'],['Newly covered',side?'#b79b7a':'#af98c4'],['Still outside','#f4eee7']].map(([value,color])=>({value,label:value,symbol:fill(color)}))}));
   const fc=role=>({type:'FeatureCollection',features:c.points.features.filter(f=>f.properties.role===role)});
   const points=[point(fc('A'),'Hypothetical model reference A','x','#70518f',10),point(fc('HALL'),'Existing community venue','square','#b75d22',8)];
   for(const l of [...areas,...points])l.visible=i===0;
   return {areas,points};
  });
  const outline=geo(data.outline,'Study area boundary',{type:'simple',symbol:{type:'simple-line',color:'#802835',width:1}});
  const map=new Map({basemap:new Basemap({baseLayers:[new VectorTileLayer({style:new URL('../elderly-map/native-basemap.json',location.href).href})]}),layers:[land,...caseLayers.flatMap(c=>c.areas),nec,...caseLayers.flatMap(c=>c.points),outline]});
  const view=new MapView({container:'map',map,center:[114.17,22.28],zoom:14,ui:{components:['attribution','zoom']}});await view.when();
  const home=new Home({view});view.ui.move('zoom','bottom-right');view.ui.add(home,'top-right');view.ui.add(new Fullscreen({view,element:document.body}),'top-right');
  const swipe=new Swipe({view,leadingLayers:[caseLayers[0].areas[0],caseLayers[0].points[0]],trailingLayers:[caseLayers[0].areas[1],caseLayers[0].points[1]],position:50});view.ui.add(swipe);
  const selector=document.getElementById('case');data.cases.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.id+' '+c.name;selector.append(o)});
  async function select(i){selector.value=String(i);caseLayers.forEach((c,j)=>[...c.areas,...c.points].forEach(l=>l.visible=i===j));swipe.leadingLayers=[caseLayers[i].areas[0],caseLayers[i].points[0]];swipe.trailingLayers=[caseLayers[i].areas[1],caseLayers[i].points[1]];const e=data.cases[i].extent;await view.goTo(new Extent({...e,spatialReference:{wkid:4326}}),{animate:false});home.viewpoint=view.viewpoint.clone();if(window.__comparison)window.__comparison.panels=caseLayers[i].areas;}
  selector.onchange=()=>select(+selector.value);await Promise.all(map.layers.toArray().map(l=>l.load()));await select(0);
  const ready=()=>new Promise(resolve=>{let n=0;const timer=setInterval(()=>{if(!view.updating||++n>150){clearInterval(timer);resolve()}},100)});await ready();document.getElementById('loading').remove();
  window.__comparison={view,map,swipe,data,panels:caseLayers[0].areas,select,ready};window.addEventListener('pagehide',()=>urls.forEach(u=>URL.revokeObjectURL(u)),{once:true});
 }
 start().catch(error=>{document.getElementById('loading').textContent='Unable to load comparison. Please refresh.';console.error(error)});
});
