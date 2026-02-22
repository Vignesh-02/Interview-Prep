# 18. CI/CD Pipelines & Deployment Strategies

## Q1. (Beginner) What is Blue-Green deployment? What is the main benefit?

**Answer:**  
**Blue-Green**: **two** **identical** **envs** (e.g. **blue** = current, **green** = new); **deploy** to **inactive**; **switch** **traffic** **all at once** to **new**. **Benefit**: **instant** **rollback** (switch **back**); **no** **partial** **versions** during **switch**. **Cost**: **double** **capacity** during **switch** (or **idle** **standby**).

---

## Q2. (Beginner) What is Canary release? How does it differ from Blue-Green?

**Answer:**  
**Canary**: **gradual** **traffic** **shift** to **new** **version** (e.g. 5% → 50% → 100%). **Differs**: **Blue-Green** = **all** **or** **nothing**; **Canary** = **gradual**; **observe** **metrics** (errors, **latency**) before **full** **cutover**. **Use** **Canary** when **risk** **reduction** and **observability**; **Blue-Green** when **simple** **switch** and **fast** **rollback**.

---

## Q3. (Beginner) What infrastructure do you need for Blue-Green (e.g. load balancer, app tier)?

**Answer:**  
**LB** (or **ingress**) that **points** to **one** **group** of **backends** (blue **or** green); **switch** = **change** **target** (e.g. **K8s** **Service** **selector**, **ALB** **target** **group**). **Two** **sets** of **app** **instances** (or **K8s** **Deployments** with **different** **version** **labels**). **DB**: **shared** (same **schema**) or **migrate** **before** **switch**; **no** **double** **DB** unless **full** **env** **clone**.

---

## Q4. (Beginner) What is a deployment pipeline stage? Name three typical stages.

**Answer:**  
**Stage**: **step** in **pipeline** (build → test → deploy). **Typical**: (1) **Build** (compile, **image**); (2) **Test** (unit, **integration**, **e2e**); (3) **Deploy** (staging → **approval** → prod). **Others**: **lint**, **security** **scan**, **deploy** **dev** → **staging** → **prod**. **Gates**: **manual** **approval** or **automated** (tests, **SLO** **check**) before **prod**.

---

## Q5. (Intermediate) How do you implement Blue-Green in Kubernetes (high level)?

**Answer:**  
**Two** **Deployments** (e.g. **myapp-blue**, **myapp-green**) with **version** **label**. **Service** **selector** = **version: blue** (or **green**). **Deploy** **new** **version** to **inactive** **Deployment** (e.g. **green**); **test**; **switch** **Service** **selector** to **version: green** (e.g. **kubectl patch** or **Argo** **sync**). **Rollback**: **patch** **selector** **back** to **blue**. **Alternative**: **single** **Deployment** with **two** **ReplicaSets** and **Service** **selector** to **desired** **ReplicaSet** (more **manual**).

---

## Q6. (Intermediate) How do you implement a Canary in Kubernetes (e.g. 10% traffic to new version)?

**Answer:**  
**Option 1**: **Two** **Deployments** (stable, canary); **Service** with **same** **selector** **label** (e.g. **app: myapp**) but **different** **version**; **weight** via **Istio**/Linkerd **VirtualService** (e.g. **90%** to **stable**, **10%** to **canary**). **Option 2**: **Replica** **count** (e.g. **9** stable + **1** canary = **10%** **canary**); **crude** (no **true** **weight**). **Best**: **service** **mesh** or **ingress** **splitting** (e.g. **nginx** **canary** **annotation**, **Argo** **Rollouts** **canary**).

---

## Q7. (Intermediate) What is a rollback? How do you automate it in a pipeline?

**Answer:**  
**Rollback**: **revert** to **previous** **version** (or **known** **good**). **Automate**: **K8s** `kubectl rollout undo deployment/myapp`; **pipeline** **step** "rollback" that **triggers** **undo** or **redeploys** **previous** **image** **tag**. **Trigger**: **manual** **button** or **auto** when **alert** (e.g. **error** **rate** **spike**). **Store** **last** **good** **tag** in **config** or **release** **tracker**.

---

## Q8. (Intermediate) What is the difference between CI and CD? What is "continuous deployment" vs "continuous delivery"?

**Answer:**  
**CI**: **continuous** **integration** (build + test on **every** **commit**). **CD**: **continuous** **delivery** = **deployable** **any** **time** (manual **approval** to prod); **continuous** **deployment** = **auto** **deploy** to prod **after** **tests** (no **manual** **gate**). **Delivery** = **safer** (approval); **deployment** = **faster** (full **automation**).

---

## Q9. (Intermediate) What is a pipeline approval gate? When would you use a manual gate before production?

**Answer:**  
**Gate**: **step** that **pauses** **pipeline** until **condition** (e.g. **manual** **approval**, **test** **pass**, **SLO** **check**). **Manual** **gate** **before** **prod**: **compliance** (change **review**); **risk** (big **release**); **no** **full** **automation** **trust** yet. **Auto** **gate**: **e2e** **pass**, **error** **budget** **ok**, **smoke** **test** **after** **canary**.

---

## Q10. (Intermediate) How do you run pipeline stages in parallel? When is it useful?

**Answer:**  
**Parallel**: **fan-out** (e.g. **matrix** for **multiple** **versions** or **paths**); **independent** **jobs** (unit **test**, **lint**, **security** **scan**) in **parallel**. **Useful**: **faster** **feedback**; **independent** **steps** don’t **block** each other. **Jenkins** **parallel** **block**; **GitHub** **Actions** **matrix**; **GitLab** **parallel** **jobs**. **Join** before **deploy** (all **must** **pass**).

---

## Q11. (Advanced) Production scenario: You must choose Blue-Green vs Canary for a payment service (high impact). Which and why?

**Answer:**  
**Canary** is **better** for **high** **impact**: **gradual** **traffic** (e.g. 1% → 5% → 25% → 100%); **monitor** **errors** and **latency**; **abort** **before** **full** **blast**. **Blue-Green** **switch** = **all** **users** **at** **once**; **bug** = **full** **outage**. **Payment**: **strict** **SLO**; **Canary** + **automated** **rollback** on **error** **rate** or **latency** **threshold**. **Infra**: **service** **mesh** or **ingress** **weight** **routing**; **feature** **flags** as **backup** to **disable** **new** **path**.

---

## Q12. (Advanced) How do you implement infrastructure for Canary (routing, metrics, rollback)?

**Answer:**  
**Routing**: **Istio** **VirtualService** with **weight** **subset** (e.g. **canary** **10%**); **Nginx** **Ingress** **canary** **annotation** (by **header** or **weight**); **Argo** **Rollouts** **canary** **strategy**. **Metrics**: **Prometheus** **scrape** **both** **versions**; **dashboard** **error** **rate**, **latency** **by** **version**; **alert** if **canary** **worse**. **Rollback**: **automated** (e.g. **Argo** **analysis** **fail** → **abort** **canary**); **manual** **promote** or **abort** from **dashboard**.

---

## Q13. (Advanced) Production scenario: Pipeline suddenly takes 30 minutes longer. How do you diagnose and optimize?

**Answer:**  
(1) **Identify** **stage**: **timing** **per** **stage** (Jenkins **timestamps**, **GitHub** **Actions** **summary**); **which** **stage** **regressed**. (2) **Causes**: **larger** **repo**/artifacts; **slower** **tests** (new **tests**, **flaky** **retries**); **cache** **miss** (Docker, **deps**); **queue** **wait** (concurrency **limit**); **external** **API** **slow**. (3) **Optimize**: **parallel** **jobs**; **cache** **deps**/layers; **split** **tests** (shard, **critical** **first**); **smaller** **images**; **faster** **runner**. (4) **Monitor**: **pipeline** **duration** **metric**; **alert** on **regression**.

---

## Q14. (Advanced) What is GitOps? How does it relate to CI/CD?

**Answer:**  
**GitOps**: **Git** as **source** of **truth** for **desired** **state** (manifests, **Helm**); **controller** (e.g. **Argo** **CD**, **Flux**) **reconciles** **cluster** to **Git**; **no** **push** from **CI** to **cluster** (CI **builds** **image** and **updates** **Git** with **new** **tag**; **GitOps** **pulls** and **applies**). **Relation**: **CI** = **build** + **test** + **update** **Git**; **CD** = **GitOps** **apply** (or **CI** **apply** with **approval**). **Benefit**: **audit** in **Git**; **rollback** = **revert** **commit**; **no** **cluster** **credentials** in **CI**.

---

## Q15. (Advanced) How do you run post-deployment verification (smoke tests) in the pipeline?

**Answer:**  
**Step** after **deploy**: **call** **health** **endpoint**; **run** **smoke** **tests** (critical **paths**); **check** **metrics** (e.g. **error** **rate** **normal**). **Pipeline**: **wait** for **rollout** (e.g. **kubectl rollout status**); **curl** **/health** or **run** **e2e** **smoke** **suite**; **fail** **pipeline** (and **trigger** **rollback**) if **fail**. **Canary**: **analysis** **step** (Prometheus **query**) to **promote** or **abort**.

---

## Q16. (Advanced) What is trunk-based development vs feature branches? How does it affect CI/CD?

**Answer:**  
**Trunk-based**: **short-lived** **branches**; **merge** to **main** **frequently**; **feature** **flags** for **unfinished** **work**. **Feature** **branches**: **long-lived** **branch** per **feature**; **merge** when **done**. **CI/CD**: **trunk-based** = **main** **always** **deployable**; **CI** on **every** **commit** to **main**; **simpler** **pipelines** (one **branch**). **Feature** **branches** = **CI** on **branch**; **merge** **conflicts** and **big** **releases**; **staging** from **main**.

---

## Q17. (Advanced) How do you implement deployment to multiple environments (dev, staging, prod) with promotion?

**Answer:**  
**Promotion**: **same** **artifact** (image **tag**) **promoted** **dev** → **staging** → **prod**. **Pipeline**: **build** **once**; **deploy** to **dev** (auto); **deploy** to **staging** (auto or **gate**); **deploy** to **prod** (manual **approval** or **automated** **after** **staging** **tests**). **GitOps**: **image** **tag** in **overlay** or **values**; **promotion** = **update** **tag** in **Git** (e.g. **staging** → **prod** **dir**); **controller** **applies**. **No** **rebuild** per **env**.

---

## Q18. (Advanced) Production scenario: Deployment to prod succeeded in pipeline but users see old version. What do you check?

**Answer:**  
(1) **Rollout**: `kubectl rollout status deployment/myapp` — **stuck**? **ReplicaSet** **not** **scaling** **up**? (2) **Image**: **pod** **image** **tag** = **expected**? **ImagePullBackOff** on **new** **nodes**? (3) **Caching**: **CDN**/browser **cache** (static **assets**); **LB** **connection** **draining**. (4) **Traffic**: **Service** **selector** **matches** **new** **pods**? **Ingress** **correct**? (5) **Readiness**: **new** **pods** **ready**? **Endpoints** **include** **new** **pods**? **Fix**: **restart** **pods** if **stale**; **clear** **cache**; **fix** **selector**/readiness.

---

## Q19. (Advanced) What is pipeline as code? Give benefits and one example (e.g. Jenkinsfile, GitHub Actions).

**Answer:**  
**Pipeline** **as** **code**: **pipeline** **defined** in **repo** (e.g. **Jenkinsfile**, **.github/workflows/*.yml**, **.gitlab-ci.yml**). **Benefits**: **versioned**, **reviewable**, **reusable**; **same** **branch** as **app**; **no** **click** **config** **drift**. **Example** **GitHub** **Actions**: **workflow** **on** **push** to **main** — **checkout** → **build** → **test** → **deploy** (with **secrets** for **kubeconfig**).

---

## Q20. (Advanced) Senior red flags to avoid in CI/CD and deployments

**Answer:**  
- **Deploying** **without** **tests** or **skipping** **flaky** **tests**.  
- **No** **rollback** **procedure** or **automation**.  
- **Rebuilding** **per** **environment** (not **promotion**).  
- **Secrets** in **pipeline** **code** or **logs**.  
- **No** **approval** **gate** for **prod** (or **blind** **auto** **deploy** without **SLO**).  
- **No** **post-deploy** **verification** (smoke **test**).  
- **Long** **pipelines** with **no** **parallelism** or **cache**.  
- **No** **pipeline** **as** **code** (only **UI** **config**).

---

**Tradeoffs:** Startup: single branch, deploy from CI. Medium: Blue-Green or rolling, approval gate, pipeline as code. Enterprise: Canary, GitOps, multi-env promotion, SLO gates.
