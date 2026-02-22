# 28. Security (CORS, XSS, CSP) (Senior)

## Q1. What is the Same-Origin Policy and what does it restrict?

**Answer:**  
**Same-Origin Policy**: A document or script from origin A can only access resources from the same origin (same scheme, host, port). It restricts: (1) Reading responses from cross-origin XHR/fetch (without CORS). (2) Access to another origin’s DOM (e.g. iframe). (3) Cookies/localStorage for other origins. It does not block embedding (e.g. scripts, images, iframes); the embedder can’t read cross-origin content. Purpose: isolate sites so one origin can’t steal another’s data.

---

## Q2. Explain CORS: what problem it solves, and what are preflight and simple requests?

**Answer:**  
**CORS** (Cross-Origin Resource Sharing) lets a server explicitly allow certain origins to read responses. **Simple requests** (GET/HEAD/POST with simple headers and content-type) are sent directly; the server responds with `Access-Control-Allow-Origin` (and optionally credentials). **Preflight**: For non-simple requests, the browser first sends an OPTIONS request; the server must allow the method and headers via CORS headers; then the actual request is sent. Without the right headers, the browser blocks the response from JS.

---

## Q3. What headers does the server need to send to allow a cross-origin request with credentials (cookies)?

**Answer:**  
- **Access-Control-Allow-Origin**: Must be the requesting origin (not `*` when credentials are used).  
- **Access-Control-Allow-Credentials: true**.  
- Optionally **Access-Control-Allow-Methods**, **Access-Control-Allow-Headers**, **Access-Control-Expose-Headers** for preflight.  
The client must use `fetch(url, { credentials: 'include' })` (or XHR with `withCredentials: true`).

---

## Q4. What is XSS? Name two types and how to mitigate each.

**Answer:**  
**XSS** (Cross-Site Scripting): Attacker injects script that runs in the victim’s browser in the context of your site. **Stored XSS**: Malicious script stored (e.g. in DB) and served to users; mitigate by encoding output (escape HTML/JS) and Content-Security-Policy. **Reflected XSS**: Script in URL or input echoed in response; mitigate by never inserting user input into HTML/JS without encoding, and using CSP. Also: sanitize/validate input, use HttpOnly cookies so script can’t read them.

---

## Q5. What is Content-Security-Policy (CSP)? What does `script-src 'self'` do?

**Answer:**  
**CSP** is a response header that restricts where scripts, styles, and other resources can load from and whether inline script/style are allowed. **`script-src 'self'`** means only scripts from the same origin are allowed; inline scripts (e.g. `<script>...</script>`) are blocked unless you add `'unsafe-inline'` (not recommended). CSP reduces impact of XSS by preventing execution of unauthorized or injected scripts.

---

## Q6. What is CSRF? How do you protect an API that uses cookie-based sessions?

**Answer:**  
**CSRF** (Cross-Site Request Forgery): A malicious site triggers a request to your site using the user’s stored cookies (e.g. form submit or img src). Protection: (1) **CSRF tokens**: Server sends a token in a cookie or page; client sends it in a header or body; server checks match. (2) **SameSite cookies**: `SameSite=Strict` or `Lax` so cookies aren’t sent on cross-site requests. (3) **Custom header**: Require a header that only your JS can set (e.g. X-Requested-With); same-origin policy blocks other sites from adding it. (4) **Origin/Referer** check on server.

---

## Q7. Why is `eval()` (or inserting user input into script) dangerous? What alternatives exist?

**Answer:**  
`eval()` (or `new Function(userInput)`) runs arbitrary code; if the input comes from the user or an attacker, it’s code injection (XSS or server-side). Alternatives: (1) **Structured data**: Send JSON and use it as data, not code. (2) **Sandbox**: If you must run code, use a sandbox (e.g. isolated iframe, Web Workers, or a server-side sandbox). (3) **Templating**: Use a safe template engine that doesn’t interpret input as code. (4) **CSP**: Disable eval and inline script so even if someone injects script, it may not run.

---

## Q8. What is the difference between HttpOnly and Secure cookie flags?

**Answer:**  
**HttpOnly**: Cookie is not accessible from JavaScript (`document.cookie`). Reduces theft via XSS. **Secure**: Cookie is sent only over HTTPS. Reduces exposure on the wire. Use both for session cookies: `Set-Cookie: sid=...; HttpOnly; Secure; SameSite=Strict`.

---

## Q9. How does Subresource Integrity (SRI) work and when would you use it?

**Answer:**  
**SRI**: You serve a hash of the expected script/style content in the `integrity` attribute. The browser fetches the resource and verifies the hash; if it doesn’t match (e.g. CDN compromised), the resource is not used. Use when loading scripts or styles from a third-party CDN to ensure they haven’t been tampered with.

---

## Q10. You have an API that different frontends (web and mobile) will call. How do you design auth and avoid CORS/CSRF issues?

**Answer:**  
(1) **Auth**: Use tokens (e.g. JWT) in **Authorization** header or a custom header, not cookies for the API. That avoids cookie-based CSRF and CORS credential complexity. (2) **CORS**: Set `Access-Control-Allow-Origin` to specific origins (or a list); avoid `*` if you need credentials or sensitive data. (3) **HTTPS** and short-lived tokens; refresh token in httpOnly cookie only for web if you need it. (4) **CSRF**: With token-in-header, no cookie is sent automatically, so classic CSRF is reduced; still validate origin/referer for browser clients. (5) **Mobile**: Same token in header; no CORS on native clients.
