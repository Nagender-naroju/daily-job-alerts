import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
import time

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

KEYWORDS = ["laravel", "codeigniter"]

def fetch_jobs():
    """Fetch jobs from RemoteOK with improved error handling"""
    jobs = []
    
    for keyword in KEYWORDS:
        try:
            url = f"https://remoteok.com/remote-{keyword}-jobs"
            print(f"Fetching jobs for: {keyword}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            
            # Add delay to avoid rate limiting
            time.sleep(2)
            
            soup = BeautifulSoup(r.text, "html.parser")
            job_rows = soup.select("tr.job")
            
            print(f"Found {len(job_rows)} job rows for {keyword}")
            
            for row in job_rows[:3]:  # Limit to 3 jobs per keyword
                try:
                    # More robust data extraction
                    title = row.get("data-title") or row.select_one("h2")
                    url_path = row.get("data-url")
                    
                    # Try multiple selectors for description
                    desc_elem = row.select_one("td.description") or row.select_one(".description")
                    
                    if not title or not url_path:
                        continue
                    
                    # Extract title text if it's an element
                    if hasattr(title, 'get_text'):
                        title = title.get_text(strip=True)
                    
                    # Extract description
                    desc = desc_elem.get_text(strip=True)[:400] if desc_elem else "No description available"
                    
                    # Ensure URL is absolute
                    link = url_path if url_path.startswith('http') else f"https://remoteok.com{url_path}"
                    
                    # Extract company if available
                    company_elem = row.select_one(".company")
                    company = company_elem.get_text(strip=True) if company_elem else "Company not specified"
                    
                    jobs.append({
                        "title": str(title).strip(),
                        "company": company,
                        "link": link.strip(),
                        "desc": desc,
                        "keyword": keyword
                    })
                    
                except Exception as e:
                    print(f"Error parsing job row: {e}")
                    continue
                    
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {keyword} jobs: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error for {keyword}: {e}")
            continue
    
    print(f"Total jobs found: {len(jobs)}")
    return jobs[:6]  # Limit to 6 total jobs

def linkedin_message(job):
    """Generate LinkedIn outreach message with error handling"""
    try:
        prompt = f"""Write a short, professional LinkedIn outreach message for this job.

Job Title: {job['title']}
Company: {job['company']}
Job Description: {job['desc'][:200]}

Requirements:
- Keep it under 4 sentences
- Be personalized and enthusiastic
- Mention specific skills related to {job['keyword']}
- Professional but friendly tone
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"Error generating LinkedIn message: {e}")
        return f"Hi [Name],\n\nI'm very interested in the {job['title']} position at {job['company']}. I'd love to discuss how my {job['keyword'].title()} experience could benefit your team.\n\nBest regards"

def send_email(jobs):
    """Send email with HTML formatting"""
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("RECIPIENT_EMAIL", sender)
    
    if not sender or not password:
        raise ValueError("EMAIL_USER and EMAIL_PASS environment variables must be set")
    
    # Create HTML email
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
            .job {{ border: 2px solid #e0e0e0; padding: 20px; margin: 20px 0; border-radius: 8px; background: #f9f9f9; }}
            .job-title {{ color: #667eea; font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
            .company {{ color: #764ba2; font-weight: 600; margin-bottom: 10px; }}
            .description {{ margin: 15px 0; color: #555; }}
            .linkedin-box {{ background: #e8f4f8; border-left: 4px solid #0077b5; padding: 15px; margin-top: 15px; border-radius: 5px; }}
            .apply-btn {{ background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Laravel & CodeIgniter Job Alert</h1>
            <p>Fresh opportunities found on {time.strftime('%B %d, %Y')}</p>
        </div>
        
        <p style="margin: 20px 0;">Found <strong>{len(jobs)}</strong> new job openings matching your criteria!</p>
    """
    
    for i, job in enumerate(jobs, 1):
        linkedin_msg = linkedin_message(job)
        
        html_body += f"""
        <div class="job">
            <div class="job-title">#{i} - {job['title']}</div>
            <div class="company">🏢 {job['company']}</div>
            <div class="description">
                <strong>Description:</strong><br>
                {job['desc']}
            </div>
            <div>
                <strong>🏷️ Technology:</strong> {job['keyword'].upper()}
            </div>
            <a href="{job['link']}" class="apply-btn">Apply Now →</a>
            
            <div class="linkedin-box">
                <strong>💬 LinkedIn Outreach Message:</strong><br><br>
                <div style="white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 13px;">
{linkedin_msg}
                </div>
            </div>
        </div>
        """
    
    html_body += """
        <div class="footer">
            <p>This is an automated job alert from your GitHub Actions workflow</p>
            <p>Powered by RemoteOK + OpenAI + Gmail</p>
        </div>
    </body>
    </html>
    """
    
    # Create plain text version as fallback
    plain_body = f"🚀 Laravel & CodeIgniter Job Alert - {time.strftime('%B %d, %Y')}\n\n"
    plain_body += f"Found {len(jobs)} new opportunities!\n\n"
    
    for i, job in enumerate(jobs, 1):
        plain_body += f"#{i} - {job['title']}\n"
        plain_body += f"Company: {job['company']}\n"
        plain_body += f"Link: {job['link']}\n"
        plain_body += f"Description: {job['desc']}\n\n"
        plain_body += "LinkedIn Message:\n"
        plain_body += linkedin_message(job)
        plain_body += "\n\n" + "="*50 + "\n\n"
    
    # Create multipart message
    msg = MIMEMultipart('alternative')
    msg["Subject"] = f"🔥 {len(jobs)} Laravel & CodeIgniter Jobs - {time.strftime('%b %d')}"
    msg["From"] = sender
    msg["To"] = recipient
    
    # Attach both plain and HTML versions
    msg.attach(MIMEText(plain_body, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))
    
    try:
        print("Connecting to Gmail SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        
        print("Logging in...")
        server.login(sender, password)
        
        print("Sending email...")
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully to {recipient}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed! Check your EMAIL_USER and EMAIL_PASS")
        print("Make sure you're using a Gmail App Password, not your regular password")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == "__main__":
    print("Starting job search automation...")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch jobs
    jobs = fetch_jobs()
    
    if not jobs:
        print("⚠️ No jobs found today.")
        # Still send an email to confirm the script ran
        sender = os.getenv("EMAIL_USER")
        msg = MIMEText("The job search automation ran but found no new Laravel or CodeIgniter jobs today. The script is working correctly!")
        msg["Subject"] = "ℹ️ Job Alert - No New Jobs Today"
        msg["From"] = sender
        msg["To"] = sender
        
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender, os.getenv("EMAIL_PASS"))
            server.send_message(msg)
            server.quit()
            print("Notification email sent.")
        except Exception as e:
            print(f"Could not send notification: {e}")
        
        exit(0)
    
    # Send email with jobs
    success = send_email(jobs)
    
    if success:
        print("✅ Job alert completed successfully!")
    else:
        print("❌ Job alert completed with errors")
        exit(1)