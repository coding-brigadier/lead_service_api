# Design Document — Alma Lead Management

**Repository:** [https://github.com/coding-brigadier/lead_service_api](https://github.com/coding-brigadier/lead_service_api)

## Overview

This application provides a lead intake pipeline for a legal services firm. Prospects submit their information and resume through a public API, and internal attorneys manage those leads through an authenticated API.

## Architectural Decisions

### Framework: FastAPI

Chosen for its async-first design, automatic OpenAPI documentation, dependency injection system, and Pydantic integration for request validation.

### Database: PostgreSQL + Async SQLAlchemy

PostgreSQL is used in all environments (dev, test, staging, production). SQLAlchemy 2.0 with async support (`asyncpg` driver) provides an ORM layer. Alembic handles schema migrations. Tests run against a dedicated `alma_test` PostgreSQL database.

### Authentication: JWT (HTTP Bearer)

Internal endpoints are protected with JWT tokens issued via a login endpoint. Passwords are hashed with `bcrypt`. Tokens are signed with HS256 via `python-jose`. The login endpoint accepts a JSON body with `email` and `password` fields and returns a JWT token. Protected endpoints require the token in the `Authorization: Bearer <token>` header.

JWT was chosen over session-based auth because it is stateless and client-agnostic — any front-end (web or mobile) can authenticate by simply storing and sending the token, with no server-side session management required. This also makes the API horizontally scalable without shared session state.

### Email: aiosmtplib with Console Fallback

When `SMTP_HOST` is configured, emails are sent via SMTP. Otherwise, emails are logged to the console. This allows local development without an email provider while maintaining the same code paths.

Emails are sent as fire-and-forget background tasks so they don't block the API response.

### File Storage: Local or S3

Resumes are stored with UUID-based filenames to prevent collisions. File type validation restricts uploads to PDF, DOC, and DOCX.

The storage backend is configurable via `STORAGE_BACKEND`: local filesystem (`uploads/` directory) for development, S3 for staging and production. S3 is the go-to choice for file storage in production — it provides durability, scalability, and integrates naturally with AWS infrastructure. It also opens the door to features like signed URLs for secure downloads and lifecycle policies for retention management.

### Configuration: `.env` with pydantic-settings

All configuration is driven by environment variables loaded via `pydantic-settings` and `.env` files. This makes it straightforward to manage different environments (local, staging, production) — each environment simply uses its own `.env` or injects variables through the deployment platform (e.g. ECS task definitions, Kubernetes secrets). Sensitive values like `DATABASE_URL` and `SECRET_KEY` have no defaults and must be explicitly set, preventing accidental use of insecure fallbacks in production.

### Lead State Machine

Leads have two states: `PENDING` (default on creation) and `REACHED_OUT`. The transition is one-way — once marked as `REACHED_OUT`, a lead cannot return to `PENDING`. This enforces a simple, auditable workflow.

## Project Structure

```
app/
├── main.py          # App factory and lifespan
├── config.py        # Pydantic Settings (env vars)
├── database.py      # Async engine and session
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request/response schemas
├── api/             # Route handlers + dependency injection
├── services/        # Business logic (auth, leads, email)
└── utils/           # File upload handling
```

The layered architecture (routes → services → models) keeps concerns separated and makes individual components testable.

## API Design

- **Public endpoint** (`POST /leads`): Accepts `multipart/form-data` since it includes a file upload alongside form fields.
- **Internal endpoints**: Standard JSON request/response. Protected by JWT via FastAPI's dependency injection.
- **Pagination**: `GET /leads` uses cursor-based pagination with `cursor` and `limit` query parameters. The cursor encodes `(created_at, id)` for stable ordering.
- **State updates**: `PATCH /leads/{id}` accepts a partial update body with just the `state` field, following REST conventions for partial updates.
