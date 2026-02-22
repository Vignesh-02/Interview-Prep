# 19. Terraform Advanced

## Q1. (Beginner) What is configuration drift? Why is it a problem?

**Answer:**  
**Drift**: **actual** **infra** **differs** from **Terraform** **state**/code (e.g. **manual** **change** in **console**, **another** **tool**). **Problem**: **next** **apply** may **overwrite** or **fail**; **state** **wrong**; **destroy** could **delete** **wrong** **thing**. **Prevent**: **no** **manual** **changes**; **terraform plan** **regularly**; **detect** **drift** and **fix** (import or **revert** **manual**).

---

## Q2. (Beginner) How do you handle manual changes to a resource that Terraform manages?

**Answer:**  
**Options**: (1) **Revert** **manual** **change** to **match** **code**. (2) **Update** **code** to **match** **reality** (then **apply** to **sync** **state**). (3) **Import** if **resource** was **created** **outside** **Terraform** (bring **under** **management**). **Don’t** **ignore**; **plan** will **show** **diff**; **resolve** so **state** and **code** match **reality**.

---

## Q3. (Beginner) What is Terraform state lock? Why use it?

**Answer:**  
**State lock**: **lock** (e.g. **DynamoDB** for **S3** backend) so **only** **one** **apply** at a time. **Prevents** **concurrent** **apply** **corrupting** **state**. **Backend** **config**: `backend "s3" { ... dynamodb_table = "tf-lock" }`. **Force** **unlock** only when **sure** no **other** **run** (e.g. **crashed** **run**).

---

## Q4. (Beginner) What is a Terraform backend? Name two types.

**Answer:**  
**Backend**: **where** **state** is **stored** (local **file** or **remote**). **Types**: **local** (default); **s3** (AWS) with **DynamoDB** **lock**; **azurerm**; **gcs**; **remote** (Terraform **Cloud**). **Remote** = **shared** **state**, **locking**, **CI** **friendly**; **local** = **dev** only.

---

## Q5. (Intermediate) How do you set up multi-cloud (e.g. AWS + Azure) in Terraform with one state?

**Answer:**  
**Multiple** **providers** in **same** **config**: `provider "aws" { ... }` and `provider "azurerm" { ... }`. **Resources** **from** **each**; **one** **state** **file** (e.g. **S3** or **Terraform** **Cloud**) **holds** **all**. **Unified** **state** = **one** **plan**/apply; **dependency** **across** **cloud** (e.g. **aws_vpc** and **azurerm_virtual_network** **peering**). **Alternative**: **separate** **state** per **cloud** (modules or **workspaces**) for **isolation**; **data** **sources** or **outputs** to **cross** **reference**.

---

## Q6. (Intermediate) What is terraform import? When do you use it?

**Answer:**  
**Import**: **bring** **existing** **resource** into **state** (no **create**); **terraform import <resource> <id>**. **Use**: **resource** **created** **manually** or by **other** **tool**; **migration** from **other** **IaC**. **After** **import**: **add** **resource** **block** to **code** to **match** (or **plan** will **want** to **recreate**). **Id** = **provider** **resource** **id** (e.g. **aws_instance** = **instance-id**).

---

## Q7. (Intermediate) What is terraform plan -refresh-only? When use it?

**Answer:**  
**refresh-only**: **update** **state** from **real** **infra** (no **apply**); **detect** **drift**. **Use**: **see** what **changed** **outside** **Terraform**; **sync** **state** to **reality** before **apply** (e.g. **terraform apply -refresh-only** to **accept** **drift** into **state**). **Then** **code** can be **updated** to **match** or **plan** will **show** **in-code** **changes**.

---

## Q8. (Intermediate) How do you use Terraform workspaces for dev/staging/prod? What are the pitfalls?

**Answer:**  
**Workspaces**: `terraform workspace select prod`; **state** **file** per **workspace** (e.g. **env:/prod/default**). **Use**: **same** **code**; **different** **tfvars** or **workspace** **name** in **resource** **naming** (e.g. **bucket** = **"myapp-${terraform.workspace}"**). **Pitfalls**: **easy** to **apply** **wrong** **workspace**; **no** **code** **isolation** (one **mistake** **affects** all); **prefer** **separate** **dirs**/repos for **prod** for **safety**.

---

## Q9. (Intermediate) What is a Terraform data source? Give an example.

**Answer:**  
**Data source**: **read** **existing** **resource** (no **create**); **data "aws_vpc" "main" { ... }`; **use** **data.aws_vpc.main.id`. **Example**: **lookup** **VPC** by **tag**; **lookup** **AMI** by **name**; **lookup** **K8s** **cluster** **auth**. **Use** when **resource** **exists** **outside** **this** **config** (e.g. **shared** **VPC**).

---

## Q10. (Intermediate) How do you avoid secrets in Terraform state?

**Answer:**  
**State** **stores** **all** **attributes** (including **sensitive**). **Reduce** **exposure**: (1) **remote** **backend** with **encryption** and **access** **control**. (2) **sensitive** **variable** (no **log** in **plan**). (3) **Don’t** **store** **secret** in **resource** if **possible** (e.g. **password** from **Vault** **at** **runtime**; **resource** **only** **reference**). (4) **Vault** **provider** to **fetch** **secret**; **avoid** **tfvars** with **secrets** in **repo**. **State** **still** may **contain**; **restrict** **who** **can** **read** **state**.

---

## Q11. (Advanced) Production scenario: Someone changed an S3 bucket policy in the AWS console. Terraform manages the bucket. What do you do?

**Answer:**  
(1) **terraform plan** — **will** **show** **diff** (Terraform **wants** to **revert** to **code**). (2) **Decide**: **keep** **manual** **change** → **update** **Terraform** **code** to **match** (copy **policy** from **console** into **resource**); **or** **revert** **manual** → **apply** to **restore** **code**. (3) **Apply** so **state** and **reality** **match**. (4) **Prevent**: **policy** (no **manual** **change**); **terraform plan** in **CI** **daily**; **alert** on **drift**; **IAM** **restrict** **console** **edit** on **managed** **resources**.

---

## Q12. (Advanced) How do you manage a unified state file across AWS and Azure (multi-cloud)?

**Answer:**  
**Single** **config**: **aws** + **azurerm** **providers**; **resources** for **both**; **one** **backend** (e.g. **S3** or **Terraform** **Cloud**) **stores** **single** **state** **file** with **all** **resources**. **No** **special** **syntax**; **state** is **global** to **config**. **Consider**: **state** **size** (split by **domain** if **huge**); **blast** **radius** (separate **state** per **env**/cloud if **preferred**); **use** **workspaces** or **separate** **root** **modules** for **isolation**.

---

## Q13. (Advanced) What is Terraform lifecycle (create_before_destroy, prevent_destroy)? When use each?

**Answer:**  
**lifecycle** **block**: **create_before_destroy** = **create** **replacement** **first**, then **destroy** **old** (e.g. **avoid** **downtime** on **LB** **change**). **prevent_destroy** = **block** **destroy** (safety for **critical** **resource**). **ignore_changes** = **don’t** **update** **attribute** (e.g. **tags** **managed** **elsewhere**). **Use** **create_before_destroy** for **stateful** or **identity** **resources** where **order** **matters**; **prevent_destroy** for **prod** **DB**/storage.

---

## Q14. (Advanced) Production scenario: Terraform apply failed halfway (e.g. network error). How do you recover?

**Answer:**  
**State** may be **updated** for **some** **resources** (partial **apply**). (1) **terraform plan** — **see** what’s **left** (Terraform **will** **try** to **create** **missing** or **update** **incomplete**). (2) **Fix** **cause** (e.g. **quota**, **permissions**). (3) **apply** again; **Terraform** **idempotent** — **should** **converge**. (4) If **state** **corrupt** (resource **exists** but **state** **wrong**): **import** or **state** **rm** then **import**; **worst** case **manual** **state** **edit** (rare). **Prevent**: **state** **lock**; **small** **apply** **batches**; **retry** **logic** in **CI**.

---

## Q15. (Advanced) How do you run Terraform in CI (plan on PR, apply on merge)?

**Answer:**  
**PR**: **terraform init**, **terraform plan** (output **to** **comment** or **artifact**); **no** **apply**. **Merge** to **main**: **terraform apply -auto-approve** (or **manual** **approval**). **Backend**: **remote** (S3 + **lock**); **credentials** from **CI** **secrets**. **Convention**: **atlantis** or **custom** **workflow**; **plan** **for** **each** **PR**; **apply** only from **main** (or **release** **branch**). **Guard**: **require** **approval** for **prod**; **policy** (e.g. **OPA**)** to **block** **dangerous** **changes**.

---

## Q16. (Advanced) What is Terragrunt? When would you use it over plain Terraform?

**Answer:**  
**Terragrunt**: **wrapper** for **Terraform**; **DRY** **backend** and **provider** **config**; **dependencies** **between** **modules** (run **in** **order**); **before/after** **hooks**; **parallel** **apply** per **module**. **Use** when: **many** **envs**/modules with **repeated** **backend** **config**; **need** **dependency** **ordering** (e.g. **vpc** then **eks**); **keep** **Terraform** **code** **reusable** and **inject** **env** **via** **Terragrunt**. **Plain** **Terraform** **sufficient** for **simple** **single** **env**.

---

## Q17. (Advanced) How do you refactor Terraform (rename resource, move to module) without destroying and recreating?

**Answer:**  
**state mv**: **terraform state mv <old> <new>** to **rename** **resource** in **state** (e.g. **aws_s3_bucket.x** → **aws_s3_bucket.y**); **update** **code** to **match**. **Move** to **module**: **terraform state mv aws_s3_bucket.x module.m.aws_s3_bucket.x**. **No** **destroy**; **state** **pointer** **updated**. **Plan** after **move** should **show** **no** **changes** (or **only** **intended** **changes**).

---

## Q18. (Advanced) How do you implement drift detection in CI (alert when plan shows changes)?

**Answer:**  
**CI** **job** (e.g. **nightly**): **terraform plan -detailed-exitcode**; **exit** **2** if **plan** has **changes**. **Pipeline** **fails** or **sends** **alert** (Slack, **ticket**); **output** **plan** to **artifact**. **Team** **reviews** and **either** **apply** (intended) or **fix** **code**/revert **manual** (drift). **Optional**: **terraform plan -refresh-only** first to **sync** **state**; then **plan** for **code** **vs** **state**.

---

## Q19. (Advanced) What is policy as code (e.g. OPA, Sentinel) with Terraform? How does it block bad changes?

**Answer:**  
**Policy** **as** **code**: **rules** that **evaluate** **plan** (e.g. "no **public** **S3**", "instance **type** **allowed** **list**"). **Sentinel** (Terraform **Cloud**); **OPA** with **conftest** (plan **JSON**); **Checkov** (scan **tf** **files**). **Block**: **CI** runs **policy** on **plan** **output**; **fail** **pipeline** if **violation**; **no** **apply** until **fix**. **Result**: **compliance** and **safety** **before** **apply**.

---

## Q20. (Advanced) Senior red flags to avoid with Terraform

**Answer:**  
- **Manual** **changes** to **managed** **resources** (causes **drift**).  
- **State** **local** in **team**/CI (use **remote** + **lock**).  
- **Secrets** in **code** or **plain** **tfvars** in **repo**.  
- **No** **plan** before **apply** in **prod** (always **review**).  
- **Large** **monolithic** **config** (split **modules**/state).  
- **No** **lifecycle** or **prevent_destroy** for **critical** **resources**.  
- **Ignoring** **drift** (regular **plan** and **remediate**).  
- **One** **workspace**/state for **all** **envs** without **safeguards** (easy **prod** **mistake**).

---

**Tradeoffs:** Startup: local state, single env. Medium: remote backend, workspaces or dirs per env. Enterprise: Terragrunt, drift detection, policy as code, multi-cloud.
