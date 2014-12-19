# -*- coding: utf-8 -*-
import urllib, urllib2, json
import unicodecsv as csv
import sys
import os

import metautils

from dbsettings import settings

def berlin_to_odm(group):
    #One dataset about WLAN locations...
    if group == 'oeffentlich':
        return [u'Infrastruktur, Bauen und Wohnen']
    if group in (u'demographie', u'jugend'):
        return [u'Bevölkerung']
    if group == u'bildung':
        return [u'Bildung und Wissenschaft']
    if group == u'gesundheit':
        return [u'Gesundheit']
    if group in (u'transport', u'verkehr'):
        return [u'Transport und Verkehr']
    if group == u'wahl':
        return [u'Politik und Wahlen']
    if group == u'justiz':
        return [u'Gesetze und Justiz']
    if group == u'geo':
        return [u'Infrastruktur, Bauen und Wohnen', u'Geographie, Geologie und Geobasisdaten']
    if group in (u'wohnen', u'verentsorgung'):
        return [u'Infrastruktur, Bauen und Wohnen']
    if group in (u'kultur', u'tourismus', u'erholung'):
        return [u'Kultur, Freizeit, Sport, Tourismus']
    if group == u'sozial':
        return [u'Soziales']
    if group == u'umwelt':
        return [u'Umwelt und Klima']
    if group == u'verbraucher':
        return [u'Verbraucherschutz']
    if group in (u'verwaltung', u'sicherheit'):
        return [u'Öffentliche Verwaltung, Haushalt und Steuern']
    if group in (u'wirtschaft', u'arbeit'):
        return [u'Wirtschaft und Arbeit']
    if group in (u'sonstiges', u'protokolle'):
        return [u'Sonstiges']
    else:
        print 'WARNING: Found no category or categories for ' + group
        return []

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
elif cityname == "berlin":
    url = "http://datenregister.berlin.de"
    apikey = os.environ['BERLINCKANAPIKEY']
else:
    print 'First argument must be an city; unsupported city'
    exit()

if cityname in ("hamburg", "koeln", "bonn"):
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
    if cityname == "berlin":
        #Berlin is special, it is CKAN 1.8 with V3 API in beta. We have to *post* with an empty dict. And we have to authenticate!
        request = urllib2.Request(url +'/api/3/action/current_package_list_with_resources')
        request.add_header('Authorization', apikey)
        jsonurl = urllib2.urlopen(request, "{}")
    else:
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
        if package['type'] != 'dataset' or 'forward-reference' in package['title']:
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
    if cityname in ('hamburg', 'koeln', 'frankfurt', 'aachen', 'berlin'):
        if cityname in ('hamburg', 'frankfurt', 'aachen'):
            licensekey = 'license_id'
            vstellekey = 'author'
            catskey = 'groups'
            catssubkey = 'title'
        elif cityname in ('koeln', 'berlin'):
            licensekey = 'license_title'
            vstellekey = 'maintainer' 
            if cityname == 'koeln':
                catskey = 'tags'
            elif cityname == 'berlin':
                catskey = 'groups'
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
            #if not already short, try to convert
            if metautils.isopen(row[u'Lizenz'], quiet=True) is None:
                row[u'Lizenz'] = metautils.long_license_to_short(row[u'Lizenz'])
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
            if cityname != 'berlin':
                odm_cats = metautils.govDataLongToODM(group)
            else:
                odm_cats = berlin_to_odm(group)
            metautils.setcats(row, odm_cats)    
            if row['Noch nicht kategorisiert'] == 'x':
                print 'WARNING! A data catalog entry\'s group is not successfully categorized, this shouldn\'t be possible and can lead to an inconsistency in the categorization'
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
metautils.addDataToDB(datafordb=datafordb, originating_portal=portalname, checked=True, accepted=True, remove_data=True)



