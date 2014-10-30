# -*- coding: utf-8 -*-
import urllib2
import urllib

import metautils
from dbsettings import settings

from lxml import html
from lxml import etree

verbose = False

def findfilesanddata(html):
    #Start to get the data for each dataset
    tables = html.xpath('//table')
    #Tables with captions contain info, tables with no caption and no border contain the files
    datatables = []
    filetables = []
    for table in tables:
        #We append the text because for some reason the objects are weird and contain data from elsewhere in the page
        if len(table.xpath('caption')) == 1:
           datatables.append(etree.tostring(table))
           if (verbose): print 'Found table of data'
        if len(table.xpath('caption')) == 0 and len(table.xpath('@border')) > 0 and table.xpath('@border')[0] == '0':
           if (verbose): print 'Found table of files'
           filetables.append(etree.tostring(table))
    return datatables, filetables
    
def get_datasets(data):
    #Get the number of datasets
    datasets = data.xpath('//body//h2/text()')
    #Maybe it's there, maybe it isn't
    if 'Inhaltsverzeichnis' in datasets:
        datasets.remove('Inhaltsverzeichnis')  
    return datasets

rooturl = u'http://www.bochum.de'
url = u'/opendata/datensaetze/nav/75F9RD294BOLD'

if (verbose): print u'Reading page of categories: ' + rooturl + url
data = html.parse(rooturl + url)

#Get the first spanned URL in each cell. There must be a way to do this all in one xpath query
cat_sites = data.xpath('//body//table//td')
cat_urls = []
for cat_site in cat_sites:
    cat_urls.append(cat_site.xpath('span[1]/a/@href')[0])
cat_urls.remove('/opendata/datensaetze/neueste-datensaetze/nav/75F9RD294BOLD')

if (verbose): print str(len(cat_urls))  + ' categories found'

allrecords = []

for category_link in cat_urls:
    #Get the page
    parser = etree.HTMLParser(encoding='utf-8')
    data = etree.parse(rooturl + category_link, parser)
    #Get the category
    category = data.xpath('//body//h1/text()')[2].strip()
    #category = urllib.unquote(category).decode('utf8')
    if (verbose): print 'Category: ' + category

    datasets = get_datasets(data)
    numdatasets = len(datasets)
    
    if (verbose): print 'There are ' + str(numdatasets) + ' datasets'
    
    #Now get the html for each one. This is painful.
    #The bit of html concerning the datasets:
    corehtml = data.xpath('//div[@id=\'ContentBlock\']')[0]
    #First try to split by the horizontal rules. This usually works, but not always
    datasetparts = etree.tostring(corehtml).split('<hr id="hr')
    if (verbose): print 'Found ' + str(len(datasetparts)) + ' datasets by splitting by hr elements with ids'
    if len(datasetparts) != numdatasets:
        if (verbose): print 'This doesn\'t match. Trying with links to TOC'
        #If there is TOC, this works. There isn\'t always one.
        datasetparts = etree.tostring(corehtml).split('nach oben')
        del datasetparts[len(datasetparts)-1]
        for index in range(0, len(datasetparts)):
            datasetparts[index] = datasetparts[index] + '</a>'   
        if (verbose): print 'Found ' + str(len(datasetparts)) + ' datasets by splitting by links to TOC'
        if len(datasetparts) != numdatasets:
            if (verbose): print 'Well, that didn\'t work either. Giving up'
            exit()
    else:
        if numdatasets>1:
            for index in range(1, len(datasetparts)):
                #That split makes for bad HTML. Make it better.
                datasetparts[index] = '<hr id="hr' + datasetparts[index]
    
    count = 1
    
    #starthtml = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="DE" lang="DE"><head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /><meta http-equiv="content-language" content="DE" /></head><body>'
    #endhtml = '</body></html>'
    
    for datasetpart in datasetparts:
        data = etree.HTML(datasetpart)
        record = metautils.getBlankRow()
        record[u'Stadt'] = 'bochum'
        record['category'] = []
        record['category'].append(category)
        
        datasets = get_datasets(data)
        record[u'Dateibezeichnung'] = datasets[0]
        
        if (verbose): print 'Parsing dataset ' + record[u'Dateibezeichnung']
        record[u'URL PARENT'] = rooturl + category_link + '#par' + str(count)
        count += 1
        datatables, filetables = findfilesanddata(data)

        if len(datatables) == 0:
            if (verbose): print 'This record contains no data... checking for link to another page...'
            checkforsubpage = data.xpath('//span//a')
            
            for link in checkforsubpage:
                if (verbose): print etree.tostring(link)
                if len(link.xpath('text()')) > 0 and u'zu den Daten' in link.xpath('text()')[0]:
                    testurl = link.xpath('@href')[0]
                    if (verbose): print 'Following/updating URL: ' + rooturl + testurl
                    record['url'] = rooturl + testurl
                    datatables, filetables = findfilesanddata(html.parse(rooturl + testurl))

        #get the data on the files, and get each link in it
        record['files'] = []
        for table in filetables:
            record['files'].extend([(rooturl + x) for x in etree.HTML(table).xpath('//a/@href')])
            
        formats = []
        for file in record['files']:
            formats.append(file.split('/')[-1].split('.')[1].upper())
        
        [formattext, geo] = metautils.processListOfFormats(formats)
        
        record[u'Format'] = formattext
        record[u'geo'] = geo

        if len(datatables) > 1:
            if (verbose): print 'ERROR: More than one data table'
            exit()
        elif len(datatables) == 0:
            if (verbose): print 'ERROR: No data table'
            exit()
            
        #parse the data table by row
        if (verbose): print 'Reading datatable...'
        rowelements = etree.HTML(datatables[0]).xpath('//tr')
        for row in rowelements:
            if len(row.xpath('td[1]/text()')) == 0: continue
            key = row.xpath('td[1]/text()')[0]
            if (verbose): print key
            if len(row.xpath('td[2]/text()')) != 0:
                val = row.xpath('td[2]/text()')[0]
            elif len(row.xpath('td[2]//a')) != 0: 
                val = row.xpath('td[2]//a/text()')[0]
            else:
                if (verbose): print 'ERROR: Missing value'
                exit()
            if (verbose): print 'Parsing key ' + key.replace(':', '') + ' with value ' + val
            if u'veröffentlicht' in key:
                record[u'Veröffentlichende Stelle'] = val
            elif u'geändert' in key:
                record[u'Zeitlicher Bezug'] = val.split(' ')[2]
            elif u'Lizenz' in key:
                record[u'Lizenz'] = metautils.long_license_to_short(val)
            #elif u'Webseite' in key:
                #record['website'] = row.xpath('td[2]//a/@href')[0] #keep, as 'original' metadata
                #if 'http://' not in record['website']:
                    #record['website'] = rooturl + record['website']
            #elif u'Kontakt' in key:
                #record['contact'] = rooturl + row.xpath('td[2]//a/@href')[0]

        allrecords.append(record)
                
#Find things in multiple categories
recordsdict = {}
for record in allrecords:
    if record[u'Dateibezeichnung'] not in recordsdict:
        recordsdict[record[u'Dateibezeichnung']] = record
    else:
        if (verbose): print record[u'Dateibezeichnung']  + ' in ' + str(record['category']) + ' is already in ' + str(recordsdict[record[u'Dateibezeichnung']]['category']) + '. Transferring category.'
        recordsdict[record[u'Dateibezeichnung'] ]['category'].extend(record['category'])

allrecords = recordsdict.values()
finalrecords = []

#Expand categories
for record in allrecords:
    odm_cats = metautils.govDataLongToODM(metautils.arraytocsv(record['category']), checkAll=True)
    if len(odm_cats) > 0:
        for cat in odm_cats:
            record[cat] = 'x'
            record[u'Noch nicht kategorisiert'] = '' 
    del record['category']
    finalrecords.append(record)
 
if (verbose): print 'Done. Adding to DB.'
#Write data to the DB
metautils.setsettings(settings)
#Add data
metautils.addDataToDB(datafordb=finalrecords, originating_portal='http://www.bochum.de/opendata', checked=True, accepted=True, remove_data=True)
