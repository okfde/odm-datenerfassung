import urllib, json
import unicodecsv as csv
import sys

geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS')

csvoutfile = open(sys.argv[1], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

csvfilesoutfile = open(sys.argv[1]+'.files', 'wb')
filesdatawriter = csv.writer(csvfilesoutfile, delimiter=',')

columns = ['title', 'name', 'notes', 'id', 'url', 'author', 'author_email', 'maintainer', 'maintainer_email', 'metadata_created', 'metadata_modified', 'capacity', 'state',  'version', 'license_id']

row = []
extraitems = ['format', 'geo', 'groups', 'tags']
row.extend(extraitems);
columnsoffset = len(extraitems)

for column in columns:
    row.append(column);

datawriter.writerow(row)

jsonurl = urllib.urlopen("http://www.opendata-hro.de/api/2/search/dataset?q=&limit=1000&all_fields=1")

data = json.loads(jsonurl.read())

for package in data['results']:
    row = []
    
    #All files, for analysis
    dict_string = package['data_dict']
    json_dict = json.loads(dict_string)
    for resource in json_dict['resources']:
        frow = []
        frow.append(resource['url'])
        filesdatawriter.writerow(frow)
    
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
        
    groups = u''
    tags = u''

    if ('groups' in package and len(package['groups']) > 0):
        for group in package['groups']:
            groups += (group + ',')
        #get rid of last comma
        groups = groups[:len(groups)-1]
        row.append(groups)

    if ('tags' in package and len(package['tags']) > 0):
        for tag in package['tags']:
            tags += (tag + ',')
        #get rid of last comma
        tags = tags[:len(tags)-1]
        row.append(tags)


    for column in columns:
        row.append(package[column])

    if row[columns.index('url') + columnsoffset] == '':
        row[columns.index('url') + columnsoffset] = 'http://www.opendata-hro.de/dataset/' + row[columns.index('id') + columnsoffset]    
    datawriter.writerow(row)

csvoutfile.close();

