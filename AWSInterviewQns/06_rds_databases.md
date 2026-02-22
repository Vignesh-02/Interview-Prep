# 6. RDS & Relational Databases

## Q1. (Beginner) What is Amazon RDS? What engines does it support?

**Answer:**  
**RDS** is managed relational database service. **Engines**: MySQL, MariaDB, PostgreSQL, Oracle, SQL Server; plus **Aurora** (MySQL/PostgreSQL compatible, AWS-managed). RDS handles provisioning, patching, backups, multi-AZ; you manage schema and queries.

---

## Q2. (Beginner) What is Multi-AZ deployment? How does it differ from a read replica?

**Answer:**  
**Multi-AZ**: **one** primary; synchronous replica in another AZ for **failover** only (not for read scaling). RDS automatically fails over to the standby if primary fails. **Read replica**: **asynchronous** copy; used for **read scaling** and sometimes for failover (promote replica). Multi-AZ = HA; read replica(s) = read scaling + optional DR.

---

## Q3. (Intermediate) Your backend (Node.js or Python) connects to RDS. How do you avoid storing the database password in code or env files in production?

**Answer:**  
Use **Secrets Manager** (or Parameter Store): store DB credentials; rotate them with Secrets Manager rotation. **At runtime**: app fetches secret via AWS SDK (with IAM role); caches it and reuses until rotation. **Example (Node.js)**: `const secret = await secretsManager.getSecretValue({ SecretId: 'prod/rds/app' }).promise(); const { username, password, host } = JSON.parse(secret.SecretString);` Then create DB connection. **Alternative**: **RDS Proxy** — app connects to Proxy with one user; Proxy uses Secrets Manager and pools connections.

---

## Q4. (Intermediate) What is RDS Proxy? When would you recommend it for Lambda or many EC2 instances?

**Answer:**  
**RDS Proxy** sits between your app and RDS; it **pools connections** and uses **Secrets Manager** for credentials. **Use when**: (1) **Lambda** — many concurrent invocations would open too many DB connections; Proxy pools and limits connections to RDS. (2) **Many EC2/containers** — same benefit. (3) **Failover** — Proxy can mask instance change. **Recommend** for serverless + RDS and for any app with high connection churn.

---

## Q5. (Intermediate) How do you restore an RDS instance from a snapshot? What happens to the current instance?

**Answer:**  
**Restore**: in RDS console or CLI, choose **Restore from snapshot**; pick the snapshot; you get a **new** instance (new endpoint). Current instance is **unchanged** unless you replace it. Use restore for **recovery** (new instance from backup) or **clone** (e.g. prod snapshot → staging). After restore, point app to new endpoint; optionally make snapshot of current before major changes.

---

## Q6. (Advanced) Production scenario: Your API uses RDS MySQL with 20 connections max. You deploy 50 Lambda functions that each open a DB connection. You see “Too many connections.” How do you fix it without changing the RDS size?

**Answer:**  
(1) **RDS Proxy**: put **RDS Proxy** in front of RDS; Lambdas connect to **Proxy** (Proxy has its own max connections, e.g. 100); Proxy **pools** and uses far fewer connections to RDS (e.g. 20). (2) **Connection reuse**: in Lambda, reuse a single connection per execution context (global variable); don’t open per request. (3) **Limit concurrency**: set **reserved concurrency** on the Lambda so not all 50 run at once. **Best**: RDS Proxy + connection reuse in Lambda.

---

## Q7. (Advanced) When would you choose Aurora over standard RDS (e.g. MySQL)? Include cost and scale.

**Answer:**  
**Aurora**: auto-scaling storage; **15 read replicas** (read scaling); faster failover; **global** databases for multi-region; higher **throughput**. **Cost**: Aurora is typically more expensive than RDS for same instance size. **Choose Aurora** when: you need **read scaling** (many replicas), **global** replication, or very high availability. **Choose RDS** when: single instance or 1–2 replicas is enough and cost is a priority. **Startup**: RDS often enough. **Enterprise**: Aurora for critical, read-heavy workloads.

---

## Q8. (Advanced) Production scenario: RDS CPU is constantly at 90%. How do you diagnose and what are the options (without “just add more CPU”)?

**Answer:**  
**Diagnose**: (1) **Performance Insights** (RDS) — top SQL by load, wait events. (2) **Slow query log** — enable and analyze. (3) **CloudWatch** — CPU, connections, read/write IOPS. **Options**: (1) **Optimize queries** — indexes, rewrite, reduce N+1. (2) **Read replicas** — offload reads. (3) **Right-size** — larger instance if CPU-bound and query tuning is done. (4) **Connection pooling** — RDS Proxy or app-side to reduce connection overhead. **Senior answer**: “I’d use Performance Insights to find the top SQL and add indexes or optimize; then consider read replicas or scaling.”

---

## Q9. (Advanced) Compare RDS for startup (single instance, dev/staging/prod) vs enterprise (Multi-AZ, replicas, backup retention, compliance).

**Answer:**  
**Startup**: one RDS instance per env (or shared dev/staging); automated backups 7 days; single AZ acceptable for dev. **Medium**: prod **Multi-AZ**; 1–2 read replicas for read scaling; 30-day backup; encryption at rest. **Enterprise**: Multi-AZ; multiple read replicas; **Aurora Global** for DR; long backup retention and cross-region copy; **Performance Insights** and monitoring; strict security (no public, VPC, KMS, audit).

---

## Q10. (Advanced) Senior red flags to avoid with RDS

**Answer:**  
- **Public accessibility** on in production.  
- **Default port** and weak credentials; no rotation.  
- **No Multi-AZ** for production.  
- **Lambdas (or many app instances)** connecting without pooling (RDS Proxy or app pool).  
- **No backup** testing (restore drill).  
- **Only vertical scaling** — not using read replicas or query optimization first.  
- **Storing credentials** in env or code instead of Secrets Manager.  
- **Ignoring** Performance Insights or slow query logs.

---

**Tradeoffs:** Startup: RDS single-AZ, 7-day backup. Medium: Multi-AZ, read replica, RDS Proxy for Lambda. Enterprise: Aurora, global DB, long retention, encryption, audit.
