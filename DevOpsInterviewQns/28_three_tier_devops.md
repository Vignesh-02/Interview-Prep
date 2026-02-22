# 28. Three-Tier DevOps Application (Git, Docker, K8s, Jenkins, Prometheus, SonarQube)

## Q1. (Beginner) What are the main components of a typical DevOps pipeline from code to production?

**Answer:**  
**Source** ( **Git**) → **CI** ( **Jenkins**/GitHub **Actions**): **build**, **test**, **scan** ( **SonarQube**), **build** **image** ( **Docker**) → **push** to **registry** → **deploy** ( **K8s** — **kubectl**/Helm/ **Argo** **CD**). **Observability**: **Prometheus** **scrape** **metrics**; **Grafana** **dashboards**; **Alertmanager** **alerts**. **Optional**: **secret** **store** ( **Vault**); **IaC** ( **Terraform**); **log** **aggregation** ( **Loki**/ELK).

---

## Q2. (Beginner) How does Jenkins trigger a build when code is pushed to Git?

**Answer:**  
**Webhook**: **Git** ( **GitHub**/GitLab) **sends** **HTTP** **POST** to **Jenkins** on **push** ( **payload** = **branch**, **commit**). **Jenkins** **job** **configured** with **Git** **plugin** ( **poll** **SCM** or **trigger** by **webhook**); **build** **starts**; **checkout** **repo** at **commit**. **Pipeline** **job**: **Jenkinsfile** **checked** **out**; **stages** ( **Build**, **Test**, **Deploy**) **run**. **Alternative**: **poll** **SCM** ( **every** **N** **min**) if **webhook** **not** **available**.

---

## Q3. (Beginner) In a pipeline, what is the typical order of steps: build, test, scan, push image, deploy?

**Answer:**  
**Typical**: (1) **Checkout** **code**. (2) **Build** ( **compile**, **npm** **install**, etc.). (3) **Test** ( **unit**, **integration**). (4) **Scan** ( **SonarQube** **SAST**, **dependency** **scan**, **secret** **scan**) — **parallel** or **after** **test**. (5) **Build** **Docker** **image**. (6) **Push** **image** to **registry**. (7) **Deploy** ( **update** **K8s** **manifest** or **Helm** **release** with **new** **tag**; **apply**). **Optional**: **e2e** **after** **deploy** to **staging**; **approval** **gate** before **prod** **deploy**.

---

## Q4. (Beginner) How does Prometheus get metrics from an application running in Kubernetes?

**Answer:**  
**App** **exposes** **/metrics** ( **Prometheus** **format**). **Prometheus** **scrapes** **targets**: **service** **discovery** (e.g. **K8s** **pods** via **annotations** or **ServiceMonitor** if **Prometheus** **Operator**); **scrape** **config** **points** to **pod** **IP** or **Service**; **interval** (e.g. **15s**). **RBAC**: **Prometheus** **ServiceAccount** **list** **pods**/ **services**. **Result**: **metrics** **stored** in **Prometheus**; **query** with **PromQL**; **Grafana** **dashboards**; **alerts**.

---

## Q5. (Intermediate) Write a minimal Jenkinsfile that builds a Docker image, pushes to a registry, and deploys to Kubernetes (deployment image update).

**Answer:**
```groovy
pipeline {
  agent any
  environment {
    REGISTRY = 'myregistry.io'
    IMAGE = 'myapp'
  }
  stages {
    stage('Build') {
      steps {
        sh 'docker build -t ${REGISTRY}/${IMAGE}:${BUILD_NUMBER} .'
      }
    }
    stage('Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'registry', usernameVariable: 'U', passwordVariable: 'P')]) {
          sh 'echo $P | docker login -u $U --password-stdin ${REGISTRY}'
          sh 'docker push ${REGISTRY}/${IMAGE}:${BUILD_NUMBER}'
        }
      }
    }
    stage('Deploy') {
      steps {
        sh "kubectl set image deployment/myapp myapp=${REGISTRY}/${IMAGE}:${BUILD_NUMBER} -n default"
        sh 'kubectl rollout status deployment/myapp -n default'
      }
    }
  }
}
```
**Assumes** **kubeconfig** in **Jenkins**; **credentials** for **registry**; **Deployment** **name** **myapp**.

---

## Q6. (Intermediate) How do you integrate SonarQube into the same pipeline without blocking the build for every minor issue?

**Answer:**  
**Stage** " **SonarQube** **Scan**" after **Build** ( **or** **parallel** with **Test**). **sonar-scanner** with **project** **key**; **quality** **gate** **check** ( **API** or **plugin**). **Don’t** **block** **for** **minor**: **quality** **gate** **only** **fails** on **critical** **bugs**/ **vulnerabilities** ( **not** **code** **smells**); **or** **report** **only** ( **publish** **quality** **report**; **block** **merge** in **Git** **integration** instead of **pipeline**). **Optional**: **incremental** **analysis**; **cache** to **speed** **scan**.

---

## Q7. (Intermediate) How do Git, Docker, and Kubernetes work together in a typical flow?

**Answer:**  
**Git**: **source** of **truth** for **code** and **Dockerfile**; **tag** or **branch** **triggers** **pipeline**. **Docker**: **CI** **builds** **image** from **Dockerfile** + **code**; **tags** **image** (e.g. **git-SHA** or **build** **number**); **pushes** to **registry**. **Kubernetes**: **Deployment** (or **Helm**) **references** **image** **tag**; **pipeline** **updates** **tag** ( **kubectl set image** or **Helm upgrade --set image.tag=...**); **K8s** **pulls** **image** and **rolls** **out**. **Result**: **one** **artifact** ( **image**); **same** **image** **deployed** to **staging** then **prod** ( **promotion**).

---

## Q8. (Intermediate) What is the role of Prometheus in a three-tier setup (web, app, DB)?

**Answer:**  
**Prometheus** **scrapes** **metrics** from **each** **tier**: **web** (e.g. **nginx** **exporter** or **app** **metrics**); **app** ( **app** **/metrics** — **request** **rate**, **latency**, **errors**); **DB** ( **exporter** for **Postgres**/MySQL — **connections**, **queries**). **Role**: **unified** **view** of **health** and **SLO** ( **RED** per **tier**); **alerts** ( **app** **down**, **DB** **slow**); **dashboards** ( **Grafana** — **tier** **breakdown**). **Correlation**: **same** **labels** ( **service**, **tier**) across **tiers** for **aggregation**.

---

## Q9. (Intermediate) How do you secure the pipeline (secrets for registry, K8s, SonarQube)?

**Answer:**  
**Secrets** in **Jenkins** **Credentials** ( **or** **Vault**): **registry** **username**/ **password**; **kubeconfig** or **K8s** **service** **account** **token**; **SonarQube** **token**. **Use** **withCredentials** in **pipeline**; **never** **echo** or **log**. **K8s** **deploy**: **Jenkins** **runs** with **kubeconfig** ( **secret** **file**); **RBAC** **minimal** ( **only** **update** **deployments** in **target** **namespaces**). **SonarQube** **token**: **env** **SONAR_TOKEN** from **credentials**. **Rotate** **secrets** **periodically**; **scan** **repo** for **leaked** **secrets**.

---

## Q10. (Intermediate) How do you deploy the same Docker image to staging then production in one pipeline?

**Answer:**  
**Build** **once**; **push** **image** with **tag** (e.g. **${BUILD_NUMBER}** or **${GIT_SHA}**). **Stage** " **Deploy** **Staging**": **kubectl** or **Helm** **upgrade** with **image** **tag** to **staging** **namespace**; **optional** **smoke** **test**. **Stage** " **Deploy** **Prod**" ( **after** **approval** or **manual** **gate**): **same** **image** **tag** — **kubectl**/ **Helm** **upgrade** to **prod** **namespace**. **No** **rebuild**; **promotion** = **deploy** **same** **artifact** to **prod**.

---

## Q11. (Advanced) Production scenario: Design a full pipeline for a three-tier app (web, app, DB) with Git, Docker, K8s, Jenkins, Prometheus, and SonarQube. Include order of stages and how each component fits.

**Answer:**  
**Repo**: **monorepo** or **per** **service**; **Git** **webhook** → **Jenkins**. **Stages**: (1) **Checkout**; (2) **Build** ( **per** **service** if **monorepo** — **matrix** or **parallel**); (3) **Unit** **test**; (4) **SonarQube** **scan** ( **parallel** or **after** **test**); (5) **Docker** **build** per **service** ( **web**, **app**); (6) **Push** to **registry** ( **tag** = **git-SHA**); (7) **Deploy** **staging** ( **Helm** or **kubectl** — **web**, **app**; **DB** = **existing** **or** **migrate**); (8) **E2E**/ **smoke** **test** ( **optional**); (9) **Approval** **gate**; (10) **Deploy** **prod** ( **same** **images**). **Prometheus**: **scrapes** **web**/ **app**/ **DB** **exporters** ( **ServiceMonitor** or **annotations**); **dashboards** and **alerts** per **tier**. **SonarQube**: **quality** **gate** **fails** **pipeline** on **critical** **issues**. **Result**: **single** **pipeline** **build** → **test** → **scan** → **image** → **staging** → **prod**; **observability** **built-in**.

---

## Q12. (Advanced) How do you run Jenkins at scale (many concurrent jobs, Docker images, K8s deploys)?

**Answer:**  
**Scale** **Jenkins** **agents**: **K8s** **plugin** — **dynamic** **agents** ( **pod** per **job**); **scale** **to** **zero** when **idle**. **Parallel** **stages**: **matrix** **job** ( **multiple** **services**); **parallel** **test**/ **scan** **stages**. **Docker**: **build** in **agent** **pod** ( **Docker-in-Docker** or **Kaniko**); **registry** **cache** ( **cache-from**) to **speed** **builds**. **K8s** **deploy**: **parallel** **deploy** per **service** ( **or** **Helm** **umbrella** **chart**); **rollout** **status** **wait**. **Resource**: **limit** **concurrent** **builds** per **branch**; **queue** **when** **busy**. **Result**: **high** **throughput** without **single** **bottleneck**.

---

## Q13. (Advanced) How do you add rollback to the pipeline (e.g. button or automatic on failure)?

**Answer:**  
**Manual** **rollback**: **pipeline** **parameter** or **separate** **job** " **Rollback** **Prod**" — **input** **previous** **image** **tag** (or **from** **release** **tracker**); **kubectl set image ... <previous-tag>** or **Helm upgrade --set image.tag=<prev>**; **kubectl rollout status**. **Automatic**: **post-deploy** **stage** runs **smoke** **test**; **on** **failure** **run** **rollback** **step** ( **kubectl rollout undo** or **redeploy** **previous** **tag**). **Store** **last** **good** **tag** in **config** **map** or **release** **metadata**; **rollback** **job** **reads** it.

---

## Q14. (Advanced) How do you make the pipeline idempotent and safe for re-runs (e.g. deploy stage)?

**Answer:**  
**Deploy** **stage**: **declarative** ( **Helm upgrade** or **kubectl apply**); **same** **manifest** + **same** **image** **tag** = **no-op** or **stable** **state**. **No** **increment** **build** **number** **in** **manifest** **from** **run** ( **use** **pipeline** **param** or **tag** from **build**). **Test** **stages**: **idempotent** **tests** ( **clean** **state** or **isolated** **env**). **Push** **image**: **tag** = **git-SHA** ( **same** **SHA** = **already** **exists**; **push** **skips** or **overwrites** **same** **tag** by **policy**). **Result**: **re-run** **same** **commit** **produces** **same** **outcome**; **no** **double** **increment** or **orphan** **resources**.

---

## Q15. (Advanced) How do you monitor the pipeline itself (Jenkins job duration, failure rate)?

**Answer:**  
**Jenkins** **metrics**: **Prometheus** **plugin** **exposes** **/prometheus** **metrics** ( **job** **duration**, **count**, **result**); **Prometheus** **scrapes** **Jenkins**. **Dashboard**: **Grafana** — **job** **duration** **trend**, **failure** **rate** by **job**/ **branch**; **queue** **length**. **Alert**: **failure** **rate** > **N%**; **duration** **spike** (e.g. **2×** **baseline**); **queue** **stuck**. **Logs**: **pipeline** **logs** **stored**; **search** for **errors**. **Result**: **pipeline** **reliability** and **performance** **visible**; **regression** **caught**.

---

## Q16. (Advanced) Where does networking and security fit in the three-tier setup (K8s network policy, ingress, TLS)?

**Answer:**  
**Ingress**: **single** **entry** ( **Ingress** **controller** or **LB**); **TLS** **termination** ( **cert** from **cert-manager**); **route** **/api** → **app** **service**, **/** → **web** **service**. **Network** **policy**: **default** **deny** **ingress** in **namespace**; **allow** **web** ← **ingress**; **app** ← **web**; **DB** ← **app** only ( **no** **web** → **DB**). **Security**: **Pod** **security** ( **non-root**, **read-only** **root**); **image** **scan** in **pipeline**; **secrets** from **Vault**/ **ESO**. **Result**: **layered** **access**; **encrypted** **user** **traffic**; **least** **privilege** **between** **tiers**.

---

## Q17. (Advanced) How do you run Prometheus and Grafana in the same Kubernetes cluster as the app (namespaces, scraping)?

**Answer:**  
**Namespace**: **monitoring** ( **Prometheus**, **Grafana**, **Alertmanager**); **app** in **default** or **app** **namespace**. **Prometheus**: **ServiceAccount** with **RBAC** ( **get** **list** **pods**/ **services** in **all** **namespaces**); **ServiceMonitor** or **scrape** **config** with **K8s** **discovery** ( **role: pod** or **endpoints**); **scrape** **annotations** on **app** **pods** ( **prometheus.io/scrape: "true"**). **Grafana**: **data** **source** **Prometheus** ( **URL** = **http://prometheus.monitoring**); **dashboards** **from** **config** **map** or **provisioning**. **Ingress** for **Grafana** ( **auth**); **Prometheus** **internal** only or **auth** **proxy**.

---

## Q18. (Advanced) How do you implement GitOps (e.g. Argo CD) so that Git is the source of truth for K8s manifests instead of Jenkins applying directly?

**Answer:**  
**CI** **pipeline**: **build** **image** → **push**; **update** **Git** **repo** ( **manifests** or **Helm** **values**) with **new** **image** **tag** (e.g. **kustomize** **edit** **image** or **Helm** **values** **file**); **commit** and **push** to **Git**. **Argo** **CD**: **watches** **Git** **repo**; **diffs** **live** **cluster** vs **Git**; **applies** **changes** ( **sync**). **Result**: **Jenkins** **does** **not** **hold** **kubeconfig** for **prod**; **Git** **history** = **deploy** **history**; **rollback** = **revert** **commit**; **audit** in **Git**. **Pipeline** **stages**: **build** → **push** → **update** **Git** ( **tag**); **Argo** **syncs** **automatically** or **on** **approval**.

---

## Q19. (Advanced) How do you add infrastructure as code (Terraform) to the same stack? When does Terraform run vs when does the app deploy?

**Answer:**  
**Terraform** **runs** **separately** or **in** **pipeline**: (1) **Infra** **pipeline** ( **on** **tf** **change** or **schedule**): **terraform plan**; **approval**; **apply** ( **VPC**, **EKS**, **RDS**, **S3**). (2) **App** **pipeline** ( **on** **app** **code** **change**): **build** **image** → **deploy** to **existing** **K8s** ( **provisioned** by **Terraform**). **Order**: **Terraform** **first** ( **cluster**, **DB**); **app** **deploy** **assumes** **cluster** **exists**. **Optional**: **single** **pipeline** with **infra** **stage** ( **plan**/ **apply** **tf**) then **deploy** **app** ( **rare**; **prefer** **separate** **pipelines** for **blast** **radius** and **approval** **granularity**).

---

## Q20. (Advanced) Senior red flags to avoid in a three-tier DevOps setup

**Answer:**  
- **Rebuilding** **image** per **env** ( **build** **once**; **promote**).  
- **Secrets** in **Jenkinsfile** or **repo** ( **use** **credentials**/ **Vault**).  
- **No** **quality** **gate** ( **SonarQube** **report** **only**; **don’t** **block**).  
- **No** **rollback** **path** ( **no** **last** **good** **tag** or **runbook**).  
- **Prometheus** **no** **scrape** **for** **one** **tier** ( **blind** **spot**).  
- **Jenkins** **single** **node** ( **no** **scale**; **bottleneck**).  
- **Deploy** **from** **Jenkins** with **broad** **kubeconfig** ( **prefer** **GitOps** for **prod**).  
- **No** **pipeline** **monitoring** ( **don’t** **notice** **slow**/ **failing** **builds**).

---

**Tradeoffs:** Startup: single Jenkins job, deploy from CI, basic Prometheus. Medium: multi-stage pipeline, SonarQube gate, staging then prod. Enterprise: GitOps, K8s agents, pipeline metrics, IaC separate, full observability.
