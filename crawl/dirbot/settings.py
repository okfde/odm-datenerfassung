# Scrapy settings for dirbot project

SPIDER_MODULES = ['dirbot.spiders']
NEWSPIDER_MODULE = 'dirbot.spiders'
DEFAULT_ITEM_CLASS = 'dirbot.items.Website'
SPIDER_MIDDLEWARES = {
    'dirbot.middleware.robotstxt.RobotsTxtMiddleware': 543,
}
ROBOTSTXT_OBEY = True

