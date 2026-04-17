import csv
import logging
from pathlib import Path

import requests
from flask import Flask, render_template, request

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

app = Flask(__name__)

DUMMYJSON_SEARCH_URL = "https://dummyjson.com/products/search"
CSV_OUTPUT_DIR = Path(__file__).resolve().parent
APP_HOST = "127.0.0.1"
APP_PORT = 5000


def fetch_reviews(search_term):
    response = requests.get(
        DUMMYJSON_SEARCH_URL,
        params={"q": search_term},
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    products = response.json().get("products", [])
    reviews = []

    for product in products:
        product_title = product.get("title", search_term)
        product_rating = product.get("rating", "No Rating")
        product_reviews = product.get("reviews", [])

        if not product_reviews:
            reviews.append(
                {
                    "Product": product_title,
                    "Name": "Catalog",
                    "Rating": product_rating,
                    "CommentHead": "Product overview",
                    "Comment": product.get("description", "No description available."),
                }
            )
            continue

        for review in product_reviews:
            reviews.append(
                {
                    "Product": product_title,
                    "Name": review.get("reviewerName", "Anonymous"),
                    "Rating": review.get("rating", product_rating),
                    "CommentHead": review.get("comment", "Customer review")[:60],
                    "Comment": review.get("comment", "No comment available."),
                }
            )

    return reviews


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
        except requests.RequestException as exc:
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
