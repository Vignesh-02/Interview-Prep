# 13. Authentication & Authorization

## Topic Introduction

**Authentication** (AuthN) verifies *who* a user is. **Authorization** (AuthZ) determines *what* they can access. In Next.js 15/16 with the App Router, auth is deeply integrated into the server-first architecture — you can protect routes in middleware, Server Components, Server Actions, and Route Handlers.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Next.js Auth Architecture                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Browser Request                                                    │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐   No token?   ┌──────────────┐                       │
│  │Middleware │──────────────▶│ /login page  │                       │
│  │(Edge)    │               └──────────────┘                       │
│  └────┬─────┘                                                       │
│       │ Valid token                                                  │
│       ▼                                                             │
│  ┌──────────────────┐                                               │
│  │ Server Component  │──── reads session via cookies()               │
│  │ (page.tsx)        │                                               │
│  └────┬─────────────┘                                               │
│       │                                                             │
│       ├──▶ Server Action ──── validates session before mutation      │
│       │                                                             │
│       └──▶ Route Handler ──── validates Bearer token / session      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Session Storage                            │   │
│  │  ┌─────────┐  ┌──────────────┐  ┌────────────────────────┐  │   │
│  │  │  JWT    │  │  Database     │  │  Encrypted Cookie      │  │   │
│  │  │ (token) │  │  (sessions)  │  │  (iron-session)        │  │   │
│  │  └─────────┘  └──────────────┘  └────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Auth.js v5** (formerly NextAuth.js) is the de-facto auth solution for Next.js, providing:

```tsx
// auth.ts — Auth.js v5 configuration (root of project)
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import Credentials from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/prisma';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    Google({ clientId: process.env.GOOGLE_ID!, clientSecret: process.env.GOOGLE_SECRET! }),
    GitHub({ clientId: process.env.GITHUB_ID!, clientSecret: process.env.GITHUB_SECRET! }),
    Credentials({
      credentials: { email: {}, password: {} },
      authorize: async (credentials) => {
        // custom logic
      },
    }),
  ],
  session: { strategy: 'jwt' },
  pages: { signIn: '/login' },
});
```

**Key cookie security attributes** for production:

| Attribute    | Purpose                                   | Recommended |
|-------------|-------------------------------------------|-------------|
| `httpOnly`  | Prevents JS access (XSS protection)      | `true`      |
| `secure`    | Only sent over HTTPS                      | `true`      |
| `sameSite`  | CSRF protection                           | `lax`       |
| `path`      | Scope of cookie                           | `/`         |
| `maxAge`    | Expiration time                           | 30 days     |

**Why this matters for senior developers**: Auth is the most security-critical feature of any production application. Understanding how Next.js layers auth across middleware, Server Components, Server Actions, and Route Handlers is essential for building secure, performant applications without leaking sensitive data to the client.

---

## Q1. (Beginner) What is the difference between authentication and authorization in a Next.js application?

**Scenario**: A junior developer on your team keeps using "auth" to mean both login and permissions. Explain the distinction with a Next.js example.

**Answer**:

**Authentication** (AuthN) answers "Who are you?" — it verifies identity through credentials (email/password), OAuth (Google, GitHub), or tokens.

**Authorization** (AuthZ) answers "What can you do?" — it checks permissions after identity is established.

```
┌──────────────────────────────────────────────────┐
│              Auth Flow in Next.js                 │
│                                                  │
│  Step 1: Authentication (Who?)                   │
│  ┌─────────┐      ┌───────────┐                  │
│  │  User   │─────▶│  Login    │──▶ JWT/Session   │
│  │ (email) │      │  (verify) │                  │
│  └─────────┘      └───────────┘                  │
│                                                  │
│  Step 2: Authorization (What?)                   │
│  ┌─────────┐      ┌───────────┐                  │
│  │ Session │─────▶│  Check    │──▶ Allow/Deny    │
│  │ (user)  │      │  (role)   │                  │
│  └─────────┘      └───────────┘                  │
└──────────────────────────────────────────────────┘
```

```tsx
// Authentication — verifying identity
// app/api/auth/login/route.ts
import { NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import { SignJWT } from 'jose';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request) {
  const { email, password } = await request.json();

  // Step 1: Find user
  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  }

  // Step 2: Verify password (authentication)
  const isValid = await bcrypt.compare(password, user.passwordHash);
  if (!isValid) {
    return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
  }

  // Step 3: Create JWT
  const token = await new SignJWT({ userId: user.id, role: user.role })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('7d')
    .sign(new TextEncoder().encode(process.env.JWT_SECRET));

  const response = NextResponse.json({ success: true });
  response.cookies.set('auth-token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  });

  return response;
}
```

```tsx
// Authorization — checking permissions
// lib/auth.ts
import { jwtVerify } from 'jose';
import { cookies } from 'next/headers';

export async function getCurrentUser() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  if (!token) return null;

  try {
    const { payload } = await jwtVerify(
      token,
      new TextEncoder().encode(process.env.JWT_SECRET)
    );
    return payload as { userId: string; role: string };
  } catch {
    return null;
  }
}

export async function requireRole(allowedRoles: string[]) {
  const user = await getCurrentUser();
  if (!user) throw new Error('Not authenticated');
  if (!allowedRoles.includes(user.role)) throw new Error('Not authorized');
  return user;
}

// Usage in a Server Component (authorization)
// app/admin/page.tsx
import { requireRole } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function AdminPage() {
  try {
    const user = await requireRole(['admin', 'superadmin']);
    return <div>Welcome, Admin {user.userId}</div>;
  } catch {
    redirect('/login');
  }
}
```

**Key distinction**: Authentication is about *identity verification* (login flow). Authorization is about *permission enforcement* (role checks). Both happen server-side in Next.js for security.

---

## Q2. (Beginner) How do you set up Auth.js v5 (NextAuth) in a Next.js 15 App Router project?

**Scenario**: You need to add Google and GitHub OAuth login to your Next.js 15 application.

**Answer**:

Auth.js v5 is a complete rewrite of NextAuth.js with first-class support for the App Router. Setup involves 4 files:

```
project/
├── auth.ts                    ← Auth configuration
├── app/
│   ├── api/auth/[...nextauth]/
│   │   └── route.ts           ← Route handler for OAuth callbacks
│   ├── login/
│   │   └── page.tsx           ← Login page
│   └── dashboard/
│       └── page.tsx           ← Protected page
├── middleware.ts               ← Protect routes globally
└── .env.local                  ← Secrets
```

**Step 1: Install dependencies**:

```bash
npm install next-auth@5 @auth/prisma-adapter
```

**Step 2: Create auth configuration** (`auth.ts`):

```tsx
// auth.ts — root of project
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/prisma';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
    }),
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID!,
      clientSecret: process.env.AUTH_GITHUB_SECRET!,
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role ?? 'user';
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as string;
        session.user.id = token.id as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
});
```

**Step 3: Create Route Handler**:

```tsx
// app/api/auth/[...nextauth]/route.ts
import { handlers } from '@/auth';

export const { GET, POST } = handlers;
```

**Step 4: Create middleware**:

```tsx
// middleware.ts
import { auth } from './auth';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isOnDashboard = req.nextUrl.pathname.startsWith('/dashboard');

  if (isOnDashboard && !isLoggedIn) {
    return Response.redirect(new URL('/login', req.nextUrl));
  }
});

export const config = {
  matcher: ['/((?!api/auth|_next/static|_next/image|favicon.ico).*)'],
};
```

**Step 5: Create login page**:

```tsx
// app/login/page.tsx
import { signIn } from '@/auth';

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm space-y-4 p-8">
        <h1 className="text-2xl font-bold text-center">Sign In</h1>

        <form
          action={async () => {
            'use server';
            await signIn('google', { redirectTo: '/dashboard' });
          }}
        >
          <button className="w-full rounded-lg bg-white border px-4 py-2 hover:bg-gray-50">
            Sign in with Google
          </button>
        </form>

        <form
          action={async () => {
            'use server';
            await signIn('github', { redirectTo: '/dashboard' });
          }}
        >
          <button className="w-full rounded-lg bg-gray-900 text-white px-4 py-2 hover:bg-gray-800">
            Sign in with GitHub
          </button>
        </form>
      </div>
    </div>
  );
}
```

**Step 6: Use session in Server Component**:

```tsx
// app/dashboard/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user) redirect('/login');

  return (
    <div>
      <h1>Welcome, {session.user.name}</h1>
      <p>Role: {session.user.role}</p>
      <img src={session.user.image ?? ''} alt="Avatar" className="rounded-full w-12 h-12" />
    </div>
  );
}
```

**Environment variables** (`.env.local`):

```env
AUTH_SECRET=your-random-secret-min-32-chars
AUTH_GOOGLE_ID=xxx.apps.googleusercontent.com
AUTH_GOOGLE_SECRET=xxx
AUTH_GITHUB_ID=xxx
AUTH_GITHUB_SECRET=xxx
```

**Production tip**: Use `npx auth secret` to generate `AUTH_SECRET`. Auth.js v5 auto-detects `AUTH_SECRET` from environment.

---

## Q3. (Beginner) What is the difference between JWT-based and session-based authentication in Next.js?

**Scenario**: Your architect asks you to recommend a session strategy for a new SaaS platform. Compare JWT vs database sessions.

**Answer**:

```
┌──────────────── JWT Strategy ────────────────┐
│                                              │
│  Login ──▶ Generate JWT ──▶ Store in Cookie  │
│                                              │
│  Request ──▶ Verify JWT ──▶ Extract User     │
│              (no DB call)                    │
│                                              │
│  Pros: Fast, stateless, works at edge        │
│  Cons: Can't revoke instantly, size limits   │
└──────────────────────────────────────────────┘

┌──────── Database Session Strategy ───────────┐
│                                              │
│  Login ──▶ Create Session Row ──▶ Session ID │
│            in Cookie                         │
│                                              │
│  Request ──▶ Lookup Session ID in DB ──▶     │
│              Get User (DB call each time)    │
│                                              │
│  Pros: Revocable, unlimited data, secure     │
│  Cons: DB latency, requires adapter          │
└──────────────────────────────────────────────┘
```

| Feature | JWT | Database Sessions |
|---------|-----|-------------------|
| Storage | Encoded in cookie | Session ID in cookie, data in DB |
| DB call per request | No | Yes |
| Revocation | Difficult (need blocklist) | Easy (delete row) |
| Edge runtime | Yes | Limited (need edge-compatible DB) |
| Session data size | Limited (~4KB cookie) | Unlimited |
| Default in Auth.js v5 | `strategy: 'jwt'` | `strategy: 'database'` |
| Best for | Stateless APIs, edge | Admin panels, banking apps |

```tsx
// auth.ts — JWT strategy (recommended for most apps)
export const { handlers, auth, signIn, signOut } = NextAuth({
  session: { strategy: 'jwt', maxAge: 30 * 24 * 60 * 60 }, // 30 days
  jwt: { maxAge: 30 * 24 * 60 * 60 },
  providers: [Google({})],
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      if (user) {
        token.role = user.role;
      }
      // Handle session update (e.g., user changes name)
      if (trigger === 'update' && session) {
        token.name = session.name;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.role = token.role as string;
      return session;
    },
  },
});
```

```tsx
// auth.ts — Database session strategy (for high-security apps)
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/prisma';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  session: { strategy: 'database', maxAge: 30 * 24 * 60 * 60 },
  providers: [Google({})],
  // With database strategy, you use the "session" callback differently:
  callbacks: {
    async session({ session, user }) {
      // 'user' comes from DB (not token)
      session.user.role = user.role;
      return session;
    },
  },
});
```

**Production recommendation**: Use **JWT** for most applications — it's faster and works at the edge. Use **database sessions** for financial apps, admin portals, or apps where instant session revocation is a regulatory requirement.

**Hybrid approach** — JWT with a revocation check:

```tsx
callbacks: {
  async jwt({ token }) {
    // Check revocation list (Redis for speed)
    const isRevoked = await redis.get(`revoked:${token.jti}`);
    if (isRevoked) throw new Error('Token revoked');
    return token;
  },
},
```

---

## Q4. (Beginner) How do you protect a page (Server Component) using auth in Next.js 15?

**Scenario**: Your `/dashboard` page should only be visible to authenticated users. Unauthenticated users should be redirected to `/login`.

**Answer**:

There are **three layers** where you can protect pages in Next.js:

```
Layer 1: Middleware (edge)     — redirect before page loads
Layer 2: Layout (server)      — wrap multiple pages
Layer 3: Page (server)        — per-page protection
```

**Approach 1: Protection in the Server Component (page.tsx)**:

```tsx
// app/dashboard/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome back, {session.user.name}!</p>
    </div>
  );
}
```

**Approach 2: Protection in a layout (for a group of pages)**:

```tsx
// app/(protected)/layout.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';

export default async function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div>
      <nav>
        <span>Logged in as {session.user.email}</span>
        <form
          action={async () => {
            'use server';
            const { signOut } = await import('@/auth');
            await signOut({ redirectTo: '/' });
          }}
        >
          <button>Sign Out</button>
        </form>
      </nav>
      {children}
    </div>
  );
}
```

**Approach 3: Middleware (recommended primary layer)**:

```tsx
// middleware.ts
import { auth } from './auth';
import { NextResponse } from 'next/server';

const protectedRoutes = ['/dashboard', '/settings', '/admin'];
const authRoutes = ['/login', '/register'];

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isLoggedIn = !!req.auth;

  // Redirect unauthenticated users away from protected routes
  if (protectedRoutes.some((route) => pathname.startsWith(route)) && !isLoggedIn) {
    const loginUrl = new URL('/login', req.nextUrl);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect authenticated users away from auth pages
  if (authRoutes.some((route) => pathname.startsWith(route)) && isLoggedIn) {
    return NextResponse.redirect(new URL('/dashboard', req.nextUrl));
  }
});

export const config = {
  matcher: ['/((?!api/auth|_next/static|_next/image|favicon.ico).*)'],
};
```

**Production best practice**: Use **middleware as the first gate** (fast, runs at the edge, prevents unnecessary server load) and **Server Component checks as the second gate** (defense-in-depth). Never rely solely on Client Component checks — they can be bypassed.

---

## Q5. (Beginner) How do you access the current user session in both Server and Client Components?

**Scenario**: You need to display the user's name in a server-rendered header and also conditionally render UI in a Client Component.

**Answer**:

**In a Server Component** — use `auth()` directly:

```tsx
// app/components/ServerHeader.tsx (Server Component — default)
import { auth } from '@/auth';

export default async function ServerHeader() {
  const session = await auth();

  return (
    <header className="flex items-center justify-between p-4 border-b">
      <h1 className="text-xl font-bold">My App</h1>
      {session?.user ? (
        <div className="flex items-center gap-2">
          <img
            src={session.user.image ?? '/default-avatar.png'}
            alt={session.user.name ?? 'User'}
            className="w-8 h-8 rounded-full"
          />
          <span>{session.user.name}</span>
        </div>
      ) : (
        <a href="/login" className="text-blue-600 hover:underline">Sign In</a>
      )}
    </header>
  );
}
```

**In a Client Component** — use the `SessionProvider` and `useSession` hook:

```tsx
// app/providers.tsx
'use client';

import { SessionProvider } from 'next-auth/react';

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
```

```tsx
// app/layout.tsx
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

```tsx
// app/components/UserMenu.tsx
'use client';

import { useSession, signOut } from 'next-auth/react';

export function UserMenu() {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return <div className="h-8 w-8 animate-pulse rounded-full bg-gray-200" />;
  }

  if (!session?.user) {
    return <a href="/login">Sign In</a>;
  }

  return (
    <div className="relative">
      <button className="flex items-center gap-2">
        <img
          src={session.user.image ?? '/default-avatar.png'}
          alt="Avatar"
          className="w-8 h-8 rounded-full"
        />
        <span>{session.user.name}</span>
      </button>
      <button
        onClick={() => signOut({ callbackUrl: '/' })}
        className="text-red-600 text-sm"
      >
        Sign Out
      </button>
    </div>
  );
}
```

| Context | Method | Notes |
|---------|--------|-------|
| Server Component | `const session = await auth()` | No extra providers needed |
| Client Component | `useSession()` hook | Requires `SessionProvider` |
| Server Action | `const session = await auth()` | Same as Server Component |
| Route Handler | `const session = await auth()` | Same as Server Component |
| Middleware | `req.auth` | Via `auth()` wrapper |

**Important**: The `auth()` function in Server Components reads the session from the cookie on each request — it's **not cached** by default, which is correct for auth (you always want fresh auth state). Auth.js v5 uses the `next-auth.session-token` cookie automatically.

---

## Q6. (Intermediate) How do you implement role-based access control (RBAC) across middleware, Server Components, and Server Actions?

**Scenario**: Your SaaS app has three roles — `user`, `admin`, and `superadmin`. Different routes and actions require different roles.

**Answer**:

A production RBAC system has **three layers**: middleware for route protection, Server Components for UI rendering, and Server Actions for mutation authorization.

```
┌──────────────────────────────────────────────┐
│              RBAC Architecture               │
│                                              │
│  ┌─────────┐   ┌──────────┐  ┌───────────┐  │
│  │  user   │   │  admin   │  │ superadmin│  │
│  └────┬────┘   └────┬─────┘  └─────┬─────┘  │
│       │             │              │         │
│       ▼             ▼              ▼         │
│  /dashboard    /dashboard      /dashboard    │
│  /settings     /settings       /settings     │
│                /admin          /admin         │
│                /admin/users    /admin/users   │
│                                /admin/billing │
│                                /admin/system  │
└──────────────────────────────────────────────┘
```

**Step 1: Define permissions**:

```tsx
// lib/permissions.ts
export type Role = 'user' | 'admin' | 'superadmin';

export type Permission =
  | 'dashboard:view'
  | 'settings:view'
  | 'settings:edit'
  | 'admin:view'
  | 'users:manage'
  | 'billing:manage'
  | 'system:manage';

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  user: ['dashboard:view', 'settings:view', 'settings:edit'],
  admin: [
    'dashboard:view',
    'settings:view',
    'settings:edit',
    'admin:view',
    'users:manage',
  ],
  superadmin: [
    'dashboard:view',
    'settings:view',
    'settings:edit',
    'admin:view',
    'users:manage',
    'billing:manage',
    'system:manage',
  ],
};

export function hasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role]?.includes(permission) ?? false;
}

export function hasAnyPermission(role: Role, permissions: Permission[]): boolean {
  return permissions.some((p) => hasPermission(role, p));
}

// Route-to-permission mapping
export const ROUTE_PERMISSIONS: Record<string, Permission> = {
  '/dashboard': 'dashboard:view',
  '/settings': 'settings:view',
  '/admin': 'admin:view',
  '/admin/users': 'users:manage',
  '/admin/billing': 'billing:manage',
  '/admin/system': 'system:manage',
};
```

**Step 2: Enforce in middleware**:

```tsx
// middleware.ts
import { auth } from './auth';
import { NextResponse } from 'next/server';
import { ROUTE_PERMISSIONS, hasPermission, type Role } from '@/lib/permissions';

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const user = req.auth?.user;

  // Check if route requires a permission
  const requiredPermission = Object.entries(ROUTE_PERMISSIONS)
    .sort(([a], [b]) => b.length - a.length) // longest match first
    .find(([route]) => pathname.startsWith(route));

  if (requiredPermission) {
    const [, permission] = requiredPermission;

    if (!user) {
      return NextResponse.redirect(new URL('/login', req.nextUrl));
    }

    if (!hasPermission(user.role as Role, permission)) {
      return NextResponse.redirect(new URL('/unauthorized', req.nextUrl));
    }
  }
});

export const config = {
  matcher: ['/((?!api/auth|_next/static|_next/image|favicon.ico).*)'],
};
```

**Step 3: Enforce in Server Components (UI-level)**:

```tsx
// app/admin/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import { hasPermission, type Role } from '@/lib/permissions';

export default async function AdminPage() {
  const session = await auth();
  if (!session?.user) redirect('/login');

  const role = session.user.role as Role;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Admin Panel</h1>

      <div className="grid grid-cols-3 gap-4 mt-6">
        {hasPermission(role, 'users:manage') && (
          <a href="/admin/users" className="p-4 border rounded-lg hover:bg-gray-50">
            <h2 className="font-semibold">User Management</h2>
            <p className="text-sm text-gray-500">Manage user accounts</p>
          </a>
        )}

        {hasPermission(role, 'billing:manage') && (
          <a href="/admin/billing" className="p-4 border rounded-lg hover:bg-gray-50">
            <h2 className="font-semibold">Billing</h2>
            <p className="text-sm text-gray-500">Manage subscriptions</p>
          </a>
        )}

        {hasPermission(role, 'system:manage') && (
          <a href="/admin/system" className="p-4 border rounded-lg hover:bg-gray-50">
            <h2 className="font-semibold">System Settings</h2>
            <p className="text-sm text-gray-500">Configure application</p>
          </a>
        )}
      </div>
    </div>
  );
}
```

**Step 4: Enforce in Server Actions (mutation-level)**:

```tsx
// app/admin/users/actions.ts
'use server';

import { auth } from '@/auth';
import { hasPermission, type Role } from '@/lib/permissions';
import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';

export async function deleteUser(userId: string) {
  const session = await auth();
  if (!session?.user) throw new Error('Not authenticated');

  const role = session.user.role as Role;
  if (!hasPermission(role, 'users:manage')) {
    throw new Error('Insufficient permissions');
  }

  // Prevent self-deletion
  if (userId === session.user.id) {
    throw new Error('Cannot delete your own account');
  }

  await prisma.user.delete({ where: { id: userId } });
  revalidatePath('/admin/users');
}

export async function changeUserRole(userId: string, newRole: Role) {
  const session = await auth();
  if (!session?.user) throw new Error('Not authenticated');

  const role = session.user.role as Role;

  // Only superadmin can promote to admin or superadmin
  if (['admin', 'superadmin'].includes(newRole) && role !== 'superadmin') {
    throw new Error('Only superadmins can assign elevated roles');
  }

  await prisma.user.update({
    where: { id: userId },
    data: { role: newRole },
  });

  revalidatePath('/admin/users');
}
```

**Key principle**: Always enforce permissions in Server Actions and Route Handlers, not just in the UI. The UI controls are for UX (hiding buttons users can't use), but the server-side checks are for **security**.

---

## Q7. (Intermediate) How do you implement a secure credentials-based login (email/password) with Auth.js v5?

**Scenario**: Your enterprise client requires email/password login in addition to OAuth. Implement it securely with password hashing, rate limiting, and proper error handling.

**Answer**:

The Credentials provider in Auth.js v5 requires careful implementation because it bypasses OAuth's built-in security. You must handle password hashing, validation, and rate limiting yourself.

```tsx
// auth.ts
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';
import bcrypt from 'bcryptjs';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({}),
    Credentials({
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        // Validate input
        const parsed = loginSchema.safeParse(credentials);
        if (!parsed.success) return null;

        const { email, password } = parsed.data;

        // Find user
        const user = await prisma.user.findUnique({
          where: { email: email.toLowerCase() },
          select: {
            id: true,
            email: true,
            name: true,
            passwordHash: true,
            role: true,
            emailVerified: true,
            failedLoginAttempts: true,
            lockedUntil: true,
          },
        });

        if (!user || !user.passwordHash) return null;

        // Check account lockout
        if (user.lockedUntil && user.lockedUntil > new Date()) {
          throw new Error('Account locked. Try again later.');
        }

        // Verify password
        const isValid = await bcrypt.compare(password, user.passwordHash);

        if (!isValid) {
          // Increment failed attempts
          const attempts = user.failedLoginAttempts + 1;
          const lockout = attempts >= 5
            ? { lockedUntil: new Date(Date.now() + 15 * 60 * 1000) } // 15 min lockout
            : {};

          await prisma.user.update({
            where: { id: user.id },
            data: { failedLoginAttempts: attempts, ...lockout },
          });
          return null;
        }

        // Check email verification
        if (!user.emailVerified) {
          throw new Error('Please verify your email before signing in.');
        }

        // Reset failed attempts on successful login
        await prisma.user.update({
          where: { id: user.id },
          data: { failedLoginAttempts: 0, lockedUntil: null },
        });

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role,
        };
      },
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.id = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.role = token.role as string;
      session.user.id = token.id as string;
      return session;
    },
  },
  pages: { signIn: '/login', error: '/login' },
});
```

**Registration Server Action**:

```tsx
// app/register/actions.ts
'use server';

import bcrypt from 'bcryptjs';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';
import { redirect } from 'next/navigation';
import { sendVerificationEmail } from '@/lib/email';
import crypto from 'crypto';

const registerSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  password: z
    .string()
    .min(8)
    .regex(/[A-Z]/, 'Must contain uppercase letter')
    .regex(/[0-9]/, 'Must contain a number')
    .regex(/[^A-Za-z0-9]/, 'Must contain a special character'),
});

export async function register(formData: FormData) {
  const parsed = registerSchema.safeParse({
    name: formData.get('name'),
    email: formData.get('email'),
    password: formData.get('password'),
  });

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const { name, email, password } = parsed.data;

  // Check if user already exists
  const existing = await prisma.user.findUnique({
    where: { email: email.toLowerCase() },
  });

  if (existing) {
    return { error: { email: ['An account with this email already exists'] } };
  }

  // Hash password with bcrypt (cost factor 12)
  const passwordHash = await bcrypt.hash(password, 12);

  // Create verification token
  const verificationToken = crypto.randomBytes(32).toString('hex');

  await prisma.user.create({
    data: {
      name,
      email: email.toLowerCase(),
      passwordHash,
      role: 'user',
      verificationToken,
      failedLoginAttempts: 0,
    },
  });

  await sendVerificationEmail(email, verificationToken);

  redirect('/login?message=Check your email to verify your account');
}
```

**Login form with error handling**:

```tsx
// app/login/page.tsx
'use client';

import { signIn } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const message = searchParams.get('message');

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);

    const result = await signIn('credentials', {
      email: formData.get('email'),
      password: formData.get('password'),
      redirect: false,
    });

    setLoading(false);

    if (result?.error) {
      setError('Invalid email or password');
    } else {
      router.push(searchParams.get('callbackUrl') ?? '/dashboard');
      router.refresh();
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-lg">
        <h1 className="text-2xl font-bold text-center mb-6">Sign In</h1>

        {message && (
          <div className="mb-4 p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">
            {message}
          </div>
        )}
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              name="email"
              type="email"
              required
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              name="password"
              type="password"
              required
              minLength={8}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <button
              onClick={() => signIn('google', { callbackUrl: '/dashboard' })}
              className="flex items-center justify-center px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              Google
            </button>
            <button
              onClick={() => signIn('github', { callbackUrl: '/dashboard' })}
              className="flex items-center justify-center px-4 py-2 border rounded-lg hover:bg-gray-50"
            >
              GitHub
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Security checklist for credentials provider**:
- Password hashing with bcrypt (cost 12+)
- Input validation with Zod
- Account lockout after 5 failed attempts
- Email verification before login
- Rate limiting at the API level
- CSRF protection (Auth.js handles this)

---

## Q8. (Intermediate) How do you protect API Route Handlers with authentication and handle different HTTP methods?

**Scenario**: You have a REST API at `/api/users` that supports GET (list users), POST (create user), and DELETE (remove user). Each method requires different authorization levels.

**Answer**:

```tsx
// lib/api-auth.ts — reusable auth wrapper for Route Handlers
import { auth } from '@/auth';
import { NextResponse } from 'next/server';
import { hasPermission, type Role, type Permission } from '@/lib/permissions';

type AuthenticatedHandler = (
  request: Request,
  context: { user: { id: string; role: string; email: string } }
) => Promise<Response>;

export function withAuth(permission: Permission, handler: AuthenticatedHandler) {
  return async (request: Request, routeContext?: unknown) => {
    const session = await auth();

    if (!session?.user) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    if (!hasPermission(session.user.role as Role, permission)) {
      return NextResponse.json(
        { error: 'Insufficient permissions' },
        { status: 403 }
      );
    }

    return handler(request, {
      user: {
        id: session.user.id!,
        role: session.user.role!,
        email: session.user.email!,
      },
    });
  };
}
```

```tsx
// app/api/users/route.ts
import { NextResponse } from 'next/server';
import { withAuth } from '@/lib/api-auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

// GET /api/users — requires dashboard:view
export const GET = withAuth('dashboard:view', async (request, { user }) => {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') ?? '1');
  const limit = parseInt(searchParams.get('limit') ?? '20');
  const search = searchParams.get('search') ?? '';

  const where = search
    ? {
        OR: [
          { name: { contains: search, mode: 'insensitive' as const } },
          { email: { contains: search, mode: 'insensitive' as const } },
        ],
      }
    : {};

  const [users, total] = await Promise.all([
    prisma.user.findMany({
      where,
      select: { id: true, name: true, email: true, role: true, createdAt: true },
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.user.count({ where }),
  ]);

  return NextResponse.json({
    users,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  });
});

// POST /api/users — requires users:manage
const createUserSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  role: z.enum(['user', 'admin']),
});

export const POST = withAuth('users:manage', async (request, { user }) => {
  const body = await request.json();
  const parsed = createUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  // Check if email already exists
  const existing = await prisma.user.findUnique({
    where: { email: parsed.data.email },
  });

  if (existing) {
    return NextResponse.json(
      { error: 'Email already registered' },
      { status: 409 }
    );
  }

  const newUser = await prisma.user.create({
    data: {
      name: parsed.data.name,
      email: parsed.data.email,
      role: parsed.data.role,
    },
    select: { id: true, name: true, email: true, role: true },
  });

  return NextResponse.json(newUser, { status: 201 });
});
```

```tsx
// app/api/users/[id]/route.ts
import { NextResponse } from 'next/server';
import { withAuth } from '@/lib/api-auth';
import { prisma } from '@/lib/prisma';

// DELETE /api/users/:id — requires users:manage
export const DELETE = withAuth('users:manage', async (request, { user }) => {
  const url = new URL(request.url);
  const id = url.pathname.split('/').pop()!;

  // Prevent self-deletion
  if (id === user.id) {
    return NextResponse.json(
      { error: 'Cannot delete your own account' },
      { status: 400 }
    );
  }

  try {
    await prisma.user.delete({ where: { id } });
    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: 'User not found' }, { status: 404 });
  }
});
```

**For external API consumers (Bearer token auth)**:

```tsx
// lib/api-auth.ts — additional Bearer token support
import { jwtVerify } from 'jose';

export async function verifyBearerToken(request: Request) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader?.startsWith('Bearer ')) return null;

  const token = authHeader.slice(7);
  try {
    const { payload } = await jwtVerify(
      token,
      new TextEncoder().encode(process.env.API_SECRET)
    );
    return payload as { userId: string; role: string; scopes: string[] };
  } catch {
    return null;
  }
}
```

**Key patterns**:
1. Use a `withAuth` higher-order function for DRY auth checks
2. Return `401` for unauthenticated, `403` for unauthorized
3. Validate input with Zod before processing
4. Prevent destructive self-operations (deleting own account)
5. Support both session-based and token-based auth for flexibility

---

## Q9. (Intermediate) How do you implement CSRF protection in Next.js Server Actions and Route Handlers?

**Scenario**: A security audit flags that your Server Actions lack explicit CSRF protection. How does Next.js handle this, and when do you need additional protection?

**Answer**:

**Next.js has built-in CSRF protection for Server Actions** through several mechanisms:

```
┌──────────────────────────────────────────────┐
│        CSRF Protection Layers                │
│                                              │
│  1. Origin Header Check                      │
│     └── Server verifies Origin matches host  │
│                                              │
│  2. POST-only                                │
│     └── Server Actions only accept POST      │
│                                              │
│  3. Encrypted Action IDs                     │
│     └── Action references are non-guessable  │
│                                              │
│  4. SameSite Cookie (Lax/Strict)             │
│     └── Browser won't send cookies on cross- │
│         origin form submissions              │
└──────────────────────────────────────────────┘
```

**How Next.js protects Server Actions automatically**:

1. **Origin header validation**: Next.js checks that the `Origin` header of POST requests matches the expected origin. If a cross-site request is detected, it's rejected.

2. **Non-guessable action IDs**: Server Action references are encrypted, so an attacker can't construct valid action payloads.

3. **POST-only**: Server Actions only respond to POST requests, preventing CSRF via `<img>` tags or simple GET links.

**When you need additional CSRF protection**:

For Route Handlers that accept state-changing requests (POST/PUT/DELETE) from forms or JavaScript without Server Actions, you should add CSRF tokens:

```tsx
// lib/csrf.ts
import { cookies } from 'next/headers';
import crypto from 'crypto';

export async function generateCsrfToken(): Promise<string> {
  const token = crypto.randomBytes(32).toString('hex');
  const cookieStore = await cookies();

  cookieStore.set('csrf-token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    path: '/',
    maxAge: 60 * 60, // 1 hour
  });

  return token;
}

export async function validateCsrfToken(requestToken: string): Promise<boolean> {
  const cookieStore = await cookies();
  const cookieToken = cookieStore.get('csrf-token')?.value;

  if (!cookieToken || !requestToken) return false;

  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(cookieToken),
    Buffer.from(requestToken)
  );
}
```

```tsx
// app/api/transfer/route.ts — Route Handler with CSRF protection
import { NextResponse } from 'next/server';
import { validateCsrfToken } from '@/lib/csrf';
import { auth } from '@/auth';

export async function POST(request: Request) {
  const session = await auth();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();

  // Validate CSRF token
  const isValid = await validateCsrfToken(body.csrfToken);
  if (!isValid) {
    return NextResponse.json({ error: 'Invalid CSRF token' }, { status: 403 });
  }

  // Process the transfer...
  return NextResponse.json({ success: true });
}
```

```tsx
// app/transfer/page.tsx — Server Component provides CSRF token
import { generateCsrfToken } from '@/lib/csrf';
import { TransferForm } from './TransferForm';

export default async function TransferPage() {
  const csrfToken = await generateCsrfToken();
  return <TransferForm csrfToken={csrfToken} />;
}
```

```tsx
// app/transfer/TransferForm.tsx
'use client';

export function TransferForm({ csrfToken }: { csrfToken: string }) {
  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    await fetch('/api/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: formData.get('amount'),
        to: formData.get('to'),
        csrfToken,
      }),
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <input name="to" placeholder="Recipient" />
      <input name="amount" type="number" placeholder="Amount" />
      <button type="submit">Transfer</button>
    </form>
  );
}
```

**Production security configuration in `next.config.js`**:

```tsx
// next.config.ts
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ['myapp.com', 'staging.myapp.com'],
      bodySizeLimit: '2mb',
    },
  },
  headers: async () => [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      ],
    },
  ],
};
```

**Summary**: Server Actions have built-in CSRF protection. Add explicit CSRF tokens for Route Handlers that accept mutations from client-side JavaScript. Always use `SameSite: Lax` (or `Strict`) on auth cookies.

---

## Q10. (Intermediate) How do you implement token refresh and session rotation in a Next.js production app?

**Scenario**: Your JWT tokens expire after 15 minutes for security. How do you silently refresh them without forcing users to re-login?

**Answer**:

```
┌─────────────────────────────────────────────────────────┐
│              Token Refresh Flow                          │
│                                                         │
│  Access Token (15 min)  ─── expires ──▶  Use Refresh    │
│                                          Token          │
│                                            │            │
│  Refresh Token (30 days) ◀──── rotated ────┘            │
│       │                                                 │
│       ▼                                                 │
│  New Access Token (15 min)                              │
│  New Refresh Token (30 days) ← rotation prevents reuse  │
└─────────────────────────────────────────────────────────┘
```

**Approach 1: Auth.js v5 JWT rotation (built-in)**:

```tsx
// auth.ts
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
      authorization: {
        params: {
          access_type: 'offline', // Request refresh token
          prompt: 'consent',
        },
      },
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, account }) {
      // Initial sign-in: store tokens
      if (account) {
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: account.expires_at! * 1000, // Convert to ms
        };
      }

      // Token hasn't expired yet
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // Token expired — refresh it
      return await refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.error = token.error as string | undefined;
      return session;
    },
  },
});

async function refreshAccessToken(token: any) {
  try {
    const response = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: process.env.AUTH_GOOGLE_ID!,
        client_secret: process.env.AUTH_GOOGLE_SECRET!,
        grant_type: 'refresh_token',
        refresh_token: token.refreshToken as string,
      }),
    });

    const data = await response.json();

    if (!response.ok) throw data;

    return {
      ...token,
      accessToken: data.access_token,
      accessTokenExpires: Date.now() + data.expires_in * 1000,
      // Rotate refresh token if provider returns a new one
      refreshToken: data.refresh_token ?? token.refreshToken,
    };
  } catch (error) {
    console.error('Token refresh failed:', error);
    return { ...token, error: 'RefreshTokenError' };
  }
}
```

**Handle refresh errors in Client Components**:

```tsx
// app/components/SessionGuard.tsx
'use client';

import { useSession, signIn } from 'next-auth/react';
import { useEffect } from 'react';

export function SessionGuard({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();

  useEffect(() => {
    if (session?.error === 'RefreshTokenError') {
      // Force re-authentication when refresh token fails
      signIn();
    }
  }, [session?.error]);

  return <>{children}</>;
}
```

**Approach 2: Custom JWT with refresh tokens (no Auth.js)**:

```tsx
// lib/tokens.ts
import { SignJWT, jwtVerify } from 'jose';
import { prisma } from '@/lib/prisma';
import crypto from 'crypto';

const ACCESS_SECRET = new TextEncoder().encode(process.env.JWT_SECRET);
const ACCESS_TTL = '15m';
const REFRESH_TTL_DAYS = 30;

export async function createTokenPair(userId: string, role: string) {
  // Short-lived access token
  const accessToken = await new SignJWT({ userId, role })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime(ACCESS_TTL)
    .setIssuedAt()
    .setJti(crypto.randomUUID())
    .sign(ACCESS_SECRET);

  // Long-lived refresh token (stored in DB for revocation)
  const refreshToken = crypto.randomBytes(64).toString('hex');
  const expiresAt = new Date(Date.now() + REFRESH_TTL_DAYS * 24 * 60 * 60 * 1000);

  await prisma.refreshToken.create({
    data: {
      token: refreshToken,
      userId,
      expiresAt,
    },
  });

  return { accessToken, refreshToken, expiresAt };
}

export async function rotateRefreshToken(oldRefreshToken: string) {
  // Find and delete old token (single use)
  const stored = await prisma.refreshToken.findUnique({
    where: { token: oldRefreshToken },
    include: { user: { select: { id: true, role: true } } },
  });

  if (!stored || stored.expiresAt < new Date()) {
    // If token reuse detected, revoke all tokens for this user
    if (stored) {
      await prisma.refreshToken.deleteMany({
        where: { userId: stored.userId },
      });
    }
    throw new Error('Invalid refresh token');
  }

  // Delete used token
  await prisma.refreshToken.delete({ where: { token: oldRefreshToken } });

  // Create new pair
  return createTokenPair(stored.user.id, stored.user.role);
}
```

```tsx
// app/api/auth/refresh/route.ts
import { NextResponse } from 'next/server';
import { rotateRefreshToken } from '@/lib/tokens';

export async function POST(request: Request) {
  const cookieHeader = request.headers.get('cookie') ?? '';
  const refreshToken = cookieHeader
    .split(';')
    .find((c) => c.trim().startsWith('refresh-token='))
    ?.split('=')[1];

  if (!refreshToken) {
    return NextResponse.json({ error: 'No refresh token' }, { status: 401 });
  }

  try {
    const { accessToken, refreshToken: newRefreshToken, expiresAt } =
      await rotateRefreshToken(refreshToken);

    const response = NextResponse.json({ accessToken });

    // Set new refresh token cookie
    response.cookies.set('refresh-token', newRefreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      path: '/api/auth/refresh',
      expires: expiresAt,
    });

    // Set new access token cookie
    response.cookies.set('access-token', accessToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
      maxAge: 15 * 60, // 15 minutes
    });

    return response;
  } catch {
    const response = NextResponse.json({ error: 'Token expired' }, { status: 401 });
    response.cookies.delete('refresh-token');
    response.cookies.delete('access-token');
    return response;
  }
}
```

**Key security practices for token refresh**:
1. **Rotate refresh tokens** — each use creates a new one
2. **Detect token reuse** — if a refresh token is used twice, revoke all tokens (indicates theft)
3. **Short access token TTL** (15 min) — limits damage window
4. **Store refresh tokens in DB** — enables revocation
5. **Set `path` on refresh token cookie** — only sent to `/api/auth/refresh`, reducing exposure

---

## Q11. (Intermediate) How do you implement auth in Server Actions with proper validation and error handling?

**Scenario**: You have a Server Action that updates user profile information. It must validate the session, check permissions, validate input, and handle errors gracefully.

**Answer**:

```tsx
// lib/action-auth.ts — reusable Server Action auth wrapper
import { auth } from '@/auth';
import { type Role, hasPermission, type Permission } from '@/lib/permissions';

type ActionResult<T> =
  | { success: true; data: T }
  | { success: false; error: string; code: 'UNAUTHORIZED' | 'FORBIDDEN' | 'VALIDATION' | 'SERVER_ERROR' };

export function createAuthenticatedAction<TInput, TOutput>(
  permission: Permission,
  handler: (
    input: TInput,
    user: { id: string; role: Role; email: string }
  ) => Promise<TOutput>
) {
  return async (input: TInput): Promise<ActionResult<TOutput>> => {
    try {
      const session = await auth();

      if (!session?.user) {
        return { success: false, error: 'Please sign in to continue', code: 'UNAUTHORIZED' };
      }

      const role = session.user.role as Role;
      if (!hasPermission(role, permission)) {
        return { success: false, error: 'You do not have permission for this action', code: 'FORBIDDEN' };
      }

      const result = await handler(input, {
        id: session.user.id!,
        role,
        email: session.user.email!,
      });

      return { success: true, data: result };
    } catch (error) {
      console.error('Action error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'An unexpected error occurred',
        code: 'SERVER_ERROR',
      };
    }
  };
}
```

```tsx
// app/settings/actions.ts
'use server';

import { z } from 'zod';
import { createAuthenticatedAction } from '@/lib/action-auth';
import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';

const updateProfileSchema = z.object({
  name: z.string().min(2).max(50),
  bio: z.string().max(500).optional(),
  website: z.string().url().optional().or(z.literal('')),
  timezone: z.string(),
});

type UpdateProfileInput = z.infer<typeof updateProfileSchema>;

export const updateProfile = createAuthenticatedAction<UpdateProfileInput, { name: string }>(
  'settings:edit',
  async (input, user) => {
    const parsed = updateProfileSchema.safeParse(input);

    if (!parsed.success) {
      throw new Error(
        parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(', ')
      );
    }

    const updated = await prisma.user.update({
      where: { id: user.id },
      data: {
        name: parsed.data.name,
        bio: parsed.data.bio ?? null,
        website: parsed.data.website || null,
        timezone: parsed.data.timezone,
      },
      select: { name: true },
    });

    revalidatePath('/settings');
    return updated;
  }
);

// Delete account — requires re-authentication
const deleteAccountSchema = z.object({
  confirmEmail: z.string().email(),
  password: z.string().min(1),
});

export const deleteAccount = createAuthenticatedAction<
  z.infer<typeof deleteAccountSchema>,
  { deleted: boolean }
>('settings:edit', async (input, user) => {
  const parsed = deleteAccountSchema.safeParse(input);
  if (!parsed.success) throw new Error('Invalid input');

  // Verify email matches
  if (parsed.data.confirmEmail.toLowerCase() !== user.email.toLowerCase()) {
    throw new Error('Email does not match your account');
  }

  // Verify password
  const dbUser = await prisma.user.findUnique({
    where: { id: user.id },
    select: { passwordHash: true },
  });

  if (!dbUser?.passwordHash) throw new Error('Cannot verify credentials');

  const bcrypt = await import('bcryptjs');
  const isValid = await bcrypt.compare(parsed.data.password, dbUser.passwordHash);
  if (!isValid) throw new Error('Invalid password');

  // Soft delete (mark as deleted, actual deletion in background job)
  await prisma.user.update({
    where: { id: user.id },
    data: { deletedAt: new Date(), email: `deleted-${user.id}@deleted.local` },
  });

  return { deleted: true };
});
```

```tsx
// app/settings/ProfileForm.tsx
'use client';

import { useActionState } from 'react';
import { updateProfile } from './actions';

interface ProfileFormProps {
  initialData: { name: string; bio?: string; website?: string; timezone: string };
}

export function ProfileForm({ initialData }: ProfileFormProps) {
  const [state, formAction, isPending] = useActionState(
    async (_prevState: any, formData: FormData) => {
      const input = {
        name: formData.get('name') as string,
        bio: formData.get('bio') as string,
        website: formData.get('website') as string,
        timezone: formData.get('timezone') as string,
      };

      const result = await updateProfile(input);

      if (result.success) {
        return { status: 'success', message: 'Profile updated!' };
      }

      if (result.code === 'UNAUTHORIZED') {
        window.location.href = '/login';
        return { status: 'error', message: result.error };
      }

      return { status: 'error', message: result.error };
    },
    null
  );

  return (
    <form action={formAction} className="space-y-4 max-w-lg">
      {state?.status === 'success' && (
        <div className="p-3 bg-green-50 text-green-700 rounded-lg">{state.message}</div>
      )}
      {state?.status === 'error' && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg">{state.message}</div>
      )}

      <div>
        <label className="block text-sm font-medium mb-1">Name</label>
        <input
          name="name"
          defaultValue={initialData.name}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Bio</label>
        <textarea
          name="bio"
          defaultValue={initialData.bio}
          rows={3}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Website</label>
        <input
          name="website"
          type="url"
          defaultValue={initialData.website}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Timezone</label>
        <input
          name="timezone"
          defaultValue={initialData.timezone}
          className="w-full px-3 py-2 border rounded-lg"
        />
      </div>

      <button
        type="submit"
        disabled={isPending}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {isPending ? 'Saving...' : 'Save Changes'}
      </button>
    </form>
  );
}
```

**Key patterns**:
1. Centralized auth wrapper for all Server Actions (`createAuthenticatedAction`)
2. Typed return values (`ActionResult<T>`) for consistent error handling
3. Zod validation inside the handler (not on the boundary)
4. Re-authentication for destructive operations (account deletion)
5. Client-side redirect to `/login` when session expires during interaction

---

## Q12. (Intermediate) How do you implement OAuth with custom callback logic and account linking in Auth.js v5?

**Scenario**: A user signs up with email/password and later wants to link their Google account. Also, you need custom logic after OAuth sign-in (e.g., creating a Stripe customer).

**Answer**:

```tsx
// auth.ts — Full configuration with account linking and callbacks
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import Credentials from 'next-auth/providers/credentials';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/prisma';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
      allowDangerousEmailAccountLinking: true, // Enable account linking by email
    }),
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID!,
      clientSecret: process.env.AUTH_GITHUB_SECRET!,
      allowDangerousEmailAccountLinking: true,
    }),
    Credentials({
      credentials: { email: {}, password: {} },
      async authorize(credentials) {
        // ... credentials logic
      },
    }),
  ],
  session: { strategy: 'jwt' },
  events: {
    // Called when a new user is created (first sign-up)
    async createUser({ user }) {
      // Create Stripe customer on first sign-up
      if (user.email) {
        const customer = await stripe.customers.create({
          email: user.email,
          name: user.name ?? undefined,
          metadata: { userId: user.id! },
        });

        await prisma.user.update({
          where: { id: user.id! },
          data: { stripeCustomerId: customer.id },
        });
      }
    },
    // Called when a new OAuth account is linked
    async linkAccount({ user, account }) {
      console.log(`Linked ${account.provider} to user ${user.id}`);

      // Track in analytics
      await prisma.auditLog.create({
        data: {
          userId: user.id!,
          action: 'ACCOUNT_LINKED',
          metadata: { provider: account.provider },
        },
      });
    },
  },
  callbacks: {
    async signIn({ user, account, profile }) {
      // Block sign-in for banned users
      if (user.id) {
        const dbUser = await prisma.user.findUnique({
          where: { id: user.id },
          select: { banned: true },
        });
        if (dbUser?.banned) return false;
      }

      // For Google: only allow verified emails
      if (account?.provider === 'google') {
        return (profile as any)?.email_verified === true;
      }

      return true;
    },
    async jwt({ token, user, account, trigger }) {
      if (user) {
        token.role = user.role ?? 'user';
        token.id = user.id;
      }

      // Fetch fresh user data on session update or first sign-in
      if (trigger === 'signIn' || trigger === 'update') {
        const dbUser = await prisma.user.findUnique({
          where: { id: token.id as string },
          select: { role: true, stripeCustomerId: true, onboardingComplete: true },
        });
        if (dbUser) {
          token.role = dbUser.role;
          token.stripeCustomerId = dbUser.stripeCustomerId;
          token.onboardingComplete = dbUser.onboardingComplete;
        }
      }

      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      session.user.role = token.role as string;
      session.user.stripeCustomerId = token.stripeCustomerId as string;
      session.user.onboardingComplete = token.onboardingComplete as boolean;
      return session;
    },
  },
});
```

**Explicit account linking (user-initiated)**:

```tsx
// app/settings/accounts/page.tsx
import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { redirect } from 'next/navigation';
import { LinkAccountButton } from './LinkAccountButton';

export default async function LinkedAccountsPage() {
  const session = await auth();
  if (!session?.user) redirect('/login');

  const accounts = await prisma.account.findMany({
    where: { userId: session.user.id },
    select: { provider: true, type: true, createdAt: true },
  });

  const linkedProviders = accounts.map((a) => a.provider);

  return (
    <div className="max-w-lg mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Linked Accounts</h1>

      <div className="space-y-4">
        {['google', 'github'].map((provider) => {
          const isLinked = linkedProviders.includes(provider);
          return (
            <div
              key={provider}
              className="flex items-center justify-between p-4 border rounded-lg"
            >
              <div>
                <p className="font-medium capitalize">{provider}</p>
                <p className="text-sm text-gray-500">
                  {isLinked ? 'Connected' : 'Not connected'}
                </p>
              </div>
              {isLinked ? (
                <span className="text-green-600 text-sm font-medium">✓ Linked</span>
              ) : (
                <LinkAccountButton provider={provider} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

```tsx
// app/settings/accounts/LinkAccountButton.tsx
'use client';

import { signIn } from 'next-auth/react';

export function LinkAccountButton({ provider }: { provider: string }) {
  return (
    <button
      onClick={() => signIn(provider, { callbackUrl: '/settings/accounts' })}
      className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      Link {provider}
    </button>
  );
}
```

**Important**: `allowDangerousEmailAccountLinking: true` automatically links accounts with the same email. Use this **only** when you trust all configured providers to return verified emails. For untrusted providers, implement manual account linking with email verification.

---

## Q13. (Advanced) How do you implement multi-tenant authentication with tenant-scoped sessions and data isolation?

**Scenario**: You're building a B2B SaaS platform where each organization (tenant) has separate users, roles, and data. Users can belong to multiple organizations and switch between them.

**Answer**:

```
┌─────────────────────────────────────────────────────────┐
│              Multi-Tenant Auth Architecture              │
│                                                         │
│  User "alice@corp.com"                                  │
│  ├── Tenant: Acme Corp  (role: admin)                   │
│  ├── Tenant: Startup Inc (role: member)                 │
│  └── Tenant: Freelance   (role: owner)                  │
│                                                         │
│  Session contains:                                      │
│  {                                                      │
│    userId: "u_abc",                                     │
│    activeTenantId: "t_acme",                            │
│    tenantRole: "admin",                                 │
│    tenants: [                                           │
│      { id: "t_acme", name: "Acme", role: "admin" },    │
│      { id: "t_startup", name: "Startup", role: "member"}│
│    ]                                                    │
│  }                                                      │
│                                                         │
│  Data isolation:                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Acme DB  │  │Startup DB│  │Freelance │              │
│  │ schema   │  │ schema   │  │ schema   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

**Database schema (Prisma)**:

```prisma
// prisma/schema.prisma
model User {
  id           String       @id @default(cuid())
  email        String       @unique
  name         String?
  passwordHash String?
  memberships  Membership[]
  createdAt    DateTime     @default(now())
}

model Tenant {
  id          String       @id @default(cuid())
  name        String
  slug        String       @unique
  plan        String       @default("free")
  memberships Membership[]
  projects    Project[]
  createdAt   DateTime     @default(now())
}

model Membership {
  id       String   @id @default(cuid())
  userId   String
  tenantId String
  role     String   @default("member") // owner, admin, member, viewer
  user     User     @relation(fields: [userId], references: [id])
  tenant   Tenant   @relation(fields: [tenantId], references: [id])
  
  @@unique([userId, tenantId])
  @@index([tenantId])
}

model Project {
  id       String @id @default(cuid())
  name     String
  tenantId String
  tenant   Tenant @relation(fields: [tenantId], references: [id])
  
  @@index([tenantId])
}
```

**Auth configuration with tenant support**:

```tsx
// auth.ts
import NextAuth from 'next-auth';
import { prisma } from '@/lib/prisma';

export const { handlers, auth, signIn, signOut } = NextAuth({
  // ... providers
  session: { strategy: 'jwt' },
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      if (user) {
        token.id = user.id;

        // Fetch user's tenant memberships
        const memberships = await prisma.membership.findMany({
          where: { userId: user.id! },
          include: { tenant: { select: { id: true, name: true, slug: true } } },
        });

        token.tenants = memberships.map((m) => ({
          id: m.tenant.id,
          name: m.tenant.name,
          slug: m.tenant.slug,
          role: m.role,
        }));

        // Set first tenant as active (or last used from cookie)
        token.activeTenantId = memberships[0]?.tenantId ?? null;
        token.tenantRole = memberships[0]?.role ?? null;
      }

      // Handle tenant switch
      if (trigger === 'update' && session?.activeTenantId) {
        const membership = (token.tenants as any[])?.find(
          (t: any) => t.id === session.activeTenantId
        );
        if (membership) {
          token.activeTenantId = membership.id;
          token.tenantRole = membership.role;
        }
      }

      return token;
    },
    async session({ session, token }) {
      session.user.id = token.id as string;
      session.user.activeTenantId = token.activeTenantId as string;
      session.user.tenantRole = token.tenantRole as string;
      session.user.tenants = token.tenants as any[];
      return session;
    },
  },
});
```

**Middleware with tenant-aware routing**:

```tsx
// middleware.ts
import { auth } from './auth';
import { NextResponse } from 'next/server';

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const user = req.auth?.user;

  // Tenant-scoped routes: /t/[slug]/*
  const tenantMatch = pathname.match(/^\/t\/([^/]+)/);

  if (tenantMatch) {
    const slug = tenantMatch[1];

    if (!user) {
      return NextResponse.redirect(new URL('/login', req.nextUrl));
    }

    // Check if user belongs to this tenant
    const tenant = user.tenants?.find((t: any) => t.slug === slug);
    if (!tenant) {
      return NextResponse.redirect(new URL('/unauthorized', req.nextUrl));
    }

    // Inject tenant context into headers for downstream use
    const headers = new Headers(req.headers);
    headers.set('x-tenant-id', tenant.id);
    headers.set('x-tenant-role', tenant.role);
    headers.set('x-tenant-slug', slug);

    return NextResponse.next({ headers });
  }
});
```

**Tenant context provider**:

```tsx
// lib/tenant.ts
import { auth } from '@/auth';
import { headers } from 'next/headers';
import { cache } from 'react';

export const getTenantContext = cache(async () => {
  const headerStore = await headers();
  const tenantId = headerStore.get('x-tenant-id');
  const tenantRole = headerStore.get('x-tenant-role');
  const tenantSlug = headerStore.get('x-tenant-slug');

  if (!tenantId) {
    // Fallback to session
    const session = await auth();
    return {
      tenantId: session?.user?.activeTenantId ?? null,
      tenantRole: session?.user?.tenantRole ?? null,
      tenantSlug: null,
    };
  }

  return { tenantId, tenantRole, tenantSlug };
});

// Prisma client with tenant scoping
export async function getTenantPrisma() {
  const { tenantId } = await getTenantContext();
  if (!tenantId) throw new Error('No tenant context');

  return {
    // Scoped queries that always filter by tenantId
    projects: {
      findMany: (args?: any) =>
        prisma.project.findMany({ ...args, where: { ...args?.where, tenantId } }),
      create: (args: any) =>
        prisma.project.create({ ...args, data: { ...args.data, tenantId } }),
    },
  };
}
```

**Tenant switcher component**:

```tsx
// app/components/TenantSwitcher.tsx
'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export function TenantSwitcher() {
  const { data: session, update } = useSession();
  const router = useRouter();

  if (!session?.user?.tenants?.length) return null;

  return (
    <select
      value={session.user.activeTenantId ?? ''}
      onChange={async (e) => {
        const tenantId = e.target.value;
        const tenant = session.user.tenants.find((t: any) => t.id === tenantId);

        // Update session with new active tenant
        await update({ activeTenantId: tenantId });

        // Navigate to tenant workspace
        router.push(`/t/${tenant.slug}`);
        router.refresh();
      }}
      className="px-3 py-2 border rounded-lg"
    >
      {session.user.tenants.map((tenant: any) => (
        <option key={tenant.id} value={tenant.id}>
          {tenant.name} ({tenant.role})
        </option>
      ))}
    </select>
  );
}
```

**Key multi-tenant security principles**:
1. **Data isolation**: Every query must include `tenantId` — use a scoped Prisma client
2. **Middleware validation**: Verify tenant membership before the page renders
3. **Session scoping**: Store `activeTenantId` in the JWT so it's available everywhere
4. **Role per tenant**: A user can be admin in one org and viewer in another
5. **Row-level security**: Consider PostgreSQL RLS for database-level isolation

---

## Q14. (Advanced) How do you implement secure cookie management for auth in Next.js with httpOnly, secure, sameSite, and cookie encryption?

**Scenario**: Your security team requires encrypted auth cookies with proper security attributes, cookie rotation, and defense against cookie theft.

**Answer**:

```
┌───────────────────────────────────────────────────┐
│            Cookie Security Attributes             │
│                                                   │
│  ┌─────────────┐  JS: document.cookie = ...       │
│  │  httpOnly   │──▶ BLOCKED (XSS protection)      │
│  └─────────────┘                                  │
│                                                   │
│  ┌─────────────┐  http://site.com                 │
│  │   secure    │──▶ BLOCKED (only HTTPS)          │
│  └─────────────┘                                  │
│                                                   │
│  ┌─────────────┐  Cross-site POST form            │
│  │  sameSite   │──▶ BLOCKED if "strict"           │
│  │  (lax)      │──▶ Allowed for GET navigation    │
│  └─────────────┘                                  │
│                                                   │
│  ┌─────────────┐  Cookie size > 4KB               │
│  │  encrypted  │──▶ Stores minimal data, rest     │
│  │  (iron)     │    encrypted with secret key      │
│  └─────────────┘                                  │
└───────────────────────────────────────────────────┘
```

**Approach 1: Using `iron-session` for encrypted cookies**:

```tsx
// lib/session.ts
import { getIronSession, type SessionOptions } from 'iron-session';
import { cookies } from 'next/headers';

export interface SessionData {
  userId: string;
  role: string;
  tenantId?: string;
  isLoggedIn: boolean;
  csrfToken: string;
  createdAt: number;
  rotatedAt: number;
}

const sessionOptions: SessionOptions = {
  password: process.env.SESSION_SECRET!, // Min 32 characters
  cookieName: '__session',
  cookieOptions: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    maxAge: 60 * 60 * 24 * 7, // 7 days
    path: '/',
  },
};

export async function getSession() {
  const cookieStore = await cookies();
  const session = await getIronSession<SessionData>(cookieStore, sessionOptions);
  return session;
}

export async function createSession(userId: string, role: string) {
  const session = await getSession();
  const crypto = await import('crypto');

  session.userId = userId;
  session.role = role;
  session.isLoggedIn = true;
  session.csrfToken = crypto.randomBytes(32).toString('hex');
  session.createdAt = Date.now();
  session.rotatedAt = Date.now();

  await session.save();
  return session;
}

export async function destroySession() {
  const session = await getSession();
  session.destroy();
}
```

**Session rotation (prevent session fixation)**:

```tsx
// lib/session-rotation.ts
import { getSession } from './session';

const ROTATION_INTERVAL = 15 * 60 * 1000; // 15 minutes

export async function rotateSessionIfNeeded() {
  const session = await getSession();
  if (!session.isLoggedIn) return session;

  const now = Date.now();
  const lastRotated = session.rotatedAt ?? session.createdAt;

  if (now - lastRotated > ROTATION_INTERVAL) {
    // Save current data
    const { userId, role, tenantId, csrfToken, createdAt } = session;

    // Destroy and recreate (new cookie ID)
    session.destroy();

    // Recreate with same data but new rotation timestamp
    const newSession = await getSession();
    newSession.userId = userId;
    newSession.role = role;
    newSession.tenantId = tenantId;
    newSession.csrfToken = csrfToken;
    newSession.isLoggedIn = true;
    newSession.createdAt = createdAt;
    newSession.rotatedAt = now;

    await newSession.save();
    return newSession;
  }

  return session;
}
```

**Use in middleware**:

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { getIronSession } from 'iron-session';
import type { SessionData } from '@/lib/session';

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Read session from request cookies
  const session = await getIronSession<SessionData>(request, response, {
    password: process.env.SESSION_SECRET!,
    cookieName: '__session',
    cookieOptions: {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax' as const,
      path: '/',
    },
  });

  const isProtected = request.nextUrl.pathname.startsWith('/dashboard');

  if (isProtected && !session.isLoggedIn) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Session rotation in middleware
  if (session.isLoggedIn) {
    const now = Date.now();
    if (now - (session.rotatedAt ?? 0) > 15 * 60 * 1000) {
      session.rotatedAt = now;
      await session.save();
    }
  }

  return response;
}
```

**Cookie hardening headers**:

```tsx
// next.config.ts
const securityHeaders = [
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
  },
];

const nextConfig = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};

export default nextConfig;
```

**Cookie theft detection**:

```tsx
// lib/session-fingerprint.ts
import { headers } from 'next/headers';
import crypto from 'crypto';

export async function generateFingerprint(): Promise<string> {
  const headerStore = await headers();
  const userAgent = headerStore.get('user-agent') ?? '';
  const acceptLanguage = headerStore.get('accept-language') ?? '';

  // Create a fingerprint from stable browser attributes
  const raw = `${userAgent}|${acceptLanguage}`;
  return crypto.createHash('sha256').update(raw).digest('hex').slice(0, 16);
}

export async function validateFingerprint(storedFingerprint: string): Promise<boolean> {
  const current = await generateFingerprint();
  return current === storedFingerprint;
}
```

**Key security practices**:
1. **Always `httpOnly: true`** — prevents JavaScript access (XSS protection)
2. **Always `secure: true` in production** — prevents transmission over HTTP
3. **`sameSite: 'lax'`** — prevents CSRF while allowing normal navigation
4. **Encrypt cookie contents** — use `iron-session` or Auth.js built-in encryption
5. **Rotate sessions** — regenerate session ID periodically
6. **Fingerprint binding** — tie session to browser characteristics
7. **HSTS header** — force HTTPS for all future requests

---

## Q15. (Advanced) How do you implement middleware-based auth with complex routing rules, rate limiting, and geo-blocking?

**Scenario**: Your production app needs middleware that handles auth checks, rate limiting (100 req/min per user), geo-blocking (block certain countries), and bot detection — all at the edge.

**Answer**:

```
┌──────────────────────────────────────────────────────────┐
│              Edge Middleware Pipeline                      │
│                                                          │
│  Request ──▶ Geo Check ──▶ Rate Limit ──▶ Bot Check      │
│                  │              │              │           │
│              ┌───▼───┐    ┌────▼────┐    ┌───▼────┐      │
│              │Block  │    │429 Too  │    │Challenge│      │
│              │Country│    │Many Req │    │  Page   │      │
│              └───────┘    └─────────┘    └────────┘      │
│                                                          │
│  ──▶ Auth Check ──▶ Tenant Resolution ──▶ Response        │
│         │                  │                              │
│    ┌────▼────┐       ┌────▼────┐                         │
│    │Redirect │       │Inject   │                         │
│    │to Login │       │Headers  │                         │
│    └─────────┘       └─────────┘                         │
└──────────────────────────────────────────────────────────┘
```

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { auth } from './auth';

// Configuration
const BLOCKED_COUNTRIES = ['RU', 'KP', 'IR']; // Sanctioned countries
const RATE_LIMIT_WINDOW = 60_000; // 1 minute
const RATE_LIMIT_MAX = 100; // requests per window

// In-memory rate limit store (use Redis in production with multiple instances)
const rateLimitStore = new Map<string, { count: number; resetAt: number }>();

function getRateLimitKey(request: NextRequest, userId?: string): string {
  return userId ?? request.headers.get('x-forwarded-for') ?? request.ip ?? 'anonymous';
}

function checkRateLimit(key: string): { allowed: boolean; remaining: number; resetAt: number } {
  const now = Date.now();
  const entry = rateLimitStore.get(key);

  if (!entry || now > entry.resetAt) {
    rateLimitStore.set(key, { count: 1, resetAt: now + RATE_LIMIT_WINDOW });
    return { allowed: true, remaining: RATE_LIMIT_MAX - 1, resetAt: now + RATE_LIMIT_WINDOW };
  }

  entry.count++;
  const remaining = RATE_LIMIT_MAX - entry.count;
  return { allowed: remaining >= 0, remaining: Math.max(0, remaining), resetAt: entry.resetAt };
}

function isBot(request: NextRequest): boolean {
  const ua = request.headers.get('user-agent') ?? '';
  const botPatterns = [
    /bot/i, /crawl/i, /spider/i, /slurp/i, /mediapartners/i,
  ];
  // Allow known good bots
  const goodBots = [/googlebot/i, /bingbot/i, /yandexbot/i];

  const isAnyBot = botPatterns.some((p) => p.test(ua));
  const isGoodBot = goodBots.some((p) => p.test(ua));

  return isAnyBot && !isGoodBot;
}

// Route definitions
const publicRoutes = ['/', '/login', '/register', '/pricing', '/about'];
const authRoutes = ['/login', '/register'];
const adminRoutes = ['/admin'];
const apiRoutes = ['/api'];

function matchRoute(pathname: string, routes: string[]): boolean {
  return routes.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );
}

export default auth((request) => {
  const { pathname, origin } = request.nextUrl;
  const user = request.auth?.user;
  const geo = request.geo;

  // 1. Geo-blocking
  if (geo?.country && BLOCKED_COUNTRIES.includes(geo.country)) {
    return NextResponse.json(
      { error: 'Service not available in your region' },
      { status: 451 } // Unavailable For Legal Reasons
    );
  }

  // 2. Bot detection (skip for API routes)
  if (!matchRoute(pathname, apiRoutes) && isBot(request as unknown as NextRequest)) {
    return NextResponse.json(
      { error: 'Automated access detected' },
      { status: 403 }
    );
  }

  // 3. Rate limiting
  const rateLimitKey = getRateLimitKey(
    request as unknown as NextRequest,
    user?.id ?? undefined
  );
  const { allowed, remaining, resetAt } = checkRateLimit(rateLimitKey);

  if (!allowed) {
    return new NextResponse('Too Many Requests', {
      status: 429,
      headers: {
        'Retry-After': String(Math.ceil((resetAt - Date.now()) / 1000)),
        'X-RateLimit-Remaining': '0',
        'X-RateLimit-Reset': String(resetAt),
      },
    });
  }

  // 4. Auth checks
  const isPublic = matchRoute(pathname, publicRoutes);
  const isAuthRoute = matchRoute(pathname, authRoutes);
  const isAdminRoute = matchRoute(pathname, adminRoutes);

  // Redirect authenticated users away from auth pages
  if (isAuthRoute && user) {
    return NextResponse.redirect(new URL('/dashboard', origin));
  }

  // Protect non-public routes
  if (!isPublic && !user) {
    const loginUrl = new URL('/login', origin);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Admin route protection
  if (isAdminRoute && user?.role !== 'admin' && user?.role !== 'superadmin') {
    return NextResponse.redirect(new URL('/unauthorized', origin));
  }

  // 5. Add rate limit headers to response
  const response = NextResponse.next();
  response.headers.set('X-RateLimit-Remaining', String(remaining));
  response.headers.set('X-RateLimit-Reset', String(resetAt));

  // Add user context headers for downstream
  if (user) {
    response.headers.set('x-user-id', user.id ?? '');
    response.headers.set('x-user-role', user.role ?? '');
  }

  return response;
});

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};
```

**Production rate limiting with Redis (Upstash)**:

```tsx
// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

// Sliding window rate limiter
export const rateLimiter = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(100, '60 s'),
  analytics: true,
  prefix: 'ratelimit:api',
});

// Separate rate limits for different endpoints
export const authRateLimiter = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(5, '60 s'), // 5 login attempts per minute
  prefix: 'ratelimit:auth',
});

// Usage in middleware
export async function checkRateLimit(identifier: string, limiter = rateLimiter) {
  const { success, remaining, reset } = await limiter.limit(identifier);
  return { allowed: success, remaining, resetAt: reset };
}
```

**Key edge middleware considerations**:
1. **Edge runtime limitations**: No Node.js APIs (use Web APIs), limited package support
2. **Redis for distributed rate limiting**: In-memory won't work with multiple edge instances
3. **Geo data**: Available via `request.geo` on Vercel, manual GeoIP lookup elsewhere
4. **Order matters**: Geo-block first (cheapest), then rate-limit, then auth (most expensive)
5. **Matcher optimization**: Exclude static files to reduce middleware invocations

---

## Q16. (Advanced) How do you handle auth state synchronization between Server Components, Client Components, and browser tabs?

**Scenario**: A user logs out in one tab. The other tab still shows them as logged in. How do you sync auth state across tabs and between server/client?

**Answer**:

```
┌─────────────────────────────────────────────────────────┐
│           Auth State Synchronization                     │
│                                                         │
│  Tab 1 (Active)          Tab 2 (Background)             │
│  ┌──────────────┐       ┌──────────────┐                │
│  │ User clicks  │       │ Stale session│                │
│  │ "Sign Out"   │       │ displayed    │                │
│  └──────┬───────┘       └──────────────┘                │
│         │                      ▲                        │
│         ▼                      │                        │
│  ┌──────────────┐    BroadcastChannel                   │
│  │ Server Action│──── { type: 'SIGN_OUT' } ────────┘    │
│  │ destroys     │                                       │
│  │ session      │    Tab 2 receives message,            │
│  └──────────────┘    redirects to /login                │
│                                                         │
│  Alternative: Storage event, polling                    │
└─────────────────────────────────────────────────────────┘
```

**Solution 1: BroadcastChannel API (modern browsers)**:

```tsx
// lib/auth-sync.ts
'use client';

type AuthEvent =
  | { type: 'SIGN_OUT' }
  | { type: 'SIGN_IN'; userId: string }
  | { type: 'SESSION_UPDATE'; role: string }
  | { type: 'TOKEN_REFRESH' };

let channel: BroadcastChannel | null = null;

export function getAuthChannel(): BroadcastChannel {
  if (!channel && typeof window !== 'undefined') {
    channel = new BroadcastChannel('auth-sync');
  }
  return channel!;
}

export function broadcastAuthEvent(event: AuthEvent) {
  try {
    getAuthChannel()?.postMessage(event);
  } catch {
    // Fallback to localStorage for older browsers
    localStorage.setItem('auth-event', JSON.stringify({ ...event, timestamp: Date.now() }));
    localStorage.removeItem('auth-event');
  }
}

export function onAuthEvent(callback: (event: AuthEvent) => void): () => void {
  const ch = getAuthChannel();

  // BroadcastChannel listener
  const handleMessage = (e: MessageEvent<AuthEvent>) => callback(e.data);
  ch?.addEventListener('message', handleMessage);

  // localStorage fallback
  const handleStorage = (e: StorageEvent) => {
    if (e.key === 'auth-event' && e.newValue) {
      callback(JSON.parse(e.newValue));
    }
  };
  window.addEventListener('storage', handleStorage);

  return () => {
    ch?.removeEventListener('message', handleMessage);
    window.removeEventListener('storage', handleStorage);
  };
}
```

**Solution 2: Auth sync provider**:

```tsx
// app/components/AuthSyncProvider.tsx
'use client';

import { useSession, signOut } from 'next-auth/react';
import { useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { onAuthEvent, broadcastAuthEvent } from '@/lib/auth-sync';

export function AuthSyncProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status, update } = useSession();
  const router = useRouter();

  // Listen for auth events from other tabs
  useEffect(() => {
    const unsubscribe = onAuthEvent(async (event) => {
      switch (event.type) {
        case 'SIGN_OUT':
          // Force sign out in this tab
          await signOut({ redirect: false });
          router.push('/login');
          router.refresh();
          break;

        case 'SIGN_IN':
          // Refresh session in this tab
          await update();
          router.refresh();
          break;

        case 'SESSION_UPDATE':
          await update();
          router.refresh();
          break;

        case 'TOKEN_REFRESH':
          await update();
          break;
      }
    });

    return unsubscribe;
  }, [router, update]);

  // Detect tab visibility change — refresh session when tab becomes active
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible' && status === 'authenticated') {
        // Silently check if session is still valid
        await update();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [status, update]);

  // Detect online/offline
  useEffect(() => {
    const handleOnline = async () => {
      if (status === 'authenticated') {
        await update();
        router.refresh();
      }
    };

    window.addEventListener('online', handleOnline);
    return () => window.removeEventListener('online', handleOnline);
  }, [status, update, router]);

  return <>{children}</>;
}
```

**Broadcast events from Server Actions**:

```tsx
// app/actions/auth-actions.ts
'use server';

import { signOut as authSignOut } from '@/auth';

export async function handleSignOut() {
  await authSignOut({ redirect: false });
  // Client-side code will broadcast the event
  return { signedOut: true };
}
```

```tsx
// app/components/SignOutButton.tsx
'use client';

import { handleSignOut } from '@/app/actions/auth-actions';
import { broadcastAuthEvent } from '@/lib/auth-sync';
import { useRouter } from 'next/navigation';

export function SignOutButton() {
  const router = useRouter();

  return (
    <button
      onClick={async () => {
        const result = await handleSignOut();
        if (result.signedOut) {
          broadcastAuthEvent({ type: 'SIGN_OUT' });
          router.push('/login');
          router.refresh();
        }
      }}
      className="text-red-600 hover:text-red-800"
    >
      Sign Out
    </button>
  );
}
```

**Solution 3: Polling for session validity** (fallback):

```tsx
// app/components/SessionPoller.tsx
'use client';

import { useSession } from 'next-auth/react';
import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';

export function SessionPoller({ interval = 60_000 }: { interval?: number }) {
  const { status, update } = useSession();
  const router = useRouter();
  const previousStatus = useRef(status);

  useEffect(() => {
    if (status !== 'authenticated') return;

    const timer = setInterval(async () => {
      const session = await update();

      // Session expired server-side
      if (!session && previousStatus.current === 'authenticated') {
        router.push('/login?reason=session_expired');
        router.refresh();
      }

      previousStatus.current = session ? 'authenticated' : 'unauthenticated';
    }, interval);

    return () => clearInterval(timer);
  }, [status, interval, update, router]);

  return null;
}
```

**Wire it all together in the root layout**:

```tsx
// app/layout.tsx
import { Providers } from './providers';
import { AuthSyncProvider } from './components/AuthSyncProvider';
import { SessionPoller } from './components/SessionPoller';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <AuthSyncProvider>
            {children}
            <SessionPoller interval={5 * 60 * 1000} />
          </AuthSyncProvider>
        </Providers>
      </body>
    </html>
  );
}
```

**Key sync strategies**:
1. **BroadcastChannel** — instant cross-tab sync (primary)
2. **localStorage events** — fallback for older browsers
3. **Visibility change** — re-validate session when tab becomes active
4. **Polling** — periodic check for session validity
5. **Online event** — re-validate when network reconnects
6. **`router.refresh()`** — re-runs Server Components with fresh session data

---

## Q17. (Advanced) How do you implement a complete social login flow with custom profile mapping, error handling, and onboarding redirect?

**Scenario**: When a user signs in with Google or GitHub for the first time, you need to create their profile with custom fields, redirect them to an onboarding wizard, and handle edge cases (email conflicts, missing data).

**Answer**:

```tsx
// auth.ts — Complete social login with profile mapping and onboarding
import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import GitHub from 'next-auth/providers/github';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/prisma';
import type { AdapterUser } from 'next-auth/adapters';

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: {
    ...PrismaAdapter(prisma),
    // Override createUser to add custom fields
    async createUser(data: AdapterUser) {
      const user = await prisma.user.create({
        data: {
          email: data.email,
          name: data.name,
          image: data.image,
          emailVerified: data.emailVerified,
          role: 'user',
          onboardingComplete: false,
          plan: 'free',
          preferences: {
            theme: 'system',
            notifications: true,
            locale: 'en',
          },
        },
      });
      return user as AdapterUser;
    },
  },
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
      profile(profile) {
        return {
          id: profile.sub,
          name: profile.name,
          email: profile.email,
          image: profile.picture,
          role: 'user',
          locale: profile.locale ?? 'en',
        };
      },
    }),
    GitHub({
      clientId: process.env.AUTH_GITHUB_ID!,
      clientSecret: process.env.AUTH_GITHUB_SECRET!,
      profile(profile) {
        return {
          id: String(profile.id),
          name: profile.name ?? profile.login,
          email: profile.email,
          image: profile.avatar_url,
          role: 'user',
          githubUsername: profile.login,
        };
      },
    }),
  ],
  session: { strategy: 'jwt' },
  callbacks: {
    async signIn({ user, account, profile }) {
      if (!user.email) {
        // GitHub users may have private emails
        if (account?.provider === 'github' && profile) {
          // Fetch email from GitHub API
          const emailRes = await fetch('https://api.github.com/user/emails', {
            headers: {
              Authorization: `Bearer ${account.access_token}`,
              Accept: 'application/vnd.github+json',
            },
          });

          if (emailRes.ok) {
            const emails = await emailRes.json();
            const primary = emails.find(
              (e: any) => e.primary && e.verified
            );
            if (primary) {
              user.email = primary.email;
            }
          }
        }

        if (!user.email) {
          // Still no email — redirect to email collection page
          return `/complete-profile?provider=${account?.provider}`;
        }
      }

      // Check for email conflicts with different providers
      const existingUser = await prisma.user.findUnique({
        where: { email: user.email! },
        include: { accounts: true },
      });

      if (existingUser && !existingUser.accounts.some(
        (a) => a.provider === account?.provider
      )) {
        // Email exists with a different provider
        // Option 1: Auto-link (if allowDangerousEmailAccountLinking is true)
        // Option 2: Redirect to account linking page
        return `/login?error=OAuthAccountNotLinked&provider=${account?.provider}`;
      }

      return true;
    },

    async jwt({ token, user, account, trigger }) {
      if (user) {
        const dbUser = await prisma.user.findUnique({
          where: { id: user.id! },
          select: {
            id: true,
            role: true,
            onboardingComplete: true,
            plan: true,
          },
        });

        token.id = dbUser?.id ?? user.id;
        token.role = dbUser?.role ?? 'user';
        token.onboardingComplete = dbUser?.onboardingComplete ?? false;
        token.plan = dbUser?.plan ?? 'free';
        token.isNewUser = !dbUser?.onboardingComplete;
      }

      if (trigger === 'update') {
        const dbUser = await prisma.user.findUnique({
          where: { id: token.id as string },
          select: { role: true, onboardingComplete: true, plan: true },
        });
        if (dbUser) {
          token.role = dbUser.role;
          token.onboardingComplete = dbUser.onboardingComplete;
          token.plan = dbUser.plan;
        }
      }

      return token;
    },

    async session({ session, token }) {
      session.user.id = token.id as string;
      session.user.role = token.role as string;
      session.user.onboardingComplete = token.onboardingComplete as boolean;
      session.user.plan = token.plan as string;
      session.user.isNewUser = token.isNewUser as boolean;
      return session;
    },

    async redirect({ url, baseUrl }) {
      // After sign-in, redirect new users to onboarding
      if (url.startsWith(baseUrl)) return url;
      return baseUrl;
    },
  },
  events: {
    async createUser({ user }) {
      // Send welcome email
      await fetch(`${process.env.NEXT_PUBLIC_APP_URL}/api/internal/welcome-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user.id, email: user.email }),
      });

      // Track in analytics
      await fetch(`${process.env.NEXT_PUBLIC_APP_URL}/api/internal/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'user_signed_up',
          properties: { userId: user.id, method: 'social' },
        }),
      });
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
    newUser: '/onboarding', // Redirect new users to onboarding
  },
});
```

**Onboarding flow**:

```tsx
// app/onboarding/page.tsx
import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import { OnboardingWizard } from './OnboardingWizard';

export default async function OnboardingPage() {
  const session = await auth();
  if (!session?.user) redirect('/login');

  // Already completed onboarding
  if (session.user.onboardingComplete) redirect('/dashboard');

  return <OnboardingWizard user={session.user} />;
}
```

```tsx
// app/onboarding/OnboardingWizard.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { completeOnboarding } from './actions';

interface Step {
  id: string;
  title: string;
  component: React.ComponentType<any>;
}

export function OnboardingWizard({ user }: { user: any }) {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<Record<string, any>>({});
  const router = useRouter();
  const { update } = useSession();

  const steps: Step[] = [
    { id: 'company', title: 'Company Info', component: CompanyStep },
    { id: 'role', title: 'Your Role', component: RoleStep },
    { id: 'preferences', title: 'Preferences', component: PreferencesStep },
  ];

  const CurrentStep = steps[step].component;

  async function handleNext(stepData: Record<string, any>) {
    const newData = { ...data, ...stepData };
    setData(newData);

    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      // Final step — complete onboarding
      const result = await completeOnboarding(newData);
      if (result.success) {
        await update(); // Refresh session to get onboardingComplete = true
        router.push('/dashboard');
      }
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={s.id} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  i <= step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {i + 1}
              </div>
              {i < steps.length - 1 && (
                <div
                  className={`h-0.5 w-16 mx-2 ${
                    i < step ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <h2 className="text-xl font-bold mb-4">{steps[step].title}</h2>
      <CurrentStep onNext={handleNext} data={data} />
    </div>
  );
}

function CompanyStep({ onNext }: { onNext: (data: any) => void }) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        onNext({ company: fd.get('company'), teamSize: fd.get('teamSize') });
      }}
      className="space-y-4"
    >
      <input name="company" placeholder="Company name" className="w-full px-3 py-2 border rounded-lg" />
      <select name="teamSize" className="w-full px-3 py-2 border rounded-lg">
        <option value="1-5">1-5 people</option>
        <option value="6-20">6-20 people</option>
        <option value="21-100">21-100 people</option>
        <option value="100+">100+ people</option>
      </select>
      <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg">Next</button>
    </form>
  );
}

function RoleStep({ onNext }: { onNext: (data: any) => void }) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        onNext({ jobTitle: fd.get('jobTitle'), useCase: fd.get('useCase') });
      }}
      className="space-y-4"
    >
      <input name="jobTitle" placeholder="Job title" className="w-full px-3 py-2 border rounded-lg" />
      <textarea name="useCase" placeholder="How will you use our product?" className="w-full px-3 py-2 border rounded-lg" rows={3} />
      <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg">Next</button>
    </form>
  );
}

function PreferencesStep({ onNext }: { onNext: (data: any) => void }) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        onNext({ theme: fd.get('theme'), notifications: fd.get('notifications') === 'on' });
      }}
      className="space-y-4"
    >
      <select name="theme" className="w-full px-3 py-2 border rounded-lg">
        <option value="system">System default</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
      <label className="flex items-center gap-2">
        <input name="notifications" type="checkbox" defaultChecked />
        <span>Enable email notifications</span>
      </label>
      <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-lg">Complete Setup</button>
    </form>
  );
}
```

```tsx
// app/onboarding/actions.ts
'use server';

import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';

export async function completeOnboarding(data: Record<string, any>) {
  const session = await auth();
  if (!session?.user) throw new Error('Unauthorized');

  await prisma.user.update({
    where: { id: session.user.id },
    data: {
      onboardingComplete: true,
      company: data.company,
      jobTitle: data.jobTitle,
      teamSize: data.teamSize,
      preferences: {
        theme: data.theme ?? 'system',
        notifications: data.notifications ?? true,
      },
    },
  });

  return { success: true };
}
```

**Error handling for OAuth edge cases**: Always handle missing emails (GitHub private emails), provider conflicts (same email different provider), and incomplete profiles by redirecting to appropriate pages rather than showing cryptic errors.

---

## Q18. (Advanced) How do you implement permission boundaries and fine-grained access control for a complex feature set?

**Scenario**: Your project management SaaS has projects, tasks, and comments. Different users have different access levels per project (owner, editor, viewer). Some tasks are private. How do you implement fine-grained permissions?

**Answer**:

```
┌────────────────────────────────────────────────────┐
│         Attribute-Based Access Control (ABAC)       │
│                                                    │
│  Subject (User)                                    │
│  ├── userId: "u_123"                               │
│  ├── orgRole: "admin"                              │
│  └── projectMemberships: [...]                     │
│                                                    │
│  Resource (Task)                                   │
│  ├── id: "t_456"                                   │
│  ├── projectId: "p_789"                            │
│  ├── isPrivate: true                               │
│  └── assigneeId: "u_123"                           │
│                                                    │
│  Action: "task:update"                             │
│                                                    │
│  Context                                           │
│  ├── projectRole: "editor"                         │
│  └── isAssignee: true                              │
│                                                    │
│  Policy: ALLOW if                                  │
│  ├── projectRole in ["owner", "editor"]  OR        │
│  ├── isAssignee AND action in ["update", "view"]   │
│  └── NOT (isPrivate AND projectRole == "viewer")   │
└────────────────────────────────────────────────────┘
```

```tsx
// lib/permissions/types.ts
export type ProjectRole = 'owner' | 'editor' | 'viewer';

export type Action =
  | 'project:view'
  | 'project:edit'
  | 'project:delete'
  | 'project:manage_members'
  | 'task:view'
  | 'task:create'
  | 'task:update'
  | 'task:delete'
  | 'task:assign'
  | 'comment:create'
  | 'comment:edit'
  | 'comment:delete';

export interface AccessContext {
  userId: string;
  orgRole: string;
  projectId: string;
  projectRole: ProjectRole | null;
  resource?: {
    type: 'task' | 'comment' | 'project';
    ownerId?: string;
    assigneeId?: string;
    isPrivate?: boolean;
  };
}
```

```tsx
// lib/permissions/engine.ts
import type { Action, AccessContext, ProjectRole } from './types';

type PolicyFn = (ctx: AccessContext) => boolean;

const PROJECT_ROLE_HIERARCHY: Record<ProjectRole, number> = {
  owner: 3,
  editor: 2,
  viewer: 1,
};

function hasMinRole(actual: ProjectRole | null, required: ProjectRole): boolean {
  if (!actual) return false;
  return PROJECT_ROLE_HIERARCHY[actual] >= PROJECT_ROLE_HIERARCHY[required];
}

// Policy definitions
const policies: Record<Action, PolicyFn> = {
  'project:view': (ctx) => !!ctx.projectRole,
  'project:edit': (ctx) => hasMinRole(ctx.projectRole, 'editor'),
  'project:delete': (ctx) => ctx.projectRole === 'owner',
  'project:manage_members': (ctx) => ctx.projectRole === 'owner' || ctx.orgRole === 'admin',

  'task:view': (ctx) => {
    if (!ctx.projectRole) return false;
    // Private tasks: only owner, assignee, or project owner
    if (ctx.resource?.isPrivate) {
      return (
        ctx.resource.ownerId === ctx.userId ||
        ctx.resource.assigneeId === ctx.userId ||
        ctx.projectRole === 'owner'
      );
    }
    return true;
  },

  'task:create': (ctx) => hasMinRole(ctx.projectRole, 'editor'),

  'task:update': (ctx) => {
    if (hasMinRole(ctx.projectRole, 'editor')) return true;
    // Assignees can update their own tasks even as viewer
    return ctx.resource?.assigneeId === ctx.userId;
  },

  'task:delete': (ctx) => {
    if (hasMinRole(ctx.projectRole, 'owner')) return true;
    // Editors can delete tasks they created
    return (
      hasMinRole(ctx.projectRole, 'editor') &&
      ctx.resource?.ownerId === ctx.userId
    );
  },

  'task:assign': (ctx) => hasMinRole(ctx.projectRole, 'editor'),

  'comment:create': (ctx) => !!ctx.projectRole,
  'comment:edit': (ctx) => ctx.resource?.ownerId === ctx.userId,
  'comment:delete': (ctx) =>
    ctx.resource?.ownerId === ctx.userId || hasMinRole(ctx.projectRole, 'owner'),
};

export function checkPermission(action: Action, ctx: AccessContext): boolean {
  const policy = policies[action];
  if (!policy) return false;
  return policy(ctx);
}

export function getPermittedActions(ctx: AccessContext): Action[] {
  return (Object.keys(policies) as Action[]).filter((action) =>
    checkPermission(action, ctx)
  );
}
```

```tsx
// lib/permissions/context.ts
import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { cache } from 'react';
import type { AccessContext, ProjectRole } from './types';

// Cache per-request to avoid duplicate DB queries
export const getAccessContext = cache(
  async (projectId: string): Promise<AccessContext> => {
    const session = await auth();
    if (!session?.user?.id) {
      return {
        userId: '',
        orgRole: '',
        projectId,
        projectRole: null,
      };
    }

    const membership = await prisma.projectMembership.findUnique({
      where: {
        userId_projectId: {
          userId: session.user.id,
          projectId,
        },
      },
      select: { role: true },
    });

    return {
      userId: session.user.id,
      orgRole: session.user.role ?? 'user',
      projectId,
      projectRole: (membership?.role as ProjectRole) ?? null,
    };
  }
);
```

**Use in Server Components**:

```tsx
// app/projects/[id]/page.tsx
import { getAccessContext } from '@/lib/permissions/context';
import { checkPermission, getPermittedActions } from '@/lib/permissions/engine';
import { prisma } from '@/lib/prisma';
import { notFound } from 'next/navigation';
import { TaskList } from './TaskList';

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const ctx = await getAccessContext(id);

  if (!checkPermission('project:view', ctx)) {
    notFound();
  }

  const project = await prisma.project.findUnique({
    where: { id },
    include: {
      tasks: {
        where: {
          OR: [
            { isPrivate: false },
            { assigneeId: ctx.userId },
            { createdById: ctx.userId },
          ],
        },
        orderBy: { createdAt: 'desc' },
      },
    },
  });

  if (!project) notFound();

  const permissions = getPermittedActions(ctx);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{project.name}</h1>
        <div className="flex gap-2">
          {permissions.includes('task:create') && (
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg">
              New Task
            </button>
          )}
          {permissions.includes('project:edit') && (
            <button className="px-4 py-2 border rounded-lg">Settings</button>
          )}
          {permissions.includes('project:manage_members') && (
            <button className="px-4 py-2 border rounded-lg">Members</button>
          )}
        </div>
      </div>

      <TaskList
        tasks={project.tasks}
        permissions={permissions}
        currentUserId={ctx.userId}
      />
    </div>
  );
}
```

**Use in Server Actions**:

```tsx
// app/projects/[id]/actions.ts
'use server';

import { getAccessContext } from '@/lib/permissions/context';
import { checkPermission } from '@/lib/permissions/engine';
import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';

export async function updateTask(
  projectId: string,
  taskId: string,
  data: { title?: string; description?: string; status?: string }
) {
  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { assigneeId: true, createdById: true, isPrivate: true, projectId: true },
  });

  if (!task || task.projectId !== projectId) {
    throw new Error('Task not found');
  }

  const ctx = await getAccessContext(projectId);
  const canUpdate = checkPermission('task:update', {
    ...ctx,
    resource: {
      type: 'task',
      assigneeId: task.assigneeId ?? undefined,
      ownerId: task.createdById,
      isPrivate: task.isPrivate,
    },
  });

  if (!canUpdate) {
    throw new Error('You do not have permission to update this task');
  }

  await prisma.task.update({
    where: { id: taskId },
    data,
  });

  revalidatePath(`/projects/${projectId}`);
}
```

**Key design principles**:
1. **Centralized policy engine** — all permission logic in one place
2. **Context-based evaluation** — permissions depend on user + resource + relationship
3. **React `cache()`** — deduplicate permission context queries per request
4. **Server-side enforcement** — never trust client-side permission checks
5. **Principle of least privilege** — default deny, explicit allow
6. **Permission list for UI** — pass `getPermittedActions()` to components to conditionally render UI

---

## Q19. (Advanced) How do you implement auth for Next.js apps deployed at the edge (Edge Runtime) and handle limitations?

**Scenario**: Your Next.js app runs on the Edge Runtime (Vercel Edge, Cloudflare Workers) for ultra-low latency. How do you handle auth given Edge Runtime limitations (no Node.js crypto, no native bcrypt, limited packages)?

**Answer**:

```
┌──────────────────────────────────────────────────────┐
│         Edge Runtime Auth Constraints                 │
│                                                      │
│  ✓ Available             ✗ Not Available             │
│  ├── Web Crypto API      ├── Node.js crypto          │
│  ├── fetch               ├── bcrypt (native)         │
│  ├── JWT (jose lib)      ├── Most ORMs               │
│  ├── Headers/cookies     ├── fs module               │
│  ├── TextEncoder         ├── Large npm packages      │
│  └── crypto.subtle       └── Database TCP connections│
│                                                      │
│  Solution: Use edge-compatible libraries             │
│  ├── jose (JWT)                                      │
│  ├── @upstash/redis (HTTP-based Redis)               │
│  ├── Prisma Accelerate or Neon HTTP driver           │
│  └── bcryptjs (pure JS, but SLOW at edge)            │
└──────────────────────────────────────────────────────┘
```

**Edge-compatible auth setup**:

```tsx
// lib/edge-auth.ts — Works in Edge Runtime
import { jwtVerify, SignJWT } from 'jose';
import { type NextRequest } from 'next/server';

const SECRET = new TextEncoder().encode(process.env.JWT_SECRET!);
const ALG = 'HS256';

export interface TokenPayload {
  userId: string;
  role: string;
  email: string;
  iat: number;
  exp: number;
}

export async function createToken(payload: Omit<TokenPayload, 'iat' | 'exp'>): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: ALG })
    .setIssuedAt()
    .setExpirationTime('15m')
    .sign(SECRET);
}

export async function verifyToken(token: string): Promise<TokenPayload | null> {
  try {
    const { payload } = await jwtVerify(token, SECRET);
    return payload as unknown as TokenPayload;
  } catch {
    return null;
  }
}

export async function getTokenFromRequest(request: NextRequest): Promise<TokenPayload | null> {
  // Check cookie first
  const cookieToken = request.cookies.get('auth-token')?.value;
  if (cookieToken) return verifyToken(cookieToken);

  // Check Authorization header (API clients)
  const authHeader = request.headers.get('Authorization');
  if (authHeader?.startsWith('Bearer ')) {
    return verifyToken(authHeader.slice(7));
  }

  return null;
}
```

**Edge-compatible middleware**:

```tsx
// middleware.ts
export const runtime = 'edge';

import { NextRequest, NextResponse } from 'next/server';
import { getTokenFromRequest } from '@/lib/edge-auth';

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip public routes
  if (isPublicRoute(pathname)) {
    return NextResponse.next();
  }

  const user = await getTokenFromRequest(request);

  if (!user) {
    if (pathname.startsWith('/api/')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Inject user info for downstream handlers
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set('x-user-id', user.userId);
  requestHeaders.set('x-user-role', user.role);
  requestHeaders.set('x-user-email', user.email);

  return NextResponse.next({ request: { headers: requestHeaders } });
}

function isPublicRoute(pathname: string): boolean {
  const publicPaths = ['/', '/login', '/register', '/api/auth'];
  return publicPaths.some((p) => pathname === p || pathname.startsWith(p + '/'));
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

**Edge-compatible session storage with Upstash Redis**:

```tsx
// lib/edge-session.ts — HTTP-based Redis session store (works at edge)
import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

interface SessionData {
  userId: string;
  role: string;
  email: string;
  createdAt: number;
  metadata?: Record<string, unknown>;
}

const SESSION_TTL = 7 * 24 * 60 * 60; // 7 days in seconds

export async function createSession(data: Omit<SessionData, 'createdAt'>): Promise<string> {
  const sessionId = crypto.randomUUID();
  const sessionData: SessionData = { ...data, createdAt: Date.now() };

  await redis.set(`session:${sessionId}`, JSON.stringify(sessionData), {
    ex: SESSION_TTL,
  });

  return sessionId;
}

export async function getSession(sessionId: string): Promise<SessionData | null> {
  const data = await redis.get<string>(`session:${sessionId}`);
  if (!data) return null;
  return typeof data === 'string' ? JSON.parse(data) : data;
}

export async function destroySession(sessionId: string): Promise<void> {
  await redis.del(`session:${sessionId}`);
}

export async function destroyAllUserSessions(userId: string): Promise<void> {
  // Scan for all sessions of this user
  const keys = await redis.keys(`session:*`);
  for (const key of keys) {
    const data = await redis.get<string>(key);
    if (data) {
      const session = typeof data === 'string' ? JSON.parse(data) : data;
      if (session.userId === userId) {
        await redis.del(key);
      }
    }
  }
}
```

**Edge-compatible password hashing (Web Crypto API)**:

```tsx
// lib/edge-crypto.ts — No native bcrypt at edge, use PBKDF2 via Web Crypto
export async function hashPassword(password: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    'PBKDF2',
    false,
    ['deriveBits']
  );

  const hash = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt,
      iterations: 600_000, // OWASP recommended for PBKDF2-SHA256
      hash: 'SHA-256',
    },
    passwordKey,
    256
  );

  // Encode as base64: salt$hash
  const saltB64 = btoa(String.fromCharCode(...salt));
  const hashB64 = btoa(String.fromCharCode(...new Uint8Array(hash)));

  return `pbkdf2:600000:${saltB64}$${hashB64}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [, iterations, rest] = stored.split(':');
  const [saltB64, hashB64] = rest.split('$');

  const salt = Uint8Array.from(atob(saltB64), (c) => c.charCodeAt(0));

  const passwordKey = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    'PBKDF2',
    false,
    ['deriveBits']
  );

  const hash = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt,
      iterations: parseInt(iterations),
      hash: 'SHA-256',
    },
    passwordKey,
    256
  );

  const hashB64Computed = btoa(String.fromCharCode(...new Uint8Array(hash)));

  // Constant-time comparison
  return hashB64 === hashB64Computed;
}
```

**Edge-compatible database access**:

```tsx
// lib/edge-db.ts — Use HTTP-based database connections at the edge
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);

export async function getUserByEmail(email: string) {
  const rows = await sql`SELECT id, email, name, role, password_hash FROM users WHERE email = ${email}`;
  return rows[0] ?? null;
}

export async function getUserById(id: string) {
  const rows = await sql`SELECT id, email, name, role FROM users WHERE id = ${id}`;
  return rows[0] ?? null;
}
```

**Key edge auth considerations**:
1. **Use `jose` for JWT** — pure JS, works everywhere
2. **HTTP-based databases** — Neon serverless, PlanetScale, Prisma Accelerate
3. **HTTP-based Redis** — Upstash for sessions and rate limiting
4. **Web Crypto for hashing** — PBKDF2 instead of bcrypt
5. **Minimize middleware work** — heavy auth logic in Server Components (Node.js runtime)
6. **Split runtime per route** — use `export const runtime = 'edge'` only where needed

---

## Q20. (Advanced) How do you build a production-grade auth system that handles session invalidation, device management, and suspicious login detection?

**Scenario**: Your security team requires: (1) users can view and revoke sessions on specific devices, (2) suspicious logins (new device, new location) trigger email alerts and optional 2FA, (3) admin can force-logout any user.

**Answer**:

```
┌─────────────────────────────────────────────────────────┐
│         Production Auth Security System                  │
│                                                         │
│  Login Request                                          │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────┐                                       │
│  │ Verify creds │                                       │
│  └──────┬───────┘                                       │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────┐    New device?   ┌──────────────┐ │
│  │ Device fingerprint│───── YES ──────▶│ Email alert  │ │
│  │ check            │                  │ + optional   │ │
│  └──────┬───────────┘                  │ 2FA prompt   │ │
│         │ Known device                 └──────────────┘ │
│         ▼                                               │
│  ┌──────────────────┐    New location? ┌──────────────┐ │
│  │ GeoIP check      │───── YES ──────▶│ Email alert  │ │
│  └──────┬───────────┘                  └──────────────┘ │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────┐                                   │
│  │ Create session   │                                   │
│  │ with device info │                                   │
│  └──────────────────┘                                   │
│                                                         │
│  Session DB:                                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │ session_id | user_id | device | ip | city | active │ │
│  │ s_001      | u_123   | Chrome | .. | NYC  | true   │ │
│  │ s_002      | u_123   | iPhone | .. | NYC  | true   │ │
│  │ s_003      | u_123   | Firefox| .. | LON  | false  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Database schema**:

```prisma
model Session {
  id            String   @id @default(cuid())
  userId        String
  user          User     @relation(fields: [userId], references: [id])
  token         String   @unique
  deviceName    String
  deviceType    String   // desktop, mobile, tablet
  browser       String
  os            String
  ip            String
  city          String?
  country       String?
  isActive      Boolean  @default(true)
  lastActiveAt  DateTime @default(now())
  createdAt     DateTime @default(now())
  expiresAt     DateTime
  
  @@index([userId])
  @@index([token])
}

model LoginAttempt {
  id        String   @id @default(cuid())
  userId    String?
  email     String
  ip        String
  city      String?
  country   String?
  userAgent String
  success   Boolean
  reason    String?  // "invalid_password", "account_locked", "2fa_failed"
  createdAt DateTime @default(now())
  
  @@index([userId])
  @@index([email])
  @@index([ip])
}

model SecurityAlert {
  id        String   @id @default(cuid())
  userId    String
  user      User     @relation(fields: [userId], references: [id])
  type      String   // "new_device", "new_location", "multiple_failures"
  metadata  Json
  dismissed Boolean  @default(false)
  createdAt DateTime @default(now())
  
  @@index([userId])
}
```

**Session management service**:

```tsx
// lib/session-manager.ts
import { prisma } from '@/lib/prisma';
import { SignJWT, jwtVerify } from 'jose';
import crypto from 'crypto';
import { headers } from 'next/headers';
import UAParser from 'ua-parser-js';
import { sendEmail } from '@/lib/email';

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET!);

interface DeviceInfo {
  deviceName: string;
  deviceType: string;
  browser: string;
  os: string;
}

function parseDevice(userAgent: string): DeviceInfo {
  const parser = new UAParser(userAgent);
  const browser = parser.getBrowser();
  const os = parser.getOS();
  const device = parser.getDevice();

  return {
    deviceName: `${browser.name ?? 'Unknown'} on ${os.name ?? 'Unknown'}`,
    deviceType: device.type ?? 'desktop',
    browser: `${browser.name ?? 'Unknown'} ${browser.version ?? ''}`.trim(),
    os: `${os.name ?? 'Unknown'} ${os.version ?? ''}`.trim(),
  };
}

async function getGeoFromIP(ip: string): Promise<{ city?: string; country?: string }> {
  try {
    const res = await fetch(`https://ipapi.co/${ip}/json/`);
    const data = await res.json();
    return { city: data.city, country: data.country_name };
  } catch {
    return {};
  }
}

export async function createSessionWithDevice(
  userId: string,
  role: string
): Promise<{ token: string; isNewDevice: boolean; isNewLocation: boolean }> {
  const headerStore = await headers();
  const userAgent = headerStore.get('user-agent') ?? '';
  const ip = headerStore.get('x-forwarded-for')?.split(',')[0]?.trim() ?? '127.0.0.1';

  const device = parseDevice(userAgent);
  const geo = await getGeoFromIP(ip);

  // Check if this is a new device
  const existingDeviceSession = await prisma.session.findFirst({
    where: {
      userId,
      browser: device.browser,
      os: device.os,
      isActive: true,
    },
  });
  const isNewDevice = !existingDeviceSession;

  // Check if this is a new location
  const existingLocationSession = await prisma.session.findFirst({
    where: {
      userId,
      city: geo.city ?? undefined,
      country: geo.country ?? undefined,
      isActive: true,
    },
  });
  const isNewLocation = !existingLocationSession && !!geo.city;

  // Create session token
  const sessionToken = crypto.randomBytes(64).toString('hex');
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days

  // Create JWT containing session reference
  const jwt = await new SignJWT({
    userId,
    role,
    sessionId: sessionToken.slice(0, 16), // Short reference
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setExpirationTime('15m')
    .sign(JWT_SECRET);

  // Store session in DB
  await prisma.session.create({
    data: {
      userId,
      token: sessionToken,
      ...device,
      ip,
      city: geo.city,
      country: geo.country,
      expiresAt,
    },
  });

  // Handle security alerts
  if (isNewDevice) {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: { email: true, name: true },
    });

    await prisma.securityAlert.create({
      data: {
        userId,
        type: 'new_device',
        metadata: {
          device: device.deviceName,
          ip,
          city: geo.city,
          country: geo.country,
          time: new Date().toISOString(),
        },
      },
    });

    if (user?.email) {
      await sendEmail({
        to: user.email,
        subject: 'New device sign-in detected',
        html: `
          <h2>New Sign-in Detected</h2>
          <p>Hi ${user.name},</p>
          <p>A new sign-in to your account was detected:</p>
          <ul>
            <li><strong>Device:</strong> ${device.deviceName}</li>
            <li><strong>Location:</strong> ${geo.city ?? 'Unknown'}, ${geo.country ?? 'Unknown'}</li>
            <li><strong>IP:</strong> ${ip}</li>
            <li><strong>Time:</strong> ${new Date().toLocaleString()}</li>
          </ul>
          <p>If this wasn't you, <a href="${process.env.NEXT_PUBLIC_APP_URL}/settings/security">secure your account</a>.</p>
        `,
      });
    }
  }

  if (isNewLocation) {
    await prisma.securityAlert.create({
      data: {
        userId,
        type: 'new_location',
        metadata: { city: geo.city, country: geo.country, ip },
      },
    });
  }

  return { token: sessionToken, isNewDevice, isNewLocation };
}

// Revoke a specific session
export async function revokeSession(sessionId: string, userId: string): Promise<void> {
  await prisma.session.updateMany({
    where: { id: sessionId, userId },
    data: { isActive: false },
  });
}

// Revoke all sessions except current
export async function revokeOtherSessions(
  currentSessionToken: string,
  userId: string
): Promise<number> {
  const result = await prisma.session.updateMany({
    where: {
      userId,
      token: { not: currentSessionToken },
      isActive: true,
    },
    data: { isActive: false },
  });
  return result.count;
}

// Admin: force logout user
export async function adminForceLogout(targetUserId: string): Promise<number> {
  const result = await prisma.session.updateMany({
    where: { userId: targetUserId, isActive: true },
    data: { isActive: false },
  });
  return result.count;
}
```

**Device management UI**:

```tsx
// app/settings/security/page.tsx
import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { redirect } from 'next/navigation';
import { DeviceList } from './DeviceList';
import { SecurityAlerts } from './SecurityAlerts';

export default async function SecurityPage() {
  const session = await auth();
  if (!session?.user) redirect('/login');

  const [sessions, alerts] = await Promise.all([
    prisma.session.findMany({
      where: { userId: session.user.id, isActive: true },
      orderBy: { lastActiveAt: 'desc' },
    }),
    prisma.securityAlert.findMany({
      where: { userId: session.user.id, dismissed: false },
      orderBy: { createdAt: 'desc' },
      take: 10,
    }),
  ]);

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">Security Settings</h1>

      {alerts.length > 0 && <SecurityAlerts alerts={alerts} />}

      <section>
        <h2 className="text-lg font-semibold mb-4">Active Sessions</h2>
        <DeviceList sessions={sessions} currentSessionToken={session.user.currentSessionToken} />
      </section>
    </div>
  );
}
```

```tsx
// app/settings/security/DeviceList.tsx
'use client';

import { revokeSessionAction, revokeAllOtherSessionsAction } from './actions';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

interface Session {
  id: string;
  deviceName: string;
  deviceType: string;
  browser: string;
  os: string;
  ip: string;
  city: string | null;
  country: string | null;
  lastActiveAt: Date;
  token: string;
}

export function DeviceList({
  sessions,
  currentSessionToken,
}: {
  sessions: Session[];
  currentSessionToken?: string;
}) {
  const router = useRouter();
  const [revoking, setRevoking] = useState<string | null>(null);

  const deviceIcons: Record<string, string> = {
    desktop: '🖥️',
    mobile: '📱',
    tablet: '📱',
  };

  return (
    <div className="space-y-3">
      {sessions.map((s) => {
        const isCurrent = s.token === currentSessionToken;
        return (
          <div
            key={s.id}
            className={`flex items-center justify-between p-4 border rounded-lg ${
              isCurrent ? 'border-green-300 bg-green-50' : ''
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{deviceIcons[s.deviceType] ?? '💻'}</span>
              <div>
                <p className="font-medium">
                  {s.deviceName}
                  {isCurrent && (
                    <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                      Current
                    </span>
                  )}
                </p>
                <p className="text-sm text-gray-500">
                  {s.city && s.country ? `${s.city}, ${s.country}` : s.ip} ·{' '}
                  {new Date(s.lastActiveAt).toLocaleDateString()}
                </p>
              </div>
            </div>

            {!isCurrent && (
              <button
                onClick={async () => {
                  setRevoking(s.id);
                  await revokeSessionAction(s.id);
                  router.refresh();
                  setRevoking(null);
                }}
                disabled={revoking === s.id}
                className="text-red-600 text-sm hover:text-red-800 disabled:opacity-50"
              >
                {revoking === s.id ? 'Revoking...' : 'Revoke'}
              </button>
            )}
          </div>
        );
      })}

      {sessions.length > 1 && (
        <button
          onClick={async () => {
            await revokeAllOtherSessionsAction();
            router.refresh();
          }}
          className="w-full mt-4 py-2 text-red-600 border border-red-200 rounded-lg hover:bg-red-50"
        >
          Sign out of all other devices
        </button>
      )}
    </div>
  );
}
```

```tsx
// app/settings/security/actions.ts
'use server';

import { auth } from '@/auth';
import { revokeSession, revokeOtherSessions } from '@/lib/session-manager';
import { revalidatePath } from 'next/cache';

export async function revokeSessionAction(sessionId: string) {
  const session = await auth();
  if (!session?.user?.id) throw new Error('Unauthorized');

  await revokeSession(sessionId, session.user.id);
  revalidatePath('/settings/security');
}

export async function revokeAllOtherSessionsAction() {
  const session = await auth();
  if (!session?.user?.id) throw new Error('Unauthorized');

  const currentToken = session.user.currentSessionToken;
  if (!currentToken) throw new Error('No current session');

  const count = await revokeOtherSessions(currentToken, session.user.id);
  revalidatePath('/settings/security');
  return { revokedCount: count };
}
```

**Suspicious login detection heuristics**:
1. **New device** — browser/OS combination not seen before
2. **New location** — city/country not seen before
3. **Impossible travel** — login from NYC then London within 1 hour
4. **Multiple failures** — 5+ failed attempts in 10 minutes
5. **Unusual time** — login at 3AM when user typically logs in 9AM-6PM

**Production checklist**:
- Store sessions in database (not just JWT)
- Send email alerts for new devices/locations
- Allow users to revoke individual sessions
- Admin can force-logout any user
- Log all login attempts (success and failure) for audit trail
- Implement rate limiting on login endpoint
- Consider optional 2FA for suspicious logins
