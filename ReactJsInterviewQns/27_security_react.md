# Security in React Applications — React 18 Interview Questions

## Topic Introduction

**Security in React applications** is a critical discipline that spans the entire stack — from the JSX your components render, to how tokens are stored in the browser, to the HTTP headers your server sends. React provides some built-in protections by default: JSX expressions are automatically escaped before rendering, which neutralizes the most common form of **Cross-Site Scripting (XSS)**. However, React is a client-side UI library, not a security framework. The moment you reach for `dangerouslySetInnerHTML`, store a JWT in `localStorage`, or trust user input without server-side validation, you open attack surfaces that React alone cannot close. In production, a secure React application is the product of disciplined front-end coding practices **combined** with server-side enforcement — Content Security Policy headers, httpOnly cookies, CORS configuration, rate limiting, and continuous dependency auditing.

Modern React 18 applications face a threat landscape that includes XSS (reflected, stored, and DOM-based), Cross-Site Request Forgery (CSRF), clickjacking, open redirects, supply-chain attacks via compromised npm packages, secrets leakage in client bundles, insecure authentication flows, and broken access control. Frameworks like Next.js 13+ add Server Components and server actions, which introduce new considerations around serialization boundaries and server-side data exposure. Whether you are building a banking dashboard, an e-commerce storefront, or an internal admin tool, understanding how to **prevent, detect, and respond** to these threats is what separates a production-ready engineer from someone who merely ships features.

The code below demonstrates the most fundamental security feature React gives you for free — automatic JSX escaping — and the most common way developers accidentally bypass it:

```jsx
import DOMPurify from "dompurify";

function CommentDisplay({ comment }) {
  // SAFE — React auto-escapes this. A string like "<img src=x onerror=alert(1)>"
  // renders as visible text, NOT as an HTML element.
  const safeOutput = <p>{comment.body}</p>;

  // DANGEROUS — bypasses React's escaping. If comment.bodyHtml contains
  // unsanitized HTML, an attacker can inject scripts.
  const riskyOutput = (
    <div dangerouslySetInnerHTML={{ __html: comment.bodyHtml }} />
  );

  // SAFE — sanitize first, THEN inject.
  const sanitized = DOMPurify.sanitize(comment.bodyHtml, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "ul", "li"],
    ALLOWED_ATTR: ["href", "target"],
  });
  const safeHtmlOutput = (
    <div dangerouslySetInnerHTML={{ __html: sanitized }} />
  );

  return (
    <article>
      <h3>Plain text (auto-escaped):</h3>
      {safeOutput}

      <h3>Raw HTML (dangerous without sanitization):</h3>
      {riskyOutput}

      <h3>Sanitized HTML (safe):</h3>
      {safeHtmlOutput}
    </article>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. How does React protect against XSS by default through JSX escaping?

**Answer:**

React's JSX rendering engine automatically **escapes** all values embedded in JSX expressions (`{}`) before inserting them into the DOM. This means that if a user submits a string like `<script>alert('hacked')</script>`, React will convert the angle brackets and other special characters into their HTML entity equivalents (`&lt;script&gt;`), causing the browser to render the string as **visible text** rather than executing it as HTML or JavaScript.

Under the hood, React calls the equivalent of `document.createTextNode()` for string values, which inherently treats content as text, not markup. This is React's first line of defense against **reflected** and **stored XSS** attacks.

**What React escapes:**
- `<` becomes `&lt;`
- `>` becomes `&gt;`
- `"` becomes `&quot;`
- `'` becomes `&#x27;`
- `&` becomes `&amp;`

**Important caveats:**
1. This protection only applies to **JSX children and attribute values**. It does NOT apply to `dangerouslySetInnerHTML`, `href` attributes with `javascript:` URLs, or inline event handlers constructed from user input.
2. Rendering user input into `<a href={userInput}>` is dangerous if `userInput` is `javascript:alert(1)`.
3. Injecting user data into `style` attributes or CSS-in-JS can also be exploited.

```jsx
function UserProfile({ user }) {
  // SAFE: React escapes the name. Even if user.name is
  // '<img src=x onerror=alert("XSS")>', it renders as plain text.
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.bio}</p>

      {/* DANGEROUS: user-controlled href can execute JavaScript */}
      {/* If user.website = "javascript:alert('XSS')" this runs code */}
      <a href={user.website}>Visit website</a>
    </div>
  );
}

// Safer version — validate the URL protocol
function SafeUserProfile({ user }) {
  const safeUrl = (() => {
    try {
      const url = new URL(user.website);
      // Only allow http and https protocols
      if (["http:", "https:"].includes(url.protocol)) {
        return url.toString();
      }
      return "#";
    } catch {
      return "#";
    }
  })();

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.bio}</p>
      <a href={safeUrl} rel="noopener noreferrer" target="_blank">
        Visit website
      </a>
    </div>
  );
}
```

**Key takeaway:** React's auto-escaping handles the most common XSS vector (injecting HTML via text content), but you must still validate URLs, avoid `dangerouslySetInnerHTML`, and never construct code strings from user input.

---

### Q2. What is `dangerouslySetInnerHTML`, why is it risky, and how do you use it safely?

**Answer:**

`dangerouslySetInnerHTML` is React's replacement for the native DOM `innerHTML` property. It accepts an object with a single key `__html` whose value is a raw HTML string. React intentionally made the API awkward (the long name, the `{__html: ...}` wrapper) to discourage casual use — it's a signal that you are **bypassing React's XSS protection**.

**Why it's dangerous:**
When you use `dangerouslySetInnerHTML`, React inserts the raw HTML string directly into the DOM without any escaping. If that string contains a `<script>` tag, an `onerror` handler, or any other executable markup, the browser will execute it. This is the primary vector for **stored XSS** in React applications — an attacker submits malicious HTML to your API, the server stores it, and your React component renders it unsanitized.

**When you might need it:**
- Rendering rich text from a CMS or WYSIWYG editor (e.g., TinyMCE, CKEditor)
- Displaying server-rendered markdown converted to HTML
- Embedding third-party widget HTML

**How to use it safely — DOMPurify:**

```jsx
import DOMPurify from "dompurify";

// Centralized sanitizer utility
const sanitizeConfig = {
  ALLOWED_TAGS: [
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "span", "div", "br", "hr",
    "ul", "ol", "li",
    "a", "strong", "em", "b", "i", "u",
    "blockquote", "pre", "code",
    "table", "thead", "tbody", "tr", "th", "td",
    "img",
  ],
  ALLOWED_ATTR: ["href", "target", "rel", "src", "alt", "class"],
  ALLOW_DATA_ATTR: false,
  ADD_ATTR: ["target"],        // Force target on <a>
  FORBID_TAGS: ["style", "script", "iframe", "form", "input"],
  FORBID_ATTR: ["onerror", "onclick", "onload", "onmouseover"],
};

export function sanitizeHTML(dirty) {
  return DOMPurify.sanitize(dirty, sanitizeConfig);
}

// React component
function BlogPost({ post }) {
  // NEVER do this without sanitization:
  // <div dangerouslySetInnerHTML={{ __html: post.htmlContent }} />

  // SAFE: sanitize before rendering
  const cleanHTML = sanitizeHTML(post.htmlContent);

  return (
    <article>
      <h1>{post.title}</h1>
      <div
        className="prose"
        dangerouslySetInnerHTML={{ __html: cleanHTML }}
      />
    </article>
  );
}

// BONUS: Custom hook for sanitized HTML
function useSanitizedHTML(dirty) {
  return React.useMemo(() => {
    if (!dirty) return { __html: "" };
    return { __html: sanitizeHTML(dirty) };
  }, [dirty]);
}

function SafeRichText({ html }) {
  const sanitized = useSanitizedHTML(html);
  return <div dangerouslySetInnerHTML={sanitized} />;
}
```

**Production tip:** Always sanitize on the **server** as well. Client-side sanitization with DOMPurify is a defense-in-depth layer, but the server should never store unsanitized HTML in the first place. Use a library like `sanitize-html` (Node.js) or bleach (Python) on the backend.

---

### Q3. What is CSRF, and how do you protect React forms against it?

**Answer:**

**Cross-Site Request Forgery (CSRF)** is an attack where a malicious website tricks a user's browser into making an authenticated request to your application. Because browsers automatically attach cookies (including session cookies) to requests matching the domain, the attacker can perform state-changing operations (transferring funds, changing emails, deleting data) without the user's knowledge.

**Why React apps are vulnerable:**
If your React app authenticates via cookies (session cookies or httpOnly JWT cookies) and makes state-changing requests (`POST`, `PUT`, `DELETE`) to your API, those requests carry the cookie automatically. An attacker's page can submit a hidden form to your API endpoint, and the browser will include the cookie.

**Protection strategies:**

1. **Synchronizer Token Pattern** — the server generates a unique CSRF token per session, embeds it in the page (or sends it via a cookie), and the React app includes it in every mutating request.
2. **SameSite cookies** — setting `SameSite=Strict` or `SameSite=Lax` on cookies prevents them from being sent on cross-origin requests.
3. **Custom request headers** — since browsers don't allow cross-origin `fetch` or `XMLHttpRequest` to set custom headers without CORS preflight, including a custom header like `X-CSRF-Token` ensures the request originates from your app.

```jsx
// csrf.js — Utility to read the CSRF token from a meta tag or cookie
export function getCsrfToken() {
  // Option 1: Read from a <meta> tag rendered by the server
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute("content");

  // Option 2: Read from a non-httpOnly cookie set by the server
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

// apiClient.js — Axios instance with CSRF token in headers
import axios from "axios";
import { getCsrfToken } from "./csrf";

const apiClient = axios.create({
  baseURL: "/api",
  withCredentials: true, // send cookies with every request
});

// Attach CSRF token to every mutating request
apiClient.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    config.headers["X-CSRF-Token"] = getCsrfToken();
  }
  return config;
});

export default apiClient;

// TransferForm.jsx — React component using the CSRF-protected client
import { useState } from "react";
import apiClient from "./apiClient";

function TransferForm() {
  const [amount, setAmount] = useState("");
  const [recipient, setRecipient] = useState("");
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // The CSRF token is automatically attached by the interceptor
      await apiClient.post("/transfers", {
        amount: parseFloat(amount),
        recipientId: recipient,
      });
      setStatus("Transfer successful!");
    } catch (err) {
      setStatus(err.response?.data?.message || "Transfer failed");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Recipient ID:
        <input value={recipient} onChange={(e) => setRecipient(e.target.value)} />
      </label>
      <label>
        Amount:
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </label>
      <button type="submit">Send Money</button>
      {status && <p>{status}</p>}
    </form>
  );
}
```

**Server-side (Express example):**

```jsx
// server.js
const csrf = require("csurf");
const cookieParser = require("cookie-parser");

app.use(cookieParser());
app.use(csrf({ cookie: { httpOnly: false, sameSite: "Strict", secure: true } }));

// Endpoint to provide the CSRF token to the SPA
app.get("/api/csrf-token", (req, res) => {
  res.json({ csrfToken: req.csrfToken() });
});

// All POST/PUT/DELETE routes are now protected —
// the middleware rejects requests missing or mismatching the token.
```

---

### Q4. What is Content Security Policy (CSP), and how do you configure it for a React SPA?

**Answer:**

**Content Security Policy (CSP)** is a browser security mechanism delivered via an HTTP response header (`Content-Security-Policy`) or a `<meta>` tag. It tells the browser which sources of content (scripts, styles, images, fonts, frames, etc.) are allowed to load and execute. If a source is not whitelisted, the browser blocks it — effectively preventing most XSS attacks even if an attacker manages to inject a `<script>` tag into the page.

**Why CSP is critical for React apps:**
React SPAs typically load a few JavaScript bundles, some CSS, images, and maybe fonts — all from known origins. A strict CSP policy locks the browser to **only** those known origins, blocking any injected scripts from unknown domains or inline `<script>` tags.

**Key directives for React SPAs:**
- `default-src 'self'` — fallback; only allow content from same origin
- `script-src 'self'` — only allow scripts from your domain (no inline scripts!)
- `style-src 'self' 'unsafe-inline'` — many CSS-in-JS libraries require inline styles
- `img-src 'self' data: https://cdn.example.com` — allow images from self, data URIs, and your CDN
- `connect-src 'self' https://api.example.com` — allow API calls
- `font-src 'self' https://fonts.gstatic.com`
- `frame-ancestors 'none'` — prevent clickjacking (replaces X-Frame-Options)

**Challenge with React:**
Build tools like Create React App and Vite inject inline `<script>` tags for chunk loading. To work with a strict CSP that disallows `'unsafe-inline'`, you need **nonces** or **hashes**.

```jsx
// next.config.js — CSP with nonce in Next.js (middleware approach)
// middleware.ts
import { NextResponse } from "next/server";
import crypto from "crypto";

export function middleware(request) {
  const nonce = crypto.randomBytes(16).toString("base64");
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}'`,
    `style-src 'self' 'nonce-${nonce}' 'unsafe-inline'`,
    `img-src 'self' data: https://cdn.example.com`,
    `font-src 'self' https://fonts.gstatic.com`,
    `connect-src 'self' https://api.example.com`,
    `frame-ancestors 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `upgrade-insecure-requests`,
  ].join("; ");

  const response = NextResponse.next();
  response.headers.set("Content-Security-Policy", csp);
  // Pass the nonce to the page via a custom header
  response.headers.set("X-Nonce", nonce);
  return response;
}

// _document.tsx — apply nonce to scripts
import { Html, Head, Main, NextScript } from "next/document";

export default function Document({ nonce }) {
  return (
    <Html>
      <Head nonce={nonce} />
      <body>
        <Main />
        <NextScript nonce={nonce} />
      </body>
    </Html>
  );
}
```

**For Vite / CRA (Express server):**

```jsx
// server.js — Express middleware to add CSP header
const crypto = require("crypto");

app.use((req, res, next) => {
  const nonce = crypto.randomBytes(16).toString("base64");
  res.locals.nonce = nonce;

  res.setHeader(
    "Content-Security-Policy",
    [
      `default-src 'self'`,
      `script-src 'self' 'nonce-${nonce}'`,
      `style-src 'self' 'unsafe-inline'`,
      `img-src 'self' data:`,
      `connect-src 'self' https://api.example.com`,
      `frame-ancestors 'none'`,
    ].join("; ")
  );
  next();
});

// Inject nonce into the HTML template served to the browser
app.get("*", (req, res) => {
  const html = fs
    .readFileSync(path.join(__dirname, "dist/index.html"), "utf-8")
    .replace(/<script/g, `<script nonce="${res.locals.nonce}"`);
  res.send(html);
});
```

**Production tip:** Start in **report-only mode** (`Content-Security-Policy-Report-Only`) with a reporting endpoint to collect violations without breaking the app, then progressively tighten the policy.

---

### Q5. Why is sanitizing user input important, and how do you do it in a React application?

**Answer:**

**Input sanitization** is the process of cleaning, validating, and transforming user-supplied data so that it cannot be used to exploit your application. Even though React auto-escapes JSX output, sanitization is still essential because:

1. User input flows to places **beyond JSX rendering** — database queries, URL parameters, API bodies, email templates, PDF generation, log files.
2. You may render user HTML via `dangerouslySetInnerHTML`.
3. URLs from users can contain `javascript:` protocols.
4. CSS injection through user-controlled style values is possible.

**Principles:**
- **Validate** — reject invalid input (wrong type, too long, unexpected characters).
- **Sanitize** — strip or encode dangerous characters from input you accept.
- **Escape** — encode output for the specific context (HTML, URL, CSS, JS).
- **Never trust the client** — always re-validate and sanitize on the server.

```jsx
import { useState, useCallback } from "react";
import DOMPurify from "dompurify";

// ---- Utility: input validators ----
const validators = {
  // Allow only alphanumeric, spaces, hyphens, apostrophes (for names)
  name: (value) => /^[a-zA-Z\s'-]{1,100}$/.test(value),

  // Standard email regex (simplified)
  email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),

  // Only allow safe URLs
  url: (value) => {
    try {
      const parsed = new URL(value);
      return ["http:", "https:"].includes(parsed.protocol);
    } catch {
      return false;
    }
  },

  // Sanitize free-text (strip HTML tags for plain-text fields)
  plainText: (value) => DOMPurify.sanitize(value, { ALLOWED_TAGS: [] }),
};

// ---- Hook: useSecureInput ----
function useSecureInput(validatorFn, sanitizerFn = (v) => v.trim()) {
  const [value, setValue] = useState("");
  const [error, setError] = useState("");

  const onChange = useCallback(
    (e) => {
      const raw = e.target.value;
      const sanitized = sanitizerFn(raw);
      setValue(sanitized);

      if (sanitized && !validatorFn(sanitized)) {
        setError("Invalid input");
      } else {
        setError("");
      }
    },
    [validatorFn, sanitizerFn]
  );

  return { value, error, onChange, isValid: !error && value.length > 0 };
}

// ---- Component: Secure Contact Form ----
function ContactForm() {
  const name = useSecureInput(validators.name);
  const email = useSecureInput(validators.email);
  const message = useSecureInput(
    () => true,
    (v) => validators.plainText(v) // Strip all HTML tags
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.isValid || !email.isValid) return;

    // Even though we sanitized on the client, the server MUST re-validate
    await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name.value,
        email: email.value,
        message: message.value,
      }),
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Name:</label>
        <input value={name.value} onChange={name.onChange} maxLength={100} />
        {name.error && <span className="error">{name.error}</span>}
      </div>
      <div>
        <label>Email:</label>
        <input
          type="email"
          value={email.value}
          onChange={email.onChange}
        />
        {email.error && <span className="error">{email.error}</span>}
      </div>
      <div>
        <label>Message:</label>
        <textarea value={message.value} onChange={message.onChange} maxLength={2000} />
      </div>
      <button type="submit">Send</button>
    </form>
  );
}
```

**Key takeaway:** Client-side sanitization improves UX (immediate feedback) and adds a defense-in-depth layer, but it is **never a substitute** for server-side validation. An attacker can bypass your React form entirely and POST directly to your API.

---

## Intermediate Level (Q6–Q12)

---

### Q6. What are the secure patterns for storing JWTs and managing authentication in React?

**Answer:**

JWT storage is one of the most debated topics in front-end security. The two primary storage options — `localStorage` and cookies — each have trade-offs:

| Storage Method | XSS Vulnerable? | CSRF Vulnerable? | Accessible to JS? |
|---|---|---|---|
| `localStorage` | Yes — any XSS can steal the token | No | Yes |
| `httpOnly` cookie | No — JS cannot read it | Yes (without SameSite) | No |

**Recommended approach for production:** Store the JWT (or session token) in an **httpOnly, Secure, SameSite=Strict** cookie. This makes it invisible to JavaScript (immune to XSS theft) and resistant to CSRF (when `SameSite` is set). For APIs on a different domain, use `SameSite=None; Secure` with an anti-CSRF token.

**Pattern: Short-lived access token + long-lived refresh token**

```jsx
// AuthProvider.jsx — Secure auth context using httpOnly cookies
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import axios from "axios";

const AuthContext = createContext(null);

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true, // CRITICAL: sends httpOnly cookies
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount, check if the user has a valid session
  // The server reads the httpOnly cookie and returns user data
  useEffect(() => {
    api
      .get("/auth/me")
      .then((res) => setUser(res.data.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    // Server sets httpOnly cookie on successful login
    const res = await api.post("/auth/login", { email, password });
    setUser(res.data.user);
    return res.data.user;
  }, []);

  const logout = useCallback(async () => {
    // Server clears the httpOnly cookie
    await api.post("/auth/logout");
    setUser(null);
  }, []);

  // Silent token refresh — the refresh token is also in an httpOnly cookie
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            // The server reads the refresh token cookie and issues a new access token cookie
            await api.post("/auth/refresh");
            return api(originalRequest);
          } catch {
            setUser(null);
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
    return () => api.interceptors.response.eject(interceptor);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

**Server-side (Express):**

```jsx
// auth.controller.js
const jwt = require("jsonwebtoken");

function loginHandler(req, res) {
  const user = authenticateUser(req.body.email, req.body.password);

  const accessToken = jwt.sign({ sub: user.id, role: user.role }, ACCESS_SECRET, {
    expiresIn: "15m",
  });
  const refreshToken = jwt.sign({ sub: user.id }, REFRESH_SECRET, {
    expiresIn: "7d",
  });

  // Store tokens in httpOnly cookies — JavaScript cannot access them
  res.cookie("access_token", accessToken, {
    httpOnly: true,
    secure: true,          // only sent over HTTPS
    sameSite: "Strict",    // blocks CSRF
    maxAge: 15 * 60 * 1000,
    path: "/",
  });
  res.cookie("refresh_token", refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: "Strict",
    maxAge: 7 * 24 * 60 * 60 * 1000,
    path: "/auth/refresh",  // only sent to the refresh endpoint
  });

  res.json({ user: { id: user.id, name: user.name, role: user.role } });
}
```

**Why NOT `localStorage`:**
If your React app has even a single XSS vulnerability (a compromised npm package, an unsanitized `dangerouslySetInnerHTML`), an attacker can run `localStorage.getItem('token')` and exfiltrate the JWT to their server. With httpOnly cookies, this is impossible.

---

### Q7. How do you implement role-based authorization and route guards in React?

**Answer:**

**Authorization** determines what an authenticated user is allowed to **see** and **do**. In React, this manifests as:

1. **Route guards** — preventing unauthorized users from accessing certain pages.
2. **Conditional rendering** — showing/hiding UI elements based on roles or permissions.
3. **API-level enforcement** — the server is the ultimate authority; client-side guards are a UX convenience, not a security boundary.

**Production pattern: Permission-based system with route guards**

```jsx
// permissions.js — Define permissions, not just roles
export const PERMISSIONS = {
  VIEW_DASHBOARD: "view:dashboard",
  MANAGE_USERS: "manage:users",
  EDIT_CONTENT: "edit:content",
  VIEW_ANALYTICS: "view:analytics",
  MANAGE_BILLING: "manage:billing",
  ADMIN_SETTINGS: "admin:settings",
};

// Map roles to permissions
export const ROLE_PERMISSIONS = {
  admin: Object.values(PERMISSIONS), // all permissions
  editor: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.EDIT_CONTENT,
    PERMISSIONS.VIEW_ANALYTICS,
  ],
  viewer: [
    PERMISSIONS.VIEW_DASHBOARD,
    PERMISSIONS.VIEW_ANALYTICS,
  ],
};

// Hook to check permissions
export function usePermissions() {
  const { user } = useAuth();
  const userPermissions = ROLE_PERMISSIONS[user?.role] || [];

  return {
    hasPermission: (permission) => userPermissions.includes(permission),
    hasAnyPermission: (perms) => perms.some((p) => userPermissions.includes(p)),
    hasAllPermissions: (perms) => perms.every((p) => userPermissions.includes(p)),
  };
}
```

```jsx
// ProtectedRoute.jsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { usePermissions } from "./permissions";

function ProtectedRoute({ requiredPermission, fallbackPath = "/unauthorized" }) {
  const { user, loading } = useAuth();
  const { hasPermission } = usePermissions();

  if (loading) {
    return <div className="spinner">Loading...</div>;
  }

  // Not logged in — redirect to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Logged in but lacks permission — redirect to unauthorized page
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to={fallbackPath} replace />;
  }

  return <Outlet />;
}

// App.jsx — Route configuration
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PERMISSIONS } from "./permissions";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />

        {/* Authenticated routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>

        {/* Admin-only routes */}
        <Route
          element={
            <ProtectedRoute requiredPermission={PERMISSIONS.MANAGE_USERS} />
          }
        >
          <Route path="/admin/users" element={<UserManagement />} />
        </Route>

        {/* Editor routes */}
        <Route
          element={
            <ProtectedRoute requiredPermission={PERMISSIONS.EDIT_CONTENT} />
          }
        >
          <Route path="/content/edit/:id" element={<ContentEditor />} />
        </Route>

        <Route path="/unauthorized" element={<UnauthorizedPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

```jsx
// PermissionGate.jsx — Conditional rendering based on permissions
function PermissionGate({ permission, children, fallback = null }) {
  const { hasPermission } = usePermissions();

  if (!hasPermission(permission)) {
    return fallback;
  }
  return children;
}

// Usage in a component
function AdminDashboard() {
  return (
    <div>
      <h1>Dashboard</h1>

      {/* Everyone with dashboard access sees this */}
      <AnalyticsWidget />

      {/* Only users with MANAGE_USERS permission see this */}
      <PermissionGate permission={PERMISSIONS.MANAGE_USERS}>
        <UserManagementPanel />
      </PermissionGate>

      {/* Only billing managers see this, others see a CTA */}
      <PermissionGate
        permission={PERMISSIONS.MANAGE_BILLING}
        fallback={<p>Contact your admin to access billing.</p>}
      >
        <BillingPanel />
      </PermissionGate>
    </div>
  );
}
```

**Critical reminder:** All of this is **client-side UI logic**. An attacker can modify JavaScript in the browser, bypass route guards, and call your API directly. Every API endpoint must independently verify the user's role and permissions using the server-side session/token.

---

### Q8. How do you securely communicate with APIs from a React application (HTTPS, CORS)?

**Answer:**

Secure API communication involves two main concerns: **transport security** (HTTPS) and **origin control** (CORS).

**HTTPS:**
- All API requests from a production React app must go over HTTPS. Mixed content (loading HTTP resources from an HTTPS page) is blocked by modern browsers.
- Set the `Strict-Transport-Security` (HSTS) header on your server to force HTTPS.
- Use `upgrade-insecure-requests` in your CSP to automatically upgrade HTTP requests.

**CORS (Cross-Origin Resource Sharing):**
- When your React app (`https://app.example.com`) calls an API on a different origin (`https://api.example.com`), the browser enforces CORS.
- The server must respond with appropriate `Access-Control-Allow-*` headers.
- **Never** set `Access-Control-Allow-Origin: *` if you use cookies (`withCredentials: true`) — the browser will reject it. You must specify the exact origin.

```jsx
// secureApiClient.js — Production-grade API client
import axios from "axios";

const secureApi = axios.create({
  baseURL: process.env.REACT_APP_API_URL, // Must be https:// in production
  withCredentials: true,                   // Send httpOnly cookies
  timeout: 30000,                          // 30-second timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — add security headers
secureApi.interceptors.request.use((config) => {
  // Ensure we never accidentally call HTTP in production
  if (
    process.env.NODE_ENV === "production" &&
    config.baseURL &&
    !config.baseURL.startsWith("https://")
  ) {
    throw new Error("API calls must use HTTPS in production");
  }

  // Attach CSRF token for mutating requests
  const method = config.method?.toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }
  }

  return config;
});

// Response interceptor — centralized error handling
secureApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Token expired — attempt refresh or redirect to login
          window.dispatchEvent(new CustomEvent("auth:unauthorized"));
          break;
        case 403:
          window.dispatchEvent(new CustomEvent("auth:forbidden"));
          break;
        case 429:
          // Rate limited — back off
          console.warn("Rate limited. Retrying after delay...");
          break;
        default:
          break;
      }
    }
    return Promise.reject(error);
  }
);

export default secureApi;
```

**Server-side CORS configuration (Express):**

```jsx
const cors = require("cors");

// WRONG — overly permissive
// app.use(cors({ origin: "*" }));

// CORRECT — allowlist specific origins
const ALLOWED_ORIGINS = [
  "https://app.example.com",
  "https://staging.example.com",
];

app.use(
  cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (mobile apps, server-to-server)
      if (!origin || ALLOWED_ORIGINS.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error("CORS not allowed for this origin"));
      }
    },
    credentials: true,               // allow cookies
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    allowedHeaders: ["Content-Type", "X-CSRF-Token", "Authorization"],
    maxAge: 86400,                    // cache preflight for 24 hours
  })
);

// Security headers
app.use((req, res, next) => {
  res.setHeader("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  next();
});
```

**Production checklist:**
1. Force HTTPS everywhere — redirect HTTP to HTTPS at the load balancer.
2. Set HSTS with a long `max-age` and `includeSubDomains`.
3. Configure CORS with an explicit origin allowlist, never `*` with credentials.
4. Use `withCredentials: true` on the client when cookies carry auth tokens.
5. Set appropriate timeouts and handle network errors gracefully.

---

### Q9. Why should you never include secrets in client-side React code, and what are the alternatives?

**Answer:**

**Any code shipped to the browser is visible to every user.** React builds are just JavaScript bundles served as static files — anyone can open DevTools, inspect network requests, or read the source maps. Environment variables prefixed with `REACT_APP_` (CRA) or `VITE_` (Vite) are **inlined at build time** into the JavaScript bundle. They are NOT secret.

**What counts as a secret:**
- API keys with write access or billing implications (Stripe secret key, AWS credentials)
- Database connection strings
- JWT signing secrets
- Third-party service tokens (SendGrid, Twilio)
- Encryption keys

**What is OK to include client-side:**
- Public API keys that are scoped to read-only and rate-limited (e.g., Google Maps JavaScript API key, Stripe publishable key)
- Feature flag identifiers
- Public endpoint URLs

```jsx
// ❌ WRONG — SECRET KEY EXPOSED IN CLIENT BUNDLE
// .env
// REACT_APP_STRIPE_SECRET_KEY=sk_live_abc123   <-- NEVER DO THIS
// REACT_APP_DATABASE_URL=postgres://user:pass@host/db  <-- NEVER

// ✅ CORRECT — only public keys in client .env
// .env
// REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_live_xyz789
// REACT_APP_API_URL=https://api.example.com

// ✅ CORRECT — proxy secret operations through your server
// PaymentForm.jsx
import { useState } from "react";
import secureApi from "./secureApiClient";

function PaymentForm({ amount }) {
  const [processing, setProcessing] = useState(false);

  const handlePayment = async (paymentMethodId) => {
    setProcessing(true);
    try {
      // The React client sends ONLY the payment method ID and amount.
      // The SECRET Stripe key is used on the SERVER — never exposed to the client.
      const { data } = await secureApi.post("/payments/create-intent", {
        paymentMethodId,
        amount,
      });
      // Handle success
      console.log("Payment succeeded:", data.paymentIntentId);
    } catch (error) {
      console.error("Payment failed:", error.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div>
      {/* Stripe Elements uses the PUBLISHABLE key — safe for client */}
      <CardElement />
      <button onClick={() => handlePayment(/* ... */)} disabled={processing}>
        {processing ? "Processing..." : `Pay $${amount}`}
      </button>
    </div>
  );
}
```

**Server-side proxy (Express):**

```jsx
// payments.controller.js
const stripe = require("stripe")(process.env.STRIPE_SECRET_KEY); // Server-only env var

app.post("/payments/create-intent", authenticate, async (req, res) => {
  const { paymentMethodId, amount } = req.body;

  const paymentIntent = await stripe.paymentIntents.create({
    amount: Math.round(amount * 100),
    currency: "usd",
    payment_method: paymentMethodId,
    confirm: true,
  });

  res.json({ paymentIntentId: paymentIntent.id, status: paymentIntent.status });
});
```

**Preventing accidental leaks:**

```jsx
// .gitignore — always include these
.env
.env.local
.env.*.local

// CI/CD — inject secrets as environment variables at runtime, never commit them.
// Use a secrets manager: AWS Secrets Manager, HashiCorp Vault, Doppler, etc.

// Build-time check: custom webpack/vite plugin to fail if secrets leak
// vite.config.js
export default defineConfig({
  define: {
    // Explicitly define ONLY public env vars
    "import.meta.env.VITE_API_URL": JSON.stringify(process.env.VITE_API_URL),
  },
});
```

**Rule of thumb:** If losing a credential would cost you money, data, or reputation, it belongs on the server, never in a React bundle.

---

### Q10. How do you manage third-party dependency security in a React project?

**Answer:**

The **npm ecosystem** is the single largest attack surface for most React applications. Supply-chain attacks — where a malicious actor publishes a compromised package version — have caused major incidents (event-stream, ua-parser-js, colors.js). Managing dependency security is an ongoing operational discipline, not a one-time task.

**Multi-layered defense strategy:**

1. **Audit regularly** — `npm audit` / `yarn audit`
2. **Lock dependencies** — always commit `package-lock.json` or `yarn.lock`
3. **Use automated scanning** — Snyk, Dependabot, Socket.dev, Renovate
4. **Pin exact versions** — avoid `^` and `~` for critical dependencies
5. **Review before updating** — read changelogs and diffs
6. **Minimize dependencies** — every package is an attack surface

```jsx
// package.json — Security-conscious dependency management
{
  "name": "secure-react-app",
  "scripts": {
    "preinstall": "npx only-allow npm",
    "audit": "npm audit --production",
    "audit:fix": "npm audit fix",
    "audit:ci": "npm audit --audit-level=high --production",
    "check:deps": "npx depcheck",
    "check:licenses": "npx license-checker --onlyAllow 'MIT;ISC;BSD-2-Clause;BSD-3-Clause;Apache-2.0'",
    "security:full": "npm run audit && npm run check:deps && npm run check:licenses"
  },
  "overrides": {
    // Force a patched version of a transitive dependency
    "nth-check": ">=2.0.1",
    "postcss": ">=8.4.31"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

**CI pipeline integration:**

```jsx
// .github/workflows/security.yml
// name: Security Audit
// on: [push, pull_request, schedule]
// schedule: cron '0 6 * * 1' — run weekly on Monday

// Steps to automate in your CI:

// 1. npm audit in CI — fail the build on high/critical vulnerabilities
// npm audit --audit-level=high --production

// 2. Snyk integration (more comprehensive than npm audit)
// npx snyk test --severity-threshold=high

// 3. Socket.dev — detects supply-chain attacks (typosquatting, install scripts)
// Integrates as a GitHub App on PRs

// 4. Lock file lint — ensure lock file is committed and consistent
// npx lockfile-lint --type npm --allowed-registries https://registry.npmjs.org --allowed-schemes https:

// React component: Security dashboard (internal tool)
function DependencySecurityDashboard({ auditResults }) {
  const criticalCount = auditResults.filter((v) => v.severity === "critical").length;
  const highCount = auditResults.filter((v) => v.severity === "high").length;

  return (
    <div className="security-dashboard">
      <h2>Dependency Security Report</h2>
      <div className="severity-summary">
        <div className={`badge ${criticalCount > 0 ? "critical" : "safe"}`}>
          Critical: {criticalCount}
        </div>
        <div className={`badge ${highCount > 0 ? "high" : "safe"}`}>
          High: {highCount}
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Package</th>
            <th>Severity</th>
            <th>Vulnerability</th>
            <th>Fix Available</th>
          </tr>
        </thead>
        <tbody>
          {auditResults.map((vuln) => (
            <tr key={vuln.id}>
              <td>{vuln.package}</td>
              <td className={vuln.severity}>{vuln.severity}</td>
              <td>{vuln.title}</td>
              <td>{vuln.fixAvailable ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**Production best practices:**
- Run `npm audit --production` (skip devDependencies which don't ship to users).
- Use `npm ci` in CI instead of `npm install` to respect the lock file exactly.
- Enable Dependabot or Renovate for automated PR-based updates.
- Review the `postinstall` scripts of new dependencies — malicious packages often hide attacks there.
- Prefer well-maintained packages with large communities and active security response.

---

### Q11. What is clickjacking, and how do you prevent it in React applications?

**Answer:**

**Clickjacking** (also called UI redress attack) is a technique where an attacker loads your application inside a transparent `<iframe>` on their malicious page and tricks users into clicking on buttons they can't see. For example, an attacker could overlay a "Win a Prize!" button on top of a transparent iframe showing your app's "Delete Account" button — the user thinks they're clicking the prize button but actually clicks delete.

**Prevention strategies:**

1. **`X-Frame-Options` header** — tells the browser whether your page can be framed.
   - `DENY` — never allow framing
   - `SAMEORIGIN` — only allow framing by the same origin
2. **CSP `frame-ancestors`** — the modern replacement for `X-Frame-Options`, more flexible.
3. **JavaScript frame-busting** — a client-side fallback (less reliable, can be bypassed).

```jsx
// 1. Server-side headers (Express) — PRIMARY DEFENSE
app.use((req, res, next) => {
  // Modern approach: CSP frame-ancestors
  // 'none' = cannot be framed by anyone (equivalent to X-Frame-Options: DENY)
  res.setHeader(
    "Content-Security-Policy",
    "frame-ancestors 'none'"
  );

  // Legacy fallback for older browsers
  res.setHeader("X-Frame-Options", "DENY");

  next();
});

// If you NEED your app to be framed by specific origins (e.g., embedded widget):
app.use("/embed", (req, res, next) => {
  res.setHeader(
    "Content-Security-Policy",
    "frame-ancestors 'self' https://trusted-partner.com"
  );
  res.setHeader("X-Frame-Options", "SAMEORIGIN");
  next();
});
```

```jsx
// 2. Client-side frame-busting (defense-in-depth, not primary defense)
// useFrameBuster.js
import { useEffect } from "react";

function useFrameBuster() {
  useEffect(() => {
    // Check if the page is loaded inside an iframe
    if (window.self !== window.top) {
      // Option 1: Break out of the frame
      try {
        window.top.location = window.self.location;
      } catch (e) {
        // Cross-origin — can't redirect. Hide the content instead.
        document.body.innerHTML = `
          <div style="padding: 40px; text-align: center;">
            <h1>Access Denied</h1>
            <p>This application cannot be embedded in an iframe.</p>
          </div>
        `;
      }
    }
  }, []);
}

// App.jsx — use the hook at the top level
function App() {
  useFrameBuster();

  return (
    <div className="app">
      {/* ...your application... */}
    </div>
  );
}
```

```jsx
// 3. React component for sensitive actions — double confirmation
// Protects against clickjacking even if framing prevention fails

function DangerousActionButton({ onConfirm, label }) {
  const [step, setStep] = useState("idle");

  const handleClick = () => {
    if (step === "idle") {
      setStep("confirming");
    } else if (step === "confirming") {
      onConfirm();
      setStep("idle");
    }
  };

  return (
    <div>
      {step === "idle" && (
        <button onClick={handleClick} className="btn-danger">
          {label}
        </button>
      )}
      {step === "confirming" && (
        <div className="confirmation-dialog">
          <p>Are you sure? This action cannot be undone.</p>
          <button onClick={handleClick} className="btn-danger">
            Yes, I'm sure
          </button>
          <button onClick={() => setStep("idle")} className="btn-secondary">
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
```

**Production recommendation:** Always set `frame-ancestors 'none'` (via CSP) and `X-Frame-Options: DENY` as server headers. Add JavaScript frame-busting as a defense-in-depth layer. For critical actions, use multi-step confirmation dialogs.

---

### Q12. How do you implement secure session management in a React application?

**Answer:**

**Session management** governs how user authentication state persists across requests and page reloads. Insecure sessions lead to session hijacking, session fixation, and privilege escalation. In a React SPA, session management typically uses one of two approaches: **server-side sessions** (with a session ID in an httpOnly cookie) or **stateless JWTs** (also in httpOnly cookies for security).

**Key principles:**
1. **Regenerate session ID after login** — prevents session fixation.
2. **Set expiration** — idle timeout + absolute timeout.
3. **Secure cookie attributes** — `httpOnly`, `Secure`, `SameSite`, `Path`.
4. **Invalidate on logout** — destroy the session server-side, not just client-side.
5. **Detect concurrent sessions** — alert users to multiple active sessions.

```jsx
// SessionManager.jsx — Client-side session monitoring
import { useEffect, useRef, useCallback } from "react";
import { useAuth } from "./AuthProvider";

const IDLE_TIMEOUT = 15 * 60 * 1000;      // 15 minutes
const WARNING_BEFORE = 2 * 60 * 1000;     // Warn 2 minutes before expiry
const HEARTBEAT_INTERVAL = 5 * 60 * 1000; // Ping server every 5 minutes

function SessionManager({ children }) {
  const { user, logout } = useAuth();
  const idleTimer = useRef(null);
  const warningTimer = useRef(null);
  const [showWarning, setShowWarning] = useState(false);

  const resetIdleTimer = useCallback(() => {
    clearTimeout(idleTimer.current);
    clearTimeout(warningTimer.current);
    setShowWarning(false);

    if (!user) return;

    // Show warning before timeout
    warningTimer.current = setTimeout(() => {
      setShowWarning(true);
    }, IDLE_TIMEOUT - WARNING_BEFORE);

    // Auto-logout on idle timeout
    idleTimer.current = setTimeout(() => {
      logout();
    }, IDLE_TIMEOUT);
  }, [user, logout]);

  // Track user activity
  useEffect(() => {
    if (!user) return;

    const events = ["mousedown", "keydown", "scroll", "touchstart"];
    const handleActivity = () => resetIdleTimer();

    events.forEach((event) => window.addEventListener(event, handleActivity));
    resetIdleTimer();

    return () => {
      events.forEach((event) =>
        window.removeEventListener(event, handleActivity)
      );
      clearTimeout(idleTimer.current);
      clearTimeout(warningTimer.current);
    };
  }, [user, resetIdleTimer]);

  // Heartbeat — keep session alive on the server while user is active
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(async () => {
      try {
        await fetch("/api/auth/heartbeat", {
          method: "POST",
          credentials: "include",
        });
      } catch {
        // Session expired server-side
        logout();
      }
    }, HEARTBEAT_INTERVAL);
    return () => clearInterval(interval);
  }, [user, logout]);

  // Detect logout in other tabs (via BroadcastChannel or storage event)
  useEffect(() => {
    const channel = new BroadcastChannel("auth");
    channel.onmessage = (event) => {
      if (event.data === "logout") {
        logout();
      }
    };
    return () => channel.close();
  }, [logout]);

  return (
    <>
      {children}
      {showWarning && (
        <div className="session-warning-overlay">
          <div className="session-warning-modal">
            <h2>Session Expiring</h2>
            <p>Your session will expire in 2 minutes due to inactivity.</p>
            <button onClick={resetIdleTimer}>Stay Logged In</button>
            <button onClick={logout}>Log Out</button>
          </div>
        </div>
      )}
    </>
  );
}

export default SessionManager;
```

**Server-side session configuration (Express + express-session):**

```jsx
const session = require("express-session");
const RedisStore = require("connect-redis").default;
const redis = require("redis");

const redisClient = redis.createClient({ url: process.env.REDIS_URL });
redisClient.connect();

app.use(
  session({
    store: new RedisStore({ client: redisClient }),
    secret: process.env.SESSION_SECRET,
    name: "__Host-sid",             // __Host- prefix enforces Secure + Path=/
    resave: false,
    saveUninitialized: false,
    rolling: true,                  // Reset expiry on every request
    cookie: {
      httpOnly: true,
      secure: true,
      sameSite: "strict",
      maxAge: 15 * 60 * 1000,      // 15 minutes
      path: "/",
    },
  })
);

// Regenerate session after login (prevents session fixation)
app.post("/auth/login", async (req, res) => {
  const user = await authenticateUser(req.body);
  req.session.regenerate((err) => {
    if (err) return res.status(500).json({ error: "Session error" });
    req.session.userId = user.id;
    req.session.role = user.role;
    req.session.loginTime = Date.now();
    res.json({ user: { id: user.id, name: user.name } });
  });
});

// Destroy session on logout
app.post("/auth/logout", (req, res) => {
  req.session.destroy((err) => {
    res.clearCookie("__Host-sid");
    res.json({ message: "Logged out" });
  });
});
```

---

## Advanced Level (Q13–Q20)

---

### Q13. Why is server-side validation essential even when your React app validates on the client?

**Answer:**

**Client-side validation in React is a UX feature, not a security feature.** Any validation that runs in the browser can be trivially bypassed — an attacker can disable JavaScript, modify the React state via DevTools, intercept and edit requests with a proxy like Burp Suite, or call your API directly with `curl`. The server is the **only trusted boundary**.

**What can go wrong without server-side validation:**
- **SQL injection** — a React form validates that a username is alphanumeric, but the attacker sends `'; DROP TABLE users; --` directly to the API.
- **Business logic bypass** — a React price calculator shows $99, but the attacker modifies the request body to $0.01.
- **Type confusion** — React sends a number, attacker sends an object or array.
- **Size/length bypass** — React enforces `maxLength={100}`, attacker sends 10 MB of data.

**Production pattern: Shared validation schema with Zod**

```jsx
// shared/schemas/userSchema.js — Use the SAME schema on client AND server
import { z } from "zod";

export const createUserSchema = z.object({
  email: z
    .string()
    .email("Invalid email address")
    .max(255, "Email too long")
    .transform((e) => e.toLowerCase().trim()),

  password: z
    .string()
    .min(12, "Password must be at least 12 characters")
    .max(128, "Password too long")
    .regex(/[A-Z]/, "Must contain an uppercase letter")
    .regex(/[a-z]/, "Must contain a lowercase letter")
    .regex(/[0-9]/, "Must contain a number")
    .regex(/[^A-Za-z0-9]/, "Must contain a special character"),

  name: z
    .string()
    .min(1, "Name is required")
    .max(100, "Name too long")
    .regex(/^[a-zA-Z\s'-]+$/, "Name contains invalid characters"),

  role: z.enum(["viewer", "editor"]),  // Users cannot self-assign "admin"
});

export const updateProfileSchema = createUserSchema
  .omit({ password: true, role: true })
  .partial();
```

```jsx
// CLIENT — React form with Zod validation
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createUserSchema } from "shared/schemas/userSchema";

function RegistrationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(createUserSchema),
  });

  const onSubmit = async (validatedData) => {
    // Data is already validated and transformed by Zod
    const response = await fetch("/api/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validatedData),
    });

    if (!response.ok) {
      const error = await response.json();
      // Display server-side validation errors
      alert(error.message);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("name")} placeholder="Full name" />
      {errors.name && <span className="error">{errors.name.message}</span>}

      <input {...register("email")} placeholder="Email" type="email" />
      {errors.email && <span className="error">{errors.email.message}</span>}

      <input {...register("password")} placeholder="Password" type="password" />
      {errors.password && <span className="error">{errors.password.message}</span>}

      <select {...register("role")}>
        <option value="viewer">Viewer</option>
        <option value="editor">Editor</option>
      </select>

      <button type="submit">Register</button>
    </form>
  );
}
```

```jsx
// SERVER — Express route with the SAME Zod schema
import { createUserSchema } from "shared/schemas/userSchema.js";
import bcrypt from "bcrypt";

app.post("/api/users", async (req, res) => {
  // Server-side validation — the REAL security boundary
  const result = createUserSchema.safeParse(req.body);

  if (!result.success) {
    return res.status(400).json({
      message: "Validation failed",
      errors: result.error.flatten().fieldErrors,
    });
  }

  const { email, password, name, role } = result.data;

  // Additional server-only checks
  const existingUser = await db.users.findByEmail(email);
  if (existingUser) {
    return res.status(409).json({ message: "Email already registered" });
  }

  // Hash password (NEVER store plain text)
  const hashedPassword = await bcrypt.hash(password, 12);

  const user = await db.users.create({
    email,
    password: hashedPassword,
    name,
    role, // Validated by Zod — cannot be "admin"
  });

  res.status(201).json({ user: { id: user.id, email, name, role } });
});
```

**Key takeaway:** Share validation schemas between client and server (using Zod, Yup, or Joi). The client uses the schema for UX; the server uses it as a security gate. Never trust `req.body` without server-side validation.

---

### Q14. What is Subresource Integrity (SRI), and how do you use it with React apps that load CDN scripts?

**Answer:**

**Subresource Integrity (SRI)** is a browser security feature that allows you to verify that files fetched from CDNs or third-party hosts have not been tampered with. You provide a cryptographic hash of the expected file content in the `integrity` attribute of `<script>` or `<link>` tags. If the downloaded file's hash doesn't match, the browser refuses to execute it.

**Why it matters for React apps:**
If you load React, a UI library, or analytics scripts from a CDN, and that CDN is compromised (or an attacker performs a man-in-the-middle attack), the browser will execute the tampered script with full access to your page's DOM, cookies, and user data. SRI ensures that only the exact file you intended is executed.

```jsx
<!-- index.html — Loading React from CDN with SRI -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Secure React App</title>

  <!-- CSS with SRI -->
  <link
    rel="stylesheet"
    href="https://cdn.example.com/styles/app.css"
    integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxAh6VgnkXM97QFijo0+lOg=="
    crossorigin="anonymous"
  />
</head>
<body>
  <div id="root"></div>

  <!-- Third-party scripts with SRI -->
  <script
    src="https://cdn.jsdelivr.net/npm/react@18.2.0/umd/react.production.min.js"
    integrity="sha384-Xz0bMHQo+ghl3/jSxOlCiZfP7yF0RFZi3/W1GChRPhjH7GNOnhNfrPAlK+cRJKp"
    crossorigin="anonymous"
  ></script>

  <!-- Your app bundle with SRI (hash generated at build time) -->
  <script
    src="https://cdn.example.com/js/app.abc123.js"
    integrity="sha384-generatedHashHere"
    crossorigin="anonymous"
  ></script>
</body>
</html>
```

**Generating SRI hashes at build time:**

```jsx
// scripts/generate-sri.js — Build script to compute SRI hashes
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const glob = require("glob");

function generateSRIHash(filePath, algorithm = "sha384") {
  const content = fs.readFileSync(filePath);
  const hash = crypto.createHash(algorithm).update(content).digest("base64");
  return `${algorithm}-${hash}`;
}

function addSRIToHTML(buildDir) {
  const htmlPath = path.join(buildDir, "index.html");
  let html = fs.readFileSync(htmlPath, "utf-8");

  // Find all script and link tags pointing to local assets
  const scriptRegex = /<script\s+src="(\/static\/js\/[^"]+)"/g;
  const linkRegex = /<link\s+[^>]*href="(\/static\/css\/[^"]+)"/g;

  let match;
  while ((match = scriptRegex.exec(html)) !== null) {
    const assetPath = path.join(buildDir, match[1]);
    if (fs.existsSync(assetPath)) {
      const hash = generateSRIHash(assetPath);
      html = html.replace(
        match[0],
        `${match[0]} integrity="${hash}" crossorigin="anonymous"`
      );
    }
  }

  while ((match = linkRegex.exec(html)) !== null) {
    const assetPath = path.join(buildDir, match[1]);
    if (fs.existsSync(assetPath)) {
      const hash = generateSRIHash(assetPath);
      html = html.replace(
        match[0],
        `${match[0]} integrity="${hash}" crossorigin="anonymous"`
      );
    }
  }

  fs.writeFileSync(htmlPath, html);
  console.log("SRI hashes added to index.html");
}

addSRIToHTML(path.join(__dirname, "../build"));
```

```jsx
// Webpack plugin approach (webpack.config.js)
const SriPlugin = require("webpack-subresource-integrity");

module.exports = {
  output: {
    crossOriginLoading: "anonymous", // Required for SRI
  },
  plugins: [
    new SriPlugin({
      hashFuncNames: ["sha384"],
      enabled: process.env.NODE_ENV === "production",
    }),
  ],
};
```

**Important notes:**
- SRI requires the `crossorigin` attribute on the tag — without it, the integrity check is skipped.
- SRI only works for files loaded from external origins or the same origin with CORS headers.
- Hashes must be regenerated on every build — automate this in your CI/CD pipeline.
- If you use a service worker, cache the integrity-verified files locally.

---

### Q15. How do you implement secure file uploads in a React application?

**Answer:**

File uploads are a high-risk attack surface. Malicious files can lead to **remote code execution** (uploading a PHP/JSP shell to a server that executes it), **stored XSS** (uploading an SVG with embedded JavaScript), **denial of service** (uploading enormous files), or **path traversal** (filenames like `../../etc/passwd`).

**Defense-in-depth strategy:**
1. **Client-side**: Validate file type, size, and count for UX.
2. **Server-side**: Re-validate everything. Never trust client headers.
3. **Storage**: Store files outside the web root; use object storage (S3) with randomized names.
4. **Serving**: Serve uploads from a different domain with restrictive headers.

```jsx
// SecureFileUpload.jsx — Client-side validation + upload
import { useState, useRef, useCallback } from "react";

const ALLOWED_TYPES = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
  "application/pdf": [".pdf"],
};
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const MAX_FILES = 5;

function validateFile(file) {
  const errors = [];

  // Check MIME type
  if (!ALLOWED_TYPES[file.type]) {
    errors.push(`File type "${file.type}" is not allowed.`);
  }

  // Check extension matches MIME type
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (ALLOWED_TYPES[file.type] && !ALLOWED_TYPES[file.type].includes(ext)) {
    errors.push(`Extension "${ext}" does not match type "${file.type}".`);
  }

  // Check size
  if (file.size > MAX_FILE_SIZE) {
    errors.push(`File exceeds maximum size of ${MAX_FILE_SIZE / 1024 / 1024} MB.`);
  }

  // Check filename for path traversal characters
  if (/[/\\:*?"<>|]/.test(file.name) || file.name.includes("..")) {
    errors.push("Filename contains invalid characters.");
  }

  return errors;
}

function SecureFileUpload({ onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);

  const handleFileSelect = useCallback((e) => {
    const selectedFiles = Array.from(e.target.files);
    const allErrors = [];

    if (selectedFiles.length > MAX_FILES) {
      allErrors.push(`Maximum ${MAX_FILES} files allowed.`);
    }

    const validFiles = [];
    selectedFiles.slice(0, MAX_FILES).forEach((file) => {
      const fileErrors = validateFile(file);
      if (fileErrors.length > 0) {
        allErrors.push(`${file.name}: ${fileErrors.join(", ")}`);
      } else {
        validFiles.push(file);
      }
    });

    setErrors(allErrors);
    setFiles(validFiles);
  }, []);

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setProgress(0);

    try {
      // Step 1: Get pre-signed URLs from the server
      // This keeps the upload credentials server-side
      const { data: presignedUrls } = await fetch("/api/uploads/presign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          files: files.map((f) => ({
            name: f.name,
            type: f.type,
            size: f.size,
          })),
        }),
      }).then((r) => r.json());

      // Step 2: Upload directly to S3 using pre-signed URLs
      const uploadPromises = files.map((file, index) => {
        return fetch(presignedUrls[index].url, {
          method: "PUT",
          body: file,
          headers: { "Content-Type": file.type },
        });
      });

      await Promise.all(uploadPromises);
      setProgress(100);
      onUploadComplete?.(presignedUrls.map((p) => p.fileId));
    } catch (err) {
      setErrors(["Upload failed. Please try again."]);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={Object.values(ALLOWED_TYPES).flat().join(",")}
        onChange={handleFileSelect}
        disabled={uploading}
      />

      {errors.length > 0 && (
        <ul className="upload-errors">
          {errors.map((err, i) => (
            <li key={i} className="error">{err}</li>
          ))}
        </ul>
      )}

      {files.length > 0 && (
        <div>
          <p>{files.length} file(s) ready to upload</p>
          <button onClick={handleUpload} disabled={uploading}>
            {uploading ? `Uploading... ${progress}%` : "Upload"}
          </button>
        </div>
      )}
    </div>
  );
}
```

**Server-side validation (Express + S3):**

```jsx
// uploads.controller.js
const { S3Client, PutObjectCommand } = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
const crypto = require("crypto");
const fileType = require("file-type");

const ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
const MAX_FILE_SIZE = 5 * 1024 * 1024;

app.post("/api/uploads/presign", authenticate, async (req, res) => {
  const { files } = req.body;

  if (!Array.isArray(files) || files.length > 5) {
    return res.status(400).json({ error: "Invalid file list" });
  }

  const presignedUrls = await Promise.all(
    files.map(async (file) => {
      // Server-side validation
      if (!ALLOWED_MIME_TYPES.includes(file.type)) {
        throw new Error(`Disallowed type: ${file.type}`);
      }
      if (file.size > MAX_FILE_SIZE) {
        throw new Error("File too large");
      }

      // Generate a random filename (prevents path traversal and overwrites)
      const fileId = crypto.randomUUID();
      const ext = file.name.split(".").pop().toLowerCase();
      const key = `uploads/${req.user.id}/${fileId}.${ext}`;

      const command = new PutObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: key,
        ContentType: file.type,
        ContentLength: file.size,
        // Scan for viruses using S3 event trigger + Lambda
      });

      const url = await getSignedUrl(s3Client, command, { expiresIn: 300 });
      return { fileId, url };
    })
  );

  res.json({ data: presignedUrls });
});
```

**Production tips:**
- Serve uploaded files from a **separate domain** (e.g., `uploads.example.com`) with `Content-Disposition: attachment` to prevent XSS via uploaded HTML/SVG.
- Run virus/malware scanning on uploads (ClamAV, AWS GuardDuty for S3).
- Validate the **actual file content** (magic bytes), not just the extension or MIME type header.

---

### Q16. How do you implement OAuth 2.0 / OpenID Connect with PKCE flow in a React SPA?

**Answer:**

**OAuth 2.0 with PKCE (Proof Key for Code Exchange)** is the recommended authorization flow for public clients like React SPAs (replacing the deprecated Implicit flow). PKCE prevents authorization code interception attacks by binding the authorization request to a cryptographic verifier.

**How PKCE works:**
1. The React app generates a random `code_verifier` and derives a `code_challenge` (SHA-256 hash).
2. The app redirects the user to the authorization server with the `code_challenge`.
3. After login, the authorization server redirects back with an `authorization_code`.
4. The app exchanges the code + `code_verifier` for tokens — the server verifies the challenge matches.
5. An attacker who intercepts the authorization code cannot exchange it without the `code_verifier`.

```jsx
// auth/pkce.js — PKCE utilities
export function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64UrlEncode(array);
}

export async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return base64UrlEncode(new Uint8Array(digest));
}

function base64UrlEncode(buffer) {
  return btoa(String.fromCharCode(...buffer))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export function generateState() {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return base64UrlEncode(array);
}
```

```jsx
// auth/OAuthProvider.jsx — Full PKCE flow implementation
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { generateCodeVerifier, generateCodeChallenge, generateState } from "./pkce";

const OAuthContext = createContext(null);

const OAUTH_CONFIG = {
  authorizationEndpoint: "https://auth.example.com/authorize",
  tokenEndpoint: "https://auth.example.com/oauth/token",
  userInfoEndpoint: "https://auth.example.com/userinfo",
  clientId: process.env.REACT_APP_OAUTH_CLIENT_ID,
  redirectUri: `${window.location.origin}/auth/callback`,
  scope: "openid profile email",
};

export function OAuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Step 1: Initiate login — redirect to authorization server
  const login = useCallback(async () => {
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);
    const state = generateState();

    // Store verifier and state in sessionStorage (survives the redirect)
    sessionStorage.setItem("pkce_code_verifier", codeVerifier);
    sessionStorage.setItem("oauth_state", state);

    const params = new URLSearchParams({
      response_type: "code",
      client_id: OAUTH_CONFIG.clientId,
      redirect_uri: OAUTH_CONFIG.redirectUri,
      scope: OAUTH_CONFIG.scope,
      state,
      code_challenge: codeChallenge,
      code_challenge_method: "S256",
    });

    window.location.href = `${OAUTH_CONFIG.authorizationEndpoint}?${params}`;
  }, []);

  // Step 2: Handle the callback — exchange code for tokens
  const handleCallback = useCallback(async () => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const returnedState = params.get("state");
    const error = params.get("error");

    if (error) {
      console.error("OAuth error:", error);
      return;
    }

    // Validate state to prevent CSRF
    const savedState = sessionStorage.getItem("oauth_state");
    if (returnedState !== savedState) {
      console.error("State mismatch — possible CSRF attack");
      return;
    }

    const codeVerifier = sessionStorage.getItem("pkce_code_verifier");

    // Exchange the authorization code for tokens via YOUR backend
    // (to avoid exposing the code_verifier in network logs of a third-party)
    try {
      const response = await fetch("/api/auth/oauth/callback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          code,
          codeVerifier,
          redirectUri: OAUTH_CONFIG.redirectUri,
        }),
      });

      const data = await response.json();
      setUser(data.user);

      // Clean up
      sessionStorage.removeItem("pkce_code_verifier");
      sessionStorage.removeItem("oauth_state");

      // Remove code from URL
      window.history.replaceState({}, "", "/dashboard");
    } catch (err) {
      console.error("Token exchange failed:", err);
    }
  }, []);

  // Check if we're on the callback URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (window.location.pathname === "/auth/callback" && params.get("code")) {
      handleCallback().finally(() => setLoading(false));
    } else {
      // Check existing session
      fetch("/api/auth/me", { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => setUser(data?.user || null))
        .finally(() => setLoading(false));
    }
  }, [handleCallback]);

  const logout = useCallback(async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    // Optionally redirect to the OAuth provider's logout endpoint
    window.location.href = "https://auth.example.com/logout?returnTo=" +
      encodeURIComponent(window.location.origin);
  }, []);

  return (
    <OAuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </OAuthContext.Provider>
  );
}

export const useOAuth = () => useContext(OAuthContext);
```

**Server-side token exchange (Express):**

```jsx
// The server performs the actual token exchange — keeping the client_secret server-side
app.post("/api/auth/oauth/callback", async (req, res) => {
  const { code, codeVerifier, redirectUri } = req.body;

  const tokenResponse = await fetch(OAUTH_CONFIG.tokenEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri,
      client_id: process.env.OAUTH_CLIENT_ID,
      client_secret: process.env.OAUTH_CLIENT_SECRET, // Server-only!
      code_verifier: codeVerifier,
    }),
  });

  const tokens = await tokenResponse.json();

  // Store tokens in httpOnly cookies
  res.cookie("access_token", tokens.access_token, {
    httpOnly: true, secure: true, sameSite: "Lax", maxAge: tokens.expires_in * 1000,
  });

  // Fetch user info
  const userInfo = await fetch(OAUTH_CONFIG.userInfoEndpoint, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  }).then((r) => r.json());

  res.json({ user: userInfo });
});
```

**Why PKCE over Implicit flow:** The Implicit flow returns the access token directly in the URL fragment, making it visible in browser history, referrer headers, and proxy logs. PKCE returns only an authorization code (useless without the verifier), then exchanges it securely.

---

### Q17. How do you implement rate limiting and bot protection in React applications?

**Answer:**

**Rate limiting** restricts how many requests a client can make in a given time window, preventing brute-force attacks, credential stuffing, DDoS, and API abuse. While rate limiting is enforced **server-side**, the React front-end plays a role in gracefully handling rate-limit responses and implementing client-side throttling.

**Bot protection** combines rate limiting with challenges (CAPTCHA), device fingerprinting, and behavioral analysis to distinguish humans from automated scripts.

**Server-side rate limiting (Express + rate-limit):**

```jsx
// middleware/rateLimiter.js
const rateLimit = require("express-rate-limit");
const RedisStore = require("rate-limit-redis").default;
const redis = require("redis");

const redisClient = redis.createClient({ url: process.env.REDIS_URL });
redisClient.connect();

// General API rate limit
export const generalLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 100,                    // 100 requests per window
  standardHeaders: true,       // Send RateLimit-* headers
  legacyHeaders: false,
  message: { error: "Too many requests. Please try again later." },
});

// Strict rate limit for auth endpoints
export const authLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args) => redisClient.sendCommand(args) }),
  windowMs: 15 * 60 * 1000,
  max: 5,                      // Only 5 login attempts per 15 minutes
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true, // Don't count successful logins
  message: { error: "Too many login attempts. Please try again in 15 minutes." },
  keyGenerator: (req) => {
    // Rate limit by IP + email combination
    return `${req.ip}-${req.body?.email || "unknown"}`;
  },
});

// Apply limiters
app.use("/api/", generalLimiter);
app.use("/api/auth/login", authLimiter);
app.use("/api/auth/register", authLimiter);
```

**React: handling rate-limit responses + CAPTCHA integration:**

```jsx
// hooks/useRateLimitedRequest.js
import { useState, useCallback, useRef } from "react";

function useRateLimitedRequest() {
  const [rateLimited, setRateLimited] = useState(false);
  const [retryAfter, setRetryAfter] = useState(0);
  const timerRef = useRef(null);

  const execute = useCallback(async (requestFn) => {
    if (rateLimited) {
      throw new Error(`Rate limited. Retry after ${retryAfter} seconds.`);
    }

    try {
      const response = await requestFn();
      return response;
    } catch (error) {
      if (error.response?.status === 429) {
        const retrySeconds = parseInt(
          error.response.headers["retry-after"] || "60",
          10
        );
        setRateLimited(true);
        setRetryAfter(retrySeconds);

        // Auto-reset after the retry period
        timerRef.current = setTimeout(() => {
          setRateLimited(false);
          setRetryAfter(0);
        }, retrySeconds * 1000);

        throw new Error(
          error.response.data?.error ||
            `Too many requests. Please wait ${retrySeconds} seconds.`
        );
      }
      throw error;
    }
  }, [rateLimited, retryAfter]);

  return { execute, rateLimited, retryAfter };
}

// LoginForm.jsx with rate limiting + reCAPTCHA
import ReCAPTCHA from "react-google-recaptcha";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [captchaToken, setCaptchaToken] = useState(null);
  const captchaRef = useRef(null);
  const { execute, rateLimited, retryAfter } = useRateLimitedRequest();

  const showCaptcha = attempts >= 3; // Show CAPTCHA after 3 failed attempts

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (showCaptcha && !captchaToken) {
      setError("Please complete the CAPTCHA.");
      return;
    }

    try {
      await execute(() =>
        fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            email,
            password,
            captchaToken: showCaptcha ? captchaToken : undefined,
          }),
        }).then((r) => {
          if (!r.ok) throw { response: r };
          return r.json();
        })
      );
      // Login successful — redirect
    } catch (err) {
      setAttempts((prev) => prev + 1);
      setError(err.message);
      captchaRef.current?.reset();
      setCaptchaToken(null);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        disabled={rateLimited}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        disabled={rateLimited}
      />

      {showCaptcha && (
        <ReCAPTCHA
          ref={captchaRef}
          sitekey={process.env.REACT_APP_RECAPTCHA_SITE_KEY}
          onChange={setCaptchaToken}
        />
      )}

      <button type="submit" disabled={rateLimited}>
        {rateLimited ? `Try again in ${retryAfter}s` : "Log In"}
      </button>

      {error && <p className="error">{error}</p>}
    </form>
  );
}
```

**Production architecture:** Use a WAF (AWS WAF, Cloudflare) as the first layer. Behind it, apply server-side rate limiting with Redis. On the client, handle 429 responses gracefully and present CAPTCHAs after suspicious behavior. For APIs, consider token-bucket algorithms that allow bursts while enforcing average rates.

---

### Q18. What security headers should you configure for a React SPA in production?

**Answer:**

Security headers are HTTP response headers that instruct the browser to enable or disable specific security features. They form a critical defense layer for React SPAs because they protect against XSS, clickjacking, MIME sniffing, information leakage, and more — all without requiring changes to your React code.

**Essential security headers and what they do:**

| Header | Purpose |
|---|---|
| `Content-Security-Policy` | Controls which resources can load (prevents XSS) |
| `Strict-Transport-Security` | Forces HTTPS (prevents downgrade attacks) |
| `X-Content-Type-Options` | Prevents MIME-type sniffing |
| `X-Frame-Options` | Prevents clickjacking (legacy; use CSP frame-ancestors) |
| `Referrer-Policy` | Controls referrer information sent with requests |
| `Permissions-Policy` | Restricts browser features (camera, mic, geolocation) |
| `X-XSS-Protection` | Legacy XSS filter (set to 0; CSP is superior) |
| `Cross-Origin-Opener-Policy` | Isolates browsing context |
| `Cross-Origin-Resource-Policy` | Controls cross-origin resource loading |
| `Cross-Origin-Embedder-Policy` | Required for SharedArrayBuffer |

```jsx
// middleware/securityHeaders.js — Express middleware
function securityHeaders(req, res, next) {
  // 1. Content Security Policy
  // Adapt based on your app's needs (CDN domains, API domains, etc.)
  res.setHeader(
    "Content-Security-Policy",
    [
      "default-src 'self'",
      "script-src 'self'",
      "style-src 'self' 'unsafe-inline'",  // CSS-in-JS often requires this
      "img-src 'self' data: https://cdn.example.com",
      "font-src 'self' https://fonts.gstatic.com",
      "connect-src 'self' https://api.example.com https://sentry.io",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests",
    ].join("; ")
  );

  // 2. HSTS — force HTTPS for 1 year, include subdomains, allow preload list
  res.setHeader(
    "Strict-Transport-Security",
    "max-age=31536000; includeSubDomains; preload"
  );

  // 3. Prevent MIME-type sniffing (stops browser from guessing content types)
  res.setHeader("X-Content-Type-Options", "nosniff");

  // 4. Clickjacking protection (legacy; CSP frame-ancestors above is the modern approach)
  res.setHeader("X-Frame-Options", "DENY");

  // 5. Referrer Policy — don't leak full URLs to third parties
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");

  // 6. Permissions Policy — disable unused browser features
  res.setHeader(
    "Permissions-Policy",
    [
      "camera=()",
      "microphone=()",
      "geolocation=()",
      "payment=(self)",            // Only allow Payment Request API on your origin
      "usb=()",
      "magnetometer=()",
      "gyroscope=()",
      "accelerometer=()",
    ].join(", ")
  );

  // 7. Disable legacy XSS filter (can introduce vulnerabilities)
  res.setHeader("X-XSS-Protection", "0");

  // 8. Cross-Origin isolation headers
  res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  res.setHeader("Cross-Origin-Resource-Policy", "same-origin");

  // 9. Remove headers that leak server info
  res.removeHeader("X-Powered-By");
  res.removeHeader("Server");

  next();
}

module.exports = securityHeaders;
```

**React component: Security headers audit tool (for internal use):**

```jsx
// SecurityHeadersAudit.jsx — Check your own app's headers
import { useState } from "react";

function SecurityHeadersAudit() {
  const [results, setResults] = useState(null);

  const EXPECTED_HEADERS = [
    { name: "content-security-policy", required: true },
    { name: "strict-transport-security", required: true },
    { name: "x-content-type-options", required: true, expected: "nosniff" },
    { name: "x-frame-options", required: true },
    { name: "referrer-policy", required: true },
    { name: "permissions-policy", required: true },
    { name: "x-xss-protection", required: false, expected: "0" },
    { name: "cross-origin-opener-policy", required: false },
  ];

  const auditHeaders = async () => {
    const response = await fetch(window.location.origin, { method: "HEAD" });
    const headerResults = EXPECTED_HEADERS.map((expected) => {
      const value = response.headers.get(expected.name);
      const present = !!value;
      const correct = expected.expected ? value === expected.expected : present;

      return {
        ...expected,
        value: value || "MISSING",
        status: correct ? "pass" : expected.required ? "fail" : "warn",
      };
    });
    setResults(headerResults);
  };

  return (
    <div>
      <h2>Security Headers Audit</h2>
      <button onClick={auditHeaders}>Run Audit</button>
      {results && (
        <table>
          <thead>
            <tr>
              <th>Header</th>
              <th>Status</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.name} className={r.status}>
                <td>{r.name}</td>
                <td>{r.status.toUpperCase()}</td>
                <td><code>{r.value}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

**Deployment-specific notes:**
- **Vercel/Netlify**: Configure headers in `vercel.json` or `netlify.toml` / `_headers` file.
- **Nginx**: Use `add_header` directives in the server block.
- **CloudFront**: Use Lambda@Edge or CloudFront Functions to inject headers.
- **Test your headers**: Use [securityheaders.com](https://securityheaders.com) or Mozilla Observatory.

---

### Q19. How do you approach penetration testing and security audits for a React application?

**Answer:**

**Penetration testing** (pen testing) is the practice of simulating real-world attacks against your application to discover vulnerabilities before attackers do. For a React SPA, pen testing covers both the **client-side** (DOM XSS, insecure storage, client-side logic bypass) and the **server-side** (API vulnerabilities, authentication flaws, injection attacks).

**Three-phase approach:**

1. **Automated scanning** — quick, broad coverage (OWASP ZAP, Burp Suite Scanner, Snyk).
2. **Manual testing** — targeted attacks by a human tester against business logic, auth flows, and access control.
3. **Code review** — static analysis of the React source code and server code (ESLint security plugins, Semgrep, SonarQube).

**Phase 1: Automated scanning setup**

```jsx
// .eslintrc.js — Security-focused linting rules
module.exports = {
  plugins: ["security", "no-unsanitized"],
  extends: ["plugin:security/recommended"],
  rules: {
    // Detect dangerous patterns in React code
    "no-unsanitized/method": "error",     // Flags innerHTML, document.write
    "no-unsanitized/property": "error",   // Flags .innerHTML assignments
    "security/detect-object-injection": "warn",
    "security/detect-non-literal-regexp": "warn",
    "security/detect-eval-with-expression": "error",
    "security/detect-no-csrf-before-method-override": "error",

    // React-specific
    "react/no-danger": "warn",            // Flags dangerouslySetInnerHTML
    "react/jsx-no-target-blank": "error", // Flags target="_blank" without rel
    "react/jsx-no-script-url": "error",   // Flags javascript: URLs in JSX
  },
};
```

**Phase 2: Security test checklist component (for QA teams)**

```jsx
// SecurityTestChecklist.jsx — Interactive checklist for manual pen testing
import { useState } from "react";

const SECURITY_TESTS = [
  {
    category: "XSS",
    tests: [
      {
        id: "xss-1",
        name: "Reflected XSS via URL parameters",
        description: "Try injecting <script>alert(1)</script> in all URL params",
        severity: "critical",
      },
      {
        id: "xss-2",
        name: "Stored XSS via form inputs",
        description: "Submit <img src=x onerror=alert(1)> in every text field",
        severity: "critical",
      },
      {
        id: "xss-3",
        name: "DOM XSS via dangerouslySetInnerHTML",
        description: "Identify all uses and verify DOMPurify sanitization",
        severity: "critical",
      },
      {
        id: "xss-4",
        name: "javascript: URL injection",
        description: "Test all user-provided URLs for javascript: protocol",
        severity: "high",
      },
    ],
  },
  {
    category: "Authentication",
    tests: [
      {
        id: "auth-1",
        name: "Brute force login",
        description: "Attempt 100 rapid login attempts — verify rate limiting",
        severity: "high",
      },
      {
        id: "auth-2",
        name: "Session fixation",
        description: "Verify session ID changes after login",
        severity: "high",
      },
      {
        id: "auth-3",
        name: "JWT/token in localStorage",
        description: "Check DevTools > Application > Local Storage for tokens",
        severity: "medium",
      },
      {
        id: "auth-4",
        name: "Password reset flow",
        description: "Test for token reuse, expiration, and enumeration",
        severity: "high",
      },
    ],
  },
  {
    category: "Authorization",
    tests: [
      {
        id: "authz-1",
        name: "IDOR (Insecure Direct Object Reference)",
        description: "Change IDs in API requests to access other users' data",
        severity: "critical",
      },
      {
        id: "authz-2",
        name: "Privilege escalation",
        description: "Try accessing admin APIs with a regular user token",
        severity: "critical",
      },
      {
        id: "authz-3",
        name: "Client-side route guard bypass",
        description: "Navigate directly to /admin URLs without auth",
        severity: "medium",
      },
    ],
  },
  {
    category: "CSRF",
    tests: [
      {
        id: "csrf-1",
        name: "Cross-origin POST without CSRF token",
        description: "Create an HTML form on a different origin and submit to API",
        severity: "high",
      },
      {
        id: "csrf-2",
        name: "SameSite cookie verification",
        description: "Verify cookies have SameSite=Strict or Lax",
        severity: "medium",
      },
    ],
  },
  {
    category: "Headers & Configuration",
    tests: [
      {
        id: "hdr-1",
        name: "Security headers present",
        description: "Run securityheaders.com scan — target A+ grade",
        severity: "medium",
      },
      {
        id: "hdr-2",
        name: "CORS misconfiguration",
        description: "Test with Origin: https://evil.com — should be rejected",
        severity: "high",
      },
      {
        id: "hdr-3",
        name: "Source maps in production",
        description: "Check if .map files are publicly accessible",
        severity: "medium",
      },
    ],
  },
];

function SecurityTestChecklist() {
  const [results, setResults] = useState({});

  const setTestResult = (testId, status) => {
    setResults((prev) => ({ ...prev, [testId]: status }));
  };

  const passCount = Object.values(results).filter((r) => r === "pass").length;
  const failCount = Object.values(results).filter((r) => r === "fail").length;
  const totalTests = SECURITY_TESTS.flatMap((c) => c.tests).length;

  return (
    <div className="security-checklist">
      <h1>Security Pen Test Checklist</h1>
      <p>
        Progress: {passCount + failCount} / {totalTests} completed |
        <span className="pass"> {passCount} passed</span> |
        <span className="fail"> {failCount} failed</span>
      </p>

      {SECURITY_TESTS.map((category) => (
        <div key={category.category}>
          <h2>{category.category}</h2>
          {category.tests.map((test) => (
            <div key={test.id} className={`test-item ${results[test.id] || ""}`}>
              <div>
                <strong>{test.name}</strong>
                <span className={`severity ${test.severity}`}>
                  {test.severity}
                </span>
                <p>{test.description}</p>
              </div>
              <div className="test-actions">
                <button onClick={() => setTestResult(test.id, "pass")}>
                  Pass
                </button>
                <button onClick={() => setTestResult(test.id, "fail")}>
                  Fail
                </button>
                <button onClick={() => setTestResult(test.id, "skip")}>
                  Skip
                </button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

**CI/CD integration for automated security scanning:**

```jsx
// Security automation scripts for CI

// 1. OWASP ZAP baseline scan (run in CI against staging)
// docker run -t owasp/zap2docker-stable zap-baseline.py \
//   -t https://staging.example.com -r report.html

// 2. Semgrep for React-specific vulnerabilities
// npx semgrep --config p/react --config p/javascript --error

// 3. Check for secrets in code
// npx trufflehog filesystem --directory=. --only-verified

// 4. Lighthouse security audit
// npx lighthouse https://staging.example.com \
//   --only-categories=best-practices --output=json
```

**Production cadence:** Run automated scans on every PR (ESLint security, Semgrep, `npm audit`). Run OWASP ZAP baseline scans weekly against staging. Conduct full manual pen tests quarterly or before major releases. Engage external pen testers annually.

---

### Q20. Describe a production security architecture for a React application covering authentication, authorization, XSS, CSRF, CSP, and monitoring.

**Answer:**

This question synthesizes everything covered in Q1–Q19 into a **holistic security architecture** for a production React application. The architecture below is modeled after a real-world financial SaaS application handling sensitive user data.

**Architecture overview:**

```
[User Browser]
    │
    ├── React SPA (CSP nonce, SRI hashes)
    │
    ▼
[CDN / Edge Layer — Cloudflare / AWS CloudFront]
    │  ├── WAF rules (rate limiting, bot detection, geo-blocking)
    │  ├── DDoS protection
    │  └── Security headers injected via edge function
    │
    ▼
[API Gateway / Load Balancer]
    │  ├── TLS termination (TLS 1.3)
    │  ├── CORS enforcement
    │  └── Request size limits
    │
    ▼
[Application Server (Node.js / Express)]
    │  ├── Authentication middleware (JWT in httpOnly cookies)
    │  ├── Authorization middleware (RBAC/ABAC)
    │  ├── CSRF validation
    │  ├── Input validation (Zod schemas)
    │  ├── Rate limiting (Redis-backed)
    │  └── Audit logging
    │
    ▼
[Database Layer]
    │  ├── Parameterized queries (no SQL injection)
    │  ├── Encryption at rest
    │  └── Row-level security (Postgres RLS)
    │
    ▼
[Monitoring & Alerting]
    ├── Sentry (error tracking, CSP violation reports)
    ├── Datadog / Grafana (metrics, anomaly detection)
    └── PagerDuty (security incident alerts)
```

**Implementation — the complete security layer:**

```jsx
// ============================================================
// 1. SECURITY CONFIGURATION — Central config
// ============================================================
// config/security.js
export const securityConfig = {
  auth: {
    accessTokenExpiry: "15m",
    refreshTokenExpiry: "7d",
    maxLoginAttempts: 5,
    lockoutDuration: 15 * 60 * 1000, // 15 minutes
    passwordMinLength: 12,
    mfaEnabled: true,
  },
  cookies: {
    httpOnly: true,
    secure: true,
    sameSite: "Strict",
    path: "/",
    domain: ".example.com",
  },
  cors: {
    allowedOrigins: [
      "https://app.example.com",
      "https://staging-app.example.com",
    ],
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE"],
    credentials: true,
  },
  rateLimit: {
    general: { windowMs: 15 * 60 * 1000, max: 200 },
    auth: { windowMs: 15 * 60 * 1000, max: 5 },
    api: { windowMs: 1 * 60 * 1000, max: 60 },
  },
  csp: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],  // nonce added dynamically
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https://cdn.example.com"],
      connectSrc: [
        "'self'",
        "https://api.example.com",
        "https://sentry.io",
      ],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      frameAncestors: ["'none'"],
      baseUri: ["'self'"],
      formAction: ["'self'"],
    },
    reportUri: "/api/csp-violations",
  },
};
```

```jsx
// ============================================================
// 2. SERVER — Security middleware stack
// ============================================================
// server.js
const express = require("express");
const helmet = require("helmet");
const cors = require("cors");
const rateLimit = require("express-rate-limit");
const { securityConfig } = require("./config/security");

const app = express();

// --- Helmet: sets many security headers automatically ---
app.use(
  helmet({
    contentSecurityPolicy: false, // We configure CSP manually with nonces
    crossOriginEmbedderPolicy: true,
    crossOriginOpenerPolicy: { policy: "same-origin" },
    crossOriginResourcePolicy: { policy: "same-origin" },
    dnsPrefetchControl: true,
    frameguard: { action: "deny" },
    hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
    referrerPolicy: { policy: "strict-origin-when-cross-origin" },
    xContentTypeOptions: true,
    xXssProtection: false, // Deprecated; CSP is better
  })
);

// --- CORS ---
app.use(
  cors({
    origin: (origin, cb) => {
      if (!origin || securityConfig.cors.allowedOrigins.includes(origin)) {
        cb(null, true);
      } else {
        cb(new Error("CORS violation"));
      }
    },
    credentials: securityConfig.cors.credentials,
    methods: securityConfig.cors.methods,
    allowedHeaders: ["Content-Type", "X-CSRF-Token"],
  })
);

// --- Rate Limiting ---
app.use("/api/", rateLimit(securityConfig.rateLimit.general));
app.use("/api/auth/", rateLimit(securityConfig.rateLimit.auth));

// --- CSP with nonces ---
app.use((req, res, next) => {
  const crypto = require("crypto");
  const nonce = crypto.randomBytes(16).toString("base64");
  res.locals.nonce = nonce;

  const directives = securityConfig.csp.directives;
  const csp = Object.entries(directives)
    .map(([key, values]) => {
      const directive = key.replace(/([A-Z])/g, "-$1").toLowerCase();
      const vals =
        directive === "script-src"
          ? [...values, `'nonce-${nonce}'`]
          : values;
      return `${directive} ${vals.join(" ")}`;
    })
    .join("; ");

  res.setHeader("Content-Security-Policy", csp);
  next();
});

// --- CSP violation reporting ---
app.post("/api/csp-violations", express.json({ type: "application/csp-report" }), (req, res) => {
  const violation = req.body["csp-report"];
  console.error("CSP Violation:", {
    blockedUri: violation?.["blocked-uri"],
    violatedDirective: violation?.["violated-directive"],
    documentUri: violation?.["document-uri"],
  });
  // Send to Sentry or logging service
  res.status(204).end();
});
```

```jsx
// ============================================================
// 3. REACT CLIENT — Secure App Shell
// ============================================================
// App.jsx
import { StrictMode } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { SecurityMonitor } from "./security/SecurityMonitor";
import { ErrorBoundary } from "./components/ErrorBoundary";
import ProtectedRoute from "./auth/ProtectedRoute";
import SessionManager from "./auth/SessionManager";

function App() {
  return (
    <StrictMode>
      <ErrorBoundary>
        <AuthProvider>
          <SessionManager>
            <SecurityMonitor>
              <BrowserRouter>
                <Routes>
                  {/* Public */}
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/auth/callback" element={<OAuthCallback />} />

                  {/* Authenticated */}
                  <Route element={<ProtectedRoute />}>
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/profile" element={<Profile />} />
                  </Route>

                  {/* Admin */}
                  <Route element={<ProtectedRoute requiredPermission="admin:settings" />}>
                    <Route path="/admin/*" element={<AdminPanel />} />
                  </Route>
                </Routes>
              </BrowserRouter>
            </SecurityMonitor>
          </SessionManager>
        </AuthProvider>
      </ErrorBoundary>
    </StrictMode>
  );
}
```

```jsx
// ============================================================
// 4. SECURITY MONITOR — Client-side threat detection
// ============================================================
// security/SecurityMonitor.jsx
import { useEffect, createContext, useContext, useRef } from "react";
import * as Sentry from "@sentry/react";

const SecurityContext = createContext(null);

export function SecurityMonitor({ children }) {
  const violationCount = useRef(0);

  useEffect(() => {
    // Monitor for XSS attempts via CSP violations
    const handleSecurityPolicyViolation = (event) => {
      violationCount.current += 1;

      Sentry.captureEvent({
        message: "CSP Violation Detected",
        level: "warning",
        extra: {
          blockedURI: event.blockedURI,
          violatedDirective: event.violatedDirective,
          originalPolicy: event.originalPolicy,
          documentURI: event.documentURI,
          count: violationCount.current,
        },
      });

      // If many violations in a short period — possible attack
      if (violationCount.current > 10) {
        Sentry.captureMessage("Possible XSS attack — high CSP violation rate", "error");
      }
    };

    // Monitor for suspicious iframe embedding
    const checkFraming = () => {
      if (window.self !== window.top) {
        Sentry.captureMessage("Application loaded in iframe — possible clickjacking", "error");
        document.body.style.display = "none";
      }
    };

    // Monitor for DevTools open (optional — for high-security apps)
    const detectDevTools = () => {
      const threshold = 160;
      if (
        window.outerWidth - window.innerWidth > threshold ||
        window.outerHeight - window.innerHeight > threshold
      ) {
        // Log but don't block — legitimate users also use DevTools
        console.info("[Security] DevTools detected");
      }
    };

    document.addEventListener("securitypolicyviolation", handleSecurityPolicyViolation);
    checkFraming();

    return () => {
      document.removeEventListener("securitypolicyviolation", handleSecurityPolicyViolation);
    };
  }, []);

  // Monitor navigation for open redirect attempts
  useEffect(() => {
    const handleClick = (event) => {
      const anchor = event.target.closest("a");
      if (anchor?.href) {
        try {
          const url = new URL(anchor.href);
          const trustedDomains = ["example.com", "cdn.example.com"];
          const isTrusted = trustedDomains.some(
            (d) => url.hostname === d || url.hostname.endsWith(`.${d}`)
          );

          if (!isTrusted && url.protocol !== "mailto:") {
            // External link — ensure rel attributes are set
            anchor.setAttribute("rel", "noopener noreferrer");
            anchor.setAttribute("target", "_blank");
          }
        } catch {
          // Invalid URL — block it
          event.preventDefault();
        }
      }
    };

    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, []);

  return (
    <SecurityContext.Provider value={{}}>
      {children}
    </SecurityContext.Provider>
  );
}
```

```jsx
// ============================================================
// 5. SECURE API CLIENT — Ties everything together
// ============================================================
// api/secureClient.js
import axios from "axios";
import * as Sentry from "@sentry/react";

const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  withCredentials: true,
  timeout: 30000,
});

// Request: CSRF token + request ID for tracing
client.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content");
    if (csrfToken) {
      config.headers["X-CSRF-Token"] = csrfToken;
    }
  }
  // Unique request ID for distributed tracing
  config.headers["X-Request-ID"] = crypto.randomUUID();
  return config;
});

// Response: centralized security error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;

    switch (status) {
      case 401:
        window.dispatchEvent(new CustomEvent("auth:session-expired"));
        break;
      case 403:
        Sentry.captureMessage("Forbidden access attempt", {
          level: "warning",
          extra: { url: error.config?.url, method: error.config?.method },
        });
        break;
      case 429:
        // Rate limited — don't retry aggressively
        Sentry.captureMessage("Rate limit hit", {
          level: "info",
          extra: { retryAfter: error.response?.headers["retry-after"] },
        });
        break;
      default:
        break;
    }

    return Promise.reject(error);
  }
);

export default client;
```

**Production deployment security checklist:**

```jsx
// DEPLOYMENT CHECKLIST — verify before every release
const PRODUCTION_SECURITY_CHECKLIST = [
  // Build
  "[ ] Source maps are NOT deployed to production (or are behind auth)",
  "[ ] Environment variables contain no secrets (only public keys)",
  "[ ] npm audit shows 0 critical/high vulnerabilities",
  "[ ] Bundle analyzer confirms no unexpected dependencies",

  // Headers
  "[ ] CSP header is strict and tested (securityheaders.com grade A+)",
  "[ ] HSTS header with preload is set",
  "[ ] X-Frame-Options: DENY is set",
  "[ ] Permissions-Policy disables unused APIs",

  // Authentication
  "[ ] Tokens stored in httpOnly Secure SameSite cookies",
  "[ ] Refresh token rotation is enabled",
  "[ ] Session expires after 15 minutes of inactivity",
  "[ ] Login endpoint is rate-limited (5 attempts / 15 min)",

  // Authorization
  "[ ] All API endpoints verify permissions server-side",
  "[ ] IDOR tests pass (cannot access other users' data)",
  "[ ] Admin routes are protected on both client and server",

  // Data
  "[ ] All user input is validated server-side (Zod schemas)",
  "[ ] DOMPurify sanitizes all dangerouslySetInnerHTML usage",
  "[ ] File uploads are validated by magic bytes, not just extension",
  "[ ] Database queries use parameterized statements",

  // Monitoring
  "[ ] Sentry captures CSP violations and auth anomalies",
  "[ ] WAF rules are active (rate limiting, bot detection)",
  "[ ] Audit logs track all privilege changes and data access",
  "[ ] Alerting is configured for suspicious patterns",
];
```

**Key takeaway:** Security in a production React application is **not a single feature** — it's a layered architecture spanning the CDN edge, server middleware, database layer, client-side code, and monitoring infrastructure. Every layer assumes the others might fail (defense-in-depth). The React front-end is one piece of a much larger security puzzle, and the server is always the ultimate authority for authentication, authorization, and data validation.
