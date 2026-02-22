# 7. CI/CD Concepts & Jenkins

## Q1. (Beginner) What is CI? What is CD? What is the difference between CD (continuous delivery) and CD (continuous deployment)?

**Answer:**  
**CI**: **integrate** code often; **build** and **test** on every change. **CD**: **delivery** = artifact is **deployable** (manual gate to prod); **deployment** = **automated** deploy to prod. So **continuous delivery** = ready to release; **continuous deployment** = every green build can go to prod automatically.

---

## Q2. (Beginner) What is a Jenkins pipeline? What is the difference between declarative and scripted pipeline?

**Answer:**  
**Pipeline**: **code** (Jenkinsfile) that defines **stages** (build, test, deploy). **Declarative**: **structured** (pipeline { stages { ... } }); **restricted**; good for most cases. **Scripted**: **Groovy** script; **flexible**; more power, more complexity. **Prefer declarative** unless you need scripted logic.

---

## Q3. (Beginner) How do you trigger a Jenkins job when code is pushed to a Git branch (e.g. main)?

**Answer:**  
**Poll SCM**: job **polls** Git (e.g. every 2 min); build if changes. **Webhook** (preferred): Git (GitHub/GitLab) sends **HTTP** request to Jenkins on push; **trigger** job. **Jenkins**: install **Git** plugin; job **Build Triggers** = "GitHub hook trigger" or "Poll SCM"; **GitHub** repo settings → Webhooks → Jenkins URL. **Pipeline**: use **triggers { pollSCM('H/5 * * * *') }** or **triggers { githubPush() }** with webhook.

---

## Q4. (Beginner) What is a Jenkins agent (node)? What is the difference between master and agent?

**Answer:**  
**Master**: **schedules** jobs, **stores** config, **UI**. **Agent** (node): **executes** jobs (build, test); can be **different** OS or have **tools** (Docker, Maven). **Distributed**: master + **agents**; jobs **run on** agents (label). **Single**: master **is** the only node (all on one machine).

---

## Q5. (Intermediate) Write a minimal declarative Jenkinsfile with stages: Checkout, Build (e.g. npm install, npm run build), Test (npm test), and a conditional "Deploy" only on main branch.

**Answer:**
```groovy
pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Build') {
      steps {
        sh 'npm ci'
        sh 'npm run build'
      }
    }
    stage('Test') {
      steps { sh 'npm test' }
    }
    stage('Deploy') {
      when { branch 'main' }
      steps { sh './deploy.sh' }
    }
  }
}
```

---

## Q6. (Intermediate) How do you pass a secret (e.g. API key) to a Jenkins pipeline without exposing it in the console or in the Jenkinsfile?

**Answer:**  
**Credentials**: store in **Jenkins** (Credentials → Secret text or Username/password). **Pipeline**: `withCredentials([string(credentialsId: 'api-key', variable: 'API_KEY')]) { sh 'curl -H "Authorization: $API_KEY" ...' }`. **Never** echo or print the variable; **mask** in log (Jenkins masks known credential vars). **Alternative**: **Vault** or **cloud** secret manager; pipeline fetches at runtime.

---

## Q7. (Intermediate) What is a Jenkins shared library? When would you use it?

**Answer:**  
**Shared library**: **Groovy** code in a **repo**; **reusable** steps and **vars** across Pipelines. **Use**: **standard** build/test/deploy **steps**; **DRY**; **governance** (one place to change). **Define** in Jenkins (Global Pipeline Libraries); **@Library('lib')** in Jenkinsfile; call **lib.steps.deploy()** etc.

---

## Q8. (Intermediate) Your Jenkins build suddenly takes 30 minutes longer. How do you diagnose the cause?

**Answer:**  
(1) **Compare**: **recent** vs **older** builds (timing per stage). (2) **Stages**: which stage **grew**? (3) **Causes**: **deps** (npm/maven) — cache? **tests** — more tests or slower? **agent** — **queue** time, **disk** full, **network**? (4) **Agent**: **disk** space, **load**; **workspace** cleanup. (5) **Logs**: **console** output for long steps. (6) **Fix**: **cache** deps (e.g. npm cache dir); **parallel** tests; **faster** agent or more agents; **trim** pipeline. **Senior**: "I’d compare stage timings, then focus on the stage that regressed — usually deps or tests — and add caching or parallelization."

---

## Q9. (Intermediate) What is the purpose of pipeline "post" (e.g. always, success, failure)? Give an example.

**Answer:**  
**post**: **run** after stages (or pipeline) based on **status**. **always**: cleanup (e.g. docker stop). **success**: notify (e.g. Slack). **failure**: notify, **archive** logs. **Example**:
```groovy
post {
  always { cleanWs() }
  failure { slackSend channel: '#alerts', message: "Build ${env.BUILD_URL} failed" }
}
```

---

## Q10. (Intermediate) How do you run Jenkins pipeline stages in parallel (e.g. lint and unit tests)?

**Answer:**  
**parallel** block:
```groovy
stage('Parallel') {
  parallel {
    stage('Lint') { steps { sh 'npm run lint' } }
    stage('Unit') { steps { sh 'npm test' } }
  }
}
```
**Matrix** (optional): multiple axis (e.g. Node 16, 18). **Use** to **shorten** total time when stages are independent.

---

## Q11. (Advanced) Production scenario: You have 20 microservices; each has a Jenkinsfile. Builds are inconsistent and maintenance is heavy. Propose consolidation (e.g. shared library, single parameterized job).

**Answer:**  
(1) **Shared library**: **one** library with **build()**, **test()**, **deploy()**; each repo **Jenkinsfile** is **thin** (e.g. `lib.buildNode()` with service name). (2) **Parameterized** job: **one** pipeline; **param** = repo/service name; **clone** that repo and run **same** stages. (3) **Multibranch**: **one** multibranch pipeline per **org** or **group**; each repo has **same** Jenkinsfile **template** (or from library). **Tradeoff**: Startup = per-repo Jenkinsfile; enterprise = library + multibranch, or single param job.

---

## Q12. (Advanced) How do you secure Jenkins (credentials, agents, and pipeline)? List at least four practices.

**Answer:**  
(1) **Credentials**: store in **Jenkins** (or **Vault**); **withCredentials** in pipeline; **never** in Jenkinsfile. (2) **Agents**: **dedicated** or **ephemeral** (Docker/K8s); **restrict** what agents can do. (3) **Pipeline**: **Script Security** (Groovy sandbox); **approve** only needed scripts. (4) **RBAC**: **roles** (e.g. dev = run, admin = config). (5) **HTTPS** and **auth**; **no** anonymous. (6) **Audit** (plugin or logs). (7) **Secrets** rotation.

---

## Q13. (Advanced) What is a Jenkinsfile "environment" block? How do you use it for different stages (e.g. dev vs prod)?

**Answer:**  
**environment**: set **env vars** for the pipeline (or stage). **Example**: `environment { ENV = 'dev' }`; **override** per stage: `stage('Deploy Prod') { environment { ENV = 'prod' }; steps { ... } }`. **Credentials**: `environment { API_KEY = credentials('prod-api-key') }`. **Per-branch**: `environment { ENV = env.BRANCH_NAME == 'main' ? 'prod' : 'dev' }`.

---

## Q14. (Advanced) Production scenario: Pipeline must deploy to staging on every PR and to production only when main is merged and tests pass. How do you model this in Jenkins?

**Answer:**  
(1) **Branch** = **PR** or **main**. (2) **Stages**: Checkout, Build, Test (always). (3) **Deploy Staging**: `when { anyOf { branch 'main'; branch 'PR-*' } }` or **when { not { branch 'main' } }** for PRs (depends on how you name branches). **Deploy Prod**: `when { branch 'main' }` and **after** Test success. (4) **Staging** on **every** push to PR (or on PR open/update); **Prod** only on **main** after merge. (5) **Approval** for prod (optional): **input** step or separate job triggered after main merge. **Clarify**: "Deploy staging on PR" = build from PR branch and deploy that to staging; "Deploy prod on main" = only when merging to main.

---

## Q15. (Advanced) How do you run Docker builds inside a Jenkins pipeline (e.g. build image and push to registry)? What about Docker-in-Docker vs host Docker?

**Answer:**  
**Option 1**: **Agent** has **Docker** (socket or CLI); pipeline does `docker build` and `docker push`. **Option 2**: **DinD** (Docker-in-Docker): agent runs **Docker** container; pipeline runs **docker** inside (privileged). **Option 3**: **Kaniko** or **Buildah** (no privileged) inside container. **Pipeline**: `docker.build('myimg').push()` or `sh 'docker build -t ... && docker push ...'`. **Best**: **Kaniko** or **host** Docker socket with **caution** (security); avoid **privileged** DinD if possible.

---

## Q16. (Advanced) What is Jenkins Blue Ocean? What problem does it solve?

**Answer:**  
**Blue Ocean**: **modern** UI for pipelines; **visual** pipeline editor; **branch** and **PR** view. **Solves**: **readability** of pipeline runs; **PR**-centric workflow. **Note**: Blue Ocean has had **reduced** development; many teams use **classic** UI or **other** tools (GitLab CI, GitHub Actions). **Still** useful for **visual** runs.

---

## Q17. (Advanced) How do you avoid storing the Jenkinsfile in the repo (e.g. load from shared config)? What are the tradeoffs?

**Answer:**  
**Load from elsewhere**: **Pipeline from SCM** can point to **different** repo or **path** for Jenkinsfile; or **Pipeline script** from **Jenkins** (single script in job). **Shared** Jenkinsfile in **config** repo: **job** checks out **app** repo but **loads** Jenkinsfile from **config** repo. **Tradeoff**: **single** place to change pipeline vs **per-repo** control. **Downside**: app and pipeline **versioning** can diverge. **Best practice**: **Jenkinsfile in app repo** (pipeline as code with app); **shared library** for **steps**.

---

## Q18. (Advanced) Production scenario: Jenkins master is down. How do you minimize impact and recover? What would you have in place beforehand?

**Answer:**  
**Beforehand**: (1) **Backup** (config, jobs, credentials **encrypted**). (2) **High availability** (multiple masters or **standby**). (3) **Agents** can be **reused** after master restore. (4) **Pipeline** definitions in **Git** (Jenkinsfile) so **recreate** job is easy. **Recovery**: (1) **Restore** from backup to new master. (2) **Re-point** agents. (3) **Verify** credentials and key jobs. **Minimize impact**: **external** CI (e.g. GitHub Actions) as **fallback**; **critical** pipelines also run elsewhere.

---

## Q19. (Advanced) How do you implement "build only when certain paths changed" (e.g. skip backend build if only docs changed)?

**Answer:**  
**Git**: **path filter** in **triggers** (e.g. Poll SCM with paths) or **webhook** with **path** filter (GitHub: paths in webhook). **Pipeline**: **when { changeset "backend/**" }** (plugin) or **script**: `sh 'git diff --name-only HEAD~1 | grep -q "^backend/"'` and **skip** build if no match. **GitLab**: **rules: changes: backend/** in .gitlab-ci.yml. **Jenkins**: **Pipeline** stage **when { changeset "backend/*" }** or **scripted** check.

---

## Q20. (Advanced) Senior red flags to avoid with Jenkins/CI

**Answer:**  
- **Secrets** in Jenkinsfile or console.  
- **No** cleanup (workspace, old builds) → **disk** full.  
- **Single** master with **no** backup.  
- **Long** queues (under-provisioned agents).  
- **No** pipeline **reuse** (copy-paste Jenkinsfile).  
- **Brittle** (flaky tests, no retry).  
- **No** notification on **failure**.  
- **Running** as **root** or **overprivileged** agents.

---

**Tradeoffs:** Startup: single job, minimal pipeline. Medium: multibranch, shared library, credentials. Enterprise: HA, backup, RBAC, audit, agents in K8s.
