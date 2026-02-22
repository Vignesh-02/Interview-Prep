# 27. API Gateway, Reverse Proxy & Load Balancing

## Topic Introduction

As backend systems grow, you need infrastructure to **route**, **balance**, and **protect** traffic. API Gateways handle cross-cutting concerns (auth, rate limiting, logging). Load balancers distribute traffic across multiple servers. Reverse proxies terminate SSL and cache responses.

```
Client → CDN → Load Balancer → API Gateway → Service A
                                            → Service B
                                            → Service C
```

**Key tools**: nginx, HAProxy, Kong, AWS ALB/API Gateway, Envoy, Traefik.

**Go/Java tradeoff**: Go services often use nginx or Envoy as a sidecar. Java uses Spring Cloud Gateway. Node.js typically sits behind nginx (reverse proxy + static files) with a separate API gateway (Kong or AWS API Gateway) for microservices.

---

## Q1. (Beginner) What is a reverse proxy and how does it differ from a forward proxy?

**Answer**:

```
Forward Proxy:  Client → Proxy → Internet (hides client identity)
                (VPN, corporate proxy)

Reverse Proxy:  Internet → Proxy → Backend Servers (hides server identity)
                (nginx, Cloudflare)
```

| | Forward Proxy | Reverse Proxy |
|---|---|---|
| Who uses it | Client | Server |
| Purpose | Hide client, filter content | Load balance, SSL, cache |
| Example | Corporate VPN, Tor | nginx, HAProxy, Cloudflare |

```nginx
# nginx as reverse proxy for Node.js
upstream nodejs_app {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://nodejs_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Q2. (Beginner) What are the different load balancing algorithms?

**Answer**:

| Algorithm | Description | Best for |
|---|---|---|
| **Round Robin** | Cycle through servers sequentially | Equal-capacity servers |
| **Weighted Round Robin** | Some servers get more traffic | Mixed-capacity servers |
| **Least Connections** | Send to server with fewest active connections | Varied request durations |
| **IP Hash** | Same client always goes to same server | Session affinity |
| **Random** | Random server selection | Simple, stateless services |

```nginx
# nginx load balancing examples

# Round Robin (default)
upstream api {
    server node1:3000;
    server node2:3000;
    server node3:3000;
}

# Weighted Round Robin
upstream api {
    server node1:3000 weight=3;  # gets 3x traffic
    server node2:3000 weight=1;
    server node3:3000 weight=1;
}

# Least Connections
upstream api {
    least_conn;
    server node1:3000;
    server node2:3000;
}

# IP Hash (sticky sessions)
upstream api {
    ip_hash;
    server node1:3000;
    server node2:3000;
}
```

---

## Q3. (Beginner) Why should Node.js sit behind nginx in production?

**Answer**:

```
DON'T: Client → Node.js directly
DO:    Client → nginx → Node.js
```

| Capability | nginx | Node.js |
|---|---|---|
| SSL termination | Excellent (OpenSSL, hardware accel) | Good but slower |
| Static files | Extremely fast (zero-copy sendfile) | Slow (reads into JS memory) |
| Gzip compression | Native, fast | Blocks event loop for large responses |
| Rate limiting | Built-in, efficient | Requires middleware |
| DDoS protection | Connection limits, request filtering | Vulnerable |
| HTTP/2, HTTP/3 | Native | Limited |
| Serving multiple apps | Port-based routing | One app per port |

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    # Static files served by nginx directly (never hits Node.js)
    location /static/ {
        root /var/www;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API routes → Node.js
    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";  # keep-alive
    }

    # Gzip
    gzip on;
    gzip_types application/json text/plain text/css;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:3000;
    }
}
```

---

## Q4. (Beginner) How do health checks work with load balancers?

```js
// Application health check endpoints
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/health/ready', async (req, res) => {
  try {
    await db.query('SELECT 1');
    await redis.ping();
    res.json({ status: 'ready', db: true, redis: true });
  } catch (err) {
    res.status(503).json({ status: 'not_ready', error: err.message });
  }
});

app.get('/health/live', (req, res) => {
  // Just check if the process is alive (no dependency checks)
  res.json({ status: 'alive' });
});
```

```nginx
# nginx health checks (active)
upstream api {
    server node1:3000;
    server node2:3000;

    # Passive health checks (mark server down after 3 failures)
    server node1:3000 max_fails=3 fail_timeout=30s;
}
```

```yaml
# Kubernetes health checks
livenessProbe:
  httpGet:
    path: /health/live
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 15
  failureThreshold: 3   # restart after 3 failures

readinessProbe:
  httpGet:
    path: /health/ready
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 2   # stop sending traffic after 2 failures
```

---

## Q5. (Beginner) What is an API Gateway? How does it differ from a reverse proxy?

| | **Reverse Proxy (nginx)** | **API Gateway (Kong/AWS)** |
|---|---|---|
| Primary job | Route traffic, SSL, static files | API management |
| Authentication | Basic (htpasswd) | JWT, OAuth, API keys |
| Rate limiting | IP-based | Per-user, per-API key |
| Transforms | Limited (headers) | Request/response transformation |
| Analytics | Access logs | API analytics, usage tracking |
| Developer portal | No | Yes (documentation, key management) |
| Best for | Simple routing | Microservices, public APIs |

```js
// Kong API Gateway configuration (declarative)
const kongConfig = {
  services: [{
    name: 'user-service',
    url: 'http://user-service:3001',
    routes: [{ paths: ['/api/users'], methods: ['GET', 'POST'] }],
    plugins: [
      { name: 'jwt' },                    // JWT authentication
      { name: 'rate-limiting', config: { minute: 100 } },
      { name: 'cors' },
      { name: 'request-transformer', config: { add: { headers: ['X-Request-ID:$(uuid)'] } } },
    ],
  }],
};
```

---

## Q6. (Intermediate) How do you configure nginx for WebSocket proxying?

```nginx
# WebSocket requires Upgrade headers to be forwarded
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream websocket_servers {
    # IP hash for sticky sessions (same client → same server)
    ip_hash;
    server node1:3000;
    server node2:3000;
}

server {
    listen 443 ssl;
    server_name ws.example.com;

    location /ws {
        proxy_pass http://websocket_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Important: increase timeouts for long-lived connections
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;

        # Buffer settings
        proxy_buffering off;
    }
}
```

---

## Q7. (Intermediate) How do you implement SSL/TLS termination?

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL certificate (Let's Encrypt or commercial)
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # Modern TLS configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS (force HTTPS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # Redirect HTTP → HTTPS
    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}

server {
    listen 80;
    server_name api.example.com;
    return 301 https://$host$request_uri;
}
```

**Answer**: SSL termination at nginx means Node.js receives plain HTTP. This is faster because nginx's OpenSSL is hardware-accelerated. Node.js doesn't need to manage certificates.

---

## Q8. (Intermediate) How do you implement rate limiting at the gateway level?

```nginx
# nginx rate limiting
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=ip:10m rate=10r/s;
    limit_req_zone $http_authorization zone=user:10m rate=50r/s;
    limit_req_zone $server_name zone=global:10m rate=1000r/s;

    server {
        # Per-IP rate limit
        location /api/ {
            limit_req zone=ip burst=20 nodelay;
            limit_req_status 429;
            proxy_pass http://nodejs_app;
        }

        # Stricter limit for auth endpoints
        location /api/auth/login {
            limit_req zone=ip burst=5 nodelay;
            limit_req_status 429;
            proxy_pass http://nodejs_app;
        }
    }
}
```

```js
// Kong rate limiting plugin
const rateLimitConfig = {
  name: 'rate-limiting',
  config: {
    second: 10,
    minute: 100,
    hour: 5000,
    policy: 'redis',  // shared across Kong instances
    redis_host: 'redis',
    limit_by: 'consumer',  // per API consumer
  },
};
```

---

## Q9. (Intermediate) How do you implement request/response transformation at the gateway?

```js
// Kong or custom gateway: transform requests before they reach the service

// Express-based API gateway with transformations
const gateway = express();

// Add request ID to all requests
gateway.use((req, res, next) => {
  req.headers['x-request-id'] = req.headers['x-request-id'] || randomUUID();
  next();
});

// Route to services with path transformation
gateway.use('/api/v2/users', (req, res, next) => {
  // Transform v2 requests to v1 format for backward compatibility
  if (req.body?.fullName) {
    const [firstName, ...rest] = req.body.fullName.split(' ');
    req.body.firstName = firstName;
    req.body.lastName = rest.join(' ');
    delete req.body.fullName;
  }
  next();
}, createProxyMiddleware({ target: 'http://user-service:3001', pathRewrite: { '^/api/v2': '/api/v1' } }));

// Response transformation
gateway.use('/api/users', createProxyMiddleware({
  target: 'http://user-service:3001',
  selfHandleResponse: true,
  onProxyRes: (proxyRes, req, res) => {
    let body = '';
    proxyRes.on('data', (chunk) => { body += chunk; });
    proxyRes.on('end', () => {
      const data = JSON.parse(body);
      // Add HATEOAS links
      if (Array.isArray(data)) {
        data.forEach(user => {
          user._links = {
            self: `/api/users/${user.id}`,
            orders: `/api/users/${user.id}/orders`,
          };
        });
      }
      res.json(data);
    });
  },
}));
```

---

## Q10. (Intermediate) How do you implement blue-green and canary deployments with load balancers?

```nginx
# Blue-Green deployment
# Switch all traffic from blue (old) to green (new)

upstream blue {
    server blue-node1:3000;
    server blue-node2:3000;
}

upstream green {
    server green-node1:3000;
    server green-node2:3000;
}

# Point to active deployment
upstream active {
    server green-node1:3000;  # currently green
    server green-node2:3000;
}

# Canary deployment: route % of traffic to new version
upstream stable {
    server stable1:3000 weight=9;  # 90% traffic
    server stable2:3000 weight=9;
}

upstream canary {
    server canary1:3000 weight=1;  # 10% traffic
}

# Using split_clients for precise canary percentages
split_clients "${remote_addr}${uri}" $backend {
    10% canary;
    *   stable;
}

server {
    location / {
        proxy_pass http://$backend;
    }
}
```

---

## Q11. (Intermediate) How do you implement circuit breaking at the gateway level?

```nginx
# nginx passive health checks act as a basic circuit breaker
upstream api {
    server node1:3000 max_fails=3 fail_timeout=30s;
    server node2:3000 max_fails=3 fail_timeout=30s;
    server backup:3000 backup;  # only used when primaries are down
}
```

```yaml
# Envoy circuit breaker configuration (more sophisticated)
clusters:
  - name: user-service
    connect_timeout: 5s
    circuit_breakers:
      thresholds:
        - max_connections: 100
          max_pending_requests: 50
          max_requests: 200
          max_retries: 3
    outlier_detection:
      consecutive_5xx: 5
      interval: 10s
      base_ejection_time: 30s
      max_ejection_percent: 50
```

---

## Q12. (Intermediate) How do you handle CORS at the gateway level?

```nginx
# nginx CORS configuration
server {
    location /api/ {
        # Preflight requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://app.example.com';
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization, X-Request-ID';
            add_header 'Access-Control-Max-Age' 86400;
            add_header 'Content-Length' 0;
            return 204;
        }

        # Regular requests
        add_header 'Access-Control-Allow-Origin' 'https://app.example.com' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;

        proxy_pass http://nodejs_app;
    }
}
```

**Answer**: Handle CORS at the gateway (not in each microservice). This ensures consistent CORS policy and avoids duplicating configuration across services.

---

## Q13. (Advanced) How do you design a highly available load balancing architecture?

```
Architecture for 99.99% uptime:

                    ┌──────────┐
                    │  DNS     │  (Route53 with health checks)
                    │  (GSLB)  │
                    └─┬──────┬─┘
                      │      │
              ┌───────┴─┐  ┌┴────────┐
              │ Region 1│  │ Region 2│  (multi-region)
              │ (active)│  │(standby)│
              └───┬─────┘  └─────────┘
                  │
          ┌───────┴───────┐
          │  ALB / nginx  │  (multiple AZs)
          │  (redundant)  │
          └───┬───────┬───┘
              │       │
        ┌─────┴─┐  ┌──┴────┐
        │Node 1 │  │Node 2 │  (auto-scaling group)
        │Node 3 │  │Node 4 │
        └───────┘  └───────┘
```

```js
// Application-level: graceful handling of load balancer health checks
let isShuttingDown = false;

app.get('/health', (req, res) => {
  if (isShuttingDown) return res.status(503).json({ status: 'draining' });
  res.json({ status: 'healthy' });
});

process.on('SIGTERM', () => {
  isShuttingDown = true;
  // Wait for load balancer to stop sending traffic (health check interval)
  setTimeout(() => {
    server.close(() => process.exit(0));
  }, 10000); // wait 10 seconds
});
```

---

## Q14. (Advanced) How do you implement request routing based on headers, paths, or query parameters?

```nginx
# Path-based routing to different microservices
server {
    location /api/users    { proxy_pass http://user-service; }
    location /api/orders   { proxy_pass http://order-service; }
    location /api/products { proxy_pass http://product-service; }

    # Version-based routing via header
    location /api/ {
        if ($http_api_version = "v2") {
            proxy_pass http://api_v2;
        }
        proxy_pass http://api_v1;
    }
}

# A/B testing: route based on cookie
map $cookie_experiment $backend {
    "variant_a" http://variant_a_servers;
    "variant_b" http://variant_b_servers;
    default     http://default_servers;
}

server {
    location /api/ {
        proxy_pass $backend;
    }
}
```

---

## Q15. (Advanced) How do you implement request authentication at the gateway?

```js
// API Gateway auth middleware — validate JWT before reaching services
async function gatewayAuth(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  if (!token) return res.status(401).json({ error: 'Missing token' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Add user info as headers (services trust the gateway)
    req.headers['x-user-id'] = decoded.userId;
    req.headers['x-user-role'] = decoded.role;
    req.headers['x-user-email'] = decoded.email;

    // Remove the original auth header (services don't need to verify again)
    delete req.headers.authorization;

    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// Apply to all API routes
gateway.use('/api/', gatewayAuth);

// Services trust headers from gateway (internal network only)
app.get('/api/users/me', (req, res) => {
  const userId = req.headers['x-user-id']; // trusted — set by gateway
  // No JWT verification needed in the service
});
```

---

## Q16. (Advanced) How do you implement response caching at the gateway level?

```nginx
# nginx response caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m
                 max_size=1g inactive=60m use_temp_path=off;

server {
    location /api/products {
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;      # cache 200 responses for 5 minutes
        proxy_cache_valid 404 1m;      # cache 404 for 1 minute
        proxy_cache_key "$request_method$request_uri";
        proxy_cache_use_stale error timeout updating;  # serve stale on error

        add_header X-Cache-Status $upstream_cache_status;  # HIT/MISS/STALE

        # Don't cache authenticated requests
        proxy_cache_bypass $http_authorization;
        proxy_no_cache $http_authorization;

        proxy_pass http://product-service;
    }

    # Never cache mutations
    location /api/ {
        if ($request_method != GET) {
            proxy_cache_bypass 1;
        }
        proxy_pass http://nodejs_app;
    }
}
```

---

## Q17. (Advanced) How do you implement request logging and tracing at the gateway?

```nginx
# nginx structured JSON logging
log_format json_combined escape=json
  '{'
    '"time":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"request":"$request",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"upstream_response_time":"$upstream_response_time",'
    '"http_user_agent":"$http_user_agent",'
    '"request_id":"$request_id",'
    '"upstream":"$upstream_addr"'
  '}';

access_log /var/log/nginx/access.log json_combined;

# Generate request ID and pass to backend
server {
    location /api/ {
        # Generate unique request ID if not present
        set $req_id $http_x_request_id;
        if ($req_id = "") { set $req_id $request_id; }

        proxy_set_header X-Request-ID $req_id;
        add_header X-Request-ID $req_id always;

        proxy_pass http://nodejs_app;
    }
}
```

---

## Q18. (Advanced) How do you handle DDoS protection at the infrastructure level?

```nginx
# nginx DDoS mitigation

# Connection limits
limit_conn_zone $binary_remote_addr zone=conn_per_ip:10m;
limit_conn conn_per_ip 50;  # max 50 connections per IP

# Request rate limiting
limit_req_zone $binary_remote_addr zone=req_per_ip:10m rate=30r/s;

# Slow client protection
client_body_timeout 10s;
client_header_timeout 10s;
send_timeout 10s;

# Request size limits
client_max_body_size 10m;
client_body_buffer_size 128k;

# Block known bad patterns
location ~* \.(php|asp|aspx|jsp)$ { return 403; }
location ~ /\. { deny all; }  # block hidden files

server {
    # Block by User-Agent
    if ($http_user_agent ~* (bot|crawl|spider|scan)) {
        return 403;
    }

    location /api/ {
        limit_req zone=req_per_ip burst=50 nodelay;
        limit_conn conn_per_ip 50;
        proxy_pass http://nodejs_app;
    }
}
```

---

## Q19. (Advanced) How do you implement service mesh vs API gateway — when to use each?

**Answer**:

| | **API Gateway** | **Service Mesh** |
|---|---|---|
| Position | Edge (north-south traffic) | Internal (east-west traffic) |
| Scope | External clients → services | Service-to-service |
| Auth | Client auth (JWT, API key) | mTLS (mutual TLS) |
| Rate limiting | Per client/API key | Per service |
| Observability | Edge metrics | Internal distributed tracing |
| Examples | Kong, AWS API Gateway | Istio, Linkerd |
| Code changes | None (infrastructure) | None (sidecar proxy) |

**Use API Gateway when**: You have external clients, need API key management, public API documentation, client-specific rate limits.

**Use Service Mesh when**: You have 10+ microservices, need mTLS everywhere, complex traffic routing (canary, fault injection), centralized policy management.

**Use both when**: External traffic enters through API Gateway, internal traffic managed by Service Mesh.

---

## Q20. (Advanced) Senior red flags in API gateway and load balancing.

**Answer**:

1. **Exposing Node.js directly to the internet** — no SSL termination, no rate limiting, no DDoS protection
2. **No health checks** — load balancer sends traffic to dead servers
3. **No graceful shutdown** — in-flight requests dropped on deploy
4. **Single point of failure** — one load balancer, no redundancy
5. **No request ID propagation** — can't trace requests across gateway → services
6. **Rate limiting only at application level** — DDoS reaches your Node.js before being blocked
7. **No response caching at gateway** — every identical request hits the backend
8. **Hardcoded service URLs** — can't scale or failover
9. **No SSL/TLS** — data in transit is unencrypted
10. **Gateway as bottleneck** — all logic in the gateway, services are dumb proxies

**Senior interview answer**: "I deploy Node.js behind nginx for SSL termination, static file serving, and basic rate limiting. For microservices, I use an API Gateway (Kong or AWS) for authentication, rate limiting, and request routing. The gateway adds request IDs and user context as headers so services don't need to re-verify JWT. I implement health checks at every layer, graceful shutdown for zero-downtime deploys, and multi-AZ redundancy for the load balancer itself. For service-to-service communication, I use a service mesh (Istio) for mTLS and traffic management."
