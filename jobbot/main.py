"""Fetch new job postings and post them to Slack.

Usage:
    python -m jobbot.main collect [--dry-run]   # update seen.json, queue new jobs
    python -m jobbot.main post                  # post the queued jobs to Slack

Collecting and posting are separate so the workflow can save seen.json
before anything is posted: if saving fails, nothing is posted, and a job
can never be posted twice.

The first run only records what exists (so the channel isn't flooded with
hundreds of old postings); later runs post anything new.
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
PENDING_PATH = ROOT / "state" / "pending.json"


def collect(dry_run: bool) -> None:
    config = json.loads(CONFIG_PATH.read_text())
    first_run = not SEEN_PATH.exists()
    seen = set() if first_run else set(json.loads(SEEN_PATH.read_text()))

    jobs = []
    for name, source_config in config["sources"].items():
        jobs.extend(SOURCES[name](source_config))

    # Links are tracked as well as IDs, so a job that shows up in two sources
    # (e.g. Simplify and the Muse sheet) is only posted once.
    new_jobs = []
    for job in sorted(jobs, key=lambda j: j["posted_at"]):
        job["url"] = clean_url(job["url"])
        url_key = f"url:{job['url']}"
        already_seen = job["id"] in seen or url_key in seen
        seen.add(url_key)
        if already_seen:
            continue
        new_jobs.append(job)

    # Everything new is marked seen, even past the cap, so a burst of new
    # listings is posted once (capped) rather than dribbled out over hours.
    to_post = [] if first_run else new_jobs[-config.get("max_posts_per_run", 10) :]
    print(f"{len(jobs)} listings, {len(new_jobs)} new, queued {len(to_post)}"
          + (" (first run: seeding only)" if first_run else ""))

    if dry_run:
        for job in to_post:
            print(f"- {job['company']}: {job['title']} {job['url']}")
        return

    SEEN_PATH.parent.mkdir(exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(seen | {j["id"] for j in new_jobs}), indent=0))
    PENDING_PATH.write_text(json.dumps(to_post))


def post_pending() -> None:
    if not PENDING_PATH.exists():
        print("Nothing queued")
        return
    to_post = json.loads(PENDING_PATH.read_text())
    PENDING_PATH.unlink()
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        raise SystemExit("SLACK_WEBHOOK_URL is not set")
    if to_post:
        post(webhook, to_post)
    print(f"Posted {len(to_post)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["collect", "post"])
    parser.add_argument("--dry-run", action="store_true", help="print instead of saving")
    args = parser.parse_args()
    if args.command == "collect":
        collect(args.dry_run)
    else:
        post_pending()


if __name__ == "__main__":
    main()
