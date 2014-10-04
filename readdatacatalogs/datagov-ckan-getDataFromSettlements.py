# -*- coding: utf-8 -*-
import sys
import json
import codecs
import unicodecsv as csv

import metautils

actualcategories = []

if (len(sys.argv)<3):
    print 'Usage: datagov-ckan-getDataFromSettlements datagovJSONDump.json outputFile.csv [list,of,portals,to,exclude]'
    exit()

excludes = []

if (len(sys.argv)>3):
    excludes = sys.argv[3].split(',')
    print 'Excluding following portals:'
    for portal in excludes:
        print portal
        
cities = metautils.getCities()

with open(sys.argv[1], 'rb') as jsonfile:
    text = jsonfile.read()
    data = json.loads(text)

foundItems = metautils.findOnlyCityData(data, cities)

print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the input list of settlements'

print 'Writing CSV file...'

#columns = ['city', 'matched_on', 'title', 'notes', 'tags', 'groups', 'format', 'geo', 'metadata_modified', 'author', 'author_email', 'maintainer', 'maintainer_email', 'id', 'url', 'isopen']
#inextras = ('metadata_original_portal', 'temporal_coverage_to', 'temporal_coverage_from', 'metadata_modified', 'metadata_created')
#intermsofuse = ('license_id')
#columns.extend(inextras)
#columns.extend(intermsofuse)

#mopIndex = columns.index('metadata_original_portal')
excludecount = 0

#Map and write the data. Still wondering how much of this can/should be pulled out to metautils
row = metautils.getBlankRow()

csvoutfile = open(sys.argv[2]+'.csv', 'wb')
datawriter = csv.DictWriter(csvoutfile, row, delimiter=',')      
datawriter.writeheader()

uniquecities = set()
datafordb = []

for foundItem in foundItems:
    item = foundItem['item']
    thecity = foundItem['city']

    row = metautils.getBlankRow()
    formatslist = []
    
    #Only add data we don't have from somewhere else
    if ('extras' in item and 'metadata_original_portal' in item['extras'] and
        not any(x in item['extras']['metadata_original_portal'] for x in excludes)):
        
        if 'resources' in item:
            for resource in item['resources']:
                if resource['format'].upper() not in formatslist:
                    formatslist.append(resource['format'].upper())
            [formattext, geo] = metautils.processListOfFormats(formatslist)
            row[u'Format'] = formattext
            row[u'geo'] = geo
        row[u'Stadt'] = theCity
        uniquecities.add(theCity)
        row[u'Dateibezeichnung'] = item['title']
        row[u'URL PARENT'] = 'https://www.govdata.de/daten/-/details/' + item['id']
        if 'notes' in item:
            row[u'Beschreibung'] = item['notes']
        if 'extras' in item and 'terms_of_use' in item['extras'] and 'license_id' in item['extras']['terms_of_use']:
            row[u'Lizenz'] = item['extras']['terms_of_use']['license_id']
        if 'maintainer' in item:
            row[u'Veröffentlichende Stelle'] = item['maintainer']
        for group in item['groups']:
            odm_cats = metautils.govDataShortToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''       

        datawriter.writerow(row)
        row[u'Stadt'] = metautils.getShortCityName(theCity)
        datafordb.append(row)
    else:
        print 'Excluding entry, in excludes list'
        excludecount += 1

csvoutfile.close()

print 'Final list of cities for db:'
for city in uniquecities:
    print city

#Write data to the DB
#Update city list
metautils.addCities(uniquecities, None)
#Remove this catalog's data
metautils.removeDataFromPortal('govdata.de')
#Add data, checking that used cities are in RLP
metautils.addDataToDB(datafordb=datafordb, originating_portal='govdata.de', checked=True, accepted=False)

print str(excludecount) + ' items excluded.'

print 'govdata.de data added to the database with checked=True but accepted=False. Remember to run \
the script for checking which entries have been accepted, which rejected, and which have not been \
considered for acceptance yet'

