# -*- coding: utf-8 -*-
import urllib, json
import unicodecsv as csv
import sys

import metautils

from dbsettings import settings

cityimport = sys.argv[1]

if cityimport == 'rostock':
    jsonurl = urllib.urlopen("http://www.opendata-hro.de/api/2/search/dataset?q=&limit=1000&all_fields=1")
elif cityimport == 'rlp':
    jsonurl = urllib.urlopen("http://www.daten.rlp.de/api/2/search/dataset?q=&limit=4000&all_fields=1")
else:
    print 'Error: \'rostock\' or \'rlp\' must be specified as the first argument'
    exit()

data = json.loads(jsonurl.read())

if cityimport == 'rlp':
    #Only deal with communal data
    allcities = metautils.getCities()
    #First take the Verbandsgemeinde
    cities = metautils.getCities(alternativeFile='verbandsgemeinderlp.csv')
    #Then all settlements in RLP
    cities.extend(metautils.filterCitiesByLand(allcities, 'Rheinland-Pfalz'))
    beforefilter = len(data['results'])
    data = metautils.findOnlyCityData(data['results'], cities)
    afterfilter = len(data)
    print 'Of the total ' + str(beforefilter) + ' records, ' + str(afterfilter) + ' appear to be related to a city'
elif cityimport == 'rostock':
    data = data['results']

#Map and write the data. Still wondering how much of this can/should be pulled out to metautils
row = metautils.getBlankRow()
uniquecities = set()
datafordb = []

for result in data:

    files = []
    resources = []

    if cityimport == 'rlp':
        package = result['item']
    elif cityimport == 'rostock':
        package = result
        
    row = metautils.getBlankRow()

    if ('res_url' in package):
        resources = package['res_url']

    for file in resources:
        files.append(file)
        
    row[u'files'] = files

    if cityimport == 'rlp':
        row[u'Stadt'] = metautils.getShortCityName(result['city']['originalname'])
        uniquecities.add(result['city']['originalname'])
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
        
    for group in package['groups']:
        odm_cats = metautils.govDataShortToODM(group)
        if len(odm_cats) > 0:
            for cat in odm_cats:
                row[cat] = 'x'
            row[u'Noch nicht kategorisiert'] = ''       

    datafordb.append(row)

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
    metautils.addDataToDB(datafordb=datafordb, originating_portal='opendata-hro.de', checked=True, accepted=True)
