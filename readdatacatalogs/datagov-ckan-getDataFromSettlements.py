import sys
import json
import codecs
import unicodecsv as csv

geoformats = ('GEOJSON', 'GML', 'GPX', 'GJSON', 'TIFF', 'SHP', 'KML', 'KMZ', 'WMS', 'WFS', 'GML2', 'GML3', 'SHAPE')

if (len(sys.argv)<4):
    print 'Usage: datagov-ckan-getDataFromSettlements inputListOfCities.csv datagovJSONDump.json outputFile.csv'
    exit()

with open(sys.argv[1], 'rb') as csvfile:
    cityreader = csv.reader(csvfile, delimiter=',')
    
    cities = []
    
    for row in cityreader:
        #First column is word to look for, second is original city name
        cities.append(row)

with open(sys.argv[2], 'rb') as jsonfile:
    text = jsonfile.read()
    data = json.loads(text)   
    
    foundItems = []
    foundCities = []
 
    for item in data:
        founditem = None
        foundcities = []
        
        if ('maintainer' in item and item['maintainer'] != None):
            for city in cities:
                if city[0] in item['maintainer']:
                    foundItem = item
                    #Note the city full name to show full basis of match
                    if city[1] not in foundcities:
                        foundcities.append(city[1])
        if ('author' in item and item['author'] != None):
            for city in cities:
                if city[0] in item['author']:
                    foundItem = item
                    if city[1] not in foundcities:
                        foundcities.append(city[1])
        if ('tags' in item and len(item['tags']) != 0):
            for city in cities:
                #TODO: convert umlauts etc to oe etc...?
                for tag in item['tags']:
                    if city[0].lower() in tag.lower():
                        foundItem = item
                        if city[1] not in foundcities:
                            foundcities.append(city[1])
        if foundItem != None:
            foundItems.append(item)
            citystring = ''
            for city in foundcities:
                citystring += '\"' + city + '\",'
            citystring = citystring[0:len(citystring)-1]
            foundCities.append(citystring)

jsonfile.close()

print 'Out of ' + str(len(data)) + ' catalog entries, ' + str(len(foundItems)) + ' appear to be related to the input list of settlements'

print 'Writing CSV file...'

columns = ['city', 'title', 'notes', 'tags', 'format', 'geo', 'metadata_modified', 'author', 'author_email', 'maintainer', 'maintainer_email', 'id', 'url', 'metadata_original_portal', 'license', 'isopen']

with open(sys.argv[3], 'wb') as csvoutfile:
    datawriter = csv.writer(csvoutfile, delimiter=',')

    row = []
    for column in columns:
        row.append(column);

    datawriter.writerow(row)

    count = -1;

    for item in foundItems:
        count += 1
        row = []
        geo = ''
        for column in columns:
            if column == 'city':
                row.append(foundCities[count])
            elif column == 'tags':
                tagstring = ''
                for tag in item['tags']:
                    tagstring += tag + ','
                #Get rid of last commas
                tagstring = tagstring[0:len(tagstring)-1]
                row.append(tagstring)
            elif column == 'url':
                row.append('https://www.govdata.de/daten/-/details/' + item['id'])
            elif column == 'format':
                formatstring = ''
                if 'resources' in item:
                    for resource in item['resources']:
                        formatstring += resource['format'] + ','
                        if resource['format'].upper() in geoformats:
                            geo = 'x'
                    #Get rid of last commas
                    formatstring = formatstring[0:len(formatstring)-1]
                row.append(formatstring)
            elif column == 'geo':
                row.append(geo)
            elif column == 'metadata_original_portal':
                if 'metadata_original_portal' in item['extras']:
                    row.append(item['extras']['metadata_original_portal'])
            else:
                row.append(item[column])
        datawriter.writerow(row)
