# 29. Cross-Account & Organizations — Senior

## Q1. (Beginner) What is AWS Organizations? What are OUs and SCPs?

**Answer:**  
**Organizations**: **manage multiple accounts** under one **root**; **consolidated billing**; **OUs** (organizational units) group accounts (e.g. Dev, Prod). **SCPs** (Service Control Policies): **allow/deny** permissions at **OU** or account level; apply to **every** user/role in that OU (including admin) unless explicitly allowed. Use for **governance** (e.g. “no one in Dev can delete prod RDS”).

---

## Q2. (Beginner) How do you allow an IAM role in account A to access an S3 bucket in account B?

**Answer:**  
(1) **Account B** (bucket owner): **Bucket policy** allows **account A’s role** ARN: `"Principal": { "AWS": "arn:aws:iam::ACCOUNT_A:role/MyRole" }`, Action s3:GetObject, Resource arn:aws:s3:::bucket/*. (2) **Account A**: **Role** MyRole has **no** S3 policy in A (bucket is in B). (3) **Principal in A** assumes MyRole; uses SDK; calls S3 in B; **B’s bucket policy** allows it. **Alternative**: A’s role **assumes** a role in B (B creates role, trusts A); then use B’s role to access B’s bucket.

---

## Q3. (Intermediate) What is the difference between Allow and Deny in an SCP? Can an SCP grant permissions?

**Answer:**  
**SCP** can only **allow** or **deny**; it **does not grant** — it’s a **boundary**. **Allow**: “these actions/resources are allowed” (whitelist). **Deny**: “these are denied” (blacklist). **Effective permission** = identity policy **and** SCP (and org root SCP). So SCP **deny** blocks even if identity has Allow. **SCP cannot grant** by itself; identity still needs an IAM policy. Use **Deny** to block dangerous actions (e.g. leave region, delete prod).

---

## Q4. (Intermediate) Production scenario: You have dev, staging, and prod accounts. You want only prod to have RDS and only prod data in S3. How do you use SCPs?

**Answer:**  
(1) **OU structure**: e.g. **Prod** OU (prod account), **NonProd** OU (dev, staging). (2) **SCP on NonProd**: **Deny** `rds:*` (and optionally `rds:CreateDBInstance`) so dev/staging cannot create RDS. (3) **SCP**: **Deny** `s3:DeleteBucket`, `s3:PutBucketPolicy` on **prod** bucket ARN in **all** OUs except Prod (or attach SCP to Prod OU that doesn’t deny, and to NonProd that denies cross-account access to prod bucket). (4) **Data**: use **bucket policy** in prod to **deny** access from non-prod account principals; or **allow** only prod roles. **Simpler**: SCP on NonProd = deny RDS; **IAM** and **bucket policy** in prod = only prod roles can access prod S3.

---

## Q5. (Intermediate) How does a developer in the dev account deploy to the prod account (e.g. CodePipeline in prod triggered by approval)?

**Answer:**  
(1) **Cross-account role**: **Prod** account has a **role** (e.g. DeployRole) that trusts **Dev** account (or Dev’s CI role). (2) **Dev**: **CodePipeline** in dev builds artifact; **manual approval** or **automated**; then **cross-account** action: assume **Prod’s DeployRole** (using AWS Cross-Account Action or Lambda that assumes role and deploys). (3) **Prod** DeployRole has permissions (e.g. CodeDeploy, ECS update, S3). (4) **Alternative**: **single** pipeline in **Prod**; **source** from dev (e.g. GitHub branch); **approval** stage before deploy. **Best**: pipeline in **prod** with source from repo; **approval** gate; no long-lived cross-account deploy from dev unless needed.

---

## Q6. (Advanced) What is AWS Control Tower? How does it relate to Organizations and SCPs?

**Answer:**  
**Control Tower**: **automated** setup of **multi-account** landing zone: **Organizations**, **OUs**, **SCPs** (guardrails), **shared** accounts (e.g. log archive, audit); **Account Factory** to create new accounts with baseline. **Relation**: Control Tower **uses** Organizations and **applies** SCPs (e.g. prevent leaving org, restrict regions). Use for **enterprise** to standardize and govern many accounts.

---

## Q7. (Advanced) Production scenario: Your company has 50 AWS accounts (per team). You need central logging: every account sends CloudWatch Logs to a single “log archive” account. How do you design it?

**Answer:**  
(1) **Log archive account**: **Kinesis Data Stream** or **Subscription filter** destination (same account) or **create** a **resource policy** on a **log group** in archive account allowing **other accounts** to write. (2) **Each account**: **Subscription filter** on critical log groups → **cross-account** destination (Kinesis or Lambda in archive account). (3) **IAM**: archive account **Kinesis** (or Lambda) resource policy allows **principal** from each account (e.g. log role ARN). (4) **Alternative**: **CloudWatch Logs** **destination** (cross-account); each account has IAM role that can PutSubscriptionFilter to that destination. (5) **Retention** and **access** in archive account; **encryption** (KMS) with shared key or per-account. **Result**: central logs in one account for audit and analysis.

---

## Q8. (Advanced) How do you restrict which AWS regions can be used across the organization?

**Answer:**  
**SCP** with **Condition**: `"Condition": { "StringNotEquals": { "aws:RequestedRegion": ["us-east-1", "eu-west-1"] } }` and **Effect": "Deny"` for actions like `*` or `ec2:*`, etc. Attach to **root** or **OU** so all accounts in scope cannot use other regions. **Allow list**: deny when RequestedRegion is not in [us-east-1, eu-west-1]. **Result**: only listed regions are usable.

---

## Q9. (Advanced) Compare multi-account for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: **single** account or **two** (dev, prod); minimal SCPs. **Medium**: **3+** accounts (dev, staging, prod); **SCPs** (e.g. deny prod delete); **cross-account** role for deploy or read. **Enterprise**: **many** accounts (per team or per app); **Control Tower** or similar; **SCPs** (regions, services); **central** logging and **security** (GuardDuty, Config); **consolidated billing** and **tag** policies.

---

## Q10. (Advanced) Senior red flags to avoid with cross-account and Organizations

**Answer:**  
- **Sharing** root or **root** credentials.  
- **No SCPs** (any admin can do anything).  
- **Overly broad** SCP (breaks legitimate use).  
- **Cross-account** access without **explicit** resource policy and trust.  
- **No audit** (CloudTrail in each account or centralized).  
- **Ignoring** permission boundaries when delegating admin.  
- **No documentation** of account purpose and trust relationships.

---

**Tradeoffs:** Startup: 1–2 accounts. Medium: 3+ accounts, SCPs. Enterprise: Control Tower, many accounts, central logging.
