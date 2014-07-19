import urllib, json
import unicodecsv as csv
import sys

geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS')

csvoutfile = open(sys.argv[1], 'wb')
datawriter = csv.writer(csvoutfile, delimiter=',')

columns = ['title', 'name', 'notes', 'url']

row = []

for column in columns:
    row.append(column);
    
row.extend(['format', 'geo', 'groups', 'tags', 'ansprechpartner', 'ansprechpartner_email', 'erstellt', 'aktualisiert', 'veroeffentlicht', 'licence_id', 'attribution_text'])

extras = ['temporal_coverage_from', 'temporal_coverage_to', 'temporal_granularity', 'metadata_original', 'metadata_original_portal', 'ogdd_version']

row.extend(extras)

datawriter.writerow(row)

jsonurl = urllib.urlopen("http://daten.bremen.de/sixcms/detail.php?template=export_daten_json_d")

packages = json.loads(jsonurl.read())

for package in packages:
    row = []
    
    for column in columns:
        row.append(package[column])
    
    #Get resource formats
    if ('resources' in package and len(package['resources']) > 0):
        geo = ''
        text = ""
        formats = []
        for resource in package['resources']:
            if (resource['format'] not in formats):
                formats.append(resource['format'].upper())
                if (resource['format'].upper() in geoformats):
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

    ansprechpartner = u''
    ansprechpartner_email = u''
    
    if ('contacts' in package['extras'] and len(package['extras']['contacts']) > 0):
        for entry in package['extras']['contacts']:
            if entry['role'] == 'ansprechpartner':
                ansprechpartner = entry['name']
                ansprechpartner_email = entry['email']
                break
    
    erstellt = ''
    aktualisiert = ''
    veroeffentlicht = ''
    
    if ('dates' in package['extras'] and len(package['extras']['dates']) > 0):
        for entry in package['extras']['dates']:
            if entry['role'] == 'erstellt':
                erstellt = entry['date']
            elif entry['role'] == 'aktualisiert':
                aktualisiert = entry['date']
            elif entry['role'] == 'veroeffentlicht':
                veroeffentlicht = entry['date']
                
    licence_id = ''
    attribution_text = u''
    
    if ('terms_of_use' in package['extras'] and len(package['extras']['terms_of_use']) > 0):
        licence_id = package['extras']['terms_of_use']['licence_id']
        attribution_text = package['extras']['terms_of_use']['attribution_text']
        
    row.extend([ansprechpartner, ansprechpartner_email, erstellt, aktualisiert, veroeffentlicht, licence_id, attribution_text])
        
    for column in extras:
        if column in package['extras']:
        		row.append(package['extras'][column])
        else:
            row.append('')
    
    datawriter.writerow(row)

csvoutfile.close();

