import unicodecsv
import urllib2
import sys
import codecs

from lxml import html
from lxml.etree import LxmlError

rooturl = u'http://www.moers.de'
url = u'/C1257221003C7526/html/063BA200D9B9F899C1257B2D003292FE?opendocument&c1=1000'

#Output the list of files for analysis
csv_file = codecs.open('files.csv', 'w', 'utf-8')

print u'Reading page of all datasets: ' + rooturl + url
data = html.parse(rooturl + url)

sites = data.xpath('//body//h4//a/@href')

print str(len(sites)) + ' datasets found'

for site in sites:
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

csv_file.close()
