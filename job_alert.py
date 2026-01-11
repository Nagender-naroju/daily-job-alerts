import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import re

KEYWORDS = ["laravel", "codeigniter"]

# ---------- Fetch Jobs ----------
def fetch_jobs():
    jobs = []

    for keyword in KEYWORDS:
        print(f"Fetching jobs for: {keyword}")
        url = f"https://remoteok.com/remote-{keyword}-jobs"

        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.select("tr.job")

        print(f"Found {len(rows)} job rows")

        for row in rows[:5]:
            title = row.get("data-title")
            company = row.get("data-company")
            url_path = row.get("data-url")

            if not title or not url_path:
                continue

            link = "https://remoteok.com" + url_path

            desc = f"Remote {keyword.title()} position at {company}"

            jobs.append({
                "title": title.strip(),
                "company": company.strip() if company else "Company",
                "link": link,
                "desc": desc,
                "keyword": keyword.upper()
            })

    # fallback sample jobs if scraping fails
    if not jobs:
        print("No jobs scraped — using sample jobs")
        jobs = [
            {
                "title": "Laravel Developer",
                "company": "Sample Company",
                "link": "https://remoteok.com",
                "desc": "Remote Laravel Developer role",
                "keyword": "LARAVEL"
            },
            {
                "title": "CodeIgniter Developer",
                "company": "Sample Startup",
                "link": "https://remoteok.com",
                "desc": "Remote CodeIgniter Developer role",
                "keyword": "CODEIGNITER"
            }
        ]

    print(f"Total jobs to send: {len(jobs)}")
    return jobs


# ---------- Free LinkedIn Message ----------
def linkedin_message(job):
    return f"""Hi,

I came across the {job['title']} role at {job['company']}. 
I have strong experience in {job['keyword']} and backend development and would love to contribute to your team.

Looking forward to connecting.

Regards,
Your Name"""


# ---------- Send Email ----------
def send_email(jobs):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("RECIPIENT_EMAIL", sender)

    if not sender or not password:
        print("EMAIL_USER or EMAIL_PASS missing")
        return False

    print(f"Sending email from: {sender} → {recipient}")

    html = f"<h2>🔥 {len(jobs)} New Jobs Found</h2>"

    for job in jobs:
        html += f"""
        <hr>
        <h3>{job['title']} - {job['company']}</h3>
        <p>{job['desc']}</p>
        <a href="{job['link']}">Apply Here</a>
        <pre>{linkedin_message(job)}</pre>
        """

    msg = MIMEMultipart()
    msg["Subject"] = f"Job Alerts - {time.strftime('%d %b %Y')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully")
        return True
    except Exception as e:
        print("❌ Email send error:", e)
        return False


# ---------- Main ----------
if __name__ == "__main__":
    print("=" * 50)
    print("Laravel & CodeIgniter Free Job Alert Started")
    print("=" * 50)

    jobs = fetch_jobs()
    success = send_email(jobs)

    if success:
        print("✅ Completed Successfully")
    else:
        print("❌ Failed")
        exit(1)
