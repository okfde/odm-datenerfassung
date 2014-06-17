import unicodecsv

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector

from dirbot.items import Website


class DataSpider(CrawlSpider):
    name = "data"
    domain = "moers.de"
    allowed_domains = [domain]
    filetypes = ('CSV', 'XLS', 'XLSX', 'JSON', 'SHP', 'KML', 'KMZ', 'RDF', 'ZIP')
    start_urls = [
        "http://www.moers.de/",
    ]
    
    fileout = "output.csv"
    fields = ('Stadt_URL', 'URL_Datei', 'URL_Text', 'URL_Dateiname', 'Format', 'URL_PARENT', 'Title_PARENT')
    writer = unicodecsv.DictWriter(open(fileout, "wb"), fields)
    writer.writeheader()
    
    rules = (
        # Extract all links and parse them with the spider's method parse_page
        Rule(SgmlLinkExtractor(),callback='parse_page',follow=True),
    )

    def parse_page(self, response):
        sel = Selector(response)
        parent_title = sel.xpath('(//head//title)[1]')
        patent_url = response.url
        sites = sel.xpath('//body//a')
        items = []

        for site in sites:
            item = Website()
            item['URL_Datei'] = site.xpath('@href').extract()
            extension = str(item['URL_Datei']).split('.')[-1].upper()
            if (extension in self.filetypes):
                item['Stadt_URL'] = domain
                item['URL_Text'] = site.xpath('text()').extract()
                item['URL_Dateiname'] = site.xpath('@href').extract()
                item['Format'] = extension
                item['URL_PARENT'] = parent_url
                item['Title_PARENT'] = parent_title
                writer.writerow(item)
                print item
            
            items.append(item)

        return items
