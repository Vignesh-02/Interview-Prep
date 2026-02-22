# 4. VPC & Networking

## Q1. (Beginner) What is a VPC? What are subnets and how do public and private subnets differ?

**Answer:**  
**VPC** is your isolated network in AWS (CIDR block, e.g. 10.0.0.0/16). **Subnets** are segments of the VPC (e.g. 10.0.1.0/24) in one AZ. **Public subnet**: has route to an **Internet Gateway** (IGW); instances with public IP can be reached from internet. **Private subnet**: no direct route to IGW; outbound via **NAT Gateway** or NAT instance; not directly reachable from internet. Put DBs and app servers in private subnets; put load balancers in public (or use public subnet for ALB only).

---

## Q2. (Beginner) What is a Security Group vs a Network ACL (NACL)?

**Answer:**  
**Security Group**: stateful; **allow** rules only (implicit deny); applied to ENI/instance; can reference other SGs. **NACL**: stateless; **allow and deny** rules; applied at subnet level; order matters. Use **SG** for instance-level control (main tool). Use **NACL** for subnet-level allow/deny (e.g. block a range) or as extra layer; remember to allow return traffic in NACL (stateful vs stateless).

---

## Q3. (Intermediate) How do you allow an EC2 instance in a private subnet to download packages from the internet (e.g. yum install)?

**Answer:**  
Use a **NAT Gateway** (or NAT instance) in a **public** subnet. **Private subnet** route table: default (0.0.0.0/0) → NAT Gateway. NAT Gateway has a route to IGW. So outbound traffic from the instance goes to NAT → IGW → internet; return traffic comes back via NAT (stateful). Instance does **not** need a public IP. Cost: NAT Gateway is hourly + data processing; for low traffic, NAT instance can be cheaper.

---

## Q4. (Intermediate) You have a VPC 10.0.0.0/16. You need 3 public and 3 private subnets (one pair per AZ). How do you size the subnets?

**Answer:**  
Split 10.0.0.0/16 into 6 subnets. Example: use /20 per subnet (4k IPs each) — 10.0.0.0/20, 10.0.16.0/20, 10.0.32.0/20 (public), 10.0.48.0/20, 10.0.64.0/20, 10.0.80.0/20 (private). Or /19 for 8k each. Reserve space for future (e.g. VPC has 65k addresses; 6×/20 uses a portion). Place one public and one private in each of 3 AZs for HA.

---

## Q5. (Intermediate) What is an Internet Gateway (IGW)? Can a private subnet have a route to the IGW?

**Answer:**  
**IGW** is the VPC component that connects the VPC to the public internet (for both inbound and outbound). A **private subnet** typically has **no** route to the IGW in its route table; its default route points to a **NAT Gateway** (in a public subnet) for outbound-only access. If you add 0.0.0.0/0 → IGW to a private subnet’s route table, instances there could get internet if they have a public IP (not recommended for “private” design).

---

## Q6. (Advanced) Production scenario: Your web app (ALB + EC2 in private subnets) must allow traffic only from a CDN (CloudFront). How do you restrict ALB to accept only CloudFront requests?

**Answer:**  
**Option 1**: **Restrict ALB SG** to allow inbound 443 only from **CloudFront IP ranges** (AWS publishes them; update periodically). Add prefix list or CIDRs to SG. **Option 2**: **Custom header** — configure CloudFront to add a secret header; ALB or app validates it (weaker; header can be spoofed if leaked). **Option 3**: **VPC-only ALB** and put CloudFront origin in VPC (complex). **Best**: use **CloudFront and restrict ALB SG** to CloudFront prefix list (managed by AWS) so only CloudFront IPs can hit ALB; no direct public access to ALB.

---

## Q7. (Advanced) What is VPC Flow Logs? When would you enable them and where do you store the logs?

**Answer:**  
**VPC Flow Logs** capture **accepted/rejected** IP traffic at VPC, subnet, or ENI level (source, dest, ports, action). **Use**: security analysis, troubleshooting connectivity, compliance. **Destination**: **CloudWatch Logs** (query with Insights) or **S3** (long retention, Athena). Enable for production VPCs; store in S3 with lifecycle for cost. **Note**: flow logs are not full packet capture; they are metadata (5-tuple + bytes/packets).

---

## Q8. (Advanced) Production scenario: You have EC2 in private subnet A and RDS in private subnet B (same VPC). EC2 cannot reach RDS on port 3306. List checks you would perform.

**Answer:**  
(1) **Security groups**: RDS SG must allow inbound 3306 from EC2’s SG (or from EC2 subnet CIDR). EC2 SG outbound must allow 3306 (or 0.0.0.0/0). (2) **Route tables**: both subnets should have local route (10.0.0.0/16 → local); no need for IGW for same-VPC traffic. (3) **NACL**: if used, both inbound and outbound for 3306 and ephemeral ports. (4) **RDS endpoint**: correct host and port in app. (5) **RDS status**: available and in same VPC. Most common: RDS SG not allowing EC2 SG.

---

## Q9. (Advanced) Compare VPC design for startup (one VPC, simple) vs enterprise (multi-VPC, shared services, transit). What does each typically need?

**Answer:**  
**Startup**: one VPC per region; public/private subnets in 2 AZs; NAT Gateway (or single NAT instance); one set of SGs. **Enterprise**: **multi-VPC** (per env or per team); **Transit Gateway** or VPC peering for connectivity; **shared services** VPC (e.g. DNS, AD); **VPC Flow Logs** and monitoring; **PrivateLink** for AWS or third-party services; strict **NACLs** and SGs; IPAM for CIDR planning.

---

## Q10. (Advanced) Senior red flags to avoid with VPC

**Answer:**  
- **Single AZ** for production (no HA).  
- **Overlapping CIDRs** when peering or connecting to on-prem.  
- **0.0.0.0/0** in security groups for production (restrict to ALB, known IPs).  
- **No NAT** for private subnets then giving instances public IPs to reach internet.  
- **Ignoring** flow logs and subnet sizing (running out of IPs).  
- **Opening** RDS/Elasticsearch to 0.0.0.0/0 “to debug.”  
- **No documentation** of VPC/subnet layout and route tables.

---

**Tradeoffs:** Startup: one VPC, 2 AZs, NAT. Medium: 2 AZs, separate subnets per tier, flow logs. Enterprise: multi-VPC, Transit Gateway, PrivateLink, IPAM, logging.
