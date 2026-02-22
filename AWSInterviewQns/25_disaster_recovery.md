# 25. Disaster Recovery & Backup — Senior

## Q1. (Beginner) What is RTO and RPO? Give one example of each.

**Answer:**  
**RPO** (Recovery Point Objective): max **acceptable data loss**. Example: RPO 1 hour → backup or replicate at least every hour. **RTO** (Recovery Time Objective): max **acceptable downtime**. Example: RTO 4 hours → you must restore or fail over within 4 hours. **Design**: backups and replication frequency for RPO; failover and runbooks for RTO.

---

## Q2. (Beginner) How do you back up an RDS instance? What is automated backup vs snapshot?

**Answer:**  
**Automated backup**: RDS **daily** backup during **backup window**; **retention** (e.g. 7 days); **point-in-time recovery** (PITR) within retention. **Snapshot**: **manual** (or automated via Lambda/EventBridge); **retained** until you delete; **restore** creates a new instance from that point. Use **automated** for short-term PITR; use **snapshots** for long-term or cross-region copy.

---

## Q3. (Intermediate) How do you implement backup for DynamoDB with point-in-time recovery (PITR)?

**Answer:**  
**PITR**: enable **Point-in-time recovery** on the table (console or CloudFormation); DynamoDB **continuously** backs up; you can **restore** to any second in the last **35 days**. **On-demand backup**: create **on-demand** backup (full snapshot); retain until deleted; use for **long-term** or **cross-region** copy. **Restore**: creates a **new** table from backup. **Best**: enable **PITR** for production; use **on-demand** for major releases or compliance snapshots.

---

## Q4. (Intermediate) Production scenario: You need to restore an S3 bucket to a point 7 days ago (objects deleted or overwritten since then). How do you do it?

**Answer:**  
(1) **Versioning**: if **versioning** was enabled, **list object versions** and **restore** (or copy) **previous** versions; delete markers can be removed to “undelete.” (2) **No versioning**: if **Cross-Region Replication** or **copy** to another bucket was in place, restore from the other bucket. (3) **Backup**: if you have **backup** (e.g. AWS Backup, third-party) that has objects from 7 days ago, restore from backup. **Prevention**: **enable versioning** and **lifecycle** (e.g. retain noncurrent versions) so you can restore.

---

## Q5. (Intermediate) What is AWS Backup? What can it back up?

**Answer:**  
**AWS Backup** is a **centralized** backup service: **schedule** and **policy-based** backups for **RDS**, **DynamoDB**, **EBS**, **EFS**, **S3** (via Storage Gateway or selected resources), **FSx**, etc. **Features**: **retention**, **cross-region copy**, **restore**, **compliance** (backup vault lock). Use for **unified** backup policy across services and **automated** cross-region copy.

---

## Q6. (Advanced) Production scenario: Define RTO 1 hour and RPO 5 minutes for a critical app (API + RDS + S3). Design backup and failover without active-active.

**Answer:**  
**RPO 5 min**: (1) **RDS**: **cross-region** read replica or **automated backup** copied to second region (e.g. every 5 min via snapshot copy or replica lag < 5 min). (2) **S3**: **CRR** (Cross-Region Replication) so second region has copies within minutes. (3) **App state**: minimal (sessions in DynamoDB or stateless). **RTO 1 h**: (1) **Secondary region**: **pre-deployed** stack (ALB, Lambda/EC2, API Gateway) or **automated** deploy (CodePipeline, CloudFormation). (2) **Route 53** health check on primary; **failover** to secondary. (3) **RDS**: **promote** replica or **restore** from latest backup/snapshot in secondary region; **S3** already replicated. (4) **Runbook**: update DNS or config to point to promoted RDS and secondary ALB; test regularly.

---

## Q7. (Advanced) What is a backup vault lock in AWS Backup? When would you use it?

**Answer:**  
**Vault lock**: **lock** a backup vault so **retention** and **delete** rules cannot be **reduced** or **removed** (compliance). Once locked, even **root** cannot shorten retention until the lock period expires. **Use** for **compliance** (e.g. regulatory 7-year retention). **Plan**: set **minimum** retention (e.g. 2555 days); then lock; test restores before locking.

---

## Q8. (Advanced) How do you test disaster recovery without affecting production? What is a drill?

**Answer:**  
(1) **Restore in isolated env**: restore **RDS** snapshot, **S3** copy, **DynamoDB** backup to **separate** account or **staging**; run app against restored data; verify. (2) **Failover drill**: **periodically** (e.g. quarterly) **trigger** Route 53 failover to **secondary** (or switch traffic in test); verify app works; **switch back**. (3) **Runbook**: document steps; **time** the drill to validate RTO. (4) **No production impact**: use **read-only** or **copy** of data; failover drill can be brief and reverted. **Senior**: “We run a DR drill every quarter; we restore backups to staging and run smoke tests; we also test Route 53 failover to secondary region.”

---

## Q9. (Advanced) Compare DR for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: **automated** backups (RDS, S3 versioning); **snapshot** to second region (manual or script); **documented** restore steps; RTO/RPO hours. **Medium**: **automated** cross-region copy; **pre-deployed** or scripted secondary; **Route 53** failover; **quarterly** drill. **Enterprise**: **RTO/RPO** targets; **automated** failover where possible; **AWS Backup** and vault lock; **regular** drills and **runbooks**; **compliance** and audit.

---

## Q10. (Advanced) Senior red flags to avoid in DR

**Answer:**  
- **No backups** or backup not tested (restore fails when needed).  
- **Backups only in same region** (region failure = data loss).  
- **No runbook** or untested failover.  
- **Assuming** “replica” means “ready to serve” (test promotion).  
- **No RTO/RPO** defined (design is arbitrary).  
- **Ignoring** backup retention and compliance (vault lock, retention policy).  
- **No drills** (first failover during real disaster).

---

**Tradeoffs:** Startup: backups, same-region. Medium: cross-region copy, failover. Enterprise: automated DR, vault lock, drills.
