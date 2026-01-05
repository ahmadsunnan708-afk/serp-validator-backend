from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import json
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- Helper Functions -------- #

def parse_html_serp(html_content):
    """
    Extract SERP titles & URLs from HTML
    (Basic Google-like structure)
    """
    soup = BeautifulSoup(html_content, "html.parser")
    results = []

    for result in soup.select("div.g"):
        title_tag = result.find("h3")
        link_tag = result.find("a")

        if title_tag and link_tag:
            results.append({
                "title": title_tag.get_text(strip=True),
                "url": link_tag.get("href")
            })

    return results


def parse_json_serp(json_content):
    """
    Expected JSON structure:
    {
      "results": [
        { "title": "", "url": "" }
      ]
    }
    """
    data = json.loads(json_content)
    return data.get("results", [])


def compare_serp(html_results, json_results):
    html_set = {(r["title"], r["url"]) for r in html_results}
    json_set = {(r["title"], r["url"]) for r in json_results}

    matched = html_set.intersection(json_set)
    missing_in_json = html_set - json_set
    extra_in_json = json_set - html_set

    return {
        "matched_count": len(matched),
        "missing_in_json": [
            {"title": t, "url": u} for t, u in missing_in_json
        ],
        "extra_in_json": [
            {"title": t, "url": u} for t, u in extra_in_json
        ]
    }

# -------- API Endpoint -------- #

@app.route("/validate", methods=["POST"])
def validate_serp():
    html_file = request.files.get("htmlFile")
    json_file = request.files.get("jsonFile")

    if not html_file or not json_file:
        return jsonify({"error": "Both HTML and JSON files are required"}), 400

    html_content = html_file.read().decode("utf-8", errors="ignore")
    json_content = json_file.read().decode("utf-8", errors="ignore")

    html_results = parse_html_serp(html_content)
    json_results = parse_json_serp(json_content)

    comparison = compare_serp(html_results, json_results)

    return jsonify({
        "html_results_count": len(html_results),
        "json_results_count": len(json_results),
        "comparison": comparison
    })


if __name__ == "__main__":
    app.run(debug=True)
