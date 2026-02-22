# 12. Load Balancing (ALB/NLB)

## Q1. (Beginner) What is an Application Load Balancer (ALB)? What layer does it operate at?

**Answer:**  
**ALB** operates at **Layer 7** (HTTP/HTTPS): it understands URLs, headers, and can route by path or host. It supports **SSL termination**, **sticky sessions**, **WebSockets**, and **Lambda** as target. Use for web apps and APIs. **NLB** is Layer 4 (TCP/UDP); **CLB** is legacy (Layer 4/7).

---

## Q2. (Beginner) What is the difference between ALB and NLB? When would you choose NLB?

**Answer:**  
**ALB**: L7; path/host routing; SSL termination; best for HTTP/HTTPS. **NLB**: L4; **ultra-low latency**, **static IP**, **preserves source IP**; handles millions of requests/s; no path routing. **Choose NLB** for: TCP/UDP (e.g. game, custom protocol), need for static IP or source IP, or extreme performance. **Choose ALB** for HTTP/HTTPS and content-based routing.

---

## Q3. (Intermediate) How do you configure an ALB to route /api/* to one target group and /* to another (e.g. frontend vs backend)?

**Answer:**  
Use **listener rules**: on the HTTPS listener, add rules in **priority** order. (1) Rule 1: path is /api/* → forward to **backend** target group. (2) Rule 2: path is /* → forward to **frontend** target group. Default action can be “fixed response” or lowest-priority forward. Path pattern is prefix or exact; can also use host-based routing (e.g. api.example.com vs www.example.com).

---

## Q4. (Intermediate) What is a target group? What are health checks and how do you set them for an API?

**Answer:**  
**Target group**: set of targets (EC2, IP, Lambda) and their **health check** config. **Health check**: ALB/NLB periodically sends a request (HTTP/HTTPS to a path, e.g. /health); **healthy threshold** (consecutive success) and **unhealthy threshold** (consecutive failure) determine state. Set **interval** (e.g. 30 s), **timeout** (5 s), **path** (/health), **expected code** (200). Unhealthy targets get no traffic.

---

## Q5. (Intermediate) Your ALB is in a public subnet; EC2 targets are in private subnets. What must be true about the VPC and security groups?

**Answer:**  
**VPC**: ALB subnet must have route to **IGW** (public subnet); target subnets can be private (route to NAT for outbound). **Security groups**: (1) **ALB SG**: inbound 80/443 from 0.0.0.0/0 (or restrict to CloudFront); outbound to target SG or private subnet. (2) **Target SG**: inbound 80 (or app port) from **ALB SG** only; outbound as needed. So only the ALB can reach the targets on the app port.

---

## Q6. (Advanced) Production scenario: You run a web app (ALB + EC2) serving 50k users. You add a new microservice and want 5% of traffic to go to the new version (canary). How do you do this with ALB?

**Answer:**  
**Weighted target groups**: (1) Create **two** target groups — “current” (existing instances) and “canary” (new version instances). (2) **Listener rule**: path or host as needed; action = **forward** with **weight**: 95% to current, 5% to canary. (3) **Health checks** on both; canary instances register in canary group. (4) Monitor errors and latency for canary; increase weight or roll back. **Alternative**: use **Route 53 weighted** in front of two ALBs (more complex). ALB weighted target groups are simpler for same ALB.

---

## Q7. (Advanced) What is connection draining (deregistration delay)? Why is it important when scaling in or deploying?

**Answer:**  
**Connection draining** (deregistration delay): when a target is **deregistering**, the ALB stops sending **new** requests but allows **in-flight** requests to complete for up to this time (e.g. 30–300 s). **Important**: during **scale-in** or **deploy**, targets are deregistered; without draining, in-flight requests would be cut off. Set delay ≥ typical request duration (e.g. 60–120 s for API). **Lambda** targets don’t use this (no long connections).

---

## Q8. (Advanced) Production scenario: You need to expose an internal TCP service (e.g. Redis or custom port) to clients in another VPC. You want one stable endpoint and high throughput. What do you use?

**Answer:**  
Use **NLB** (Layer 4): (1) Create **NLB** with listener on the TCP port; targets = your service (EC2 or IP). (2) NLB gets a **static** (elastic) IP or you use the NLB DNS name. (3) **Cross-VPC**: use **PrivateLink** (NLB as endpoint service) so the other VPC can create an interface endpoint and connect privately; or **VPC peering** + NLB in one VPC, route from other VPC. **Stable endpoint** = NLB DNS or static IP; **high throughput** = NLB handles it. Don’t use ALB for raw TCP.

---

## Q9. (Advanced) Compare load balancing for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: one ALB; public subnets; one target group; HTTP redirect to HTTPS; single cert. **Medium**: ALB in multiple AZs; path-based or host-based rules; WAF; access logs to S3. **Enterprise**: **NLB** for TCP or static IP; **internal** ALB/NLB for microservices; **PrivateLink** for cross-account/VPC; **connection draining** and lifecycle hooks; strict **security groups** and logging.

---

## Q10. (Advanced) Senior red flags to avoid with load balancing

**Answer:**  
- **Single AZ** for ALB or targets (use 2+ AZs).  
- **Target SG** allowing 0.0.0.0/0 on app port (allow only ALB SG).  
- **No health check** or wrong path (e.g. / that returns 404).  
- **Zero deregistration delay** during deploys (in-flight requests dropped).  
- **No access logs** (enable for audit and debugging).  
- **Using CLB** for new workloads (prefer ALB/NLB).  
- **Ignoring** target response time and unhealthy host metrics.

---

**Tradeoffs:** Startup: one ALB, 2 AZs. Medium: path/host routing, WAF, logs. Enterprise: NLB where needed, PrivateLink, multi-VPC.
