# WEB-SCRAPPING-PROJECT

A Flask-based product review search app with a polished premium UI. The app lets you enter a product keyword, fetch matching product review data from a live API, display the results in a styled dashboard, and export each search result as a CSV file.

## Features

- Search product reviews by keyword
- Responsive premium UI for search and result screens
- CSV export for every successful search
- Clean empty-state and error handling
- Watermark branding: `Built by Neha Nishad`

## Tech Stack

- Python
- Flask
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

1. Open the home page.
2. Enter a product keyword such as `iphone 12`, `laptop`, `perfume`, or `chair`.
3. The Flask backend sends the search to a product API.
4. Matching review data is rendered in the results dashboard.
5. A CSV file is generated for the current search in the project folder.

## Installation

```bash
pip install -r requirements.txt
```

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
- laptop
- perfume
- chair
- smartphone

## Notes

- Generated CSV files and logs are not intended to be committed.
- The current implementation uses a live product API instead of scraping protected e-commerce pages directly.

## Author

Built by Neha Nishad
