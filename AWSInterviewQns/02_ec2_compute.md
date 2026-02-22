# 2. EC2 & Compute Basics

## Q1. (Beginner) What is EC2? What are instance types and what do “family” and “size” mean?

**Answer:**  
**EC2** is virtual servers in the cloud. **Instance type** = CPU, memory, storage, network (e.g. t3.micro, m5.large). **Family**: use case — t (burstable), m (general), c (compute), r (memory), etc. **Size**: micro, small, large, xlarge (roughly 2× per step). Choose by workload: CPU-bound → c; memory → r; general → m; bursty → t.

---

## Q2. (Beginner) What is an AMI? Why would you create a custom AMI?

**Answer:**  
**AMI** (Amazon Machine Image) is a template: OS, software, config. **Custom AMI**: pre-install app, agents, security patches so new instances start ready; faster boot and consistent config. Use for Auto Scaling (launch config/template uses your AMI) or for compliance (hardened image).

---

## Q3. (Intermediate) How do you allow SSH (port 22) to an EC2 instance only from your office IP? What AWS components are involved?

**Answer:**  
Use **Security Group** (SG) on the EC2 instance: **Inbound rule**: Type SSH (22), Source = your office public IP/32 (e.g. 203.0.113.10/32). No 0.0.0.0/0 for SSH in production. Optionally use **VPN** or **AWS Client VPN** and allow SG from VPN CIDR. **Network ACL** can add another layer but SG is the main control.

---

## Q4. (Intermediate) What is the difference between EC2 User Data and SSM Parameter Store (or Secrets Manager) for passing config at launch?

**Answer:**  
**User Data**: script or cloud-init at **first boot**; visible in console/describe; not for secrets (unless encrypted). Good for install scripts, instance-specific config. **Parameter Store / Secrets Manager**: fetch at runtime via SDK or SSM Agent; encrypted; rotation; no secret in User Data. **Best**: User Data to install app and maybe fetch parameter names; app reads secrets from Parameter Store/Secrets Manager at runtime.

---

## Q5. (Intermediate) Write a minimal User Data script (Linux) that installs Docker and runs a container from ECR on instance startup.

**Answer:**
```bash
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker pull 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
docker run -d -p 80:8080 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
```
Instance must have IAM role with ECR read; ensure SG allows port 80.

---

## Q6. (Advanced) Production scenario: Your web app runs on 5 EC2 instances behind an ALB. Traffic grows from 1k to 50k users. How do you scale and what metrics do you use? Include tradeoff for startup vs enterprise.

**Answer:**  
**Scale**: **Auto Scaling Group** (ASG) with min=5, max=20 (or higher); scale on **CPU** or **RequestCountPerTarget** (better for web). **Metrics**: CloudWatch — CPUUtilization, ALB RequestCount, TargetResponseTime, UnHealthyHostCount. Scale-out when CPU > 70% or requests per target high; scale-in with cooldown to avoid flapping. **Startup**: simple CPU-based scaling, single AZ or two AZs. **Enterprise**: Predictive Scaling, multiple AZs, custom metrics (e.g. queue depth), and lifecycle hooks for graceful drain.

---

## Q7. (Advanced) What is the difference between Spot, On-Demand, and Reserved Instances? When would you use each for a production web tier?

**Answer:**  
**On-Demand**: pay per hour; no commitment; use for baseline or unknown load. **Reserved** (1/3 yr): discount for commitment; use for steady baseline (e.g. always-on web tier). **Spot**: interruptible; up to 90% discount; use for fault-tolerant or batch. **Production web**: **On-Demand or Reserved** for the web tier (availability); **Spot** only for optional batch workers or with Spot Fleet + fallback. Mix: Reserved for baseline, On-Demand for ASG scale-out.

---

## Q8. (Advanced) Production scenario: You must deploy a legacy monolithic app that cannot run in containers. It needs 4 vCPU, 16 GB RAM, and runs on Windows. How do you choose instance type, storage, and high availability for 10k concurrent users?

**Answer:**  
**Instance**: e.g. **m5.xlarge** (4 vCPU, 16 GB) or **c5.xlarge** if CPU-bound. **Storage**: EBS gp3 for OS and app; size based on data. **HA**: **Multi-AZ** — 2+ instances in an ASG across 2 AZs behind ALB; no single point of failure. **Scaling**: ASG min=2, scale on CPU or custom metric. Consider **Reserved** for the baseline to save cost. For 10k users, estimate requests per second and add instances so CPU stays under ~70%.

---

## Q9. (Advanced) What are Graviton (ARM) instances? When would you recommend them over x86?

**Answer:**  
**Graviton** is AWS’s ARM-based processor (Graviton2/3). **Benefits**: often **better price-performance** (e.g. 20–40% cost saving) for compatible workloads. **Use when**: app and dependencies run on ARM (Node, Python, Java, Go, many Linux apps); avoid if you need x86-only binaries. **Recommend**: try **m7g/c7g** (Graviton3) for general/compute; compare cost and performance. Good for startup (cost) and enterprise (efficiency at scale).

---

## Q10. (Advanced) Senior red flags to avoid with EC2

**Answer:**  
- **Single instance** for production with no ASG or multi-AZ.  
- **SSH open to 0.0.0.0/0** or storing private keys in code.  
- **Secrets in User Data** or in plain config files.  
- **No monitoring** (CloudWatch) or alarms for CPU/memory/disk.  
- **Treating “add more RAM” as the only scaling** — use metrics and ASG.  
- **Using only On-Demand** at scale without Reserved or Savings Plans.  
- **No backup** (AMIs, EBS snapshots) or disaster recovery plan.  
- **Ignoring** patch management (use SSM Patch Manager or custom AMI updates).

---

**Tradeoffs:** Startup: On-Demand + ASG, 1–2 AZs. Medium: Reserved baseline + On-Demand scale-out, 2 AZs. Enterprise: Reserved/Savings Plans, multi-AZ, Predictive Scaling, automated patching.
