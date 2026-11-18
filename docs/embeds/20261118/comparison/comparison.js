"use strict";
const element = id => document.getElementById(id);
let map;

function rgba([r, g, b, a]) {
  return `rgba(${r},${g},${b},${a / 255})`;
}

function layerData(source, id) {
  return source.operationalLayers.find(layer => layer.id === id).featureCollection.layers[0];
}

function coordinates([x, y], sr) {
  return sr.wkid === 4326 ? L.latLng(y, x) : L.CRS.EPSG3857.unproject(L.point(x, y));
}

function renderAreas(source, layerId, pane) {
  const {featureSet, layerDefinition} = layerData(source, layerId);
  const renderer = layerDefinition.drawingInfo.renderer;
  const ranges = renderer.classBreakInfos;
  for (const feature of featureSet.features) {
    const value = feature.attributes[renderer.field];
    const band = value == null ? null : ranges.find(b => value <= b.classMaxValue);
    const symbol = band?.symbol ?? renderer.defaultSymbol;
    if (!symbol) continue;
    const polygon = L.polygon(feature.geometry.rings.map(ring =>
      ring.map(point => coordinates(point, featureSet.spatialReference))), {
      pane, fillColor: rgba(symbol.color), fillOpacity: .91,
      color: "#fff", opacity: .84, weight: .55
    });
    const popup = document.createElement("span");
    popup.textContent = `STPUG ${feature.attributes.stpug_id} · ${value == null ? "Not assessed" : Number(value).toFixed(2) + "% beyond 800 m"}`;
    polygon.bindPopup(popup).addTo(map);
  }
  return renderer;
}

function sharedContext(source) {
  const bounds = L.latLngBounds();
  const boundary = layerData(source, "study_outline").featureSet;
  for (const feature of boundary.features) {
    const outline = L.polyline(feature.geometry.paths.map(path => path.map(p => coordinates(p, boundary.spatialReference))), {
      pane: "reference", color: "#802835", weight: 1.2, interactive: false
    });
    bounds.extend(outline.getBounds());
    outline.addTo(map);
  }
  const centres = layerData(source, "nec").featureSet;
  for (const feature of centres.features) {
    const mark = document.createElement("div");
    mark.style.cssText = "width:100%;height:100%;background:#145341;border:1px solid white;transform:rotate(45deg)";
    L.marker(coordinates([feature.geometry.x,feature.geometry.y],centres.spatialReference), {
      pane:"reference", interactive:false,
      icon:L.divIcon({className:"facility", html:mark, iconSize:[7,7]})
    }).addTo(map);
  }
  return bounds;
}

function drawLegend(target, title, subtitle, renderer) {
  const section = element(target);
  const heading = document.createElement("h2");
  heading.textContent = title;
  const description = document.createElement("p");
  description.textContent = subtitle;
  const list = document.createElement("ul");
  function entry(label, color, facility = false) {
    const row = document.createElement("li"), swatch = document.createElement("i");
    if (facility) swatch.className = "facility";
    swatch.style.background = color;
    row.append(swatch, document.createTextNode(label));
    list.append(row);
  }
  for (const band of renderer.classBreakInfos) entry(band.label, rgba(band.symbol.color));
  if (renderer.defaultSymbol) entry(renderer.defaultLabel || "Not assessed", rgba(renderer.defaultSymbol.color));
  entry("NEC", "#145341", true);
  section.append(heading, description, list);
  section.hidden = false;
}

function start() {
  const { "02_euclidean": left, "03_network": right } = window.networkMaps;
  if (!left || !right) throw Error("Comparison data unavailable.");
  map = L.map("map", {scrollWheelZoom:false, minZoom:7, maxZoom:16, zoomSnap:.1,
    zoomAnimation:false, attributionControl:false});
  L.control.attribution({prefix:false}).addTo(map).addAttribution("HKSAR Government CSDI · Tiles © Esri, HERE, Garmin");
  L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    {maxNativeZoom:16, maxZoom:16, className:"context-tiles"}).addTo(map);
  const leftPane = map.createPane("straight"), rightPane = map.createPane("network");
  leftPane.style.zIndex = rightPane.style.zIndex = 420;
  map.createPane("reference").style.zIndex = 440;
  drawLegend("left-legend", "Straight-line gap", "Residential land beyond 800 m", renderAreas(left,"eu","straight"));
  drawLegend("right-legend", "3D network gap", "Lower bound beyond 800 m", renderAreas(right,"net","network"));
  const bounds = sharedContext(left);
  const divider = element("divider"), handle = element("handle");
  let split = 50;
  function clip() {
    const size = map.getSize();
    const first = map.containerPointToLayerPoint([0,0]);
    const x = first.x + size.x * split / 100, right = first.x + size.x, bottom = first.y + size.y;
    leftPane.style.clipPath = `polygon(${first.x}px ${first.y}px,${x}px ${first.y}px,${x}px ${bottom}px,${first.x}px ${bottom}px)`;
    rightPane.style.clipPath = `polygon(${x}px ${first.y}px,${right}px ${first.y}px,${right}px ${bottom}px,${x}px ${bottom}px)`;
    divider.style.left = split + "%";
    handle.setAttribute("aria-valuenow", Math.round(split));
  }
  function move(value) {
    split = Math.max(0, Math.min(100, value));
    clip();
  }
  function reset() {
    map.fitBounds(bounds, {paddingTopLeft:[18,18],paddingBottomRight:[18,34],animate:false});
    move(50);
  }
  function drag(e) {
    const r = element("map").getBoundingClientRect();
    move(100 * (e.clientX - r.left) / r.width);
  }
  handle.addEventListener("pointerdown", e => { handle.setPointerCapture(e.pointerId); drag(e); });
  handle.addEventListener("pointermove", e => { if (handle.hasPointerCapture(e.pointerId)) drag(e); });
  handle.addEventListener("keydown", e => {
    const values = {ArrowLeft:split-3, ArrowRight:split+3, Home:0, End:100};
    if (!(e.key in values)) return;
    e.preventDefault();
    move(values[e.key]);
  });
  map.on("move zoomend",clip);
  new ResizeObserver(() => {map.invalidateSize({pan:false});clip();}).observe(element("map"));
  element("reset").onclick = reset;
  reset();
  divider.hidden = element("reset").hidden = false;
  element("status").hidden = true;
}

try {
  start();
} catch (error) {
  element("status").textContent = error.message;
}
