# -*- coding: utf-8 -*-
import urllib, json
import unicodecsv as csv
import sys

import metautils

url = ""
cityname = sys.argv[1]

if cityname == "koeln":
    url = "http://offenedaten-koeln.de"
elif cityname == "bonn":
    url = "http://opendata.bonn.de"
elif cityname == "hamburg":
    url = "http://suche.transparenz.hamburg.de"
else:
    print 'First argument must be an city; unsupported city'
    exit()

if cityname == "hamburg":
    jsonurl = urllib.urlopen(url + "/api/3/action/package_list")
    if len(sys.argv) > 3:
        print 'Loading from file...'
        jsonurl = open(sys.argv[3], 'rb')
    listpackages = json.loads(jsonurl.read())
    if len(sys.argv) < 4:
        listpackages = listpackages['result']
    if len(sys.argv) > 3:
        jsonurl.close()
    groups = []
    if len(sys.argv) < 4:
        for item in listpackages:
            print 'Downloading dataset ' + item
            purl = urllib.urlopen(url + "/api/3/action/package_show?id=" + item)
            pdata = json.loads(purl.read())
            if 'result' in pdata:
                groups.append(pdata['result'])
            else:
                print 'WARNING: No result - access denied?\n' + purl
    else:
        groups = listpackages
else:
    jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
    groups = json.loads(jsonurl.read())

#It takes a long time to gather the Hamburg data... save it if we downloaded it
if cityname == "hamburg" and len(sys.argv) < 4:
    with open('../metadata/hamburg/catalognew.json', 'wb') as outfile:
        json.dump(groups, outfile)

row = metautils.getBlankRow()

csvoutfile = open(sys.argv[2]+'.csv', 'wb')
datawriter = csv.DictWriter(csvoutfile, row, delimiter=',')
csv_files = open(sys.argv[2]+'.files.csv', 'wb')
csv_files_writer = csv.writer(csv_files, delimiter=',')
            
datawriter.writeheader()

for package in groups:
    filefound = False
    
    resources = []
    formatarray = []
    urlkey = 'url'
    formatkey = 'format'
    
    if cityname != "hamburg":
        fulljsonurl = urllib.urlopen(package['webService'])
        fulldata = json.loads(fulljsonurl.read())
        urlkey = 'file_url'
        if ('resources' in fulldata):
            resources = fulldata['resources']
    else:
        if ('resources' in package):
            resources = package['resources']
    
    #TODO: Formats for dkan
    for file in resources:
        if (file[urlkey] != ''):
            filefound = True
            filerow = []
            filerow.append(file[urlkey])
            csv_files_writer.writerow(filerow)
            if cityname == "hamburg":
                format = file[formatkey]
                if format not in formatarray:
                    formatarray.append(format)
    
    if not filefound:
        filerow = []
        #Fake file for analysis
        filerow.append('/' + package['identifier'])
        csv_files_writer.writerow(filerow)
    
    row = metautils.getBlankRow()
    
    row[u'Format'] = metautils.arraytocsv(formatarray)
    row[u'Stadt'] = cityname + '.de'
    row[u'Dateibezeichnung'] = package['title']
    
    if cityname == 'hamburg':
        row[u'URL PARENT'] = None
        if 'url' in package:
            row[u'URL PARENT'] = package['url']
        if row[u'URL PARENT'] == None:
            row[u'URL PARENT'] = url + '/dataset/' + package['name']
        if 'notes' in package:
            row[u'Beschreibung'] = package['notes']
        else:
            row[u'Beschreibung'] = ''
        row[u'Zeitlicher Bezug'] = ''
        row[u'Lizenz'] = package['license_id']
        row[u'Veröffentlichende Stelle'] = package['author']
        for group in metautils.setofvaluesasarray(package['groups'], 'title'):
            odm_cats = metautils.govDataLongToODM(group)
            if len(odm_cats) > 0:
                for cat in odm_cats:
                    row[cat] = 'x'
                row[u'Noch nicht kategorisiert'] = ''       
    else:
        row[u'URL PARENT'] = package['accessURL']
        row[u'Beschreibung'] = package['description']
        row[u'Zeitlicher Bezug'] = package['granularity']
        row[u'Lizenz'] = package['license']
        row[u'Veröffentlichende Stelle'] = package['publisher']

    datawriter.writerow(row)

csvoutfile.close()
csv_files.close()
