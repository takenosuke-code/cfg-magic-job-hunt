# cfg-magic-job-hunt

Automatically posts new SWE internship listings into a Slack channel (e.g. `#swe-recruitment-prep`) so club members don't have to paste links by hand.

## How it works

1. A GitHub Action runs every 30 minutes (`.github/workflows/post-jobs.yml`).
2. `jobbot` pulls listings from each source in `config.json`. Right now that's the [SimplifyJobs Summer 2027 internship list](https://github.com/SimplifyJobs/Summer2027-Internships), filtered to Software / Software Engineering roles. It's the same pool zero2sudo reposts from.
3. Tracking parameters (`fbclid`, `utm_*`, `ref`, ...) are stripped from links.
4. Anything not already in `state/seen.json` is queued (max 10 per run, so a quiet run might post 0 to 3). The Action commits the updated `state/seen.json` first, then posts, so a failed save means nothing is posted and a listing is never posted twice.

The very first run only records existing postings and posts nothing, so the channel isn't flooded with hundreds of old links.

## Setup

1. In Slack, create an app with an [incoming webhook](https://api.slack.com/messaging/webhooks) for your channel.
2. In this repo, go to **Settings → Secrets and variables → Actions** and add `SLACK_WEBHOOK_URL`.
3. Run the workflow once from the **Actions** tab (**Run workflow**) to seed `state/seen.json`.

## Run locally

```sh
python -m unittest discover tests
python -m jobbot.main collect --dry-run   # prints what would be posted, saves nothing
```

No dependencies beyond the Python 3 standard library.

## Adding sources

Write a function in `jobbot/sources.py` that returns job dicts (`id`, `company`, `title`, `url`, `locations`, `posted_at`, `source`), register it in `SOURCES`, and add it to `config.json`. Ideas:

- zero2sudo directly
- New-grad lists
- Sharing what members apply to (e.g. a Muse export)
