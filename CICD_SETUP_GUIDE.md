# CI/CD Setup Guide for Intelligent Room Booking

This guide explains how to configure and manage the continuous integration and continuous deployment (CI/CD) pipelines for the Intelligent Room Booking application.

## Overview

The CI/CD pipeline consists of **six** GitHub Actions workflows:

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | Push / PR to `main` | Django lint + unit tests **and** Unity EditMode tests (parallel) |
| `dev.yml` | Push to `dev` branch | Lightweight Django CI for feature branches |
| `staging.yml` | Tag `stg-v*` | Full Django CI + build/push staging Docker image |
| `production.yml` | Tag `prod-v*` | Strict Django CI + build/push production Docker image |
| `cd.yml` | Tags `dev-v*` / `stg-v*` / `prod-v*` | Django Docker image build and push |
| `unity-build.yml` | Tags `dev-v*` / `stg-v*` / `prod-v*` | Unity WebGL build + upload artifact |

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

### Alternative: Command Line Setup (via GitHub CLI)

If you have the [GitHub CLI (`gh`)](https://cli.github.com/) installed, you can configure these secrets directly from your terminal:

```bash
# 1. Login to GitHub
gh auth login

# 2. Set the Docker Username
echo "12345chhounoudom" | gh secret set DOCKER_USERNAME

# 3. Set the Docker Password (Replace with your actual Access Token)
echo "your_docker_hub_access_token_here" | gh secret set DOCKER_PASSWORD
```

> [!WARNING]
> If these secrets are missing or incorrect, the deployment workflows will fail during the "Log in to Docker Registry" step with an "unauthorized" error.

---

## 🎮 Unity CI/CD Setup

The Unity pipeline uses **[GameCI](https://game.ci)** — the industry-standard open-source action suite for running Unity in GitHub Actions.

### Step 1: Get a Unity License File

Unity requires a license to run headlessly in CI. This is a **one-time setup**.

1. **Create a temporary workflow** to generate a license request file (`.alf`). Run this manually once:

```yaml
# Save as .github/workflows/unity-activation.yml — DELETE AFTER USE
name: Unity Activation (Run Once)
on: [workflow_dispatch]
jobs:
  activation:
    runs-on: ubuntu-latest
    steps:
      - uses: game-ci/unity-request-activation-file@v2
        id: get-license-file
      - uses: actions/upload-artifact@v4
        with:
          name: Unity_v2022.x.alf
          path: ${{ steps.get-license-file.outputs.filePath }}
```

2. Go to **Actions tab → "Unity Activation"** → click **"Run workflow"**.
3. Download the `.alf` artifact after it completes.

### Step 2: Activate the License Online

1. Go to **https://license.unity3d.com/manual** (Unity's manual activation page).
2. Upload the `.alf` file you just downloaded.
3. Download the resulting `.ulf` (Unity License File).

### Step 3: Add Unity Secrets to GitHub

Add these three secrets to **Settings > Secrets and variables > Actions**:

| Secret Name | Value |
|---|---|
| `UNITY_LICENSE` | The **full text contents** of the `.ulf` file (open in Notepad, copy all) |
| `UNITY_EMAIL` | Your Unity account email address |
| `UNITY_PASSWORD` | Your Unity account password |

```bash
# Or via GitHub CLI:
gh secret set UNITY_EMAIL    --body "your@email.com"
gh secret set UNITY_PASSWORD --body "your_unity_password"
# For UNITY_LICENSE, paste the full .ulf file content:
gh secret set UNITY_LICENSE  < Unity_v2022.x.ulf
```

> [!IMPORTANT]
> After setup, **delete** the `unity-activation.yml` workflow file — it is only needed once and should not remain in the repo.

### How Unity fits in the pipeline

```
Push to main / PR
       │
       ▼
   ┌─────────────────────────────────────┐
   │           CI Workflow (ci.yml)       │
   │  ┌─────────────────┐ ┌────────────┐ │
   │  │  django-test     │ │unity-test  │ │  ← Parallel jobs
   │  │  (lint+tests)    │ │(EditMode)  │ │
   │  └────────┬─────────┘ └─────┬──────┘ │
   └───────────┼─────────────────┼────────┘
               │  Both must pass │
               └────────┬────────┘
                        ▼
              Push tag (e.g. prod-v1.0.0)
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
   Django CD (cd.yml)        Unity CD (unity-build.yml)
   Build Docker image        Build WebGL artifact
   Push to Docker Hub        Upload to GitHub Actions
```

---

## 🚀 How to Trigger Deployments

Deployments are **tag-driven**. This means you must push a specific git tag to trigger the building and pushing of a Docker image.

### 1. Development Deployment
To push an image for the development environment:
```bash
git tag dev-v1.0.0
git push origin dev-v1.0.0
```
**Result**: Pushes image tags `:dev-1.0.0` and `:master` to Docker Hub. Unity WebGL build uploaded as `unity-dev-build-webgl-dev-v1.0.0` artifact.

### 2. Staging Deployment
To push an image for the staging (QA) environment:
```bash
git tag stg-v1.0.0
git push origin stg-v1.0.0
```
**Result**: Pushes image tags `:stg-1.0.0` and `:testing` to Docker Hub. Unity WebGL build uploaded as `unity-stg-build-webgl-stg-v1.0.0` artifact.

### 3. Production Deployment
To push an image for the live production environment:
```bash
git tag prod-v1.0.0
git push origin prod-v1.0.0
```
**Result**: Pushes image tags `:prod-1.0.0`, `:production`, and `:latest` to Docker Hub. Unity WebGL build is copied to `static/unity_game/WebGL/` and included in the Docker image automatically.

---

## 🐳 Docker Hub Details

- **Repository**: [https://hub.docker.com/r/12345chhounoudom/intelligent_room_booking](https://hub.docker.com/r/12345chhounoudom/intelligent_room_booking)
- The workflows use Docker Buildx for multi-architecture support and layer caching, meaning subsequent builds will be much faster.

---

## 🔧 Troubleshooting

- **CI Fails on `requirements.txt`**: The project now uses `requirements.ci.txt` for CI pipelines. This excludes heavy machine learning and analytics libraries (like `streamlit` and `av`) to ensure fast and reliable CI runs. If you add a new core dependency, remember to add it to both `requirements.txt` and `requirements.ci.txt`.
- **Ruff Lint Errors**: The CI pipeline is strict about code style. If your build fails on the "Lint with Ruff" step, run `ruff check --fix .` locally before pushing to automatically resolve most issues.
- **System Check Fails**: Ensure that your Django application starts successfully locally by running `python manage.py check`.
- **Unity License Error**: If the Unity job fails with "License activation failed", verify that `UNITY_LICENSE`, `UNITY_EMAIL`, and `UNITY_PASSWORD` are all set correctly in GitHub Secrets.
- **Unity Library Cache Miss**: On the first run, Unity imports all assets (~10 min). Subsequent runs use the cache and take ~2-3 min.

## Visual Flow
You can review the interactive visual flow of the CI/CD pipeline by opening the `CICD_FLOW.html` file in your browser.


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

### Alternative: Command Line Setup (via GitHub CLI)

If you have the [GitHub CLI (`gh`)](https://cli.github.com/) installed, you can configure these secrets directly from your terminal:

```bash
# 1. Login to GitHub
gh auth login

# 2. Set the Docker Username
echo "12345chhounoudom" | gh secret set DOCKER_USERNAME

# 3. Set the Docker Password (Replace with your actual Access Token)
echo "your_docker_hub_access_token_here" | gh secret set DOCKER_PASSWORD
```

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
