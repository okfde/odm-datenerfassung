# Scrapy settings for dirbot project

SPIDER_MODULES = ['dirbot.spiders']
NEWSPIDER_MODULE = 'dirbot.spiders'
DEFAULT_ITEM_CLASS = 'dirbot.items.Website'
DOWNLOADER_MIDDLEWARES = {
    'dirbot.middleware.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.contrib.downloadermiddleware.robotstxt.RobotsTxtMiddleware': None,
}
ROBOTSTXT_OBEY = True
ROBOTSTXT_BLACKLIST = ('sixcms/%20/sixcms', 'sixcms/sixcms', 'search', 'suche', 'dataset?f', 'branchen', 'mobil.koeln.de', 'flag_content', 'comment', 'immobilien.koeln', 'stadtfuehrungen', 'stadtplan.html', 'veranstaltungen/kalender', 'koeln.de/kleinanzeigen', '/feedback/' , '/recommend/', 'termine.koeln', 'bildung.koeln', 'anwendungen.bielefeld', 'rostock.de/veranstaltungen', 'wahlomat')
ROBOTSTXT_WHITELIST = ('/wahlen')
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3.0
AUTOTHROTTLE_DEBUG = True
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'
USER_AGENT = "Open_Data_Crawler/0.1 (+http://open-data-map.de)"
