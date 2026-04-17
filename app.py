import csv
import logging
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse

from flask import Flask, render_template, request
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)

CSV_OUTPUT_DIR = Path(__file__).resolve().parent
APP_HOST = "127.0.0.1"
APP_PORT = 5000
FLIPKART_SEARCH_URL = "https://www.flipkart.com/search?q={query}"
REVIEW_BLOCK_PATTERN = re.compile(r"^[1-5]\.0$")


def build_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1600,2600")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def extract_first_product_link(driver):
    links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
    for link in links:
        href = link.get_attribute("href")
        if href and "/p/" in href:
            return href, link.text
    raise ValueError("No Flipkart product link found for this search.")


def extract_product_name(link_text, fallback_search_term):
    lines = [line.strip() for line in link_text.splitlines() if line.strip()]
    for line in lines:
        if "Ratings" in line or "Reviews" in line or "Currently unavailable" in line:
            continue
        if "Add to Compare" in line:
            continue
        if len(line) > 12:
            return line
    return fallback_search_term.title()


def build_review_url(product_url):
    parsed = urlparse(product_url)
    pid = parse_qs(parsed.query).get("pid", [None])[0]
    if not pid:
        raise ValueError("Could not determine product id from Flipkart product URL.")

    path_before_query = parsed.path
    if "/p/" not in path_before_query:
        raise ValueError("Unexpected Flipkart product path.")

    slug, item_id = path_before_query.split("/p/", 1)
    return (
        f"https://www.flipkart.com{slug}/product-reviews/{item_id}"
        f"?pid={pid}&sortOrder=MOST_HELPFUL"
    )


def split_review_blocks(review_text):
    lines = [line.rstrip() for line in review_text.splitlines()]
    blocks = []
    current_block = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if REVIEW_BLOCK_PATTERN.match(line) and current_block:
            blocks.append(current_block)
            current_block = [line]
            continue

        current_block.append(line)

    if current_block:
        blocks.append(current_block)

    return blocks


def load_url_with_retries(driver, url, attempts=3, pause_seconds=4):
    last_exception = None
    for attempt in range(attempts):
        try:
            driver.get(url)
            return
        except (TimeoutException, WebDriverException) as exc:
            last_exception = exc
            if attempt == attempts - 1:
                break
            time.sleep(pause_seconds)
    raise last_exception


def parse_review_block(product_name, block_lines):
    if len(block_lines) < 8:
        return None

    try:
        rating = block_lines[0]
        heading = block_lines[1]
        product_variant = block_lines[2].replace("Review for:", "").strip()
        date = block_lines[-1]
        verified_purchase = block_lines[-2]
        helpful_votes = block_lines[-3]
        helpful_label = block_lines[-4]
        location = block_lines[-5]
        reviewer_name = block_lines[-6]
        comment_lines = block_lines[3:-6]

        if not comment_lines or "Verified Purchase" not in verified_purchase:
            return None

        comment = " ".join(comment_lines).strip()
        variant_suffix = f" ({product_variant})" if product_variant else ""
        helpful_summary = f"{helpful_label} ({helpful_votes})"

        return {
            "Product": f"{product_name}{variant_suffix}",
            "Name": reviewer_name,
            "Rating": rating,
            "CommentHead": heading,
            "Comment": f"{comment} | {location} | {helpful_summary} | {date}",
        }
    except (IndexError, ValueError):
        return None


def fetch_reviews(search_term):
    driver = build_driver()
    try:
        load_url_with_retries(
            driver,
            FLIPKART_SEARCH_URL.format(query=quote_plus(search_term)),
        )
        time.sleep(5)

        product_url, link_text = extract_first_product_link(driver)
        product_name = extract_product_name(link_text, search_term)
        review_url = build_review_url(product_url)

        load_url_with_retries(driver, review_url)
        time.sleep(8)

        body_text = driver.find_element(By.TAG_NAME, "body").text.encode("ascii", "ignore").decode()
        start_index = body_text.find("User reviews sorted by")
        end_index = body_text.find("Hang on, loading content")
        review_text = body_text[start_index:end_index if end_index != -1 else None]
        review_blocks = split_review_blocks(review_text)

        reviews = []
        for block in review_blocks:
            parsed_review = parse_review_block(product_name, block)
            if parsed_review:
                reviews.append(parsed_review)

        return reviews
    finally:
        driver.quit()


def write_reviews_csv(search_term, reviews):
    csv_path = CSV_OUTPUT_DIR / f"{search_term.replace(' ', '_')}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["Product", "Name", "Rating", "CommentHead", "Comment"],
        )
        writer.writeheader()
        writer.writerows(reviews)


@app.route("/", methods=["GET"])
def homepage():
    return render_template("index.html")


@app.route("/review", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        search_term = request.form.get("content", "").strip()
        if not search_term:
            return render_template(
                "result.html",
                reviews=[],
                search_term="",
                error="Please enter a product name to search.",
            )

        try:
            reviews = fetch_reviews(search_term)
            if not reviews:
                return render_template(
                    "result.html",
                    reviews=[],
                    search_term=search_term,
                    error="No reviews were found for that search.",
                )

            write_reviews_csv(search_term, reviews)
            logging.info("Fetched %s reviews for %s", len(reviews), search_term)
            return render_template(
                "result.html",
                reviews=reviews,
                search_term=search_term,
                error=None,
            )
        except (TimeoutException, WebDriverException, ValueError) as exc:
            logging.exception("Search failed for %s", search_term)
            return render_template(
                "result.html",
                reviews=[],
                search_term=search_term,
                error=f"Unable to fetch reviews right now: {exc}",
            )

    return render_template("index.html")


if __name__ == "__main__":
    print(f"Open this URL in your browser: http://{APP_HOST}:{APP_PORT}/")
    app.run(host=APP_HOST, port=APP_PORT)
