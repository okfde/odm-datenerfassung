# -*- coding: utf-8 -*-
import urllib, urllib2, json
import unicodecsv as csv
import sys

import metautils

from dbsettings import settings

url = ""
cityname = sys.argv[1]

#TODO: get from DB
if cityname == "koeln":
    url = "http://offenedaten-koeln.de"
elif cityname == "bonn":
    url = "http://opendata.bonn.de"
elif cityname == "hamburg":
    url = "http://suche.transparenz.hamburg.de"
elif cityname == "frankfurt":
    url = "http://www.offenedaten.frankfurt.de"
elif cityname == "aachen":
    url = "http://daten.aachen.de"
else:
    print 'First argument must be an city; unsupported city'
    exit()

if cityname == "hamburg" or cityname == "koeln" or cityname == 'bonn':
    if cityname == 'bonn':
        jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
    else:
        jsonurl = urllib.urlopen(url + "/api/3/action/package_list")
    if len(sys.argv) > 2:
        print 'Loading from file...'
        jsonurl = open(sys.argv[2], 'rb')
    listpackages = json.loads(jsonurl.read())
    if len(sys.argv) < 3:
        if cityname != 'bonn':
            listpackages = listpackages['result']
    if len(sys.argv) > 2:
        jsonurl.close()
    groups = []
    if len(sys.argv) < 3:
        print 'INFO: the names that follow have had special characters removed'
        for item in listpackages:
            if cityname == 'bonn':
                urltoread = item['webService']
            else:
                urltoread = url + "/api/3/action/package_show?id=" + item
            print 'Downloading ' + metautils.findLcGermanCharsAndReplace(urltoread)
            trycount = 0
            try:
                req = urllib2.Request(urltoread.encode('utf8'))
                resp = urllib2.urlopen(req)
                urldata = resp.read()
            except IOError:
                if trycount == 100:
                    print 'Download failed 100 times, giving up...'
                    exit()
                print 'Something went wrong, retrying...'
                trycount += 1
            pdata = json.loads(urldata)
            if cityname != 'bonn':
                if 'success' in pdata and pdata['success']:
                    if cityname == "koeln":
                        groups.append(pdata['result'][0])
                    else:
                        groups.append(pdata['result'])
                else:
                    print 'WARNING: No result - access denied?\n' + metautils.findLcGermanCharsAndReplace(item)
            else:
                #Now put all the missing/better data from the overview JSON into the DKAN JSON :'(
                for better in ['accessURL', 'modified', 'license', 'keyword']:
                    pdata[better] = item[better]
                groups.append(pdata)
    else:
        groups = listpackages
else:
    print 'Downloading ' + url + "/api/3/action/current_package_list_with_resources..."
    jsonurl = urllib.urlopen(url + "/api/3/action/current_package_list_with_resources")
    groups = json.loads(jsonurl.read())
    groups = groups['result']

#It takes a long time to gather the Hamburg data... save it if we downloaded it
#For Köln and Bonn the data is better than the single API call
if cityname in ['hamburg', 'koeln', 'bonn'] and cityname != "hamburg" or (cityname == 'hamburg' and len(sys.argv) < 3):
    with open('../metadata/' + cityname + '/catalog.json', 'wb') as outfile:
        json.dump(groups, outfile)

datafordb = []

for package in groups:
    if cityname == 'hamburg':
        #Only take 'open data'
        if package['type'] != 'dataset':
            continue
    resources = []
    formats = set()
    files = []
    #Key for the file link in the resource
    urlkeys = ['url']
    formatkey = 'format'
    
    if cityname == "bonn":
        urlkeys = ['file_url', 'link_to_api', 'url']
        if 'file_link' in package and package['file_link']!= None and package['file_link'] != '':
            print 'WARNING! file_link was actually used! Here it is: ' + package['file_link']
    if ('resources' in package):
        resources = package['resources']

    for file in resources:
        for urlkey in urlkeys:
            if (file[urlkey] not in [None, '']):
                if '://' not in file[urlkey]:
                    files.append(url + file[urlkey])
                else:
                    files.append(file[urlkey])
                break
        if formatkey in file and file[formatkey] not in [None, '']:
            format = file[formatkey]
            formats.add(format.upper())

    row = metautils.getBlankRow()
    
    row[u'Format'] = metautils.arraytocsv(formats)
    row[u'Stadt'] = cityname
    row[u'Dateibezeichnung'] = package['title']
    row[u'files'] = files
    
    if cityname == 'hamburg' or cityname == 'koeln' or cityname == 'frankfurt' or cityname == 'aachen':
        if cityname == 'hamburg' or cityname == 'frankfurt' or cityname == 'aachen':
            licensekey = 'license_id'
            vstellekey = 'author'
            catskey = 'groups'
            catssubkey = 'title'
        if cityname == 'koeln':
            licensekey = 'license_title'
            vstellekey = 'maintainer' 
            catskey = 'tags'
            catssubkey = 'name'
        #Generate URL for the catalog page
        row[u'URL PARENT'] = url + '/dataset/' + package['name']
        if 'notes' in package and package['notes'] != None:
            row[u'Beschreibung'] = package['notes']
            if cityname == 'koeln':
                row[u'Beschreibung'] = metautils.unrenderhtml(row[u'Beschreibung'])
        else:
            row[u'Beschreibung'] = ''
        row[u'Zeitlicher Bezug'] = ''
        if licensekey in package and package[licensekey] != None:
            row[u'Lizenz'] = package[licensekey]
        else:
            row[u'Lizenz'] = 'nicht bekannt'
        if vstellekey in package and package[vstellekey] != None:
            row[u'Veröffentlichende Stelle'] = package[vstellekey]
        else:
            row[u'Veröffentlichende Stelle'] = ''
            if 'extras' in package:
                print 'WARNING: No author/maintainer/publisher, checking extras'
                for extra in package['extras']:
                    if extra['key'] == 'contacts':
                        print 'WARNING: No author, but amazingly there is possibly data in the contacts: ' + extra['value']
        for group in metautils.setofvaluesasarray(package[catskey], catssubkey):
            odm_cats = metautils.govDataLongToODM(group)
            metautils.setcats(row, odm_cats)    
    #Bonn is just different enough to do it separately. TODO: Consider combining into above.
    elif cityname == 'bonn':
        row[u'URL PARENT'] = package['accessURL']
        row[u'Beschreibung'] = package['description']
        for timeattempt in ['temporal_coverage', 'granularity', 'modified']:
            if timeattempt in package and package[timeattempt] not in [None, '']:
                row[u'Zeitlicher Bezug'] = package[timeattempt]
                break
        row[u'Lizenz'] = metautils.long_license_to_short(package['license'])
        row[u'Veröffentlichende Stelle'] = package['publisher']
        #Commas in categories cannot be distinguished from separation of categories :(
        odm_cats = metautils.govDataLongToODM(package['keyword'], checkAll=True)
        metautils.setcats(row, odm_cats)
    #Take a copy of the metadata    
    row['metadata'] = package
    datafordb.append(row)

print 'Adding ' + str(len(datafordb)) + ' datasets'

#Write data to the DB
metautils.setsettings(settings)
#Remove this catalog's data
portalname = metautils.getCityOpenDataPortal(cityname)
metautils.removeDataFromPortal(portalname)
#Add data
metautils.addDataToDB(datafordb=datafordb, originating_portal=portalname, checked=True, accepted=True)

