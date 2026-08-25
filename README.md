# Uptime Watcher

Pings your live sites daily and emails you **only when something
changes** — a site goes down, or comes back up. No email at all on a
normal day where everything's fine, and no repeat "still down"
spam while an outage is ongoing. Run entirely on GitHub Actions
(no server needed).

Currently watching:
- **Portfolio** — https://damien222201.github.io/my-portfolio/
- **HeXeNe Website** — https://damien222201.github.io/HeXeNe-Website/

## Setup

1. **Create a Gmail App Password** (skip if you already have one from
   another project — you can reuse it)
   - Go to your Google Account → Security → 2-Step Verification (must be on)
   - Then Security → App passwords → generate one for "Mail"
   - Copy the 16-character password

2. **Push this repo to GitHub**

3. **Add repository secrets**
   Go to your repo → Settings → Secrets and variables → Actions → New repository secret, and add:

   | Secret name     | Value                                  |
   |-----------------|-----------------------------------------|
   | `SMTP_USER`     | your Gmail address                     |
   | `SMTP_PASSWORD` | the Gmail App Password                 |
   | `EMAIL_TO`      | the email address(es) to send alerts to (comma-separated for multiple) |

4. **Set workflow permissions**
   Go to Settings → Actions → General → Workflow permissions → select
   **"Read and write permissions"**. This is required because the
   workflow commits `last_status.json` back to the repo after each run.

5. **Test it manually**
   Go to the "Actions" tab → "Daily Uptime Watcher" → "Run workflow"
   to trigger it immediately. If both sites are up, you won't get an
   email — check the run's log instead to confirm it worked (it'll
   say "No status changes — skipping email.").

## Adding or changing sites

Edit the `SITES` dictionary near the top of `main.py`:

```python
SITES = {
    "Portfolio": "https://damien222201.github.io/my-portfolio/",
    "HeXeNe Website": "https://damien222201.github.io/HeXeNe-Website/",
}
```

Add more `"Name": "https://..."` entries as needed.

## Schedule

Runs daily at **5:00 AM UTC (6:00 AM WAT)** via the cron in
`.github/workflows/daily-uptime-watcher.yml`. Edit the `cron` line
there to change the time, or add more schedule entries if you want
multiple checks per day (e.g. every 6 hours) — GitHub Actions cron is
always in UTC.

## Local testing

```bash
pip install -r requirements.txt
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=you@gmail.com
export SMTP_PASSWORD=your_app_password
export EMAIL_TO=you@gmail.com
python main.py
```

## Notes

- On the very first run, if a site happens to already be down, you'll
  get an alert immediately (not silently skipped) — otherwise a real
  outage on day one would go unnoticed until it recovers.
- GitHub Pages sites are generally very reliable, so this is mostly
  useful as a safety net and a good template if you later add
  Render-hosted apps (like CureLearn) which can occasionally spin down
  on free tiers.
