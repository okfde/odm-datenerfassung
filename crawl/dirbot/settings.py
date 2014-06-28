# Scrapy settings for dirbot project

SPIDER_MODULES = ['dirbot.spiders']
NEWSPIDER_MODULE = 'dirbot.spiders'
DEFAULT_ITEM_CLASS = 'dirbot.items.Website'
DOWNLOADER_MIDDLEWARES = {
    'dirbot.middleware.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.contrib.downloadermiddleware.robotstxt.RobotsTxtMiddleware': None,
}
ROBOTSTXT_OBEY = True
ROBOTSTXT_BLACKLIST = ('bildung.koeln', 'anwendungen.bielefeld')
ROBOTSTXT_WHITELIST = ('/wahlen')
