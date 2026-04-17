# WEB-SCRAPPING-PROJECT

A Flask-based product review search application with a premium UI and live Flipkart data scraping. The app opens Flipkart search pages through Selenium, reads the live review pages in a real browser session, and displays the extracted product reviews in a polished dashboard. Each successful search is also exported as a CSV file.

## Features

- Live Flipkart product review scraping
- Premium responsive UI for search and results
- CSV export for each successful search
- Error and empty-state handling
- Watermark branding: `Built by Neha Nishad`

## Tech Stack

- Python
- Flask
- Selenium
- WebDriver Manager
- Requests
- HTML / CSS

## Project Structure

```text
WEB-SCRAPPING-PROJECT/
|-- app.py
|-- requirements.txt
|-- static/
|   `-- css/
|       |-- main.css
|       `-- style.css
|-- templates/
|   |-- base.html
|   |-- index.html
|   `-- result.html
`-- README.md
```

## How It Works

1. Open the app home page.
2. Enter a product keyword such as `iphone 12`.
3. The backend launches a headless Chrome session with Selenium.
4. The app opens Flipkart search results, finds the first product, then opens its live review page.
5. Review rows are parsed and rendered in the results dashboard.
6. The same data is saved as a CSV file in the project folder.

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.10+
- Google Chrome installed on the system
- Internet connection for Flipkart page access

## Run Locally

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## Example Search Keywords

- iphone 12
- samsung mobile
- oneplus
- realme phone

## Notes

- Generated CSV files and logs are not intended to be committed.
- Flipkart uses dynamic pages and anti-bot protection, so the project uses Selenium instead of plain `requests`.
- First-time searches may take a few extra seconds while the browser session loads.

## Author

Built by Neha Nishad
