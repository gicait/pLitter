const gpmfExtract = require('gpmf-extract');
const goproTelemetry = require(`gopro-telemetry`);
const fs = require('fs');

const videoFile = process.argv.slice(2)[0];
console.log(videoFile);
const file = fs.readFileSync(videoFile);

gpmfExtract(file)
  .then(extracted => {
    goproTelemetry(extracted, {stream: ['GPS5'], preset: 'csv'}, telemetry => {
      const csvFile = videoFile.substr(0, videoFile.lastIndexOf(".")) + "_" + Object.keys(telemetry)[0] +".csv"
      console.log(csvFile);
      fs.writeFileSync(csvFile, telemetry[Object.keys(telemetry)[0]]);
      console.log('Telemetry saved as csv');
    });
  })
  .catch(error => console.error(error));
