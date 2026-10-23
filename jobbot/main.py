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
    new_urls = set()
    for job in sorted(jobs, key=lambda j: j["posted_at"]):
        job["url"] = clean_url(job["url"])
        url_key = f"url:{job['url']}"
        if job["id"] in seen or url_key in seen:
            seen.add(url_key)
            continue
        if url_key in new_urls:
            continue
        new_urls.add(url_key)
        new_jobs.append(job)

    cap = config.get("max_posts_per_run", 10)
    flood_limit = config.get("flood_limit", 60)
    if first_run or len(new_jobs) > flood_limit:
        # A first run, or a source reshuffling its IDs, makes everything look
        # new. Record it all without posting rather than flooding the channel.
        to_post, done = [], new_jobs
        reason = "first run" if first_run else f"over flood_limit of {flood_limit}"
        print(f"{len(new_jobs)} new ({reason}): marking seen without posting")
    else:
        # Oldest first; anything past the cap stays unseen and posts next run.
        to_post = done = new_jobs[:cap]
    print(f"{len(jobs)} listings, {len(new_jobs)} new, queued {len(to_post)}, "
          f"{len(new_jobs) - len(done)} carried over to next run")

    if dry_run:
        for job in to_post:
            print(f"- {job['company']}: {job['title']} {job['url']}")
        return

    for job in done:
        seen.add(job["id"])
        seen.add(f"url:{job['url']}")
    SEEN_PATH.parent.mkdir(exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(seen), indent=0))
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
