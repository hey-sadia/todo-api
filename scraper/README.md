\# The Polite Scraper



A small, polite web scraper that collects book data from a public practice sandbox.



\## Target Classification



\- \*\*Site:\*\* https://books.toscrape.com

\- \*\*Why this site:\*\* Books to Scrape is a sandbox built specifically for practicing web scraping. It is free, requires no login, and explicitly exists for this purpose.

\- \*\*Scope:\*\* Only the first 3 catalogue pages (60 books total). No other pages or sites are touched.

\- \*\*Data collected:\*\* Book title, price, availability, rating, description, and product URL.

\- \*\*Robots.txt check:\*\* I requested https://books.toscrape.com/robots.txt and received a 404 Not Found response. This means there is no robots file present. A missing file is not permission — it simply means no explicit robots rules exist. Since this site is explicitly built and advertised as a practice sandbox for scraping, scraping it remains appropriate within this assignment's scope (first 3 catalogue pages only).



I will not reuse this code on another site without checking its rules and terms first.





\## How to Run



1\. Install the libraries: `pip install requests beautifulsoup4 pydantic`

2\. Go into the scraper folder: `cd scraper`

3\. Run: `python src/main.py`



The first run downloads pages into `cache/`. Later runs read from the cache and do not hit the website again.



\## How It Works



1\. \*\*Fetch (politely):\*\* Every request sends a clear User-Agent, has a 10 second timeout, and waits 0.5 seconds after each real request. Pages are saved in `cache/`, so a repeat run makes no new requests.

2\. \*\*Discover:\*\* Reads the first 3 catalogue pages and collects 60 unique book links.

3\. \*\*Extract:\*\* Visits each book page and pulls out title, price, availability, rating, description, product URL, source page and fetched time.

4\. \*\*Validate:\*\* Converts `price\_text` like `£51.77` into the number `price\_gbp` 51.77, then checks every record with a Pydantic schema.

5\. \*\*Save:\*\* Valid books go to `output/books.json`, bad records and failed pages go to `output/errors.json`, and a summary goes to `output/run-report.json`.



\## Failure Handling



If one page fails to download, the scraper prints a `FAILED` line, saves the problem in `errors.json`, and continues with the remaining pages.



\## Failure Test Result



I added one fake URL on purpose (`this-page-does-not-exist\_999`). It returned a 404 and was logged as a failure, but the other 60 books were still scraped.



\- urls\_attempted: 61

\- pages\_fetched: 60

\- fetch\_failures: 1

\- records\_valid: 60

\- records\_invalid: 0



\## Known Issues



\- Some book descriptions contain repeated text. This comes from the website's own data, not from a bug in the scraper.

\- Only the first 3 catalogue pages are scraped, by design.

