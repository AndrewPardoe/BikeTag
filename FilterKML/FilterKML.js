/*  Node.js app to filter some values from a KML file. Very specific to my scenario.

    Given a KML file from https://www.google.com/maps/d/viewer?mid=1ALf0s6IwCar4juuSamKjhZuOBVoPvSfk 
    named SeattleBikeTag.kml, remove all bike tags contained in excludes array. Create a file called
    SeattleBikeTag.new.kml. This SeattleBikeTag.new.kml file can be uploaded to a new Google Map.
*/

var fs = require('fs'),
    path = require('path'),
    xmlReader = require('read-xml')
    ;
var convert = require('xml-js');
require("dotenv").config();

// Customize the paths here
const FILE = path.join(__dirname, '/SeattleBikeTag.kml'); 
var excludes = populateExcludes(path.join(process.env.ONEDRIVE, '/Biketag'));

xmlReader.readXML(fs.readFileSync(FILE), function(err, data) {
    if (err) {
        console.error(err);
    }

    var xml = data.content;
    var results = JSON.parse(convert.xml2json(xml, {compact: true, spaces: 4}));

    for (var i=0; i < results.kml.Document.Folder.Placemark.length; i++) {
        let name = results.kml.Document.Folder.Placemark[i]['name'];
        let description = name._text ? name._text : name._cdata;
        let tagNum = parseInt(description.substring(0, description.indexOf(':')));
        if (excludes.includes(tagNum)) {
            delete results.kml.Document.Folder.Placemark[i];
        }
    }

    var newXml = convert.json2xml(results, {compact: true, spaces: 4});
    let newFile = FILE.substring(0, FILE.indexOf('.kml')) + '.new' +  FILE.substring(FILE.indexOf('.kml'));
    var ws = fs.createWriteStream(newFile);
    ws.write(newXml);
    ws.end();

});

/*  This function populates the excludes array for my setup.
    I have a directory with a bunch of biketag photos named 001.jpg, 002.heic, 003.png, etc.
    The numbers 001, 002, 003 are the biketags I want to exclude from the new map.
    Your setup almost certainly varies :)
*/

function populateExcludes(dir) {
    // Populate list of locations to exclude in excludes array
    const tag = /^\d{3}/; // filename format: 007.jpg
    let excludes = new Array();

    try {
        const files = fs.readdirSync(dir);
        files.forEach(file => {
            if (result = file.match(tag)) {
                excludes.push(parseInt(result[0])); // also strips leading zeroes
            }
        });
    } catch (err) {
        console.error(err);
    }
    return excludes;
}