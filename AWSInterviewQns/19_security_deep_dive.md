# 19. Security Deep Dive (Secrets Manager, KMS, SCPs) — Senior

## Q1. (Beginner) What is AWS Secrets Manager? How does it differ from Parameter Store?

**Answer:**  
**Secrets Manager**: stores **secrets** (DB credentials, API keys); **automatic rotation** (e.g. RDS); **cross-account** access; paid per secret and per 10k API calls. **Parameter Store**: **Standard** (free) and **Advanced** (paid); **hierarchical** (e.g. /app/prod/db); **no** built-in rotation. Use **Secrets Manager** for **credentials** and **rotation**; use **Parameter Store** for config and non-secret parameters (or simple secrets without rotation).

---

## Q2. (Beginner) What is KMS? What is a CMK vs an AWS-managed key?

**Answer:**  
**KMS** (Key Management Service): create and manage **encryption keys**; used by S3, EBS, RDS, etc. **CMK** (Customer Master Key): **your** key; you control policy and rotation; **customer-managed**. **AWS-managed key**: AWS creates and manages (e.g. aws/s3); you can’t change policy or rotate manually. Use **customer-managed CMK** when you need **audit** (key policy, CloudTrail), **rotation**, or **cross-account** use.

---

## Q3. (Intermediate) How do you automate rotation of a database password used by an application? What does the app need to do?

**Answer:**  
(1) Store secret in **Secrets Manager** (e.g. RDS credentials). (2) Enable **rotation** (Secrets Manager can rotate RDS password via Lambda). (3) **App**: at startup or periodically, call **Secrets Manager GetSecretValue**; cache the secret; **re-fetch** when you get **ResourceNotFoundException** or on a schedule (e.g. hourly) so you pick up the new password after rotation. (4) **IAM**: app role needs `secretsmanager:GetSecretValue`. **Alternative**: use **RDS Proxy** — it uses Secrets Manager and handles rotation; app only talks to Proxy.

---

## Q4. (Intermediate) What is a Service Control Policy (SCP)? How does it limit what even an admin can do?

**Answer:**  
**SCP** is applied at **OU** or **account** level in **AWS Organizations**. It sets the **maximum** permissions (allow list or deny list) for that account/OU. **Example**: SCP that **denies** `s3:DeleteBucket` and `rds:DeleteDBInstance` — even a user with AdministratorAccess in that account **cannot** perform those actions. Use to **guardrail** prod (e.g. no delete prod RDS) or enforce **compliance** (e.g. only certain regions).

---

## Q5. (Intermediate) Production scenario: A third-party API key was leaked in Git. It’s stored in Secrets Manager and used by Lambda. Describe the steps to rotate and prevent future leaks.

**Answer:**  
(1) **Rotate** the key at the **third-party** (revoke old, create new). (2) **Update** the secret in **Secrets Manager** (put new value). (3) **Lambda** will get new value on next **GetSecretValue** (or cache TTL); optionally **restart** or **update** Lambda env to force refresh. (4) **Remove** from Git history (BFG, git filter-repo); force-push; team re-clones. (5) **Prevent**: **pre-commit** hooks (e.g. git-secrets); **scan** (TruffleHog); **never** commit secrets — use Secrets Manager/Parameter Store and IAM. (6) **Audit**: CloudTrail for who accessed the secret.

---

## Q6. (Advanced) How do you grant a Lambda in account A access to an S3 bucket in account B using cross-account role and bucket policy?

**Answer:**  
(1) **Account B** (bucket owner): **Bucket policy** allows account A’s **Lambda execution role** (ARN) to s3:GetObject, etc. Example: `"Principal": { "AWS": "arn:aws:iam::ACCOUNT_A:role/my-lambda-role" }`, Action s3:GetObject, Resource arn:aws:s3:::bucket/*. (2) **Account A**: Lambda has **execution role** (my-lambda-role) with **no** S3 policy in A (bucket is in B). (3) **Lambda** uses default credentials (its role); when it calls S3 in B, B’s bucket policy allows it. **Alternative**: Lambda in A **assumes** a role in B (B creates role, trusts A’s Lambda role); then Lambda uses assumed-role credentials to access B’s bucket.

---

## Q7. (Advanced) What is a Permission Boundary? How do you use it so a developer with “admin” in a dev account cannot delete a critical S3 bucket?

**Answer:**  
**Permission Boundary**: managed policy attached to a **user** or **role** that defines the **maximum** permissions they can have. **Use**: create a boundary that **denies** `s3:DeleteBucket` on `arn:aws:s3:::critical-bucket` (and optionally PutBucketPolicy). Attach this boundary to the developer’s user/role. Even if their **identity policy** grants s3:* , the **boundary** caps them — they cannot delete that bucket. Apply to **all** dev/admin roles in the account.

---

## Q8. (Advanced) Production scenario: You need to share encrypted S3 objects with a partner. They have their own AWS account. How do you design key and bucket policy so they can decrypt and read?

**Answer:**  
(1) **Your bucket**: encrypted with **customer-managed CMK** (KMS). (2) **CMK key policy**: add **partner account** (or partner’s role) as principal allowed to **kms:Decrypt** (and kms:DescribeKey). (3) **Bucket policy**: allow **partner’s role/user** (ARN) to s3:GetObject on the bucket. (4) Partner uses **their** credentials; when they GetObject, S3 returns the object; KMS decrypts with the CMK (partner has decrypt permission). **Alternative**: **cross-account role** — partner assumes a role in your account that has S3 + KMS access; then they read with that role.

---

## Q9. (Advanced) Compare security for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: IAM users/roles; **Secrets Manager** or Parameter Store; **no root** use; MFA; encryption at rest (default). **Medium**: **KMS** CMK for critical data; **rotation** for secrets; **least privilege** roles; **CloudTrail** and Config. **Enterprise**: **Organizations** and **SCPs**; **Permission Boundaries**; **cross-account** roles; **Secrets Manager** rotation; **KMS** and key policies; **audit** and compliance (Config, GuardDuty).

---

## Q10. (Advanced) Senior red flags to avoid in security

**Answer:**  
- **Root** for daily use or automation.  
- **Long-lived** access keys for apps (use roles).  
- **Secrets in code** or in Git.  
- **Overly broad** policies (“*” on Action/Resource).  
- **No MFA** on human users.  
- **No encryption** (S3, RDS, EBS) or using default keys only.  
- **Ignoring** SCPs and boundaries when delegating admin.  
- **No audit** (CloudTrail, Config) or not reviewing who did what.

---

**Tradeoffs:** Startup: IAM, Secrets Manager, encryption. Medium: KMS CMK, rotation, least privilege. Enterprise: SCPs, boundaries, cross-account, audit.
