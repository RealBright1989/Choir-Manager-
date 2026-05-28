# Choir Manager 🎵

A full-featured choir management web application built with Flask, SQLAlchemy, and modern Python. Manage members, track attendance, handle finances, generate professional invoices/receipts, and export reports — all in one place.

## Features

| Feature | Description |
|---|---|
| 👥 **Member Management** | Add, edit, delete members with photo upload, NIN, passport, zones/areas, Nigerian state/LGA cascading dropdowns |
| 📋 **Attendance Tracking** | Mark Present/Absent/Excused per date, view history per member |
| 💰 **Finance Module** | Monthly income/expense statements, balance brought forward, closing balance |
| 📄 **Invoices & Receipts** | Create professional PDF invoices before payment, receipts after payment with logo and branding |
| 📊 **Reports & Exports** | Members, payments, attendance, hierarchy reports — Excel and PDF with logo |
| 🎵 **Songs Library** | Store song lyrics, composer info, upload audio files |
| 🔐 **Role-based Auth** | Admin, Treasurer, Viewer roles with session management |
| ⚙️ **Settings** | Choir name, currency, SMS (Twilio), SMTP email, social links |
| 📱 **Responsive** | Mobile-friendly sidebar with hamburger menu |
| 🔄 **Auto-backup** | Full data backup to Excel on every server start (last 10 kept) |
| 🌐 **REST API** | JSON endpoints for members, payments, invoices, attendance, stats |

## Tech Stack

```
Backend:    Python 3 · Flask · SQLAlchemy 2.0 · Alembic
Frontend:   Jinja2 · HTML/CSS · JavaScript
Database:   SQLite (dev) · PostgreSQL (production)
PDF:        fpdf2
Excel:      openpyxl
Testing:    pytest (32 tests)
DevOps:     Docker · docker-compose · GitHub Actions
```

## Quick Start

### Local Development

```bash
git clone https://github.com/RealBright1989/Choir-Manager-.git
cd Choir-Manager-
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000` — **default admin login:** `admin` / `admin123`

### Docker

```bash
docker-compose up -d
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask secret key | `change-this-to-a-random-secret` |
| `DATABASE_URL` | Database connection | `sqlite:///choir_web.db` |
| `PORT` | Server port | `5000` |

## API Endpoints

All API endpoints require authentication (session cookie).

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/members` | List all members |
| GET | `/api/members/<id>` | Single member details |
| GET | `/api/payments?member_id=` | List payments (optional filter) |
| GET | `/api/invoices` | List all invoices with items |
| GET | `/api/attendance?date=` | Attendance records (optional date) |
| GET | `/api/expenses` | List all expenses |
| GET | `/api/songs` | List all songs |
| GET | `/api/stats` | Dashboard statistics |

## Screenshots

> *Add screenshots here after deployment*

## Testing

```bash
pytest tests/ -v
```

## License

MIT
