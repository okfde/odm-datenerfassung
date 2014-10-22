import urllib, json
import unicodecsv as csv

import metautils

from dbsettings import settings

jsonurl = urllib.urlopen("http://daten.bremen.de/sixcms/detail.php?template=export_daten_json_d")

packages = json.loads(jsonurl.read())

datafordb = []

for package in packages:
    row = metautils.getBlankRow()
    row[u'Stadt'] = 'bremen'
    row[u'Dateibezeichnung'] = package['title']
    row[u'Beschreibung'] = package['notes']
    row[u'URL PARENT'] = package['url']
    
    #Get resources and formats
    if ('resources' in package and len(package['resources']) > 0):
        formats = []
        files = []
        for resource in package['resources']:
            files.append(resource['url'])
            formats.append(resource['format'])
        [formattext, geo] = metautils.processListOfFormats(formats)
        row[u'Format'] = formattext
        row[u'geo'] = geo
        row[u'files'] = files
        
    if 'temporal_coverage_from' in package['extras'] and len(package['extras']['temporal_coverage_from'])>3:
        row[u'Zeitlicher Bezug'] = package['extras']['temporal_coverage_from'][0:4]
    
    if ('terms_of_use' in package['extras'] and len(package['extras']['terms_of_use']) > 0):
        row[u'Lizenz'] = package['extras']['terms_of_use']['licence_id']

    groups = u''
    if ('groups' in package and len(package['groups']) > 0):
        for group in package['groups']:
            odm_cats = metautils.govDataShortToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''
                
    #Store a copy of the metadata
    row['metadata'] = package
                
    datafordb.append(row)

#Write data to the DB
metautils.setsettings(settings)
#Remove this catalog's data
metautils.removeDataFromPortal('daten.bremen.de')
#Add data
metautils.addDataToDB(datafordb=datafordb, originating_portal='daten.bremen.de', checked=True, accepted=True)



