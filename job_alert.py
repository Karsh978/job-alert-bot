cat /mnt/user-data/outputs/job-alert-bot/job_alert.py
Output

"""
Job Alert Bot
-------------
Checks job sources for new internship/fresher postings matching your resume
keywords, and sends a WhatsApp message via Twilio for every NEW job found.

Sources covered:
  1. Internshala (search pages - scrape-friendly, no login needed)
  2. Greenhouse / Lever company career boards (used by many startups:
     Razorpay, Postman, Freshworks, CRED, Groww, etc. - public JSON APIs)

NOT covered (intentionally - these block bots / need paid APIs):
  - LinkedIn, Naukri, Glassdoor, Foundit, Indeed
  -> for these, the script prints a reminder link so you can check manually.

State (seen job IDs) is stored in seen_jobs.json so the same job is never
alerted twice. This file is committed back to the repo by the GitHub Action.
"""

import json
import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup

SEEN_FILE = "seen_jobs.json"

# ---- Resume keyword filter ----------------------------------------------
RESUME_KEYWORDS = [
    "mern", "react", "node", "javascript", "typescript", "java",
    "express", "mongodb", "mysql", "rest api", "full stack",
    "backend", "software engineer intern", "sde intern", "react native",
    "spring boot", "graduate engineer trainee", "sde-1", "fresher"
]

# Companies with public Greenhouse/Lever boards worth checking
GREENHOUSE_BOARDS = {
    "razorpay": "https://boards-api.greenhouse.io/v1/boards/razorpay/jobs",
    "postman": "https://boards-api.greenhouse.io/v1/boards/postman/jobs",
}
LEVER_BOARDS = {
    "groww": "https://api.lever.co/v0/postings/groww?mode=json",
}

INTERNSHALA_URLS = [
    "https://internshala.com/internships/mean-mern-stack-internship/",
    "https://internshala.com/internships/full-stack-development-internship/",
    "https://internshala.com/internships/node-js-internship/",
    "https://internshala.com/internships/react-js-internship/",
]

MANUAL_CHECK_LINKS = [
    ("LinkedIn", "https://in.linkedin.com/jobs/software-engineer-intern-jobs"),
    ("Naukri", "https://www.naukri.com/mern-stack-intern-jobs"),
    ("Indeed", "https://in.indeed.com/q-software-engineering-intern-jobs.html"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobAlertBot/1.0)"}


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def matches_resume(text):
    text = text.lower()
    return any(k in text for k in RESUME_KEYWORDS)


def job_id(*parts):
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def scrape_internshala():
    found = []
    for url in INTERNSHALA_URLS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("div.individual_internship")
            for c in cards[:15]:
                title_el = c.select_one("h3.heading_4_5.profile, a.job-title-href")
                company_el = c.select_one("p.company-name, h4.heading_6")
                link_el = c.select_one("a.job-title-href, a.view_detail_button")
                title = title_el.get_text(strip=True) if title_el else "Unknown role"
                company = company_el.get_text(strip=True) if company_el else "Unknown company"
                link = "https://internshala.com" + link_el["href"] if link_el and link_el.get("href", "").startswith("/") else (link_el["href"] if link_el else url)

                if matches_resume(title):
                    found.append({
                        "id": job_id("internshala", title, company),
                        "source": "Internshala",
                        "title": title,
                        "company": company,
                        "link": link,
                    })
        except Exception as e:
            print(f"[warn] Internshala scrape failed for {url}: {e}")
    return found


def scrape_greenhouse():
    found = []
    for name, api in GREENHOUSE_BOARDS.items():
        try:
            r = requests.get(api, headers=HEADERS, timeout=15)
            data = r.json()
            for job in data.get("jobs", []):
                title = job.get("title", "")
                if matches_resume(title):
                    found.append({
                        "id": job_id("greenhouse", name, str(job.get("id"))),
                        "source": f"Greenhouse - {name}",
                        "title": title,
                        "company": name.capitalize(),
                        "link": job.get("absolute_url", api),
                    })
        except Exception as e:
            print(f"[warn] Greenhouse scrape failed for {name}: {e}")
    return found


def scrape_lever():
    found = []
    for name, api in LEVER_BOARDS.items():
        try:
            r = requests.get(api, headers=HEADERS, timeout=15)
            data = r.json()
            for job in data:
                title = job.get("text", "")
                if matches_resume(title):
                    found.append({
                        "id": job_id("lever", name, str(job.get("id"))),
                        "source": f"Lever - {name}",
                        "title": title,
                        "company": name.capitalize(),
                        "link": job.get("hostedUrl", api),
                    })
        except Exception as e:
            print(f"[warn] Lever scrape failed for {name}: {e}")
    return found


def send_whatsapp(message):
    """Sends a WhatsApp message via Twilio Sandbox.
    Requires env vars: TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, TWILIO_TO
    TWILIO_FROM is Twilio's sandbox number e.g. 'whatsapp:+14155238886'
    TWILIO_TO is your number e.g. 'whatsapp:+91XXXXXXXXXX'
    Returns True if sent successfully, False otherwise.
    """
    sid = os.environ["TWILIO_SID"]
    token = os.environ["TWILIO_AUTH_TOKEN"]
    from_num = os.environ["TWILIO_FROM"]
    to_num = os.environ["TWILIO_TO"]

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    resp = requests.post(
        url,
        auth=(sid, token),
        data={"From": from_num, "To": to_num, "Body": message},
        timeout=15,
    )
    if resp.status_code >= 300:
        print(f"[error] Twilio send failed: {resp.status_code} {resp.text}")
        return False
    else:
        print("[ok] WhatsApp message sent")
        return True


def main():
    seen = load_seen()
    all_jobs = scrape_internshala() + scrape_greenhouse() + scrape_lever()

    new_jobs = [j for j in all_jobs if j["id"] not in seen]

    if not new_jobs:
        print("No new matching jobs this run.")
    else:
        print(f"Found {len(new_jobs)} new matching job(s).")
        # Group multiple jobs into one WhatsApp message to avoid spam/rate limits
        chunks = [new_jobs[i:i + 3] for i in range(0, len(new_jobs), 3)]
        successfully_sent_ids = []
        for chunk in chunks:
            lines = ["🚨 *New Internship/Job Alert!*\n"]
            for j in chunk:
                lines.append(
                    f"*{j['title']}*\n"
                    f"Company: {j['company']}\n"
                    f"Source: {j['source']}\n"
                    f"Apply: {j['link']}\n"
                )
            sent_ok = send_whatsapp("\n".join(lines))
            if sent_ok:
                successfully_sent_ids.extend(j["id"] for j in chunk)
            else:
                print(f"[warn] Skipping seen-mark for {len(chunk)} job(s) since the message failed to send (will retry next run).")

        if successfully_sent_ids:
            seen.update(successfully_sent_ids)
            save_seen(seen)

    print("\nReminder - check these manually (cannot be auto-scraped reliably):")
    for name, link in MANUAL_CHECK_LINKS:
        print(f"  {name}: {link}")


if __name__ == "__main__":
    main()
