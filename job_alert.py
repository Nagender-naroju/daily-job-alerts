import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

KEYWORDS = ["laravel", "codeigniter"]

def fetch_jobs():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://remoteok.com/remote-{keyword}-jobs"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.select("tr.job"):
            title = row.get("data-title")
            link = "https://remoteok.com" + row.get("data-url")
            desc = row.select_one("td.description")
            if title and desc:
                jobs.append({
                    "title": title,
                    "link": link,
                    "desc": desc.get_text(strip=True)[:300]
                })
    return jobs[:5]  # avoid spam

def linkedin_message(job):
    prompt = f"""
Write a short LinkedIn outreach message for this job:

Title: {job['title']}
Description: {job['desc']}
"""

    res = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120
    )
    return res.choices[0].message.content

def send_email(body):
    msg = MIMEText(body)
    msg["Subject"] = "🔥 Daily Laravel / CI Jobs"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_USER")

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
    server.send_message(msg)
    server.quit()

if __name__ == "__main__":
    jobs = fetch_jobs()
    if not jobs:
        exit()

    email_body = ""
    for job in jobs:
        email_body += f"\n{job['title']}\n{job['link']}\n{job['desc']}\n"
        email_body += "LinkedIn Message:\n"
        email_body += linkedin_message(job)
        email_body += "\n\n------------------------\n"

    send_email(email_body)
