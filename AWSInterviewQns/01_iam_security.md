# 1. IAM & Security Fundamentals

## Q1. (Beginner) What is IAM? What are users, groups, and roles?

**Answer:**  
**IAM** (Identity and Access Management) controls **who** can do **what** on AWS resources. **Users**: identity for a person or app (long-lived credentials: access key + secret). **Groups**: collection of users for assigning policies (e.g. Developers, Admins). **Roles**: identity with **temporary** credentials; assumed by users, services, or cross-account. Prefer **roles** over users for applications and EC2/Lambda; use users only for human console/CLI.

---

## Q2. (Beginner) What is the difference between an IAM user access key and an IAM role? When would you use each?

**Answer:**  
**Access key** (user): long-lived secret; stored in app or env; must rotate manually; risk if leaked. **Role**: short-lived credentials (STS); no secret to store; assumed by EC2, Lambda, or cross-account. **Use role** for EC2 instance profile, Lambda execution role, ECS task role, or any service-to-service. **Use access key** only for human CLI/scripts or legacy systems; prefer role where possible.

---

## Q3. (Intermediate) How do you grant an EC2 instance permission to read from S3 without storing keys on the instance?

**Answer:**  
Attach an **IAM role** to the EC2 instance (instance profile). The role has a policy allowing `s3:GetObject` (and optionally `s3:ListBucket`) on the needed bucket(s). Instance gets **temporary credentials** from the instance metadata service (IMDS); AWS SDK automatically uses them. No access key on disk.

**Example policy (attach to role):**
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": ["arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket/*"]
  }]
}
```

---

## Q4. (Intermediate) What is the principle of least privilege? Give one example of a policy that is too broad vs one that is scoped.

**Answer:**  
**Least privilege**: grant only the permissions **needed** for the task, nothing more. **Too broad**: `"Action": "s3:*", "Resource": "*"` — allows delete, change bucket policy, etc. **Scoped**: `"Action": ["s3:GetObject", "s3:PutObject"], "Resource": "arn:aws:s3:::my-app-bucket/uploads/*"` — only read/write in one prefix. Scope by action, resource (ARN), and condition (e.g. IP, MFA) where possible.

---

## Q5. (Intermediate) How would a backend application running on EC2 assume a role to access another AWS account’s S3 bucket?

**Answer:**  
**Other account** creates an IAM **role** that trusts your account (or a role in your account). Your EC2 has an instance profile that allows `sts:AssumeRole` on that role’s ARN. **In code**: use AWS SDK; call `STS AssumeRole` to get temporary credentials, then use them to create S3 client (or use SDK’s built-in support for assuming role via config). **Example (Node.js):** configure credential provider that assumes the role; SDK handles refresh.

---

## Q6. (Advanced) Production scenario: Your company has 50 developers. You need devs to deploy to dev/staging but not production. How do you structure IAM users, groups, and policies? Include tradeoff for startup vs enterprise.

**Answer:**  
**Approach**: (1) **One IAM user per developer** (or federated login — enterprise). (2) **Groups**: `Developers`, `DevOps`, `ReadOnly`. (3) **Developers** group: policy allowing deploy to dev/staging (e.g. CodePipeline/CodeDeploy for dev/staging, S3 for dev bucket); **deny** or no permission for prod. (4) **DevOps** or separate role for prod deploys (with MFA for prod). **Startup**: single account; groups + managed policies. **Enterprise**: AWS Organizations, multiple accounts (dev/staging/prod); use roles to assume into each account; SCPs to restrict at org level; no long-lived keys in prod.

---

## Q7. (Advanced) What is a Permission Boundary? When would you use it so that even an “admin” cannot delete a critical resource?

**Answer:**  
**Permission boundary** is a managed policy attached to a user or role that sets the **maximum** permissions they can have. Policies on the user/role can only grant a **subset** of the boundary. So you can give a user “admin” policy but set a boundary that **denies** `s3:DeleteBucket` and `s3:PutBucketPolicy` on production buckets. Even if their policy allows it, the boundary caps them. Use for delegating admin in a dev account without allowing deletion of critical resources.

---

## Q8. (Advanced) Production scenario: A third-party API key was committed to Git and pushed. The key is now in AWS (Secrets Manager) and used by Lambda. What steps do you take to rotate it and prevent future leaks?

**Answer:**  
(1) **Immediately rotate** the key in the third-party system (revoke old key, generate new). (2) **Update** the secret in **Secrets Manager** with the new value (or use automatic rotation if supported). (3) **Remove** the key from Git history (BFG, git filter-repo, or force-push after amend; notify team to re-clone). (4) **Scan** repos for other leaks (e.g. git-secrets, TruffleHog). (5) **Lambda** already reads from Secrets Manager; next invocation gets new value (or restart/env refresh if cached). (6) Use **pre-commit hooks** and **Secrets Manager** (or Parameter Store) for all secrets so keys are never in code.

---

## Q9. (Advanced) Compare IAM for a small startup (single account, 5 devs) vs a medium company (20 devs, dev/prod) vs a large enterprise (multi-account, SSO, compliance). What does each typically use?

**Answer:**  
**Startup**: Single account; IAM users or SSO (e.g. Google); one or two groups (Admin, Developer); managed policies; maybe one role for CI. **Medium**: Two accounts (dev, prod) or more; IAM roles to assume cross-account; groups per team; CI uses role (e.g. GitHub OIDC) to assume deploy role in prod. **Enterprise**: AWS Organizations; many accounts (per team or per env); **SSO (IAM Identity Center)**; SCPs; Permission Boundaries; no IAM users where possible (federation); audit via CloudTrail and Config.

---

## Q10. (Advanced) Senior red flags to avoid in IAM

**Answer:**  
- **Using root** for daily tasks or in automation.  
- **Long-lived access keys** for applications (use roles).  
- **Overly broad policies** (`*` on Action or Resource) “to get it working.”  
- **Hardcoding** access keys in code or config in repo.  
- **No MFA** on human users, especially for prod.  
- **Sharing** one IAM user or key across people or services.  
- **Ignoring** Permission Boundaries when delegating admin.  
- **Not rotating** keys or not using automatic rotation for Secrets Manager.

---

**Tradeoffs (startup / medium / enterprise):**  
Startup: IAM users + groups + managed policies, single account. Medium: roles for services, 2+ accounts, assume role for prod. Enterprise: Organizations, SSO, SCPs, no users, audit and compliance.
