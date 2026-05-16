# Lectra AI Backend

Backend API for Lectra AI platform.

## Tech Stack

- Django
- Django REST Framework
- PostgreSQL
- JWT Authentication

---

## Setup

### Clone Project

```bash
git clone https://github.com/Shabeebbv/lectra-ai-backend.git
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key

DEBUG=True

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Run Server

```bash
python manage.py runserver
```