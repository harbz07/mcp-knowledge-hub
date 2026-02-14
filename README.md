# Daily Email Report with GitHub Actions

This repository is configured to run a Python report script once per day on GitHub-hosted infrastructure (no local cron required).

## Project Layout

```text
daily-email-report/
├── daily_report.py
├── requirements.txt
└── .github/
    └── workflows/
        └── daily_report.yml
```

## How It Works

- `daily_report.py` generates a report and sends it via SMTP.
- GitHub Actions runs the script on a daily `cron` schedule.
- Credentials are read from GitHub Actions Secrets.

## Required GitHub Secrets

In your repository settings, add the following secrets under:
**Settings → Secrets and variables → Actions**

- `REPORT_SENDER_EMAIL` — sender email address.
- `REPORT_EMAIL_PASSWORD` — sender app password (e.g., Gmail app password).
- `REPORT_RECIPIENT_EMAIL` — recipient email address.

> Never commit credentials to this repository.

## Schedule and Time Zone

Workflow schedule is currently set to:

- `0 18 * * *` (18:00 UTC), which is **08:00 Hawaii time (UTC-10)**.

Update `.github/workflows/daily_report.yml` if you need a different send time.

## Manual Test Run

1. Open the **Actions** tab in GitHub.
2. Select **Daily Email Report**.
3. Click **Run workflow**.

If secrets are configured correctly, you should receive the email.

## Local Run (Optional)

Export required environment variables and run:

```bash
export REPORT_SENDER_EMAIL="you@example.com"
export REPORT_EMAIL_PASSWORD="app-password"
export REPORT_RECIPIENT_EMAIL="recipient@example.com"
python daily_report.py
```
