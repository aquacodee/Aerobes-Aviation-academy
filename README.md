# AeroNex Aviation Academy Management System

A branded public website and Flask/PostgreSQL registration and academy administration platform, powered by Daudrone.

## Stack
- Flask 3, SQLAlchemy, Flask-Migrate, JWT, Flask-Limiter, PostgreSQL
- React, Vite, TypeScript, Tailwind, React Router, React Hook Form dependencies, Recharts
- Docker Compose, Gunicorn

## Quick start (Docker)
1. Copy `backend/.env.example` to `backend/.env`.
2. Change `SECRET_KEY`, `JWT_SECRET_KEY`, and `ADMIN_PASSWORD` before use.
3. From the project root run: `docker compose up --build -d`.
4. Seed the database and initial administrator:
   `docker compose exec api python seed.py`
5. Open the public website at http://localhost:5173.
6. Open administration at http://localhost:5173/admin/login.
7. Sign in with `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `backend/.env`.

The seed command creates the seven configured programmes and the initial superadmin only when absent. Change the initial password immediately after first login; the initial credentials are bootstrap credentials, not production defaults.

## Local development without Docker
Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
flask --app run.py run --debug
```
Frontend:
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_URL` if the API is not at `http://localhost:5000/api/v1`.

## Database migrations
```bash
cd backend
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
```
For a new installation, `seed.py` currently creates tables for a quick local bootstrap. Use migrations for ongoing schema changes and production.

## API
Public:
- `GET /api/v1/programmes`
- `POST /api/v1/applicants`
- `POST /api/v1/enquiries`

Authentication:
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Admin endpoints require `Authorization: Bearer <access_token>`:
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/applicants?search=&status=&page=1&per_page=20`
- `GET /api/v1/admin/applicants/<id>`
- `PATCH /api/v1/admin/applicants/<id>`
- `PATCH /api/v1/admin/applicants/<id>/status`
- `POST /api/v1/admin/applicants/<id>/notes`
- `POST /api/v1/admin/applicants/<id>/enrol`
- `GET /api/v1/admin/students`
- `PATCH /api/v1/admin/students/<id>`
- `GET|POST /api/v1/admin/programmes`
- `PATCH /api/v1/admin/programmes/<id>`
- `GET|POST /api/v1/admin/cohorts`
- `GET|POST /api/v1/admin/certificates`
- `GET /api/v1/admin/reports`
- `GET /api/v1/admin/exports/applicants`

## Important production work before launch
This codebase is a functional development foundation, not a security-audited deployment. Before accepting real student data:
- Use HTTPS behind Nginx and set secure production cookies/headers.
- Move JWT from localStorage to an HttpOnly Secure SameSite cookie and add CSRF protection, or use a carefully managed short-lived token/refresh strategy.
- Implement admin password change/reset, account lockout, MFA and session revocation.
- Configure durable rate-limit storage (Redis), email provider, backups, monitoring and error reporting.
- Add object storage for programme images and generated certificate PDFs, plus authenticated certificate verification/download.
- Add full CRUD and detail screens for students, programmes, enquiries, cohorts and certificates; the current dashboard includes complete registration workflow and API foundations, while several secondary admin pages are list-data placeholders.
- Complete audit logging coverage, field-level validation, retention policy, privacy notice and consent review.
- Review licensing/exam-preparation wording with the relevant GCAA requirements. AeroNex completion certificates are not official pilot licences or evidence of GCAA accreditation.

## Notes
- The supplied official logo artwork was extracted from the AeroNex brand board and placed in `frontend/public/`.
- Demo records are not seeded. Only the initial admin and seven programme definitions are created.
- Public duplicate protection checks the same phone number within a 24-hour window; it returns the prior registration reference rather than creating a second record.
- Admin notifications are a provider integration hook only; configure and implement SMTP/provider delivery before production.
