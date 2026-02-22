# 11. Infrastructure as Code (Terraform)

## Q1. (Beginner) What is Infrastructure as Code (IaC)? What problems does it solve?

**Answer:**  
**IaC**: **define** infra (servers, networks, etc.) in **code** (files); **apply** to create/update. **Solves**: **reproducibility**, **version control**, **review**, **no** manual drift; **documentation** (code is the doc). **Tools**: Terraform, CloudFormation, Pulumi.

---

## Q2. (Beginner) What is Terraform state? Why is it needed?

**Answer:**  
**State**: **file** (or backend) that **maps** **resources** in code to **real** IDs and **attributes**. **Needed**: Terraform must **know** what it **created** (e.g. instance id) to **update** or **destroy**; **state** holds that. **Keep** state **safe** (remote backend, **lock**); **don’t** edit by hand.

---

## Q3. (Beginner) What is the difference between `terraform plan` and `terraform apply`?

**Answer:**  
**plan**: **dry-run** — shows **what** would change (create, update, delete); **no** changes. **apply**: **executes** the plan; **modifies** real infra. **Use** plan in **CI** or before apply to **review**; apply **after** approval.

---

## Q4. (Beginner) What is a Terraform provider? Give two examples.

**Answer:**  
**Provider**: **plugin** that talks to a **platform** (cloud, API). **Examples**: **aws** (AWS), **kubernetes** (K8s), **docker**, **vault**. **Configure**: `provider "aws" { region = "us-east-1" }`. **Version** in **required_providers** to **pin** and avoid breakage.

---

## Q5. (Intermediate) Write a minimal Terraform config that creates an S3 bucket with versioning enabled.

**Answer:**
```hcl
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = "us-east-1" }
resource "aws_s3_bucket" "app" {
  bucket = "my-app-bucket-unique-name"
}
resource "aws_s3_bucket_versioning" "app" {
  bucket = aws_s3_bucket.app.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

---

## Q6. (Intermediate) What is a Terraform module? When would you create one?

**Answer:**  
**Module**: **reusable** bundle of **resources** (folder or registry); **inputs** (variables), **outputs**. **Use**: **DRY** (e.g. "vpc" module, "eks" module); **share** across **envs** or **teams**. **Call**: `module "vpc" { source = "./modules/vpc"; ... }`.

---

## Q7. (Intermediate) What is Terraform workspace? When would you use workspaces vs separate state (e.g. folders)?

**Answer:**  
**Workspace**: **multiple** state **files** in same **config** (e.g. dev, prod); **switch** with `terraform workspace select prod`. **Use** for **small** teams and **same** structure per env. **Separate** (dirs or repos) per env: **strong** isolation, **different** config per env. **Prefer** **separate** dirs/repos for **prod** vs dev to avoid **mistakes**; **workspaces** for **simple** multi-env.

---

## Q8. (Intermediate) How do you pass a secret (e.g. DB password) into Terraform without putting it in a .tf file?

**Answer:**  
(1) **Env**: `TF_VAR_db_password`; **variable** in Terraform. (2) **File**: **-var-file** (e.g. prod.tfvars) **gitignored**. (3) **Vault** (or cloud): **external** data source or **provider** (e.g. vault provider) to **read** secret; use in resource. **Never** commit **.tfvars** with secrets; use **CI** secret or **Vault**.

---

## Q9. (Intermediate) What is `terraform destroy`? When would you use it with caution?

**Answer:**  
**destroy**: **delete** all resources in **state**. **Caution**: **irreversible** (data loss for DB, buckets); **dependencies** (destroy order). **Use**: **dev** env teardown; **never** run **blind** on prod. **Protect**: **resource** **lifecycle** `prevent_destroy`; **state** **lock**; **approval** in CI.

---

## Q10. (Intermediate) What is a Terraform data source? Give one example.

**Answer:**  
**Data source**: **read** **existing** resource (not managed by this Terraform); **reference** in config. **Example**: `data "aws_ami" "ubuntu" { most_recent = true; owners = ["amazon"] }` then `ami = data.aws_ami.ubuntu.id`. **Use** for **existing** VPC, AMI, etc.

---

## Q11. (Advanced) Production scenario: Someone changed a resource manually in the cloud (e.g. resized an instance). What is configuration drift? How do you detect and fix it with Terraform?

**Answer:**  
**Drift**: **real** state **differs** from **Terraform** state/code. **Detect**: `terraform plan` (Terraform will show **change** to match code). **Fix**: (1) **Adopt** change in **code** (update .tf to match real) then **plan** (no change). (2) **Revert** real to match **code** (manual or **apply**). **Prevent**: **discourage** manual changes; **policy** (e.g. OPA) or **cloud** (e.g. Config) to **alert** on drift; **run** plan in **CI** and **alert** on diff.

---

## Q12. (Advanced) How do you structure Terraform for multiple environments (dev, staging, prod) and multiple regions?

**Answer:**  
**Option 1**: **Separate** dirs per env: `envs/dev`, `envs/prod`; **shared** **modules**; **different** tfvars/backend. **Option 2**: **Workspaces** (dev, prod) + **var** for env. **Option 3**: **Terragrunt** (or wrapper) for **DRY** backend and **vars**. **Regions**: **provider** alias per region; **modules** or **resources** per region. **Prefer** **separate** dirs for **prod** (clear **boundaries**).

---

## Q13. (Advanced) What is Terraform state lock? Why is it critical in a team or CI?

**Answer:**  
**Lock**: **prevent** two **apply** at once (e.g. **DynamoDB** for S3 backend); **lock** while **apply** runs. **Critical**: **without** lock, **concurrent** apply can **corrupt** state or **double** create. **Backend** (e.g. S3 + DynamoDB) provides **locking**; **CI** must use **same** backend so **one** runner at a time per state.

---

## Q14. (Advanced) Production scenario: You need to rename a resource (e.g. change S3 bucket name). Terraform would destroy and recreate (losing data). How do you handle it?

**Answer:**  
(1) **Avoid** rename if **name** is **identity** (e.g. S3 bucket **name** can’t be changed in-place → **recreate**). (2) **Move** in **state** if **only** **logical** name changed: `terraform state mv aws_s3_bucket.old aws_s3_bucket.new`. (3) **Data**: **copy** data to **new** resource (script or **null_resource**); then **remove** old. (4) **Lifecycle**: **create_before_destroy** so **new** is created first (when applicable). **S3**: **new** bucket + **replication** or **copy** then **delete** old; **state mv** only for **logical** id change, not for **real** bucket rename.

---

## Q15. (Advanced) What is Terraform remote backend (e.g. S3)? What are the benefits?

**Answer:**  
**Remote backend**: **state** stored **remotely** (e.g. **S3** + DynamoDB lock). **Benefits**: **shared** state for **team**; **locking**; **no** state file in **repo**; **encryption** at rest. **Config**: `backend "s3" { bucket = "tf-state"; key = "app/terraform.tfstate"; dynamodb_table = "tf-lock"; }`. **CI**: **init** with backend; **apply** uses same state.

---

## Q16. (Advanced) How do you use Terraform to manage Kubernetes resources? What are the tradeoffs vs Helm or plain kubectl?

**Answer:**  
**Terraform**: **kubernetes** provider; **resource** "kubernetes_deployment" etc.; **full** **IaC** (K8s + cloud in one). **Helm**: **templating** and **releases**; **charts**; **K8s-native**. **kubectl**: **imperative** or **apply** YAML. **Tradeoff**: **Terraform** = **one** tool, **state** in TF; **Helm** = **rich** chart **ecosystem**; **GitOps** (Flux, Argo) = **apply** YAML from Git. **Use** Terraform for **cluster** and **cloud**; **Helm/GitOps** for **apps** inside cluster often.

---

## Q17. (Advanced) What is Terraform import? When would you use it?

**Answer:**  
**import**: **bring** **existing** resource **into** state (by **id**); **no** code **creation**. **Use**: **adopt** existing **infra** into Terraform; **migrate** from **manual** or other IaC. **Steps**: **write** **empty** resource (or minimal); `terraform import aws_instance.foo i-12345`; **run** **plan** and **adjust** config to match (no change). **Limitation**: **no** automatic **code** generation; you **write** config to match.

---

## Q18. (Advanced) Production scenario: Terraform apply fails halfway (e.g. network created, instance failed). How do you recover safely?

**Answer:**  
(1) **State**: **state** has **partial** updates (some resources **created**). (2) **Fix** **cause** (quota, permission, typo). (3) **Run** **apply** again; Terraform will **retry** **failed** resource and **continue** (or **create** missing). (4) **If** resource **exists** but **not** in state: **import** it. (5) **Avoid** **manual** delete of **half-created** resources without **state rm** (or state will drift). **Prevent**: **target** apply for **risky** resources; **small** changes; **plan** review.

---

## Q19. (Advanced) How would you set up Terraform in CI (e.g. plan on PR, apply on merge to main)? What about state and secrets?

**Answer:**  
**PR**: **init** (backend); **plan**; **post** plan **output** to PR (comment or artifact). **Merge to main**: **apply** (or **apply** on **approval**). **State**: **remote** backend (S3 etc.); **same** for CI and local. **Secrets**: **env** (TF_VAR_*) from **CI** secret store; **backend** credentials from CI. **Lock**: **single** runner per **state** (e.g. **lock** or **serial** job). **Approval**: **manual** approval for **apply** in prod.

---

## Q20. (Advanced) Senior red flags to avoid with Terraform

**Answer:**  
- **State** in **repo** or **local** only (use **remote** backend).  
- **No** **locking** (concurrent apply).  
- **Secrets** in **.tf** or **committed** tfvars.  
- **No** **plan** before **apply** in prod.  
- **Huge** monolith **state** (split by **layer** or **env**).  
- **Ignoring** **drift** (no periodic plan).  
- **No** **version** pinning (provider, module).  
- **Destructive** changes without **review** or **backup**.

---

**Tradeoffs:** Startup: single state, minimal modules. Medium: remote backend, workspaces or dirs. Enterprise: separate state per env, policy (OPA), CI with plan/apply.
