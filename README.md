<div align="center">

# AI-Assisted Exam Platform

### A class-centric platform for creating, grading, reviewing, and publishing exams with responsible AI assistance

[![Project Status](https://img.shields.io/badge/status-in%20development-F59E0B?style=for-the-badge)](#project-status)
[![API](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](#tech-stack)
[![Web](https://img.shields.io/badge/Web-Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](#tech-stack)
[![Database](https://img.shields.io/badge/Database-PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](#tech-stack)

</div>

> [!IMPORTANT]
> This project is under active development and is not production-ready yet. Data models, API contracts, background jobs, and UI flows may change as the product is stabilized.

## Table of Contents

- [Overview](#overview)
- [Project Status](#project-status)
- [Features](#features)
- [Product Workflow](#product-workflow)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Manual Service Setup](#manual-service-setup)
- [External Services](#external-services)
- [Local Service URLs](#local-service-urls)
- [Testing and Quality Checks](#testing-and-quality-checks)
- [Roadmap](#roadmap)
- [Security Notes](#security-notes)
- [Contributing](#contributing)

## Overview

AI-Assisted Exam Platform is a monorepo application for managing the full exam lifecycle inside a classroom workflow. Teachers can create classes, manage students, build exams, schedule exam windows, send student-specific access links, review AI-assisted grading, publish results, and handle appeals.

The product is designed around a human-in-the-loop grading model. Objective questions are graded deterministically, while short-answer and essay responses can be evaluated with an AI provider. The teacher remains the final authority for reviewing low-confidence answers, adjusting grades, approving results, and responding to appeals.

Core workflow:

```text
Create exam -> Invite students -> Run exam -> Grade automatically -> Teacher review -> Publish results -> Handle appeals
```

## Project Status

| Area | Current State |
|---|---|
| Development stage | Active development |
| API version | `0.1.0` |
| Main exam flow | Implemented and being stabilized |
| Web application | Implemented and being refined |
| AI grading | Mock provider and Google Gemini provider |
| Email delivery | Mock, SMTP, and Gmail-compatible configuration |
| Production readiness | Not ready yet |

The main flow from teacher registration to result publication and appeals is already present. The next development focus is stability, broader test coverage, UI polish, operational security, and deployment readiness.

## Features

| Area | Capability | Status |
|---|---|:---:|
| Authentication | Teacher sign-up, login, logout, and cookie-based sessions | Done |
| Class management | Create, view, update, and delete classes | Done |
| Student management | Add and manage students inside each class | Done |
| Exam setup | Configure title, description, total score, and result visibility rules | Done |
| Exam blueprint | Define counts for multiple-choice, true/false, short-answer, and essay questions | Done |
| Question builder | Save drafts, set scores, define correct answers, add grading guidance, and create rubrics | Done |
| AI assistance | Suggest essay rubrics with teacher approval before use | Done |
| Readiness checks | Validate question completion, score totals, and exam finalization | Done |
| Scheduling | Set start/end windows, exam duration, and student-specific access links | Done |
| Invitations | Queue exam invitation emails | Done |
| Exam taking | Token-based access, timer support, and backend time-window validation | Done |
| Objective grading | Deterministic grading for multiple-choice and true/false questions | Done |
| AI grading | Score and provide feedback for short-answer and essay responses | Done |
| Teacher review | Route low-confidence answers to the teacher and allow grade overrides | Done |
| Audit trail | Store grading source, review status, and grade-change history | Done |
| Result publishing | Publish student result links with configurable feedback and answer visibility | Done |
| Leaderboard | Provide class-scoped ranking and public result views | Done |
| Appeals | Allow students to appeal one answer or the full exam; allow teachers to resolve appeals | Done |
| Background jobs | Separate queues for grading, AI work, email, and leaderboard updates | Done |

## Product Workflow

| Step | Actor | Description |
|---:|---|---|
| 1 | Teacher | Register, create a class, and add students |
| 2 | Teacher | Create an exam, define the blueprint, and complete the questions |
| 3 | System | Check readiness, validate score totals, and finalize the exam |
| 4 | Teacher | Schedule the exam and send invitations |
| 5 | Student | Open the private exam link and submit answers within the allowed window |
| 6 | Worker | Grade objective answers and evaluate written responses |
| 7 | Teacher | Review sensitive or low-confidence answers and approve results |
| 8 | System | Publish result links and update leaderboard data |
| 9 | Student / Teacher | Submit, review, and resolve appeals |

## Architecture

| Source | Target | Responsibility |
|---|---|---|
| Teacher / Student | Next.js Web App | User-facing teacher dashboard and student exam experience |
| Next.js Web App | FastAPI REST API | Authenticated requests, data loading, mutations, and session handling |
| FastAPI REST API | PostgreSQL | Persistent storage for users, classes, exams, submissions, grades, and appeals |
| FastAPI REST API | Redis | Queue broker and task-state backend |
| Redis | Celery Worker | Asynchronous execution of long-running jobs |
| Celery Worker | PostgreSQL | Persist grading output, result state, leaderboard data, and logs |
| Celery Worker | Mock / Gemini | AI-assisted evaluation for written responses |
| Celery Worker | Mock / SMTP / Gmail | Email invitations, exam links, and result notifications |

This is a monorepo architecture. The API handles synchronous application workflows, while time-consuming jobs such as AI grading, email delivery, and leaderboard updates are delegated to Celery workers.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Frontend state and data | TanStack Query, Zustand |
| Forms and validation | React Hook Form, Zod |
| Backend | Python, FastAPI, Pydantic |
| ORM and migrations | SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 |
| Queue and cache | Redis 7, Celery 5 |
| AI provider | Google Gemini and mock provider |
| Email provider | SMTP, Gmail-compatible SMTP, and mock provider |
| Testing | Pytest |
| Local infrastructure | Docker Compose, PowerShell |
| Package manager | pnpm workspace |

## Project Structure

```text
exam_product/
|-- apps/
|   |-- api/                 # FastAPI application, domain modules, and migrations
|   |   |-- alembic/
|   |   `-- app/
|   |       |-- api/
|   |       |-- core/
|   |       |-- db/
|   |       |-- infrastructure/
|   |       `-- modules/
|   |-- web/                 # Next.js web application
|   |   |-- app/
|   |   |-- components/
|   |   |-- features/
|   |   |-- lib/
|   |   `-- types/
|   `-- worker/              # Celery workers and background tasks
|       |-- services/
|       `-- tasks/
|-- infra/                   # Infrastructure and deployment-related configuration
|-- scripts/dev/             # Windows development runner scripts
|-- tests/                   # Backend and workflow tests
|-- docker-compose.yml       # PostgreSQL and Redis
|-- pnpm-workspace.yaml
|-- .env.example
`-- README.md
```

## Quick Start

### Prerequisites

| Tool | Recommended Version | Purpose |
|---|---:|---|
| Git | Stable | Clone and manage the repository |
| Python | `3.11+` | Run the API and worker |
| Node.js | `20+` | Run the web application |
| pnpm | `11.0.9` | Manage frontend dependencies |
| Docker | Stable | Run PostgreSQL and Redis locally |
| PowerShell | `5.1+` | Use the Windows runner scripts |

### 1. Clone the repository

```powershell
git clone https://github.com/MrAshki/exam_product.git
cd exam_product
```

### 2. Create local environment variables

```powershell
Copy-Item .env.example .env
```

Before using the project seriously, replace `SECRET_KEY` in `.env` with a strong random value. By default, AI and email providers use mock mode, so local development does not call external services or send real emails.

### 3. Install dependencies

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt
pnpm install
```

### 4. Run the full stack on Windows

```powershell
.\run-all.cmd
```

This command starts PostgreSQL and Redis, applies database migrations, and opens the API, worker, and web application in separate terminals. The browser opens automatically.

Stop application processes:

```powershell
.\stop-all.cmd
```

Stop application processes and Docker services:

```powershell
.\stop-all.cmd -StopInfrastructure
```

### Runner Options

| Command | Purpose |
|---|---|
| `.\run-all.cmd` | Start the stack with safe mock AI and mock email providers |
| `.\run-all.cmd -Clean` | Clear Next.js cache before starting |
| `.\run-all.cmd -NoBrowser` | Start without opening the browser |
| `.\run-all.cmd -NoWorker` | Start without the Celery worker |
| `.\run-all.cmd -UseConfiguredAI` | Use the AI provider configured in `.env` |
| `.\run-all.cmd -UseConfiguredEmail` | Use the email provider configured in `.env` |
| `.\run-all.cmd -UseConfiguredProviders` | Use both configured AI and email providers |
| `.\run-all.cmd -CheckConfiguredProviders` | Validate provider configuration without starting services |

> [!WARNING]
> `UseConfigured...` options can consume AI quota or send real emails. Use the default mock providers for everyday local development.

## Manual Service Setup

If you are not using the Windows runner, start services manually in separate terminals.

### Infrastructure and migrations

```bash
docker compose up -d
cd apps/api
../../.venv/Scripts/python -m alembic upgrade head
```

On Linux and macOS, use `.venv/bin/python` instead of `.venv/Scripts/python`.

### API

```bash
cd apps/api
../../.venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8081
```

### Worker

```bash
.venv/Scripts/python -m celery -A apps.worker.worker:celery_app worker --loglevel=INFO --pool=solo
```

### Frontend

```bash
pnpm --filter web dev
```

## External Services

Full configuration options and defaults are available in [`.env.example`](./.env.example).

| Group | Important Variables | Description |
|---|---|---|
| Application | `PROJECT_NAME`, `APP_DEBUG`, `SECRET_KEY` | Main API settings |
| Sessions | `COOKIE_NAME`, `COOKIE_SECURE`, `COOKIE_SAMESITE` | Authentication cookie settings |
| Frontend | `FRONTEND_BASE_URL`, `NEXT_PUBLIC_API_BASE_URL` | Web and API base URLs |
| CORS | `BACKEND_CORS_ORIGINS` | Allowed origins, comma-separated |
| PostgreSQL | `DATABASE_URL` or `POSTGRES_*` variables | Database connection |
| Redis / Celery | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Queue broker and task result backend |
| AI | `AI_PROVIDER`, `AI_MODEL`, `GEMINI_API_KEY` | AI grading provider settings |
| Email | `EMAIL_PROVIDER`, `SMTP_*` variables | Email delivery provider settings |

Enable Gemini:

```dotenv
AI_PROVIDER=gemini
AI_MODEL=gemini-2.0-flash
GEMINI_API_KEY=your_api_key
```

Enable real email delivery by setting `EMAIL_PROVIDER` to `smtp` or `gmail` and completing the required `SMTP_*` values.

## Local Service URLs

| Service | Local URL |
|---|---|
| Frontend | <http://localhost:3000> |
| API | <http://localhost:8081> |
| Swagger UI | <http://localhost:8081/docs> |
| ReDoc | <http://localhost:8081/redoc> |
| Health Check | <http://localhost:8081/health> |
| PostgreSQL | `localhost:55432` |
| Redis | `localhost:16379` |

Use `localhost` consistently in browser-facing URLs. Mixing `localhost` and `127.0.0.1` can affect cookies and CORS behavior.

## Testing and Quality Checks

Run backend tests from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run frontend checks:

```bash
pnpm --filter web lint
pnpm --filter web typecheck
pnpm --filter web build
```

The current backend test suite covers authentication, migrations, student access, deterministic grading, AI-assisted grading, teacher review, result publication, leaderboard behavior, and appeals. AI-related tests use the mock provider and should not make real requests to Gemini.

## Roadmap

| Priority | Item | Status |
|:---:|---|:---:|
| High | Stabilize the full exam creation, delivery, grading, review, and publication flow | In progress |
| High | Expand integration and end-to-end test coverage | In progress |
| High | Improve production security, rate limits, and operational hardening | Planned |
| Medium | Improve UX, accessibility, and mobile responsiveness | Planned |
| Medium | Add richer class performance reports and analytics | Planned |
| Medium | Add printable/PDF exports for exams and reports | Planned |
| Low | Finalize deployment configuration, monitoring, and operations documentation | Planned |

## Security Notes

- `.env` is ignored by Git. Do not commit secrets, passwords, API keys, or tokens.
- Use a long, random `SECRET_KEY` outside local development.
- Enable `COOKIE_SECURE=true` in HTTPS environments.
- Restrict CORS origins to real application domains before deployment.
- Use mock providers for regular development and automated tests.
- AI output is not the final authority. Low-confidence or invalid responses must be reviewed by a teacher.
- Treat exam links and result links as sensitive information.

> [!CAUTION]
> The project has not completed production security review. Do not use real sensitive student data in development environments.

## Contributing

1. Create a focused branch for your change.
2. Keep changes small, scoped, and covered by relevant tests.
3. Run backend tests and frontend quality checks before opening a pull request.
4. Describe the problem, solution, and validation steps clearly in the pull request.

---

<div align="center">

Built around teacher control, transparent feedback, and responsible AI-assisted grading.

</div>
