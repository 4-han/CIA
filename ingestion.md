### Running the Ingestion Pipeline

To scrape PDF links between May 1, 2025, and May 31, 2025, and also scrape the "Workshops" tab:

```bash
    python scripts/ingestion.py --click_workshop True --start_date 2025-05-01 --end_date 2025-05-31 
```
To scrape without clicking on the "Workshops" tab (using the default date range if not specified):
```bash
python scripts/ingestion.py --click_workshop False
# Or with a specific date range:
python scripts/ingestion.py --click_workshop False --start_date 2025-06-01 --end_date 2025-06-30
```

### Data Output

When the script runs, it will provide console output indicating its progress and any new links found.

The script outputs the following:

-   A list of newly found PDF links within the specified date range printed to the console, including the date, title, and URL of the document.
-   An updated `pdf_links.json` file located in the directory from which the script was executed. This file stores all previously scraped links along with any newly found ones, preventing duplicates in future scrapes.

### How It Works

1.  **Argument Parsing:** The script utilizes the `argparse` library to handle command-line arguments (`--click_workshop`, `--start_date`, `--end_date`). This allows users to control the scraping behavior and date filtering directly from the command line.

2.  **Setting Up Selenium:** `Selenium` is employed to automate browser interaction. It launches a headless Chrome browser instance (`--headless` flag) to visit the NITW notifications page. Selenium is crucial because the page's content is dynamically loaded using JavaScript. Running headless conserves resources, making it suitable for automated tasks.

3.  **Loading Saved Data:** Before initiating the scrape, the script checks for an existing `pdf_links.json` file. If found, it loads the saved list of previously scraped PDF links. This list is used to efficiently identify and skip any links that have already been recorded, ensuring data uniqueness and faster subsequent runs.

4.  **Extracting PDF Data:** The script leverages `BeautifulSoup` to parse the HTML source code obtained by Selenium. It navigates the HTML structure to locate elements corresponding to notification entries. For each entry, it specifically looks for:
    -   An `<a>` tag whose `href` attribute ends with `.pdf`.
    -   A date element (identified by a specific CSS selector).
    -   Title elements (identified by `h5` or `h6` tags).
    -   A regular expression (`\d{4}-\d{2}-\d{2}`) is used to ensure the extracted date string is in the expected `YYYY-MM-DD` format before converting it to a date object. Only links with dates falling within the user-specified `--start_date` and `--end_date` range are considered.

5.  **Workshop Tab Scraping (Optional):** If the `--click_workshop True` argument is provided, the script attempts to find and simulate a click on the HTML element corresponding to the "Workshops" tab. After clicking, it waits briefly for the page content to update via JavaScript and then repeats the PDF data extraction process for the newly loaded content in the Workshops section. Error handling is included in case the element cannot be found or clicked.

6.  **Saving Data:** After the scraping and filtering process is complete (including the optional Workshops tab), the script merges the newly found links with the previously loaded ones (if any). This combined list is then saved back to the `pdf_links.json` file in a formatted JSON structure. This persistence ensures that the script maintains a cumulative list of all scraped PDF links.

7.  **Logging and Output:** The script uses the `logging` module and `tqdm` to provide informative output during execution:
    -   `[INFO]`: General progress updates (e.g., launching browser, loading data, parsing pages).
    -   `[SUCCESS]`: Details of any newly found PDF links that meet the criteria.
    -   `[WARN]`: Potential non-critical issues (e.g., failure to click a tab).
    -   `[ERROR]`: Critical errors that might prevent parts of the script from running.

### Why This Script?

This scraper automates the tedious process of manually checking the NITW notifications page for new PDF announcements. By providing a simple command-line interface with date filtering and optional tab scraping, it streamlines the process of finding and collecting relevant official documents.

#### Key Benefits:

-   **Automated Document Discovery:** Eliminates the need for manual website monitoring.
-   **Targeted Scraping:** Focuses on specific date ranges and notification categories (default + workshops).
-   **Efficient Data Collection:** Avoids re-scraping already recorded links.
-   **Foundation for Further Processing:** The structured JSON output is ready to be used for further data processing steps, such as text extraction and indexing (like the `database.json` creation in the main project).