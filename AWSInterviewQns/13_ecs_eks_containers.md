# 13. ECS/EKS & Containers

## Q1. (Beginner) What is ECS? What is the difference between EC2 and Fargate launch types?

**Answer:**  
**ECS** (Elastic Container Service) runs **Docker** containers; you define **task definitions** (image, CPU, memory, env) and run them as **tasks** (service or standalone). **EC2 launch type**: tasks run on **your** EC2 instances (you manage the cluster). **Fargate**: **serverless** — no EC2 to manage; ECS runs tasks on AWS-managed infra. Use Fargate for simplicity; EC2 for cost control or special requirements.

---

## Q2. (Beginner) What is ECR? How do you push an image from your machine or CI to ECR?

**Answer:**  
**ECR** is AWS’s **container registry** (Docker-compatible). **Push**: (1) `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com`. (2) Tag image: `docker tag myapp:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest`. (3) `docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest`. **CI**: use IAM role (e.g. CodeBuild) with ECR push permissions; same login and push.

---

## Q3. (Intermediate) What is an ECS task definition? What are task role vs execution role?

**Answer:**  
**Task definition**: JSON that defines container(s), image, CPU/memory, env, logging, **task role**, **execution role**. **Execution role**: used by **ECS agent** to pull image (ECR), write logs (CloudWatch), pull secrets; needed for Fargate. **Task role**: assumed by the **containers** at runtime (e.g. access S3, DynamoDB); optional. So: execution = ECS infra; task = your app’s AWS permissions.

---

## Q4. (Intermediate) How do you run an ECS service behind an ALB? What are the main steps?

**Answer:**  
(1) **ALB** with listener (e.g. 80/443); **target group** (type = IP for Fargate, instance for EC2). (2) **Task definition**: container exposes a port (e.g. 8080); **health check** path. (3) **ECS Service**: linked to task definition; **load balancer** config — attach to the target group; **service discovery** optional. (4) ECS registers task **IP** (Fargate) or instance in the target group; ALB routes to tasks. (5) **Security groups**: ALB allows inbound; tasks allow inbound from ALB SG only.

---

## Q5. (Intermediate) What is EKS? How does it differ from ECS?

**Answer:**  
**EKS** is managed **Kubernetes** on AWS; you get a control plane (API server, etc.) managed by AWS; you run worker nodes (EC2 or Fargate). **ECS** is AWS-native orchestration (task definitions, services); no Kubernetes API. **EKS**: use when you need **Kubernetes** (portability, ecosystem, existing k8s skills). **ECS**: use when you want **simpler** AWS-native containers (Fargate, less concepts). Both use ECR for images.

---

## Q6. (Advanced) Production scenario: You run 10 microservices on ECS Fargate. Each service has 2 tasks. You want zero-downtime deployment and rollback. How do you configure the service and what do you monitor?

**Answer:**  
(1) **Deployment**: **rolling update**; **minimum healthy %** = 50 (or 100), **maximum %** = 200 so new tasks start before old stop. (2) **Health check**: ALB health check on /health; **grace period** so tasks don’t get killed before app is ready. (3) **Rollback**: ECS can **roll back** to previous task definition if deployment fails (enable **circuit breaker** — stop if too many failures). (4) **Monitor**: **Deployment** events; **target group** healthy count; **CloudWatch** errors and latency; alarm on unhealthy tasks or failed deployments. (5) **Blue/green** optional: two services, switch target group.

---

## Q7. (Advanced) How do you give an ECS task (Fargate) permission to read from S3 and write to DynamoDB without hardcoding keys?

**Answer:**  
Use **task role**: in the **task definition**, set **taskRoleArn** to an IAM role that has policies for `s3:GetObject` and `dynamodb:PutItem` (and similar) on the needed resources. **No keys** in env or code; the task assumes this role. **Secrets**: use **Secrets Manager** or **Parameter Store**; reference in task definition as env (ECS injects at start); task role needs `secretsmanager:GetSecretValue` or `ssm:GetParameters`.

---

## Q8. (Advanced) Production scenario: Your company wants to move from EC2 to containers. Compare ECS Fargate vs EKS (managed Kubernetes). Consider team size (5 devs), existing skills, and cost. Which would you recommend for a medium-sized product?

**Answer:**  
**ECS Fargate**: simpler; no nodes to manage; task definitions and services; lower ops; good for 5 devs without k8s experience; **cost**: per task (vCPU + memory). **EKS**: Kubernetes; more concepts (pods, deployments, ingress); **cost**: control plane ~$0.10/hr + nodes; need k8s skills or learning. **Recommendation**: **ECS Fargate** for “we want containers, not k8s” and smaller team; **EKS** if you need k8s ecosystem (Helm, operators, portability) or have k8s experience. For 5 devs and “medium product,” ECS Fargate is often the better fit unless there’s a strong k8s requirement.

---

## Q9. (Advanced) Compare containers (ECS/EKS) for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: ECS Fargate; ECR; one cluster; task definitions in code; ALB. **Medium**: ECS or EKS; multiple services; CI/CD (CodeBuild, CodePipeline); secrets in Secrets Manager; private subnets. **Enterprise**: **EKS** for portability and ecosystem; **multi-tenant** or multi-cluster; **IRSA** (pod IAM); **network policies**; **image scanning** (ECR or Trivy); compliance and audit.

---

## Q10. (Advanced) Senior red flags to avoid with ECS/EKS

**Answer:**  
- **No resource limits** (CPU/memory) on tasks/pods (risk of noisy neighbor).  
- **Running as root** or privileged in production.  
- **Secrets in env** or image (use Secrets Manager/Parameter Store or IAM).  
- **Single task** per service (no redundancy).  
- **No health checks** or wrong readiness/liveness.  
- **Public ECR** or images from untrusted registries without scanning.  
- **Ignoring** deployment circuit breaker and rollback.

---

**Tradeoffs:** Startup: ECS Fargate, ECR. Medium: ECS or EKS, CI/CD, secrets. Enterprise: EKS, IRSA, scanning, compliance.
