"""
This is a middleware to respect robots.txt policies. To activate it you must
enable this middleware and enable the ROBOTSTXT_OBEY setting.

"""
import re

from reppy.cache import RobotsCache

from scrapy import signals, log
from scrapy.exceptions import NotConfigured, IgnoreRequest
from scrapy.http import Request
from scrapy.utils.httpobj import urlparse_cached


class RobotsTxtMiddleware(object):
    DOWNLOAD_PRIORITY = 1000

    def __init__(self, crawler):
        if not crawler.settings.getbool('ROBOTSTXT_OBEY'):
            raise NotConfigured

        self.completeblacklist = crawler.settings.get('ROBOTSTXT_BLACKLIST', ())
        self.blacklist = []
        self.generalblacklist = crawler.settings.get('GENERAL_BLACKLIST', ())
        self.hasblacklist = False
        self.whitelist = crawler.settings.get('ROBOTSTXT_WHITELIST', ())
        self.crawler = crawler
        self._useragent = crawler.settings.get('USER_AGENT')
        self._parsers = {}
        self._spider_netlocs = set()
        self.robots = RobotsCache()
        
        self.stoprepetitionsrearg = re.compile(ur'.*?\&(.*?\&)\1{1,}.*')
        self.stoprepetitionsreslash = re.compile(ur'.*?\/(.*?\/)\1{1,}.*')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        useragent = self._useragent
        if not self.hasblacklist:
            self.hasblacklist = True
            if ('http://' + spider.domain) in self.completeblacklist and self.completeblacklist['http://' + spider.domain] != None:
                self.blacklist = [el.lower() for el in self.completeblacklist['http://' + spider.domain]]
                log.msg(format="Got blacklist from DB for domain",
                    level=log.DEBUG, request=request)
            else:
                log.msg(format="Didn't get a blacklist from DB for domain",
                    level=log.DEBUG, request=request)
            self.blacklist.extend([el.lower() for el in self.generalblacklist])
        #Check for silly repeating arguments
        if self.stoprepetitionsrearg.match(request.url) != None or self.stoprepetitionsreslash.match(request.url) != None:
            log.msg(format="URL is suspicious: %(request)s",
                    level=log.DEBUG, request=request)
            raise IgnoreRequest
        #Blacklist overrides whitelist and robots
        if any(bl in request.url.lower() for bl in self.blacklist):
            log.msg(format="Forbidden by blacklist: %(request)s",
                    level=log.DEBUG, request=request)
            raise IgnoreRequest
        if not any(wl in request.url for wl in self.whitelist) and self.robots and not self.robots.allowed(request.url, useragent):
            log.msg(format="Forbidden by robots.txt: %(request)s",
                    level=log.DEBUG, request=request)
            raise IgnoreRequest

