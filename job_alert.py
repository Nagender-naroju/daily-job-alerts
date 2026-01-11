import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

KEYWORDS = ["laravel", "codeigniter"]

# ---------- Fetch Jobs from Remotive API ----------
def fetch_jobs():
    jobs = []

    for keyword in KEYWORDS:
        print(f"Fetching jobs for: {keyword} from Remotive API")
        url = f"https://remotive.io/api/remote-jobs?search={keyword}"
        
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json()
            
            for job in data.get("jobs", [])[:5]:  # top 5 jobs per keyword
                jobs.append({
                    "title": job["title"],
                    "company": job["company_name"],
                    "link": job["url"],
                    "desc": (job.get("description") or "Remote position").replace("\n", " ")[:400],
                    "keyword": keyword.upper()
                })
        except Exception as e:
            print(f"Error fetching jobs for {keyword}: {e}")
            continue

    print(f"Total jobs found: {len(jobs)}")
    return jobs[:6]  # limit total jobs to 6


# ---------- Free LinkedIn Message ----------
def linkedin_message(job):
    return f"""Hi,

I came across the {job['title']} role at {job['company']}. 
I have strong experience in {job['keyword']} and backend development and would love to contribute to your team.

Looking forward to connecting.

Regards,
Nagender Naroju"""


# ---------- Send Email ----------
def send_email(jobs):
    if not jobs:
        print("No jobs found. Email will not be sent.")
        return False

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
        import smtplib
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
    if not jobs:
        print("⚠️ No jobs found. Exiting without sending email.")
        exit(0)

    success = send_email(jobs)

    if success:
        print("✅ Completed Successfully")
    else:
        print("❌ Failed")
        exit(1)
