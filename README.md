Data gathering for http://www.open-data-map.de/ (odm-datenerfassung)
==================

Various tools to gather data on open data provided by German city/town web portals:

  * Export metadata from data catalogs to CSV
  * Scrape metadata from data catalogs to CSV when API is absent or incomplete
  * Use Bing's API to gather search engine results
  * Crawl websites using Scrapy, Heritrix (WARC files) and the 2013 Common Crawl Corpus (because it's indexed!) for files that could be open data
  * Removing duplicates from the data in a prioritized fashion
  * Analysis for comparing methods
    
Some parts are highly experimental and incomplete, some parts less. The Scrapy crawler works quite well and is somewhat robust.

## ODM Workflow
The Open Data Monitor (ODM) project began by examining what data (in terms of open government data) can be found on city websites in Germany. The first data were manually collected, then Google searches were carried out and analysed, then Bing searches. In addition we used our own crawler, primarily because the data on what sites the links were to be found on ('parent URLs') was missing in Google and Bing. In addition we also gathered the 'low hanging fruit' available from data catalogs by using their APIs or scraping where none was available.

The website can be found at okfde/odmonitormap. Important to note that is completely static. We publish CSV files per city and these are downloaded and processed by the browser.

### Workflow #1
Initially, all data, even that from catalogs was checked and completed by hand and stored in a 'validated sheet': a Google Spreadsheet, one per city. These were published and the GIDs stored in a master spreadsheet. The data was downloaded and published on open-data-map.de.

* Extract data on city from complete Google and Bing search results
* Add data from crawler
* Add data from catalog
* Download all data, per city
* Add data to a final output CSV file, as follows:
    * Add data in the order: manual, data catalog, crawl, google, bing (why this is important will become clear in the following steps!)
    * Take the parent URL if available
    * If the parent URL already exists, do not add, but expand the existing entry with the current entry's geo and category attributes. Store the filename from the URL. If not, add and store the filename.
    * If there is no parent URL, check if the filename has already been stored (comparing complete URLs is too risky). If not, add. If so, transfer geo and category attributes.
    * If the URL suggests that the data came from the city's catalog, don't add it

Juicy details: https://github.com/okfde/odmonitormap/blob/fac3c17a84aadaeb1cd8a409208ab22fbdc8a3c4/data/downloadData.py

### Workflow #2
Workflow #1 was a bit cumbersome, and the reading of the data catalogs can more or less be automated. We created a PostgreSQL DB to hold the data and divided the consistency checks into two steps:

* Import (we had to get everything in from the validated sheets)
* Publish (using the same final CSV output files as before)

The import step is more or less the algorithm shown in Workflow #1. Its important to note though that there is no longer the requirement to/function of processing all data per city at once. In fact the code was extended to be able to handle sheets with multiple cities. By the end of the project it was more comfortable to be able to work with the complete Bing/Google results. This has the side effect that results without parents can end up in the database even if their filenames are stored as files in other entries. The only criterion for the database is that URLs have to be unique. Likewise, duplicate URLs from a "second" import would just be refused and won't have their category/geo attributes transferred. However, there is a second step that takes care of some of these issues, the publishing step.
