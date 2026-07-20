# Junior Data Job Scout

A beginner-friendly Python portfolio project that collects job listings, scores them against your target role and skills, removes previously seen jobs, and creates a daily CSV and HTML report.

The first version uses the Remotive public API. Remotive requires applications using its data to link back to the original job listing and identify Remotive as the source.

## What this project demonstrates

- Working with a REST API
- JSON processing
- Data cleaning with pandas
- Keyword-based scoring
- SQLite storage and duplicate prevention
- HTML and CSV reporting
- Optional automated email delivery
- Task automation with Windows Task Scheduler or Linux cron

## Project structure

```text
junior-data-job-scout/
├── config.yaml
├── requirements.txt
├── .env.example
├── data/
├── reports/
└── src/
    └── job_scout.py
```

## Step 1 — Install Python

Use Python 3.11 or newer.

Check your version:

```bash
python --version
```

## Step 2 — Create a virtual environment

### Windows PowerShell

```powershell
cd junior-data-job-scout
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux

```bash
cd junior-data-job-scout
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Step 3 — Run the program

```bash
python src/job_scout.py
```

Open the generated HTML file inside the `reports` folder.

On the first run, matching jobs are marked as new. On later runs, SQLite remembers previously found listings and reports only newly discovered jobs.

## Step 4 — Customize your search

Edit `config.yaml`.

Useful changes:

- Add or remove job-title keywords
- Add Israeli cities
- Add skills from your CV
- Raise `minimum_score` to make matching stricter
- Change `max_age_days`

## Step 5 — Enable email reports

Copy `.env.example` to `.env`:

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux

```bash
cp .env.example .env
```

Set `EMAIL_ENABLED=true` and enter your email settings.

For Gmail, use a Google App Password rather than your normal account password.

## Step 6 — Schedule it every morning

### Windows Task Scheduler

1. Open **Task Scheduler**.
2. Select **Create Basic Task**.
3. Name it `Junior Data Job Scout`.
4. Choose **Daily**.
5. Set the desired morning time.
6. Choose **Start a program**.
7. Program: full path to `.venv\Scripts\python.exe`
8. Arguments: full path to `src\job_scout.py`
9. Start in: full path to the project folder.

### Linux cron

Run:

```bash
crontab -e
```

Example for every day at 08:00:

```cron
0 8 * * * /full/path/junior-data-job-scout/.venv/bin/python /full/path/junior-data-job-scout/src/job_scout.py
```

## Suggested learning milestones

### Version 1 — Starter
Run the included program and understand every function.

### Version 2 — Better filtering
Add separate scores for title, location, skills, and experience.

### Version 3 — Multiple sources
Add another permitted API or company career-page feed. Normalize its results into the `Job` class.

### Version 4 — Dashboard
Build a Streamlit dashboard showing:
- New jobs by day
- Companies hiring most often
- Most requested skills
- Average match score
- Locations and remote availability

### Version 5 — CV matching
Read skills from your CV and calculate a more advanced job-match score.

## GitHub portfolio checklist

- Add screenshots of the HTML report
- Explain the problem and solution
- Add an architecture diagram
- Document the scoring rules
- Include a sample report without personal information
- Add tests
- Never upload your `.env` file or passwords

## Important note

Prefer official APIs, RSS feeds, and permitted public feeds. Do not scrape websites that prohibit automated access. Always follow the source's terms and link users to the original listing.
