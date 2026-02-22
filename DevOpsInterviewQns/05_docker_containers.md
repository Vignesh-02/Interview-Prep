# 5. Docker & Containers

## Q1. (Beginner) What is the difference between an image and a container?

**Answer:**  
**Image**: **read-only** template (layers + config); built from Dockerfile or from another image. **Container**: **running** (or stopped) **instance** of an image; has writable layer on top. Many containers can run from the same image.

---

## Q2. (Beginner) What does `docker run -d -p 8080:80 --name myweb nginx` do?

**Answer:**  
**-d**: run in **background** (detached). **-p 8080:80**: **publish** container port 80 to host **8080**. **--name myweb**: container name **myweb**. **nginx**: image. So: start nginx in background, reachable at **localhost:8080**.

---

## Q3. (Beginner) How do you list running containers? How do you remove a stopped container and an unused image?

**Answer:**  
**Running**: `docker ps`. **All**: `docker ps -a`. **Remove container**: `docker rm <id_or_name>`. **Remove image**: `docker rmi <id_or_name>`. **Prune**: `docker container prune`, `docker image prune` (removes unused).

---

## Q4. (Beginner) What is the purpose of a Dockerfile `ENTRYPOINT` vs `CMD`? Can you use both?

**Answer:**  
**CMD**: default **arguments** for the container; overridden by `docker run` args. **ENTRYPOINT**: **fixed** executable (or script); `docker run` args are appended. **Both**: ENTRYPOINT = executable; CMD = default args; e.g. `ENTRYPOINT ["python"]` `CMD ["app.py"]` → run `python app.py` unless you pass different args.

---

## Q5. (Intermediate) Write a minimal Dockerfile for a Node.js app (app in current dir, listen on 3000, no root).

**Answer:**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
USER node
EXPOSE 3000
CMD ["node", "index.js"]
```

---

## Q6. (Intermediate) What is a Docker volume? How do you persist database data across container restarts?

**Answer:**  
**Volume**: **named** or **bind** storage; survives container removal. **Persist DB**: `docker run -v dbdata:/var/lib/mysql mysql` (named volume **dbdata**). **Bind mount**: `-v /host/path:/container/path`. Data in **/var/lib/mysql** is in the volume; restarting or recreating the container keeps data.

---

## Q7. (Intermediate) What is the difference between `docker build` and `docker compose build`? When would you use Compose?

**Answer:**  
**docker build**: build **one** image from Dockerfile. **docker compose build**: build **images** defined in **compose file** (one or more services). **Compose**: **multi-container** app (app + DB + cache); **one** file for run order, networks, volumes; `docker compose up`. Use Compose for **local** or **single-host** multi-service stack.

---

## Q8. (Intermediate) How do you reduce the size of a Docker image? Name three techniques.

**Answer:**  
(1) **Small base**: **alpine** or **distroless** instead of full OS. (2) **Multi-stage**: build in one stage; **copy** only artifact to final stage (no build tools in final image). (3) **Fewer layers**: combine RUN; **.dockerignore** to exclude unneeded files. (4) **No cache** in final image (e.g. npm cache, apt cache cleaned in same RUN).

---

## Q9. (Intermediate) What is `.dockerignore`? Why use it?

**Answer:**  
**.dockerignore**: exclude **files/dirs** from **build context** (sent to daemon on `docker build`). **Use**: **faster** build (smaller context); **smaller** context; avoid copying **node_modules**, **.git**, **env** files into image. **Security**: keep secrets and dev files out of context.

---

## Q10. (Intermediate) How do you pass an environment variable (e.g. API_URL) into a container at runtime?

**Answer:**  
**-e**: `docker run -e API_URL=https://api.example.com app`. **File**: `docker run --env-file .env app`. **Compose**: `environment: - API_URL=https://...` or `env_file: .env`. **Never** put secrets in Dockerfile or commit .env with secrets; use **secret** management at runtime.

---

## Q11. (Advanced) Production scenario: Your Docker build is slow (10+ min). The app is a Node app with 500 MB node_modules. How do you speed up builds and keep the image small?

**Answer:**  
(1) **.dockerignore**: exclude **node_modules**, **.git**, **test**, **docs**. (2) **Layer order**: **COPY package*.json** and **RUN npm ci** **before** **COPY . .** so **node_modules** layer is **cached** when only code changes. (3) **Multi-stage**: build in one stage; **copy** only **node_modules** and **app** to final stage; use **alpine**. (4) **npm ci** (not npm install) for reproducible, faster install. (5) **BuildKit**: `DOCKER_BUILDKIT=1` for cache mounts (e.g. npm cache). **Result**: smaller context, cached deps, smaller final image.

---

## Q12. (Advanced) What is the difference between Docker bridge network and host network? When would you use host?

**Answer:**  
**Bridge** (default): container gets **own** IP; **port publish** to host; **isolated** from host network. **Host**: container **shares** host network stack; no port mapping; **faster** (no NAT); **less** isolation. **Use host** for **performance** (e.g. load generator, some monitoring) when you don’t need isolation; **avoid** for multi-tenant or security-sensitive apps.

---

## Q13. (Advanced) How do you run a container as a specific user (non-root)? Why does it matter for security?

**Answer:**  
**Dockerfile**: `USER node` (or numeric UID). **Run**: `docker run --user 1000:1000 app`. **Why**: **limit** impact of container compromise; **root** in container can mount host or escape in misconfigurations. **Best**: create **non-root** user in image and **USER** that; avoid running as root in production.

---

## Q14. (Advanced) Production scenario: A container exits with code 137. What does that mean and how do you debug?

**Answer:**  
**137** = 128 + 9 = **SIGKILL**; often **OOM killed** (out of memory). **Check**: `docker inspect <id>` for **OOMKilled**; host memory: `free`, `dmesg | grep -i oom`. **Fix**: **increase** memory limit (`docker run -m 512m`) or **optimize** app; set **limits** so one container doesn’t starve others. **Debug**: reproduce with **memory limit**; profile app memory.

---

## Q15. (Advanced) What is Docker BuildKit? What feature (e.g. cache mount) would you use to speed up npm/pip installs?

**Answer:**  
**BuildKit**: next-gen **builder**; **parallel** stages, **cache** mounts, **secrets**. **Cache mount**: `RUN --mount=type=cache,target=/root/.npm npm install` so **npm cache** is reused across builds. **Pip**: `RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt`. **Enable**: `DOCKER_BUILDKIT=1 docker build ...`.

---

## Q16. (Advanced) How do you ensure sensitive data (API keys) are not baked into the image? What are the options at runtime?

**Answer:**  
**Never** COPY .env with secrets or ARG at build time for secrets. **Runtime**: (1) **Env**: `-e` or **--env-file** (file not in image). (2) **Secrets**: Docker **secrets** (Swarm) or **Kubernetes** secrets; mount as file. (3) **Vault** or **cloud** secret manager: app fetches at startup. (4) **Build**: use **BuildKit secret** mount for private package install only (not in final image). **Production**: use **orchestrator** secrets or **Vault**.

---

## Q17. (Advanced) Write a multi-stage Dockerfile that builds a Go app and produces a minimal final image (no build tools).

**Answer:**
```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server .

# Final stage
FROM alpine:3.18
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /app/server .
USER nobody
EXPOSE 8080
CMD ["./server"]
```

---

## Q18. (Advanced) How do you clean up unused images, containers, and volumes to reclaim disk? What is the risk?

**Answer:**  
**Prune**: `docker system prune -a` (containers, networks, images); `docker volume prune` (dangling volumes). **Risk**: **volumes** may hold **data**; prune volumes only if you’re sure no important data. **Safe**: prune **containers** and **unused images**; **volumes** only after confirming. **Production**: use **registry** and **orchestrator**; prune **build** nodes, not data nodes.

---

## Q19. (Advanced) Production scenario: You have 50 microservices; each has a Dockerfile. Builds are inconsistent (different base images, no standard user). Propose a standard and how to enforce it.

**Answer:**  
**Standard**: (1) **Base**: single **approved** base per language (e.g. node:18-alpine, go distroless). (2) **Non-root**: **USER** set in every Dockerfile. (3) **No** secrets in image; **health check** (HEALTHCHECK). (4) **Labels**: org, version. **Enforce**: (1) **Dockerfile lint** (hadolint) in CI; (2) **Image scan** (Trivy, Snyk) in pipeline; (3) **Template** or **base image** repo; (4) **PR check** that Dockerfile passes policy. **Tradeoff**: Startup = guidelines; enterprise = policy-as-code and blocking CI.

---

## Q20. (Advanced) Senior red flags to avoid with Docker

**Answer:**  
- **Running as root** in production.  
- **Secrets** in image or build args.  
- **Large** or **unpinned** base images (pin tag, use alpine/distroless).  
- **No .dockerignore** (slow build, bloat).  
- **Single-stage** with build tools in final image.  
- **No health check** for orchestration.  
- **Unbounded** logs (stdout/stderr filling disk).  
- **Ignoring** image scanning (CVEs).

---

**Tradeoffs:** Startup: single Dockerfile, basic best practices. Medium: multi-stage, non-root, CI build. Enterprise: base image policy, scanning, secrets from vault.
