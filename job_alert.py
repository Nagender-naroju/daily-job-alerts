import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

KEYWORDS = ["laravel", "codeigniter"]

def fetch_jobs():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://remoteok.com/remote-{keyword}-jobs"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.select("tr.job"):
            title = row.get("data-title")
            url_path = row.get("data-url")
            desc = row.select_one("td.description")

            # Skip rows missing data
            if not title or not url_path or not desc:
                continue

            link = "https://remoteok.com" + url_path

            jobs.append({
                "title": title.strip(),
                "link": link.strip(),
                "desc": desc.get_text(strip=True)[:300]
            })

    return jobs[:5]  # Limit to 5 jobs to avoid long emails


def linkedin_message(job):
    prompt = f"""
Write a short professional LinkedIn outreach message for this job.

Job Title: {job['title']}
Job Description: {job['desc']}

Keep it under 3 lines.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120
    )

    return response.choices[0].message.content.strip()


def send_email(body):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEText(body)
    msg["Subject"] = "🔥 Daily Laravel & CodeIgniter Jobs"
    msg["From"] = sender
    msg["To"] = sender

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.send_message(msg)
    server.quit()


if __name__ == "__main__":
    jobs = fetch_jobs()

    if not jobs:
        print("No jobs found today.")
        exit()

    email_body = "🚀 Today's Laravel & CodeIgniter Job Openings\n\n"

    for job in jobs:
        email_body += f"📌 {job['title']}\n"
        email_body += f"🔗 {job['link']}\n"
        email_body += f"📝 {job['desc']}\n\n"
        email_body += "💬 LinkedIn Outreach Message:\n"
        email_body += linkedin_message(job)
        email_body += "\n\n-----------------------------\n\n"

    send_email(email_body)
    print("Email sent successfully!")
