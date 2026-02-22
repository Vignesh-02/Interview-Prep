# 3. S3 & Object Storage

## Q1. (Beginner) What is S3? What are buckets and objects?

**Answer:**  
**S3** is object storage: unlimited **buckets** (containers, globally unique name), each holding **objects** (key = full path, value = data, metadata, version ID). No hierarchy; “folders” are key prefixes. Use for static assets, backups, data lake, logs.

---

## Q2. (Beginner) What is the difference between S3 Standard, S3 IA (Infrequent Access), and Glacier? When would you use each?

**Answer:**  
**Standard**: frequent access; low latency, higher cost. **IA**: less frequent access; lower storage cost, retrieval fee. **Glacier**: archive; lowest storage cost, retrieval delay (minutes to hours). **Use**: hot data → Standard; backups/compliance → IA or Glacier (with lifecycle to move); long-term archive → Glacier Deep Archive.

---

## Q3. (Intermediate) How do you make an S3 bucket private and allow only a specific IAM role to read/write? What is a bucket policy vs IAM policy?

**Answer:**  
**Bucket private**: block public access (Block Public Access settings = all on); no public ACLs. **Access**: attach **IAM policy** to the role allowing `s3:GetObject`, `s3:PutObject` on `arn:aws:s3:::bucket-name/*`. **Bucket policy** is resource-based (on the bucket); **IAM policy** is identity-based (on user/role). For “only this role,” IAM policy on the role is enough; optionally add bucket policy with explicit `Principal` that role to deny others if you use bucket policy for other rules.

---

## Q4. (Intermediate) Your backend needs to upload files to S3. Should it use SDK PutObject or pre-signed URLs? Compare both.

**Answer:**  
**SDK PutObject**: backend has AWS credentials; uploads on behalf of the user; backend sees and can process the file; more load on backend. **Pre-signed URL**: backend generates a time-limited URL; **client** uploads directly to S3; no file through backend; less bandwidth and CPU on backend; better for large files. **Use pre-signed** for user uploads (especially large); use SDK when backend must process or validate before storing.

---

## Q5. (Intermediate) Write backend code (Node.js or Python) to generate a pre-signed URL for uploading a file to `my-bucket/uploads/` with a 15-minute expiry.

**Answer (Node.js):**
```javascript
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { PutObjectCommand, S3Client } = require('@aws-sdk/client-s3');
const client = new S3Client({ region: 'us-east-1' });
const key = `uploads/${userId}/${Date.now()}-${filename}`;
const cmd = new PutObjectCommand({ Bucket: 'my-bucket', Key: key });
const url = await getSignedUrl(client, cmd, { expiresIn: 900 });
// Return url to client; client PUTs file to this URL
```

**Answer (Python):**
```python
import boto3
from botocore.config import Config
s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': f'uploads/{user_id}/{filename}'},
    ExpiresIn=900
)
```

---

## Q6. (Advanced) Production scenario: Your app serves 10M images/month. Current setup: S3 Standard, CloudFront in front. Cost is high. Propose a strategy for storage class, caching, and lifecycle. Include user-count assumption.

**Answer:**  
**Assumption**: e.g. 100k MAU; 10M requests/month ≈ 4–5 req/s average; many views for popular images. **Strategy**: (1) **CloudFront** in front (already) — cache at edge; reduce S3 GET and data transfer. (2) **Lifecycle**: move objects not accessed in 90 days to **S3 IA** (or Intelligent-Tiering); after 180 days to Glacier if acceptable. (3) **Storage class**: keep hot prefix (e.g. thumbnails) in Standard or use **Intelligent-Tiering** for unknown access pattern. (4) **Metrics**: enable S3 request metrics; tune cache TTL and lifecycle by prefix. **Result**: lower storage and GET cost; most traffic served from CloudFront.

---

## Q7. (Advanced) How do you enforce that all uploads to an S3 bucket are encrypted (SSE-S3 or SSE-KMS)? What if you need to reject unencrypted uploads?

**Answer:**  
**Bucket default**: set **default encryption** (SSE-S3 or SSE-KMS) on the bucket; new objects are encrypted if client doesn’t specify. **Reject unencrypted**: use **bucket policy** with `Deny` on `s3:PutObject` when `s3:x-amz-server-side-encryption` is null or not `aws:kms`/`AES256`. **Example** (deny PutObject without encryption):
```json
{
  "Effect": "Deny",
  "Principal": "*",
  "Action": "s3:PutObject",
  "Resource": "arn:aws:s3:::my-bucket/*",
  "Condition": {
    "StringNotEquals": { "s3:x-amz-server-side-encryption": "AES256" }
  }
}
```

---

## Q8. (Advanced) Production scenario: A compliance team requires that object access (who read what and when) is logged and retained for 7 years. How do you implement this with S3 and where do you store logs?

**Answer:**  
(1) **Enable S3 server access logging** (or use **CloudTrail data events** for object-level). CloudTrail data events give API-level (GetObject, etc.) with identity and time. (2) **Log destination**: separate **S3 bucket** (e.g. `my-company-audit-logs`) with **restricted access** (only logging service and audit role); enable **object lock** or lifecycle to retain 7 years and prevent delete. (3) **Athena** or analytics on the log bucket for querying. (4) Consider **Macie** for sensitive data detection. **Retention**: lifecycle rule or Object Lock (compliance mode) for 7 years.

---

## Q9. (Advanced) Compare S3 for a startup (single region, one bucket) vs enterprise (multi-region, compliance, lifecycle). What does each typically need?

**Answer:**  
**Startup**: one bucket per env or one bucket with prefixes; default encryption; Block Public Access on; versioning optional; lifecycle for cost (move to IA/Glacier). **Enterprise**: multiple buckets by sensitivity; **replication** (CRR) for DR or compliance; **Object Lock** for WORM; **lifecycle** by prefix and compliance rules; **access logging** and CloudTrail; cross-account access via bucket policy and IAM; KMS CMK for encryption.

---

## Q10. (Advanced) Senior red flags to avoid with S3

**Answer:**  
- **Public bucket** or public read without strong justification and locking.  
- **No encryption** (enable default encryption and reject unencrypted uploads).  
- **No versioning** on production buckets (accidental overwrite/delete).  
- **No lifecycle** — old data stays in Standard forever (cost).  
- **Storing secrets** in S3 without encryption and access control.  
- **No logging** or audit trail for compliance.  
- **Pre-signed URLs** with very long expiry or overly broad key prefix.  
- **Ignoring** request costs and data transfer; not using CloudFront for high read traffic.

---

**Tradeoffs:** Startup: one bucket, encryption, lifecycle. Medium: buckets per app/env, versioning, replication for critical data. Enterprise: replication, Object Lock, logging, KMS, compliance policies.
