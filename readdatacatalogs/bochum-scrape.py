# -*- coding: utf-8 -*-
import urllib2

from lxml import html
from lxml.etree import LxmlError

def findfilesanddata(html):
    #Start to get the data for each dataset
    tables = html.xpath('//body//table')
    #Tables with captions contain info, tables with no caption and no border contain the files
    datatables = []
    filetables = []
    for table in tables:
        if len(table.xpath('caption')) == 1:
           datatables.append(table)
           print 'Found table of data'
        elif len(table.xpath('@border')) > 0 and table.xpath('@border')[0] == '0':
           print 'Found table of files'
           filetables.append(table)
    return [datatables, filetables]

rooturl = u'http://www.bochum.de'
url = u'/opendata/datensaetze/nav/75F9RD294BOLD'

print u'Reading page of categories: ' + rooturl + url
data = html.parse(rooturl + url)

#Get the first spanned URL in each cell. There must be a way to do this all in one xpath query
cat_sites = data.xpath('//body//table//td')
cat_urls = []
for cat_site in cat_sites:
    cat_urls.append(cat_site.xpath('span[1]/a/@href')[0])
cat_urls.remove('/opendata/datensaetze/neueste-datensaetze/nav/75F9RD294BOLD')

print str(len(cat_urls))  + ' categories found'

for category_link in cat_urls:
    #Get the page
    data = html.parse(rooturl + category_link)
    #Get the category
    category = data.xpath('//body//h1/text()')[2].strip()
    #Get set of datasets
    datasets = data.xpath('//body//h2/text()')
    if 'Inhaltsverzeichnis' in datasets:
        datasets.remove('Inhaltsverzeichnis')    
    
    [datatables, filetables] = findfilesanddata(data)

    print len(datasets)
    print len(datatables)
    if len(datatables) < len(datasets):
        checkforsubpage = data.xpath('//body//div//span//a')
        for link in checkforsubpage:
            if len(link.xpath('text()')) > 0 and u'zu den Datensätzen' in link.xpath('text()')[0]:
                testurl = link.xpath('@href')[0]
                print 'Following URL ' + rooturl + testurl
                [extradatatables, extrafiletables] = findfilesanddata(html.parse(rooturl + testurl))
                print len(extradatatables)
                print len(extrafiletables)
    #TODO: Match everything together!
    continue
    filefound = False
    
    print u'Reading ' + rooturl + site
    datapage = html.parse(rooturl + site)
    
    tableheaders = datapage.xpath('//*[@id="content"]//div/table/tbody/tr/th')
    
    linkcount = 0
    
    for th in tableheaders:
        rowtitle = th.xpath('text()')[0]
        rowid = th.xpath('@id')[0]
        #Oh Moers... oh Moers... (not all of these necessarily exist, some are guesses)
        titles = ('Datei', 'Link', 'Download', 'Dateien', 'Links', 'Downloads') #Any more...?
        if any(x == rowtitle for x in titles):
            query = '//*[@id="content"]//div/table/tbody/tr/td[contains(@headers, "' + rowid + '")]//a'
            links = datapage.xpath(query)
     
            print  'Found ' + str(len(links)) + ' under ' + rowtitle
    
            for link in links:
                dataurl =  link.xpath('@href')[0]
                print dataurl
                filefound = True
                linkcount += 1
                csv_file.write(dataurl + '\n')
    
            print u'Found ' + str(linkcount) + ' files'
    
    if not filefound:
        #If no files, write out part of the path
        print 'WARNING! No files found!!! Maybe Moers found another word for the same thing... please check'
        csv_file.write(site.split('/')[-1] + '\n')
    
print 'Done.'
