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
* Consistency checks within the database

Based on what data is marked as 'accepted', the data is published (using the same final CSV output files as before) to the website. This is done using the script https://github.com/okfde/odmonitormap/blob/gh-pages/data/downloadDataFromDB.py, the successor to downloadData.py. The consistency checks were moved from that repo to this one.

The import step (https://github.com/okfde/odm-datenerfassung/blob/master/utils/copyDataToDB.py) is more or less the algorithm shown in Workflow #1. Its important to note though that there is no longer the requirement to/function of processing all data per city at once. In fact the code was extended to be able to handle single sheets with multiple cities. By the end of the project it was more comfortable to be able to work with the complete Bing/Google results. This has the side effect that results without parents can end up in the database even if their filenames are stored as files in other entries. The only criterion for the database is that URLs have to be unique. Likewise, duplicate URLs from a "second" import would just be refused and won't have their category/geo attributes transferred. However, there is a second step that takes care of some of these issues, a consistency checking step within the DB (https://github.com/okfde/odm-datenerfassung/blob/master/utils/consistentDb.py). This performs the following steps:

* Mark all data from Google for Bonn as rejected. Bonn took the step of making sure that everything found with Google was put in the data catalog. As we are not repeating Google searches, this is not a problem. An alternative would be to just delete the data.
* Ensure that blank licenses receive a description that we don't know the license and open status. Ensure that open licenses lead to open being set to True. I.e. don't trust any import scripts to set the open status correctly :)
* For each city with data, retrieve a list of all filenames found using Google/Bing. If any of these filenames are found in a complete listing of all files from the crawler and data catalog, mark the corresponding record as not accepted.
* Remove cities with no data if they are not part of the original set of examined cities
* Mark as not accepted results from Google/Bing/Crawl where URLs appear to come from the data catalog
* Check that all cities have a coordinate. If not, try to get one using nominatim.openstreetmap.org.
* Convert any 'ODM' categories to the new, GovData-based categories
* Remove any unknown categories

The site was made self-updating by having a set of cron jobs that download the data from the catalogs on a regular basis and update the DB. Google/Bing/Crawl/Manual data was imported manually. The consistency checks were also run from a cron job as well as the publishing to CSV files. A git push is all that was needed to update the site. These scripts need to be put under okfde/infra/opendatamap (TODO). It is not neccessary to continue this in the long term; the site should actually reflect the status at the end of the project and we have a more sustainable workflow for the future, below.

### Sustainable workflow (CKAN+)
Towards the end of the project we started publishing the data to a CKAN instance. Currently we are creating harvesters for all of the catalog readers (almost finished) as well as for the data that is on offenedaten.de (not started, AFAIK). The non-catalog data still needs to be imported manually, a script exists for this purpose (https://github.com/okfde/odm-datenerfassung/blob/master/utils/export_to_ckan.py) as well as scripts to bring in the cities as organisations (https://github.com/okfde/odm-datenerfassung/blob/master/utils/export_orgs_to_ckan.py) and set up the categories (https://github.com/okfde/odm-datenerfassung/blob/master/utils/create_categories_in_ckan.py). The actual setup of this CKAN (currently at beta.offenedaten.de) is/will be documented at https://github.com/okfde/infra/blob/master/offenedaten. The CKAN work is at https://github.com/okfde/ckanext-offenedaten.

One idea was to extend CKAN to be able to handle the rejected and 'to be checked' data coming from (primarily) the crawler (https://github.com/okfde/ckanext-offenedaten/issues/44). The idea would be that data found that has been checked before does not need to be checked again, and that unchecked data is presented to an admin for checking. It turned out to not be such a high-priority issue.

### Connection to "Politik bei uns" and "Frag den Staat"
Towards the end of the project we scraped a large amount of data from Ratsinformationssysteme (city politics documentation, RIS). This should be browsable under politikbeiuns.de. The idea would be to a) show on the city map where RIS data is available (link to Politik bei uns) and b) extract data-heavy files from the scraped data for integration as datasets.

There is a simple function in https://github.com/okfde/ckanext-offenedaten to send an email to the person responsible if a dataset's status is closed or unknown. This has some similarity to the thinking behind fragdenstaat.de, where requests are sent for information. Behind fragdenstaat is a database of who to contact for what, and potentially this database could be used for offenedaten.de as well.
