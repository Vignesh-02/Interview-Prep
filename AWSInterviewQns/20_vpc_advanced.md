# 20. VPC Advanced (Peering, Transit Gateway) — Senior

## Q1. (Beginner) What is VPC peering? What are its limitations?

**Answer:**  
**VPC peering**: connect **two VPCs** (same or different accounts) so instances can communicate using **private IPs**. **Limitations**: **no transitive** peering (A–B and B–C does not imply A–C); **no overlapping** CIDRs; **one** peering per pair; **region** (same region or cross-region peering). Use for **direct** VPC-to-VPC; for many VPCs use **Transit Gateway**.

---

## Q2. (Beginner) What is a VPC endpoint? What is the difference between Gateway and Interface endpoints?

**Answer:**  
**VPC endpoint**: private connection from your VPC to an **AWS service** (or custom) without going through the internet. **Gateway endpoint**: for **S3** and **DynamoDB**; free; you add a **route** in route table to a prefix list (e.g. com.amazonaws.region.s3). **Interface endpoint** (PrivateLink): **ENI** in your subnet; used for most other services (e.g. ECR, Secrets Manager, SQS); you pay per AZ and hour + data. Use **Gateway** for S3/DynamoDB; **Interface** when the service doesn’t support Gateway.

---

## Q3. (Intermediate) You have 10 VPCs (dev, staging, prod per team). You want centralised outbound internet and shared services (e.g. DNS). What do you use?

**Answer:**  
**Transit Gateway**: attach all 10 VPCs to one **Transit Gateway**; **route** between VPCs via TGW. **Outbound internet**: one **shared** VPC with **NAT Gateway** (or NAT instances); attach to TGW; other VPCs route 0.0.0.0/0 to TGW → shared VPC → NAT. **Shared services**: e.g. **Route 53 Resolver** or a **shared services VPC** (DNS, AD); other VPCs route to it via TGW. **Alternative**: **VPC peering** (many pairs, no transitive); TGW scales better for many VPCs.

---

## Q4. (Intermediate) What is AWS PrivateLink? When would you expose your service via PrivateLink?

**Answer:**  
**PrivateLink**: expose a **service** (e.g. your NLB/ALB or API) so **consumers** connect via an **interface endpoint** in their VPC; traffic stays on AWS; no public internet, no peering. **Expose your service**: create **Endpoint Service** (NLB in your VPC); **consumers** create **Interface Endpoint** and connect. Use when **enterprise** or **partners** need to access your service **privately** without opening to internet or managing peering.

---

## Q5. (Intermediate) Production scenario: Your Lambda needs to call an API that runs on EC2 in a private subnet. You don’t want the API on the public internet. How do you connect Lambda to the VPC and what are the implications?

**Answer:**  
(1) **Lambda in VPC**: configure Lambda with **VPC** (subnets, security groups); Lambda gets an ENI in your subnets and can reach EC2 by **private IP**. (2) **Implications**: **NAT** required for Lambda to reach **internet** (e.g. call external API); **cold start** can be longer (ENI attachment); **private subnet** for Lambda if you only need to reach EC2 (no outbound internet). (3) **Security groups**: Lambda SG allows outbound to EC2; EC2 SG allows inbound from Lambda SG on API port. **Alternative**: put API behind **PrivateLink** and call from Lambda via interface endpoint (no Lambda in VPC).

---

## Q6. (Advanced) You have VPC A (10.0.0.0/16) and VPC B (10.1.0.0/16). You peer them. Can an instance in A reach an instance in B? What about routing and security groups?

**Answer:**  
**Yes**, if: (1) **Peering connection** is **active** and **accepted**. (2) **Route tables**: in VPC A, add route **10.1.0.0/16** → peering connection (pcx-xxx); in VPC B, add route **10.0.0.0/16** → peering connection. (3) **Security groups**: instance in B must allow **inbound** from A’s CIDR or from A’s security group (if **referencing** SG across VPC is allowed — it is for same-region peering). So both routing and SG must allow the traffic.

---

## Q7. (Advanced) What is Transit Gateway attachment and route propagation? How do you restrict which VPCs can talk to which?

**Answer:**  
**Attachment**: each VPC (or VPN) is **attached** to the Transit Gateway. **Route propagation**: each attachment can **propagate** its routes to the TGW **route table**; TGW then **propagates** to other attachments (or you add **static** routes). **Restrict**: use **multiple** TGW route tables (e.g. one for dev, one for prod); **associate** attachments to the right table; **propagate** only allowed CIDRs. Or use **security groups** and **NACLs** in each VPC to restrict by subnet or SG.

---

## Q8. (Advanced) Production scenario: Your company has 3 AWS accounts (dev, staging, prod). Each has one VPC. You want dev and staging to reach a shared RDS in prod (private). Design the network and IAM.

**Answer:**  
(1) **Option A — Peering**: **Prod** VPC peers with **Dev** and **Staging** (two peering connections); prod RDS subnet route in dev/staging points to peering; RDS SG allows dev/staging VPC CIDRs (or peered SG). **Cross-account**: peering can be cross-account; prod accepts peering from dev/staging; each account adds route to prod CIDR via peering. (2) **Option B — Transit Gateway**: all three VPCs attach to **one** TGW (same or different accounts); TGW route table has routes to all VPCs; RDS in prod; dev/staging route to prod CIDR via TGW. **IAM**: dev/staging **roles** (e.g. EC2 or Lambda) need no direct RDS IAM; **network** access is enough; optionally use **Secrets Manager** in prod and allow dev/staging roles to read secret (cross-account). **Prefer TGW** if you have or plan more VPCs/accounts.

---

## Q9. (Advanced) Compare VPC design for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one VPC, 2 AZs, NAT, Gateway endpoints for S3/DynamoDB. **Medium**: VPC per env or per team; **peering** or **TGW**; **Interface endpoints** for critical services (no NAT for AWS APIs). **Enterprise**: **multi-account**; **TGW** or **Shared VPC**; **PrivateLink** for internal and partner services; **flow logs** and **traffic inspection** (e.g. Gateway Load Balancer); strict **NACLs** and **SG** policies.

---

## Q10. (Advanced) Senior red flags to avoid with VPC

**Answer:**  
- **Overlapping CIDRs** when peering or connecting to on-prem.  
- **Transitive routing** assumption (peering is not transitive).  
- **Lambda in VPC** without considering NAT cost and cold start.  
- **0.0.0.0/0** in security groups for production.  
- **No flow logs** or documentation of route tables.  
- **Exposing** internal APIs to 0.0.0.0/0 “temporarily.”  
- **Ignoring** endpoint policies (e.g. S3 Gateway endpoint policy to restrict bucket).

---

**Tradeoffs:** Startup: one VPC, endpoints. Medium: peering or TGW. Enterprise: TGW, PrivateLink, multi-account.
