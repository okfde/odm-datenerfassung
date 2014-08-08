import warc
import sys
import unicodecsv as csv

filetypes = ['.CSV', '.XLS', '.XLSX', '.JSON', '.RDF', '.ZIP']
geofiletypes = ('.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS')
filetypes.extend(geofiletypes)

csvoutfile = open(sys.argv[1]+'.data.csv', 'a+b')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = ['Stadt_URL', 'URL_Datei', 'URL_Text', 'URL_Dateiname', 'Format', 'geo', 'URL_PARENT', 'Title_Parent']

datawriter.writerow(columns)

f = warc.open(sys.argv[2])
domain = sys.argv[1]
blacklist = ('.jpg', '.gif', '.ico', '.txt', '.pdf', '.png', 'dns:', '.css', '.js')

for record in f:
    if ('WARC-Target-URI' in record.header) and (domain in record['WARC-Target-URI']) and not any(x in record['WARC-Target-URI'] for x in blacklist) and 'metadata' in record['warc-type']:
        #for item in record.__dict__['header'].items():
            #print item
        for line in record.__dict__['payload'].read().split('\n'):
            if any(ext in line.upper() for ext in filetypes):
                url = line.split(' ')[1] 
                extension = url.split('.')[-1].upper()
                geo = ''
                if (('.' + extension) in geofiletypes):
                    geo = 'x'
                filename = url.split('/')[-1]
                row = [sys.argv[1],url,'',filename,extension,geo,record.header['WARC-Target-URI'],'']
                datawriter.writerow(row)

csvoutfile.close()
