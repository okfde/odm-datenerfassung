# -*- coding: utf-8 -*-
import sys
import json
import codecs
import unicodecsv as csv

import metautils

actualcategories = []

if (len(sys.argv)<2):
    print 'Usage: datagov-ckan-getDataFromSettlements datagovJSONDump.json [list,of,portals,to,exclude]'
    exit()

excludes = []

if (len(sys.argv)>2):
    excludes = sys.argv[2].replace(' ', '').split(',')
    print 'Excluding following portals:'
    for portal in excludes:
        print portal
        
cities = metautils.getCities()

with open(sys.argv[1], 'rb') as jsonfile:
    text = jsonfile.read()
    alldata = json.loads(text)

#Only add data we don't have from somewhere else
data = []
excludecount = 0
uniqueportals = set()
for item in alldata:
    if ('extras' in item and 'metadata_original_portal' in item['extras']):
        if not any(x in item['extras']['metadata_original_portal'] for x in excludes):
            data.append(item)
            uniqueportals.add(item['extras']['metadata_original_portal'])
        else:
            excludecount += 1
    else:
        data.append(item)
print str(excludecount) + ' items excluded.'
print 'List of remaining portals:'
print uniqueportals

foundItems = metautils.findOnlyCityData(data, cities)

print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the input list of settlements'

#columns = ['city', 'matched_on', 'title', 'notes', 'tags', 'groups', 'format', 'geo', 'metadata_modified', 'author', 'author_email', 'maintainer', 'maintainer_email', 'id', 'url', 'isopen']
#inextras = ('metadata_original_portal', 'temporal_coverage_to', 'temporal_coverage_from', 'metadata_modified', 'metadata_created')
#intermsofuse = ('license_id')
#columns.extend(inextras)
#columns.extend(intermsofuse)

#mopIndex = columns.index('metadata_original_portal')

#Map and write the data. Still wondering how much of this can/should be pulled out to metautils
row = metautils.getBlankRow()

uniquecities = set()
uniqueportals = set()
datafordb = []

#Don't use cities that have their own open data catalogs (regardless of originating portal field)
excludecities = metautils.getCitiesWithOpenDataPortals() 

print 'Excluding cities with portals:'
print excludecities

excludecount = 0

for foundItem in foundItems:
    thecity = metautils.getShortCityName(foundItem['city']['shortname'])
    if thecity not in excludecities:
        item = foundItem['item']
        row = metautils.getBlankRow()
        formatslist = []
  
        if 'resources' in item:
            for resource in item['resources']:
                if resource['format'].upper() not in formatslist:
                    formatslist.append(resource['format'].upper())
            [formattext, geo] = metautils.processListOfFormats(formatslist)
            row[u'Format'] = formattext
            row[u'geo'] = geo
        row[u'Stadt'] = thecity
        uniquecities.add(foundItem['city']['originalname'])
        row[u'Dateibezeichnung'] = item['title']
        row[u'URL PARENT'] = 'https://www.govdata.de/daten/-/details/' + item['id']
        if 'notes' in item:
            row[u'Beschreibung'] = item['notes']
        if 'extras' in item and 'terms_of_use' in item['extras'] and 'license_id' in item['extras']['terms_of_use']:
            #Really?
            if type(item['extras']['terms_of_use']) != dict:
                row[u'Lizenz'] = json.loads(item['extras']['terms_of_use'])['license_id']
            else:
                row[u'Lizenz'] = item['extras']['terms_of_use']['license_id']
        if 'maintainer' in item and item['maintainer'] != None:
            row[u'Veröffentlichende Stelle'] = item['maintainer']
        for group in item['groups']:
            odm_cats = metautils.govDataShortToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''       

        datafordb.append(row) 
    else:
            excludecount += 1

print str(excludecount) + ' items excluded.'       

print 'Final list of cities for db:'
for city in uniquecities:
    print city

#Write data to the DB
#Update city list
metautils.addCities(uniquecities, None)
#Remove this catalog's data
metautils.removeDataFromPortal('govdata.de')
#Add data, checking that used cities are in RLP
metautils.addDataToDB(datafordb=datafordb, originating_portal='govdata.de', checked=True, accepted=True)


