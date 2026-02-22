# 21. S3 Advanced (Lifecycle, Replication) — Senior

## Q1. (Beginner) What is S3 lifecycle? Name two actions.

**Answer:**  
**Lifecycle** rules automatically **transition** or **expire** objects. **Actions**: **Transition** — move to IA, Glacier, etc. after N days. **Expiration** — delete after N days (or delete incomplete multipart uploads). Use to **reduce cost** (e.g. move to Glacier after 90 days) and **retention** (e.g. delete after 7 years).

---

## Q2. (Beginner) What is S3 Cross-Region Replication (CRR)? What is required to enable it?

**Answer:**  
**CRR** replicates **new** objects (and optionally deletes) from **source** bucket to **destination** bucket in **another region**. **Required**: **versioning** on **both** buckets; **IAM** role for replication (S3 can assume and read source, write destination); **replication rule** (filter by prefix/tag, destination bucket, optional storage class). **Use**: DR, compliance, low-latency access in second region.

---

## Q3. (Intermediate) How do you design a lifecycle policy so that logs in s3://my-bucket/logs/ move to Glacier after 30 days and are deleted after 7 years?

**Answer:**  
**Rule**: (1) **Filter**: prefix `logs/`. (2) **Transition**: to **Glacier** (or Glacier Deep Archive) after **30** days. (3) **Expiration**: delete objects after **2555** days (≈7 years). In **Lifecycle** configuration for the bucket, add this rule. **Note**: transition to Glacier Instant Retrieval, Glacier Flexible Retrieval, or Deep Archive depending on retrieval needs; 7-year retention may require **Object Lock** for compliance (prevent early delete).

---

## Q4. (Intermediate) What is S3 Replication Time Control (RTC)? When would you use it?

**Answer:**  
**RTC** guarantees **99.99%** of objects replicated within **15 minutes** and provides a **replication metrics** (S3 Replication metrics in CloudWatch). **Use** when you need **predictable** replication SLA (e.g. DR with low RPO). **Standard** replication is async with no SLA. **Cost**: RTC has additional charge. Use for critical buckets; use standard replication for non-critical.

---

## Q5. (Intermediate) Production scenario: You have 100 TB in S3 Standard. Most objects are never accessed after 90 days. How do you reduce cost with lifecycle without losing data?

**Answer:**  
**Lifecycle rule**: (1) **Transition** objects to **S3 IA** after **90** days. (2) Optionally **Transition** to **Glacier** after 180 or 365 days. (3) **No expiration** if you must keep data. **Alternative**: **Intelligent-Tiering** — no rule; S3 moves between tiers by access pattern (small monthly monitoring charge). **Result**: most data moves to IA (or Glacier); **significant** storage cost reduction; data remains available (IA) or restorable (Glacier).

---

## Q6. (Advanced) What is S3 Object Lock? What is compliance mode vs governance mode?

**Answer:**  
**Object Lock**: **WORM** (Write Once Read Many) — objects cannot be **deleted** or **overwritten** for a **retention** period. **Governance mode**: retention set by **retention period**; only users with `s3:BypassGovernanceRetention` can delete early. **Compliance mode**: **no one** can delete or shorten retention (not even root). Use for **compliance** (e.g. financial, legal). **Requires** versioning and bucket-level Object Lock enabled.

---

## Q7. (Advanced) Production scenario: Compliance requires that all uploads to a bucket are encrypted and that object versions cannot be deleted for 7 years. How do you implement this?

**Answer:**  
(1) **Encryption**: **Default encryption** on bucket (SSE-S3 or SSE-KMS); **Bucket policy** **Deny** PutObject when `s3:x-amz-server-side-encryption` is null or not AES256/aws:kms. (2) **Retention**: enable **Object Lock** on bucket (at creation; cannot enable later on existing bucket); **default retention** 7 years in **compliance** mode; or set **object-level** retention on each PutObject. (3) **Versioning**: **enabled** (required for Object Lock). (4) **Lifecycle**: do **not** expire current or noncurrent versions if lock applies; or use lifecycle only for noncurrent versions after 7 years if policy allows.

---

## Q8. (Advanced) How does S3 batch replication work? When would you use it?

**Answer:**  
**Batch replication**: replicate **existing** objects (that were in the bucket before replication was enabled) or **failed** replications; you create a **batch job** (S3 Batch Operations) to replicate those objects. **Use** when: (1) You **enable CRR** on a bucket that already has objects. (2) Some objects **failed** to replicate (e.g. permission, throttling) and you want to retry. Without batch, only **new** objects replicate.

---

## Q9. (Advanced) Compare S3 for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one bucket or few; default encryption; lifecycle for cost (IA/Glacier); versioning optional. **Medium**: versioning on prod buckets; **CRR** for critical data; **lifecycle** by prefix; access logging. **Enterprise**: **Object Lock** for compliance; **RTC** for DR; **replication** and **cross-account**; **Macie** for sensitive data; **strict** bucket policies and encryption.

---

## Q10. (Advanced) Senior red flags to avoid with S3

**Answer:**  
- **No encryption** or no enforcement (bucket policy) for uploads.  
- **No versioning** on production buckets (accidental overwrite/delete).  
- **No lifecycle** (cost grows; move to IA/Glacier).  
- **Public** bucket without strong justification and locking.  
- **No replication** for critical/DR buckets.  
- **Deleting** or shortening retention on compliance-held data.  
- **Ignoring** request costs and data transfer (use CloudFront, lifecycle).

---

**Tradeoffs:** Startup: encryption, lifecycle. Medium: versioning, CRR. Enterprise: Object Lock, RTC, compliance.
