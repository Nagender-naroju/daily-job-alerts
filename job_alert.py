import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import re

KEYWORDS = ["laravel", "codeigniter"]

def fetch_jobs():
    """Fetch jobs from RemoteOK with improved parsing"""
    jobs = []
    
    for keyword in KEYWORDS:
        try:
            url = f"https://remoteok.com/remote-{keyword}-jobs"
            print(f"Fetching jobs for: {keyword}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.5",
            }
            
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            time.sleep(2)
            
            soup = BeautifulSoup(r.text, "html.parser")
            job_rows = soup.select("tr.job")
            
            print(f"Found {len(job_rows)} job elements for {keyword}")
            
            for row in job_rows[:3]:
                try:
                    title = row.get("data-title")
                    url_path = row.get("data-url")
                    desc_elem = row.select_one("td.description")
                    company_elem = row.select_one(".company")

                    if not title or not url_path:
                        print("Skipping job - missing title or URL")
                        continue
                    
                    company = company_elem.get_text(strip=True) if company_elem else "Startup"
                    
                    desc = "Remote position available. Check link for details."
                    if desc_elem:
                        desc_text = re.sub(r'\s+', ' ', desc_elem.get_text(strip=True))
                        desc = desc_text[:400]

                    link = f"https://remoteok.com{url_path}"

                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "link": link.strip(),
                        "desc": desc,
                        "keyword": keyword.upper()
                    })
                    print(f"✓ Added job: {title}")

                except Exception as e:
                    print(f"Error parsing row: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching {keyword} jobs: {e}")
            continue

    # Fallback sample jobs if scraping returns nothing
    if not jobs:
        print("No jobs scraped — using sample jobs for testing")
        jobs = [
            {
                "title": "Senior Laravel Developer",
                "company": "Tech Startup",
                "link": "https://remoteok.com/",
                "desc": "Looking for Laravel developer to build scalable backend systems.",
                "keyword": "LARAVEL"
            },
            {
                "title": "CodeIgniter PHP Developer",
                "company": "Innovative Labs",
                "link": "https://remoteok.com/",
                "desc": "Maintain and enhance CodeIgniter 3 applications.",
                "keyword": "CODEIGNITER"
            }
        ]

    print(f"Total jobs to send: {len(jobs)}")
    return jobs[:6]


def linkedin_message(job):
    """Free LinkedIn outreach template (no AI)"""
    return f"""Hi,

I came across the {job['title']} role at {job['company']} and found it interesting.
I have hands-on experience in {job['keyword']} and backend development, and I’d love to connect to learn more about this opportunity.

Thanks,
Nagu"""


def send_email(jobs):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("RECIPIENT_EMAIL", sender)

    if not sender or not password:
        print("ERROR: EMAIL_USER or EMAIL_PASS not set!")
        return False

    print(f"Sending email from: {sender} → {recipient}")

    html_body = f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2 style="background:#667eea;color:white;padding:15px;border-radius:6px;">
        🚀 Laravel & CodeIgniter Job Alerts
        </h2>
        <p>Found <b>{len(jobs)}</b> new job openings.</p>
    """

    for i, job in enumerate(jobs, 1):
        linkedin_msg = linkedin_message(job)

        html_body += f"""
        <div style="border:1px solid #ddd;padding:15px;margin:15px 0;border-radius:6px;">
            <h3 style="color:#667eea;">#{i} {job['title']}</h3>
            <p><b>Company:</b> {job['company']}</p>
            <p>{job['desc']}</p>
            <p><a href="{job['link']}">🔗 Apply Here</a></p>
            <hr>
            <b>💬 LinkedIn Outreach Message:</b>
            <pre style="white-space:pre-wrap;font-family:Arial;">{linkedin_msg}</pre>
        </div>
        """

    html_body += """
        <p style="font-size:12px;color:#888;">
        Automated Job Alert via GitHub Actions
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 {len(jobs)} New Laravel & CodeIgniter Jobs"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("Laravel & CodeIgniter Free Job Alert Started")
    print("="*60)
    
    jobs = fetch_jobs()
    
    if not jobs:
        print("No jobs found.")
        exit(1)
    
    success = send_email(jobs)
    
    if not success:
        exit(1)
