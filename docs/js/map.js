var mymap = L.map("leaflet_map", {maxZoom: 20}).setView([ 14.014359204645759, 100.61305046081544], 13);
// var lastZoom = 13
var tileLayer = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
  attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
  maxZoom: 20 ,
  id: 'mapbox/streets-v11',
  tileSize: 512,
  zoomOffset: -1,
  accessToken: 'pk.eyJ1IjoibmlzY2hhbGIiLCJhIjoiY2tydDN2OWJzMWQ5YTJ0cGZuZDU4cXptcCJ9.93a5e6uSq2ta0ATUyhBZTw'
})

googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',{
  maxZoom: 20,
  subdomains:['mt0','mt1','mt2','mt3']
});

tileLayer.addTo(mymap);

setTimeout(() => {
    console.log("LoL! Alright!")
    mymap.invalidateSize();
  }, 1000
);

async function getImagesAndClusters(bounds, zoom) {
  console.log(bounds._northEast);
  console.log(bounds._southWest);

  var left = bounds._southWest.lng;
  var top = bounds._northEast.lat;
  var right = bounds._northEast.lng;
  var bottom = bounds._southWest.lat;


  let response = await fetch("https://citizens.plitter.org/api/image/map", {
  // let response = await fetch("http://203.159.29.159:5000/api/image/map", {
    "headers": {
      "accept": "application/json",
      "accept-language": "en-US,en;q=0.9",
      "content-type": "application/json",
      "sec-gpc": "1"
    },
    "referrer": "http://203.159.29.187:5000/api/",
    "referrerPolicy": "strict-origin-when-cross-origin",
    "body": JSON.stringify({ "left": left, "top": top, "right": right, "bottom": bottom, "zoom": zoom }),
    "method": "POST",
    "mode": "cors",
    "credentials": "include"
  });
  let data = response.json();
  return data;
}

var geojsonMarkerOptions = {
  radius: 3,
  fillColor: "#ff7800",
  color: "#000",
  weight: 1,
  opacity: 1,
  fillOpacity: 0.8,
  renderer: L.canvas({padding: 0.5})
};

// function imageIdToUrl(id) {
//   // const BASE_URL = "https://annotator.ait.ac.th/api/image/";
//   const BASE_URL = "http://203.159.29.159:5000/api/image/";
//   return BASE_URL + id;
// }

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

function makepopuphtml(imageId) {
  // const BASE_URL = "http://203.159.29.159:5000/api/image/";
  const BASE_URL = "https://annotator.ait.ac.th/api/image/";
  let imageUrl = BASE_URL + imageId
  let prevId = imageId == 0 ? 0 : imageId - 1;
  let nextId = imageId + 1;

  let popupHtml = `
    <div class='container'> <div class='row'>
      <span onclick="image_markers['${prevId}'].openPopup()"><i class="fas fa-arrow-left"></i></span>
      <img src="${imageUrl}" style="max-width: 200px; max-height: 200px">
      <span onclick="image_markers['${nextId}'].openPopup()"><i class="fas fa-arrow-right"></i></span>
    </div></div>
  `;

  return popupHtml;
}

var image_markers = {}
var featureLayer = L.geoJSON(null, {
  filter: function(feature, layer) { if(image_markers.hasOwnProperty(feature.properties.image_id)){ return false;} else { return true;} },
  pointToLayer: function (feature, latlng) { let marker = L.circleMarker(latlng, geojsonMarkerOptions); image_markers[feature.properties.image_id] = marker; return marker; },
  onEachFeature: function (feature, layer) { if(feature.properties.image_id){ layer.bindPopup(makepopuphtml(feature.properties.image_id));}},
  renderer: L.canvas({padding: 0.5})
}).addTo(mymap);

var clusterLayer = L.geoJSON(null, {}).addTo(mymap);

async function update() {
  // var presentZoom = mymap.getZoom()
  // if(presentZoom != lastZoom) {
    // mymap.eachLayer(function (layer) {
    //   if (layer._leaflet_id != tileLayer._leaflet_id) mymap.removeLayer(layer);
    // });
    var dataGeoJson = await getImagesAndClusters(mymap.getBounds(), mymap.getZoom());
    // console.log(dataGeoJson)
    if(dataGeoJson['type'] == "ClusterCollection"){
      clusterCollection = dataGeoJson['clusters'];
      // console.log(clusterCollection);
      // if(clusterLayer){
      //   clusterLayer.remove();
      // }
      if(mymap.hasLayer(clusterLayer)){
        mymap.removeLayer(clusterLayer);
      }
      clusterLayer = L.geoJSON(null, {}).addTo(mymap);
      clusterCollection.forEach((cluster, index) => {
        // console.log(cluster.latitude, cluster.longitude, cluster.count);
        const size =
          cluster.count < 100 ? 'small' :
          cluster.count < 1000 ? 'medium' : 'large';
        const icon = L.divIcon({
          html: `<div><span>${  abbreviate_number(cluster.count)  }</span></div>`,
          className: `marker-cluster marker-cluster-${  size}`,
          iconSize: L.point(40, 40)
        });
        var circlec = L.marker([cluster.latitude, cluster.longitude], {icon}).addTo(clusterLayer);
      });
    }
    if(dataGeoJson['type'] == "FeatureCollection"){
      if(mymap.hasLayer(clusterLayer)){
        mymap.removeLayer(clusterLayer);
      }
      featureCollection = dataGeoJson['features']
      console.log(featureCollection);
      featureLayer.addData(featureCollection);
    }
  // }
}

mymap.on('moveend', () => {
  update();
});
