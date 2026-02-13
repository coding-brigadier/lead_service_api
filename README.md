Lead Service API

A FastAPI application that allows prospects to submit leads (public endpoint) and attorneys to manage them via an authenticated internal API.

## Quick Start with Docker Compose

```bash
docker-compose up --build
```

This starts the app on `http://localhost:8000` and a PostgreSQL database.

### Seed an internal user

```bash
docker-compose exec app python -m scripts.seed
```

Default credentials: `admin@alma.com` / `changeme123`

## Local Development (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL running locally

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and edit environment variables
cp .env.example .env
# Edit .env with your database URL and secrets

# Run database migrations
alembic upgrade head

# Seed an internal user
python -m scripts.seed

# Start the server
uvicorn app.main:app --reload
```

## API Endpoints

### Public

| Method | Path     | Description               |
|--------|----------|---------------------------|
| POST   | `/leads` | Submit a new lead         |

Submit a lead with `multipart/form-data`: `first_name`, `last_name`, `email`, `resume` (file: PDF/DOC/DOCX).

### Internal (JWT-protected)

| Method | Path             | Description            |
|--------|------------------|------------------------|
| POST   | `/auth/login`    | Get a JWT token        |
| GET    | `/leads`         | List leads (paginated) |
| GET    | `/leads/{id}`    | Get a single lead      |
| PATCH  | `/leads/{id}`    | Update lead state      |

### Example workflow

```bash
# 1. Submit a lead (public)
curl -X POST http://localhost:8000/leads \
  -F "first_name=Jane" \
  -F "last_name=Doe" \
  -F "email=jane@example.com" \
  -F "resume=@resume.pdf"

# 2. Log in
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@alma.com", "password": "changeme123"}'

# 3. List leads (use token from step 2)
curl http://localhost:8000/leads \
  -H "Authorization: Bearer <token>"

# 4. Update lead state
curl -X PATCH http://localhost:8000/leads/<lead-id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"state": "REACHED_OUT"}'
```

## Running Tests

Tests run against PostgreSQL (database `alma_test` by default).

```bash
# Create the test database (one-time)
createdb -U alma alma_test

# Run tests
pytest
```

Override the test database URL if needed:

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/my_test_db pytest
```

## File Storage

Resume uploads are stored differently depending on the environment:

| Environment | Backend                       | Config |
|-------------|-------------------------------|-----------------------------------|
| Local dev   | Local filesystem (`uploads/`) | `STORAGE_BACKEND=local` (default) |
| Staging     | S3                            | `STORAGE_BACKEND=s3`              |
| Production  | S3                            | `STORAGE_BACKEND=s3`              |

### Local (default)

Files are saved to the `UPLOAD_DIR` directory (defaults to `uploads/`). No additional setup needed.

### S3 (staging / production)

Set the following environment variables:

```bash
STORAGE_BACKEND=s3
S3_BUCKET=my-alma-bucket
S3_REGION=us-east-1
S3_PREFIX=resumes/          # optional key prefix
S3_ENDPOINT_URL=            # optional, for MinIO / LocalStack
```

AWS credentials are picked up from the standard chain (env vars, instance profile, etc.) via `aiobotocore`.

The `resume_path` stored in the database will be an `s3://bucket/key` URI when using S3, or a local file path when using local storage.

## Interactive API Docs

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI.
