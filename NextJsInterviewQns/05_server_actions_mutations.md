# 5. Server Actions & Mutations

## Overview & Architecture

Server Actions are asynchronous functions that run on the server, invokable directly from Client and Server Components. They are the primary mechanism for mutations in the App Router, replacing API routes for most data mutation use cases. Introduced in Next.js 13.4 and stable since Next.js 14, they've become the backbone of form handling and data mutation in modern Next.js applications.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SERVER ACTIONS ARCHITECTURE                         │
│                                                                     │
│  Client (Browser)                    Server (Node.js/Edge)          │
│  ────────────────                    ─────────────────────          │
│                                                                     │
│  ┌──────────────┐    HTTP POST       ┌──────────────────┐          │
│  │ <form>       │ ──────────────►    │ Server Action    │          │
│  │  action={fn} │    (Encrypted      │ 'use server'     │          │
│  └──────────────┘     Action ID)     │                  │          │
│                                      │ ├─ Validate input│          │
│  ┌──────────────┐                    │ ├─ Auth check    │          │
│  │ Client       │    fetch() POST    │ ├─ DB mutation   │          │
│  │ Component    │ ──────────────►    │ ├─ Revalidate   │          │
│  │ onClick={fn} │    (Serialized     │ └─ Return result│          │
│  └──────────────┘     Args)          └──────────────────┘          │
│                                             │                       │
│         ◄───────────────────────────────────┘                       │
│         RSC Payload (updated UI) or                                 │
│         Serialized return value                                     │
│                                                                     │
│  KEY PROPERTIES:                                                    │
│  • Always run on the server (never exposed to client)               │
│  • Integrated with React's transition system                        │
│  • Support progressive enhancement (work without JS)                │
│  • Automatically handle CSRF protection                             │
│  • Can revalidate cache and redirect                                │
│  • Type-safe with TypeScript end-to-end                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Two Forms of Server Actions

```typescript
// FORM 1: Module-Level (Recommended for reuse)
// app/actions/user.ts
'use server';

export async function updateUser(formData: FormData) {
  // Entire file is server-only
}

export async function deleteUser(userId: string) {
  // Can export multiple actions from one file
}
```

```typescript
// FORM 2: Inline (Defined inside Server Components)
// app/settings/page.tsx
export default function SettingsPage() {
  async function handleSubmit(formData: FormData) {
    'use server';  // Marks this specific function as a Server Action
    // Only available to this component
  }

  return <form action={handleSubmit}>...</form>;
}
```

```
┌─────────────────────────────────────────────────────────────┐
│          SERVER ACTIONS vs API ROUTES                         │
├──────────────────────┬──────────────────┬───────────────────┤
│  Feature             │  Server Actions  │  API Routes       │
├──────────────────────┼──────────────────┼───────────────────┤
│  Invocation          │  Function call   │  HTTP request     │
│  Type safety         │  End-to-end TS   │  Manual typing    │
│  Progressive enh.    │  Yes (forms)     │  No               │
│  CSRF protection     │  Automatic       │  Manual           │
│  Revalidation        │  Built-in        │  Manual           │
│  File uploads        │  FormData        │  FormData/Stream  │
│  External clients    │  No              │  Yes              │
│  Webhooks            │  No              │  Yes              │
│  Rate limiting       │  Manual          │  Manual           │
│  Caching             │  No (mutations)  │  Yes (GET)        │
└──────────────────────┴──────────────────┴───────────────────┘
```

---

## Q1. What is the `"use server"` directive and how does it work at the module vs. function level? (Beginner)

**Scenario:** You're new to Server Actions and confused about where to place the `"use server"` directive. You've seen it at the top of files and inside functions and want to understand the difference.

```typescript
// Version A: Module-level directive
// app/actions.ts
'use server';

export async function createPost(formData: FormData) {
  // ...
}

export async function deletePost(postId: string) {
  // ...
}
```

```typescript
// Version B: Inline function-level directive
// app/page.tsx (Server Component)
export default function Page() {
  async function submitForm(formData: FormData) {
    'use server';
    // ...
  }

  return <form action={submitForm}>...</form>;
}
```

**Answer:**

The `"use server"` directive tells Next.js to create a server-side endpoint for the marked function(s). Here's how each form works:

**Module-level (`'use server'` at top of file):**
- Every `export`ed async function in the file becomes a Server Action.
- Non-exported functions remain private server-side helpers.
- These actions can be imported and used in any Client or Server Component.

**Function-level (`'use server'` inside function body):**
- Only that specific function becomes a Server Action.
- Can only be used inside Server Components (not in files marked `'use client'`).
- Useful for one-off actions that don't need reuse.

```
┌──────────────────────────────────────────────────────┐
│            HOW SERVER ACTIONS ARE COMPILED             │
│                                                       │
│  Source Code:                                         │
│  ┌──────────────────────────────────────────────┐    │
│  │ 'use server';                                │    │
│  │ export async function createPost(data) { ... }│   │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Next.js Compiler Output:                             │
│                                                       │
│  Server Bundle:                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │ // Full function body lives here              │    │
│  │ async function createPost(data) {             │    │
│  │   await db.post.create({ data });             │    │
│  │ }                                             │    │
│  │ // Registered as action ID: "abc123"          │    │
│  └──────────────────────────────────────────────┘    │
│                                                       │
│  Client Bundle:                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │ // Reference only — no server code leaked!    │    │
│  │ const createPost = createServerReference(     │    │
│  │   "abc123"                                    │    │
│  │ );                                            │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

**Important rules:**
1. Server Actions must be `async` functions.
2. Arguments and return values must be serializable (no functions, Dates become strings, etc.).
3. Server Actions are always POST requests under the hood.
4. You cannot define Server Actions in `'use client'` files — import them from a `'use server'` module instead.

```typescript
// ❌ WRONG — Can't define Server Actions in Client Components
'use client';

export function LoginForm() {
  async function login(formData: FormData) {
    'use server'; // ERROR: Can't use 'use server' in a 'use client' file
  }
  return <form action={login}>...</form>;
}

// ✅ CORRECT — Import from a 'use server' module
// app/actions/auth.ts
'use server';
export async function login(formData: FormData) { /* ... */ }

// app/components/LoginForm.tsx
'use client';
import { login } from '@/app/actions/auth';

export function LoginForm() {
  return <form action={login}>...</form>;
}
```

---

## Q2. How do you handle form submissions with Server Actions and display validation errors? (Beginner)

**Scenario:** You need to build a contact form that validates input on the server, displays field-level errors, and shows a success message after submission.

**Answer:**

```typescript
// app/actions/contact.ts
'use server';

import { z } from 'zod';

const contactSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email'),
  message: z.string().min(10, 'Message must be at least 10 characters'),
  subject: z.enum(['general', 'support', 'sales'], {
    errorMap: () => ({ message: 'Please select a subject' }),
  }),
});

export type ContactFormState = {
  success: boolean;
  message: string;
  errors?: {
    name?: string[];
    email?: string[];
    message?: string[];
    subject?: string[];
  };
};

export async function submitContactForm(
  prevState: ContactFormState,
  formData: FormData
): Promise<ContactFormState> {
  // Parse and validate
  const rawData = {
    name: formData.get('name'),
    email: formData.get('email'),
    message: formData.get('message'),
    subject: formData.get('subject'),
  };

  const result = contactSchema.safeParse(rawData);

  if (!result.success) {
    return {
      success: false,
      message: 'Please fix the errors below.',
      errors: result.error.flatten().fieldErrors,
    };
  }

  // Simulate sending email
  try {
    await sendEmail({
      to: 'support@example.com',
      subject: `[${result.data.subject}] Contact from ${result.data.name}`,
      body: result.data.message,
      replyTo: result.data.email,
    });

    return {
      success: true,
      message: 'Thank you! Your message has been sent.',
    };
  } catch {
    return {
      success: false,
      message: 'Failed to send message. Please try again.',
    };
  }
}

async function sendEmail(_params: {
  to: string;
  subject: string;
  body: string;
  replyTo: string;
}) {
  // Email sending logic
  await new Promise((resolve) => setTimeout(resolve, 500));
}
```

```typescript
// app/contact/page.tsx
'use client';

import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';
import { submitContactForm, type ContactFormState } from '@/app/actions/contact';

const initialState: ContactFormState = {
  success: false,
  message: '',
};

export default function ContactPage() {
  const [state, formAction] = useActionState(submitContactForm, initialState);

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Contact Us</h1>

      {state.success && (
        <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded mb-6">
          {state.message}
        </div>
      )}

      {!state.success && state.message && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded mb-6">
          {state.message}
        </div>
      )}

      <form action={formAction} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium mb-1">
            Name
          </label>
          <input
            id="name"
            name="name"
            type="text"
            className="w-full border rounded p-2"
            aria-describedby="name-error"
          />
          {state.errors?.name && (
            <p id="name-error" className="text-red-600 text-sm mt-1">
              {state.errors.name[0]}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium mb-1">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            className="w-full border rounded p-2"
            aria-describedby="email-error"
          />
          {state.errors?.email && (
            <p id="email-error" className="text-red-600 text-sm mt-1">
              {state.errors.email[0]}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="subject" className="block text-sm font-medium mb-1">
            Subject
          </label>
          <select
            id="subject"
            name="subject"
            className="w-full border rounded p-2"
            aria-describedby="subject-error"
          >
            <option value="">Select a subject</option>
            <option value="general">General Inquiry</option>
            <option value="support">Technical Support</option>
            <option value="sales">Sales</option>
          </select>
          {state.errors?.subject && (
            <p id="subject-error" className="text-red-600 text-sm mt-1">
              {state.errors.subject[0]}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="message" className="block text-sm font-medium mb-1">
            Message
          </label>
          <textarea
            id="message"
            name="message"
            rows={4}
            className="w-full border rounded p-2"
            aria-describedby="message-error"
          />
          {state.errors?.message && (
            <p id="message-error" className="text-red-600 text-sm mt-1">
              {state.errors.message[0]}
            </p>
          )}
        </div>

        <SubmitButton />
      </form>
    </div>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {pending ? 'Sending...' : 'Send Message'}
    </button>
  );
}
```

```
┌──────────────────────────────────────────────────────┐
│       FORM SUBMISSION FLOW WITH useActionState        │
│                                                       │
│  1. User fills form, clicks Submit                    │
│  2. useFormStatus → { pending: true }                 │
│  3. FormData serialized → POST to Server Action       │
│  4. Server validates with Zod                         │
│     ├── Invalid → Returns { errors: {...} }           │
│     └── Valid → Processes, returns { success: true }  │
│  5. useActionState receives new state                 │
│  6. Component re-renders with state                   │
│  7. useFormStatus → { pending: false }                │
│                                                       │
│  PROGRESSIVE ENHANCEMENT:                             │
│  Without JavaScript, the form still works!            │
│  • Form submits as traditional POST                   │
│  • Server processes and returns full page             │
│  • No useFormStatus (button stays enabled)            │
└──────────────────────────────────────────────────────┘
```

---

## Q3. What is `useFormStatus` and how does it differ from `useActionState`? (Beginner)

**Scenario:** You want to show a loading spinner on your submit button and disable form inputs while a Server Action is processing.

**Answer:**

**`useFormStatus`** (from `react-dom`) gives you the pending state of the parent `<form>`. It must be used in a component that is a **child** of the `<form>` element.

**`useActionState`** (from `react`, renamed from `useFormState` in React 19) manages the form action's return value (state) and provides a wrapped action function.

```
┌──────────────────────────────────────────────────────────────┐
│          useFormStatus vs useActionState                       │
├────────────────────┬─────────────────────┬───────────────────┤
│                    │  useFormStatus      │  useActionState   │
├────────────────────┼─────────────────────┼───────────────────┤
│  Import from       │  react-dom          │  react            │
│  Returns           │  { pending, data,   │  [state, action,  │
│                    │    method, action }  │   isPending]      │
│  Purpose           │  UI feedback during │  Manage action    │
│                    │  submission         │  return values    │
│  Must be child of  │  <form> (required)  │  No requirement   │
│  Handles errors    │  No                 │  Yes (via state)  │
│  Progressive enh.  │  No (needs JS)      │  Yes              │
└────────────────────┴─────────────────────┴───────────────────┘
```

```typescript
// useFormStatus — must be a CHILD component of <form>
'use client';

import { useFormStatus } from 'react-dom';

// ❌ WRONG — useFormStatus in the same component as <form>
function BadForm() {
  const { pending } = useFormStatus(); // Will NEVER show pending!
  return (
    <form action={someAction}>
      <button disabled={pending}>Submit</button>
    </form>
  );
}

// ✅ CORRECT — useFormStatus in a child component
function SubmitButton() {
  const { pending, data, method, action } = useFormStatus();

  return (
    <button type="submit" disabled={pending}>
      {pending ? (
        <span className="flex items-center gap-2">
          <Spinner className="animate-spin h-4 w-4" />
          Processing...
        </span>
      ) : (
        'Submit'
      )}
    </button>
  );
}

function FormFields() {
  const { pending } = useFormStatus();

  return (
    <fieldset disabled={pending} className="space-y-4">
      <input name="name" className="border p-2 rounded w-full" />
      <input name="email" type="email" className="border p-2 rounded w-full" />
    </fieldset>
  );
}

function GoodForm() {
  return (
    <form action={someAction}>
      <FormFields />
      <SubmitButton />
    </form>
  );
}
```

```typescript
// useActionState — manages action state and pending status
'use client';

import { useActionState } from 'react';

type FormState = {
  message: string;
  success: boolean;
};

function RegistrationForm() {
  const [state, formAction, isPending] = useActionState(
    registerUser,
    { message: '', success: false } // Initial state
  );

  // isPending — same as useFormStatus's pending, but available here
  // state — the return value of the Server Action
  // formAction — the wrapped action to pass to <form>

  return (
    <form action={formAction}>
      <input name="email" disabled={isPending} />

      {/* Display server-returned state */}
      {state.message && (
        <p className={state.success ? 'text-green-600' : 'text-red-600'}>
          {state.message}
        </p>
      )}

      <button disabled={isPending}>
        {isPending ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
}
```

---

## Q4. How does progressive enhancement work with Server Actions and forms? (Beginner)

**Scenario:** Your team requires that critical forms (login, checkout) work even if JavaScript fails to load. How do Server Actions enable this?

**Answer:**

Progressive enhancement means the form works as a basic HTML form submission without JavaScript, and gets enhanced with JavaScript when available.

```typescript
// app/actions/auth.ts
'use server';

import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';

export async function loginAction(
  prevState: { error: string },
  formData: FormData
) {
  const email = formData.get('email') as string;
  const password = formData.get('password') as string;

  const result = await authenticateUser(email, password);

  if (!result.success) {
    return { error: 'Invalid email or password' };
  }

  // Set session cookie
  const cookieStore = await cookies();
  cookieStore.set('session', result.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 1 week
  });

  redirect('/dashboard');
}

async function authenticateUser(_email: string, _password: string) {
  // Auth logic
  return { success: true, token: 'xxx' };
}
```

```typescript
// app/login/page.tsx
// This is a SERVER component — it renders HTML on the server
import { loginAction } from '@/app/actions/auth';
import { LoginForm } from './login-form';

export default function LoginPage() {
  return (
    <div className="max-w-sm mx-auto mt-20">
      <h1 className="text-2xl font-bold mb-6">Sign In</h1>
      <LoginForm action={loginAction} />
    </div>
  );
}
```

```typescript
// app/login/login-form.tsx
'use client';

import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';

interface LoginFormProps {
  action: (prevState: { error: string }, formData: FormData) => Promise<{ error: string }>;
}

export function LoginForm({ action }: LoginFormProps) {
  const [state, formAction] = useActionState(action, { error: '' });

  return (
    <form action={formAction} className="space-y-4">
      {state.error && (
        <div className="bg-red-50 text-red-700 p-3 rounded text-sm">
          {state.error}
        </div>
      )}

      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          className="w-full border p-2 rounded mt-1"
          autoComplete="email"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          required
          className="w-full border p-2 rounded mt-1"
          autoComplete="current-password"
        />
      </div>

      <SubmitButton />
    </form>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="w-full bg-black text-white py-2 rounded hover:bg-gray-800 disabled:opacity-60"
    >
      {pending ? 'Signing in...' : 'Sign In'}
    </button>
  );
}
```

```
┌──────────────────────────────────────────────────────────────┐
│         PROGRESSIVE ENHANCEMENT BEHAVIOR                      │
│                                                               │
│  WITHOUT JAVASCRIPT:                                          │
│  ──────────────────                                           │
│  1. User fills form, clicks "Sign In"                         │
│  2. Browser sends native HTML form POST to the page URL       │
│  3. Next.js server receives POST, runs loginAction            │
│  4. Action calls redirect('/dashboard')                       │
│  5. Server sends 303 redirect → browser navigates             │
│  6. Full page reload to /dashboard                            │
│                                                               │
│  Note: useFormStatus won't work (needs JS), so button         │
│  stays as "Sign In" the whole time. The form still works!     │
│                                                               │
│  WITH JAVASCRIPT:                                             │
│  ────────────────                                             │
│  1. User fills form, clicks "Sign In"                         │
│  2. React intercepts submission (client-side)                 │
│  3. useFormStatus → { pending: true } → "Signing in..."       │
│  4. fetch() POST to Server Action endpoint                    │
│  5. Action runs server-side, calls redirect('/dashboard')     │
│  6. Client-side navigation (no full reload)                   │
│  7. Only changed parts re-render (RSC streaming)              │
│                                                               │
│  SAME SERVER ACTION CODE HANDLES BOTH CASES!                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Q5. How do you call a Server Action from a Client Component outside of a form? (Beginner)

**Scenario:** You have a "like" button, a "delete" icon, and a toggle switch — none of which are inside forms. You need to call Server Actions from button click handlers.

**Answer:**

```typescript
// app/actions/social.ts
'use server';

import { revalidatePath } from 'next/cache';
import { auth } from '@/lib/auth';

export async function toggleLike(postId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const existing = await db.like.findUnique({
    where: {
      userId_postId: { userId: session.user.id, postId },
    },
  });

  if (existing) {
    await db.like.delete({ where: { id: existing.id } });
  } else {
    await db.like.create({
      data: { userId: session.user.id, postId },
    });
  }

  revalidatePath('/feed');

  return { liked: !existing, likeCount: await db.like.count({ where: { postId } }) };
}

export async function deletePost(postId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const post = await db.post.findUnique({ where: { id: postId } });
  if (post?.authorId !== session.user.id) throw new Error('Forbidden');

  await db.post.delete({ where: { id: postId } });
  revalidatePath('/feed');

  return { success: true };
}

export async function toggleNotifications(enabled: boolean) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  await db.user.update({
    where: { id: session.user.id },
    data: { notificationsEnabled: enabled },
  });

  revalidatePath('/settings');

  return { notificationsEnabled: enabled };
}
```

```typescript
// components/LikeButton.tsx
'use client';

import { useTransition, useState } from 'react';
import { toggleLike } from '@/app/actions/social';

interface LikeButtonProps {
  postId: string;
  initialLiked: boolean;
  initialCount: number;
}

export function LikeButton({ postId, initialLiked, initialCount }: LikeButtonProps) {
  const [isPending, startTransition] = useTransition();
  const [liked, setLiked] = useState(initialLiked);
  const [count, setCount] = useState(initialCount);

  function handleClick() {
    // Optimistic update
    setLiked(!liked);
    setCount(liked ? count - 1 : count + 1);

    startTransition(async () => {
      try {
        const result = await toggleLike(postId);
        setLiked(result.liked);
        setCount(result.likeCount);
      } catch {
        // Revert on error
        setLiked(liked);
        setCount(count);
      }
    });
  }

  return (
    <button
      onClick={handleClick}
      disabled={isPending}
      className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm transition-colors ${
        liked
          ? 'bg-red-100 text-red-600'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      <span>{liked ? '♥' : '♡'}</span>
      <span>{count}</span>
    </button>
  );
}
```

```typescript
// components/DeleteButton.tsx
'use client';

import { useTransition } from 'react';
import { deletePost } from '@/app/actions/social';

export function DeleteButton({ postId }: { postId: string }) {
  const [isPending, startTransition] = useTransition();

  function handleDelete() {
    if (!confirm('Are you sure you want to delete this post?')) return;

    startTransition(async () => {
      await deletePost(postId);
    });
  }

  return (
    <button
      onClick={handleDelete}
      disabled={isPending}
      className="text-red-600 hover:text-red-800 disabled:opacity-50"
    >
      {isPending ? 'Deleting...' : 'Delete'}
    </button>
  );
}
```

```typescript
// components/NotificationToggle.tsx
'use client';

import { useTransition, useOptimistic } from 'react';
import { toggleNotifications } from '@/app/actions/social';

export function NotificationToggle({ enabled }: { enabled: boolean }) {
  const [isPending, startTransition] = useTransition();
  const [optimisticEnabled, setOptimisticEnabled] = useOptimistic(enabled);

  function handleToggle() {
    const newValue = !optimisticEnabled;
    setOptimisticEnabled(newValue);

    startTransition(async () => {
      await toggleNotifications(newValue);
    });
  }

  return (
    <button
      role="switch"
      aria-checked={optimisticEnabled}
      onClick={handleToggle}
      disabled={isPending}
      className={`relative inline-flex h-6 w-11 rounded-full transition-colors ${
        optimisticEnabled ? 'bg-blue-600' : 'bg-gray-300'
      }`}
    >
      <span
        className={`inline-block h-5 w-5 rounded-full bg-white shadow transform transition-transform mt-0.5 ${
          optimisticEnabled ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'
        }`}
      />
    </button>
  );
}
```

**Key pattern:** When calling Server Actions outside forms, use `useTransition` to wrap the call. This keeps the UI responsive and gives you an `isPending` state for loading indicators.

---

## Q6. How do you implement optimistic updates with `useOptimistic` for a todo list? (Intermediate)

**Scenario:** You have a todo list where adding, toggling, and deleting items should feel instant, even though the actual mutations happen on the server. Network latency is 200-500ms.

**Answer:**

```typescript
// app/actions/todos.ts
'use server';

import { revalidatePath } from 'next/cache';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { z } from 'zod';

const todoSchema = z.object({
  title: z.string().min(1).max(200),
});

export async function addTodo(prevState: unknown, formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const result = todoSchema.safeParse({ title: formData.get('title') });
  if (!result.success) {
    return { error: 'Invalid todo title' };
  }

  await db.todo.create({
    data: {
      title: result.data.title,
      userId: session.user.id,
      completed: false,
    },
  });

  revalidatePath('/todos');
  return { error: null };
}

export async function toggleTodo(todoId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const todo = await db.todo.findUnique({ where: { id: todoId } });
  if (!todo || todo.userId !== session.user.id) throw new Error('Not found');

  await db.todo.update({
    where: { id: todoId },
    data: { completed: !todo.completed },
  });

  revalidatePath('/todos');
}

export async function deleteTodo(todoId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  await db.todo.delete({
    where: { id: todoId, userId: session.user.id },
  });

  revalidatePath('/todos');
}
```

```typescript
// app/todos/page.tsx
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { TodoList } from './todo-list';

export default async function TodosPage() {
  const session = await auth();
  const todos = await db.todo.findMany({
    where: { userId: session!.user.id },
    orderBy: { createdAt: 'desc' },
  });

  return (
    <div className="max-w-lg mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">My Todos</h1>
      <TodoList initialTodos={todos} />
    </div>
  );
}
```

```typescript
// app/todos/todo-list.tsx
'use client';

import { useOptimistic, useRef } from 'react';
import { useActionState } from 'react';
import { addTodo, toggleTodo, deleteTodo } from '@/app/actions/todos';

interface Todo {
  id: string;
  title: string;
  completed: boolean;
  createdAt: Date;
}

type OptimisticAction =
  | { type: 'add'; todo: Todo }
  | { type: 'toggle'; todoId: string }
  | { type: 'delete'; todoId: string };

export function TodoList({ initialTodos }: { initialTodos: Todo[] }) {
  const formRef = useRef<HTMLFormElement>(null);

  // Optimistic state management
  const [optimisticTodos, addOptimisticUpdate] = useOptimistic(
    initialTodos,
    (currentTodos: Todo[], action: OptimisticAction) => {
      switch (action.type) {
        case 'add':
          return [action.todo, ...currentTodos];
        case 'toggle':
          return currentTodos.map((t) =>
            t.id === action.todoId ? { ...t, completed: !t.completed } : t
          );
        case 'delete':
          return currentTodos.filter((t) => t.id !== action.todoId);
        default:
          return currentTodos;
      }
    }
  );

  // Add todo with optimistic update
  const [_addState, addAction] = useActionState(
    async (prevState: unknown, formData: FormData) => {
      const title = formData.get('title') as string;

      // Optimistic: add immediately
      addOptimisticUpdate({
        type: 'add',
        todo: {
          id: `temp-${Date.now()}`, // Temporary ID
          title,
          completed: false,
          createdAt: new Date(),
        },
      });

      formRef.current?.reset();

      // Server mutation
      return addTodo(prevState, formData);
    },
    null
  );

  async function handleToggle(todoId: string) {
    addOptimisticUpdate({ type: 'toggle', todoId });
    await toggleTodo(todoId);
  }

  async function handleDelete(todoId: string) {
    addOptimisticUpdate({ type: 'delete', todoId });
    await deleteTodo(todoId);
  }

  const activeTodos = optimisticTodos.filter((t) => !t.completed);
  const completedTodos = optimisticTodos.filter((t) => t.completed);

  return (
    <div>
      {/* Add Todo Form */}
      <form ref={formRef} action={addAction} className="flex gap-2 mb-6">
        <input
          name="title"
          placeholder="What needs to be done?"
          required
          className="flex-1 border rounded px-3 py-2"
          autoComplete="off"
        />
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Add
        </button>
      </form>

      {/* Active Todos */}
      <ul className="space-y-2 mb-6">
        {activeTodos.map((todo) => (
          <TodoItem
            key={todo.id}
            todo={todo}
            onToggle={handleToggle}
            onDelete={handleDelete}
          />
        ))}
      </ul>

      {/* Completed Todos */}
      {completedTodos.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-500 mb-2">
            Completed ({completedTodos.length})
          </h2>
          <ul className="space-y-2">
            {completedTodos.map((todo) => (
              <TodoItem
                key={todo.id}
                todo={todo}
                onToggle={handleToggle}
                onDelete={handleDelete}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TodoItem({
  todo,
  onToggle,
  onDelete,
}: {
  todo: Todo;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const isTemp = todo.id.startsWith('temp-');

  return (
    <li
      className={`flex items-center gap-3 p-3 rounded border ${
        isTemp ? 'opacity-60' : ''
      } ${todo.completed ? 'bg-gray-50' : 'bg-white'}`}
    >
      <button
        onClick={() => onToggle(todo.id)}
        className={`h-5 w-5 rounded-full border-2 flex items-center justify-center ${
          todo.completed ? 'bg-green-500 border-green-500' : 'border-gray-300'
        }`}
      >
        {todo.completed && <span className="text-white text-xs">✓</span>}
      </button>

      <span
        className={`flex-1 ${
          todo.completed ? 'line-through text-gray-400' : ''
        }`}
      >
        {todo.title}
      </span>

      {!isTemp && (
        <button
          onClick={() => onDelete(todo.id)}
          className="text-gray-400 hover:text-red-500"
        >
          ×
        </button>
      )}
    </li>
  );
}
```

```
┌──────────────────────────────────────────────────────────────┐
│           OPTIMISTIC UPDATE FLOW                              │
│                                                               │
│  User clicks "Add Todo: Buy milk"                             │
│  ─────────────────────────────────                            │
│  T+0ms:   useOptimistic adds { id: 'temp-123', ... }         │
│           UI instantly shows "Buy milk" (greyed out)          │
│           Form resets                                         │
│                                                               │
│  T+0ms:   Server Action addTodo() called                      │
│           ┌──────────────────────────────────┐                │
│           │ Server: validate → insert to DB   │               │
│           │         → revalidatePath('/todos')│               │
│           └──────────────────────────────────┘                │
│                                                               │
│  T+300ms: Server responds with revalidated page               │
│           React reconciles: temp-123 replaced with real DB ID │
│           UI shows "Buy milk" at full opacity                 │
│                                                               │
│  IF SERVER FAILS:                                             │
│  T+300ms: initialTodos hasn't changed → optimistic state      │
│           auto-reverts to last known good state               │
│           "Buy milk" disappears from list                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Q7. How do you handle file uploads via Server Actions with progress tracking? (Intermediate)

**Scenario:** Users need to upload profile pictures (max 5MB) and documents (max 50MB). You need upload validation, progress indication, and storage to S3-compatible object storage.

**Answer:**

```typescript
// app/actions/upload.ts
'use server';

import { auth } from '@/lib/auth';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import crypto from 'crypto';

const s3 = new S3Client({
  region: process.env.AWS_REGION!,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const ALLOWED_DOC_TYPES = ['application/pdf', 'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB
const MAX_DOC_SIZE = 50 * 1024 * 1024; // 50MB

export type UploadResult = {
  success: boolean;
  url?: string;
  error?: string;
  fileName?: string;
  fileSize?: number;
};

export async function uploadProfilePicture(
  prevState: UploadResult,
  formData: FormData
): Promise<UploadResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, error: 'You must be signed in to upload.' };
  }

  const file = formData.get('avatar') as File;

  if (!file || file.size === 0) {
    return { success: false, error: 'No file selected.' };
  }

  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return {
      success: false,
      error: `Invalid file type. Allowed: ${ALLOWED_IMAGE_TYPES.join(', ')}`,
    };
  }

  if (file.size > MAX_IMAGE_SIZE) {
    return {
      success: false,
      error: `File too large. Maximum size is ${MAX_IMAGE_SIZE / 1024 / 1024}MB.`,
    };
  }

  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    const hash = crypto.createHash('sha256').update(buffer).digest('hex').slice(0, 16);
    const ext = file.name.split('.').pop();
    const key = `avatars/${session.user.id}/${hash}.${ext}`;

    await s3.send(
      new PutObjectCommand({
        Bucket: process.env.S3_BUCKET!,
        Key: key,
        Body: buffer,
        ContentType: file.type,
        CacheControl: 'public, max-age=31536000, immutable',
      })
    );

    const url = `${process.env.CDN_URL}/${key}`;

    // Update user profile in DB
    await db.user.update({
      where: { id: session.user.id },
      data: { avatarUrl: url },
    });

    revalidatePath('/settings');
    revalidatePath('/', 'layout'); // Avatar shows in navbar

    return { success: true, url, fileName: file.name, fileSize: file.size };
  } catch (error) {
    console.error('Upload failed:', error);
    return { success: false, error: 'Upload failed. Please try again.' };
  }
}

export async function uploadDocument(
  prevState: UploadResult,
  formData: FormData
): Promise<UploadResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, error: 'Unauthorized' };
  }

  const file = formData.get('document') as File;

  if (!file || file.size === 0) {
    return { success: false, error: 'No file selected.' };
  }

  if (!ALLOWED_DOC_TYPES.includes(file.type)) {
    return { success: false, error: 'Invalid file type. Only PDF and Word documents allowed.' };
  }

  if (file.size > MAX_DOC_SIZE) {
    return { success: false, error: 'File too large. Maximum 50MB.' };
  }

  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    const hash = crypto.createHash('sha256').update(buffer).digest('hex').slice(0, 16);
    const key = `documents/${session.user.id}/${hash}-${file.name}`;

    await s3.send(
      new PutObjectCommand({
        Bucket: process.env.S3_BUCKET!,
        Key: key,
        Body: buffer,
        ContentType: file.type,
        ContentDisposition: `attachment; filename="${file.name}"`,
      })
    );

    const url = `${process.env.CDN_URL}/${key}`;

    await db.document.create({
      data: {
        userId: session.user.id,
        name: file.name,
        url,
        size: file.size,
        mimeType: file.type,
      },
    });

    revalidatePath('/documents');

    return { success: true, url, fileName: file.name, fileSize: file.size };
  } catch (error) {
    console.error('Document upload failed:', error);
    return { success: false, error: 'Upload failed. Please try again.' };
  }
}
```

```typescript
// components/AvatarUpload.tsx
'use client';

import { useActionState, useRef, useState } from 'react';
import { useFormStatus } from 'react-dom';
import { uploadProfilePicture, type UploadResult } from '@/app/actions/upload';

export function AvatarUpload({ currentAvatarUrl }: { currentAvatarUrl?: string }) {
  const [preview, setPreview] = useState<string | null>(currentAvatarUrl ?? null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [state, formAction] = useActionState(uploadProfilePicture, {
    success: false,
  } as UploadResult);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  }

  return (
    <form action={formAction} className="space-y-4">
      <div className="flex items-center gap-4">
        <div className="h-20 w-20 rounded-full overflow-hidden bg-gray-200">
          {preview ? (
            <img src={preview} alt="Avatar" className="h-full w-full object-cover" />
          ) : (
            <div className="h-full w-full flex items-center justify-center text-gray-400">
              No photo
            </div>
          )}
        </div>

        <div>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Choose photo
          </button>
          <p className="text-xs text-gray-500 mt-1">
            JPG, PNG, or WebP. Max 5MB.
          </p>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        name="avatar"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />

      {state.error && (
        <p className="text-sm text-red-600">{state.error}</p>
      )}

      {state.success && (
        <p className="text-sm text-green-600">Avatar updated successfully!</p>
      )}

      <UploadButton />
    </form>
  );
}

function UploadButton() {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="bg-blue-600 text-white px-4 py-2 rounded text-sm disabled:opacity-50"
    >
      {pending ? 'Uploading...' : 'Upload'}
    </button>
  );
}
```

---

## Q8. How do you secure Server Actions with authentication, authorization, and input validation? (Intermediate)

**Scenario:** Your app has Server Actions that perform sensitive operations — updating user roles, deleting resources, processing payments. You need to ensure these actions are protected against unauthorized access and malicious input.

**Answer:**

```typescript
// lib/auth/action-guard.ts
import { auth } from '@/lib/auth';
import { headers } from 'next/headers';

type Role = 'user' | 'admin' | 'superadmin';

interface ActionContext {
  userId: string;
  email: string;
  role: Role;
  sessionId: string;
}

// Reusable auth guard for Server Actions
export async function requireAuth(): Promise<ActionContext> {
  const session = await auth();

  if (!session?.user) {
    throw new Error('UNAUTHORIZED');
  }

  return {
    userId: session.user.id,
    email: session.user.email!,
    role: session.user.role as Role,
    sessionId: session.sessionId,
  };
}

export async function requireRole(minimumRole: Role): Promise<ActionContext> {
  const context = await requireAuth();

  const roleHierarchy: Record<Role, number> = {
    user: 0,
    admin: 1,
    superadmin: 2,
  };

  if (roleHierarchy[context.role] < roleHierarchy[minimumRole]) {
    throw new Error('FORBIDDEN');
  }

  return context;
}

// Rate limiting for Server Actions
const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

export async function rateLimit(
  key: string,
  maxRequests: number = 10,
  windowMs: number = 60000
): Promise<void> {
  const headersList = await headers();
  const ip = headersList.get('x-forwarded-for') || 'unknown';
  const rateLimitKey = `${key}:${ip}`;

  const now = Date.now();
  const entry = rateLimitMap.get(rateLimitKey);

  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(rateLimitKey, { count: 1, resetAt: now + windowMs });
    return;
  }

  if (entry.count >= maxRequests) {
    throw new Error('RATE_LIMITED');
  }

  entry.count++;
}
```

```typescript
// lib/actions/safe-action.ts
// Type-safe Server Action wrapper with built-in security
import { z } from 'zod';
import { requireAuth, requireRole, rateLimit } from '@/lib/auth/action-guard';

type Role = 'user' | 'admin' | 'superadmin';

interface ActionConfig<TInput extends z.ZodType, TOutput> {
  input: TInput;
  role?: Role;
  rateLimit?: { maxRequests: number; windowMs: number };
  handler: (params: {
    input: z.infer<TInput>;
    ctx: { userId: string; email: string; role: string };
  }) => Promise<TOutput>;
}

type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; code: string };

export function createSafeAction<TInput extends z.ZodType, TOutput>(
  config: ActionConfig<TInput, TOutput>
) {
  return async (rawInput: z.infer<TInput>): Promise<ActionResult<TOutput>> => {
    try {
      // 1. Authentication
      const ctx = config.role
        ? await requireRole(config.role)
        : await requireAuth();

      // 2. Rate limiting
      if (config.rateLimit) {
        await rateLimit(
          `action:${config.handler.name}`,
          config.rateLimit.maxRequests,
          config.rateLimit.windowMs
        );
      }

      // 3. Input validation
      const parsed = config.input.safeParse(rawInput);
      if (!parsed.success) {
        return {
          success: false,
          error: parsed.error.errors.map((e) => e.message).join(', '),
          code: 'VALIDATION_ERROR',
        };
      }

      // 4. Execute handler
      const data = await config.handler({
        input: parsed.data,
        ctx,
      });

      return { success: true, data };
    } catch (error) {
      if (error instanceof Error) {
        switch (error.message) {
          case 'UNAUTHORIZED':
            return { success: false, error: 'Please sign in.', code: 'UNAUTHORIZED' };
          case 'FORBIDDEN':
            return { success: false, error: 'Permission denied.', code: 'FORBIDDEN' };
          case 'RATE_LIMITED':
            return { success: false, error: 'Too many requests. Try again later.', code: 'RATE_LIMITED' };
          default:
            console.error('Action error:', error);
            return { success: false, error: 'Something went wrong.', code: 'INTERNAL_ERROR' };
        }
      }
      return { success: false, error: 'Unknown error.', code: 'UNKNOWN' };
    }
  };
}
```

```typescript
// app/actions/admin.ts
'use server';

import { z } from 'zod';
import { createSafeAction } from '@/lib/actions/safe-action';
import { revalidatePath } from 'next/cache';
import { db } from '@/lib/db';

// Type-safe, authenticated, rate-limited, validated Server Action
export const updateUserRole = createSafeAction({
  input: z.object({
    userId: z.string().uuid('Invalid user ID'),
    newRole: z.enum(['user', 'admin'], {
      errorMap: () => ({ message: 'Role must be "user" or "admin"' }),
    }),
  }),
  role: 'superadmin', // Only superadmins can change roles
  rateLimit: { maxRequests: 5, windowMs: 60000 },
  handler: async ({ input, ctx }) => {
    // Prevent self-demotion
    if (input.userId === ctx.userId) {
      throw new Error('Cannot change your own role');
    }

    const user = await db.user.update({
      where: { id: input.userId },
      data: { role: input.newRole },
    });

    // Audit log
    await db.auditLog.create({
      data: {
        action: 'UPDATE_USER_ROLE',
        performedBy: ctx.userId,
        targetUserId: input.userId,
        details: JSON.stringify({ newRole: input.newRole }),
      },
    });

    revalidatePath('/admin/users');

    return { userId: user.id, newRole: user.role };
  },
});

export const deleteResource = createSafeAction({
  input: z.object({
    resourceId: z.string().uuid(),
    resourceType: z.enum(['post', 'comment', 'file']),
    reason: z.string().min(10, 'Please provide a reason (min 10 chars)'),
  }),
  role: 'admin',
  rateLimit: { maxRequests: 20, windowMs: 60000 },
  handler: async ({ input, ctx }) => {
    const { resourceId, resourceType, reason } = input;

    // Soft delete with audit trail
    switch (resourceType) {
      case 'post':
        await db.post.update({
          where: { id: resourceId },
          data: { deletedAt: new Date(), deletedBy: ctx.userId, deleteReason: reason },
        });
        revalidatePath('/feed');
        break;
      case 'comment':
        await db.comment.update({
          where: { id: resourceId },
          data: { deletedAt: new Date(), deletedBy: ctx.userId },
        });
        break;
      case 'file':
        await db.file.update({
          where: { id: resourceId },
          data: { deletedAt: new Date(), deletedBy: ctx.userId },
        });
        break;
    }

    return { deleted: true, resourceType, resourceId };
  },
});
```

```
┌──────────────────────────────────────────────────────────────┐
│          SERVER ACTION SECURITY LAYERS                        │
│                                                               │
│  Client Request                                               │
│       │                                                       │
│       ▼                                                       │
│  ┌─────────────────┐                                          │
│  │ 1. CSRF Check   │ ← Automatic in Next.js                  │
│  │    (Origin      │    Checks Origin header matches host     │
│  │     header)     │                                          │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ 2. Rate Limit   │ ← Per IP + action key                   │
│  │    (IP-based)   │    Prevents abuse                        │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ 3. Auth Check   │ ← Verify session exists                 │
│  │    (Session)    │    Extract user context                  │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ 4. Role Check   │ ← Verify sufficient permissions         │
│  │    (RBAC)       │    Hierarchy: user < admin < superadmin  │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ 5. Validation   │ ← Zod schema validation                 │
│  │    (Zod)        │    Type-safe, detailed errors            │
│  └────────┬────────┘                                          │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ 6. Execute      │ ← Business logic runs                   │
│  │    Handler      │    Audit logging                         │
│  └─────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Q9. How do you implement Server Actions with proper error handling and error boundaries? (Intermediate)

**Scenario:** Your Server Actions can fail for various reasons — network errors, database timeouts, validation failures, business rule violations. You need a robust error handling strategy that provides good UX.

**Answer:**

```typescript
// lib/errors.ts
// Custom error classes for different failure types

export class ActionError extends Error {
  code: string;
  statusCode: number;

  constructor(message: string, code: string, statusCode: number = 400) {
    super(message);
    this.name = 'ActionError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

export class ValidationError extends ActionError {
  fieldErrors: Record<string, string[]>;

  constructor(fieldErrors: Record<string, string[]>) {
    super('Validation failed', 'VALIDATION_ERROR', 400);
    this.name = 'ValidationError';
    this.fieldErrors = fieldErrors;
  }
}

export class NotFoundError extends ActionError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends ActionError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409);
    this.name = 'ConflictError';
  }
}
```

```typescript
// lib/actions/error-handler.ts
import { ActionError, ValidationError } from '@/lib/errors';

export type ActionResponse<T = void> =
  | { success: true; data: T }
  | {
      success: false;
      error: {
        message: string;
        code: string;
        fieldErrors?: Record<string, string[]>;
      };
    };

export function handleActionError(error: unknown): ActionResponse<never> {
  // Known application errors
  if (error instanceof ValidationError) {
    return {
      success: false,
      error: {
        message: error.message,
        code: error.code,
        fieldErrors: error.fieldErrors,
      },
    };
  }

  if (error instanceof ActionError) {
    return {
      success: false,
      error: {
        message: error.message,
        code: error.code,
      },
    };
  }

  // Database errors
  if (error instanceof Error && error.message.includes('Unique constraint')) {
    return {
      success: false,
      error: {
        message: 'This record already exists.',
        code: 'DUPLICATE',
      },
    };
  }

  // Unknown errors — don't leak internal details
  console.error('[Server Action Error]', error);

  return {
    success: false,
    error: {
      message: 'An unexpected error occurred. Please try again.',
      code: 'INTERNAL_ERROR',
    },
  };
}
```

```typescript
// app/actions/workspace.ts
'use server';

import { z } from 'zod';
import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { NotFoundError, ConflictError, ValidationError } from '@/lib/errors';
import { handleActionError, type ActionResponse } from '@/lib/actions/error-handler';

const createWorkspaceSchema = z.object({
  name: z.string().min(2).max(50),
  slug: z.string().min(2).max(30).regex(/^[a-z0-9-]+$/, 'Only lowercase letters, numbers, and hyphens'),
  plan: z.enum(['free', 'pro', 'enterprise']),
});

export async function createWorkspace(
  prevState: ActionResponse<{ id: string; slug: string }>,
  formData: FormData
): Promise<ActionResponse<{ id: string; slug: string }>> {
  try {
    const session = await auth();
    if (!session?.user) {
      return { success: false, error: { message: 'Please sign in.', code: 'UNAUTHORIZED' } };
    }

    // Validate input
    const parsed = createWorkspaceSchema.safeParse({
      name: formData.get('name'),
      slug: formData.get('slug'),
      plan: formData.get('plan'),
    });

    if (!parsed.success) {
      throw new ValidationError(parsed.error.flatten().fieldErrors as Record<string, string[]>);
    }

    // Check for slug conflict
    const existing = await db.workspace.findUnique({
      where: { slug: parsed.data.slug },
    });

    if (existing) {
      throw new ConflictError(`Workspace slug "${parsed.data.slug}" is already taken.`);
    }

    // Check workspace limit
    const workspaceCount = await db.workspace.count({
      where: { ownerId: session.user.id },
    });

    if (workspaceCount >= 5) {
      return {
        success: false,
        error: {
          message: 'You can have a maximum of 5 workspaces. Please upgrade or delete an existing workspace.',
          code: 'LIMIT_EXCEEDED',
        },
      };
    }

    // Create workspace
    const workspace = await db.workspace.create({
      data: {
        name: parsed.data.name,
        slug: parsed.data.slug,
        plan: parsed.data.plan,
        ownerId: session.user.id,
        members: {
          create: {
            userId: session.user.id,
            role: 'owner',
          },
        },
      },
    });

    revalidatePath('/workspaces');

    return { success: true, data: { id: workspace.id, slug: workspace.slug } };
  } catch (error) {
    return handleActionError(error);
  }
}
```

```typescript
// components/CreateWorkspaceForm.tsx
'use client';

import { useActionState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useFormStatus } from 'react-dom';
import { createWorkspace } from '@/app/actions/workspace';
import type { ActionResponse } from '@/lib/actions/error-handler';

const initialState: ActionResponse<{ id: string; slug: string }> = {
  success: false,
  error: { message: '', code: '' },
};

export function CreateWorkspaceForm() {
  const [state, formAction] = useActionState(createWorkspace, initialState);
  const router = useRouter();

  // Navigate on success
  useEffect(() => {
    if (state.success) {
      router.push(`/workspaces/${state.data.slug}`);
    }
  }, [state, router]);

  const fieldErrors = !state.success ? state.error.fieldErrors : undefined;

  return (
    <form action={formAction} className="space-y-4 max-w-md">
      {/* General error (non-field-specific) */}
      {!state.success && state.error.message && !fieldErrors && (
        <div className="bg-red-50 border border-red-200 p-4 rounded">
          <p className="text-red-800 text-sm">{state.error.message}</p>
          {state.error.code === 'LIMIT_EXCEEDED' && (
            <a href="/billing" className="text-red-600 underline text-sm mt-1 inline-block">
              Upgrade your plan
            </a>
          )}
        </div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">Workspace Name</label>
        <input
          name="name"
          className={`w-full border rounded p-2 ${fieldErrors?.name ? 'border-red-500' : ''}`}
        />
        {fieldErrors?.name && (
          <p className="text-red-600 text-sm mt-1">{fieldErrors.name[0]}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">URL Slug</label>
        <div className="flex items-center">
          <span className="text-gray-500 text-sm mr-1">app.example.com/</span>
          <input
            name="slug"
            className={`flex-1 border rounded p-2 ${fieldErrors?.slug ? 'border-red-500' : ''}`}
            pattern="[a-z0-9-]+"
          />
        </div>
        {fieldErrors?.slug && (
          <p className="text-red-600 text-sm mt-1">{fieldErrors.slug[0]}</p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Plan</label>
        <select name="plan" className="w-full border rounded p-2">
          <option value="free">Free</option>
          <option value="pro">Pro — $20/mo</option>
          <option value="enterprise">Enterprise — $99/mo</option>
        </select>
      </div>

      <SubmitButton />
    </form>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="w-full bg-black text-white py-2 rounded disabled:opacity-50"
    >
      {pending ? 'Creating...' : 'Create Workspace'}
    </button>
  );
}
```

---

## Q10. How do you implement revalidation strategies after Server Action mutations? (Intermediate)

**Scenario:** After creating a new blog post via a Server Action, you need to update the blog listing page, the author's profile page, the RSS feed, and the sitemap. Different pages have different freshness requirements.

**Answer:**

```typescript
// app/actions/blog.ts
'use server';

import { revalidatePath, revalidateTag } from 'next/cache';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

export async function publishBlogPost(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const title = formData.get('title') as string;
  const content = formData.get('content') as string;
  const slug = formData.get('slug') as string;
  const categoryId = formData.get('categoryId') as string;
  const tags = (formData.get('tags') as string).split(',').map((t) => t.trim());

  const post = await db.post.create({
    data: {
      title,
      content,
      slug,
      categoryId,
      authorId: session.user.id,
      status: 'published',
      publishedAt: new Date(),
      tags: {
        connectOrCreate: tags.map((tag) => ({
          where: { name: tag },
          create: { name: tag, slug: tag.toLowerCase().replace(/\s+/g, '-') },
        })),
      },
    },
    include: { category: true, tags: true },
  });

  // REVALIDATION STRATEGY:
  // Use tags for data-level invalidation (most precise)
  // Use paths for specific pages that need updating

  // 1. Invalidate blog listing caches
  revalidateTag('blog-posts');           // All blog listing data
  revalidateTag('latest-posts');         // "Latest posts" widget

  // 2. Invalidate category-specific caches
  revalidateTag(`category-${post.categoryId}`);

  // 3. Invalidate tag-specific caches
  for (const tag of post.tags) {
    revalidateTag(`tag-${tag.slug}`);
  }

  // 4. Invalidate author page
  revalidateTag(`author-${session.user.id}`);

  // 5. Revalidate specific paths
  revalidatePath('/blog');                          // Blog listing
  revalidatePath(`/blog/category/${post.category.slug}`); // Category page
  revalidatePath(`/authors/${session.user.id}`);    // Author profile

  // 6. Revalidate feeds and sitemap
  revalidatePath('/feed.xml');    // RSS feed
  revalidatePath('/sitemap.xml'); // Sitemap

  // 7. Redirect to the new post
  redirect(`/blog/${post.slug}`);
}

export async function updateBlogPost(postId: string, formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const post = await db.post.findUnique({
    where: { id: postId },
    include: { tags: true, category: true },
  });

  if (!post || post.authorId !== session.user.id) {
    throw new Error('Not found or unauthorized');
  }

  const newTitle = formData.get('title') as string;
  const newContent = formData.get('content') as string;
  const newCategoryId = formData.get('categoryId') as string;

  const updated = await db.post.update({
    where: { id: postId },
    data: {
      title: newTitle,
      content: newContent,
      categoryId: newCategoryId,
      updatedAt: new Date(),
    },
    include: { category: true },
  });

  // Revalidate the post itself
  revalidatePath(`/blog/${post.slug}`);

  // If category changed, revalidate both old and new category pages
  if (post.categoryId !== newCategoryId) {
    revalidateTag(`category-${post.categoryId}`);
    revalidateTag(`category-${newCategoryId}`);
  }

  // Always revalidate listing
  revalidateTag('blog-posts');

  redirect(`/blog/${updated.slug}`);
}

export async function deleteBlogPost(postId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const post = await db.post.findUnique({
    where: { id: postId },
    include: { tags: true },
  });

  if (!post || post.authorId !== session.user.id) {
    throw new Error('Not found or unauthorized');
  }

  await db.post.delete({ where: { id: postId } });

  // Broad revalidation since content was removed
  revalidateTag('blog-posts');
  revalidateTag(`category-${post.categoryId}`);
  revalidateTag(`author-${session.user.id}`);

  for (const tag of post.tags) {
    revalidateTag(`tag-${tag.slug}`);
  }

  revalidatePath('/blog');
  revalidatePath('/feed.xml');

  redirect('/blog');
}
```

```
┌──────────────────────────────────────────────────────────────┐
│      REVALIDATION STRATEGY AFTER publishBlogPost()            │
│                                                               │
│  Mutation: New post in "Technology" category with             │
│            tags: ["react", "nextjs"]                          │
│                                                               │
│  Tag Revalidation (data-level):                               │
│  ├── 'blog-posts'          → Blog listing fetches             │
│  ├── 'latest-posts'        → "Latest" widget fetches          │
│  ├── 'category-technology'  → Technology page fetches          │
│  ├── 'tag-react'           → React tag page fetches           │
│  ├── 'tag-nextjs'          → Next.js tag page fetches         │
│  └── 'author-user123'      → Author profile fetches           │
│                                                               │
│  Path Revalidation (route-level):                             │
│  ├── /blog                  → Blog listing page               │
│  ├── /blog/category/tech    → Category page                   │
│  ├── /authors/user123       → Author profile page             │
│  ├── /feed.xml              → RSS feed route                  │
│  └── /sitemap.xml           → Sitemap route                   │
│                                                               │
│  redirect('/blog/new-post-slug') → Navigate to new post       │
└──────────────────────────────────────────────────────────────┘
```

---

## Q11. What are the tradeoffs between Server Actions and API Routes, and when should you use each? (Intermediate)

**Scenario:** Your team is debating whether to use Server Actions exclusively or maintain API routes. Some features include: form submissions, webhook handlers, mobile app API, third-party integrations, and internal admin tools.

**Answer:**

```
┌──────────────────────────────────────────────────────────────────┐
│           DECISION MATRIX: Server Actions vs API Routes          │
├──────────────────────────┬─────────────────┬────────────────────┤
│  Use Case                │ Server Actions  │ API Routes         │
├──────────────────────────┼─────────────────┼────────────────────┤
│  Form submissions        │ ✅ Primary       │ 🟡 Possible       │
│  Data mutations (CRUD)   │ ✅ Primary       │ 🟡 Possible       │
│  Optimistic updates      │ ✅ Built-in      │ ❌ Manual          │
│  Progressive enhancement │ ✅ Automatic     │ ❌ Not possible    │
│  Webhook endpoints       │ ❌ No            │ ✅ Required        │
│  External API clients    │ ❌ No            │ ✅ Required        │
│  Mobile app backend      │ ❌ No            │ ✅ Required        │
│  Streaming responses     │ ❌ No            │ ✅ Yes             │
│  Custom HTTP methods     │ ❌ POST only     │ ✅ GET/POST/etc    │
│  Custom headers/status   │ ❌ Limited       │ ✅ Full control    │
│  CORS handling           │ ❌ N/A           │ ✅ Required        │
│  File downloads          │ ❌ No            │ ✅ Yes             │
│  SSE / long-polling      │ ❌ No            │ ✅ Yes             │
│  Cache-able GET requests │ ❌ No            │ ✅ Yes             │
│  Rate limiting           │ 🟡 Manual       │ 🟡 Manual         │
│  Type safety             │ ✅ End-to-end   │ 🟡 Manual         │
│  Testing                 │ 🟡 Integration  │ ✅ Unit testable  │
└──────────────────────────┴─────────────────┴────────────────────┘
```

**Production architecture using both:**

```typescript
// ✅ SERVER ACTIONS — for internal mutations from the Next.js UI
// app/actions/project.ts
'use server';

import { revalidateTag } from 'next/cache';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

export async function createProject(formData: FormData) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const project = await db.project.create({
    data: {
      name: formData.get('name') as string,
      ownerId: session.user.id,
    },
  });

  revalidateTag('projects');
  return { id: project.id };
}
```

```typescript
// ✅ API ROUTES — for external consumers, webhooks, and special HTTP needs

// app/api/v1/projects/route.ts — for mobile app / external clients
import { NextRequest, NextResponse } from 'next/server';
import { verifyApiKey } from '@/lib/auth/api-key';
import { db } from '@/lib/db';

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key');
  const client = await verifyApiKey(apiKey);
  if (!client) {
    return NextResponse.json({ error: 'Invalid API key' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '20');

  const projects = await db.project.findMany({
    where: { organizationId: client.organizationId },
    skip: (page - 1) * limit,
    take: limit,
  });

  return NextResponse.json({
    data: projects,
    pagination: { page, limit },
  });
}

export async function POST(request: NextRequest) {
  const apiKey = request.headers.get('x-api-key');
  const client = await verifyApiKey(apiKey);
  if (!client) {
    return NextResponse.json({ error: 'Invalid API key' }, { status: 401 });
  }

  const body = await request.json();

  const project = await db.project.create({
    data: {
      name: body.name,
      organizationId: client.organizationId,
    },
  });

  return NextResponse.json({ data: project }, { status: 201 });
}
```

```typescript
// app/api/webhooks/stripe/route.ts — Webhook handler (must be API route)
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { headers } from 'next/headers';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: NextRequest) {
  const body = await request.text();
  const headersList = await headers();
  const sig = headersList.get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed':
      await handleCheckoutComplete(event.data.object as Stripe.Checkout.Session);
      break;
    case 'customer.subscription.updated':
      await handleSubscriptionUpdate(event.data.object as Stripe.Subscription);
      break;
  }

  return NextResponse.json({ received: true });
}

async function handleCheckoutComplete(_session: Stripe.Checkout.Session) { /* ... */ }
async function handleSubscriptionUpdate(_subscription: Stripe.Subscription) { /* ... */ }
```

---

## Q12. How do you implement a multi-step form wizard with Server Actions that preserves state across steps? (Intermediate)

**Scenario:** You're building an onboarding flow with 4 steps: Personal Info → Company Details → Team Invites → Review & Submit. Each step validates independently, and users can go back to previous steps.

**Answer:**

```typescript
// app/actions/onboarding.ts
'use server';

import { z } from 'zod';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

// Step-specific schemas
const step1Schema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  jobTitle: z.string().min(2, 'Job title is required'),
});

const step2Schema = z.object({
  companyName: z.string().min(2, 'Company name is required'),
  companySize: z.enum(['1-10', '11-50', '51-200', '201-1000', '1000+']),
  industry: z.string().min(1, 'Please select an industry'),
});

const step3Schema = z.object({
  invites: z.array(
    z.object({
      email: z.string().email('Invalid email'),
      role: z.enum(['admin', 'member']),
    })
  ).max(10, 'Maximum 10 invites'),
});

export type OnboardingState = {
  step: number;
  data: {
    step1?: z.infer<typeof step1Schema>;
    step2?: z.infer<typeof step2Schema>;
    step3?: z.infer<typeof step3Schema>;
  };
  errors?: Record<string, string[]>;
};

// Load saved progress from encrypted cookie
async function loadOnboardingState(): Promise<OnboardingState> {
  const cookieStore = await cookies();
  const saved = cookieStore.get('onboarding-state');

  if (saved) {
    try {
      return JSON.parse(saved.value);
    } catch {
      // Corrupted cookie
    }
  }

  return { step: 1, data: {} };
}

// Save progress to encrypted cookie
async function saveOnboardingState(state: OnboardingState) {
  const cookieStore = await cookies();
  cookieStore.set('onboarding-state', JSON.stringify(state), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 24, // 24 hours
    path: '/onboarding',
  });
}

export async function submitStep1(
  _prevState: OnboardingState,
  formData: FormData
): Promise<OnboardingState> {
  const state = await loadOnboardingState();

  const result = step1Schema.safeParse({
    firstName: formData.get('firstName'),
    lastName: formData.get('lastName'),
    jobTitle: formData.get('jobTitle'),
  });

  if (!result.success) {
    return { ...state, step: 1, errors: result.error.flatten().fieldErrors as Record<string, string[]> };
  }

  const newState: OnboardingState = {
    step: 2,
    data: { ...state.data, step1: result.data },
  };

  await saveOnboardingState(newState);
  redirect('/onboarding/step-2');
}

export async function submitStep2(
  _prevState: OnboardingState,
  formData: FormData
): Promise<OnboardingState> {
  const state = await loadOnboardingState();

  const result = step2Schema.safeParse({
    companyName: formData.get('companyName'),
    companySize: formData.get('companySize'),
    industry: formData.get('industry'),
  });

  if (!result.success) {
    return { ...state, step: 2, errors: result.error.flatten().fieldErrors as Record<string, string[]> };
  }

  const newState: OnboardingState = {
    step: 3,
    data: { ...state.data, step2: result.data },
  };

  await saveOnboardingState(newState);
  redirect('/onboarding/step-3');
}

export async function submitStep3(
  _prevState: OnboardingState,
  formData: FormData
): Promise<OnboardingState> {
  const state = await loadOnboardingState();

  const inviteEmails = formData.getAll('invite-email') as string[];
  const inviteRoles = formData.getAll('invite-role') as string[];

  const invites = inviteEmails
    .map((email, i) => ({ email, role: inviteRoles[i] }))
    .filter((inv) => inv.email.trim() !== '');

  const result = step3Schema.safeParse({ invites });

  if (!result.success) {
    return { ...state, step: 3, errors: { invites: result.error.errors.map((e) => e.message) } };
  }

  const newState: OnboardingState = {
    step: 4,
    data: { ...state.data, step3: result.data },
  };

  await saveOnboardingState(newState);
  redirect('/onboarding/review');
}

export async function completeOnboarding(): Promise<void> {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const state = await loadOnboardingState();

  // Validate all steps are complete
  if (!state.data.step1 || !state.data.step2 || !state.data.step3) {
    redirect('/onboarding/step-1');
  }

  // Create everything in a transaction
  await db.$transaction(async (tx) => {
    // Update user profile
    await tx.user.update({
      where: { id: session.user.id },
      data: {
        firstName: state.data.step1!.firstName,
        lastName: state.data.step1!.lastName,
        jobTitle: state.data.step1!.jobTitle,
        onboardedAt: new Date(),
      },
    });

    // Create organization
    const org = await tx.organization.create({
      data: {
        name: state.data.step2!.companyName,
        size: state.data.step2!.companySize,
        industry: state.data.step2!.industry,
        ownerId: session.user.id,
      },
    });

    // Send invites
    for (const invite of state.data.step3!.invites) {
      await tx.invite.create({
        data: {
          email: invite.email,
          role: invite.role,
          organizationId: org.id,
          invitedBy: session.user.id,
        },
      });
    }
  });

  // Clear onboarding state
  const cookieStore = await cookies();
  cookieStore.delete('onboarding-state');

  redirect('/dashboard');
}

export async function goToStep(step: number): Promise<void> {
  const state = await loadOnboardingState();
  const newState = { ...state, step };
  await saveOnboardingState(newState);

  const stepPaths: Record<number, string> = {
    1: '/onboarding/step-1',
    2: '/onboarding/step-2',
    3: '/onboarding/step-3',
    4: '/onboarding/review',
  };

  redirect(stepPaths[step] || '/onboarding/step-1');
}
```

---

## Q13. How do you implement Server Actions that handle concurrent mutations with optimistic concurrency control? (Advanced)

**Scenario:** Multiple users can edit the same document simultaneously. When two users submit changes at the same time, you need to detect conflicts and handle them gracefully rather than silently losing one user's changes.

**Answer:**

```typescript
// app/actions/document.ts
'use server';

import { z } from 'zod';
import { revalidateTag } from 'next/cache';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { diff_match_patch } from 'diff-match-patch';

const updateDocSchema = z.object({
  documentId: z.string().uuid(),
  content: z.string().max(100000),
  title: z.string().min(1).max(200),
  baseVersion: z.number().int().positive(),
});

export type DocumentUpdateResult =
  | { success: true; newVersion: number }
  | { success: false; conflict: true; serverContent: string; serverVersion: number; serverTitle: string }
  | { success: false; conflict: false; error: string };

export async function updateDocument(input: z.infer<typeof updateDocSchema>): Promise<DocumentUpdateResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, conflict: false, error: 'Unauthorized' };
  }

  const parsed = updateDocSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, conflict: false, error: 'Invalid input' };
  }

  const { documentId, content, title, baseVersion } = parsed.data;

  try {
    // Use a transaction with serializable isolation for safety
    const result = await db.$transaction(async (tx) => {
      // Lock the row and check version
      const current = await tx.document.findUnique({
        where: { id: documentId },
      });

      if (!current) {
        throw new Error('Document not found');
      }

      // Check if user has permission
      const hasAccess = await tx.documentAccess.findFirst({
        where: {
          documentId,
          userId: session.user.id,
          permission: { in: ['write', 'owner'] },
        },
      });

      if (!hasAccess) {
        throw new Error('No write access');
      }

      // OPTIMISTIC CONCURRENCY CHECK
      if (current.version !== baseVersion) {
        // Conflict detected — another user modified the document
        return {
          conflict: true as const,
          serverContent: current.content,
          serverVersion: current.version,
          serverTitle: current.title,
        };
      }

      // No conflict — apply the update
      const updated = await tx.document.update({
        where: { id: documentId },
        data: {
          content,
          title,
          version: { increment: 1 },
          lastEditedBy: session.user.id,
          updatedAt: new Date(),
        },
      });

      // Record edit history
      await tx.documentHistory.create({
        data: {
          documentId,
          content: current.content,
          title: current.title,
          version: current.version,
          editedBy: session.user.id,
        },
      });

      return { conflict: false as const, newVersion: updated.version };
    });

    if (result.conflict) {
      return {
        success: false,
        conflict: true,
        serverContent: result.serverContent,
        serverVersion: result.serverVersion,
        serverTitle: result.serverTitle,
      };
    }

    revalidateTag(`doc-${documentId}`);

    return { success: true, newVersion: result.newVersion };
  } catch (error) {
    console.error('Document update error:', error);
    return {
      success: false,
      conflict: false,
      error: error instanceof Error ? error.message : 'Update failed',
    };
  }
}

// Automatic merge attempt for conflicts
export async function mergeAndSave(input: {
  documentId: string;
  baseContent: string;
  clientContent: string;
  serverContent: string;
  serverVersion: number;
  title: string;
}): Promise<DocumentUpdateResult> {
  const dmp = new diff_match_patch();

  // Create patches from base → client changes
  const patches = dmp.patch_make(input.baseContent, input.clientContent);

  // Apply client's patches to the server's current content
  const [mergedContent, results] = dmp.patch_apply(patches, input.serverContent);

  // Check if all patches applied cleanly
  const allApplied = results.every(Boolean);

  if (!allApplied) {
    // Patches didn't apply cleanly — manual merge needed
    return {
      success: false,
      conflict: true,
      serverContent: input.serverContent,
      serverVersion: input.serverVersion,
      serverTitle: input.title,
    };
  }

  // Patches applied — save the merged content
  return updateDocument({
    documentId: input.documentId,
    content: mergedContent,
    title: input.title,
    baseVersion: input.serverVersion,
  });
}
```

```typescript
// components/DocumentEditor.tsx
'use client';

import { useState, useCallback, useRef } from 'react';
import { updateDocument, mergeAndSave, type DocumentUpdateResult } from '@/app/actions/document';

interface DocumentEditorProps {
  documentId: string;
  initialContent: string;
  initialTitle: string;
  initialVersion: number;
}

export function DocumentEditor({
  documentId,
  initialContent,
  initialTitle,
  initialVersion,
}: DocumentEditorProps) {
  const [content, setContent] = useState(initialContent);
  const [title, setTitle] = useState(initialTitle);
  const [version, setVersion] = useState(initialVersion);
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState<{
    serverContent: string;
    serverVersion: number;
  } | null>(null);

  const baseContentRef = useRef(initialContent);

  const handleSave = useCallback(async () => {
    setSaving(true);
    setConflict(null);

    const result = await updateDocument({
      documentId,
      content,
      title,
      baseVersion: version,
    });

    if (result.success) {
      setVersion(result.newVersion);
      baseContentRef.current = content;
      setSaving(false);
      return;
    }

    if (result.conflict) {
      // Attempt automatic merge
      const mergeResult = await mergeAndSave({
        documentId,
        baseContent: baseContentRef.current,
        clientContent: content,
        serverContent: result.serverContent,
        serverVersion: result.serverVersion,
        title,
      });

      if (mergeResult.success) {
        setVersion(mergeResult.newVersion);
        baseContentRef.current = content;
        setSaving(false);
        return;
      }

      // Auto-merge failed — show conflict to user
      setConflict({
        serverContent: result.serverContent,
        serverVersion: result.serverVersion,
      });
    }

    setSaving(false);
  }, [documentId, content, title, version]);

  const resolveConflict = useCallback(
    (resolution: 'mine' | 'theirs' | 'merged', mergedContent?: string) => {
      if (!conflict) return;

      switch (resolution) {
        case 'mine':
          setVersion(conflict.serverVersion);
          break;
        case 'theirs':
          setContent(conflict.serverContent);
          setVersion(conflict.serverVersion);
          break;
        case 'merged':
          if (mergedContent) setContent(mergedContent);
          setVersion(conflict.serverVersion);
          break;
      }

      setConflict(null);
    },
    [conflict]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="text-2xl font-bold border-none outline-none flex-1"
        />
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">v{version}</span>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      {conflict && (
        <ConflictResolver
          myContent={content}
          theirContent={conflict.serverContent}
          onResolve={resolveConflict}
        />
      )}

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="w-full h-96 p-4 border rounded font-mono"
      />
    </div>
  );
}

function ConflictResolver({
  myContent,
  theirContent,
  onResolve,
}: {
  myContent: string;
  theirContent: string;
  onResolve: (resolution: 'mine' | 'theirs' | 'merged', merged?: string) => void;
}) {
  return (
    <div className="bg-yellow-50 border border-yellow-300 p-4 rounded">
      <h3 className="font-bold text-yellow-800 mb-2">Conflict Detected</h3>
      <p className="text-sm text-yellow-700 mb-4">
        Another user modified this document while you were editing.
      </p>
      <div className="flex gap-2">
        <button
          onClick={() => onResolve('mine')}
          className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
        >
          Keep My Changes
        </button>
        <button
          onClick={() => onResolve('theirs')}
          className="bg-gray-600 text-white px-3 py-1 rounded text-sm"
        >
          Use Their Changes
        </button>
      </div>
    </div>
  );
}
```

---

## Q14. How do you implement rate limiting for Server Actions in a production environment? (Advanced)

**Scenario:** Your public-facing Server Actions (registration, password reset, contact forms) are being abused by bots. You need per-action, per-IP, and per-user rate limiting that works across serverless instances.

**Answer:**

```typescript
// lib/rate-limit/index.ts
import { Redis } from '@upstash/redis';
import { Ratelimit } from '@upstash/ratelimit';
import { headers } from 'next/headers';
import { auth } from '@/lib/auth';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_URL!,
  token: process.env.UPSTASH_REDIS_TOKEN!,
});

// Different rate limit tiers
const rateLimiters = {
  // Public forms — strict limits
  public: new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(5, '60 s'), // 5 requests per minute
    prefix: 'ratelimit:public',
  }),

  // Authenticated actions — moderate limits
  authenticated: new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(30, '60 s'), // 30 requests per minute
    prefix: 'ratelimit:authenticated',
  }),

  // Sensitive actions (password reset, etc.) — very strict
  sensitive: new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(3, '300 s'), // 3 per 5 minutes
    prefix: 'ratelimit:sensitive',
  }),

  // Admin actions — generous limits
  admin: new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(100, '60 s'), // 100 per minute
    prefix: 'ratelimit:admin',
  }),
};

export type RateLimitTier = keyof typeof rateLimiters;

interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: Date;
}

export async function checkRateLimit(
  actionName: string,
  tier: RateLimitTier = 'authenticated'
): Promise<RateLimitResult> {
  const headersList = await headers();
  const ip = headersList.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';

  // Build identifier: IP for public, userId for authenticated
  let identifier = `${actionName}:${ip}`;

  if (tier !== 'public') {
    const session = await auth();
    if (session?.user) {
      identifier = `${actionName}:${session.user.id}`;
    }
  }

  const limiter = rateLimiters[tier];
  const result = await limiter.limit(identifier);

  return {
    allowed: result.success,
    remaining: result.remaining,
    resetAt: new Date(result.reset),
  };
}

// Decorator-style rate limit wrapper
export function withRateLimit<TArgs extends unknown[], TReturn>(
  actionName: string,
  tier: RateLimitTier,
  action: (...args: TArgs) => Promise<TReturn>
) {
  return async (...args: TArgs): Promise<TReturn> => {
    const { allowed, remaining, resetAt } = await checkRateLimit(actionName, tier);

    if (!allowed) {
      const retryAfter = Math.ceil((resetAt.getTime() - Date.now()) / 1000);
      throw new Error(
        `Rate limit exceeded. Try again in ${retryAfter} seconds.`
      );
    }

    if (remaining <= 2) {
      console.warn(`[Rate Limit] ${actionName}: ${remaining} requests remaining`);
    }

    return action(...args);
  };
}
```

```typescript
// app/actions/auth.ts
'use server';

import { z } from 'zod';
import { checkRateLimit, withRateLimit } from '@/lib/rate-limit';

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2),
});

type RegisterResult =
  | { success: true; userId: string }
  | { success: false; error: string; retryAfter?: number };

// Method 1: Manual rate limit check
export async function register(
  _prevState: RegisterResult,
  formData: FormData
): Promise<RegisterResult> {
  // Rate limit check FIRST
  const { allowed, remaining, resetAt } = await checkRateLimit('register', 'public');

  if (!allowed) {
    const retryAfter = Math.ceil((resetAt.getTime() - Date.now()) / 1000);
    return {
      success: false,
      error: `Too many registration attempts. Please try again in ${retryAfter} seconds.`,
      retryAfter,
    };
  }

  const parsed = registerSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
    name: formData.get('name'),
  });

  if (!parsed.success) {
    return { success: false, error: 'Invalid input.' };
  }

  // ... registration logic
  return { success: true, userId: 'new-user-id' };
}

// Method 2: Using the withRateLimit wrapper
const _requestPasswordReset = async (email: string) => {
  // ... send password reset email
  return { success: true, message: 'Reset email sent if account exists.' };
};

export const requestPasswordReset = withRateLimit(
  'password-reset',
  'sensitive',
  _requestPasswordReset
);
```

```
┌──────────────────────────────────────────────────────────────┐
│          RATE LIMITING ARCHITECTURE                           │
│                                                               │
│  Server Action Call                                           │
│       │                                                       │
│       ▼                                                       │
│  ┌─────────────────────┐                                      │
│  │ Extract Identifier  │                                      │
│  │ (IP / User ID)      │                                      │
│  └─────────┬───────────┘                                      │
│            ▼                                                   │
│  ┌─────────────────────┐     ┌──────────────┐                │
│  │ Upstash Redis       │────►│ Sliding      │                │
│  │ Rate Limiter        │     │ Window       │                │
│  │                     │     │ Algorithm    │                │
│  └─────────┬───────────┘     └──────────────┘                │
│            │                                                   │
│       ┌────┴────┐                                             │
│       │         │                                              │
│  ┌────▼───┐ ┌──▼──────┐                                      │
│  │ALLOWED │ │ DENIED  │                                       │
│  │        │ │         │                                       │
│  │Execute │ │ Return  │                                       │
│  │Action  │ │ Error + │                                       │
│  │        │ │ Retry   │                                       │
│  └────────┘ │ After   │                                       │
│             └─────────┘                                       │
│                                                               │
│  TIER CONFIG:                                                 │
│  ┌──────────────┬──────────────┬──────────────┐              │
│  │ public       │ authenticated│ sensitive    │              │
│  │ 5/min        │ 30/min       │ 3/5min      │              │
│  │ By IP        │ By User ID   │ By User ID  │              │
│  └──────────────┴──────────────┴──────────────┘              │
└──────────────────────────────────────────────────────────────┘
```

---

## Q15. How do you build a real-time collaborative form with Server Actions and optimistic updates for a complex entity like a project settings page? (Advanced)

**Scenario:** Multiple team admins can edit project settings simultaneously. Changes should be saved per-field (not per-form) with debouncing, optimistic updates, and conflict handling.

**Answer:**

```typescript
// app/actions/project-settings.ts
'use server';

import { z } from 'zod';
import { revalidateTag } from 'next/cache';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

const fieldSchemas: Record<string, z.ZodType> = {
  name: z.string().min(1).max(100),
  description: z.string().max(500),
  visibility: z.enum(['public', 'private', 'internal']),
  defaultBranch: z.string().min(1),
  enableIssues: z.boolean(),
  enableWiki: z.boolean(),
  enableDiscussions: z.boolean(),
  maxFileSize: z.number().min(1).max(100),
};

export type FieldUpdateResult =
  | { success: true; field: string; value: unknown; version: number }
  | { success: false; field: string; error: string; currentValue: unknown; currentVersion: number };

export async function updateProjectField(
  projectId: string,
  field: string,
  value: unknown,
  expectedVersion: number
): Promise<FieldUpdateResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, field, error: 'Unauthorized', currentValue: null, currentVersion: 0 };
  }

  // Validate the specific field
  const schema = fieldSchemas[field];
  if (!schema) {
    return { success: false, field, error: 'Unknown field', currentValue: null, currentVersion: 0 };
  }

  const parsed = schema.safeParse(value);
  if (!parsed.success) {
    return {
      success: false,
      field,
      error: parsed.error.errors[0]?.message || 'Invalid value',
      currentValue: null,
      currentVersion: expectedVersion,
    };
  }

  try {
    const result = await db.$transaction(async (tx) => {
      const project = await tx.project.findUnique({
        where: { id: projectId },
        select: { version: true, [field]: true, id: true },
      });

      if (!project) throw new Error('Project not found');

      // Optimistic concurrency check
      if (project.version !== expectedVersion) {
        return {
          conflict: true as const,
          currentValue: (project as Record<string, unknown>)[field],
          currentVersion: project.version,
        };
      }

      const updated = await tx.project.update({
        where: { id: projectId },
        data: {
          [field]: parsed.data,
          version: { increment: 1 },
          updatedAt: new Date(),
          lastEditedBy: session.user.id,
        },
      });

      // Audit log for settings changes
      await tx.settingsAudit.create({
        data: {
          projectId,
          field,
          oldValue: JSON.stringify((project as Record<string, unknown>)[field]),
          newValue: JSON.stringify(parsed.data),
          changedBy: session.user.id,
        },
      });

      return { conflict: false as const, newVersion: updated.version };
    });

    if (result.conflict) {
      return {
        success: false,
        field,
        error: 'This field was modified by another user.',
        currentValue: result.currentValue,
        currentVersion: result.currentVersion,
      };
    }

    revalidateTag(`project-${projectId}`);

    return { success: true, field, value: parsed.data, version: result.newVersion };
  } catch (error) {
    console.error('Field update error:', error);
    return {
      success: false,
      field,
      error: 'Failed to save. Please try again.',
      currentValue: null,
      currentVersion: expectedVersion,
    };
  }
}
```

```typescript
// hooks/use-auto-save-field.ts
'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { updateProjectField, type FieldUpdateResult } from '@/app/actions/project-settings';

interface UseAutoSaveFieldOptions {
  projectId: string;
  field: string;
  initialValue: unknown;
  initialVersion: number;
  debounceMs?: number;
  onConflict?: (result: Extract<FieldUpdateResult, { success: false }>) => void;
}

export function useAutoSaveField({
  projectId,
  field,
  initialValue,
  initialVersion,
  debounceMs = 1000,
  onConflict,
}: UseAutoSaveFieldOptions) {
  const [value, setValue] = useState(initialValue);
  const [version, setVersion] = useState(initialVersion);
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const latestValueRef = useRef(initialValue);

  const save = useCallback(
    async (newValue: unknown) => {
      setStatus('saving');
      setError(null);

      const result = await updateProjectField(projectId, field, newValue, version);

      if (result.success) {
        setVersion(result.version);
        setStatus('saved');
        setTimeout(() => setStatus('idle'), 2000);
      } else {
        setError(result.error);
        setStatus('error');

        if (result.currentValue !== null) {
          // Conflict — another user changed this field
          onConflict?.(result);
        }
      }
    },
    [projectId, field, version, onConflict]
  );

  const handleChange = useCallback(
    (newValue: unknown) => {
      setValue(newValue);
      latestValueRef.current = newValue;

      // Debounce the save
      if (timerRef.current) clearTimeout(timerRef.current);

      timerRef.current = setTimeout(() => {
        save(latestValueRef.current);
      }, debounceMs);
    },
    [save, debounceMs]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { value, setValue: handleChange, status, error, save };
}
```

```typescript
// app/projects/[id]/settings/page.tsx
'use client';

import { useAutoSaveField } from '@/hooks/use-auto-save-field';

interface ProjectSettings {
  id: string;
  name: string;
  description: string;
  visibility: 'public' | 'private' | 'internal';
  enableIssues: boolean;
  enableWiki: boolean;
  version: number;
}

export default function ProjectSettingsPage({
  project,
}: {
  project: ProjectSettings;
}) {
  return (
    <div className="max-w-2xl space-y-8 p-6">
      <h1 className="text-2xl font-bold">Project Settings</h1>

      <AutoSaveTextField
        projectId={project.id}
        field="name"
        label="Project Name"
        initialValue={project.name}
        initialVersion={project.version}
      />

      <AutoSaveTextField
        projectId={project.id}
        field="description"
        label="Description"
        initialValue={project.description}
        initialVersion={project.version}
        multiline
      />

      <AutoSaveSelectField
        projectId={project.id}
        field="visibility"
        label="Visibility"
        initialValue={project.visibility}
        initialVersion={project.version}
        options={[
          { value: 'public', label: 'Public' },
          { value: 'private', label: 'Private' },
          { value: 'internal', label: 'Internal' },
        ]}
      />

      <AutoSaveToggleField
        projectId={project.id}
        field="enableIssues"
        label="Enable Issues"
        description="Allow team members to create and track issues."
        initialValue={project.enableIssues}
        initialVersion={project.version}
      />

      <AutoSaveToggleField
        projectId={project.id}
        field="enableWiki"
        label="Enable Wiki"
        description="Enable the project wiki for documentation."
        initialValue={project.enableWiki}
        initialVersion={project.version}
      />
    </div>
  );
}

function AutoSaveTextField({
  projectId,
  field,
  label,
  initialValue,
  initialVersion,
  multiline = false,
}: {
  projectId: string;
  field: string;
  label: string;
  initialValue: string;
  initialVersion: number;
  multiline?: boolean;
}) {
  const { value, setValue, status, error } = useAutoSaveField({
    projectId,
    field,
    initialValue,
    initialVersion,
    debounceMs: 1500,
  });

  const InputComponent = multiline ? 'textarea' : 'input';

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium">{label}</label>
        <SaveStatus status={status} />
      </div>
      <InputComponent
        value={value as string}
        onChange={(e) => setValue(e.target.value)}
        className="w-full border rounded p-2"
        rows={multiline ? 3 : undefined}
      />
      {error && <p className="text-red-600 text-sm mt-1">{error}</p>}
    </div>
  );
}

function AutoSaveSelectField({
  projectId,
  field,
  label,
  initialValue,
  initialVersion,
  options,
}: {
  projectId: string;
  field: string;
  label: string;
  initialValue: string;
  initialVersion: number;
  options: { value: string; label: string }[];
}) {
  const { value, setValue, status, error } = useAutoSaveField({
    projectId,
    field,
    initialValue,
    initialVersion,
    debounceMs: 0, // Save immediately on selection
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium">{label}</label>
        <SaveStatus status={status} />
      </div>
      <select
        value={value as string}
        onChange={(e) => setValue(e.target.value)}
        className="w-full border rounded p-2"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-red-600 text-sm mt-1">{error}</p>}
    </div>
  );
}

function AutoSaveToggleField({
  projectId,
  field,
  label,
  description,
  initialValue,
  initialVersion,
}: {
  projectId: string;
  field: string;
  label: string;
  description: string;
  initialValue: boolean;
  initialVersion: number;
}) {
  const { value, setValue, status, error } = useAutoSaveField({
    projectId,
    field,
    initialValue,
    initialVersion,
    debounceMs: 0,
  });

  return (
    <div className="flex items-center justify-between p-4 border rounded">
      <div>
        <p className="font-medium">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
        {error && <p className="text-red-600 text-sm mt-1">{error}</p>}
      </div>
      <div className="flex items-center gap-2">
        <SaveStatus status={status} />
        <button
          role="switch"
          aria-checked={value as boolean}
          onClick={() => setValue(!(value as boolean))}
          className={`relative inline-flex h-6 w-11 rounded-full transition ${
            value ? 'bg-blue-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-5 w-5 rounded-full bg-white shadow mt-0.5 transition ${
              value ? 'translate-x-5 ml-0.5' : 'translate-x-0.5'
            }`}
          />
        </button>
      </div>
    </div>
  );
}

function SaveStatus({ status }: { status: string }) {
  switch (status) {
    case 'saving':
      return <span className="text-xs text-gray-400">Saving...</span>;
    case 'saved':
      return <span className="text-xs text-green-600">Saved</span>;
    case 'error':
      return <span className="text-xs text-red-600">Error</span>;
    default:
      return null;
  }
}
```

---

## Q16. How do you implement a Server Action that processes large batch operations with progress reporting? (Advanced)

**Scenario:** An admin needs to bulk-import 10,000 products from a CSV file. The operation takes several minutes. You need to show progress, handle partial failures, and allow cancellation.

**Answer:**

```typescript
// app/actions/bulk-import.ts
'use server';

import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { z } from 'zod';
import { revalidateTag } from 'next/cache';

const productRowSchema = z.object({
  name: z.string().min(1),
  sku: z.string().min(1),
  price: z.coerce.number().positive(),
  stock: z.coerce.number().int().min(0),
  category: z.string().min(1),
  description: z.string().optional(),
});

export type ImportProgress = {
  status: 'idle' | 'parsing' | 'importing' | 'complete' | 'error' | 'cancelled';
  totalRows: number;
  processedRows: number;
  successCount: number;
  errorCount: number;
  errors: { row: number; message: string }[];
  batchId?: string;
};

// Step 1: Parse and validate the CSV file
export async function parseAndValidateCSV(
  formData: FormData
): Promise<ImportProgress & { validRows?: z.infer<typeof productRowSchema>[] }> {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const file = formData.get('file') as File;
  if (!file) {
    return {
      status: 'error',
      totalRows: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      errors: [{ row: 0, message: 'No file provided' }],
    };
  }

  const text = await file.text();
  const lines = text.split('\n').filter((line) => line.trim());
  const headerLine = lines[0];
  const dataLines = lines.slice(1);

  if (!headerLine) {
    return {
      status: 'error',
      totalRows: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      errors: [{ row: 0, message: 'Empty file' }],
    };
  }

  const headers = headerLine.split(',').map((h) => h.trim().toLowerCase());
  const validRows: z.infer<typeof productRowSchema>[] = [];
  const errors: { row: number; message: string }[] = [];

  for (let i = 0; i < dataLines.length; i++) {
    const values = dataLines[i].split(',').map((v) => v.trim());
    const rowData: Record<string, string> = {};

    headers.forEach((header, idx) => {
      rowData[header] = values[idx] || '';
    });

    const result = productRowSchema.safeParse(rowData);

    if (result.success) {
      validRows.push(result.data);
    } else {
      errors.push({
        row: i + 2, // +2 for header row and 1-indexing
        message: result.error.errors.map((e) => `${e.path}: ${e.message}`).join('; '),
      });
    }
  }

  // Store valid rows in DB as a pending batch
  const batch = await db.importBatch.create({
    data: {
      userId: session.user.id,
      totalRows: dataLines.length,
      validRows: validRows.length,
      invalidRows: errors.length,
      data: JSON.stringify(validRows),
      status: 'pending',
    },
  });

  return {
    status: 'parsing',
    totalRows: dataLines.length,
    processedRows: dataLines.length,
    successCount: validRows.length,
    errorCount: errors.length,
    errors: errors.slice(0, 50), // Limit errors shown
    batchId: batch.id,
    validRows,
  };
}

// Step 2: Execute the import in batches
export async function executeBatchImport(
  batchId: string
): Promise<ImportProgress> {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const batch = await db.importBatch.findUnique({
    where: { id: batchId, userId: session.user.id },
  });

  if (!batch || batch.status === 'cancelled') {
    return {
      status: 'cancelled',
      totalRows: 0,
      processedRows: 0,
      successCount: 0,
      errorCount: 0,
      errors: [],
      batchId,
    };
  }

  const products: z.infer<typeof productRowSchema>[] = JSON.parse(batch.data as string);
  const BATCH_SIZE = 100;
  let successCount = 0;
  let errorCount = 0;
  const errors: { row: number; message: string }[] = [];

  // Update batch status
  await db.importBatch.update({
    where: { id: batchId },
    data: { status: 'processing', startedAt: new Date() },
  });

  for (let i = 0; i < products.length; i += BATCH_SIZE) {
    // Check for cancellation
    const currentBatch = await db.importBatch.findUnique({
      where: { id: batchId },
      select: { status: true },
    });

    if (currentBatch?.status === 'cancelled') {
      return {
        status: 'cancelled',
        totalRows: products.length,
        processedRows: i,
        successCount,
        errorCount,
        errors,
        batchId,
      };
    }

    const batchProducts = products.slice(i, i + BATCH_SIZE);

    try {
      // Upsert products in batch
      await db.$transaction(
        batchProducts.map((product) =>
          db.product.upsert({
            where: { sku: product.sku },
            create: {
              name: product.name,
              sku: product.sku,
              price: product.price,
              stock: product.stock,
              categoryName: product.category,
              description: product.description || '',
            },
            update: {
              name: product.name,
              price: product.price,
              stock: product.stock,
              description: product.description || '',
            },
          })
        )
      );

      successCount += batchProducts.length;
    } catch (error) {
      // Retry individual items on batch failure
      for (let j = 0; j < batchProducts.length; j++) {
        try {
          await db.product.upsert({
            where: { sku: batchProducts[j].sku },
            create: {
              name: batchProducts[j].name,
              sku: batchProducts[j].sku,
              price: batchProducts[j].price,
              stock: batchProducts[j].stock,
              categoryName: batchProducts[j].category,
              description: batchProducts[j].description || '',
            },
            update: {
              name: batchProducts[j].name,
              price: batchProducts[j].price,
              stock: batchProducts[j].stock,
            },
          });
          successCount++;
        } catch (innerError) {
          errorCount++;
          errors.push({
            row: i + j + 1,
            message: innerError instanceof Error ? innerError.message : 'Unknown error',
          });
        }
      }
    }

    // Update progress
    await db.importBatch.update({
      where: { id: batchId },
      data: {
        processedRows: Math.min(i + BATCH_SIZE, products.length),
        successCount,
        errorCount,
      },
    });
  }

  // Mark complete
  await db.importBatch.update({
    where: { id: batchId },
    data: { status: 'complete', completedAt: new Date(), successCount, errorCount },
  });

  revalidateTag('products');
  revalidateTag('product-listings');

  return {
    status: 'complete',
    totalRows: products.length,
    processedRows: products.length,
    successCount,
    errorCount,
    errors: errors.slice(0, 50),
    batchId,
  };
}

// Step 3: Get progress for a batch
export async function getImportProgress(batchId: string): Promise<ImportProgress> {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  const batch = await db.importBatch.findUnique({
    where: { id: batchId, userId: session.user.id },
  });

  if (!batch) {
    return { status: 'error', totalRows: 0, processedRows: 0, successCount: 0, errorCount: 0, errors: [] };
  }

  return {
    status: batch.status as ImportProgress['status'],
    totalRows: batch.validRows,
    processedRows: batch.processedRows,
    successCount: batch.successCount,
    errorCount: batch.errorCount,
    errors: [],
    batchId,
  };
}

// Step 4: Cancel import
export async function cancelImport(batchId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  await db.importBatch.update({
    where: { id: batchId, userId: session.user.id },
    data: { status: 'cancelled' },
  });
}
```

---

## Q17. How do you implement Server Actions for a checkout flow with payment processing, idempotency, and error recovery? (Advanced)

**Scenario:** Your e-commerce checkout processes payments via Stripe. You need to handle: double-submissions, payment failures, partial state (payment succeeded but order creation failed), and session timeouts.

**Answer:**

```typescript
// app/actions/checkout.ts
'use server';

import { z } from 'zod';
import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { revalidatePath, revalidateTag } from 'next/cache';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

const checkoutSchema = z.object({
  shippingAddressId: z.string().uuid(),
  paymentMethodId: z.string(),
  couponCode: z.string().optional(),
});

export type CheckoutResult =
  | { success: true; orderId: string }
  | { success: false; error: string; code: string; recoverable: boolean };

export async function processCheckout(
  _prevState: CheckoutResult,
  formData: FormData
): Promise<CheckoutResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, error: 'Please sign in to checkout.', code: 'AUTH', recoverable: false };
  }

  const parsed = checkoutSchema.safeParse({
    shippingAddressId: formData.get('shippingAddressId'),
    paymentMethodId: formData.get('paymentMethodId'),
    couponCode: formData.get('couponCode') || undefined,
  });

  if (!parsed.success) {
    return { success: false, error: 'Invalid checkout data.', code: 'VALIDATION', recoverable: true };
  }

  // Generate idempotency key — prevents double-charges on retry
  const idempotencyKey = `checkout-${session.user.id}-${Date.now()}`;

  // Check for existing pending order (duplicate submission guard)
  const cookieStore = await cookies();
  const existingOrderId = cookieStore.get('pending-order-id')?.value;

  if (existingOrderId) {
    const existingOrder = await db.order.findUnique({
      where: { id: existingOrderId },
    });

    if (existingOrder) {
      if (existingOrder.status === 'completed') {
        // Already completed — redirect
        redirect(`/orders/${existingOrder.id}/confirmation`);
      }

      if (existingOrder.status === 'processing') {
        return {
          success: false,
          error: 'Your order is already being processed. Please wait.',
          code: 'DUPLICATE',
          recoverable: false,
        };
      }
    }
  }

  try {
    // Step 1: Get cart and calculate totals
    const cart = await db.cart.findUnique({
      where: { userId: session.user.id },
      include: {
        items: { include: { product: true } },
      },
    });

    if (!cart || cart.items.length === 0) {
      return { success: false, error: 'Your cart is empty.', code: 'EMPTY_CART', recoverable: false };
    }

    // Step 2: Verify stock availability
    for (const item of cart.items) {
      if (item.product.stock < item.quantity) {
        return {
          success: false,
          error: `${item.product.name} only has ${item.product.stock} units available.`,
          code: 'STOCK',
          recoverable: true,
        };
      }
    }

    // Step 3: Calculate totals
    let subtotal = cart.items.reduce(
      (sum, item) => sum + item.product.price * item.quantity,
      0
    );

    let discount = 0;
    if (parsed.data.couponCode) {
      const coupon = await db.coupon.findUnique({
        where: { code: parsed.data.couponCode, active: true },
      });
      if (coupon) {
        discount = coupon.type === 'percentage'
          ? subtotal * (coupon.value / 100)
          : coupon.value;
      }
    }

    const shipping = subtotal > 100 ? 0 : 9.99;
    const tax = (subtotal - discount) * 0.08; // 8% tax
    const total = subtotal - discount + shipping + tax;

    // Step 4: Create order in DB (status: pending)
    const order = await db.$transaction(async (tx) => {
      const newOrder = await tx.order.create({
        data: {
          userId: session.user.id,
          status: 'pending',
          subtotal,
          discount,
          shipping,
          tax,
          total,
          shippingAddressId: parsed.data.shippingAddressId,
          idempotencyKey,
          items: {
            create: cart.items.map((item) => ({
              productId: item.productId,
              quantity: item.quantity,
              price: item.product.price,
            })),
          },
        },
      });

      // Reserve stock
      for (const item of cart.items) {
        await tx.product.update({
          where: { id: item.productId },
          data: { stock: { decrement: item.quantity } },
        });
      }

      return newOrder;
    });

    // Store order ID in cookie (for duplicate detection)
    cookieStore.set('pending-order-id', order.id, {
      httpOnly: true,
      maxAge: 60 * 30, // 30 minutes
      path: '/checkout',
    });

    // Step 5: Process payment via Stripe
    let paymentIntent: Stripe.PaymentIntent;

    try {
      paymentIntent = await stripe.paymentIntents.create(
        {
          amount: Math.round(total * 100), // Stripe uses cents
          currency: 'usd',
          payment_method: parsed.data.paymentMethodId,
          confirm: true,
          metadata: { orderId: order.id },
          automatic_payment_methods: {
            enabled: true,
            allow_redirects: 'never',
          },
        },
        { idempotencyKey } // Stripe idempotency key
      );
    } catch (stripeError) {
      // Payment failed — revert stock reservation
      await db.$transaction(async (tx) => {
        for (const item of cart.items) {
          await tx.product.update({
            where: { id: item.productId },
            data: { stock: { increment: item.quantity } },
          });
        }

        await tx.order.update({
          where: { id: order.id },
          data: { status: 'payment_failed' },
        });
      });

      const message = stripeError instanceof Stripe.errors.StripeCardError
        ? stripeError.message
        : 'Payment failed. Please try a different payment method.';

      return { success: false, error: message, code: 'PAYMENT', recoverable: true };
    }

    // Step 6: Finalize order
    if (paymentIntent.status === 'succeeded') {
      await db.$transaction(async (tx) => {
        await tx.order.update({
          where: { id: order.id },
          data: {
            status: 'completed',
            stripePaymentIntentId: paymentIntent.id,
            paidAt: new Date(),
          },
        });

        // Clear cart
        await tx.cartItem.deleteMany({ where: { cartId: cart.id } });
      });

      // Clean up cookie
      cookieStore.delete('pending-order-id');

      // Revalidate caches
      revalidateTag('cart');
      revalidateTag(`user-orders-${session.user.id}`);
      revalidatePath('/cart');

      return { success: true, orderId: order.id };
    }

    return {
      success: false,
      error: 'Payment requires additional authentication.',
      code: 'REQUIRES_ACTION',
      recoverable: true,
    };
  } catch (error) {
    console.error('[Checkout Error]', error);
    return {
      success: false,
      error: 'An unexpected error occurred. Your card was not charged.',
      code: 'INTERNAL',
      recoverable: true,
    };
  }
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│              CHECKOUT FLOW STATE MACHINE                          │
│                                                                   │
│  ┌──────┐     ┌────────┐     ┌──────────┐     ┌──────────────┐  │
│  │ CART │────►│VALIDATE│────►│ CREATE   │────►│ PROCESS      │  │
│  │      │     │ INPUT  │     │ ORDER    │     │ PAYMENT      │  │
│  └──────┘     └────┬───┘     │ (pending)│     └──────┬───────┘  │
│                    │ ✗       └──────────┘            │           │
│                    ▼                            ┌────┴────┐      │
│               [SHOW ERROR]                      │         │      │
│                                           SUCCESS    FAILURE     │
│                                                │         │       │
│                                                ▼         ▼       │
│                                          ┌──────────┐ ┌────────┐│
│                                          │COMPLETED │ │REVERT  ││
│                                          │Clear cart│ │stock   ││
│                                          │Redirect  │ │Mark    ││
│                                          └──────────┘ │failed  ││
│                                                       └────────┘│
│  IDEMPOTENCY GUARDS:                                             │
│  • Cookie: pending-order-id prevents duplicate form submissions  │
│  • Stripe: idempotencyKey prevents duplicate charges             │
│  • DB: order.idempotencyKey prevents duplicate orders            │
└──────────────────────────────────────────────────────────────────┘
```

---

## Q18. How do you test Server Actions in isolation and integration? (Advanced)

**Scenario:** You need to write comprehensive tests for your Server Actions — unit tests for validation logic, integration tests with the database, and end-to-end tests for the full form submission flow.

**Answer:**

```typescript
// __tests__/actions/user.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock next/cache before importing the action
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
  revalidateTag: vi.fn(),
}));

vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}));

// Mock auth
vi.mock('@/lib/auth', () => ({
  auth: vi.fn(),
}));

// Mock db
vi.mock('@/lib/db', () => ({
  db: {
    user: {
      update: vi.fn(),
      findUnique: vi.fn(),
    },
    auditLog: {
      create: vi.fn(),
    },
  },
}));

import { updateProfile, type ProfileUpdateResult } from '@/app/actions/user';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { revalidatePath, revalidateTag } from 'next/cache';

describe('updateProfile Server Action', () => {
  const mockUser = {
    id: 'user-123',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'user',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (auth as ReturnType<typeof vi.fn>).mockResolvedValue({
      user: mockUser,
    });
  });

  it('should update user profile with valid data', async () => {
    (db.user.update as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...mockUser,
      name: 'Jane Doe',
    });

    const formData = new FormData();
    formData.set('name', 'Jane Doe');
    formData.set('bio', 'Software Engineer');

    const prevState: ProfileUpdateResult = { success: false, message: '' };
    const result = await updateProfile(prevState, formData);

    expect(result.success).toBe(true);
    expect(db.user.update).toHaveBeenCalledWith({
      where: { id: 'user-123' },
      data: expect.objectContaining({ name: 'Jane Doe' }),
    });
    expect(revalidatePath).toHaveBeenCalledWith('/profile');
    expect(revalidateTag).toHaveBeenCalledWith('user-user-123');
  });

  it('should return validation errors for invalid input', async () => {
    const formData = new FormData();
    formData.set('name', ''); // Empty name — should fail validation
    formData.set('bio', 'x'.repeat(1001)); // Too long

    const prevState: ProfileUpdateResult = { success: false, message: '' };
    const result = await updateProfile(prevState, formData);

    expect(result.success).toBe(false);
    expect(result.errors?.name).toBeDefined();
    expect(db.user.update).not.toHaveBeenCalled();
  });

  it('should return error when not authenticated', async () => {
    (auth as ReturnType<typeof vi.fn>).mockResolvedValue(null);

    const formData = new FormData();
    formData.set('name', 'Test');

    const prevState: ProfileUpdateResult = { success: false, message: '' };
    const result = await updateProfile(prevState, formData);

    expect(result.success).toBe(false);
    expect(result.message).toContain('sign in');
  });

  it('should handle database errors gracefully', async () => {
    (db.user.update as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error('Connection timeout')
    );

    const formData = new FormData();
    formData.set('name', 'Jane Doe');

    const prevState: ProfileUpdateResult = { success: false, message: '' };
    const result = await updateProfile(prevState, formData);

    expect(result.success).toBe(false);
    expect(result.message).toContain('unexpected error');
  });
});
```

```typescript
// __tests__/actions/checkout.integration.test.ts
// Integration test with real database (test DB)
import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { db } from '@/lib/db';

describe('Checkout Server Action (Integration)', () => {
  let testUserId: string;
  let testProductId: string;
  let testCartId: string;

  beforeAll(async () => {
    // Seed test data
    const user = await db.user.create({
      data: { email: 'test@example.com', name: 'Test User' },
    });
    testUserId = user.id;

    const product = await db.product.create({
      data: { name: 'Test Product', price: 29.99, stock: 10, sku: 'TEST-001' },
    });
    testProductId = product.id;

    const cart = await db.cart.create({
      data: {
        userId: user.id,
        items: {
          create: { productId: product.id, quantity: 2 },
        },
      },
    });
    testCartId = cart.id;
  });

  afterAll(async () => {
    // Cleanup
    await db.cartItem.deleteMany({ where: { cartId: testCartId } });
    await db.cart.delete({ where: { id: testCartId } });
    await db.product.delete({ where: { id: testProductId } });
    await db.user.delete({ where: { id: testUserId } });
  });

  it('should reserve stock when order is created', async () => {
    const productBefore = await db.product.findUnique({
      where: { id: testProductId },
    });
    expect(productBefore?.stock).toBe(10);

    // Simulate order creation (stock reservation)
    await db.$transaction(async (tx) => {
      await tx.product.update({
        where: { id: testProductId },
        data: { stock: { decrement: 2 } },
      });
    });

    const productAfter = await db.product.findUnique({
      where: { id: testProductId },
    });
    expect(productAfter?.stock).toBe(8);

    // Restore
    await db.product.update({
      where: { id: testProductId },
      data: { stock: 10 },
    });
  });
});
```

---

## Q19. How do you implement Server Actions that interact with external queues for long-running background jobs? (Advanced)

**Scenario:** Some mutations trigger expensive operations (video transcoding, PDF generation, email campaigns) that can't complete within a Server Action's timeout. You need to queue these jobs and update the UI when they finish.

**Answer:**

```typescript
// lib/queue/index.ts
import { Redis } from '@upstash/redis';
import { Client as QstashClient } from '@upstash/qstash';

const qstash = new QstashClient({
  token: process.env.QSTASH_TOKEN!,
});

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_URL!,
  token: process.env.UPSTASH_REDIS_TOKEN!,
});

export type JobStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface Job {
  id: string;
  type: string;
  payload: Record<string, unknown>;
  status: JobStatus;
  progress: number;
  result?: unknown;
  error?: string;
  createdAt: number;
  updatedAt: number;
}

export async function enqueueJob(
  type: string,
  payload: Record<string, unknown>
): Promise<string> {
  const jobId = crypto.randomUUID();

  const job: Job = {
    id: jobId,
    type,
    payload,
    status: 'queued',
    progress: 0,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  // Store job state in Redis
  await redis.set(`job:${jobId}`, JSON.stringify(job), { ex: 86400 }); // 24h TTL

  // Enqueue via QStash (delivers to our API route)
  await qstash.publishJSON({
    url: `${process.env.SITE_URL}/api/jobs/process`,
    body: { jobId, type, payload },
    retries: 3,
    headers: {
      'x-job-id': jobId,
    },
  });

  return jobId;
}

export async function getJobStatus(jobId: string): Promise<Job | null> {
  const data = await redis.get(`job:${jobId}`);
  return data ? (typeof data === 'string' ? JSON.parse(data) : data) as Job : null;
}

export async function updateJobStatus(
  jobId: string,
  updates: Partial<Job>
): Promise<void> {
  const current = await getJobStatus(jobId);
  if (!current) return;

  const updated: Job = {
    ...current,
    ...updates,
    updatedAt: Date.now(),
  };

  await redis.set(`job:${jobId}`, JSON.stringify(updated), { ex: 86400 });
}
```

```typescript
// app/actions/media.ts
'use server';

import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { enqueueJob, getJobStatus, type Job } from '@/lib/queue';
import { revalidateTag } from 'next/cache';

export type UploadAndProcessResult =
  | { success: true; jobId: string; message: string }
  | { success: false; error: string };

export async function uploadAndProcessVideo(
  _prevState: UploadAndProcessResult,
  formData: FormData
): Promise<UploadAndProcessResult> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, error: 'Unauthorized' };
  }

  const file = formData.get('video') as File;
  const title = formData.get('title') as string;

  if (!file || file.size === 0) {
    return { success: false, error: 'No file provided' };
  }

  if (file.size > 500 * 1024 * 1024) { // 500MB limit
    return { success: false, error: 'File too large. Maximum 500MB.' };
  }

  try {
    // Upload to temporary storage
    const buffer = Buffer.from(await file.arrayBuffer());
    const tempKey = `uploads/temp/${session.user.id}/${crypto.randomUUID()}`;

    // Upload to S3 (simplified)
    await uploadToS3(tempKey, buffer, file.type);

    // Create video record
    const video = await db.video.create({
      data: {
        title,
        userId: session.user.id,
        sourceUrl: `s3://${process.env.S3_BUCKET}/${tempKey}`,
        status: 'processing',
      },
    });

    // Enqueue transcoding job
    const jobId = await enqueueJob('video-transcode', {
      videoId: video.id,
      sourceKey: tempKey,
      userId: session.user.id,
      formats: ['720p', '1080p', '4k'],
    });

    // Link job to video
    await db.video.update({
      where: { id: video.id },
      data: { processingJobId: jobId },
    });

    return {
      success: true,
      jobId,
      message: 'Video uploaded! Transcoding will take a few minutes.',
    };
  } catch (error) {
    console.error('Video upload failed:', error);
    return { success: false, error: 'Upload failed. Please try again.' };
  }
}

// Polling action for job status
export async function checkJobProgress(jobId: string): Promise<Job | null> {
  const session = await auth();
  if (!session?.user) return null;

  const job = await getJobStatus(jobId);

  // If completed, revalidate the videos list
  if (job?.status === 'completed') {
    revalidateTag('user-videos');
  }

  return job;
}

async function uploadToS3(_key: string, _buffer: Buffer, _contentType: string) {
  // S3 upload implementation
}
```

```typescript
// app/api/jobs/process/route.ts
// Background job processor (called by QStash)
import { NextRequest, NextResponse } from 'next/server';
import { verifySignature } from '@upstash/qstash/nextjs';
import { updateJobStatus } from '@/lib/queue';

async function handler(request: NextRequest) {
  const { jobId, type, payload } = await request.json();

  try {
    await updateJobStatus(jobId, { status: 'processing', progress: 0 });

    switch (type) {
      case 'video-transcode':
        await processVideoTranscode(jobId, payload);
        break;
      case 'pdf-generate':
        await processPdfGeneration(jobId, payload);
        break;
      case 'email-campaign':
        await processEmailCampaign(jobId, payload);
        break;
      default:
        throw new Error(`Unknown job type: ${type}`);
    }

    await updateJobStatus(jobId, { status: 'completed', progress: 100 });

    return NextResponse.json({ success: true });
  } catch (error) {
    await updateJobStatus(jobId, {
      status: 'failed',
      error: error instanceof Error ? error.message : 'Unknown error',
    });

    return NextResponse.json({ error: 'Job failed' }, { status: 500 });
  }
}

async function processVideoTranscode(
  jobId: string,
  payload: Record<string, unknown>
) {
  const formats = payload.formats as string[];

  for (let i = 0; i < formats.length; i++) {
    await updateJobStatus(jobId, {
      progress: Math.round(((i + 1) / formats.length) * 100),
    });

    // Transcoding logic per format
    await transcodeVideo(
      payload.sourceKey as string,
      formats[i],
      payload.videoId as string
    );
  }
}

async function transcodeVideo(_sourceKey: string, _format: string, _videoId: string) {
  // FFmpeg transcoding via AWS MediaConvert, etc.
}
async function processPdfGeneration(_jobId: string, _payload: Record<string, unknown>) {}
async function processEmailCampaign(_jobId: string, _payload: Record<string, unknown>) {}

export const POST = verifySignature(handler);
```

```typescript
// components/VideoUploadWithProgress.tsx
'use client';

import { useActionState, useEffect, useState, useRef } from 'react';
import { uploadAndProcessVideo, checkJobProgress, type UploadAndProcessResult } from '@/app/actions/media';
import type { Job } from '@/lib/queue';

export function VideoUpload() {
  const [state, formAction] = useActionState(uploadAndProcessVideo, {
    success: false,
    error: '',
  } as UploadAndProcessResult);

  const [job, setJob] = useState<Job | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  // Start polling when job is created
  useEffect(() => {
    if (state.success && state.jobId) {
      pollRef.current = setInterval(async () => {
        const status = await checkJobProgress(state.jobId);
        setJob(status);

        if (status?.status === 'completed' || status?.status === 'failed') {
          clearInterval(pollRef.current);
        }
      }, 2000);
    }

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [state]);

  return (
    <div className="space-y-4">
      <form action={formAction} className="space-y-4">
        <input name="title" placeholder="Video title" required className="w-full border p-2 rounded" />
        <input name="video" type="file" accept="video/*" required />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
          Upload
        </button>
      </form>

      {job && (
        <div className="border rounded p-4">
          <div className="flex justify-between mb-2">
            <span className="font-medium">Processing Video</span>
            <span className="text-sm text-gray-500">{job.status}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${
                job.status === 'failed' ? 'bg-red-500' : 'bg-blue-600'
              }`}
              style={{ width: `${job.progress}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-1">{job.progress}% complete</p>
          {job.status === 'completed' && (
            <p className="text-green-600 text-sm mt-2">Video ready!</p>
          )}
          {job.status === 'failed' && (
            <p className="text-red-600 text-sm mt-2">Failed: {job.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Q20. How do you architect Server Actions for a large-scale application with shared validation, middleware chains, and composable action pipelines? (Advanced)

**Scenario:** Your application has 100+ Server Actions. You need a consistent architecture with shared validation, logging, error handling, analytics, and feature flags — without duplicating code in every action.

**Answer:**

```typescript
// lib/actions/pipeline.ts
// Composable middleware pipeline for Server Actions

type ActionContext = {
  userId: string;
  email: string;
  role: string;
  sessionId: string;
  requestId: string;
  startTime: number;
  metadata: Record<string, unknown>;
};

type MiddlewareResult =
  | { continue: true; ctx: ActionContext }
  | { continue: false; error: ActionResponse<never> };

type ActionResponse<T> =
  | { success: true; data: T }
  | { success: false; error: string; code: string };

type Middleware = (ctx: ActionContext) => Promise<MiddlewareResult>;

type ActionHandler<TInput, TOutput> = (
  input: TInput,
  ctx: ActionContext
) => Promise<TOutput>;

class ActionPipeline<TInput, TOutput> {
  private middlewares: Middleware[] = [];
  private handler: ActionHandler<TInput, TOutput>;
  private inputValidator?: (input: unknown) => { success: boolean; data?: TInput; error?: string };

  constructor(handler: ActionHandler<TInput, TOutput>) {
    this.handler = handler;
  }

  use(middleware: Middleware): ActionPipeline<TInput, TOutput> {
    this.middlewares.push(middleware);
    return this;
  }

  validate(
    validator: (input: unknown) => { success: boolean; data?: TInput; error?: string }
  ): ActionPipeline<TInput, TOutput> {
    this.inputValidator = validator;
    return this;
  }

  build(): (input: TInput) => Promise<ActionResponse<TOutput>> {
    return async (rawInput: TInput): Promise<ActionResponse<TOutput>> => {
      const requestId = crypto.randomUUID().slice(0, 8);
      const startTime = Date.now();

      let ctx: ActionContext = {
        userId: '',
        email: '',
        role: '',
        sessionId: '',
        requestId,
        startTime,
        metadata: {},
      };

      try {
        // Run middleware chain
        for (const middleware of this.middlewares) {
          const result = await middleware(ctx);
          if (!result.continue) {
            return result.error;
          }
          ctx = result.ctx;
        }

        // Validate input
        if (this.inputValidator) {
          const validation = this.inputValidator(rawInput);
          if (!validation.success) {
            return { success: false, error: validation.error!, code: 'VALIDATION' };
          }
          rawInput = validation.data as TInput;
        }

        // Execute handler
        const result = await this.handler(rawInput, ctx);

        // Log success
        const duration = Date.now() - startTime;
        console.log(`[Action:${requestId}] Success in ${duration}ms`);

        return { success: true, data: result };
      } catch (error) {
        const duration = Date.now() - startTime;
        console.error(`[Action:${requestId}] Failed in ${duration}ms:`, error);

        return {
          success: false,
          error: error instanceof Error ? error.message : 'An error occurred',
          code: 'INTERNAL',
        };
      }
    };
  }
}

// Factory function
export function createAction<TInput, TOutput>(
  handler: ActionHandler<TInput, TOutput>
) {
  return new ActionPipeline(handler);
}
```

```typescript
// lib/actions/middleware.ts
// Reusable middleware functions

import { auth } from '@/lib/auth';
import { checkRateLimit } from '@/lib/rate-limit';
import { db } from '@/lib/db';

type ActionContext = {
  userId: string;
  email: string;
  role: string;
  sessionId: string;
  requestId: string;
  startTime: number;
  metadata: Record<string, unknown>;
};

type MiddlewareResult =
  | { continue: true; ctx: ActionContext }
  | { continue: false; error: { success: false; error: string; code: string } };

// Authentication middleware
export async function withAuth(ctx: ActionContext): Promise<MiddlewareResult> {
  const session = await auth();

  if (!session?.user) {
    return {
      continue: false,
      error: { success: false, error: 'Authentication required', code: 'UNAUTHORIZED' },
    };
  }

  return {
    continue: true,
    ctx: {
      ...ctx,
      userId: session.user.id,
      email: session.user.email!,
      role: session.user.role as string,
      sessionId: session.sessionId ?? '',
    },
  };
}

// Role check middleware factory
export function withRole(minimumRole: string) {
  const hierarchy: Record<string, number> = { user: 0, admin: 1, superadmin: 2 };

  return async (ctx: ActionContext): Promise<MiddlewareResult> => {
    if ((hierarchy[ctx.role] ?? 0) < (hierarchy[minimumRole] ?? 0)) {
      return {
        continue: false,
        error: { success: false, error: 'Insufficient permissions', code: 'FORBIDDEN' },
      };
    }
    return { continue: true, ctx };
  };
}

// Rate limiting middleware factory
export function withRateLimit(tier: string, maxRequests: number = 30) {
  return async (ctx: ActionContext): Promise<MiddlewareResult> => {
    const key = `${tier}:${ctx.userId || 'anonymous'}`;
    const { allowed } = await checkRateLimit(key, maxRequests);

    if (!allowed) {
      return {
        continue: false,
        error: { success: false, error: 'Rate limit exceeded', code: 'RATE_LIMITED' },
      };
    }

    return { continue: true, ctx };
  };
}

// Feature flag middleware
export function withFeatureFlag(flagName: string) {
  return async (ctx: ActionContext): Promise<MiddlewareResult> => {
    const flag = await db.featureFlag.findUnique({
      where: { name: flagName },
    });

    if (!flag?.enabled) {
      return {
        continue: false,
        error: { success: false, error: 'This feature is not available yet', code: 'FEATURE_DISABLED' },
      };
    }

    ctx.metadata[`flag:${flagName}`] = true;
    return { continue: true, ctx };
  };
}

// Audit logging middleware
export function withAuditLog(actionName: string) {
  return async (ctx: ActionContext): Promise<MiddlewareResult> => {
    ctx.metadata.auditAction = actionName;

    // Audit log will be written after the action completes (in the handler)
    return { continue: true, ctx };
  };
}
```

```typescript
// app/actions/projects.ts
'use server';

import { z } from 'zod';
import { createAction } from '@/lib/actions/pipeline';
import { withAuth, withRole, withRateLimit, withFeatureFlag, withAuditLog } from '@/lib/actions/middleware';
import { revalidateTag } from 'next/cache';
import { db } from '@/lib/db';

// Schema definitions
const createProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  visibility: z.enum(['public', 'private']),
  templateId: z.string().uuid().optional(),
});

const deleteProjectSchema = z.object({
  projectId: z.string().uuid(),
  confirmName: z.string(),
});

// Action: Create Project
// Middleware: Auth → Rate Limit → Feature Flag → Handler
export const createProject = createAction(
  async (input: z.infer<typeof createProjectSchema>, ctx) => {
    const project = await db.project.create({
      data: {
        name: input.name,
        description: input.description ?? '',
        visibility: input.visibility,
        ownerId: ctx.userId,
      },
    });

    if (input.templateId) {
      await applyTemplate(project.id, input.templateId);
    }

    revalidateTag('projects');
    revalidateTag(`user-projects-${ctx.userId}`);

    return { id: project.id, name: project.name };
  }
)
  .use(withAuth)
  .use(withRateLimit('create-project', 10))
  .use(withFeatureFlag('projects-v2'))
  .validate((input) => {
    const result = createProjectSchema.safeParse(input);
    return result.success
      ? { success: true, data: result.data }
      : { success: false, error: result.error.errors[0]?.message || 'Invalid input' };
  })
  .build();

// Action: Delete Project (Admin only)
// Middleware: Auth → Admin Role → Rate Limit → Audit Log → Handler
export const deleteProject = createAction(
  async (input: z.infer<typeof deleteProjectSchema>, ctx) => {
    const project = await db.project.findUnique({
      where: { id: input.projectId },
    });

    if (!project) throw new Error('Project not found');

    if (project.name !== input.confirmName) {
      throw new Error('Project name does not match. Deletion cancelled.');
    }

    await db.project.delete({ where: { id: input.projectId } });

    await db.auditLog.create({
      data: {
        action: 'DELETE_PROJECT',
        performedBy: ctx.userId,
        resourceId: input.projectId,
        details: JSON.stringify({ projectName: project.name }),
      },
    });

    revalidateTag('projects');

    return { deleted: true };
  }
)
  .use(withAuth)
  .use(withRole('admin'))
  .use(withRateLimit('delete-project', 5))
  .use(withAuditLog('delete-project'))
  .validate((input) => {
    const result = deleteProjectSchema.safeParse(input);
    return result.success
      ? { success: true, data: result.data }
      : { success: false, error: result.error.errors[0]?.message || 'Invalid input' };
  })
  .build();

async function applyTemplate(_projectId: string, _templateId: string) {
  // Template application logic
}
```

```
┌──────────────────────────────────────────────────────────────────┐
│         SERVER ACTION ARCHITECTURE (100+ Actions)                 │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    ACTION PIPELINE                           │ │
│  │                                                              │ │
│  │  Input ──► [Middleware Chain] ──► [Validator] ──► [Handler]  │ │
│  │                                                              │ │
│  │  Middleware Library:                                          │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬────────────┐ │ │
│  │  │  withAuth │ withRole │withRate  │withFeature│withAudit  │ │ │
│  │  │          │          │Limit     │Flag       │Log        │ │ │
│  │  └──────────┴──────────┴──────────┴──────────┴────────────┘ │ │
│  │                                                              │ │
│  │  Composable: action.use(withAuth).use(withRole('admin'))    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SHARED UTILITIES                           │ │
│  │  ┌────────────┬───────────┬──────────┬───────────────────┐  │ │
│  │  │ Zod Schemas│ Error     │ Response │ Type Definitions   │  │ │
│  │  │ (shared)   │ Handling  │ Types    │ (shared)           │  │ │
│  │  └────────────┴───────────┴──────────┴───────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  File Organization:                                               │
│  app/actions/                                                     │
│  ├── projects.ts    (createProject, deleteProject, ...)           │
│  ├── users.ts       (updateProfile, changePassword, ...)          │
│  ├── billing.ts     (subscribe, cancelPlan, ...)                  │
│  ├── admin.ts       (updateRole, banUser, ...)                    │
│  └── uploads.ts     (uploadFile, uploadAvatar, ...)               │
│                                                                   │
│  lib/actions/                                                     │
│  ├── pipeline.ts    (createAction, ActionPipeline)                │
│  ├── middleware.ts   (withAuth, withRole, withRateLimit, ...)     │
│  └── error-handler.ts (handleActionError, ActionError, ...)       │
└──────────────────────────────────────────────────────────────────┘
```

This architecture provides:
- **Consistency**: Every action goes through the same pipeline.
- **Reusability**: Middleware is shared across actions.
- **Type safety**: Input validation with Zod, typed responses.
- **Observability**: Built-in logging, audit trails, analytics.
- **Security**: Auth, RBAC, rate limiting as composable layers.
- **Maintainability**: New actions are ~20 lines of business logic.

---

*End of Server Actions & Mutations — 20 Questions*
