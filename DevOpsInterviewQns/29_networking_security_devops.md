# 29. Networking & Security in DevOps

## Q1. (Beginner) What is a network policy in Kubernetes? What does it do?

**Answer:**  
**Network** **policy**: **rule** that **allows**/ **denies** **traffic** **between** **pods** (or **from** **external**) based on **labels** ( **pod**, **namespace**). **Default** in **many** **clusters** = **allow** **all**; **policy** **restricts** (e.g. **only** **app** **pods** can **talk** to **DB** **pods**). **Requires** **CNI** that **supports** **NetworkPolicy** (e.g. **Calico**, **Cilium**). **Result**: **micro-segmentation**; **limit** **lateral** **movement** if **compromised**.

---

## Q2. (Beginner) What is the difference between ingress and egress in firewall/network policy?

**Answer:**  
**Ingress**: **incoming** **traffic** **to** **pod** ( **who** can **connect** **to** **me**). **Egress**: **outgoing** **traffic** **from** **pod** ( **where** **can** **I** **connect**). **Policy**: **ingress** **rules** **allow** **from** **specific** **pods**/ **namespaces**; **egress** **rules** **allow** **to** **specific** **pods** or **external** **IPs** (e.g. **API** **only**). **Default** **deny** **both** then **allow** **only** **needed** **paths**.

---

## Q3. (Beginner) What is TLS termination? Where does it typically happen in Kubernetes?

**Answer:**  
**TLS** **termination**: **decrypt** **HTTPS** at **edge** ( **load** **balancer** or **ingress**); **traffic** **inside** **cluster** can be **HTTP** ( **or** **re-encrypt** to **backend**). **K8s**: **Ingress** **controller** ( **nginx**, **traefik**) **terminates** **TLS** ( **cert** from **cert-manager** or **secret**); **backend** **service** **receives** **HTTP** unless **backend** **TLS** **configured**. **Benefit**: **certs** **managed** in **one** place; **offload** **crypto** from **app** **pods**.

---

## Q4. (Beginner) What is a service mesh? What problem does it solve?

**Answer:**  
**Service** **mesh**: **layer** that **handles** **traffic** **between** **services** ( **mTLS**, **retry**, **timeout**, **observability**) **without** **app** **code** **change**. **Problem**: **cross-cutting** **concerns** ( **auth**, **routing**, **resilience**) **repeated** in **every** **service**. **Solution**: **sidecar** **proxy** ( **Envoy**) **per** **pod**; **control** **plane** ( **Istio**, **Linkerd**) **configures** **proxies**. **Result**: **uniform** **mTLS**, **metrics**, **traffic** **split** ( **canary**).

---

## Q5. (Intermediate) Write a NetworkPolicy that allows only pods with label app=frontend to talk to pods with label app=api on port 8080.

**Answer:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```
**Result**: **only** **frontend** **pods** can **connect** to **api** **pods** on **8080**; **all** **other** **ingress** **denied** (if **default** **deny** **enabled**).

---

## Q6. (Intermediate) How do you restrict egress so pods can only reach internal services and a specific external API?

**Answer:**  
**Egress** **NetworkPolicy**: **allow** **egress** to (1) **internal** **DNS** ( **kube-dns** **namespace**); (2) **internal** **pods** ( **podSelector** or **namespaceSelector**); (3) **external** **API** **IP** or **CIDR** (e.g. **api.stripe.com** — **resolve** to **IP** or **allow** **CIDR**). **Example**: **egress** to **0.0.0.0/0** **except** **allowed** **destinations** = **hard** ( **deny** **all** then **allow** **specific** **IPs**/ **namespaces**). **Some** **CNI** **support** **DNS** **based** **egress** ( **Cilium** **FQDN**). **Result**: **no** **arbitrary** **outbound** **internet**; **only** **needed** **deps**.

---

## Q7. (Intermediate) What is mTLS (mutual TLS)? How does a service mesh use it?

**Answer:**  
**mTLS**: **both** **sides** **present** **certs** ( **client** and **server** **authenticated**). **Service** **mesh**: **sidecar** **injects** **certs**; **pod-to-pod** **traffic** **encrypted** and **authenticated**; **control** **plane** **issues** **short-lived** **certs** per **pod**. **App** **code** **unchanged**; **mesh** **terminates** **mTLS** at **sidecar**. **Result**: **zero-trust** **internal** **traffic**; **no** **plain** **text** **between** **pods**.

---

## Q8. (Intermediate) How do you manage TLS certificates in Kubernetes (e.g. cert-manager)?

**Answer:**  
**cert-manager**: **CRD** **Certificate**; **issuer** ( **Let’s** **Encrypt**, **internal** **CA**). **Certificate** **spec**: **secret** **name**, **dnsNames**; **cert-manager** **requests** **cert** and **stores** in **Secret**; **renew** **before** **expiry**. **Ingress** **references** **Secret** ( **tls.secretName**). **Result**: **automatic** **provision** and **renewal**; **no** **manual** **cert** **upload**. **For** **internal** **mTLS**: **mesh** or **cert-manager** **internal** **issuer**.

---

## Q9. (Intermediate) What is the principle of least privilege in networking? How do you apply it?

**Answer:**  
**Least** **privilege**: **grant** **only** **necessary** **access** ( **no** **default** **allow** **all**). **Apply**: **NetworkPolicy** **default** **deny** **ingress**/ **egress**; **allow** **only** **known** **paths** ( **frontend** → **api** → **db**). **RBAC** **minimal** ( **service** **account** **only** **needed** **roles**). **Pod** **security** ( **non-root**, **drop** **capabilities**). **Secrets** **per** **app** ( **not** **shared** **admin** **cred**). **Result**: **compromised** **pod** **can’t** **reach** **everything**.

---

## Q10. (Intermediate) How do you expose a Kubernetes service to the internet securely?

**Answer:**  
**Ingress** with **TLS** ( **cert-manager** + **Let’s** **Encrypt**); **single** **entry** **point**; **path**/ **host** **routing** to **services**. **Or** **LoadBalancer** **Service** ( **cloud** **LB**) with **TLS** **at** **LB** or **in** **pod**. **Secure**: **HTTPS** **only** ( **redirect** **HTTP** → **HTTPS**); **WAF** ( **optional**) in **front**; **rate** **limit**; **auth** ( **OAuth**/ **basic**) if **internal** **tool**. **Network** **policy** **allow** **ingress** **only** from **ingress** **controller** to **app** **pods**.

---

## Q11. (Advanced) Production scenario: You need to segment a cluster so team A pods cannot talk to team B pods, but both can talk to shared services. How do you design NetworkPolicies?

**Answer:**  
**Namespaces**: **team-a**, **team-b**, **shared**. **Default** **deny** **ingress** in **team-a** and **team-b** ( **NetworkPolicy** **deny** **all** **ingress** then **allow** **specific**). **Allow** **team-a** **pods** **ingress** from **team-a** ( **podSelector** **matchLabels** **team-a**) and **from** **shared** **services** ( **namespaceSelector** **shared**; **or** **allow** **shared** **to** **team-a** **egress** and **team-a** **ingress** from **shared**). **Same** for **team-b**. **Shared** **namespace**: **allow** **ingress** from **team-a** and **team-b** ( **namespaceSelector**); **egress** as **needed** (e.g. **DB**). **No** **policy** **allowing** **team-a** ↔ **team-b**; **result** = **segmentation**.

---

## Q12. (Advanced) How do you implement zero-trust networking in a Kubernetes cluster?

**Answer:**  
**Zero-trust**: **never** **trust** **by** **location**; **verify** **identity** and **authorize** **per** **request**. **In** **K8s**: (1) **NetworkPolicy** **default** **deny**; **allow** **only** **explicit** **pod**/ **namespace** **pairs**. (2) **mTLS** ( **service** **mesh**) so **every** **connection** **authenticated**. (3) **RBAC** **per** **service** **account**; **no** **overly** **broad** **roles**. (4) **Admission** **policy** ( **OPA**) **no** **privileged** **pods**; **no** **host** **network**. (5) **Secrets** **per** **app**; **no** **shared** **secrets** **store** **access** **for** **all**. **Result**: **identity** and **policy** **drive** **access**; **network** **segment** **is** **one** **layer**.

---

## Q13. (Advanced) What is the difference between Calico and Cilium? When would you choose one?

**Answer:**  
**Calico**: **CNI** + **NetworkPolicy**; **eBPF** **optional** ( **dataplane**); **routing**; **IP** **per** **pod**. **Cilium**: **eBPF**-based **CNI**; **NetworkPolicy**; **observability** ( **Hubble**); **FQDN** **egress**; **service** **mesh** **lite**. **Choose** **Calico**: **mature**; **simple** **policy**; **multi** **cloud**. **Choose** **Cilium**: **eBPF** **performance** and **observability**; **advanced** **egress** ( **DNS**); **future** **mesh** **features**. **Both** **support** **NetworkPolicy**; **Cilium** **richer** **L7** and **visibility**.

---

## Q14. (Advanced) How do you secure the supply chain (images, pipeline) from a networking and access perspective?

**Answer:**  
**Images**: **only** **from** **trusted** **registry** ( **admission** **policy**); **sign** **images** ( **cosign**); **scan** in **CI** ( **Trivy**). **Pipeline**: **Jenkins**/ **CI** **in** **restricted** **network** ( **egress** **only** to **registry**, **Git**, **Vault**); **no** **arbitrary** **outbound**. **Access**: **RBAC** on **CI** ( **who** can **approve** **prod**); **audit** **log** for **deploys**. **K8s**: **imagePullSecrets** from **secret** **store**; **no** **public** **untrusted** **registries**. **Result**: **images** **and** **pipeline** **trusted**; **lateral** **access** **limited**.

---

## Q15. (Advanced) Production scenario: A pod is compromised. How do network policies limit lateral movement and exfiltration?

**Answer:**  
**Lateral** **movement**: **NetworkPolicy** **deny** **all** **ingress**/ **egress** by **default**; **allow** **only** **needed** (e.g. **app** **pod** → **api** **pod**; **api** **pod** → **db** **pod**). **Compromised** **pod** **can’t** **reach** **other** **namespaces** or **pods** **not** in **allow** **list**. **Exfiltration**: **egress** **policy** — **allow** **only** **specific** **external** **IPs** (e.g. **API** **deps**); **deny** **arbitrary** **internet**. **DNS** **egress** **restrict** ( **Cilium** **FQDN** or **allow** **only** **internal** **DNS**). **Result**: **attacker** **stuck** in **pod**; **no** **DB** **access** or **exfil** to **random** **IP**.

---

## Q16. (Advanced) How do you implement WAF (web application firewall) in front of Kubernetes?

**Answer:**  
**Option** **1**: **Ingress** **controller** with **WAF** **module** (e.g. **ModSecurity** with **nginx**); **rules** **in** **config**. **Option** **2**: **Cloud** **WAF** ( **AWS** **WAF**, **Cloudflare**) in **front** of **LB**/ **ingress**; **traffic** **flows** **through** **WAF** before **cluster**. **Option** **3**: **Sidecar** **WAF** ( **Envoy** **filter** or **dedicated** **proxy**) per **pod**. **Rules**: **OWASP** **core**; **rate** **limit**; **block** **known** **bad** **patterns**. **Result**: **L7** **attacks** **blocked** **before** **app**.

---

## Q17. (Advanced) How do you rotate TLS certificates and private keys without downtime?

**Answer:**  
**cert-manager**: **auto** **renew** ( **before** **expiry**); **new** **cert** **written** to **Secret**; **Ingress** **references** **Secret** — **controller** **reloads** **new** **cert** ( **no** **restart** **pods** if **ingress** **controller** **reloads** **config**). **Manual** **rotation**: **create** **new** **Secret** with **new** **cert**; **update** **Ingress** **tls.secretName** to **new** **secret** ( **or** **same** **name** **replace** **content**); **ingress** **controller** **reload**; **gradual** **traffic** **to** **new** **cert**. **App** **pods** **no** **change** if **termination** at **ingress**; **zero** **downtime** if **reload** **graceful**.

---

## Q18. (Advanced) What is pod security (Pod Security Standards, securityContext)? How does it relate to network security?

**Answer:**  
**Pod** **security**: **restrict** **what** **pod** **can** **do** ( **runAsNonRoot**, **readOnlyRootFilesystem**, **drop** **capabilities**); **PSA** ( **restricted**/ **baseline**) **enforces** via **admission**. **Relation**: **network** **policy** **limits** **who** **pod** **talks** **to**; **pod** **security** **limits** **what** **pod** **can** **do** **locally** ( **reduce** **privilege** **escalation**; **if** **compromised**, **attacker** **has** **less** **power**). **Together**: **defense** **in** **depth** ( **network** + **identity** + **least** **privilege** **container**).

---

## Q19. (Advanced) How do you audit network access and security events (who talked to whom, policy changes)?

**Answer:**  
**Network** **audit**: **Cilium** **Hubble** ( **flow** **log** — **who** **talked** **to** **whom**); **export** to **SIEM** or **log** **store**. **Policy** **changes**: **NetworkPolicy** **in** **Git** ( **audit** **trail**); **K8s** **audit** **log** ( **who** **created**/ **updated** **policy**). **Security** **events**: **Falco** ( **runtime** **anomaly**); **image** **scan** **results**; **admission** **denials** ( **OPA** **log**). **Correlate** in **dashboard**; **alert** on **unusual** **flows** or **denied** **attempts**.

---

## Q20. (Advanced) Senior red flags to avoid in networking and security

**Answer:**  
- **No** **NetworkPolicy** ( **default** **allow** **all**; **lateral** **movement** **easy**).  
- **TLS** **only** at **edge** with **plain** **text** **between** **tiers** ( **use** **mTLS** or **encrypt** **sensitive** **paths**).  
- **Overly** **broad** **egress** ( **allow** **0.0.0.0/0**; **exfil** **easy**).  
- **Secrets** in **env** **or** **config** **in** **repo** ( **use** **secret** **store**).  
- **No** **cert** **rotation** ( **expired** **or** **manual** **forever**).  
- **Privileged** **pods** or **host** **network** **without** **justification**.  
- **No** **admission** **policy** ( **any** **image**/ **config** **allowed**).  
- **No** **audit** of **network** **flows** or **policy** **changes**.

---

**Tradeoffs:** Startup: basic ingress TLS, no mesh. Medium: NetworkPolicy per namespace, cert-manager. Enterprise: service mesh mTLS, zero-trust, WAF, audit and supply chain security.
