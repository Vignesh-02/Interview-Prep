# 23. EKS & Kubernetes on AWS — Senior

## Q1. (Beginner) What is EKS? What does AWS manage vs what do you manage?

**Answer:**  
**EKS** is managed **Kubernetes** on AWS. **AWS manages**: control plane (API server, etcd, scheduler, controller manager); availability and patches. **You manage**: **worker nodes** (EC2 or Fargate); **pods**, **deployments**, **services**; **add-ons** (CNI, CoreDNS, kube-proxy); **upgrades** of node AMI and add-ons. You get a **kubeconfig** to talk to the cluster; run workloads on nodes.

---

## Q2. (Beginner) What is IRSA (IAM Roles for Service Accounts)? Why use it instead of instance roles for pods?

**Answer:**  
**IRSA**: **Pod** (via **ServiceAccount**) assumes an **IAM role**; no need to give the **node** (EC2) that role. **Benefit**: **least privilege** per pod (e.g. pod A needs S3, pod B needs DynamoDB — different roles). **Instance role**: all pods on that node share the node’s role (over-privilege). **Use IRSA** for production; create IAM role with OIDC trust (EKS cluster OIDC); annotate ServiceAccount with role ARN; pods using that SA get the role.

---

## Q3. (Intermediate) How do you expose a Kubernetes service (e.g. web app) to the internet on EKS? What AWS components are involved?

**Answer:**  
(1) **Service** type **LoadBalancer**: EKS (with AWS Load Balancer Controller) creates an **ALB** or **NLB** and points it to the service’s endpoints. (2) **Ingress**: create **Ingress** resource; **ALB Ingress Controller** (or AWS Load Balancer Controller) provisions an **ALB** and routes by host/path to **Services**. (3) **Security groups**: controller creates SG and allows traffic to nodes/pods. (4) **Route 53**: point DNS to ALB. **Typical**: **Ingress** + ALB + optional cert (ACM) via annotation.

---

## Q4. (Intermediate) What is the AWS Load Balancer Controller? What does it do when you create an Ingress?

**Answer:**  
**AWS Load Balancer Controller**: Kubernetes **controller** that watches **Ingress** and **Service** (type LoadBalancer) resources; it **creates/updates** **ALB** or **NLB** in AWS and configures **target groups** to point to **pods** (via NodePort or instance target type). **When you create Ingress**: controller creates an ALB; adds **listener** and **rules** from Ingress spec; registers **targets** (nodes or pods); updates **security groups**. So you manage **Kubernetes** resources; controller manages **AWS** load balancers.

---

## Q5. (Intermediate) Production scenario: Your EKS cluster runs in private subnets. Pods need to pull images from ECR. How do you enable that without public internet?

**Answer:**  
(1) **VPC Endpoints**: create **Interface endpoints** for **ECR API** (ecr.api) and **ECR DKR** (ecr.dkr) and **S3** (Gateway endpoint) in the VPC; nodes/pods reach ECR via **private** network. (2) **IRSA** or **node IAM role**: give **pull** permission (ecr:GetDownloadUrlForLayer, etc.) to the node role or pod role. (3) **No NAT** needed for ECR if endpoints are in place. **Result**: private subnet nodes pull images from ECR without internet.

---

## Q6. (Advanced) How do you run EKS with Fargate? What are the tradeoffs vs EC2 nodes?

**Answer:**  
**EKS Fargate**: create **Fargate profile** (selector = namespace and optionally labels); pods that match run on **Fargate** (no EC2 to manage). **Tradeoffs**: **Fargate** — no node management, **higher** cost per pod, **no** daemonsets or privileged pods, **limited** to supported config. **EC2 nodes** — you manage nodes (or use managed node groups), **cheaper** at scale, **full** Kubernetes (daemonsets, etc.). Use **Fargate** for simplicity and isolation; use **EC2** for cost and flexibility.

---

## Q7. (Advanced) Production scenario: You deploy 10 microservices on EKS. Each needs different IAM permissions (S3, DynamoDB, Secrets Manager). How do you set up IAM without giving the node role all permissions?

**Answer:**  
Use **IRSA** for each service: (1) Create **IAM role** per service (e.g. app-a-s3, app-b-dynamodb); trust policy = EKS OIDC provider and namespace/servicename. (2) Create **ServiceAccount** in each namespace (e.g. app-a) with annotation `eks.amazonaws.com/role-arn: arn:aws:iam::...:role/app-a-s3`. (3) **Pods** use `serviceAccountName: app-a`; they get the role’s credentials via projected volume. (4) **Node role** has only **minimal** permissions (EKS, ECR pull). **Result**: each pod has least-privilege IAM.

---

## Q8. (Advanced) What is Cluster Autoscaler (Karpenter or CA)? How does it interact with EKS and EC2?

**Answer:**  
**Cluster Autoscaler** (or **Karpenter**): scales the **number of nodes** (or node groups) based on **pending pods** (unschedulable due to insufficient CPU/memory). **CA**: adds/removes **EC2** instances in **node groups**; **Karpenter** provisions **individual** nodes (or Fargate) per pod needs (often faster and more efficient). **Interaction**: pods are **pending** → autoscaler adds nodes → scheduler places pods. **Configure**: set **min/max** nodes and **resource requests** on pods so autoscaler can make good decisions.

---

## Q9. (Advanced) Compare EKS for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: small EKS cluster; **managed node group**; **ALB** via Load Balancer Controller; **IRSA** for AWS access. **Medium**: **Fargate** or mixed; **multiple** namespaces; **monitoring** (Prometheus, CloudWatch); **CI/CD** (Argo CD, Flux, or CodePipeline). **Enterprise**: **multi-tenant** or multi-cluster; **Karpenter** or CA; **Pod Security** (PSS); **network policies**; **private** cluster and endpoints; **compliance** and scanning (EKS Audit, Trivy).

---

## Q10. (Advanced) Senior red flags to avoid with EKS

**Answer:**  
- **Node role** with broad permissions (use IRSA).  
- **Pods** running as root or privileged in production.  
- **No resource requests/limits** (noisy neighbor, bad scaling).  
- **Public** API endpoint without restrict access.  
- **No backup** (Velero, etcd backup for critical state).  
- **Ignoring** upgrade path (control plane and node AMI).  
- **No network policies** (all pods can talk to all pods).  
- **Images** from untrusted registries without scanning.

---

**Tradeoffs:** Startup: managed node group, ALB, IRSA. Medium: Fargate option, monitoring. Enterprise: Karpenter, PSS, network policies, compliance.
