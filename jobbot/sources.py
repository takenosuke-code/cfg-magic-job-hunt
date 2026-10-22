"""Job listing sources. Each source returns a list of Job dicts:

    {"id", "company", "title", "url", "locations", "posted_at", "source"}

To add a source (zero2sudo, a Muse export, etc.), write a function that
returns that shape and register it in SOURCES.
"""
import json
import urllib.request

SIMPLIFY_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/"
    "dev/.github/scripts/listings.json"
)


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "cfg-magic-job-hunt"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


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


SOURCES = {"simplify": simplify}
