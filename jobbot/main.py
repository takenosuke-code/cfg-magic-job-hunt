"""Fetch new job postings and post them to Slack.

Usage: python -m jobbot.main [--dry-run]

The first run only records what exists (so the channel isn't flooded with
thousands of old postings); later runs post anything new.
"""
import argparse
import json
import os
from pathlib import Path

from jobbot.links import clean_url
from jobbot.slack import post
from jobbot.sources import SOURCES

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
SEEN_PATH = ROOT / "state" / "seen.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="print instead of posting")
    args = parser.parse_args()

    config = json.loads(CONFIG_PATH.read_text())
    first_run = not SEEN_PATH.exists()
    seen = set() if first_run else set(json.loads(SEEN_PATH.read_text()))

    jobs = []
    for name, source_config in config["sources"].items():
        jobs.extend(SOURCES[name](source_config))

    new_jobs = [j for j in jobs if j["id"] not in seen]
    new_jobs.sort(key=lambda j: j["posted_at"])
    for job in new_jobs:
        job["url"] = clean_url(job["url"])

    to_post = [] if first_run else new_jobs[-config.get("max_posts_per_run", 20) :]
    print(f"{len(jobs)} listings, {len(new_jobs)} new, posting {len(to_post)}"
          + (" (first run: seeding only)" if first_run else ""))

    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if to_post:
        if args.dry_run or not webhook:
            for job in to_post:
                print(f"- {job['company']}: {job['title']} {job['url']}")
        else:
            post(webhook, to_post)

    if not args.dry_run:
        SEEN_PATH.parent.mkdir(exist_ok=True)
        SEEN_PATH.write_text(json.dumps(sorted(seen | {j["id"] for j in new_jobs}), indent=0))


if __name__ == "__main__":
    main()
