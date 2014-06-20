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
        self.filetypes = ('.CSV', '.XLS', '.XLSX', '.JSON', '.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS', '.RDF', '.ZIP')
        self.geofiletypes = ('.GEOJSON', '.GML', '.GPX', '.GJSON', '.TIFF', '.SHP', '.KML', '.KMZ', '.WMS', '.WFS')

        self.fields = ('Stadt_URL', 'URL_Datei', 'URL_Text', 'URL_Dateiname', 'Format', 'geo', 'URL_PARENT', 'Title_PARENT')
        self.writer = unicodecsv.DictWriter(open(self.fileoutall, "wb"), self.fields)
        self.writer.writeheader()
        self.writerdata = unicodecsv.DictWriter(open(self.fileoutdata, "wb"), self.fields)
        self.writerdata.writeheader()
        print "Searching " + domain + "..."


    def parse_page(self, response):
        sel = Selector(response)
        parent_title = sel.xpath('//title/text()').extract()
        if (len(parent_title)>0): parent_title = parent_title[0].encode('utf-8')
        parent_url = response.url
        sites = sel.xpath('//body//a')
        items = []

        for site in sites:
            item = Website()
            item['URL_Datei'] = site.xpath('@href').extract()
            if (len(item['URL_Datei'])>0): item['URL_Datei'] = item['URL_Datei'][0].encode('utf-8')
            item['Stadt_URL'] = self.domain
            item['URL_Text'] = site.xpath('text()').extract()
            #TODO? Grab other stuff in side the A like image alt text
            if (len(item['URL_Text'])>0): item['URL_Text'] = item['URL_Text'][0].encode('utf-8')
            item['URL_Dateiname'] = str(item['URL_Datei']).split('/')[-1]
            if (len(item['URL_Dateiname'])>0): item['URL_Dateiname'] = item['URL_Dateiname'][0].encode('utf-8')
            item['Format'] = 'Not interesting'
            item['geo'] = ''
            item['URL_PARENT'] = parent_url
            item['Title_PARENT'] = parent_title
            for ext in self.filetypes:
               if ext in str(item['URL_Datei']).upper():
                   item['Format'] = ext[1:len(ext)]
                   self.writerdata.writerow(item)
                   if ext in self.geofiletypes:
                       item['geo'] = 'x'
            self.writer.writerow(item) 
            items.append(item)

        return items
