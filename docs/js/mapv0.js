
  var mymap = L.map("leaflet_map", {maxZoom: 20}).setView([ 14.014359204645759, 100.61305046081544], 13);

  

  var tileLayer = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 20 ,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: 'pk.eyJ1IjoibmlzY2hhbGIiLCJhIjoiY2tydDN2OWJzMWQ5YTJ0cGZuZDU4cXptcCJ9.93a5e6uSq2ta0ATUyhBZTw'
})

tileLayer.addTo(mymap);


setTimeout(() => {
    console.log("loll")
    mymap.invalidateSize();
 }, 100);

const MARKERS = L.markerClusterGroup();
const MARKERS_BY_ID = {};
const lastZoom = 0;

mymap.on('moveend', async function(e) {
  var presentZoom = mymap.getZoom()
  if(presentZoom == lastZoom) {
    return undefined;
  }
  mymap.eachLayer(function (layer) {
    if (layer._leaflet_id != tileLayer._leaflet_id) mymap.removeLayer(layer);
  });

  var data = await getImagesAndClusters(mymap.getBounds());
  console.log("Got data:", data);

  var imageCount = 0;
  data?.images?.forEach((image, index) => {
      if (imageCount > 1000)  return;
    imageCount++;

      let prevId = data.images[index == 0 ? data.images.length - 1 : index - 1].id;
      let nextId = data.images[index == data.images.length - 1 ? 0 : index + 1].id;

      console.log(image)
      addImageToMap(mymap, image.location.coordinates[1], image.location.coordinates[0], image.id, prevId, nextId);
  });

  data?.clusters?.forEach((cluster, index) => {
    // check if image of cluster
    addClusterToMap(mymap, cluster.latitude, cluster.longitude, cluster.count);
  });
});

function addClusterToMap(map, xCoordinate, yCoordinate, count) {
  // todo: add count text
//   var circle = L.circleMarker([xCoordinate, yCoordinate], {
//     color: 'red',
//     fillColor: '#f03',
//     fillOpacity: 0.2,
//     radius: 10
//   }).addTo(mymap);

  const size =
    count < 100 ? 'small' :
    count < 1000 ? 'medium' : 'large';
  const icon = L.divIcon({
    html: `<div><span>${  abbreviate_number(count)  }</span></div>`,
    className: `marker-cluster marker-cluster-${  size}`,
    iconSize: L.point(40, 40)
  });

  var circlec = L.marker([xCoordinate, yCoordinate], {icon}).addTo(mymap)



}

function addImageToMap(map, xCoordinate, yCoordinate, imageId, prevId, nextId) {
  let marker = L.circleMarker([xCoordinate, yCoordinate], {"radius":4, fill:true, "fillColor": "#007bff", fillOpacity:5, "color": "#007bff", "weight": 1, "opacity": 10}).addTo(map);
  
  let popupHtml = `
    <div class='container'> <div class='row'>
      <span onclick="MARKERS_BY_ID['${prevId}'].openPopup()"><i class="fas fa-arrow-left"></i></span>
      <img src="${imageIdToUrl(imageId)}" style="max-width: 200px; max-height: 200px">
      <span onclick="MARKERS_BY_ID['${nextId}'].openPopup()"><i class="fas fa-arrow-right"></i></span>
    </div></div>
  `;
  marker.bindPopup(popupHtml);

  MARKERS_BY_ID[imageId] = marker;

  function imageIdToUrl(id) {
    // const BASE_URL = "https://annotator.ait.ac.th/api/image/";
    const BASE_URL = "http://203.159.29.51:5000/api/image/";
    return BASE_URL + id;
  }
}

abbreviate_number = function(num, fixed) {
    if (num === null) { return null; } // terminate early
    if (num === 0) { return '0'; } // terminate early
    fixed = (!fixed || fixed < 0) ? 0 : fixed; // number of decimal places to show
    var b = (num).toPrecision(2).split("e"), // get power
        k = b.length === 1 ? 0 : Math.floor(Math.min(b[1].slice(1), 14) / 3), // floor at decimals, ceiling at trillions
        c = k < 1 ? num.toFixed(0 + fixed) : (num / Math.pow(10, k * 3) ).toFixed(1 + fixed), // divide by power
        d = c < 0 ? c : Math.abs(c), // enforce -0 is 0
        e = d + ['', 'K', 'M', 'B', 'T'][k]; // append power
    return e;
}

async function getImagesAndClusters(bounds) {
  console.log(bounds._northEast);
  console.log(bounds._southWest);

  var left = bounds._southWest.lng;
  var top = bounds._northEast.lat;
  var right = bounds._northEast.lng;
  var bottom = bounds._southWest.lat;


  // let response = await fetch("https://annotator.ait.ac.th/api/image/map", {
  let response = await fetch("http://203.159.29.51:5000/api/image/map", {
    "headers": {
      "accept": "application/json",
      "accept-language": "en-US,en;q=0.9",
      "content-type": "application/json",
      "sec-gpc": "1"
    },
    "referrer": "http://203.159.29.187:5000/api/",
    "referrerPolicy": "strict-origin-when-cross-origin",
    "body": JSON.stringify({ "left": left, "top": top, "right": right, "bottom": bottom, "zoom": mymap.getZoom() }),
    "method": "POST",
    "mode": "cors",
    "credentials": "include"
  });

  let data = response.json();

  return data;
}
