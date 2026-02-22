# 9. Networking Fundamentals (DevOps)

## Q1. (Beginner) What is the difference between TCP and UDP? When would you use each?

**Answer:**  
**TCP**: **reliable**, **ordered**, **connection**-oriented; retransmits; flow control. **UDP**: **unreliable**, **no** guarantee; **low** overhead. **Use TCP**: HTTP, DB, file transfer. **Use UDP**: **real-time** (video, voice), **DNS** (often), **metrics** (StatsD) when loss is acceptable.

---

## Q2. (Beginner) What is a port? What are well-known ports for HTTP, HTTPS, and SSH?

**Answer:**  
**Port**: **16-bit** number (0–65535); identifies **service** on a host. **Well-known**: **80** = HTTP, **443** = HTTPS, **22** = SSH, **3306** = MySQL, **5432** = PostgreSQL. **Ephemeral**: client side; OS assigns (e.g. 49152–65535).

---

## Q3. (Beginner) What is DNS resolution? What is the difference between A record and CNAME?

**Answer:**  
**DNS**: **name** → **IP** (or other data). **A**: name → **IPv4**. **CNAME**: name → **another name** (alias). **Use A** for apex (e.g. example.com); **CNAME** for subdomain (e.g. www → lb.example.com). **Lookup**: `dig example.com`, `nslookup example.com`.

---

## Q4. (Beginner) What is localhost and what is the loopback address?

**Answer:**  
**localhost**: **hostname** for **this** machine. **Loopback**: **127.0.0.1** (IPv4), **::1** (IPv6); traffic **never** leaves the host. **Use**: services binding to **127.0.0.1** are **not** reachable from other hosts (safe for dev or local-only).

---

## Q5. (Intermediate) What is a firewall? What is the difference between allow-list and deny-list?

**Answer:**  
**Firewall**: **filter** traffic by **rules** (IP, port, protocol). **Allow-list** (whitelist): **only** listed traffic allowed; **default deny**. **Deny-list** (blacklist): **block** listed; **default allow**. **Prefer** allow-list for **servers** (minimal surface). **Example**: allow **22** (SSH) from office IP only; allow **80, 443** from anywhere.

---

## Q6. (Intermediate) What is a load balancer? What is layer 4 vs layer 7?

**Answer:**  
**Load balancer**: **distributes** traffic across **backends** (health check, stickiness). **L4**: **TCP/UDP** (IP, port); **fast**; no content awareness. **L7**: **HTTP** (path, host, headers); **routing** by URL; **SSL** termination. **Use L4** for raw TCP; **L7** for HTTP/HTTPS and path-based routing.

---

## Q7. (Intermediate) What is SSL/TLS? What is the role of a certificate?

**Answer:**  
**TLS**: **encrypts** and **authenticates** (integrity) traffic. **Certificate**: **binds** identity (domain) to **public key**; **signed** by CA; client **verifies** before trusting. **HTTPS** = HTTP over TLS. **DevOps**: **terminate** TLS at LB or ingress; **cert** from Let’s Encrypt or internal CA; **rotate** before expiry.

---

## Q8. (Intermediate) How do you test connectivity to a remote host and port (e.g. is PostgreSQL reachable)?

**Answer:**  
**telnet**: `telnet host 5432` (connect or timeout). **nc** (netcat): `nc -zv host 5432`. **curl**: `curl -v telnet://host:5432` or **HTTP** only. **Bash**: `timeout 2 bash -c '</dev/tcp/host/5432'` (open = reachable). **From container**: same from inside pod or use **service** name in K8s.

---

## Q9. (Intermediate) What is a subnet and CIDR? What does 10.0.1.0/24 mean?

**Answer:**  
**Subnet**: **segment** of a network. **CIDR**: **prefix/length** (e.g. 10.0.1.0/24). **/24** = first **24** bits fixed → **256** addresses (10.0.1.0–10.0.1.255); **usable** often 10.0.1.1–10.0.1.254 (gateway and broadcast reserved). **/16** = 65k addresses; **/8** = 16M.

---

## Q10. (Intermediate) What is NAT? Why is it used in private networks?

**Answer:**  
**NAT** (Network Address Translation): **rewrite** source/dest **IP** (and port) at boundary; **private** IPs (10.x, 192.168.x) → **single** public IP. **Use**: **save** public IPs; **hide** internal topology; **outbound** internet from private subnet. **SNAT**: internal → internet; **DNAT**: port forward (external → internal).

---

## Q11. (Advanced) Production scenario: A pod in Kubernetes cannot reach an external API (e.g. https://api.example.com). How do you debug? List checks.

**Answer:**  
(1) **From pod**: `kubectl exec -it <pod> -- sh`; `curl -v https://api.example.com` (timeout? DNS? TLS?). (2) **DNS**: `nslookup api.example.com` (resolve?). (3) **Egress**: **network policy** blocking? **No** egress policy = allow; **policy** may deny. (4) **Node**: **outbound** from node (NAT, firewall). (5) **TLS**: **cert** or **proxy** (e.g. corporate proxy). (6) **Service** mesh or **sidecar** can **intercept**; check **iptables** or mesh config. **Order**: DNS → connectivity → TLS → policy.

---

## Q12. (Advanced) What is a network namespace (Linux)? How does it relate to containers?

**Answer:**  
**Network namespace**: **isolated** network stack (interfaces, routes, iptables). **Container**: usually has **own** network namespace; **veth** pair connects to **bridge** (e.g. docker0) or **CNI** (K8s). **Result**: container has **own** IP; **isolated** from host and other containers; **NAT** or bridge for external access.

---

## Q13. (Advanced) What is mTLS (mutual TLS)? When would you use it between services?

**Answer:**  
**mTLS**: **both** sides present **certificates**; **server** authenticates **client** (not just client verifying server). **Use**: **service-to-service** in **zero-trust** (e.g. mesh, API backend). **DevOps**: **issuing** client certs (or **automated** via Istio/Vault); **validation** on server; **rotate** certs. **Tradeoff**: more **complex** than one-way TLS; use when **strong** service identity is required.

---

## Q14. (Advanced) How do you implement "allow only HTTPS and block HTTP" at the edge (e.g. load balancer or ingress)?

**Answer:**  
(1) **LB/Ingress**: **listener** only for **443** (no 80); or **80** → **redirect** to **301/302** to https://. (2) **Ingress** (e.g. nginx): **server** block for 80 with `return 301 https://$host$request_uri`. (3) **WAF** or **firewall**: allow **443**; **deny** 80 or redirect. **HSTS** header so browsers upgrade to HTTPS.

---

## Q15. (Advanced) Production scenario: You have 3 tiers (web, app, DB). Only web should be public; app talks to DB. Describe firewall/security group rules.

**Answer:**  
**Web**: **inbound** 80/443 from **internet** (or LB only); **outbound** to **app** (e.g. 8080). **App**: **inbound** 8080 from **web** tier only (SG or IP range); **outbound** to **DB** (e.g. 5432). **DB**: **inbound** 5432 from **app** tier only; **no** public. **Default**: **deny** all; **allow** only above. **K8s**: **NetworkPolicy** (ingress from web to app; from app to DB); **no** ingress to DB from web.

---

## Q16. (Advanced) What is BGP? When would a DevOps engineer encounter it?

**Answer:**  
**BGP** (Border Gateway Protocol): **routing** between **autonomous systems** (AS); used on **internet** and in **data centers** (e.g. **ECMP**, **anycast**). **Encounter**: **cloud** (e.g. Direct Connect, VPN); **on-prem** **routing**; **global** load balancing (anycast). **Rare** for app-level DevOps; more for **network**/platform.

---

## Q17. (Advanced) What is a reverse proxy? How does it differ from a load balancer?

**Answer:**  
**Reverse proxy**: **receives** client request; **forwards** to **backend**; **returns** backend response; can **terminate** TLS, **cache**, **rewrite**. **Load balancer**: **distributes** to **multiple** backends. **Overlap**: many **L7** LBs are reverse proxies (nginx, HAProxy, ALB). **Proxy** = one logical function; **LB** = distribution; often **combined**.

---

## Q18. (Advanced) How do you debug "connection refused" vs "connection timed out"?

**Answer:**  
**Refused**: **nothing** listening on that **port** (service down or wrong port). **Timeout**: **path** blocked (firewall, routing, **no route**); or **filtered** (e.g. DROP). **Check**: **local** — `ss -tlnp` (listening?); **remote** — **telnet/nc** (refused = no listener; timeout = network/firewall). **Firewall**: **reject** often returns "refused"; **drop** → timeout.

---

## Q19. (Advanced) Production scenario: After a deploy, 10% of users get 502 Bad Gateway. Others are fine. What could cause this and how do you narrow it down?

**Answer:**  
**Causes**: **new** backend **crashes** or **not ready** (health check **flapping**); **sticky** session to **bad** node; **subset** of **paths** or **versions** broken. **Narrow**: (1) **Which** backends? (LB targets, pod list.) (2) **Logs** from **502** requests (LB and backend). (3) **Compare** 502 vs 200 (same backend? path?). (4) **Rollback** or **scale** old version; **fix** new (e.g. readiness, memory). **Senior**: "I’d check target health and backend logs for 502; likely a subset of new instances failing health or crashing."

---

## Q20. (Advanced) Senior red flags to avoid in networking (DevOps)

**Answer:**  
- **Opening** all ports (0.0.0.0/0) for "debugging".  
- **No** TLS or **plain** HTTP in production.  
- **Ignoring** DNS (hardcoded IPs, no TTL).  
- **No** firewall/security groups (default allow).  
- **Single** point of failure (one LB, one AZ).  
- **No** health checks on backends.  
- **Sensitive** services **public** (DB, admin).  
- **No** monitoring (latency, errors, connection count).

---

**Tradeoffs:** Startup: single region, basic SG. Medium: L7 LB, TLS, health checks. Enterprise: WAF, mTLS, network policies, multi-region.
