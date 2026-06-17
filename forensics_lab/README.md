# Cloud-Based Digital Forensics Lab — Phase 1 (Local Docker Setup)

## Quick Start (Windows + Docker Desktop)

1. Install Docker Desktop, Python 3.11+, Git, VS Code (see chat for full install guide)
2. Open this folder in VS Code, open terminal (Ctrl + `)
3. Run:
   ```
   docker-compose up --build
   ```
4. In a second terminal:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```
5. Open MinIO console at http://localhost:9001 (minioadmin / minioadmin123) and create a bucket named `evidence`
6. Open the app at http://localhost:8000

## URLs
- App: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- MinIO Console: http://localhost:9001
- Flower (Celery monitor): http://localhost:5555

## Project Structure
- `apps/accounts` — auth, roles, audit log
- `apps/cases` — case management, dashboard
- `apps/evidence` — file upload, hashing, chain of custody
- `apps/analysis` — Celery tasks: YARA scan, string extraction, metadata
- `apps/reports` — HTML + PDF report generation
- `apps/audit` — audit log views

## Daily Commands
```
docker-compose up          # start
docker-compose down        # stop
docker-compose logs -f web # view logs
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```
