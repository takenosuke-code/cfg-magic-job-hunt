"""Job listing sources. Each source returns a list of Job dicts:

    {"id", "company", "title", "url", "locations", "posted_at", "source"}

To add a source (zero2sudo, a Muse export, etc.), write a function that
returns that shape and register it in SOURCES.
"""
import csv
import io
import json
import time
import urllib.request

from jobbot.links import clean_url

SIMPLIFY_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/"
    "dev/.github/scripts/listings.json"
)


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "cfg-magic-job-hunt"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _get_json(url: str):
    return json.loads(_get(url))


def simplify(config: dict) -> list:
    """SimplifyJobs internship list (the same listings zero2sudo reposts)."""
    terms = set(config.get("terms", []))
    categories = set(config.get("categories", []))
    jobs = []
    for row in _get_json(config.get("url", SIMPLIFY_URL)):
        if not (row.get("active") and row.get("is_visible", True)):
            continue
        if terms and not terms.intersection(row.get("terms", [])):
            continue
        if categories and row.get("category") not in categories:
            continue
        jobs.append(
            {
                "id": f"simplify:{row['id']}",
                "company": row.get("company_name", "?"),
                "title": row.get("title", "?"),
                "url": row.get("url", ""),
                "locations": row.get("locations", []),
                "posted_at": row.get("date_posted", 0),
                "source": "Simplify",
            }
        )
    return jobs


def google_sheet(config: dict) -> list:
    """A Google Sheet that Muse (or anyone) appends job links to.

    Needs a CSV link: share the sheet as "Anyone with the link can view" and use
    https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv
    Columns (header row, case-insensitive): url (required), company, title, location.
    """
    if not config.get("csv_url"):
        return []
    rows = csv.DictReader(io.StringIO(_get(config["csv_url"]).decode("utf-8-sig")))
    now = time.time()
    jobs = []
    for i, row in enumerate(rows):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        url = row.get("url") or row.get("link")
        if not url or not url.startswith("http"):
            continue
        location = row.get("location", "")
        jobs.append(
            {
                "id": f"sheet:{clean_url(url)}",
                "company": row.get("company") or "?",
                "title": row.get("title") or row.get("role") or "Job posting",
                "url": url,
                "locations": [location] if location else [],
                # Newer rows sort last, so they win when the per-run cap applies.
                "posted_at": now + i,
                "source": "Google Sheet",
            }
        )
    return jobs


SOURCES = {"simplify": simplify, "google_sheet": google_sheet}
