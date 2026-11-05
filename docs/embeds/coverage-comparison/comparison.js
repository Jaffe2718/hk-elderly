"use strict";
require(['esri/Map','esri/views/MapView','esri/layers/GeoJSONLayer','esri/layers/VectorTileLayer','esri/Basemap','esri/widgets/Swipe','esri/widgets/Home','esri/widgets/Fullscreen','esri/geometry/Extent'],(Map,MapView,GeoJSONLayer,VectorTileLayer,Basemap,Swipe,Home,Fullscreen,Extent)=>{
 async function start(){
  const response=await fetch('data.json');if(!response.ok)throw Error('Comparison data unavailable');const data=await response.json();
  const urls=[];function geo(fc,title,renderer){const url=URL.createObjectURL(new Blob([JSON.stringify(fc)],{type:'application/geo+json'}));urls.push(url);return new GeoJSONLayer({url,title,renderer,outFields:['*'],copyright:'GEOG7302 Group 13 · supplied 2021 land and 2026 premises'});}
  const fill=c=>({type:'simple-fill',color:c,outline:{color:'#fff',width:.5}});
  const land=geo(data.land,'Study area',{type:'simple',symbol:fill('#f7f9f8')});
  const panels=data.panels.map((p,i)=>geo(p.residential,i?'NEC + DECC':'NEC only',{type:'unique-value',field:p.field,uniqueValueInfos:[{value:0,label:'Within 800 m',symbol:fill(i?'#f3eadf':'#eee8f4')},{value:1,label:'Beyond 800 m',symbol:fill(i?'#b79b7a':'#af98c4')}]}));
  const sites=(key,style,color)=>geo(data[key],key==='nec_sites'?'NEC premises':'DECC premises',{type:'simple',symbol:{type:'simple-marker',style,color,size:style==='diamond'?5.5:7,outline:{color:'white',width:.7}}});
  const nec=sites('nec_sites','diamond','#145341'),decc=sites('decc_sites','triangle','#b75d22');
  const outline=geo(data.outline,'Study area boundary',{type:'simple',symbol:{type:'simple-line',color:'#802835',width:1}});
  const map=new Map({basemap:new Basemap({baseLayers:[new VectorTileLayer({style:new URL('../elderly-map/native-basemap.json',location.href).href})]}),layers:[land,...panels,nec,decc,outline]});
  const view=new MapView({container:'map',map,center:[114.25,22.3],zoom:14,ui:{components:['attribution','zoom']}});await view.when();
  const home=new Home({view});view.ui.move('zoom','bottom-right');view.ui.add(home,'top-right');view.ui.add(new Fullscreen({view,element:document.body}),'top-right');
  const swipe=new Swipe({view,leadingLayers:[panels[0]],trailingLayers:[panels[1],decc],position:50});view.ui.add(swipe);
  const selector=document.getElementById('case');data.cases.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.name;selector.append(o)});
  async function select(i){selector.value=String(i);const e=data.cases[i].extent;await view.goTo(new Extent({...e,spatialReference:{wkid:4326}}),{animate:false});home.viewpoint=view.viewpoint.clone();}
  selector.onchange=()=>select(+selector.value);await Promise.all([land,...panels,nec,decc,outline].map(l=>l.load()));await select(2);
  const ready=()=>new Promise(resolve=>{let n=0;const timer=setInterval(()=>{if(!view.updating||++n>150){clearInterval(timer);resolve()}},100)});await ready();document.getElementById('loading').remove();
  window.__comparison={view,map,swipe,data,panels,select,ready};window.addEventListener('pagehide',()=>urls.forEach(u=>URL.revokeObjectURL(u)),{once:true});
 }
 start().catch(error=>{document.getElementById('loading').textContent='Unable to load comparison. Please refresh.';console.error(error)});
});
