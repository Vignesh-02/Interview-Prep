# 23. Shift-Left Security & SonarQube

## Q1. (Beginner) What is shift-left security? Why does it matter?

**Answer:**  
**Shift-left**: **do** **security** **earlier** in the **lifecycle** (design, **code**, **PR**) instead of **only** at **deploy**/prod. **Matters**: **cheaper** to **fix** **early**; **fewer** **vulnerabilities** in **prod**; **culture** of **secure** **code**. **Examples**: **SAST** in **PR**, **dependency** **scan**, **secure** **design** **review**.

---

## Q2. (Beginner) What is SonarQube? What does it analyze?

**Answer:**  
**SonarQube**: **static** **analysis** **platform** for **code** **quality** and **security** (bugs, **vulnerabilities**, **code** **smells**, **duplication**). **Analyzes**: **source** **code** (many **languages**); **quality** **gates** (e.g. **no** **new** **bugs**); **security** **hotspots** and **vulnerabilities**. **Runs** in **CI** (e.g. **on** **PR**); **report** to **dashboard**.

---

## Q3. (Beginner) What is SAST? How does it differ from DAST?

**Answer:**  
**SAST** (Static **Application** **Security** **Testing**): **analyze** **source** **code** (or **bytecode**) **without** **running** **app**; **find** **patterns** (e.g. **SQL** **injection**, **hardcoded** **secret**). **DAST** (Dynamic): **run** **app** and **probe** (e.g. **scanner** **hits** **URLs**); **find** **runtime** **issues**. **SAST** = **early** (PR); **DAST** = **staging**/prod ( **real** **behavior**). **Use** **both**.

---

## Q4. (Beginner) What is dependency scanning (e.g. SCA)? Why run it in CI?

**Answer:**  
**SCA** (Software **Composition** **Analysis**): **scan** **dependencies** (npm, **Maven**, **pip**) for **known** **CVEs**. **CI**: **fail** **build** if **critical** **vuln** (or **block** **merge**); **report** in **PR**. **Why**: **deps** are **big** **attack** **surface**; **fix** **before** **merge** ( **bump** or **patch**). **Tools**: **Snyk**, **Dependabot**, **Trivy**, **OWASP** **Dependency-Check**.

---

## Q5. (Intermediate) How do you integrate SonarQube into a Jenkins pipeline without significantly increasing build time?

**Answer:**  
(1) **Run** **SonarQube** **scan** in **parallel** with **other** **steps** (e.g. **test**); **don’t** **block** **critical** **path** unless **gate** **fails**. (2) **Incremental** **analysis** ( **only** **changed** **files**); **SonarQube** **supports** **incremental**. (3) **Cache** **Sonar** **cache** (e.g. **.sonar/cache**) in **CI** to **speed** **re-scans**. (4) **Quality** **gate** **as** **async** or **non-blocking** for **report**; **block** **merge** only if **gate** **fails** ( **separate** **stage**). **Result**: **feedback** **fast**; **gate** **enforced** without **doubling** **build** **time**.

---

## Q6. (Intermediate) What is a SonarQube quality gate? How do you use it to block merges?

**Answer:**  
**Quality** **gate**: **conditions** (e.g. **no** **new** **bugs**, **coverage** **≥** **80%**, **no** **new** **vulnerabilities**). **Project** **status** = **pass** or **fail**. **Block** **merge**: **CI** **step** that **runs** **sonar-scanner** and **checks** **gate** **status** (e.g. **API** **call** or **SonarQube** **plugin**); **fail** **pipeline** if **failed**. **PR** **decoration**: **report** **status** in **GitHub**/GitLab **PR** ( **SonarQube** **plugin** or **API**).

---

## Q7. (Intermediate) How do you integrate security earlier in the pipeline without slowing builds? (Shift-left tactics)

**Answer:**  
(1) **Parallel** **stages**: **lint**, **SAST**, **dependency** **scan** in **parallel** with **test**. (2) **Fast** **checks** **first**: **secret** **scan** ( **gitleaks**), **dependency** **scan** ( **cached**); **fail** **fast** on **critical**. (3) **Incremental** **SAST** ( **only** **changed** **files**). (4) **Async** **report** ( **don’t** **wait** for **full** **report** to **proceed**; **gate** at **merge**). (5) **Cache** **deps** and **scan** **cache**. **Result**: **security** **feedback** in **same** **PR** **cycle** with **minimal** **added** **time**.

---

## Q8. (Intermediate) What is a false positive in SAST? How do you handle it?

**Answer:**  
**False** **positive**: **tool** **reports** **issue** that **isn’t** **real** (e.g. **safe** **use** **of** **function**). **Handle**: (1) **Tune** **rules** ( **disable** or **lower** **severity** for **rule** if **acceptable**). (2) **Suppress** at **line** ( **comment** or **annotation** with **justification**). (3) **Mark** **won’t fix** in **SonarQube** with **comment**. (4) **Improve** **code** so **tool** **understands** (e.g. **assert** **not** **null**). **Don’t** **disable** **all** **rules**; **track** **suppressions** and **review** **periodically**.

---

## Q9. (Intermediate) How do you run SonarQube in a Docker-based CI (e.g. no Java on host)?

**Answer:**  
**Run** **sonar-scanner** in **container**: **image** **sonarsource/sonar-scanner-cli**; **mount** **repo**; **env** **SONAR_HOST_URL**, **SONAR_TOKEN**; **run** **scan** ( **project** **key** from **config**). **CI**: **step** that **runs** **docker run ... sonarsource/sonar-scanner-cli** or **use** **SonarQube** **plugin** ( **Jenkins** **plugin** **runs** **scanner**). **No** **Java** **on** **host** **required**.

---

## Q10. (Intermediate) What is a security hotspot in SonarQube? How is it different from a vulnerability?

**Answer:**  
**Security** **hotspot**: **sensitive** **code** that **needs** **review** (e.g. **password** **handling**); **developer** **confirms** **safe** or **fixes**. **Vulnerability**: **clear** **issue** (e.g. **SQL** **injection**); **must** **fix**. **Hotspot** = **review** **required**; **vulnerability** = **fail** **gate** if **not** **resolved**. **Quality** **gate** can **require** **no** **open** **hotspots** or **all** **reviewed**.

---

## Q11. (Advanced) Production scenario: You need to add shift-left security to an existing pipeline; build time must not increase by more than 2 minutes. What do you add and in what order?

**Answer:**  
**Add** ( **parallel** where possible): (1) **Secret** **scan** ( **gitleaks**/truffleHog) — **fast** (< 1 min); **run** **first**; **fail** on **hit**. (2) **Dependency** **scan** ( **Snyk**/Trivy) — **cache** **deps**; **run** in **parallel** with **test**; **fail** on **critical**. (3) **SAST** ( **SonarQube** or **Semgrep**) — **incremental**; **parallel** with **test**; **quality** **gate** **as** **separate** **step** ( **report** **only** or **block** **merge**). **Order**: **secret** **scan** **early** ( **fast** **fail**); **dependency** + **SAST** **parallel** to **test**; **gate** at **end** so **total** **added** **time** ≈ **max** of **parallel** **steps** (target **< 2** min **extra**).

---

## Q12. (Advanced) How do you reduce SonarQube false positives and keep the quality gate meaningful?

**Answer:**  
(1) **Tune** **rules**: **disable** **noisy** **rules**; **custom** **rule** **set** per **repo**. (2) **Baseline**: **gate** on **new** **issues** only ( **Sonar** **new** **code** **period**); **ignore** **legacy** **debt** until **tackled**. (3) **Suppress** with **justification** ( **comment** + **track** in **ticket**). (4) **Review** **hotspots** ( **not** **auto-fail**); **vulnerabilities** **fail**. (5) **Regular** **retro** on **false** **positives**; **feedback** to **rule** **config**. **Result**: **gate** **catches** **real** **issues**; **team** **trusts** **tool**.

---

## Q13. (Advanced) What is Semgrep vs SonarQube? When would you use both?

**Answer:**  
**Semgrep**: **pattern**-based **SAST** ( **regex**-like **for** **code**); **fast**; **custom** **rules** **easy**; **CI** **friendly**. **SonarQube**: **broad** **quality** + **security**; **dashboard**; **quality** **gates**; **many** **languages**. **Use** **both**: **Semgrep** for **custom** **security** **rules** and **fast** **CI** **check**; **SonarQube** for **quality** **metrics** and **standard** **security** **rules**; **run** **Semgrep** **first** ( **fast** **fail**), **SonarQube** for **full** **report**.

---

## Q14. (Advanced) How do you enforce "no new critical vulnerabilities" in a quality gate while allowing existing technical debt?

**Answer:**  
**SonarQube**: **quality** **gate** **condition** " **No** **new** **issues**" on **Vulnerability** **severity** **Critical** ( **new** **code** **only**). **New** **code** = **configurable** **period** (e.g. **since** **last** **release** or **90** days). **Existing** **issues** = **not** **in** **new** **code**; **gate** **passes** if **no** **new** **critical** **vulns**. **Track** **old** **debt** in **backlog**; **don’t** **block** **release** for **pre-existing** **items** ( **policy** **decision**).

---

## Q15. (Advanced) Production scenario: A critical CVE is found in a dependency in prod. What is the process to fix and prevent recurrence?

**Answer:**  
(1) **Assess**: **impact** ( **in** **use**? **exploitable**?); **patch** or **workaround** **available**. (2) **Fix**: **bump** **dependency** or **patch**; **test**; **deploy** **hotfix** to **prod**. (3) **Prevent**: **dependency** **scan** in **CI** ( **Snyk**, **Dependabot**, **Trivy**) **fail** on **critical**; **alert** on **new** **CVE** ( **Dependabot** **alert**); **regular** **rebuild**/ **bump** ( **Renovate**). (4) **Policy**: **no** **deploy** with **critical** **CVE**; **exception** **process** ( **ticket** + **time** **limit**). (5) **Post-mortem**: **why** **did** **it** **reach** **prod**? **Improve** **gate** or **scan** **frequency**.

---

## Q16. (Advanced) How do you run SAST on a monorepo with multiple languages without one huge scan?

**Answer:**  
**Per** **language** **or** **path**: **matrix** **job** (e.g. **backend** = **Java** **Sonar**, **frontend** = **JS** **Sonar**); **only** **run** **scanner** for **changed** **paths** ( **path** **filter** in **CI**). **SonarQube** **multi-module**: **one** **project** with **modules** ( **sonar.modules**); **each** **module** **scanned** **separately** ( **incremental**). **Result**: **faster** **scans**; **relevant** **rules** per **language**; **unified** **dashboard** if **one** **project** **key** with **modules**.

---

## Q17. (Advanced) What is container image scanning in the context of shift-left? Where does it run?

**Answer:**  
**Scan** **image** for **CVEs** ( **OS** + **app** **deps**). **Shift-left**: **run** **after** **build** in **CI**; **before** **push** to **registry**; **fail** **pipeline** if **critical** **CVE**. **Tools**: **Trivy**, **Snyk**, **Clair**. **Where**: **CI** **step** after **docker build**; **optional** **admission** in **K8s** ( **block** **unsigned** or **unscanned** **images**). **Result**: **vulnerable** **images** **don’t** **reach** **prod**.

---

## Q18. (Advanced) How do you report security scan results to developers (e.g. in PR) without exposing sensitive details?

**Answer:**  
**PR** **comment**: **bot** or **CI** **step** that **posts** **summary** ( **count** of **issues** by **severity**; **no** **full** **code** **snippet** if **sensitive**). **Link** to **SonarQube**/dashboard for **details** ( **auth** **required**). **Don’t** **post** **secrets** or **full** **vuln** **description** in **public** **PR**; **internal** **tool** with **access** **control**. **Fix** **suggestions** **generic** (e.g. " **use** **parameterized** **query**") **without** **exposing** **internal** **logic**.

---

## Q19. (Advanced) How do you balance "block on any critical" vs "allow with approval" for dependency CVEs?

**Answer:**  
**Default**: **block** **merge** on **critical** **CVE** ( **fail** **CI**). **Exception**: **approval** **workflow** (e.g. **security** **team** **approves** **exception** with **ticket** and **mitigation**); **time** **bound** (e.g. **30** days to **fix**). **Implement**: **CI** **step** **fails**; **override** **button** or **label** (e.g. **security-exception-123**) **triggers** **approval**; **audit** **log** of **exceptions**. **Report** **exceptions** **periodically**; **reduce** **exceptions** over **time**.

---

## Q20. (Advanced) Senior red flags to avoid with shift-left and SonarQube

**Answer:**  
- **Disabling** **quality** **gate** or **security** **rules** to **make** **build** **pass**.  
- **No** **dependency** **scan** ( **only** **SAST**).  
- **Ignoring** **security** **hotspots** ( **never** **review**).  
- **Huge** **build** **time** **increase** ( **no** **parallel**/incremental).  
- **Secrets** in **scan** **reports** or **PR** **comments**.  
- **No** **exception** **process** ( **block** **everything** → **bypass** **or** **disable**).  
- **Only** **new** **code** **gate** with **no** **plan** to **reduce** **debt**.  
- **SAST** **only** ( **no** **DAST** or **dependency** **scan**).

---

**Tradeoffs:** Startup: dependency scan + gitleaks in CI. Medium: SonarQube quality gate, SAST in parallel. Enterprise: Semgrep custom rules, image scan, approval workflow, dashboard and metrics.
