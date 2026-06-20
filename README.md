# Cloud-Based Digital Forensics Lab

A full-stack web platform for managing digital forensic investigations — built with Django, Celery, and Docker. It lets investigators upload digital evidence, automatically analyse it for malware and tampering, track a legally defensible chain of custody, and generate court-ready PDF reports.

## Why this project

Digital forensic investigations face three recurring problems: evidence can be challenged in court if its integrity isn't provably intact, manual file analysis is slow and error-prone, and there is often no reliable audit trail of who accessed what evidence and when. This project addresses all three by automating hash verification, malware scanning, and custody logging from the moment evidence is uploaded.

## Features

- **Case Management** — create, assign, and track investigations with status and priority workflows
- **Evidence Ingestion** — file uploads are automatically fingerprinted with MD5 and SHA-256 hashes on arrival, proving the file hasn't been altered
- **Automated Forensic Analysis** — background Celery tasks run YARA malware scanning, file type detection, string extraction, and metadata parsing without blocking the UI
- **Chain of Custody** — every action on a piece of evidence (upload, analysis, download, verification) is logged in an append-only audit trail that cannot be edited or deleted
- **Role-Based Access Control** — Admin, Investigator, Analyst, and Viewer roles with different permissions
- **Report Generation** — one-click PDF export summarising case details, evidence hashes, analysis findings, and the full custody log
- **Cloud-Ready Storage** — file storage uses an S3-compatible API (MinIO locally, AWS S3 in production) so the same code runs in both environments

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Django REST Framework |
| Background tasks | Celery + Redis |
| Database | PostgreSQL |
| File storage | MinIO (dev) / AWS S3 (production) |
| Forensic tooling | yara-python, python-magic, hashlib |
| Reports | WeasyPrint (PDF generation) |
| Containerisation | Docker, Docker Compose |
| Task monitoring | Flower |

## Architecture

```
Browser → Django (views + REST API) → PostgreSQL (cases, users, audit log)
                ↓
          Celery + Redis (async analysis queue)
                ↓
     YARA scan / hashing / metadata extraction
                ↓
          MinIO / S3 (evidence file storage)
```

## Getting Started

### Prerequisites
- Docker Desktop
- Git

### Run locally

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
docker-compose up --build
```

In a second terminal, create an admin account:

```bash
docker-compose exec web python manage.py createsuperuser
```

Open the MinIO console at `http://localhost:9001` (`minioadmin` / `minioadmin123`) and create a bucket named `evidence`.

### Access points

| Service | URL |
|---|---|
| Application | http://localhost:8000 |
| Django Admin | http://localhost:8000/admin |
| MinIO Console | http://localhost:9001 |
| Flower (task monitor) | http://localhost:5555 |

## Project Structure

```
apps/
├── accounts/   — authentication, roles, audit logging
├── cases/      — case management and dashboard
├── evidence/   — file upload, hashing, chain of custody
├── analysis/   — Celery tasks: YARA scanning, metadata, string extraction
├── reports/    — HTML and PDF report generation
└── audit/      — audit trail views
```

## Roadmap

- [x] Phase 1 — Core Django application (local Docker environment)
- [ ] Phase 2 — AWS migration (RDS, S3, ElastiCache, EC2)
- [ ] Phase 3 — Production deployment (CI/CD, SSL, CloudWatch monitoring)

## License

This project is for educational purposes.
