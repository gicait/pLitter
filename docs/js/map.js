function heatmap(){
var mymap = L.map('map').setView([14.0823695,100.6126375], 13);

googleStreets = L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
maxZoom: 20,
subdomains:['mt0','mt1','mt2','mt3']
});
googleStreets.addTo(mymap)


// don't forget to include leaflet-heatmap.js
var testData = {
max: 2,
data: [{lat: 14.0823695, lng:100.6126375, count: 3},{lat: 14.0822, lng:100.61300, count: 1}]
};

var cfg = {
// radius should be small ONLY if scaleRadius is true (or small radius is intended)
// if scaleRadius is false it will be the constant radius used in pixels
"radius": 0.1,
"maxOpacity": .5,
// scales the radius based on map zoom
"scaleRadius": true,
// if set to false the heatmap uses the global maximum for colorization
// if activated: uses the data maximum within the current map boundaries
//   (there will always be a red spot with useLocalExtremas true)
"useLocalExtrema": true,
// which field name in your data represents the latitude - default "lat"
latField: 'lat',
// which field name in your data represents the longitude - default "lng"
lngField: 'lng',
// which field name in your data represents the data value - default "value"
valueField: 'count'
};


var heatmapLayer = new HeatmapOverlay(cfg);
heatmapLayer.setData(testData);
heatmapLayer.addTo(mymap)


window.onresize = doALoadOfStuff;

function doALoadOfStuff() {
    //do a load of stuff
    // alert("working")
   setTimeout(function(){ mymap.invalidateSize()}, 400);
}
}
//     L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
//     attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
//     maxZoom: 18,
//     id: 'mapbox/streets-v11',
//     tileSize: 512,
//     zoomOffset: -1,
//     accessToken: 'your.mapbox.access.token'
// }).addTo(mymap);












