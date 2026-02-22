# 14. CI/CD (CodePipeline, CodeBuild)

## Q1. (Beginner) What is CodePipeline? What are stages and actions?

**Answer:**  
**CodePipeline** is a managed **CI/CD** service: **stages** (e.g. Source, Build, Deploy) and **actions** (e.g. pull from GitHub, run CodeBuild, deploy to ECS). Pipeline runs on **trigger** (webhook, manual, schedule). You define the pipeline (console, CLI, or CloudFormation); each action produces **output** (e.g. build artifact) for the next stage.

---

## Q2. (Beginner) What is CodeBuild? How does it differ from running builds on Jenkins or GitHub Actions?

**Answer:**  
**CodeBuild** is **managed** build service: you provide **source** (e.g. CodeCommit, GitHub) and **buildspec** (commands, env); it runs in a container and produces artifacts. **No servers** to manage; pay per build minutes. **vs Jenkins**: no self-hosted; less customization. **vs GitHub Actions**: AWS-native; good for deploying to AWS (same account, IAM); Actions is repo-centric and multi-cloud. Use CodeBuild when you want AWS-native CI and deploys to AWS.

---

## Q3. (Intermediate) Write a minimal buildspec.yml that installs dependencies, runs tests, and outputs a zip for Lambda deployment (Node.js).

**Answer:**
```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 18
  pre_build:
    commands:
      - npm ci
  build:
    commands:
      - npm test
      - npm run build
  post_build:
    commands:
      - zip -r lambda.zip . -x "*.git*" "node_modules/aws-sdk/*"
artifacts:
  files:
    - lambda.zip
```
Use `npm ci` for reproducible installs; zip excludes dev deps if needed or include node_modules for Lambda.

---

## Q4. (Intermediate) How do you trigger a CodePipeline when code is pushed to a GitHub branch? What permissions are needed?

**Answer:**  
Use **GitHub (Version 2)** or **GitHub** source action: connect with **OAuth** or **token**; select repo and branch (e.g. main). Pipeline creates a **webhook** in GitHub so pushes trigger the pipeline. **Permissions**: GitHub app or token with repo access; **CodePipeline** needs permission to start the pipeline (implicit). For **cross-account** or private repo, use connection (e.g. CodeStar Connection) and ensure the connection is approved in GitHub.

---

## Q5. (Intermediate) You want to deploy to ECS (update service with new task definition) as the final stage of CodePipeline. What action do you use and what input does it need?

**Answer:**  
Use **ECS** deploy action (or **CodeDeploy** for blue/green ECS). **Input**: (1) **Artifact** from Build stage that contains the **task definition** (and optionally image definition) — build stage should output `taskdef.json` or use **Amazon ECS** action that updates the task definition image and deploys. (2) **ECS cluster** and **service** name. (3) **CodeDeploy** (optional) for blue/green: application and deployment group. **Typical**: Build produces new image tag and task definition; Deploy action updates service with new task definition revision.

---

## Q6. (Advanced) Production scenario: You have a monorepo (frontend and backend). You want: push to main → build both, run tests; deploy backend to Lambda only if backend/ changed; deploy frontend to S3/CloudFront only if frontend/ changed. How do you design the pipeline?

**Answer:**  
(1) **Source**: GitHub, branch main. (2) **Build stage**: one or two **CodeBuild** actions — e.g. “BuildBackend” (buildspec checks backend, runs tests, outputs Lambda zip) and “BuildFrontend” (buildspec checks frontend, runs tests, outputs dist). Use **path filters** or **script** to detect changes (e.g. `git diff --name-only HEAD~1`); skip or run conditionally. (3) **Deploy stage**: **Lambda** deploy (e.g. from BuildBackend artifact) with **conditional** (run only if backend artifact exists or use manual approval); **S3/CloudFront** deploy from BuildFrontend. **Alternative**: **parallel** build actions with path filter on source; each produces artifact; deploy actions run only when their artifact is present (CodePipeline doesn’t natively “skip” by path — use two pipelines or one pipeline with conditional execution via Lambda or step that checks changed paths and triggers appropriate deploy).

**Simpler approach**: One pipeline; Build stage runs both builds (or one build that builds both and outputs both artifacts); Deploy stage has two actions: deploy Lambda (input = backend artifact), deploy S3 (input = frontend artifact). Use **CodeBuild** to set output variables (e.g. BACKEND_CHANGED) and use **conditional** in pipeline (if supported) or use **Lambda** in between to decide. **Practical**: two pipelines (backend pipeline, frontend pipeline) each with source filter on path — e.g. backend pipeline triggers only when backend/** changes; frontend when frontend/** changes. GitHub webhook or EventBridge can filter by path; or use one pipeline and in first Build step, detect changes and write to manifest, then later stages read manifest and deploy only what changed.

---

## Q7. (Advanced) What is blue/green deployment for ECS? What AWS services are involved?

**Answer:**  
**Blue/green**: two **environments** (blue = current, green = new); switch traffic from blue to green after validation. **ECS**: use **CodeDeploy** with ECS: (1) **Two target groups** (blue, green); ALB listener forwards to one. (2) **CodeDeploy** deploys new tasks to the **green** target group; runs **test** (optional); then **shifts traffic** (e.g. canary 10%, 50%, 100%) from blue to green. (3) **Rollback** = shift back to blue. **Services**: ECS, ALB, CodeDeploy, CodePipeline (to trigger).

---

## Q8. (Advanced) How do you store build secrets (e.g. npm token, API keys) for CodeBuild without putting them in the repo?

**Answer:**  
(1) **Parameter Store** or **Secrets Manager**: store the secret; **CodeBuild** project has an **IAM role** that can read it; in **buildspec** use `aws ssm get-parameter --name /npm/token --with-decryption --query Parameter.Value --output text` or Secrets Manager `get-secret-value`. (2) **Environment variables** in CodeBuild project: mark as **secure** (encrypted); reference in buildspec. (3) **Secrets Manager** is better for rotation; Parameter Store for simple values. Never commit secrets; use IAM for CodeBuild to access AWS secrets.

---

## Q9. (Advanced) Compare CI/CD for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one pipeline (build + deploy); CodeBuild; deploy to one env (e.g. prod or dev+prod); GitHub webhook. **Medium**: stages (test, staging deploy, prod deploy with approval); CodeBuild or Jenkins; secrets in Parameter Store/Secrets Manager; ECS or Lambda deploy. **Enterprise**: **multi-account** (dev/staging/prod); **approval** gates and compliance; **scanning** (SAST, container); **audit** (CloudTrail, pipeline history); blue/green or canary.

---

## Q10. (Advanced) Senior red flags to avoid with CI/CD

**Answer:**  
- **Secrets in repo** or in buildspec in plain text.  
- **No tests** in pipeline (or skipped).  
- **Deploy to prod** without approval or staging.  
- **No rollback** plan (how to revert bad deploy).  
- **Overprivileged** CodeBuild or pipeline role (least privilege).  
- **No artifact versioning** or immutable tags (e.g. always :latest).  
- **Ignoring** failed pipeline (alerts and visibility).

---

**Tradeoffs:** Startup: one pipeline, CodeBuild, deploy to one env. Medium: staging, approval, secrets in Parameter Store. Enterprise: multi-account, scanning, audit, blue/green.
