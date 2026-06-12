# Future University LIMS — Startup Guide

## Every time you start working:

### Window 1 — Docker (run in D:\lab_sys)
docker compose up -d

### Window 2 — Django backend (run in D:\lab_sys\backend)
py -3.11 manage.py runserver

### Window 3 — React frontend (run in D:\lab_sys\frontend)
npm run dev

## URLs
- Main app:     http://localhost:5173
- Django admin: http://localhost:8000/admin  (admin / FutureUniv2025!)
- Senaite LIMS: http://localhost:8081        (admin / admin)
- API:          http://localhost:8000/api

## Stop everything
docker compose down
