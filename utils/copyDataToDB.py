# -*- coding: utf-8 -*-
#Download the index file and all cities
import urllib
import unicodecsv as csv
import os
import psycopg2
import sys

import metautils

from dbsettings import settings

generalvalidsources = ('m', 'd', 'c', 'g', 'b')

#Change if not importing from crawled data and data does not have a 'Quelle' column
unknownsource = 'c'

def reformatdata(cityname, accepted, overridevalidsources, multiCity = False):    
    dictsdata = dict()
    if overridevalidsources is not None:
        validsources = overridevalidsources
    else:
        validsources = generalvalidsources

    with open(cityname + '.csv', 'rb') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            if not multiCity:
                row['Stadt_URL'] = cityname + '.de'
                
            row = metautils.convert_crawl_row(row, unknownsource)
            
            source = row['Quelle'].strip()
            if source not in generalvalidsources:
                print 'Error: data has missing or unrecognised source(s): ' + source
                exit()
            elif source not in validsources:
                print 'Ignoring row with source: ' + source
                continue
            else:
                if source not in dictsdata:
                    dictsdata[source] = []
                dictsdata[source].append(row)
            
    takenrows = dict()

    for source in validsources:
        if source in dictsdata:
            print 'Processing source: ' + source
            for row in dictsdata[source]:
                theurl = ''
                
                #URL of file found. Will be blank for data catalog.
                url = row['URL Datei'].strip()
                #URL of parent. Will be blank for Google/Bing
                parent = row['URL PARENT'].strip()           
                print 'Processing entry with parent [' + parent +'] and url [' + url + ']'

                #If no parent, take file
                if url != '' and parent == '':
                    theurl = url
                #If no file URL or if parent isn't blank, take parent (parents are always favoured)
                else:
                    theurl = parent

                #URLs must be unique
                #We assume that all catalog and manual entries are unique
                if (theurl not in takenrows) or source == 'd' or source == 'm':
                    print 'Adding ' + theurl 
                    row['URL'] = theurl
                    #When we have parent and URL (crawler), store both
                    if theurl == parent and url != '':
                        row['filenames'] = [url]
                    else:
                        row['filenames'] = []
                    takenrows[theurl] = row
                else:
                    print 'Not adding: url already there, transferring filename, categories and geo'
                    if url != '' and url != theurl: #Prevent storing url as filename when e.g. Google and Bing find the same result
                        takenrows[theurl]['filenames'].append(url)
                    for key in row:
                        if row[key].strip().lower() == 'x':
                             takenrows[theurl][key] = 'x'
  
    dataForDB = []
    checked = True #All of this data is 'open data'
    
    for row in takenrows.values():   
        dataForDB.append(row)
        
    metautils.addCrawlDataToDB(datafordb=dataForDB, accepted=accepted, checked=checked)

metautils.setsettings(settings)

if len(sys.argv) > 3:
    print 'Processing sheet with key ' + sys.argv[1] + ' and gid ' + sys.argv[2]
    durl = "https://docs.google.com/spreadsheets/d/" + sys.argv[1] + "/export?gid=" + sys.argv[2] + "&format=csv"
    print "Downloading data using url " + durl + "..."
    urllib.urlretrieve (durl, "tempsheet.csv");
    if sys.argv[3] == 'accepted':
        accepted = True
    elif sys.argv[3] == 'rejected':
        accepted = False
    else:
        print 'Please state a third argument accepted|rejected. Remember that data of existing URLs will NOT be overwritten, and that the value may be overwritten by DB checks for duplicates etc.'
    reformatdata('tempsheet', accepted, None, multiCity = True)
                  
elif len(sys.argv) == 1:
    print 'Importing all data specified in index'
    kurznamecolumn = 'kurzname'
    gidcolumn = 'GID in Datenerfassung'

    indexkey = os.environ['INDEXKEY']
    erfassungkey = os.environ['ERFASSUNGKEY']

    iurl = "https://docs.google.com/spreadsheets/d/" + indexkey + "/export?gid=0&format=csv"
    print "Downloading index of cities to index.csv using url " + iurl + "..."
    urllib.urlretrieve (iurl, "index.csv");

    print "Parsing list of cities to download each file..."

    with open('index.csv', 'rb') as csvfile:
        cityreader = csv.DictReader(csvfile, delimiter=',')
        indexfields = cityreader.fieldnames
    
        #For each city that has a short name, download its data from the other sheet, if we have the gid
        for row in cityreader:
            if row[kurznamecolumn] != "":
              if row[gidcolumn] != "":
                  durl = "https://docs.google.com/spreadsheets/d/" + erfassungkey + "/export?gid=" + row[gidcolumn] + "&format=csv"
                  print "Downloading data for " + row[kurznamecolumn] + " using url " + durl + "..."
                  urllib.urlretrieve (durl, row[kurznamecolumn] + ".csv");
                  reformatdata(row[kurznamecolumn], True, None)
              else:
                  print "No gid for this city, please check spreadsheet"
else:
    print 'Either use three arguments, GSheets key and gid for importing a sheet and \'accepted\' or \'rejected\', or no arguments, setting the environment variables INDEXKEY and ERFASSUNGSKEY appropriately'
 


