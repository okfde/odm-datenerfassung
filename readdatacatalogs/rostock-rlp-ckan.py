# -*- coding: utf-8 -*-
import urllib, json
import unicodecsv as csv
import sys

import metautils

if (len(sys.argv)<3):
    print 'Usage: rostock-rlp-ckan rostock|rlp outputFilePrefix'
    exit()

columns = ['title', 'name', 'notes', 'id', 'url', 'author', 'author_email', 'maintainer', 'maintainer_email', 'metadata_created', 'metadata_modified', 'capacity', 'state',  'version', 'license_id']

if sys.argv[1] == 'rostock':
    jsonurl = urllib.urlopen("http://www.opendata-hro.de/api/2/search/dataset?q=&limit=1000&all_fields=1")
elif sys.argv[1] == 'rlp':
    jsonurl = urllib.urlopen("http://www.daten.rlp.de/api/2/search/dataset?q=&limit=4000&all_fields=1")
else:
    print 'Error: \'rostock\' or \'rlp\' must be specified as the first argument'
    exit()

data = json.loads(jsonurl.read())

if sys.argv[1] == 'rostock':
    #The old way - dump data
    metautils.writerawresults(data['results'], columns, 'http://www.opendata-hro.de/dataset/', sys.argv[2])
elif sys.argv[1] == 'rlp':
    #Only deal with communal data
    allcities = metautils.getCities()
    cities = metautils.filterCitiesByLand(allcities, 'Rheinland-Pfalz')
    beforefilter = len(data['results'])
    data = metautils.findOnlyCityData(data['results'], cities)
    afterfilter = len(data)
    
    print 'Of the total ' + str(beforefilter) + ' records, ' + str(afterfilter) + ' appear to be related to a city'
    
    #Map and write the data. Still wondering how much of this can/should be pulled out to metautils
    row = metautils.getBlankRow()

    csvoutfile = open(sys.argv[2]+'.csv', 'wb')
    datawriter = csv.DictWriter(csvoutfile, row, delimiter=',')      
    datawriter.writeheader()
    
    uniquecities = []

    for result in data:
        package = result['item']
        filefound = False
    
        row = metautils.getBlankRow()
        
        if ('res_format' in package):
            [formattext, geo] = metautils.processListOfFormats(package['res_format'])
            row[u'Format'] = formattext
        row[u'Stadt'] = result['city']['originalname']
        if result['city']['originalname'] not in uniquecities:
            uniquecities.append(result['city']['originalname'])
        row[u'Dateibezeichnung'] = package['title']
        row[u'URL PARENT'] = 'http://www.daten.rlp.de/dataset/' + package['id']
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

        datawriter.writerow(row)

    csvoutfile.close()
    
    #Write data to the DB (in progress)
    #Update city list
    metautils.addCities(uniquecities, 'Rheinland-Pfalz')
    #CHECK WHETHER FOUND CITY IS IN RLP!!!
