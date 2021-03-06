# Scrapy settings for dirbot project

import psycopg2

import metautils

from dbsettings import settings

SPIDER_MODULES = ['dirbot.spiders']
NEWSPIDER_MODULE = 'dirbot.spiders'
DEFAULT_ITEM_CLASS = 'dirbot.items.Website'
DOWNLOADER_MIDDLEWARES = {
    'dirbot.middleware.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.contrib.downloadermiddleware.robotstxt.RobotsTxtMiddleware': None,
}
ROBOTSTXT_OBEY = True
GENERAL_BLACKLIST = ('.pdf', 'kontakt/', 'kontakt.', 'veranstaltungskalender', 'veranstaltungen', 'font=', 'print=', 'style=', 'font_size=')
#Old - not deleting as this needs to be transferred to the DB as far as possible
#ROBOTSTXT_BLACKLIST = ('urban.gera.de', 'extranet.iserlohn.de', 'timestamp=', 'textmodus=&textmodu', 'modul=druckansicht', 'switchtodate', 'dienstleistungen.php', 'siegen.de/vereinsregister', 'mitarbeiter/mitarbeiter.php', 'dienstleistungen/formular.php', 'events/list.php', 'lexikon/index.php', '.krebs/karte', 'cottbus.de/opt', 'cottbus.de/abfrage', 'sixcms/%20/sixcms', 'sixcms/sixcms', 'search', 'suche', 'dataset?f', 'branchen', 'mobil.koeln.de', 'flag_content', 'comment', 'immobilien.koeln', 'stadtfuehrungen', 'stadtplan.html', 'koeln.de/kleinanzeigen', '/feedback/' , '/recommend/', 'termine.koeln', 'bildung.koeln', 'anwendungen.bielefeld', 'wahlomat', 'php/merkliste', '_druck=1', 'unt_tagung', 'buergerinfo.ulm.de', 'map.jsp')
ROBOTSTXT_WHITELIST = ('/wahlen')
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3.0
AUTOTHROTTLE_DEBUG = True
DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'
USER_AGENT = "Open_Data_Crawler/0.1 (+http://open-data-map.de)"

ROBOTSTXT_BLACKLIST = dict()

cur = metautils.getDBCursor(settings)
cur.execute("SELECT url, crawl_blacklist FROM cities;")
results = cur.fetchall()
for result in results:
    ROBOTSTXT_BLACKLIST[result[0]] = result[1] #Key is city url, value is array of forbidden URL parts