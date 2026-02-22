# 14. Authentication & Authorization (JWT, OAuth, RBAC)

## Topic Introduction

**Authentication** (AuthN) verifies *who you are*. **Authorization** (AuthZ) verifies *what you can do*. Together they form the security backbone of every backend API.

```
Client → Login (AuthN) → Token → Request + Token → Verify Token → Check Permissions (AuthZ) → Resource
```

Common patterns: **JWT** (stateless tokens), **Sessions** (server-side state), **OAuth 2.0** (third-party login), **API Keys** (service-to-service). Authorization models: **RBAC** (role-based), **ABAC** (attribute-based), **ReBAC** (relationship-based like Zanzibar/SpiceDB).

**Go/Java tradeoff**: Java Spring Security provides declarative `@PreAuthorize("hasRole('ADMIN')")`. Go uses middleware chains. Node.js uses Passport.js or custom middleware. The concepts are identical; Java's ecosystem is the most mature for enterprise auth.

---

## Q1. (Beginner) What is JWT? How does it work for authentication?

```js
const jwt = require('jsonwebtoken');
const SECRET = process.env.JWT_SECRET;

// Create token on login
function createToken(user) {
  return jwt.sign(
    { userId: user.id, email: user.email, role: user.role }, // payload
    SECRET,
    { expiresIn: '1h', issuer: 'myapp' } // options
  );
}

// Verify token on each request
function verifyToken(token) {
  return jwt.verify(token, SECRET); // throws if invalid/expired
}

// JWT structure: header.payload.signature (base64url encoded)
// Header:  { "alg": "HS256", "typ": "JWT" }
// Payload: { "userId": 1, "role": "admin", "exp": 1709000000 }
// Signature: HMACSHA256(header + "." + payload, secret)
```

**Answer**: JWT is a self-contained token that encodes user identity. The server doesn't need to store sessions — it verifies the signature to trust the token. The payload is **not encrypted** (only base64-encoded), so never put secrets in it.

---

## Q2. (Beginner) JWT vs Sessions — when do you use each?

**Answer**:

| | **JWT (Stateless)** | **Sessions (Stateful)** |
|---|---|---|
| Storage | Client (cookie/header) | Server (Redis/DB) |
| Scalability | Easy (no shared state) | Needs shared store |
| Revocation | Hard (must wait for expiry or use blacklist) | Easy (delete from store) |
| Size | Token can be large (payload) | Cookie is small (session ID) |
| Best for | APIs, microservices, mobile | Traditional web apps, SSR |

```js
// Session-based auth with express-session + Redis
const session = require('express-session');
const RedisStore = require('connect-redis').default;

app.use(session({
  store: new RedisStore({ client: redis }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { secure: true, httpOnly: true, maxAge: 3600000 },
}));

app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);
  req.session.userId = user.id; // stored in Redis
  res.json({ success: true });
});
```

---

## Q3. (Beginner) How do you implement refresh tokens?

```js
// Login returns access token (short-lived) + refresh token (long-lived)
app.post('/auth/login', async (req, res) => {
  const user = await authenticateUser(req.body.email, req.body.password);
  const accessToken = jwt.sign({ userId: user.id }, SECRET, { expiresIn: '15m' });
  const refreshToken = crypto.randomBytes(64).toString('hex');

  // Store refresh token in DB (can be revoked)
  await db.query('INSERT INTO refresh_tokens(token_hash, user_id, expires_at) VALUES($1,$2,$3)',
    [hashToken(refreshToken), user.id, new Date(Date.now() + 7 * 86400000)]);

  res.json({ accessToken, refreshToken });
});

// Refresh endpoint — exchange refresh token for new access token
app.post('/auth/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  const stored = await db.query(
    'SELECT * FROM refresh_tokens WHERE token_hash = $1 AND expires_at > NOW()',
    [hashToken(refreshToken)]
  );
  if (!stored.rows[0]) return res.status(401).json({ error: 'Invalid refresh token' });

  // Rotate refresh token (invalidate old, issue new)
  await db.query('DELETE FROM refresh_tokens WHERE token_hash = $1', [hashToken(refreshToken)]);
  const newRefresh = crypto.randomBytes(64).toString('hex');
  await db.query('INSERT INTO refresh_tokens(token_hash, user_id, expires_at) VALUES($1,$2,$3)',
    [hashToken(newRefresh), stored.rows[0].user_id, new Date(Date.now() + 7 * 86400000)]);

  const accessToken = jwt.sign({ userId: stored.rows[0].user_id }, SECRET, { expiresIn: '15m' });
  res.json({ accessToken, refreshToken: newRefresh });
});
```

**Answer**: Access tokens expire quickly (15min). Refresh tokens last longer (7 days) and are stored server-side (revocable). On refresh, rotate the refresh token to prevent reuse.

---

## Q4. (Beginner) What is OAuth 2.0? Explain the Authorization Code flow.

```
1. User clicks "Login with Google"
2. App redirects to Google: /authorize?client_id=X&redirect_uri=Y&scope=email
3. User logs in at Google, consents
4. Google redirects back: /callback?code=AUTHORIZATION_CODE
5. App exchanges code for tokens (server-to-server)
6. App gets user info from Google with the access token
```

```js
// Step 4-6: Exchange code for token and get user info
app.get('/auth/google/callback', async (req, res) => {
  const { code } = req.query;

  // Exchange code for tokens
  const tokenRes = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code,
      client_id: process.env.GOOGLE_CLIENT_ID,
      client_secret: process.env.GOOGLE_CLIENT_SECRET,
      redirect_uri: 'https://myapp.com/auth/google/callback',
      grant_type: 'authorization_code',
    }),
  });
  const tokens = await tokenRes.json();

  // Get user info
  const userRes = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  const googleUser = await userRes.json();

  // Create or find local user
  let user = await db.query('SELECT * FROM users WHERE google_id = $1', [googleUser.id]);
  if (!user.rows[0]) {
    user = await db.query('INSERT INTO users(email, google_id, name) VALUES($1,$2,$3) RETURNING *',
      [googleUser.email, googleUser.id, googleUser.name]);
  }

  const jwt = createToken(user.rows[0]);
  res.redirect(`https://myapp.com/auth-callback?token=${jwt}`);
});
```

---

## Q5. (Beginner) What is RBAC (Role-Based Access Control)? Show a simple implementation.

```js
const ROLES = {
  admin: ['users:read', 'users:write', 'users:delete', 'posts:read', 'posts:write', 'posts:delete'],
  editor: ['posts:read', 'posts:write', 'posts:delete'],
  viewer: ['posts:read'],
};

function authorize(permission) {
  return (req, res, next) => {
    const userPerms = ROLES[req.user.role] || [];
    if (!userPerms.includes(permission)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}

app.get('/api/posts', authenticate, authorize('posts:read'), getPosts);
app.post('/api/posts', authenticate, authorize('posts:write'), createPost);
app.delete('/api/posts/:id', authenticate, authorize('posts:delete'), deletePost);
app.delete('/api/users/:id', authenticate, authorize('users:delete'), deleteUser);
```

---

## Q6. (Intermediate) How do you securely handle JWT in the browser (XSS, CSRF)?

**Answer**:

| Storage | XSS Risk | CSRF Risk | Recommendation |
|---------|----------|-----------|----------------|
| `localStorage` | HIGH (JS can read) | None | Avoid for auth tokens |
| `httpOnly` cookie | None (JS can't read) | HIGH | Use with CSRF protection |
| `httpOnly` + `SameSite=Strict` | None | Low | Best for same-origin apps |

```js
// Set JWT in httpOnly cookie (server-side)
app.post('/auth/login', async (req, res) => {
  const token = createToken(user);
  res.cookie('token', token, {
    httpOnly: true,   // JS can't access
    secure: true,     // HTTPS only
    sameSite: 'strict', // prevents CSRF
    maxAge: 3600000,  // 1 hour
    path: '/',
  });
  res.json({ success: true });
});

// Read from cookie in middleware
function authenticate(req, res, next) {
  const token = req.cookies.token;
  if (!token) return res.status(401).json({ error: 'Not authenticated' });
  try { req.user = jwt.verify(token, SECRET); next(); }
  catch { res.status(401).json({ error: 'Invalid token' }); }
}
```

---

## Q7. (Intermediate) How do you implement token revocation for JWTs?

```js
// Option 1: Short-lived tokens + refresh token rotation (preferred)
// Access token: 15 min, refresh token: 7 days (stored in DB, can be deleted)

// Option 2: Token blacklist (for immediate revocation)
app.post('/auth/logout', authenticate, async (req, res) => {
  const token = req.headers.authorization.split(' ')[1];
  const decoded = jwt.decode(token);
  const ttl = decoded.exp - Math.floor(Date.now() / 1000);
  if (ttl > 0) {
    await redis.set(`blacklist:${token}`, '1', 'EX', ttl);
  }
  res.json({ success: true });
});

// Check blacklist in auth middleware
async function authenticate(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  const blacklisted = await redis.get(`blacklist:${token}`);
  if (blacklisted) return res.status(401).json({ error: 'Token revoked' });
  // ... verify JWT
}
```

---

## Q8. (Intermediate) How do you implement multi-factor authentication (MFA)?

```js
const speakeasy = require('speakeasy');
const QRCode = require('qrcode');

// Setup MFA — generate secret and QR code
app.post('/auth/mfa/setup', authenticate, async (req, res) => {
  const secret = speakeasy.generateSecret({ name: `MyApp:${req.user.email}` });
  await db.query('UPDATE users SET mfa_secret = $1, mfa_enabled = false WHERE id = $2',
    [secret.base32, req.user.id]);
  const qrCode = await QRCode.toDataURL(secret.otpauth_url);
  res.json({ qrCode, secret: secret.base32 });
});

// Verify MFA code during login
app.post('/auth/mfa/verify', async (req, res) => {
  const user = await db.query('SELECT * FROM users WHERE id = $1', [req.body.userId]);
  const verified = speakeasy.totp.verify({
    secret: user.rows[0].mfa_secret,
    encoding: 'base32',
    token: req.body.code,
    window: 1, // allow 30s clock drift
  });
  if (!verified) return res.status(401).json({ error: 'Invalid MFA code' });
  const token = createToken(user.rows[0]);
  res.json({ token });
});
```

---

## Q9. (Intermediate) How do you implement API key authentication for service-to-service calls?

```js
// Generate API key (show once, store hash)
app.post('/api-keys', authenticate, authorize('admin'), async (req, res) => {
  const rawKey = `sk_live_${crypto.randomBytes(32).toString('hex')}`;
  const hash = crypto.createHash('sha256').update(rawKey).digest('hex');
  const prefix = rawKey.slice(0, 12); // for identification

  await db.query(
    'INSERT INTO api_keys(prefix, key_hash, user_id, name, scopes) VALUES($1,$2,$3,$4,$5)',
    [prefix, hash, req.user.id, req.body.name, req.body.scopes]
  );

  res.status(201).json({
    key: rawKey, // ONLY shown once
    prefix,
    note: 'Store this key securely. It cannot be retrieved again.',
  });
});

// Middleware
async function apiKeyAuth(req, res, next) {
  const key = req.headers['x-api-key'];
  if (!key) return next(); // fall through to JWT auth
  const hash = crypto.createHash('sha256').update(key).digest('hex');
  const apiKey = await db.query(
    'SELECT * FROM api_keys WHERE key_hash = $1 AND revoked_at IS NULL', [hash]
  );
  if (!apiKey.rows[0]) return res.status(401).json({ error: 'Invalid API key' });
  req.user = { id: apiKey.rows[0].user_id, scopes: apiKey.rows[0].scopes };
  next();
}
```

---

## Q10. (Intermediate) How do you implement password reset securely?

```js
app.post('/auth/forgot-password', async (req, res) => {
  const user = await db.query('SELECT id, email FROM users WHERE email = $1', [req.body.email]);
  // Always respond 200 (don't reveal if email exists)
  res.json({ message: 'If the email exists, a reset link has been sent' });

  if (!user.rows[0]) return;

  const token = crypto.randomBytes(32).toString('hex');
  const hash = crypto.createHash('sha256').update(token).digest('hex');
  await db.query(
    'INSERT INTO password_resets(user_id, token_hash, expires_at) VALUES($1,$2,$3)',
    [user.rows[0].id, hash, new Date(Date.now() + 3600000)] // 1 hour
  );

  await sendEmail(user.rows[0].email, {
    subject: 'Password Reset',
    body: `Reset link: https://myapp.com/reset-password?token=${token}`,
  });
});

app.post('/auth/reset-password', async (req, res) => {
  const hash = crypto.createHash('sha256').update(req.body.token).digest('hex');
  const reset = await db.query(
    'SELECT * FROM password_resets WHERE token_hash = $1 AND expires_at > NOW() AND used = false',
    [hash]
  );
  if (!reset.rows[0]) return res.status(400).json({ error: 'Invalid or expired token' });

  const passwordHash = await bcrypt.hash(req.body.newPassword, 12);
  await db.query('UPDATE users SET password_hash = $1 WHERE id = $2', [passwordHash, reset.rows[0].user_id]);
  await db.query('UPDATE password_resets SET used = true WHERE id = $1', [reset.rows[0].id]);

  // Invalidate all sessions/tokens for this user
  await redis.del(`sessions:${reset.rows[0].user_id}`);

  res.json({ message: 'Password reset successful' });
});
```

---

## Q11. (Intermediate) What is ABAC (Attribute-Based Access Control)? When is it better than RBAC?

```js
// ABAC: decisions based on user attributes, resource attributes, and environment
function checkAccess(user, resource, action) {
  const policies = [
    // Users can edit their own posts
    { effect: 'allow', condition: (u, r, a) => a === 'edit' && r.type === 'post' && r.authorId === u.id },
    // Managers can edit posts in their department
    { effect: 'allow', condition: (u, r, a) => a === 'edit' && r.type === 'post' && u.role === 'manager' && r.department === u.department },
    // Admins can do anything
    { effect: 'allow', condition: (u, r, a) => u.role === 'admin' },
    // No access outside business hours for non-admins
    { effect: 'deny', condition: (u, r, a) => {
      const hour = new Date().getHours();
      return u.role !== 'admin' && (hour < 9 || hour > 17);
    }},
  ];

  for (const policy of policies) {
    if (policy.condition(user, resource, action)) return policy.effect === 'allow';
  }
  return false; // default deny
}
```

**RBAC vs ABAC**: RBAC is simpler (roles map to permissions). ABAC handles complex rules (time-based, resource ownership, department). Use RBAC for simple apps, ABAC when you need context-dependent access control.

---

## Q12. (Intermediate) How do you implement service-to-service authentication in microservices?

```js
// Option 1: Shared JWT for internal services
function createServiceToken(serviceName) {
  return jwt.sign({ service: serviceName, type: 'service' },
    process.env.INTERNAL_JWT_SECRET, { expiresIn: '5m' });
}

// When calling another service:
const response = await fetch('http://payment-service/charge', {
  headers: { 'X-Service-Token': createServiceToken('order-service') },
  body: JSON.stringify(data),
});

// Option 2: mTLS (mutual TLS) — certificate-based
// Each service has its own certificate signed by internal CA
// No tokens needed — TLS handshake proves identity
```

---

## Q13. (Advanced) Production scenario: A JWT token is compromised. How do you invalidate it across all services?

**Answer**: JWTs are stateless — they can't be individually revoked without extra infrastructure.

```js
// Solution 1: Global token version
// Store a "token version" per user in Redis
app.post('/auth/revoke-all', authenticate, async (req, res) => {
  await redis.incr(`token_version:${req.user.id}`);
  res.json({ message: 'All tokens revoked' });
});

// In auth middleware, check version
async function authenticate(req, res, next) {
  const payload = jwt.verify(token, SECRET);
  const currentVersion = await redis.get(`token_version:${payload.userId}`) || 0;
  if (payload.tokenVersion < parseInt(currentVersion)) {
    return res.status(401).json({ error: 'Token revoked' });
  }
  next();
}

// Solution 2: Short-lived tokens (15min) + revoke refresh token
// The compromised token expires in at most 15 minutes
// Revoke the refresh token in DB to prevent renewal

// Solution 3: Centralized token blacklist (Redis)
// All services check Redis before accepting a token
```

---

## Q14. (Advanced) How do you implement fine-grained authorization like Google Docs sharing?

```js
// Relationship-based access control (ReBAC)
// Model: user:alice has editor access on document:123
// Stored as tuples: (object, relation, user)

// Check permission
async function checkPermission(userId, resourceId, permission) {
  // Direct permission
  const direct = await db.query(
    'SELECT * FROM permissions WHERE user_id = $1 AND resource_id = $2 AND permission = $3',
    [userId, resourceId, permission]
  );
  if (direct.rows.length > 0) return true;

  // Inherited through groups/teams
  const groups = await db.query('SELECT group_id FROM group_members WHERE user_id = $1', [userId]);
  for (const { group_id } of groups.rows) {
    const groupPerm = await db.query(
      'SELECT * FROM permissions WHERE group_id = $1 AND resource_id = $2 AND permission = $3',
      [group_id, resourceId, permission]
    );
    if (groupPerm.rows.length > 0) return true;
  }

  // Inherited through parent resources (folder → document)
  const parent = await db.query('SELECT parent_id FROM resources WHERE id = $1', [resourceId]);
  if (parent.rows[0]?.parent_id) {
    return checkPermission(userId, parent.rows[0].parent_id, permission);
  }

  return false;
}
```

For production scale, use dedicated authorization services like **SpiceDB** (open-source Zanzibar), **OPA**, or **Cerbos**.

---

## Q15. (Advanced) How do you implement OAuth 2.0 as a provider (not just consumer)?

```js
// Your app IS the OAuth provider (other apps authenticate via your system)
// Authorization endpoint
app.get('/oauth/authorize', authenticate, (req, res) => {
  const { client_id, redirect_uri, scope, state } = req.query;
  // Validate client_id and redirect_uri
  // Show consent screen to user
  res.render('consent', { clientName: client.name, scopes: scope.split(' '), state });
});

app.post('/oauth/authorize', authenticate, async (req, res) => {
  const code = crypto.randomBytes(32).toString('hex');
  await redis.set(`auth_code:${code}`, JSON.stringify({
    userId: req.user.id, clientId: req.body.client_id, scopes: req.body.scopes,
  }), 'EX', 600); // 10 min

  res.redirect(`${req.body.redirect_uri}?code=${code}&state=${req.body.state}`);
});

// Token endpoint
app.post('/oauth/token', async (req, res) => {
  const { code, client_id, client_secret, grant_type } = req.body;
  // Validate client credentials
  const stored = JSON.parse(await redis.get(`auth_code:${code}`));
  if (!stored || stored.clientId !== client_id) return res.status(400).json({ error: 'invalid_grant' });
  await redis.del(`auth_code:${code}`);

  const accessToken = jwt.sign({ userId: stored.userId, scopes: stored.scopes, clientId: client_id },
    SECRET, { expiresIn: '1h' });
  res.json({ access_token: accessToken, token_type: 'Bearer', expires_in: 3600 });
});
```

---

## Q16. (Advanced) How does authentication differ in Go, Java, and Node.js?

| Aspect | **Node.js** | **Go** | **Java** |
|--------|------------|--------|----------|
| JWT | `jsonwebtoken` (manual) | `golang-jwt` (manual) | Spring Security (declarative) |
| OAuth | Passport.js or manual | `golang.org/x/oauth2` | Spring OAuth2 Client |
| Sessions | express-session + Redis | gorilla/sessions | Spring Session |
| Password hashing | bcrypt (async, non-blocking) | bcrypt (blocks goroutine) | BCryptPasswordEncoder |
| Middleware | Express middleware chain | `http.Handler` wrapping | Spring Security filter chain |

**Java advantage**: Spring Security is the most comprehensive auth framework. `@PreAuthorize`, CSRF protection, OAuth2 login — all declarative.

**Node advantage**: Lightweight, flexible. You understand exactly what's happening. No magic.

---

## Q17. (Advanced) How do you implement passkeys (WebAuthn/FIDO2)?

```js
const { generateRegistrationOptions, verifyRegistrationResponse,
  generateAuthenticationOptions, verifyAuthenticationResponse } = require('@simplewebauthn/server');

// Registration
app.post('/auth/passkey/register/options', authenticate, async (req, res) => {
  const options = await generateRegistrationOptions({
    rpName: 'MyApp',
    rpID: 'myapp.com',
    userID: req.user.id,
    userName: req.user.email,
    attestationType: 'none',
  });
  req.session.challenge = options.challenge;
  res.json(options);
});

app.post('/auth/passkey/register/verify', authenticate, async (req, res) => {
  const verification = await verifyRegistrationResponse({
    response: req.body,
    expectedChallenge: req.session.challenge,
    expectedOrigin: 'https://myapp.com',
    expectedRPID: 'myapp.com',
  });
  if (verification.verified) {
    await db.query('INSERT INTO passkeys(user_id, credential_id, public_key) VALUES($1,$2,$3)',
      [req.user.id, verification.registrationInfo.credentialID, verification.registrationInfo.credentialPublicKey]);`
  }
  res.json({ verified: verification.verified });
});
```

---

## Q18. (Advanced) How do you handle auth in a microservices architecture with an API gateway?

```
Client → API Gateway (validates JWT, adds user context headers)
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
Service A  Service B  Service C
(trusts gateway headers — no JWT verification needed)
```

```js
// API Gateway middleware
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) return res.status(401).json({ error: 'Token required' });

  try {
    const user = jwt.verify(token, SECRET);
    // Forward user info as headers to internal services
    req.headers['x-user-id'] = user.userId;
    req.headers['x-user-role'] = user.role;
    req.headers['x-user-email'] = user.email;
    next();
  } catch { res.status(401).json({ error: 'Invalid token' }); }
});

// Internal service — trusts gateway headers
app.use((req, res, next) => {
  req.user = {
    id: req.headers['x-user-id'],
    role: req.headers['x-user-role'],
    email: req.headers['x-user-email'],
  };
  next();
});
```

**Security**: Internal services must ONLY accept requests from the gateway (network policy). Otherwise, anyone could set these headers.

---

## Q19. (Advanced) How do you implement rate-limited, secure login with progressive delay?

```js
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const failKey = `login-fail:${email}`;
  const attempts = parseInt(await redis.get(failKey)) || 0;

  // Progressive delay: 0s, 1s, 2s, 4s, 8s, 16s, 30s max
  if (attempts > 0) {
    const delay = Math.min(Math.pow(2, attempts - 1) * 1000, 30000);
    await new Promise(r => setTimeout(r, delay));
  }

  // Account lockout after 10 attempts
  if (attempts >= 10) {
    return res.status(429).json({
      error: 'Account locked. Please reset your password or try again in 30 minutes.',
    });
  }

  const user = await db.query('SELECT * FROM users WHERE email = $1', [email]);
  if (!user.rows[0] || !(await bcrypt.compare(password, user.rows[0].password_hash))) {
    await redis.incr(failKey);
    await redis.expire(failKey, 1800); // 30 min window
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  await redis.del(failKey); // reset on success
  const token = createToken(user.rows[0]);
  res.json({ token });
});
```

---

## Q20. (Advanced) Senior auth red flags in code reviews.

**Answer**:

1. **JWT secret in source code** — must be in environment variable
2. **No token expiration** — `{ expiresIn: undefined }` means token lasts forever
3. **Storing JWT in localStorage** — XSS can steal it
4. **Not validating JWT `alg` field** — `"alg": "none"` attack bypasses signature
5. **Password stored as MD5/SHA256** — use bcrypt or argon2
6. **No rate limiting on login** — brute force vulnerability
7. **Exposing user existence in login errors** — "user not found" vs "wrong password" is an oracle
8. **Not revoking tokens on password change** — old stolen tokens still work
9. **Using symmetric JWT (HS256) between services** — asymmetric (RS256) is better for microservices
10. **No audit logging for auth events** — can't detect account compromise

**Senior interview answer**: "I implement layered auth: short-lived JWTs in httpOnly cookies with refresh token rotation, bcrypt for passwords, MFA for sensitive accounts, RBAC for coarse access control, and audit logging for all auth events. I revoke all tokens on password change and use progressive delays to prevent brute force."
