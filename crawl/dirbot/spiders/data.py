import unicodecsv

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector

from dirbot.items import Website


class DataSpider(CrawlSpider):
    name = "data"
    rules = (
        # Extract all links and parse them with the spider's method parse_page
        Rule(SgmlLinkExtractor(),callback='parse_page',follow=True),
    ) 
    
    def __init__(self, domain=None, *a, **kw):
        super(DataSpider, self).__init__(*a, **kw)
        self.domain = domain
        self.fileoutall = domain + ".csv"
        self.fileoutdata = domain + ".data.csv"
        self.allowed_domains = [self.domain]
        self.start_urls = [
        "http://www." + domain + "/",
        ]
        
        #File types to search for (non-geo); list so that we can extend
        self.filetypes = ['.CSV', '.XLS', '.XLSX', '.JSON', '.RDF', '.ZIP']
        #Geographic file types
        self.geofiletypes = ('.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS')
        #Combined list to search for at first
        self.filetypes.extend(self.geofiletypes)
        #Better for searching later
        self.filetypes = tuple(self.filetypes)

        self.fields = ('Stadt_URL', 'URL_Datei', 'URL_Text', 'URL_Dateiname', 'Format', 'geo', 'URL_PARENT', 'Title_PARENT')
        self.writer = unicodecsv.DictWriter(open(self.fileoutall, "wb"), self.fields)
        self.writer.writeheader()
        self.writerdata = unicodecsv.DictWriter(open(self.fileoutdata, "wb"), self.fields)
        self.writerdata.writeheader()
        print "Searching " + domain + "..."


    def parse_page(self, response):
        sel = Selector(response)
        
        #Title of the page we are on (this will be the 'parent')
        parent_title = sel.xpath('//title/text()').extract()
        if (len(parent_title)>0): parent_title = parent_title[0]
        #URL of the page we are on (parent)
        parent_url = response.url
        
        #Get all links
        sites = sel.xpath('//body//a')
        items = []

        for site in sites:
            item = Website()
            
            item['URL_Datei'] = unicode('', 'utf-8')
            url_file = site.xpath('@href').extract()
            if (len(url_file)>0):
                item['URL_Datei'] = url_file[0]
            
            item['Stadt_URL'] = unicode(self.domain, 'utf-8')
            
            #Get ALL text of everything inside the link
            #First any sub-elements like <span>
            textbits = site.xpath('child::node()')
            item['URL_Text'] = unicode('', 'utf-8')
            for text in textbits:
                thetext = text.xpath('text()').extract()
                if (len(thetext) > 0): item['URL_Text'] += thetext[0]
            #Then the actual text
            directText = site.xpath('text()').extract()
            #If there's something there and it isn't a repetition, use it
            if (len(directText) > 0) and (directText != thetext):
                item['URL_Text'] += directText[0]
            item['URL_Text'] = item['URL_Text'].replace("\t", " ").replace("\n", "").strip()
            
            #If that got us nothing, then look at the title and alt elements
            title_text = site.xpath('@title').extract()
            if (len(title_text)>0) and (item['URL_Text'] == u''):
                item['URL_Datei'] = title_text[0]
            alt_text = site.xpath('@alt').extract()
            if (len(alt_text)>0) and (item['URL_Text'] == u''):
                item['URL_Datei'] = alt_text[0]
            
            item['URL_Dateiname'] = unicode(item['URL_Datei']).split('/')[-1]
            item['Format'] = u'Not interesting'
            item['geo'] = u''
            item['URL_PARENT'] = parent_url
            item['Title_PARENT'] = parent_title
            
            #Is it a file (does it have any of the extensions (including the '.' in the filename,
            #then remove the '.' 
            for ext in self.filetypes:
               if ext in item['URL_Datei'].encode('ascii', errors='ignore').upper():
                   item['Format'] = ext[1:len(ext)]
                   self.writerdata.writerow(item)
                   #And is it one of our special geo filetypes?
                   if ext in self.geofiletypes:
                       item['geo'] = 'x'
            self.writer.writerow(item) 
            items.append(item)

        return items
