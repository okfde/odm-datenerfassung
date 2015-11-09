# -*- coding: utf-8 -*-
import urllib, json
import unicodecsv as csv
import sys

import metautils

from dbsettings import settings

def mapData(data, nocity=False):
    returndata = []
    uniquecities = set()
    
    for result in data:

        files = []
        resources = []

        if cityimport == 'rlp':
            package = result['item']
        else:
            package = result
        
        row = metautils.getBlankRow()

        if ('res_url' in package):
            resources = package['res_url']

        for file in resources:
            files.append(file)
        
        row[u'files'] = files

        if cityimport == 'rlp':
            if not nocity:
                row[u'Stadt'] = metautils.getShortCityName(result['city']['originalname'])
                uniquecities.add(result['city']['originalname'])
            else:
                row[u'Stadt'] = 'rheinlandpfalz'
            row[u'URL PARENT'] = 'http://www.daten.rlp.de/dataset/' + package['id']
        elif cityimport == 'rostock':
            row[u'Stadt'] = 'rostock'
            row[u'URL PARENT'] = 'http://www.opendata-hro.de/dataset/' + package['id']
        
        if ('res_format' in package):
            [formattext, geo] = metautils.processListOfFormats(package['res_format'])
            row[u'Format'] = formattext
            row[u'geo'] = geo
        
        row[u'Dateibezeichnung'] = package['title']
        if 'notes' in package:
            row[u'Beschreibung'] = package['notes']
        if 'license_id' in package:
            row[u'Lizenz'] = package['license_id']
        if 'maintainer' in package:
            row[u'Veröffentlichende Stelle'] = package['maintainer']
        
        if 'groups' in package:
            for group in package['groups']:
                odm_cats = metautils.govDataShortToODM(group)
                if len(odm_cats) > 0:
                    for cat in odm_cats:
                        row[cat] = 'x'
                    row[u'Noch nicht kategorisiert'] = ''       

        returndata.append(row)
    
    return [returndata, uniquecities]
    
cityimport = sys.argv[1]

if cityimport == 'rostock':
    jsonurl = urllib.urlopen("http://www.opendata-hro.de/api/2/search/dataset?q=&limit=1000&all_fields=1")
elif cityimport == 'rlp':
    #N.B. max limit is 1000
    limit = 1000
    urlbase = "http://www.daten.rlp.de/api/2/search/dataset?q=&limit=" + str(limit) + "&all_fields=1"
    jsonurl = urllib.urlopen(urlbase)
elif cityimport == 'bayern':
    urlbase = "https://opendata.bayern.de/api/2/search/dataset?q=&limit=1000&all_fields=1"
    jsonurl = urllib.urlopen(urlbase)
else:
    print 'Error: \'rostock\' or \'rlp\' must be specified as the first argument'
    exit()

data = json.loads(jsonurl.read())

if cityimport == 'rlp':
    #Get the rest of the data
    gotdata = data
    while len(gotdata['results']) > 0:
        gotdata = json.loads(urllib.urlopen(urlbase + "&offset=" + str(limit)).read())
        data['results'].extend(gotdata['results'])
        limit += 1000
    #The average user doen't want to write a script to get all the data. Create a file:
    with open('../metadata/rheinlandpfalz/catalog.json', 'wb') as outfile:
        json.dump(data['results'], outfile)
    #Separate out communal data
    allcities = metautils.getCities()
    #First take the Verbandsgemeinde
    cities = metautils.getCities(alternativeFile='verbandsgemeinderlp.csv')
    #Then all settlements in RLP
    cities.extend(metautils.filterCitiesByLand(allcities, 'Rheinland-Pfalz'))
    beforefilter = len(data['results'])
    [data, notcitydata] = metautils.findOnlyCityData(data['results'], cities)
    afterfilter = len(data)
    print 'Of the total ' + str(beforefilter) + ' records, ' + str(afterfilter) + ' appear to be related to a city'
    print 'The rest (' + str(len(notcitydata)) + ') will be assigned to Rheinland-Pfalz as a Land'
else:
    data = data['results']

#Map and write the data. Still wondering how much of this can/should be pulled out to metautils
row = metautils.getBlankRow()
datafordb = []

[returnData, uniquecities] = mapData(data)
datafordb.extend(returnData)
if cityimport == 'rlp':
    [returnData, ignoreuniquecities] = mapData(notcitydata, nocity=True)
    datafordb.extend(returnData)

#Write data to the DB
metautils.setsettings(settings)
if cityimport == 'rlp':
    #Update city list
    metautils.addCities(uniquecities, 'Rheinland-Pfalz')
    #Remove this catalog's data
    metautils.removeDataFromPortal('daten.rlp.de')
    #Add data, checking that used cities are in RLP
    metautils.addDataToDB(datafordb=datafordb, bundesland='Rheinland-Pfalz', originating_portal='daten.rlp.de', checked=True, accepted=True)
elif cityimport == 'rostock':
    #Remove this catalog's data
    metautils.removeDataFromPortal('opendata-hro.de')
    #Add data, checking that used cities are in RLP
    metautils.addDataToDB(datafordb=datafordb, originating_portal='opendata-hro.de', checked=True, accepted=True, remove_data=True)
else:
    print datafordb