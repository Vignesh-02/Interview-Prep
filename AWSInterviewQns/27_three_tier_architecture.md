# 27. Three-Tier Architecture (EC2, Lambda, EKS) — Senior

## Q1. (Beginner) What is a classic three-tier architecture? Name the tiers.

**Answer:**  
**Three-tier**: (1) **Presentation** — user-facing (web/app server, static assets). (2) **Application** — business logic (API, services). (3) **Data** — persistence (RDS, DynamoDB, S3). **AWS**: e.g. **CloudFront** + **ALB** (presentation), **EC2** or **Lambda** (application), **RDS** + **S3** (data). Separation allows scale and security (e.g. DB in private subnet).

---

## Q2. (Beginner) How would you deploy a three-tier app using only EC2? What goes in public vs private subnet?

**Answer:**  
**Public subnet**: **ALB** (or single web server for small); optionally **NAT Gateway**. **Private subnet**: **App** EC2 (API, business logic); **Data** — **RDS** (and S3 access via Gateway endpoint or NAT). **Order**: Internet → ALB (public) → App (private) → RDS (private). **Security groups**: ALB allows 80/443 from internet; App allows from ALB only; RDS allows from App only. **No** DB or app in public subnet.

---

## Q3. (Intermediate) How would the same three-tier app look with Lambda as the application tier? What are the main components?

**Answer:**  
**Presentation**: **CloudFront** (static) + **API Gateway** (API). **Application**: **Lambda** (API handlers, business logic). **Data**: **RDS** (with **RDS Proxy**) or **DynamoDB**, **S3**. **Flow**: Client → API Gateway → Lambda → RDS Proxy → RDS (or DynamoDB). **VPC**: Lambda in VPC only if it needs to reach RDS in private subnet; use **RDS Proxy** for connection pooling. **No** EC2 to manage for app tier.

---

## Q4. (Intermediate) How would you add EKS as the application tier? What replaces Lambda or EC2?

**Answer:**  
**Presentation**: **ALB** (via Ingress) or **CloudFront** + **ALB**. **Application**: **EKS** — **pods** (containers) run your API/services; **Service** (LoadBalancer) exposes ALB; **Ingress** for path/host routing. **Data**: **RDS**, **DynamoDB**, **S3** (pods use **IRSA** for AWS APIs). **Flow**: Client → ALB → Ingress → Service → Pods → RDS/DynamoDB. **EKS** replaces EC2 app servers or Lambda with **Kubernetes**-managed containers.

---

## Q5. (Intermediate) Production scenario: Draw a three-tier architecture for 50k users: web + API + RDS. Include EC2, Lambda, ALB, RDS, CloudWatch. Which tier would you use Lambda vs EC2 and why?

**Answer:**  
**Option A — Lambda**: **CloudFront** (static) + **API Gateway** (API) → **Lambda** (API tier) → **RDS Proxy** → **RDS**. **Option B — EC2**: **ALB** → **EC2** (auto-scaled) → **RDS**. **Choice**: **Lambda** for **variable** traffic and **no** server management; **EC2** for **steady** load and **stateful** or long-running needs. For **50k users** (moderate): **Lambda** + API Gateway + RDS Proxy is suitable; use **EC2** if you have heavy compute or need persistent connections. **CloudWatch**: metrics and logs for ALB, Lambda/EC2, RDS; alarms on errors and latency.

---

## Q6. (Advanced) Production scenario: Design a three-tier system that uses API Gateway, Lambda, EKS (for one heavy service), RDS, DynamoDB, S3, SQS, CloudWatch, and ECR. Describe the flow for “user uploads document, backend processes it, result stored.”

**Answer:**  
(1) **Upload**: Client → **API Gateway** → **Lambda** (auth, validate) → **S3** (store document); Lambda sends message to **SQS** (job queue). (2) **Process**: **EKS** worker (or **Lambda** consumer) reads from **SQS**; processes document (heavy compute); writes result to **DynamoDB** (or **S3**); deletes message. (3) **Storage**: **RDS** for user/session data; **DynamoDB** for job result metadata; **S3** for raw and processed files. (4) **Images**: **ECR** for EKS worker image. (5) **Observability**: **CloudWatch** (logs, metrics); **X-Ray** for tracing; alarms on SQS DLQ, Lambda errors, EKS pod failures. **Flow**: API Gateway → Lambda → S3 + SQS → EKS (or Lambda) → DynamoDB/S3; all monitored with CloudWatch.

---

## Q7. (Advanced) How do you secure the three tiers (presentation, application, data) so that only the intended caller can reach each? Include WAF, security groups, and IAM.

**Answer:**  
(1) **Presentation**: **WAF** on CloudFront/ALB (rate limit, allow list, geo). **ALB** in public subnet; **SG** allows 80/443 from internet (or CloudFront only). (2) **Application**: **App** (EC2/Lambda/EKS) in **private** subnet or serverless; **SG** allows only from **ALB SG** (or API Gateway). **IAM**: app role has least privilege (e.g. RDS, S3, DynamoDB). (3) **Data**: **RDS** in **private** subnet; **SG** allows only from **App SG**. **DynamoDB/S3**: no SG; **IAM** only (app role). **No** 0.0.0.0/0 on app or data; **secrets** in Secrets Manager.

---

## Q8. (Advanced) What is the role of ECR in a three-tier app that uses EKS? Where does CodePipeline fit?

**Answer:**  
**ECR**: stores **Docker images** for EKS **pods** (e.g. API image, worker image). **Build**: **CodeBuild** builds image from source; pushes to **ECR** (tag with commit or version). **EKS**: **pods** pull image from ECR (IRSA or node role for ECR pull). **CodePipeline**: **Source** (e.g. GitHub) → **Build** (CodeBuild, push to ECR) → **Deploy** (update EKS deployment with new image tag). **Result**: CI/CD produces images in ECR; EKS runs those images.

---

## Q9. (Advanced) Compare three-tier on EC2 vs Lambda vs EKS for startup vs enterprise. When would you choose each?

**Answer:**  
**EC2**: full control; good for **legacy** or **stateful**; **ops** burden. **Lambda**: **serverless**; scale to zero; good for **API** and **event-driven**; cold start and 15 min limit. **EKS**: **Kubernetes**; portability; good for **microservices** and **existing k8s**; more complex. **Startup**: **Lambda** + API Gateway + RDS/DynamoDB (fast, low ops). **Medium**: **EC2** or **EKS** if team wants containers; **Lambda** for events. **Enterprise**: **EKS** for many services; **Lambda** for events and APIs; **EC2** for special workloads.

---

## Q10. (Advanced) Senior red flags to avoid in three-tier design

**Answer:**  
- **DB or app in public subnet** (use private).  
- **No WAF** or open ALB to world without rate limit.  
- **Single point of failure** (one AZ, one instance).  
- **No health checks** or auto-scaling for app tier.  
- **Secrets** in env or code (use Secrets Manager, IAM).  
- **No observability** (logs, metrics, tracing).  
- **Lambda** talking to RDS without **RDS Proxy** (connection exhaustion).  
- **No CI/CD** (manual deploy, no ECR/CodePipeline).

---

**Tradeoffs:** Startup: Lambda + API Gateway + RDS/DynamoDB. Medium: EC2 or EKS + ALB + RDS. Enterprise: EKS, multi-AZ, WAF, full observability.
