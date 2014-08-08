Data gathering for http://www.open-data-map.de/ (odm-datenerfassung)
==================

Various tools to gather data on open data provided by German city/town web portals:
    * Export metadata from data catalogs to CSV
    * Scrape metadata from data catalogs to CSV when API is absent or incomplete
    * Use Bing's API to gather search engine results
    * Crawl websites using Scrapy, Heritrix (WARC files) and the 2013 Common Crawl Corpus (because it's indexed!) for files that could be open data
    * Removing duplicates from the data in a prioritized fashion
    * Analysis for comparing methods
    
Some parts are highly experimental and incomplete, some parts less. The Scrapy crawler works quites well but could use some 'getting stuck' detection. More improvements and info coming soon!
