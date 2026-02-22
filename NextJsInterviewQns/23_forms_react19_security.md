# 23. Forms, React 19 & Security (XSS, CSRF, Env)

## Topic Introduction

**Forms** in Next.js 15/16 are built on **Server Actions**, **useActionState** (React 19), **useFormStatus**, and optional **useOptimistic**. **Security** covers XSS (React escaping, dangerouslySetInnerHTML), CSRF (SameSite cookies, tokens, Origin check), and **environment variables** (NEXT_PUBLIC_ vs server-only, rotation). Senior developers must implement safe, progressive forms and harden production apps.

```
Form + Security flow:
┌─────────────────────────────────────────────────────────────┐
│  Form (Client or Server-rendered)                           │
│     │ action={serverAction}  or  onSubmit → fetch/serverAction │
│     ▼                                                         │
│  Server Action                                                 │
│     ├─ Validate input (Zod)                                   │
│     ├─ Check auth/session                                     │
│     ├─ CSRF: same-origin or token                             │
│     ├─ Mutate DB / call API                                   │
│     └─ revalidatePath / redirect / return                     │
│     │                                                         │
│     ▼                                                         │
│  Client: useActionState (pending, error), useOptimistic        │
│  Env: Server-only vars never in client bundle                 │
└─────────────────────────────────────────────────────────────┘
```

**Next.js 15 vs 16**: Same Server Actions and security model. React 19 brings **useActionState** and **useFormStatus**; Next.js 16 supports them. Always validate on the server; never trust client-only checks.

---

## Q1. (Beginner) How do you submit a form to a Server Action in the App Router?

**Scenario**: Simple contact form; on submit, run a server function.

**Answer**:

Set the form’s **action** to the Server Action. No need for a separate API route.

```tsx
// actions/contact.ts
'use server';

import { redirect } from 'next/navigation';

export async function submitContact(formData: FormData) {
  const name = formData.get('name') as string;
  const email = formData.get('email') as string;
  if (!name || !email) return { error: 'Missing fields' };
  await db.contacts.create({ name, email });
  redirect('/thank-you');
}
```

```tsx
// app/contact/page.tsx
import { submitContact } from '@/actions/contact';

export default function ContactPage() {
  return (
    <form action={submitContact}>
      <input name="name" required />
      <input name="email" type="email" required />
      <button type="submit">Send</button>
    </form>
  );
}
```

---

## Q2. (Beginner) What is useFormStatus and when do you use it?

**Scenario**: Show "Submitting…" on the button while the form is submitting.

**Answer**:

**useFormStatus** (React 19) returns **pending** for the form that is currently submitting. It must be used in a **child** of the form (not in the same component that renders the form), and that child must be a Client Component.

```tsx
'use client';
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting…' : 'Submit'}
    </button>
  );
}

export function ContactForm() {
  return (
    <form action={submitContact}>
      <input name="email" />
      <SubmitButton />
    </form>
  );
}
```

---

## Q3. (Beginner) How do you avoid XSS when rendering user-generated HTML (e.g. blog body)?

**Scenario**: Blog content is stored as HTML; you need to show it safely.

**Answer**:

- **Prefer**: Don’t render raw HTML. Store and render **Markdown** or a safe subset (e.g. a sanitized subset of HTML).
- **If you must**: Use a **sanitization** library (e.g. DOMPurify) **on the server** (or in a trusted environment) to strip scripts and dangerous attributes, then pass the sanitized string to **dangerouslySetInnerHTML**. Never pass unsanitized user input to **dangerouslySetInnerHTML**. React’s default escaping only applies to text and attributes, not to the content you inject with **dangerouslySetInnerHTML**.

```tsx
import DOMPurify from 'isomorphic-dompurify';

export function SafeHtml({ html }: { html: string }) {
  const sanitized = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
}
```

---

## Q4. (Beginner) What is the difference between NEXT_PUBLIC_ env vars and server-only env vars?

**Answer**:

- **NEXT_PUBLIC_***: Inlined at build time into the **client** bundle. Anyone can see them in the browser. Use only for non-secret config (e.g. public API URL).
- **Server-only** (no prefix): Available only in Server Components, Server Actions, Route Handlers, and build-time Node. Never sent to the client. Use for DB URLs, API secrets, private keys.

Never put secrets in **NEXT_PUBLIC_**. Use **server-only** package in modules that use secrets so they can’t be imported from Client Components by mistake.

---

## Q5. (Beginner) How do you show validation errors from a Server Action next to the form fields?

**Scenario**: Server Action validates with Zod and returns field-level errors.

**Answer**:

Return an object (e.g. `{ errors: { field: string } }`) from the Server Action and use it in the form component. With **useActionState** (React 19), you can bind the action and get the previous state/error in the same component.

```tsx
// actions/signup.ts
'use server';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export async function signUp(prev: unknown, formData: FormData) {
  const parsed = schema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });
  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors };
  }
  await createUser(parsed.data);
  return { errors: {} };
}
```

```tsx
'use client';
import { useActionState } from 'react';
import { signUp } from '@/actions/signup';

export function SignUpForm() {
  const [state, formAction] = useActionState(signUp, null);

  return (
    <form action={formAction}>
      <input name="email" type="email" />
      {state?.errors?.email && <span>{state.errors.email}</span>}
      <input name="password" type="password" />
      {state?.errors?.password && <span>{state.errors.password}</span>}
      <button type="submit">Sign up</button>
    </form>
  );
}
```

---

## Q6. (Intermediate) How do you protect Server Actions against CSRF? What does Next.js do by default?

**Scenario**: You want to ensure form submissions and mutations can’t be triggered from another origin.

**Answer**:

- **Same-origin**: Browsers send cookies (including session) only to the same origin. If your app and API are on the same origin, a request from another site won’t include your cookies, so the server won’t see a session. That mitigates CSRF for cookie-based auth **if** you don’t use GET for mutations and you don’t allow arbitrary origins via CORS.
- **Next.js**: Server Actions are invoked with **POST** and a **Next-Action** header; they’re intended to be used from your own pages. Don’t expose them as a general API to other origins.
- **Extra hardening**: Check **Origin** or **Referer** in middleware or inside the Server Action (must match your app origin). For sensitive actions, use a **CSRF token** in a cookie and in the form (or header); verify they match on the server.

---

## Q7. (Intermediate) Implement a Server Action that uploads a file and validates type/size. Show error handling.

**Scenario**: User uploads avatar; max 2MB, only images.

**Answer**:

```tsx
// actions/avatar.ts
'use server';

const MAX_SIZE = 2 * 1024 * 1024; // 2MB
const ALLOWED = ['image/jpeg', 'image/png', 'image/webp'];

export async function uploadAvatar(formData: FormData) {
  const file = formData.get('avatar') as File | null;
  if (!file?.size) return { error: 'No file' };
  if (file.size > MAX_SIZE) return { error: 'File too large (max 2MB)' };
  if (!ALLOWED.includes(file.type)) return { error: 'Invalid type. Use JPEG, PNG, or WebP.' };

  const bytes = await file.arrayBuffer();
  const key = `avatars/${crypto.randomUUID()}-${file.name}`;
  await s3.put(key, Buffer.from(bytes), { contentType: file.type });
  await db.user.updateAvatar(userId, `https://cdn.example.com/${key}`);
  revalidatePath('/profile');
  return { success: true };
}
```

```tsx
<form action={uploadAvatar}>
  <input name="avatar" type="file" accept="image/jpeg,image/png,image/webp" required />
  <button type="submit">Upload</button>
</form>
```

---

## Q8. (Intermediate) Find the bug: Form works in dev but in production "use server" form action is not found.

**Wrong setup**:

```tsx
// actions.ts — no 'use server' at top
export async function submit(formData: FormData) {
  'use server';  // Too late: directive must be at top of file or at function level for that function
  await save(formData);
}
```

**Answer**:

**'use server'** must be at the **top** of the file (applying to all exports) or at the **start** of the function body for that specific function. Putting it in the middle or after other code can break. Also ensure the action is **exported** and the path is correct when deployed (e.g. barrel files and tree-shaking can sometimes drop server actions if not imported correctly).

**Fix**:

```tsx
// actions.ts
'use server';

export async function submit(formData: FormData) {
  await save(formData);
}
```

---

## Q9. (Intermediate) How do you use React 19's <Form> component with Server Actions and progressive enhancement?

**Scenario**: Form should work without JS (progressive enhancement) and with useActionState when JS loads.

**Answer**:

Use a **form** with **action** set to the Server Action. Without JS, the browser will POST the form to the same URL (or the action URL); Next.js handles that POST and runs the Server Action. With JS, React will intercept the submit and call the action without a full navigation. For **useActionState**, pass the action as the first argument and use the returned **formAction** on the form.

```tsx
'use client';
import { useActionState } from 'react';
import { signUp } from '@/actions/signup';

export function SignUpForm() {
  const [state, formAction] = useActionState(signUp, null);

  return (
    <form action={formAction}>
      {/* same as before */}
    </form>
  );
}
```

Progressive enhancement: the form’s **action** is the Server Action; with JS you get pending state and inline errors; without JS you still get a POST and a full-page redirect/response.

---

## Q10. (Intermediate) Where should you validate form input — client, server, or both? Why?

**Answer**:

- **Server**: **Always**. Never trust the client. Validate (e.g. Zod) in the Server Action and return field errors. Required for security and data integrity.
- **Client**: **Optional but recommended**. Validate on change or submit to give instant feedback and fewer round-trips. Use the same schema (e.g. Zod) so client and server rules match.

So: **both** for UX (client) and **security** (server). Server validation is non-negotiable.

---

## Q11. (Intermediate) How do you securely pass an API key from the server to an external service without exposing it to the client?

**Scenario**: Server Action calls a third-party API that requires an API key.

**Answer**:

- Store the key in an **env var** **without** the **NEXT_PUBLIC_** prefix (e.g. `THIRD_PARTY_API_KEY`). It will only be available on the server.
- In the Server Action (or a server-only module), read `process.env.THIRD_PARTY_API_KEY` and use it in the server-side request. Never send this key to the client or use it in Client Components.

```tsx
// actions/order.ts
'use server';

export async function createOrder(formData: FormData) {
  const key = process.env.THIRD_PARTY_API_KEY;
  if (!key) throw new Error('Missing API key');
  await fetch('https://api.thirdparty.com/order', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ ... }),
  });
}
```

---

## Q12. (Intermediate) Production scenario: After a breach, you need to rotate an API key that was in .env. What steps do you take in Next.js and deployment?

**Answer**:

1. Generate a new key in the third-party dashboard and disable or delete the old key.
2. Update the env var in your deployment (Vercel, AWS, etc.): set **THIRD_PARTY_API_KEY** to the new value. Use a secret manager (e.g. AWS Secrets Manager, Vercel Env) if available.
3. Redeploy or restart the app so the new value is loaded. If using serverless, new invocations will use the new env.
4. If the key was ever committed: remove it from git history (e.g. BFG, git filter-repo), rotate the key as above, and ensure .env is in .gitignore and never committed again.

---

## Q13. (Advanced) Implement a pattern where a Client Component form calls a Server Action and shows an optimistic update, then reverts if the action fails.

**Scenario**: "Like" button: count goes up immediately; if the server fails, revert and show error.

**Answer**:

Use **useOptimistic** for the count and call the Server Action. On success, **router.refresh()**. On failure, the optimistic state will revert (or you can set it back explicitly) and show a toast.

```tsx
'use client';
import { useOptimistic } from 'react';
import { useRouter } from 'next/navigation';
import { likePost } from '@/actions/like';

export function LikeButton({ postId, initialCount }: { postId: string; initialCount: number }) {
  const router = useRouter();
  const [optimisticCount, addOptimistic] = useOptimistic(initialCount, (s, _) => s + 1);

  async function handleClick() {
    addOptimistic(undefined);
    try {
      await likePost(postId);
      router.refresh();
    } catch (e) {
      // Revert: refresh to get server state back
      router.refresh();
      toast.error('Could not like');
    }
  }

  return <button onClick={handleClick}>Like ({optimisticCount})</button>;
}
```

---

## Q14. (Advanced) How do you prevent Server Actions from being called from other origins (e.g. a script on evil.com)?

**Answer**:

- **Same-origin**: Server Actions are POSTed to your origin; browsers send cookies only to same origin. So if the user is not on your site, the request either doesn’t include your session cookie (and your action should require auth and reject) or is a cross-origin request. Restrict CORS so your action URL doesn’t accept cross-origin POST from arbitrary sites.
- **Origin/Referer check**: In middleware or inside the action, read **Origin** or **Referer** and ensure they match your app’s origin (e.g. `https://myapp.com`). Reject the request if they’re missing or wrong. This blocks simple cross-origin form POSTs from other sites.
- **CSRF token**: For high-risk actions, use a token stored in a cookie (or session) and sent in the request body or header; verify they match. Next.js doesn’t add this by default; you add it if you need stronger CSRF protection.

---

## Q15. (Advanced) Find the bug: Sensitive data is visible in the client bundle.

**Wrong code**:

```tsx
// lib/config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  apiKey: process.env.API_SECRET_KEY,  // Server-only; but importing in a Client Component
};
```

```tsx
// components/ClientWidget.tsx
'use client';
import { config } from '@/lib/config';  // Pulls in API_SECRET_KEY into client bundle
export function ClientWidget() {
  return <div>{config.apiUrl}</div>;
}
```

**Answer**:

**process.env.API_SECRET_KEY** is undefined in the client (not inlined), but **importing** a module that references it can still pull that module (and any other code in it) into the client bundle. If that module or a dependency ever inlined the value (e.g. in a different build), or if you later add NEXT_PUBLIC_ by mistake, you risk leaking the secret. **Fix**: Keep server-only config in a **server-only** file and don’t import it from Client Components. Use **server-only** package so the build fails if a Client Component imports it.

```tsx
// lib/config.server.ts
import 'server-only';
export const serverConfig = {
  apiKey: process.env.API_SECRET_KEY,
};
```

Use **serverConfig** only in Server Components, Server Actions, or Route Handlers. In the client, use a separate **config.client.ts** that only has **NEXT_PUBLIC_** vars.

---

## Q16. (Advanced) How do you rate-limit Server Actions to prevent abuse (e.g. signup or contact form spam)?

**Scenario**: One IP should not submit the contact form more than 5 times per minute.

**Answer**:

- **Middleware**: Read IP (e.g. **x-forwarded-for** or **x-real-ip**), increment a counter in a store (e.g. Redis, Vercel KV) with a TTL of 1 minute, and if count > 5, return **NextResponse.redirect** or **NextResponse.json** with 429 before the request hits the Server Action.
- **Inside the Server Action**: Alternatively, check the same store (by IP or by user id if authenticated) at the start of the action and throw or return an error if over limit. Middleware is better for failing fast and not running the action at all.

```tsx
// In middleware or in the Server Action (pseudo)
const key = `ratelimit:contact:${ip}`;
const count = await redis.incr(key);
if (count === 1) await redis.expire(key, 60);
if (count > 5) return { error: 'Too many requests' };
```

---

## Q17. (Advanced) Next.js 15 vs 16: Any difference in how Server Actions or form security work?

**Answer**:

No fundamental change. Both use the same **'use server'** model, POST-based invocation, and same-origin behavior. Next.js 16 may improve reliability or tooling around Server Actions but the security model (no automatic CSRF token, same-origin + cookies, Origin check recommended) is the same. Keep validating on the server and not exposing secrets to the client.

---

## Q18. (Advanced) How do you ensure that a form that uses useActionState and redirect() in the Server Action doesn’t leave the UI in a stuck "pending" state if redirect throws?

**Scenario**: Server Action calls redirect() after success; useActionState might not get a return value.

**Answer**:

**redirect()** in Next.js throws a special error that is caught by the framework to perform the redirect. So the Server Action never "returns" normally when you call **redirect()**. The client may see the request complete (navigation happens) and the form will unblock when the new page loads. If the client stays on the same page (e.g. redirect failed or was caught), ensure you **return** something before calling **redirect()** so that in error paths you still return an object (e.g. `{ error: '...' }`) and the client can clear pending state. In the success path, the redirect will cause a new document load, so the previous form’s pending state is irrelevant. If you need to show a message before redirect, return `{ redirect: '/thank-you' }` and in the client check for that and call **router.push** instead of using **redirect()** in the action, so the action always returns and the client can clear pending.

---

## Q19. (Advanced) Design a secure "forgot password" flow using Server Actions: request form, token generation, reset form, and token validation. Avoid common pitfalls.

**Answer**:

- **Request form**: Server Action accepts email, looks up user, generates a **cryptographically random token**, stores hash and expiry (e.g. in DB), sends link with token in query (or path). Always return a generic "If an account exists, you’ll get an email" to avoid user enumeration.
- **Reset form**: Page reads token from URL; form submits new password + token. Server Action validates token (exists, not expired, hash matches), updates password, invalidates token. Use **POST** for the reset (not GET). Token in body or path; don’t rely on Referer for security.
- **Pitfalls**: Short or predictable tokens; no expiry; storing plain token instead of hash; revealing whether email exists; not invalidating token after use; allowing token reuse.

---

## Q20. (Advanced) How do you use the "server-only" package to prevent accidental import of server code in Client Components?

**Answer**:

Install **server-only** and add **import 'server-only'** at the top of any file that must only run on the server (e.g. DB client, code that uses secrets).

```tsx
// lib/db.ts
import 'server-only';
import { Pool } from 'pg';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export async function query(...) { return pool.query(...); }
```

If a Client Component (or any code in the client bundle) imports this file, the **build** will fail with an error that **server-only** cannot be imported from the client. That prevents accidentally bundling server code and secrets into the client.
