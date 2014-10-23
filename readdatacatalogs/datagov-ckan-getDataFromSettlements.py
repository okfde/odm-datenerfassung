# -*- coding: utf-8 -*-
import sys
import json
import codecs
import unicodecsv as csv

import metautils

from dbsettings import settings

actualcategories = []

if (len(sys.argv)<2):
    print 'Usage: datagov-ckan-getDataFromSettlements all|portal datagovJSONDump.json [list,of,portals,to,exclude]'
    exit()

with open(sys.argv[2], 'rb') as jsonfile:
    text = jsonfile.read()
    alldata = json.loads(text)

if sys.argv[1] == 'all':
    portal = 'govdata.de'
    excludes = []

    if (len(sys.argv)>3):
        excludes = sys.argv[3].replace(' ', '').split(',')
        print 'Excluding following portals:'
        for portal in excludes:
            print portal
        
    cities = metautils.getCities()

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

else:
    portal = sys.argv[1]
    if 'http://' in portal:
        portal = portal[7:len(portal)]
    data = alldata
    #Search for the input term, it can include http://
    foundItems = metautils.findOnlyPortalData(data, sys.argv[1])
    print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the portal specified'


#Map and write the data. Still wondering how much of this can/should be pulled out to metautils
datafordb = []
row = metautils.getBlankRow()

uniquecities = set()

#Write data to the DB
metautils.setsettings(settings)

if sys.argv[1] == 'all':
    #Don't use cities that have their own open data catalogs (regardless of originating portal field)
    excludecities = metautils.getCitiesWithOpenDataPortals() 
    print 'Excluding cities with portals:'
    print excludecities
else:
    excludecities = []

excludecount = 0

for foundItem in foundItems:
    thecity = metautils.getShortCityName(foundItem['city']['shortname'])
    if thecity not in excludecities:
        item = foundItem['item']
        row = metautils.getBlankRow()
        formatslist = []
  
        if 'resources' in item:
            for resource in item['resources']:
                row['files'].append(resource['url'])
                if resource['format'].upper() not in formatslist:
                    formatslist.append(resource['format'].upper())
            [formattext, geo] = metautils.processListOfFormats(formatslist)
            row[u'Format'] = formattext
            row[u'geo'] = geo
        row[u'Stadt'] = thecity
        uniquecities.add(foundItem['city']['originalname'])
        row[u'Dateibezeichnung'] = item['title']
        if sys.argv[1] == 'all' or 'url' not in item or item['url'] == '':
            row[u'URL PARENT'] = 'https://www.govdata.de/daten/-/details/' + item['id']
        else:
            row[u'URL PARENT'] = item['url']
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
        row['metadata'] = item
        datafordb.append(row) 
    else:
        excludecount += 1

if sys.argv[1] == 'all':
    print str(excludecount) + ' items excluded.'

#Update city list
metautils.addCities(uniquecities, None)
#Remove this catalog's data
metautils.removeDataFromPortal(portal)
#Add data
metautils.addDataToDB(datafordb=datafordb, originating_portal=portal, checked=True, accepted=True)


