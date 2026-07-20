# Job Scout AI

An automated Python job-search assistant that finds junior data roles, scores them based on configurable criteria, compares job descriptions against a master CV, calculates ATS compatibility, and generates truthful tailored CVs.

---

# Project Overview

Job Scout AI automates the repetitive parts of a job search while keeping every generated application truthful and under the user's control.

The application:

- Fetches job listings
- Scores jobs based on relevance
- Filters junior opportunities
- Calculates ATS compatibility
- Detects matching skills
- Generates tailored DOCX CVs
- Tracks previously seen jobs
- Produces CSV & HTML reports
- Sends email notifications

---

# Current Features

- Job fetching
- Job relevance scoring
- ATS keyword matching
- Multi-word technical phrase detection
- Duplicate keyword prevention
- SQLite job history
- New-job detection
- CSV report generation
- HTML report generation
- Email notifications
- Automatic tailored CV generation
- Truthful skill filtering
- Safe company/job-title filenames

---

# Architecture

```text
                   Configuration
                         │
                         ▼
                  Job Search API
                         │
                         ▼
                 Job Fetching Engine
                         │
                         ▼
                 Job Scoring Engine
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
     ATS Matching                 SQLite Database
          │                             │
          ▼                             ▼
   CV Tailoring Engine          Seen Job Tracking
          │
          ▼
    DOCX CV Generator
          │
          ▼
 CSV Report • HTML Report • Email
```

---

# Project Structure

```text
job-scout-ai/
│
├── config/
├── data/
├── docs/
├── outputs/
│   └── tailored_cvs/
├── reports/
├── screenshots/
├── src/
│   ├── cv/
│   │   ├── generator.py
│   │   ├── keywords.py
│   │   ├── parser.py
│   │   ├── scorer.py
│   │   └── tailor.py
│   │
│   └── job_scout.py
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

# CV Tailoring Workflow

```text
Master CV                      Job Description
    │                                 │
    ▼                                 ▼
CV Text Extraction            Job Text Extraction
    │                                 │
    ▼                                 ▼
CV Keyword Detection         Job Keyword Detection
    │                                 │
    └──────────────┬──────────────────┘
                   │
                   ▼
          ATS Match Calculation
                   │
                   ▼
         Matching Skills Selection
                   │
                   ▼
          Truthful CV Tailoring
                   │
                   ▼
            Tailored DOCX CV
```

The system only uses skills that already exist in the master CV.

It never invents experience, technologies, or qualifications.

---

# Main Pipeline

```text
Load Configuration
        │
        ▼
Load Master CV
        │
        ▼
Extract CV Keywords
        │
        ▼
Fetch Jobs
        │
        ▼
Score Jobs
        │
        ▼
Calculate ATS Match
        │
        ▼
Filter Relevant Jobs
        │
        ▼
Detect New Jobs
        │
        ▼
Generate Tailored CVs
        │
        ▼
Generate Reports
        │
        ▼
Send Email
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/natanlts-sketch/job-scout-ai.git
cd job-scout-ai
```

Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials.

---

# Running

```bash
python -m src.job_scout
```

---

# Generated Output

Tailored CVs

```text
outputs/tailored_cvs/
```

Reports

```text
reports/
```

---

# Technologies

- Python
- SQLite
- python-docx
- REST APIs
- HTML
- CSV
- Email Automation
- Git
- GitHub

---

# Completed Roadmap

- [x] Job fetching
- [x] Job scoring
- [x] ATS score calculation
- [x] CV parsing
- [x] Keyword extraction
- [x] Technical phrase recognition
- [x] Duplicate keyword prevention
- [x] SQLite database
- [x] Seen-job tracking
- [x] CSV reports
- [x] HTML reports
- [x] Email reports
- [x] Automatic DOCX generation
- [x] Truthful skill matching
- [x] Git integration
- [x] GitHub integration

---

# Next Milestones

## Smart CV Tailoring

- [ ] Rewrite professional summary
- [ ] Reorder skills automatically
- [ ] Prioritize relevant projects
- [ ] Preserve one-page layout
- [ ] Improve formatting

## AI Integration

- [ ] OpenAI / Claude integration
- [ ] AI-generated summaries
- [ ] AI-generated cover letters
- [ ] Truthfulness validation

## Application Package

- [ ] PDF export
- [ ] Cover letter generation
- [ ] Application folder
- [ ] Metadata tracking

## Dashboard

- [ ] Search Now button
- [ ] Jobs dashboard
- [ ] ATS dashboard
- [ ] Download CV
- [ ] Generate cover letter
- [ ] Application tracking

## Analytics

- [ ] Interview tracking
- [ ] Reply rate
- [ ] ATS performance
- [ ] Best keywords
- [ ] Best companies

---

# Why This Project?

Most job-search tools only scrape vacancies.

Job Scout AI goes further by helping users identify relevant jobs, measuring ATS compatibility, generating truthful tailored CVs, organizing application data, and automating repetitive tasks while keeping the user in control.

---

# Future Vision

```text
Jobs
   │
   ▼
Job Scout AI
   │
   ├── Score Jobs
   ├── ATS Analysis
   ├── Tailor CV
   ├── Generate Cover Letter
   ├── Export PDF
   ├── Dashboard
   └── Application Tracking
```

---

# Author

**Natan Mamedov**

Junior Data Analyst | Python | SQL | Tableau | Data Automation

Building practical automation tools and data-driven solutions while transitioning into Data Analytics.
