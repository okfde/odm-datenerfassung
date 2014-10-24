# -*- coding: utf-8 -*-
import urllib, json
import unicodecsv as csv
import sys

import metautils

from dbsettings import settings

if sys.argv[1] == 'bremen':
    city = 'bremen'
    portalname = 'daten.bremen.de'
    jsonurl = 'http://daten.bremen.de/sixcms/detail.php?template=export_daten_json_d'
    jsonurl = urllib.urlopen(jsonurl)
    packages = json.loads(jsonurl.read())
elif sys.argv[1] == 'moers':
    city = 'moers'
    portalname = 'offenedaten.moers.de'
    jsonurl = 'http://download.moers.de/Open_Data/Gesamtdatei/Moers_alles.json'
    jsonurl = urllib.urlopen(jsonurl)
    #The JSON file is very broken, and this is probably not the best way to fix it, but it might change tomorrow, so...
    jtexts = jsonurl.read().split('\"name\"')
    jtexts[len(jtexts)-1] = jtexts[len(jtexts)-1] + ' '
    del jtexts[0]
    packages = []
    for text in jtexts:
	jtext = ('[{\"name\"' + text[0:len(text)-7] + ']').replace('application\\', 'application/').replace('\r', '').replace('\n', '').replace('},"license_id"', ']},"license_id"').replace('"description": "Ressourcen: Folgende Felder können für jede Ressource individuell angegeben werden.","type": "array","items": {','"description": "Ressourcen: Folgende Felder können für jede Ressource individuell angegeben werden.","type": "array","items": [{') 
        package = json.loads(jtext)
	packages.append(package[0])
    #Save the fixed JSON
    with open('../metadata/moers/catalog.json', 'wb') as outfile:
        json.dump(packages, outfile)

datafordb = []
for part in packages:

    row = metautils.getBlankRow()

    if city == 'moers':
        package = {}
        #Simplify JSON
        package['title'] = part['title']['description']
        package['notes'] = part['notes']['description']
        package['author'] = part['author']['description']
        package['url'] = part['url']['description']
        package['groups'] = [part['subgroups']['items']['description']]
	if 'resources' in part:
            package['resources'] = []
	    for theresource in part['resources']['items']:
                resource = {}
	        resource['url'] = theresource['properties']['url']['description']
                resource['format'] = theresource['properties']['format']['description'].split('/')[1].upper()
                if 'moers.de' not in resource['url']:
                    resource['url'] = 'http://www.moers.de' + package['url']
                if resource['format'] == 'NSF': resource['format'] = 'XML'
                package['resources'].append(resource)
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



