"""
Daily uptime watcher.

Pings a list of your live sites, compares against their last known
status (tracked in last_status.json in this repo), and emails an
alert via SMTP only when a site's status CHANGES — goes down, or
comes back up. No email is sent on days where nothing changed, to
avoid daily noise.

Environment variables (set as GitHub Actions secrets):
    SMTP_HOST       e.g. smtp.gmail.com
    SMTP_PORT       e.g. 587
    SMTP_USER       the Gmail address sending the email
    SMTP_PASSWORD   a Gmail App Password (NOT your normal password)
    EMAIL_TO        address(es) to send the alert to (comma-separated ok)
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

SITES = {
    "Portfolio": "https://damien222201.github.io/my-portfolio/",
    "HeXeNe Website": "https://damien222201.github.io/HeXeNe-Website/",
}

REQUEST_TIMEOUT_SECONDS = 15
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_status.json")


def check_site(url: str) -> tuple[bool, str]:
    """Returns (is_up, detail_message)."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        if resp.status_code < 400:
            return True, f"HTTP {resp.status_code}"
        return False, f"HTTP {resp.status_code}"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"


def load_last_status() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_last_status(data: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def build_email_body(changes: list) -> tuple[str, str]:
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    text_lines = [f"Uptime Alert — {today}\n"]
    html_rows = []

    for name, url, is_up, detail in changes:
        status_str = "✅ BACK UP" if is_up else "🔴 DOWN"
        color = "#1a9c4c" if is_up else "#d13c3c"

        text_lines.append(f"{status_str} — {name} ({url})")
        text_lines.append(f"  {detail}\n")

        html_rows.append(
            f"""
            <div style="border-left:4px solid {color};padding:10px 14px;margin-bottom:10px;background:#fafafa;">
              <p style="margin:0;font-weight:bold;color:{color};">{status_str} — {name}</p>
              <p style="margin:2px 0 0 0;font-size:13px;color:#555;">{url}</p>
              <p style="margin:2px 0 0 0;font-size:12px;color:#888;">{detail}</p>
            </div>
            """
        )

    text_body = "\n".join(text_lines)

    html_body = f"""\
<html>
  <body style="font-family:Arial,sans-serif;background:#f7f7f7;padding:20px;">
    <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;padding:24px;">
      <h2 style="margin-top:0;">📡 Uptime Alert</h2>
      <p style="color:#666;margin-top:-10px;">{today}</p>
      {''.join(html_rows)}
    </div>
  </body>
</html>
"""
    return text_body, html_body


def send_email(text_body: str, html_body: str, has_down: bool) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    email_to = os.environ["EMAIL_TO"]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject_prefix = "🔴 DOWN ALERT" if has_down else "✅ Recovered"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{subject_prefix} — Site Status Change — {today}"
    msg["From"] = smtp_user
    msg["To"] = email_to

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email_to.split(","), msg.as_string())


def main():
    last_status = load_last_status()
    current_status = {}
    changes = []

    for name, url in SITES.items():
        is_up, detail = check_site(url)
        current_status[name] = {"up": is_up, "detail": detail}

        previous = last_status.get(name, {})
        previous_up = previous.get("up")  # None on first run

        # Alert only when status changed since last check (or first-ever
        # down detection). Don't alert on first run if the site is up —
        # that's the normal, unremarkable case.
        if previous_up is None:
            if not is_up:
                changes.append((name, url, is_up, detail))
        elif previous_up != is_up:
            changes.append((name, url, is_up, detail))

    save_last_status(current_status)

    if not changes:
        print("No status changes — skipping email.")
        return

    has_down = any(not is_up for _, _, is_up, _ in changes)
    text_body, html_body = build_email_body(changes)

    try:
        send_email(text_body, html_body, has_down)
    except Exception as e:
        print(f"Failed to send email: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Email sent successfully with {len(changes)} status change(s).")


if __name__ == "__main__":
    main()
