# CI/CD Setup Guide for Intelligent Room Booking

This guide explains how to configure and manage the continuous integration and continuous deployment (CI/CD) pipelines for the Intelligent Room Booking application.

## Overview

The CI/CD pipeline consists of four main GitHub Actions workflows:

1. **`ci.yml` (Main Branch CI)**: Runs automatically on pull requests and pushes to the `main` branch. Validates code through linting, formatting checks, and unit tests.
2. **`dev.yml` (Development CI)**: A lightweight CI pipeline for feature branches and the `dev` branch.
3. **`staging.yml` (Staging CD)**: Runs full CI and builds/pushes a staging Docker image when a tag starting with `stg-v` is pushed.
4. **`production.yml` (Production CD)**: Runs strict CI and builds/pushes a production Docker image when a tag starting with `prod-v` is pushed.

---

## 🛠️ Required Setup (GitHub Secrets)

Before the deployment pipelines can push images to Docker Hub, you must configure two **Repository Secrets** in your GitHub repository.

1. Go to your repository on GitHub.
2. Navigate to **Settings > Secrets and variables > Actions**.
3. Click the **New repository secret** button.
4. Add the following two secrets exactly as named:

| Secret Name       | Value Required | Description |
|-------------------|----------------|-------------|
| `DOCKER_USERNAME` | `12345chhounoudom` | Your Docker Hub username. |
| `DOCKER_PASSWORD` | `dckr_pat_...` | A Docker Hub Access Token. **DO NOT** use your actual password. Create an Access Token in Docker Hub under **Account Settings > Security**. |

> [!WARNING]
> If these secrets are missing or incorrect, the deployment workflows will fail during the "Log in to Docker Registry" step with an "unauthorized" error.

---

## 🚀 How to Trigger Deployments

Deployments are **tag-driven**. This means you must push a specific git tag to trigger the building and pushing of a Docker image.

### 1. Development Deployment
To push an image for the development environment:
```bash
git tag dev-v1.0.0
git push origin dev-v1.0.0
```
**Result**: Pushes image tags `:dev-1.0.0` and `:master` to Docker Hub.

### 2. Staging Deployment
To push an image for the staging (QA) environment:
```bash
git tag stg-v1.0.0
git push origin stg-v1.0.0
```
**Result**: Pushes image tags `:stg-1.0.0` and `:testing` to Docker Hub.

### 3. Production Deployment
To push an image for the live production environment:
```bash
git tag prod-v1.0.0
git push origin prod-v1.0.0
```
**Result**: Pushes image tags `:prod-1.0.0`, `:production`, and `:latest` to Docker Hub.

---

## 🐳 Docker Hub Details

- **Repository**: [https://hub.docker.com/r/12345chhounoudom/intelligent_room_booking](https://hub.docker.com/r/12345chhounoudom/intelligent_room_booking)
- The workflows use Docker Buildx for multi-architecture support and layer caching, meaning subsequent builds will be much faster.

---

## 🔧 Troubleshooting

- **CI Fails on `requirements.txt`**: The project now uses `requirements.ci.txt` for CI pipelines. This excludes heavy machine learning and analytics libraries (like `streamlit` and `av`) to ensure fast and reliable CI runs. If you add a new core dependency, remember to add it to both `requirements.txt` and `requirements.ci.txt`.
- **Ruff Lint Errors**: The CI pipeline is strict about code style. If your build fails on the "Lint with Ruff" step, run `ruff check --fix .` locally before pushing to automatically resolve most issues.
- **System Check Fails**: Ensure that your Django application starts successfully locally by running `python manage.py check`.

## Visual Flow
You can review the interactive visual flow of the CI/CD pipeline by opening the `CICD_FLOW.html` file in your browser.
