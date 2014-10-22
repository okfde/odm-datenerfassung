#Moers data doesn't read well with json module... strange
import urllib, simplejson
import unicodecsv as csv
import sys

import metautils

from dbsettings import settings

if sys.argv[1] == 'bremen':
    city = 'bremen'
    portalname = 'daten.bremen.de'
    jsonurl = 'http://daten.bremen.de/sixcms/detail.php?template=export_daten_json_d'
    jsonurl = urllib.urlopen(jsonurl)
    packages = simplejson.loads(jsonurl.read())
elif sys.argv[1] == 'moers':
    city = 'moers'
    portalname = 'offenedaten.moers.de'
    jsonurl = 'http://download.moers.de/Open_Data/Gesamtdatei/Moers_alles.json'
    jsonurl = urllib.urlopen(jsonurl)
    jtext = jsonurl.read().replace('\r','').replace('}\n}\n}]','}]').replace('}\n}\n},{', '},{').replace('\\', '\\\\')
    packages = simplejson.loads(jtext)
    #Save the fixed JSON
    with open('../metadata/moers/catalog.json', 'wb') as outfile:
        simplejson.dump(packages, outfile)

datafordb = []

for part in packages:

    row = metautils.getBlankRow()

    if city == 'moers':
        part = part['properties']
        package = {}
        #Simplify JSON
        package['title'] = part['title']['description']
        package['notes'] = part['notes']['description']
        package['author'] = part['author']['description']
        package['url'] = part['url']['description']
        package['groups'] = [part['subgroups']['items']['description']]
        if part['resources']['items']['properties']['url']['description'].strip() != '':
            package['resources'] = [{}]
            package['resources'][0]['url'] = part['resources']['items']['properties']['url']['description']
            if 'apijson' in package['resources'][0]['url']:
                package['resources'][0]['format'] = 'JSON'
            elif 'webio.nsf' in package['resources'][0]['url']:
                package['resources'][0]['format'] = 'XML'
            elif '.csv' in package['resources'][0]['url']:
                package['resources'][0]['format'] = 'CSV'
            else:
                print 'Could not guess format: ' + package['url'] + ', ' + package['resources'][0]['url']
            if 'moers.de' not in package['resources'][0]['url']:
                package['resources'][0]['url'] = 'http://www.moers.de' + package['resources'][0]['url']
        package['extras'] = {}
        package['extras']['temporal_coverage_from'] = part['extras']['properties']['dates']['items']['properties']['date']['description'][6:10]
        package['extras']['terms_of_use'] = {}
        package['extras']['terms_of_use']['licence_id'] = part['license_id']['description']
        #Store a copy of the metadata
        row['metadata'] = part
    elif city == 'bremen':
        package = part
        #Store a copy of the metadata
        row['metadata'] = package

    row[u'Stadt'] = city
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
            if city == 'moers':
                odm_cats = metautils.govDataLongToODM(group)
            elif city == 'bremen':
                odm_cats = metautils.govDataShortToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''

    datafordb.append(row)

#Write data to the DB
metautils.setsettings(settings)
#Remove this catalog's data
metautils.removeDataFromPortal(portalname)
#Add data
metautils.addDataToDB(datafordb=datafordb, originating_portal=portalname, checked=True, accepted=True)



