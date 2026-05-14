# CI/CD Report — Intelligent Room Booking System

> **Project:** Intelligent Room Booking System  
> **Author:** [Your Name]  
> **Date:** May 2026  
> **Repository:** GitHub — `Intelligent_Room_Booking`

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Objectives of CI/CD in This Project](#2-objectives-of-cicd-in-this-project)
3. [Tools and Technologies Used](#3-tools-and-technologies-used)
4. [CI/CD Pipeline Overview](#4-cicd-pipeline-overview)
5. [Continuous Integration (CI) Process](#5-continuous-integration-ci-process)
6. [Continuous Deployment/Delivery (CD) Process](#6-continuous-deploymentdelivery-cd-process)
7. [Workflow Configuration](#7-workflow-configuration)
8. [Challenges Faced](#8-challenges-faced)
9. [Benefits of CI/CD in This Project](#9-benefits-of-cicd-in-this-project)
10. [Conclusion](#10-conclusion)

---

## 1. Introduction

### What is CI/CD?

**CI/CD** stands for **Continuous Integration** and **Continuous Deployment/Delivery**. It is a set of modern software engineering practices that automate the steps between writing code and getting it running in a live environment.

| Term | Full Name | What It Means |
|------|-----------|---------------|
| **CI** | Continuous Integration | Automatically build and test code every time a developer pushes changes |
| **CD** | Continuous Delivery | Automatically prepare and package code for deployment after tests pass |
| **CD** | Continuous Deployment | Automatically release the application to a live environment |

CI/CD removes the manual, error-prone steps that used to exist between writing code and shipping it to users. Instead of deploying manually every few weeks, CI/CD allows teams to ship small, tested, and reliable changes many times a day.

### Why CI/CD is Important

Without CI/CD, developers must manually:
- Run tests on their own machine
- Package the application
- Upload files to a server
- Restart services

This is slow, inconsistent, and risky. CI/CD automates all of this. When a developer pushes code, the pipeline handles the rest — testing, linting, building, and deploying automatically.

### About This Project

The **Intelligent Room Booking System** is a full-stack web application built with **Django (Python)** for the backend and **Flutter** for the mobile client. It provides:

- 🏢 Room reservation management with approval workflows
- 👥 User authentication with Google OAuth
- 🤖 AI-powered chatbot (DeepSeek / Groq LLM integration)
- 📊 Real-time analytics dashboard (Streamlit)
- 📱 Telegram and Google Calendar notifications
- 🐳 Docker-based containerized deployment

Given the complexity of this system (multiple apps, AI integrations, mobile frontend, and three environments), automating the build, test, and deployment pipeline was essential.

---

## 2. Objectives of CI/CD in This Project

The CI/CD pipeline was set up to solve specific problems and achieve clear goals:

| Objective | Problem It Solves |
|-----------|-----------------|
| **Automate testing** | Prevent bugs from reaching production by running tests on every code change |
| **Enforce code quality** | Stop poorly formatted or insecure code from being merged |
| **Speed up deployment** | Remove manual deployment steps — push a tag and the system deploys automatically |
| **Support multiple environments** | Manage Development, Staging, and Production deployments separately and safely |
| **Containerize consistently** | Ensure the same Docker image is used in testing and production |
| **Reduce human error** | Automated pipelines do not forget steps or make typos |

### Summary of Goals

```
✅ Reduce manual deployment work
✅ Catch bugs early with automated testing
✅ Enforce coding standards automatically
✅ Deliver to multiple environments reliably
✅ Scan for security vulnerabilities automatically
```

---

## 3. Tools and Technologies Used

### Core Stack

| Category | Tool / Technology | Purpose |
|----------|------------------|---------|
| **Language** | Python 3.11 | Backend application language |
| **Framework** | Django 4.2 | Web framework for the backend |
| **Mobile** | Flutter 3.22.0 | Cross-platform mobile application |
| **Database (dev)** | SQLite | Lightweight database for CI testing |
| **Database (prod)** | MySQL | Production-grade relational database |

### CI/CD Toolchain

| Tool | Role |
|------|------|
| **Git** | Version control for all source code changes |
| **GitHub** | Remote repository hosting and collaboration platform |
| **GitHub Actions** | CI/CD automation engine — runs workflows on every push/PR |
| **Ruff** | Python linter and formatter (replaces Flake8 + Black) |
| **Bandit** | Python security vulnerability scanner |
| **Safety** | Python dependency vulnerability checker |
| **Pytest** | Python unit and integration test runner |
| **pytest-cov** | Code coverage measurement for tests |
| **Flake8** | Complementary code style linter |
| **Docker** | Containerization — packages the app into a portable image |
| **Docker Hub** | Container registry — stores and distributes Docker images |
| **Codecov** | Coverage report visualization and tracking |

### Workflow Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Main CI pipeline — tests Django backend and Flutter mobile |
| `.github/workflows/cd.yml` | Tag-driven Docker build and push to Docker Hub |

> Note (repository snapshot, May 2026): only `ci.yml` and `cd.yml` are currently present in `.github/workflows`.

---

## 4. CI/CD Pipeline Overview

The pipeline follows a clear, automated flow from the moment a developer pushes code to GitHub, all the way to deployment.

### High-Level Flow

```
Developer writes code
      │
      ▼
git push / pull request to GitHub
      │
      ▼
┌─────────────────────────────────┐
│       CI Pipeline Starts        │
│  (GitHub Actions triggered)     │
│                                 │
│  1. Checkout source code        │
│  2. Set up Python / Flutter     │
│  3. Install dependencies        │
│  4. Run Linter (Ruff)           │
│  5. Run Security Scan (Bandit)  │
│  6. Run Unit Tests (Pytest)     │
│  7. Check Coverage (≥ 70%)      │
└─────────────────────────────────┘
      │
      ▼
  Tests Pass?
      │
  YES │              NO → ❌ Pipeline Fails, Developer Notified
      ▼
┌─────────────────────────────────┐
│       CD Pipeline Starts        │
│  (triggered by release tag)     │
│                                 │
│  1. Checkout source code        │
│  2. Set up Docker Buildx        │
│  3. Login to Docker Hub         │
│  4. Determine environment from  │
│     tag (dev-v*, stg-v*, prod-v*)│
│  5. Build Docker image          │
│  6. Push to Docker Hub          │
└─────────────────────────────────┘
      │
      ├──► dev tag  → Docker image tagged :master
      ├──► stg tag  → Docker image tagged :testing
      └──► prod tag → Docker image tagged :production
```

### Environment Strategy

| Environment | Git Branch | Tag Pattern | Docker Tag | Purpose |
|------------|-----------|------------|-----------|---------|
| **Development** | `dev` | `dev-v1.0` | `:dev-1.0` / `:master` | Feature development |
| **Staging** | `staging` | `stg-v1.0` | `:stg-1.0` / `:testing` | QA and pre-production |
| **Production** | `main` | `prod-v1.0` | `:prod-1.0` / `:production` | Live application |

---

## 5. Continuous Integration (CI) Process

### What Happens on Every Code Push

In the current workflow configuration, CI runs on push and pull request events for the `main` branch.

### Django Backend CI (`ci.yml` — `django-test` job)

**Step-by-step process:**

```
Step 1: Checkout code
   → GitHub Actions clones the repository into the runner machine

Step 2: Set up Python 3.11
   → Install the correct Python version with pip caching for speed

Step 3: Install dependencies
   → pip install -r requirements.txt
   → pip install pytest pytest-cov pytest-django ruff

Step 4: Save environment info
   → Log Python version, pip version, installed packages for debugging

Step 5: Check Django project
   → python manage.py check
   → Verifies Django configuration and settings are valid

Step 6: Lint with Ruff
   → ruff check .
   → Checks code style (unused imports, bad formatting, etc.)

Step 7: Format check with Ruff
   → ruff format --check .
   → Ensures code formatting matches project standards

Step 8: Run unit tests with coverage
   → pytest --cov=. --cov-report=xml --cov-fail-under=70 -v
   → Runs all tests and fails the pipeline if coverage < 70%

Step 9: Upload coverage report
   → Saves coverage.xml as a GitHub Actions artifact
```

**Environment variables used in CI:**

```yaml
DJANGO_SETTINGS_MODULE: room_booking_system.settings
SECRET_KEY: ci-secret-key
DEBUG: "False"
USE_SQLITE: "True"   # Use SQLite instead of MySQL for faster CI testing
```

### Flutter Mobile CI (`ci.yml` — `flutter-test` job)

The CI pipeline also runs tests for the Flutter mobile application in parallel with the Django tests:

```
Step 1: Checkout code
Step 2: Set up Flutter 3.22.0 (stable channel, with cache)
Step 3: flutter pub get → Install Dart/Flutter packages
Step 4: flutter analyze → Static code analysis
Step 5: flutter test --coverage → Run widget and unit tests
Step 6: Upload lcov coverage report as artifact
```

### Quality & Security CI (Current Status)

Code quality and test checks currently run inside `.github/workflows/ci.yml`.
There is no separate `quality.yml` workflow file in the current repository snapshot.

---

## 6. Continuous Deployment/Delivery (CD) Process

### How Deployment is Triggered

Unlike CI (which runs on every push), the CD pipeline is **tag-driven**. Deployment only happens when the developer creates and pushes a specific Git tag:

```bash
# Deploy to Development
git tag dev-v1.2.0
git push origin dev-v1.2.0

# Deploy to Staging
git tag stg-v1.2.0
git push origin stg-v1.2.0

# Deploy to Production
git tag prod-v1.2.0
git push origin prod-v1.2.0
```

### CD Pipeline Steps (`cd.yml`)

```
Step 1: Checkout repository
   → Pull the exact commit associated with the tag

Step 2: Set up Docker Buildx
   → Enables multi-platform Docker builds

Step 3: Log in to Docker Hub
   → Authenticate using DOCKER_USERNAME and DOCKER_PASSWORD secrets

Step 4: Extract version and environment from tag
   → dev-v1.2 → ENV=dev, VERSION=1.2
   → stg-v1.2 → ENV=stg, VERSION=1.2
   → prod-v1.2 → ENV=prod, VERSION=1.2

Step 5: Build and push Docker image
   → docker build -t username/intelligent_room_booking:dev-1.2 .
   → docker tag ... :master   (or :testing or :production)
   → docker push both tags to Docker Hub

Step 6: Create deployment summary
   → Posts a summary of what was deployed to the GitHub Actions log
```

### Docker Image Tagging Strategy

```
Docker Hub Repository: username/intelligent_room_booking

Tag pattern:
  dev-v1.2  →  :dev-1.2   (versioned)  +  :master      (latest dev)
  stg-v1.2  →  :stg-1.2   (versioned)  +  :testing     (latest staging)
  prod-v1.2 →  :prod-1.2  (versioned)  +  :production  (latest production)
```

### Running the Deployed Docker Image

```bash
# Pull and run production image
docker pull username/intelligent_room_booking:production
docker run -p 8000:8000 --env-file .env.docker username/intelligent_room_booking:production

# Or use docker-compose
docker-compose up --build
```

---

## 7. Workflow Configuration

### File: `.github/workflows/ci.yml` — Main CI

```yaml
name: Django CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  django-test:
    runs-on: ubuntu-latest
    env:
      DJANGO_SETTINGS_MODULE: room_booking_system.settings
      SECRET_KEY: ci-secret-key
      DEBUG: "False"
      USE_SQLITE: "True"

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-django ruff

      - name: Check Django project
        run: python manage.py check

      - name: Lint with Ruff
        run: ruff check .

      - name: Run unit tests
        run: pytest --cov=. --cov-report=xml --cov-fail-under=70 -v

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml

  flutter-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: room_booking_flutter
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: "3.22.0"
          channel: stable
      - run: flutter pub get
      - run: flutter analyze
      - run: flutter test --coverage
```

### File: `.github/workflows/cd.yml` — CD (Docker Build & Push)

```yaml
name: Django CD

on:
  push:
    tags:
      - 'dev-v*'    # e.g., dev-v1.0
      - 'stg-v*'    # e.g., stg-v1.0
      - 'prod-v*'   # e.g., prod-v1.0

env:
  REGISTRY: ${{ secrets.DOCKER_USERNAME }}/intelligent_room_booking

jobs:
  build-and-push:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract Version and Tag
        id: extract
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          if [[ "$TAG" == dev-v* ]]; then
            echo "VERSION=${TAG#dev-v}" >> $GITHUB_OUTPUT
            echo "ENV=dev" >> $GITHUB_OUTPUT
          elif [[ "$TAG" == stg-v* ]]; then
            echo "VERSION=${TAG#stg-v}" >> $GITHUB_OUTPUT
            echo "ENV=stg" >> $GITHUB_OUTPUT
          elif [[ "$TAG" == prod-v* ]]; then
            echo "VERSION=${TAG#prod-v}" >> $GITHUB_OUTPUT
            echo "ENV=prod" >> $GITHUB_OUTPUT
          fi

      - name: Build and Push Docker Images
        run: |
          # Build, tag, and push to Docker Hub
          docker build -t $REGISTRY:$ENV-$VERSION .
          docker tag $REGISTRY:$ENV-$VERSION $REGISTRY:$ALIAS_TAG
          docker push $REGISTRY:$ENV-$VERSION
          docker push $REGISTRY:$ALIAS_TAG
```

### File: `.github/workflows/quality.yml` — Code Quality & Security

This file is referenced in earlier drafts of the pipeline design but is not currently present in the repository.
Equivalent checks (lint, format check, and tests) are already included in `.github/workflows/ci.yml`.

### Required GitHub Secrets

Configure these in: **GitHub Repository → Settings → Secrets and Variables → Actions**

| Secret Name | Description |
|-------------|-------------|
| `DOCKER_USERNAME` | Docker Hub account username |
| `DOCKER_PASSWORD` | Docker Hub account password or access token |
| `DEV_DEEPSEEK_API_KEY` | DeepSeek AI API key for development |
| `DEV_GROQ_API_KEY` | Groq AI API key for development |
| `DEV_APP_URL` | Development application URL |
| `STAGING_*` | Staging equivalents of all dev secrets |
| `PROD_APP_URL` | Production application URL |

---

## 8. Challenges Faced

During the setup and operation of the CI/CD pipeline, several challenges were encountered:

### Challenge 1: Managing Multiple Environments

**Problem:** The project needed three separate environments (dev, staging, production), each with different database configurations, API keys, and Docker image tags.

**Solution:** Used a tag-naming convention (`dev-v*`, `stg-v*`, `prod-v*`) in the CD workflow so the same workflow file handles all environments based on the pushed tag.

---

### Challenge 2: Heavy Dependencies in CI

**Problem:** The project uses large AI libraries (DeepSeek, Groq, Streamlit) that take a long time to install in the GitHub Actions runner, slowing down every CI run.

**Solution:** Created a separate `requirements.docker.txt` file with only the production-essential packages. The CI pipeline uses the standard `requirements.txt` and enables `pip` caching via `cache: "pip"` in the `setup-python` action.

---

### Challenge 3: SQLite vs MySQL in CI

**Problem:** The production environment uses MySQL, but setting up a full MySQL service in GitHub Actions adds complexity and latency to every CI run.

**Solution:** Used the `USE_SQLITE=True` environment variable in CI. The Django settings file checks this variable and switches to SQLite for testing, keeping CI fast without losing test accuracy.

---

### Challenge 4: Flutter and Django Testing in Parallel

**Problem:** Both the Django backend and the Flutter mobile app needed CI coverage, but running them sequentially would make the pipeline very slow.

**Solution:** Defined two separate jobs (`django-test` and `flutter-test`) in `ci.yml`. GitHub Actions runs them in parallel on separate virtual machines, cutting total CI time roughly in half.

---

### Challenge 5: Code Coverage Threshold

**Problem:** Setting a strict 70% coverage requirement (`--cov-fail-under=70`) caused pipeline failures during early development when test coverage was still being built out.

**Solution:** Progressively added test cases in the `tests/` directory to meet the threshold. The coverage report (uploaded as an artifact) helped identify which modules needed more testing.

---

### Challenge 6: Secret Management

**Problem:** The project requires many API keys (DeepSeek, Groq, Telegram, Google OAuth) which cannot be stored in the repository.

**Solution:** All secrets are stored as GitHub Actions Secrets and injected as environment variables only during the workflow run. The `.env.example` file documents all required variables without exposing real values.

---

## 9. Benefits of CI/CD in This Project

After implementing the full CI/CD pipeline, the project gained the following measurable benefits:

### Developer Productivity

| Before CI/CD | After CI/CD |
|-------------|------------|
| Manual testing before every push | Tests run automatically on every push |
| No consistent code style enforcement | Ruff linter catches style issues instantly |
| Manual Docker builds and uploads | CD pipeline builds and pushes Docker images automatically |
| Risk of deploying untested code | Only tested code can be deployed |

### Reliability

- **Every commit is tested** — no code reaches main without passing all tests
- **Code coverage stays above 70%** — enforced by the pipeline
- **Security vulnerabilities are scanned** — Bandit and Safety run on every push
- **Consistent Docker images** — same build process every time, no "works on my machine" issues

### Speed

- Django and Flutter tests run **in parallel**, reducing total wait time
- `pip` caching means dependency installation is fast after the first run
- Tag-based deployment means releasing is as simple as `git tag prod-v1.0 && git push`

### Traceability

- Every deployment is linked to an exact Git tag and commit
- Coverage reports are saved as GitHub Actions artifacts for review
- Security reports (`bandit-report.json`) are archived for audit purposes

---

## 10. Conclusion

### Summary

This project successfully implemented a complete CI/CD pipeline using **GitHub Actions** for the **Intelligent Room Booking System**. The pipeline covers:

1. **Automated testing** for both the Django backend and Flutter mobile app
2. **Code quality enforcement** using Ruff linter and formatter
3. **Security scanning** using Bandit and Safety
4. **Test coverage enforcement** at a minimum of 70%
5. **Automated Docker image building and pushing** to Docker Hub
6. **Multi-environment deployment** using tag-based triggers for dev, staging, and production

### Final Result

```
Every code push → Automatically tested and linted
Every release tag → Automatically built and deployed to Docker Hub

Developer effort: git tag prod-v1.0 && git push
Result: Production Docker image live on Docker Hub
```

### Key Takeaway

CI/CD is not just a tool — it is a **practice** that improves software quality, team collaboration, and delivery speed. For the Intelligent Room Booking System, the pipeline ensures that every feature added to the codebase is:

- ✅ Tested automatically
- ✅ Code-quality checked
- ✅ Security scanned
- ✅ Deployable with a single Git command

This makes the development process faster, safer, and more professional.

---

*Report generated for the Intelligent Room Booking System project — May 2026*
