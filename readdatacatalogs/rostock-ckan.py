import urllib, json
import unicodecsv as csv
import sys

geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS')

csvoutfile = open(sys.argv[1], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = ['title', 'name', 'notes', 'id', 'url', 'author', 'author_email', 'maintainer', 'maintainer_email', 'metadata_created', 'metadata_modified', 'capacity', 'state',  'version', 'license_id']

row = []
row.extend(['format', 'geo']);

for column in columns:
    row.append(column);

datawriter.writerow(row)

jsonurl = urllib.urlopen("http://www.opendata-hro.de/api/2/search/dataset?q=&limit=1000&all_fields=1")

groups = json.loads(jsonurl.read())

for package in groups['results']:
    row = []
    
    #Get resource formats
    if ('res_format' in package and len(package['res_format']) > 0):
        geo = ''
        text = ""
        formats = []
        for format in package['res_format']:
            if (format.upper() not in formats):
                formats.append(format.upper())
                if (format.upper() in geoformats):
                    geo = 'x'
        
        for format in formats:
            text += (format + ',')
            
        #get rid of last comma
        text = text[:len(text)-1]
        row.extend([text, geo])
        
    for column in columns:
        row.append(package[column])
        
    datawriter.writerow(row)

csvoutfile.close();

