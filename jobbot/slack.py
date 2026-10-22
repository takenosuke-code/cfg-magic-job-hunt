"""Post jobs to Slack through an incoming webhook."""
import json
import urllib.request


def format_job(job: dict) -> dict:
    locations = ", ".join(job["locations"][:3]) or "Location N/A"
    if len(job["locations"]) > 3:
        locations += f" +{len(job['locations']) - 3} more"
    text = f"*{job['company']}* - <{job['url']}|{job['title']}>\n:round_pushpin: {locations}"
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def post(webhook_url: str, jobs: list) -> None:
    # Slack allows 50 blocks per message; keep it readable with 10.
    for i in range(0, len(jobs), 10):
        batch = jobs[i : i + 10]
        payload = {
            "text": f"{len(batch)} new SWE posting(s)",
            "blocks": [format_job(j) for j in batch],
        }
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=30).read()
