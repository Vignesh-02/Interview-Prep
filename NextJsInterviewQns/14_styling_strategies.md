# 14. Styling Strategies in Next.js

## Topic Introduction

Styling in Next.js 15/16 with the App Router requires understanding how **Server Components** and **Client Components** impact your CSS choices. Not all styling solutions work the same way in the server-first architecture.

```
┌────────────────────────────────────────────────────────────┐
│            Next.js Styling Decision Tree                    │
│                                                            │
│  ┌─────────────────┐                                       │
│  │ Server Component │                                       │
│  │ (default)        │                                       │
│  └────────┬────────┘                                       │
│           │                                                │
│           ├── CSS Modules ✅ (zero JS, best perf)           │
│           ├── Tailwind CSS ✅ (compiled at build)           │
│           ├── Global CSS ✅ (imported in layout)            │
│           ├── Sass/SCSS ✅ (compiled at build)              │
│           ├── CSS-in-JS ❌ (needs runtime JS)              │
│           └── Inline styles ✅ (but not recommended)        │
│                                                            │
│  ┌─────────────────┐                                       │
│  │ Client Component │                                       │
│  │ ("use client")   │                                       │
│  └────────┬────────┘                                       │
│           │                                                │
│           ├── CSS Modules ✅                                │
│           ├── Tailwind CSS ✅                               │
│           ├── styled-components ✅ (with registry)          │
│           ├── Emotion ✅ (with registry)                    │
│           └── All CSS-in-JS ✅ (with proper setup)          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Performance comparison of styling approaches**:

```
┌───────────────────────────────────────────────────────────┐
│  Approach        │ Bundle Size │ Runtime Cost │ SSR       │
├──────────────────┼─────────────┼──────────────┼───────────┤
│  CSS Modules     │    0 JS     │    None      │ Full      │
│  Tailwind CSS    │    0 JS     │    None      │ Full      │
│  Sass/SCSS       │    0 JS     │    None      │ Full      │
│  Global CSS      │    0 JS     │    None      │ Full      │
│  styled-comp.    │  ~15KB JS   │    Medium    │ Registry  │
│  Emotion         │  ~11KB JS   │    Medium    │ Registry  │
│  Vanilla Extract │    0 JS     │    None      │ Full      │
└───────────────────────────────────────────────────────────┘
```

**Tailwind CSS v4** (released with Next.js 15+) brings significant changes:

```css
/* app/globals.css — Tailwind v4 (new CSS-first config) */
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #10b981;
  --font-sans: "Inter", sans-serif;
  --breakpoint-3xl: 1920px;
}
```

**shadcn/ui** has become the de-facto component library for Next.js production apps, combining Radix primitives with Tailwind styling:

```tsx
// components/ui/button.tsx (shadcn/ui pattern)
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  }
);
```

**Why this matters for senior developers**: Choosing the right styling strategy impacts bundle size, rendering performance, developer experience, and maintainability. In the App Router, zero-runtime CSS solutions (CSS Modules, Tailwind) have a significant advantage because they work natively with Server Components without any JS overhead.

---

## Q1. (Beginner) What are CSS Modules in Next.js and why are they the default styling recommendation?

**Scenario**: A new team member asks why the Next.js docs recommend CSS Modules over other approaches. Explain with examples.

**Answer**:

**CSS Modules** are CSS files where class names are automatically scoped to the component, preventing naming collisions. Next.js has built-in support — no configuration needed.

```
┌─────────────── CSS Modules Flow ───────────────┐
│                                                │
│  button.module.css                             │
│  .primary { background: blue; }                │
│       │                                        │
│       ▼ (build time transformation)            │
│                                                │
│  .button_primary__x7ks2 { background: blue; }  │
│                                                │
│  Zero runtime JS. Pure CSS.                    │
└────────────────────────────────────────────────┘
```

```css
/* app/components/Button.module.css */
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 150ms ease;
  cursor: pointer;
}

.primary {
  composes: button;
  background-color: #3b82f6;
  color: white;
}

.primary:hover {
  background-color: #2563eb;
}

.secondary {
  composes: button;
  background-color: transparent;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.secondary:hover {
  background-color: #eff6ff;
}

.large {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
}

.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

```tsx
// app/components/Button.tsx — Server Component (no "use client" needed!)
import styles from './Button.module.css';

interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'default' | 'large';
  disabled?: boolean;
  children: React.ReactNode;
}

export function Button({
  variant = 'primary',
  size = 'default',
  disabled = false,
  children,
}: ButtonProps) {
  const className = [
    styles[variant],
    size === 'large' && styles.large,
    disabled && styles.disabled,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button className={className} disabled={disabled}>
      {children}
    </button>
  );
}
```

**Why CSS Modules are recommended**:

| Benefit | Explanation |
|---------|-------------|
| Zero JS runtime | Styles compile to static CSS — no JavaScript needed |
| Server Component compatible | Works in both Server and Client Components |
| Scoped by default | No class name collisions across components |
| TypeScript support | Can generate `.d.ts` files for type-safe class names |
| No configuration | Built into Next.js out of the box |
| Great performance | No FOUC, no style injection, pure CSS |

**TypeScript support for CSS Modules**:

```bash
npm install -D typescript-plugin-css-modules
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "plugins": [
      { "name": "typescript-plugin-css-modules" }
    ]
  }
}
```

**When NOT to use CSS Modules**: When you need highly dynamic styles based on props (many conditional classes), Tailwind CSS or CSS-in-JS may be more ergonomic. CSS Modules require separate `.css` files, which can feel verbose for utility-heavy designs.

---

## Q2. (Beginner) How do you set up and configure Tailwind CSS in a Next.js 15 project?

**Scenario**: You're starting a new Next.js 15 project and need to set up Tailwind CSS with a custom design system.

**Answer**:

**Tailwind CSS v4** (latest with Next.js 15) uses a CSS-first configuration approach:

```bash
npx create-next-app@latest my-app --tailwind
# OR add to existing project:
npm install tailwindcss @tailwindcss/postcss postcss
```

**Tailwind v4 setup (CSS-first config)**:

```css
/* app/globals.css */
@import "tailwindcss";

/* Custom theme using @theme directive (Tailwind v4) */
@theme {
  /* Colors */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-900: #1e3a5f;

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;

  /* Typography */
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  /* Spacing */
  --spacing-18: 4.5rem;
  --spacing-88: 22rem;

  /* Breakpoints */
  --breakpoint-xs: 475px;
  --breakpoint-3xl: 1920px;

  /* Border radius */
  --radius-button: 0.5rem;
  --radius-card: 0.75rem;

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-card-hover: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
}

/* Custom utilities */
@utility container-narrow {
  max-width: 768px;
  margin-inline: auto;
  padding-inline: 1rem;
}

/* Custom variants */
@custom-variant hocus (&:hover, &:focus);

/* Layer overrides for base styles */
@layer base {
  html {
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
  }

  body {
    @apply bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-100;
  }
}
```

**PostCSS config** (Tailwind v4):

```js
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

**Tailwind v3 setup (still widely used, JS config)**:

```js
// tailwind.config.ts (Tailwind v3)
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class', // or 'media'
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
};

export default config;
```

**Usage in components**:

```tsx
// app/components/Card.tsx — Server Component with Tailwind
interface CardProps {
  title: string;
  description: string;
  badge?: string;
}

export function Card({ title, description, badge }: CardProps) {
  return (
    <div className="group rounded-card border border-gray-200 bg-white p-6 shadow-card transition-shadow hover:shadow-card-hover dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-start justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        {badge && (
          <span className="rounded-full bg-primary-100 px-2.5 py-0.5 text-xs font-medium text-primary-700 dark:bg-primary-900 dark:text-primary-100">
            {badge}
          </span>
        )}
      </div>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}
```

**Key point**: Tailwind produces zero JavaScript at runtime — all styles are compiled to static CSS at build time, making it ideal for Server Components.

---

## Q3. (Beginner) How do you implement dark mode in a Next.js app with Tailwind CSS?

**Scenario**: Your app needs to support light mode, dark mode, and "system preference" with a toggle. The setting should persist and not cause a flash of wrong theme (FOUC).

**Answer**:

```
┌─────────────── Dark Mode Strategy ─────────────┐
│                                                │
│  Option 1: class-based (recommended)           │
│  <html class="dark"> → .dark\:bg-gray-900      │
│  ├── Full control                              │
│  ├── Toggle-able                               │
│  └── Persists via localStorage + cookie        │
│                                                │
│  Option 2: media-based                         │
│  @media (prefers-color-scheme: dark)           │
│  ├── Follows system only                       │
│  └── No user control                           │
│                                                │
│  Anti-FOUC Strategy:                           │
│  1. Read cookie in Server Component            │
│  2. Set class="dark" on <html> in layout       │
│  3. No flash — correct theme from first paint  │
└────────────────────────────────────────────────┘
```

**Step 1: Configure Tailwind** (v3: `tailwind.config.ts`, v4: `globals.css`):

```js
// tailwind.config.ts (v3)
export default {
  darkMode: 'class',
  // ...
};
```

```css
/* globals.css (v4) — dark mode is class-based by default */
@import "tailwindcss";
@custom-variant dark (&:where(.dark, .dark *));
```

**Step 2: Theme script to prevent FOUC** (runs before React hydration):

```tsx
// app/components/ThemeScript.tsx
export function ThemeScript() {
  // This inline script runs synchronously before paint to prevent FOUC
  const script = `
    (function() {
      try {
        var stored = localStorage.getItem('theme');
        var systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var dark = stored === 'dark' || (!stored && systemDark);
        document.documentElement.classList.toggle('dark', dark);
      } catch(e) {}
    })();
  `;

  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
```

**Step 3: Server-side theme detection via cookies**:

```tsx
// app/layout.tsx
import { cookies } from 'next/headers';
import { ThemeScript } from './components/ThemeScript';
import { ThemeProvider } from './components/ThemeProvider';
import './globals.css';

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const theme = cookieStore.get('theme')?.value ?? 'system';

  return (
    <html lang="en" className={theme === 'dark' ? 'dark' : ''} suppressHydrationWarning>
      <head>
        <ThemeScript />
      </head>
      <body className="bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 transition-colors">
        <ThemeProvider initialTheme={theme}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
```

**Step 4: Theme provider and toggle**:

```tsx
// app/components/ThemeProvider.tsx
'use client';

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

export function ThemeProvider({
  children,
  initialTheme,
}: {
  children: React.ReactNode;
  initialTheme: string;
}) {
  const [theme, setThemeState] = useState<Theme>((initialTheme as Theme) ?? 'system');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  const applyTheme = useCallback((newTheme: Theme) => {
    const isDark =
      newTheme === 'dark' ||
      (newTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);

    document.documentElement.classList.toggle('dark', isDark);
    setResolvedTheme(isDark ? 'dark' : 'light');
  }, []);

  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
      localStorage.setItem('theme', newTheme);

      // Set cookie for SSR
      document.cookie = `theme=${newTheme};path=/;max-age=${365 * 24 * 60 * 60};samesite=lax`;

      applyTheme(newTheme);
    },
    [applyTheme]
  );

  useEffect(() => {
    applyTheme(theme);

    // Listen for system preference changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      if (theme === 'system') applyTheme('system');
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [theme, applyTheme]);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

```tsx
// app/components/ThemeToggle.tsx
'use client';

import { useTheme } from './ThemeProvider';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 rounded-lg border border-gray-200 dark:border-gray-700 p-1">
      {(['light', 'system', 'dark'] as const).map((t) => (
        <button
          key={t}
          onClick={() => setTheme(t)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            theme === t
              ? 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-white'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          {t === 'light' ? '☀️' : t === 'dark' ? '🌙' : '💻'} {t.charAt(0).toUpperCase() + t.slice(1)}
        </button>
      ))}
    </div>
  );
}
```

**Anti-FOUC strategy summary**: Cookie-based theme → set `class="dark"` on `<html>` in the Server Component → inline script as safety net → no flash on any navigation type.

---

## Q4. (Beginner) How do you use global styles and import external fonts in Next.js?

**Scenario**: You need to set up Inter as the primary font, add global reset styles, and ensure fonts load efficiently without layout shift.

**Answer**:

```tsx
// app/layout.tsx — Using next/font (recommended)
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap', // Prevent FOIT
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
```

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --font-sans: var(--font-sans, "Inter", ui-sans-serif, system-ui, sans-serif);
  --font-mono: var(--font-mono, "JetBrains Mono", ui-monospace, monospace);
}

/* Global resets */
@layer base {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  html {
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    scroll-behavior: smooth;
  }

  body {
    margin: 0;
    line-height: 1.6;
  }

  /* Focus visible outline for accessibility */
  :focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
  }

  /* Reduce motion for users who prefer it */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }

  /* Typography defaults */
  h1 { @apply text-4xl font-bold tracking-tight; }
  h2 { @apply text-3xl font-semibold tracking-tight; }
  h3 { @apply text-2xl font-semibold; }
  h4 { @apply text-xl font-semibold; }

  /* Form defaults */
  input, textarea, select {
    @apply rounded-lg border border-gray-300 px-3 py-2 text-sm;
    @apply focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 focus:outline-none;
    @apply dark:border-gray-700 dark:bg-gray-900 dark:text-white;
  }
}
```

**Using local fonts**:

```tsx
// app/layout.tsx — Local font files
import localFont from 'next/font/local';

const customFont = localFont({
  src: [
    { path: '../public/fonts/CustomFont-Regular.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/CustomFont-Medium.woff2', weight: '500', style: 'normal' },
    { path: '../public/fonts/CustomFont-Bold.woff2', weight: '700', style: 'normal' },
  ],
  variable: '--font-custom',
  display: 'swap',
  preload: true,
});
```

**Why `next/font`**:
- **Zero layout shift** — fonts are self-hosted and preloaded
- **No external requests** — Google Fonts are downloaded at build time
- **Automatic `font-display: swap`** — configurable per font
- **CSS variable support** — integrates cleanly with Tailwind

| Approach | Layout Shift | External Request | Bundle Impact |
|----------|-------------|-----------------|---------------|
| `next/font/google` | None | None (build-time) | Optimal |
| `next/font/local` | None | None | Optimal |
| `<link>` Google Fonts | Possible | Yes | Not recommended |
| `@import` in CSS | Yes | Yes | Worst |

---

## Q5. (Beginner) What are the limitations of CSS-in-JS with Server Components, and how do you work around them?

**Scenario**: Your team has been using styled-components. You're migrating to Next.js 15 App Router and some components break.

**Answer**:

**The core problem**: CSS-in-JS libraries like styled-components and Emotion generate styles at **runtime using JavaScript**. Server Components don't send JavaScript to the client, so there's no JS to execute the style generation.

```
┌─────────── CSS-in-JS Problem ─────────────────┐
│                                                │
│  Server Component (no JS sent to client)       │
│  ┌─────────────────────────────────────────┐   │
│  │ const Title = styled.h1`                │   │
│  │   color: blue;                          │   │
│  │ `;                                      │   │
│  │                                         │   │
│  │ ❌ FAILS — styled() needs client JS     │   │
│  └─────────────────────────────────────────┘   │
│                                                │
│  Client Component (JS sent to client)          │
│  ┌─────────────────────────────────────────┐   │
│  │ 'use client';                           │   │
│  │ const Title = styled.h1`                │   │
│  │   color: blue;                          │   │
│  │ `;                                      │   │
│  │                                         │   │
│  │ ✅ Works — but needs style registry     │   │
│  │    for SSR to prevent FOUC             │   │
│  └─────────────────────────────────────────┘   │
│                                                │
└────────────────────────────────────────────────┘
```

**Setting up styled-components with App Router (style registry)**:

```tsx
// lib/registry.tsx
'use client';

import React, { useState } from 'react';
import { useServerInsertedHTML } from 'next/navigation';
import { ServerStyleSheet, StyleSheetManager } from 'styled-components';

export function StyledComponentsRegistry({ children }: { children: React.ReactNode }) {
  const [styledComponentsStyleSheet] = useState(() => new ServerStyleSheet());

  useServerInsertedHTML(() => {
    const styles = styledComponentsStyleSheet.getStyleElement();
    styledComponentsStyleSheet.instance.clearTag();
    return <>{styles}</>;
  });

  if (typeof window !== 'undefined') return <>{children}</>;

  return (
    <StyleSheetManager sheet={styledComponentsStyleSheet.instance}>
      {children}
    </StyleSheetManager>
  );
}
```

```tsx
// app/layout.tsx
import { StyledComponentsRegistry } from '@/lib/registry';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <StyledComponentsRegistry>
          {children}
        </StyledComponentsRegistry>
      </body>
    </html>
  );
}
```

```tsx
// app/components/StyledCard.tsx
'use client'; // MUST be a Client Component

import styled from 'styled-components';

const CardWrapper = styled.div`
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 1px solid #e5e7eb;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  }
`;

const Title = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
`;

export function StyledCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <CardWrapper>
      <Title>{title}</Title>
      {children}
    </CardWrapper>
  );
}
```

**Migration strategy** — move away from CSS-in-JS:

| From | To | Effort |
|------|----|--------|
| styled-components | Tailwind CSS | Medium (rewrite styles) |
| styled-components | CSS Modules | Medium (separate files) |
| Emotion | Tailwind CSS | Medium |
| CSS-in-JS (any) | Vanilla Extract | Low (similar API, zero runtime) |

**Recommendation for new projects**: Avoid runtime CSS-in-JS in the App Router. Use Tailwind CSS, CSS Modules, or Vanilla Extract for zero-runtime styling that works natively with Server Components.

---

## Q6. (Intermediate) How do you build a responsive design system with Tailwind CSS and CSS variables for a production Next.js app?

**Scenario**: Your design team has defined a comprehensive design system with responsive typography, spacing scales, and component tokens. Implement it with Tailwind CSS.

**Answer**:

```css
/* app/globals.css — Design system with CSS variables and Tailwind */
@import "tailwindcss";

@theme {
  /* === Color Tokens === */
  /* Neutral */
  --color-neutral-50: #fafafa;
  --color-neutral-100: #f5f5f5;
  --color-neutral-200: #e5e5e5;
  --color-neutral-300: #d4d4d4;
  --color-neutral-400: #a3a3a3;
  --color-neutral-500: #737373;
  --color-neutral-600: #525252;
  --color-neutral-700: #404040;
  --color-neutral-800: #262626;
  --color-neutral-900: #171717;
  --color-neutral-950: #0a0a0a;

  /* Brand */
  --color-brand-50: #eef2ff;
  --color-brand-100: #e0e7ff;
  --color-brand-500: #6366f1;
  --color-brand-600: #4f46e5;
  --color-brand-700: #4338ca;

  /* Semantic */
  --color-surface: var(--color-neutral-50);
  --color-surface-elevated: #ffffff;
  --color-text-primary: var(--color-neutral-900);
  --color-text-secondary: var(--color-neutral-500);
  --color-text-inverse: #ffffff;
  --color-border: var(--color-neutral-200);
  --color-ring: var(--color-brand-500);

  /* === Typography Scale === */
  --text-xs: 0.75rem;
  --text-xs--line-height: 1rem;
  --text-sm: 0.875rem;
  --text-sm--line-height: 1.25rem;
  --text-base: 1rem;
  --text-base--line-height: 1.5rem;
  --text-lg: 1.125rem;
  --text-lg--line-height: 1.75rem;
  --text-xl: 1.25rem;
  --text-xl--line-height: 1.75rem;
  --text-2xl: 1.5rem;
  --text-2xl--line-height: 2rem;
  --text-3xl: 1.875rem;
  --text-3xl--line-height: 2.25rem;
  --text-4xl: 2.25rem;
  --text-4xl--line-height: 2.5rem;
  --text-5xl: 3rem;
  --text-5xl--line-height: 1.16;

  /* === Spacing === */
  --spacing-page-x: 1rem;
  --spacing-section-y: 4rem;
  --spacing-card-padding: 1.5rem;

  /* === Shadows === */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);

  /* === Radius === */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  /* === Animation === */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;

  /* === Breakpoints === */
  --breakpoint-xs: 475px;
  --breakpoint-3xl: 1920px;
}

/* Dark mode overrides */
.dark {
  --color-surface: var(--color-neutral-950);
  --color-surface-elevated: var(--color-neutral-900);
  --color-text-primary: var(--color-neutral-50);
  --color-text-secondary: var(--color-neutral-400);
  --color-border: var(--color-neutral-800);
}

/* Responsive spacing overrides */
@media (min-width: 768px) {
  :root {
    --spacing-page-x: 2rem;
    --spacing-section-y: 6rem;
  }
}

@media (min-width: 1280px) {
  :root {
    --spacing-page-x: 4rem;
    --spacing-section-y: 8rem;
  }
}
```

**Utility function for conditional classes**:

```tsx
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Design system components**:

```tsx
// components/ui/Typography.tsx
import { cn } from '@/lib/utils';

type TypographyVariant = 'h1' | 'h2' | 'h3' | 'h4' | 'body' | 'body-sm' | 'caption';

const variantClasses: Record<TypographyVariant, string> = {
  h1: 'text-4xl font-bold tracking-tight md:text-5xl',
  h2: 'text-3xl font-semibold tracking-tight md:text-4xl',
  h3: 'text-2xl font-semibold md:text-3xl',
  h4: 'text-xl font-semibold md:text-2xl',
  body: 'text-base text-text-secondary',
  'body-sm': 'text-sm text-text-secondary',
  caption: 'text-xs text-text-secondary',
};

const variantElements: Record<TypographyVariant, keyof JSX.IntrinsicElements> = {
  h1: 'h1', h2: 'h2', h3: 'h3', h4: 'h4',
  body: 'p', 'body-sm': 'p', caption: 'span',
};

interface TypographyProps {
  variant: TypographyVariant;
  children: React.ReactNode;
  className?: string;
  as?: keyof JSX.IntrinsicElements;
}

export function Typography({ variant, children, className, as }: TypographyProps) {
  const Component = as ?? variantElements[variant];
  return <Component className={cn(variantClasses[variant], className)}>{children}</Component>;
}
```

```tsx
// components/ui/Container.tsx
import { cn } from '@/lib/utils';

interface ContainerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: React.ReactNode;
  className?: string;
}

const sizeClasses = {
  sm: 'max-w-2xl',
  md: 'max-w-4xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
  full: 'max-w-full',
};

export function Container({ size = 'xl', children, className }: ContainerProps) {
  return (
    <div className={cn('mx-auto w-full px-[var(--spacing-page-x)]', sizeClasses[size], className)}>
      {children}
    </div>
  );
}
```

**Responsive layout patterns**:

```tsx
// app/dashboard/page.tsx
import { Container } from '@/components/ui/Container';
import { Typography } from '@/components/ui/Typography';

export default function DashboardPage() {
  return (
    <Container>
      <div className="py-[var(--spacing-section-y)]">
        <Typography variant="h1">Dashboard</Typography>

        {/* Responsive grid: 1 col → 2 col → 3 col */}
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard title="Revenue" value="$45,231" change="+12.5%" />
          <StatCard title="Users" value="2,350" change="+3.2%" />
          <StatCard title="Orders" value="1,247" change="-0.4%" />
        </div>

        {/* Sidebar layout on desktop */}
        <div className="mt-12 flex flex-col gap-8 lg:flex-row">
          <div className="flex-1">{/* Main content */}</div>
          <aside className="w-full lg:w-80">{/* Sidebar */}</aside>
        </div>
      </div>
    </Container>
  );
}

function StatCard({ title, value, change }: { title: string; value: string; change: string }) {
  const isPositive = change.startsWith('+');
  return (
    <div className="rounded-lg border border-border bg-surface-elevated p-[var(--spacing-card-padding)] shadow-sm">
      <p className="text-sm text-text-secondary">{title}</p>
      <p className="mt-1 text-3xl font-bold text-text-primary">{value}</p>
      <p className={cn('mt-1 text-sm', isPositive ? 'text-green-600' : 'text-red-600')}>
        {change}
      </p>
    </div>
  );
}
```

**Key design system principles**: Use CSS variables for semantic tokens (colors, spacing) so dark mode and responsive overrides work through variable reassignment rather than class duplication.

---

## Q7. (Intermediate) How do you set up and use Sass/SCSS with Next.js, and when should you choose it over Tailwind or CSS Modules?

**Scenario**: Your existing project uses a large SCSS design system with mixins, functions, and complex nesting. How do you integrate it with Next.js 15?

**Answer**:

```bash
npm install -D sass
```

Next.js supports Sass out of the box — no extra configuration. Both `.scss` and `.sass` extensions work.

```scss
// styles/_variables.scss — Design tokens
$colors: (
  'primary': (
    50: #eff6ff,
    100: #dbeafe,
    500: #3b82f6,
    600: #2563eb,
    700: #1d4ed8,
  ),
  'neutral': (
    50: #fafafa,
    100: #f5f5f5,
    200: #e5e5e5,
    700: #404040,
    900: #171717,
  ),
);

$breakpoints: (
  'sm': 640px,
  'md': 768px,
  'lg': 1024px,
  'xl': 1280px,
);

$font-sizes: (
  'xs': 0.75rem,
  'sm': 0.875rem,
  'base': 1rem,
  'lg': 1.125rem,
  'xl': 1.25rem,
  '2xl': 1.5rem,
  '3xl': 1.875rem,
  '4xl': 2.25rem,
);

$spacing-unit: 0.25rem;
$border-radius: 0.5rem;
$transition-duration: 200ms;
```

```scss
// styles/_mixins.scss — Reusable patterns
@use 'variables' as *;

// Responsive breakpoint mixin
@mixin respond-to($breakpoint) {
  $value: map-get($breakpoints, $breakpoint);
  @if $value {
    @media (min-width: $value) {
      @content;
    }
  } @else {
    @warn "Unknown breakpoint: #{$breakpoint}";
  }
}

// Typography mixin
@mixin font-size($size) {
  font-size: map-get($font-sizes, $size);
}

// Color helper
@function color($name, $shade: 500) {
  $palette: map-get($colors, $name);
  @return map-get($palette, $shade);
}

// Truncate text
@mixin truncate($lines: 1) {
  @if $lines == 1 {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  } @else {
    display: -webkit-box;
    -webkit-line-clamp: $lines;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

// Focus ring
@mixin focus-ring {
  &:focus-visible {
    outline: 2px solid color('primary', 500);
    outline-offset: 2px;
  }
}

// Flex center
@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}
```

**Usage with CSS Modules (SCSS Modules)**:

```scss
// app/components/Card.module.scss
@use '@/styles/mixins' as *;
@use '@/styles/variables' as *;

.card {
  padding: $spacing-unit * 6;
  border-radius: $border-radius;
  border: 1px solid color('neutral', 200);
  background: white;
  transition: box-shadow $transition-duration ease;

  &:hover {
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
  }

  &__title {
    @include font-size('lg');
    font-weight: 600;
    color: color('neutral', 900);
    @include truncate(1);
  }

  &__description {
    @include font-size('sm');
    color: color('neutral', 700);
    margin-top: $spacing-unit * 2;
    @include truncate(3);
  }

  &__footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: $spacing-unit * 4;
    padding-top: $spacing-unit * 4;
    border-top: 1px solid color('neutral', 200);
  }
}

// Responsive variant
.cardGrid {
  display: grid;
  grid-template-columns: 1fr;
  gap: $spacing-unit * 6;

  @include respond-to('sm') {
    grid-template-columns: repeat(2, 1fr);
  }

  @include respond-to('lg') {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

```tsx
// app/components/Card.tsx
import styles from './Card.module.scss';

interface CardProps {
  title: string;
  description: string;
  author: string;
  date: string;
}

export function Card({ title, description, author, date }: CardProps) {
  return (
    <div className={styles.card}>
      <h3 className={styles.card__title}>{title}</h3>
      <p className={styles.card__description}>{description}</p>
      <div className={styles.card__footer}>
        <span>{author}</span>
        <span>{date}</span>
      </div>
    </div>
  );
}
```

**Configure Sass import paths** in `next.config.ts`:

```tsx
// next.config.ts
const nextConfig = {
  sassOptions: {
    includePaths: ['./styles'],
    prependData: `@use "variables" as *; @use "mixins" as *;`,
  },
};

export default nextConfig;
```

**When to choose Sass over Tailwind**:

| Scenario | Recommendation |
|----------|---------------|
| Existing large SCSS codebase | Keep Sass |
| Complex mathematical calculations | Sass functions |
| Need BEM methodology | Sass nesting |
| Starting fresh | Tailwind CSS |
| Rapid prototyping | Tailwind CSS |
| Design system with tokens | Either (CSS variables bridge both) |

---

## Q8. (Intermediate) How do you integrate shadcn/ui with Next.js and customize it for a production design system?

**Scenario**: Your team decides to use shadcn/ui as the base component library. Set it up, customize the theme, and create composite components.

**Answer**:

**shadcn/ui** is not a component library you install — it's a collection of copy-paste components built on Radix UI primitives and Tailwind CSS. You own the code.

```bash
# Initialize shadcn/ui
npx shadcn@latest init

# Add components
npx shadcn@latest add button dialog card input select table toast
```

**Project structure after setup**:

```
app/
├── globals.css          ← Theme variables
components/
├── ui/
│   ├── button.tsx       ← shadcn components (you own these)
│   ├── dialog.tsx
│   ├── card.tsx
│   └── input.tsx
lib/
└── utils.ts             ← cn() helper
components.json          ← shadcn config
```

**Customizing the theme** (`app/globals.css`):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 243 75% 59%;       /* Indigo - custom brand */
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 243 75% 59%;
    --radius: 0.5rem;

    /* Custom additions */
    --success: 142 76% 36%;
    --success-foreground: 0 0% 98%;
    --warning: 38 92% 50%;
    --warning-foreground: 0 0% 9%;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --primary: 243 75% 65%;
    --primary-foreground: 0 0% 9%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 243 75% 65%;
  }
}
```

**Extending shadcn/ui Button with custom variants**:

```tsx
// components/ui/button.tsx (customized)
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
        // Custom variants
        success: 'bg-[hsl(var(--success))] text-[hsl(var(--success-foreground))] hover:bg-[hsl(var(--success))]/90',
        warning: 'bg-[hsl(var(--warning))] text-[hsl(var(--warning-foreground))] hover:bg-[hsl(var(--warning))]/90',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        xl: 'h-12 rounded-lg px-10 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {rightIcon && <span className="ml-2">{rightIcon}</span>}
      </Comp>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
```

**Composite component using shadcn/ui primitives**:

```tsx
// components/ConfirmDialog.tsx
'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

interface ConfirmDialogProps {
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'default' | 'destructive';
  onConfirm: () => Promise<void> | void;
  trigger: React.ReactNode;
}

export function ConfirmDialog({
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'default',
  onConfirm,
  trigger,
}: ConfirmDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleConfirm() {
    setLoading(true);
    try {
      await onConfirm();
      setOpen(false);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            {cancelText}
          </Button>
          <Button
            variant={variant === 'destructive' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            loading={loading}
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

**Why shadcn/ui for production**:
1. **You own the code** — full control, no version lock-in
2. **Accessible by default** — built on Radix primitives (WAI-ARIA)
3. **Tailwind-native** — consistent with your styling approach
4. **Tree-shakeable** — only import what you use
5. **Customizable** — modify any component to match your design system

---

## Q9. (Intermediate) How do you implement responsive and container-query-based layouts in Next.js?

**Scenario**: You need components that adapt based on their container width (not the viewport) — for example, a card that shows differently in a sidebar vs. main content area.

**Answer**:

```
┌────────────── Container Queries vs Media Queries ──────────────┐
│                                                                │
│  Media Query: responds to VIEWPORT width                       │
│  @media (min-width: 768px) { ... }                             │
│                                                                │
│  Container Query: responds to CONTAINER width                  │
│  @container (min-width: 400px) { ... }                         │
│                                                                │
│  ┌───── Sidebar (300px) ─────┐  ┌──── Main (800px) ────────┐  │
│  │  ┌───────────────────┐    │  │  ┌──────────────────────┐ │  │
│  │  │ Card (compact)    │    │  │  │ Card (full layout)   │ │  │
│  │  │ [stacked layout]  │    │  │  │ [horizontal layout]  │ │  │
│  │  └───────────────────┘    │  │  └──────────────────────┘ │  │
│  └───────────────────────────┘  └───────────────────────────┘  │
│                                                                │
│  Same component, different layout based on container!          │
└────────────────────────────────────────────────────────────────┘
```

**Tailwind CSS container queries** (built-in with `@tailwindcss/container-queries`):

```tsx
// For Tailwind v3, install the plugin:
// npm install @tailwindcss/container-queries

// tailwind.config.ts (v3)
import containerQueries from '@tailwindcss/container-queries';
export default {
  plugins: [containerQueries],
};

// Tailwind v4: container queries are built-in, no plugin needed
```

```tsx
// components/AdaptiveCard.tsx — Server Component
import { cn } from '@/lib/utils';

interface AdaptiveCardProps {
  title: string;
  description: string;
  image: string;
  author: string;
  date: string;
}

export function AdaptiveCard({ title, description, image, author, date }: AdaptiveCardProps) {
  return (
    // @container marks this as a container query context
    <div className="@container">
      <div
        className={cn(
          // Base: stacked layout (small container)
          'flex flex-col gap-4 rounded-lg border p-4',
          // When container >= 400px: horizontal layout
          '@[400px]:flex-row @[400px]:items-start',
          // When container >= 600px: larger spacing
          '@[600px]:gap-6 @[600px]:p-6'
        )}
      >
        <img
          src={image}
          alt={title}
          className={cn(
            // Base: full width
            'w-full rounded-md object-cover',
            // 400px+ container: fixed width thumbnail
            '@[400px]:w-40 @[400px]:h-28',
            // 600px+ container: larger thumbnail
            '@[600px]:w-56 @[600px]:h-36'
          )}
        />
        <div className="flex-1">
          <h3
            className={cn(
              'font-semibold text-gray-900 dark:text-white',
              'text-base @[400px]:text-lg @[600px]:text-xl'
            )}
          >
            {title}
          </h3>
          <p
            className={cn(
              'mt-1 text-sm text-gray-600 dark:text-gray-400',
              'line-clamp-2 @[400px]:line-clamp-3 @[600px]:line-clamp-none'
            )}
          >
            {description}
          </p>
          <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
            <span>{author}</span>
            <span>·</span>
            <span>{date}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Usage in different contexts — same component, different layouts**:

```tsx
// app/dashboard/page.tsx
import { AdaptiveCard } from '@/components/AdaptiveCard';

export default function DashboardPage() {
  const article = {
    title: 'Understanding React Server Components',
    description: 'A deep dive into how RSC works and why it matters for production apps...',
    image: '/images/rsc.jpg',
    author: 'Jane Doe',
    date: 'Feb 15, 2026',
  };

  return (
    <div className="flex gap-6 p-6">
      {/* Sidebar: card renders in compact mode */}
      <aside className="w-72">
        <h2 className="mb-4 font-semibold">Recent</h2>
        <AdaptiveCard {...article} />
      </aside>

      {/* Main content: same card renders in full mode */}
      <main className="flex-1">
        <h2 className="mb-4 font-semibold">Featured</h2>
        <AdaptiveCard {...article} />
      </main>
    </div>
  );
}
```

**Named containers for nested queries**:

```tsx
// components/DashboardWidget.tsx
export function DashboardWidget({ children }: { children: React.ReactNode }) {
  return (
    <div className="@container/widget rounded-lg border bg-white p-4 dark:bg-gray-900">
      {/* Child elements can query @[size]/widget */}
      {children}
    </div>
  );
}

export function WidgetChart({ data }: { data: number[] }) {
  return (
    <div className={cn(
      'h-32 @[300px]/widget:h-48 @[500px]/widget:h-64',
    )}>
      {/* Chart adapts to widget container size */}
    </div>
  );
}
```

**CSS Modules with container queries** (no Tailwind):

```css
/* components/Card.module.css */
.wrapper {
  container-type: inline-size;
  container-name: card;
}

.card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
}

@container card (min-width: 400px) {
  .card {
    flex-direction: row;
    align-items: flex-start;
  }

  .image {
    width: 10rem;
    flex-shrink: 0;
  }
}

@container card (min-width: 600px) {
  .card {
    gap: 1.5rem;
    padding: 1.5rem;
  }
}
```

**Key points**: Container queries make components truly self-contained — they adapt to their context rather than the viewport. This is essential for dashboard layouts, sidebar panels, and reusable component libraries.

---

## Q10. (Intermediate) How do you handle conditional and dynamic styling patterns in Next.js while maintaining performance?

**Scenario**: You have components that need styling based on dynamic data (user preferences, API data, runtime state). How do you handle this efficiently without sacrificing Server Component compatibility?

**Answer**:

```
┌──────────── Dynamic Styling Approaches ────────────┐
│                                                    │
│  Approach 1: Data Attribute Selectors              │
│  Server Component compatible ✅                    │
│  <div data-variant="primary" />                    │
│  [data-variant="primary"] { color: blue; }         │
│                                                    │
│  Approach 2: CSS Variables (inline)                │
│  Server Component compatible ✅                    │
│  <div style={{ '--progress': '75%' }} />           │
│  .bar { width: var(--progress); }                  │
│                                                    │
│  Approach 3: Class merging (Tailwind)              │
│  Server Component compatible ✅                    │
│  cn('base', variant === 'primary' && 'bg-blue')   │
│                                                    │
│  Approach 4: CSS-in-JS (styled)                    │
│  Client Component only ❌ (SC)                     │
│  styled.div<{ variant: string }>`...`              │
└────────────────────────────────────────────────────┘
```

**Pattern 1: Data attributes for server-side dynamic styling**:

```css
/* components/Badge.module.css */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge[data-variant='success'] {
  background-color: #dcfce7;
  color: #166534;
}

.badge[data-variant='warning'] {
  background-color: #fef3c7;
  color: #92400e;
}

.badge[data-variant='error'] {
  background-color: #fecaca;
  color: #991b1b;
}

.badge[data-variant='info'] {
  background-color: #dbeafe;
  color: #1e40af;
}
```

```tsx
// components/Badge.tsx — Server Component, dynamic styling via data attributes
import styles from './Badge.module.css';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span className={styles.badge} data-variant={variant}>
      {children}
    </span>
  );
}

// Usage in Server Component — data comes from database
export async function OrderStatus({ orderId }: { orderId: string }) {
  const order = await prisma.order.findUnique({ where: { id: orderId } });
  const variantMap: Record<string, BadgeVariant> = {
    pending: 'warning',
    completed: 'success',
    failed: 'error',
    processing: 'info',
  };
  return <Badge variant={variantMap[order?.status ?? 'pending']}>{order?.status}</Badge>;
}
```

**Pattern 2: CSS custom properties for computed values**:

```tsx
// components/ProgressBar.tsx — Server Component
interface ProgressBarProps {
  value: number;     // 0-100
  color?: string;    // any CSS color
  height?: number;   // pixels
}

export function ProgressBar({ value, color = '#3b82f6', height = 8 }: ProgressBarProps) {
  return (
    <div
      className="w-full rounded-full bg-gray-200 dark:bg-gray-700"
      style={{ height: `${height}px` } as React.CSSProperties}
    >
      <div
        className="rounded-full transition-all duration-500 ease-out"
        style={
          {
            '--progress': `${Math.min(100, Math.max(0, value))}%`,
            width: 'var(--progress)',
            height: '100%',
            backgroundColor: color,
          } as React.CSSProperties
        }
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      />
    </div>
  );
}
```

**Pattern 3: Dynamic Tailwind classes with safelist**:

```tsx
// components/UserAvatar.tsx — Server Component
import { cn } from '@/lib/utils';

const colorVariants = {
  red: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  green: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  purple: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
  orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
} as const;

type AvatarColor = keyof typeof colorVariants;

function getColorFromName(name: string): AvatarColor {
  const colors = Object.keys(colorVariants) as AvatarColor[];
  const index = name.charCodeAt(0) % colors.length;
  return colors[index];
}

interface UserAvatarProps {
  name: string;
  image?: string | null;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-14 w-14 text-lg',
};

export function UserAvatar({ name, image, size = 'md' }: UserAvatarProps) {
  if (image) {
    return (
      <img
        src={image}
        alt={name}
        className={cn('rounded-full object-cover', sizeClasses[size])}
      />
    );
  }

  const color = getColorFromName(name);
  const initials = name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className={cn(
        'inline-flex items-center justify-center rounded-full font-medium',
        sizeClasses[size],
        colorVariants[color]
      )}
    >
      {initials}
    </div>
  );
}
```

**Pattern 4: Theme-aware components with CSS variables**:

```tsx
// components/BrandedSection.tsx — Server Component
interface BrandedSectionProps {
  brandColor: string;  // From database: "#ff6b35"
  children: React.ReactNode;
}

export function BrandedSection({ brandColor, children }: BrandedSectionProps) {
  return (
    <section
      style={
        {
          '--brand': brandColor,
          '--brand-light': `${brandColor}20`,
        } as React.CSSProperties
      }
      className="rounded-lg border-l-4 border-l-[var(--brand)] bg-[var(--brand-light)] p-6"
    >
      {children}
    </section>
  );
}
```

**Key rule**: For Server Components, use CSS variables, data attributes, or pre-defined class maps. Avoid template literals in class names (e.g., `bg-${color}-500`) — Tailwind can't detect these at build time.

---

## Q11. (Intermediate) How do you implement a production theming system with multiple brand themes in Next.js?

**Scenario**: Your white-label SaaS product needs to support different themes per tenant — each with their own colors, fonts, and component styles.

**Answer**:

```
┌────────────── Multi-Theme Architecture ────────────┐
│                                                    │
│  Tenant "Acme"          Tenant "TechCo"            │
│  ┌──────────────┐       ┌──────────────┐           │
│  │ Primary: blue│       │ Primary: teal│           │
│  │ Font: Inter  │       │ Font: Poppins│           │
│  │ Radius: 8px  │       │ Radius: 16px │           │
│  └──────────────┘       └──────────────┘           │
│         │                      │                   │
│         ▼                      ▼                   │
│  CSS Variables applied at root level               │
│  ┌─────────────────────────────────────────────┐   │
│  │ :root {                                     │   │
│  │   --primary: [tenant-specific];             │   │
│  │   --font-sans: [tenant-specific];           │   │
│  │   --radius: [tenant-specific];              │   │
│  │ }                                           │   │
│  └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

```tsx
// lib/themes.ts
export interface ThemeConfig {
  name: string;
  colors: {
    primary: string;         // HSL values: "243 75% 59%"
    primaryForeground: string;
    secondary: string;
    secondaryForeground: string;
    accent: string;
    accentForeground: string;
    background: string;
    foreground: string;
    card: string;
    cardForeground: string;
    border: string;
    ring: string;
    muted: string;
    mutedForeground: string;
  };
  darkColors: {
    primary: string;
    primaryForeground: string;
    background: string;
    foreground: string;
    card: string;
    cardForeground: string;
    border: string;
    ring: string;
    muted: string;
    mutedForeground: string;
  };
  fonts: {
    sans: string;
    heading?: string;
  };
  radius: string;
  borderWidth: string;
}

export const themes: Record<string, ThemeConfig> = {
  default: {
    name: 'Default',
    colors: {
      primary: '243 75% 59%',
      primaryForeground: '0 0% 98%',
      secondary: '240 4.8% 95.9%',
      secondaryForeground: '240 5.9% 10%',
      accent: '240 4.8% 95.9%',
      accentForeground: '240 5.9% 10%',
      background: '0 0% 100%',
      foreground: '240 10% 3.9%',
      card: '0 0% 100%',
      cardForeground: '240 10% 3.9%',
      border: '240 5.9% 90%',
      ring: '243 75% 59%',
      muted: '240 4.8% 95.9%',
      mutedForeground: '240 3.8% 46.1%',
    },
    darkColors: {
      primary: '243 75% 65%',
      primaryForeground: '0 0% 9%',
      background: '240 10% 3.9%',
      foreground: '0 0% 98%',
      card: '240 10% 3.9%',
      cardForeground: '0 0% 98%',
      border: '240 3.7% 15.9%',
      ring: '243 75% 65%',
      muted: '240 3.7% 15.9%',
      mutedForeground: '240 5% 64.9%',
    },
    fonts: { sans: 'Inter' },
    radius: '0.5rem',
    borderWidth: '1px',
  },
  ocean: {
    name: 'Ocean',
    colors: {
      primary: '199 89% 48%',
      primaryForeground: '0 0% 100%',
      secondary: '190 30% 94%',
      secondaryForeground: '199 70% 20%',
      accent: '190 30% 94%',
      accentForeground: '199 70% 20%',
      background: '200 20% 98%',
      foreground: '200 50% 10%',
      card: '0 0% 100%',
      cardForeground: '200 50% 10%',
      border: '200 15% 88%',
      ring: '199 89% 48%',
      muted: '200 15% 94%',
      mutedForeground: '200 10% 45%',
    },
    darkColors: {
      primary: '199 89% 55%',
      primaryForeground: '0 0% 9%',
      background: '200 50% 5%',
      foreground: '0 0% 95%',
      card: '200 40% 8%',
      cardForeground: '0 0% 95%',
      border: '200 20% 18%',
      ring: '199 89% 55%',
      muted: '200 20% 15%',
      mutedForeground: '200 10% 60%',
    },
    fonts: { sans: 'Poppins', heading: 'Playfair Display' },
    radius: '1rem',
    borderWidth: '1px',
  },
};
```

```tsx
// app/layout.tsx — Apply tenant theme
import { cookies, headers } from 'next/headers';
import { themes, type ThemeConfig } from '@/lib/themes';

async function getTenantTheme(): Promise<ThemeConfig> {
  const headerStore = await headers();
  const host = headerStore.get('host') ?? '';

  // Lookup tenant by subdomain
  const subdomain = host.split('.')[0];
  const tenant = await prisma?.tenant.findUnique({
    where: { subdomain },
    select: { themeId: true },
  });

  return themes[tenant?.themeId ?? 'default'] ?? themes.default;
}

function generateThemeCSS(theme: ThemeConfig): string {
  const lightVars = Object.entries(theme.colors)
    .map(([key, value]) => `--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}: ${value};`)
    .join('\n    ');

  const darkVars = Object.entries(theme.darkColors)
    .map(([key, value]) => `--${key.replace(/([A-Z])/g, '-$1').toLowerCase()}: ${value};`)
    .join('\n    ');

  return `
    :root {
      ${lightVars}
      --radius: ${theme.radius};
      --border-width: ${theme.borderWidth};
    }
    .dark {
      ${darkVars}
    }
  `;
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const theme = await getTenantTheme();

  return (
    <html lang="en">
      <head>
        <style dangerouslySetInnerHTML={{ __html: generateThemeCSS(theme) }} />
      </head>
      <body className="bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
```

**All shadcn/ui components automatically adapt** because they use the CSS variables (`hsl(var(--primary))`, etc.). No component changes needed when switching themes.

---

## Q12. (Intermediate) How do you optimize CSS delivery and reduce unused styles in a production Next.js build?

**Scenario**: Your Next.js app has grown large and the CSS bundle includes unused styles, impacting Core Web Vitals (LCP, CLS). How do you optimize?

**Answer**:

```
┌────────────── CSS Optimization Pipeline ────────────┐
│                                                     │
│  Source CSS (500KB+)                                │
│       │                                             │
│       ▼                                             │
│  ┌──────────────┐                                   │
│  │ Tree Shaking │ ← Tailwind purge / PurgeCSS       │
│  │ (unused)     │                                   │
│  └──────┬───────┘                                   │
│         │ (~50KB)                                   │
│         ▼                                           │
│  ┌──────────────┐                                   │
│  │ Minification │ ← Lightning CSS / cssnano         │
│  └──────┬───────┘                                   │
│         │ (~35KB)                                   │
│         ▼                                           │
│  ┌──────────────┐                                   │
│  │ Compression  │ ← gzip / brotli                   │
│  └──────┬───────┘                                   │
│         │ (~8KB)                                    │
│         ▼                                           │
│  Delivered to browser                               │
└─────────────────────────────────────────────────────┘
```

**Tailwind CSS already handles tree-shaking** — it only includes classes used in your source files:

```tsx
// next.config.ts — Enable Lightning CSS (Tailwind v4 uses it by default)
const nextConfig = {
  experimental: {
    optimizeCss: true, // Uses Lightning CSS for minification
  },
};

export default nextConfig;
```

**Analyze your CSS bundle**:

```bash
# Install bundle analyzer
npm install -D @next/bundle-analyzer

# next.config.ts
import withBundleAnalyzer from '@next/bundle-analyzer';

const config = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
})({
  // ... your config
});

# Run analysis
ANALYZE=true npm run build
```

**Critical CSS and code splitting** — Next.js automatically:

```
┌─────────────────────────────────────────┐
│  Next.js CSS Optimization (automatic)   │
│                                         │
│  1. Per-page CSS splitting              │
│     /dashboard → dashboard.css          │
│     /settings → settings.css            │
│                                         │
│  2. CSS Modules scoping                 │
│     Each .module.css → unique classes    │
│                                         │
│  3. Automatic minification              │
│     Production builds are minified      │
│                                         │
│  4. Deduplication                       │
│     Shared styles extracted to commons  │
└─────────────────────────────────────────┘
```

**Reducing Tailwind CSS bundle size**:

```tsx
// tailwind.config.ts — Strict content paths
export default {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    // Don't include test files, stories, etc.
    // './node_modules/...' only if needed for component libraries
  ],
};
```

**Lazy-loading heavy CSS components**:

```tsx
// app/dashboard/page.tsx
import dynamic from 'next/dynamic';

// Chart component with its own CSS — only loaded when visible
const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <div className="h-64 animate-pulse rounded-lg bg-gray-100" />,
  ssr: false, // Client-only if CSS-in-JS dependent
});

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <HeavyChart />
    </div>
  );
}
```

**Font subsetting** (major CSS performance win):

```tsx
// Only load Latin characters (not all Unicode ranges)
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'], // Don't include 'latin-ext', 'cyrillic', etc. unless needed
  display: 'swap',
  preload: true,
});
```

**Key optimization metrics to track**:

| Metric | Target | Tool |
|--------|--------|------|
| Total CSS size (gzip) | < 20KB | Build output |
| Unused CSS | < 5% | Chrome DevTools Coverage |
| First Contentful Paint | < 1.8s | Lighthouse |
| Cumulative Layout Shift | < 0.1 | Lighthouse |
| Largest Contentful Paint | < 2.5s | Lighthouse |

---

## Q13. (Advanced) How do you implement a zero-runtime CSS-in-JS solution (Vanilla Extract) with Next.js App Router?

**Scenario**: Your team wants type-safe, component-scoped styles with the DX of CSS-in-JS but zero runtime cost. Implement Vanilla Extract with the App Router.

**Answer**:

**Vanilla Extract** compiles CSS-in-TypeScript to static CSS at build time — giving you the API of CSS-in-JS with the performance of CSS Modules.

```
┌───────── Vanilla Extract Flow ─────────────┐
│                                            │
│  TypeScript (styles.css.ts)                │
│  export const button = style({             │
│    background: 'blue',                     │
│    ':hover': { background: 'darkblue' }    │
│  });                                       │
│       │                                    │
│       ▼ (build-time compilation)           │
│                                            │
│  CSS Output:                               │
│  .styles_button__1a2b3c {                  │
│    background: blue;                       │
│  }                                         │
│  .styles_button__1a2b3c:hover {            │
│    background: darkblue;                   │
│  }                                         │
│                                            │
│  JavaScript Output:                        │
│  export const button = 'styles_button__1a2b3c'; │
│                                            │
│  ✅ Zero runtime. Type-safe. Server-safe.  │
└────────────────────────────────────────────┘
```

**Setup**:

```bash
npm install @vanilla-extract/css @vanilla-extract/next-plugin @vanilla-extract/recipes @vanilla-extract/sprinkles
```

```tsx
// next.config.ts
import { createVanillaExtractPlugin } from '@vanilla-extract/next-plugin';

const withVanillaExtract = createVanillaExtractPlugin();

const nextConfig = {};

export default withVanillaExtract(nextConfig);
```

**Theme definition**:

```tsx
// styles/theme.css.ts
import { createTheme, createThemeContract } from '@vanilla-extract/css';

export const vars = createThemeContract({
  color: {
    primary: '',
    primaryHover: '',
    secondary: '',
    background: '',
    surface: '',
    text: { primary: '', secondary: '', inverse: '' },
    border: '',
  },
  space: { xs: '', sm: '', md: '', lg: '', xl: '', '2xl': '' },
  radius: { sm: '', md: '', lg: '', full: '' },
  font: { body: '', heading: '', mono: '' },
  fontSize: { xs: '', sm: '', base: '', lg: '', xl: '', '2xl': '', '3xl': '' },
  shadow: { sm: '', md: '', lg: '' },
});

export const lightTheme = createTheme(vars, {
  color: {
    primary: '#4f46e5',
    primaryHover: '#4338ca',
    secondary: '#10b981',
    background: '#ffffff',
    surface: '#f9fafb',
    text: { primary: '#111827', secondary: '#6b7280', inverse: '#ffffff' },
    border: '#e5e7eb',
  },
  space: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', '2xl': '48px' },
  radius: { sm: '4px', md: '8px', lg: '12px', full: '9999px' },
  font: {
    body: "'Inter', system-ui, sans-serif",
    heading: "'Inter', system-ui, sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  fontSize: {
    xs: '0.75rem', sm: '0.875rem', base: '1rem', lg: '1.125rem',
    xl: '1.25rem', '2xl': '1.5rem', '3xl': '1.875rem',
  },
  shadow: {
    sm: '0 1px 2px rgba(0,0,0,0.05)',
    md: '0 4px 6px -1px rgba(0,0,0,0.1)',
    lg: '0 10px 15px -3px rgba(0,0,0,0.1)',
  },
});

export const darkTheme = createTheme(vars, {
  color: {
    primary: '#818cf8',
    primaryHover: '#6366f1',
    secondary: '#34d399',
    background: '#0f172a',
    surface: '#1e293b',
    text: { primary: '#f1f5f9', secondary: '#94a3b8', inverse: '#0f172a' },
    border: '#334155',
  },
  space: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px', '2xl': '48px' },
  radius: { sm: '4px', md: '8px', lg: '12px', full: '9999px' },
  font: {
    body: "'Inter', system-ui, sans-serif",
    heading: "'Inter', system-ui, sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  fontSize: {
    xs: '0.75rem', sm: '0.875rem', base: '1rem', lg: '1.125rem',
    xl: '1.25rem', '2xl': '1.5rem', '3xl': '1.875rem',
  },
  shadow: {
    sm: '0 1px 2px rgba(0,0,0,0.2)',
    md: '0 4px 6px -1px rgba(0,0,0,0.3)',
    lg: '0 10px 15px -3px rgba(0,0,0,0.4)',
  },
});
```

**Component styles with recipes (variants)**:

```tsx
// components/Button/Button.css.ts
import { recipe, type RecipeVariants } from '@vanilla-extract/recipes';
import { vars } from '@/styles/theme.css';

export const button = recipe({
  base: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: vars.font.body,
    fontWeight: 500,
    borderRadius: vars.radius.md,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 150ms ease',
    ':disabled': { opacity: 0.5, cursor: 'not-allowed' },
    ':focus-visible': {
      outline: `2px solid ${vars.color.primary}`,
      outlineOffset: '2px',
    },
  },
  variants: {
    variant: {
      primary: {
        backgroundColor: vars.color.primary,
        color: vars.color.text.inverse,
        ':hover': { backgroundColor: vars.color.primaryHover },
      },
      secondary: {
        backgroundColor: 'transparent',
        color: vars.color.primary,
        border: `1px solid ${vars.color.border}`,
        ':hover': { backgroundColor: vars.color.surface },
      },
      ghost: {
        backgroundColor: 'transparent',
        color: vars.color.text.primary,
        ':hover': { backgroundColor: vars.color.surface },
      },
    },
    size: {
      sm: { height: '36px', padding: `0 ${vars.space.md}`, fontSize: vars.fontSize.sm },
      md: { height: '40px', padding: `0 ${vars.space.lg}`, fontSize: vars.fontSize.base },
      lg: { height: '48px', padding: `0 ${vars.space.xl}`, fontSize: vars.fontSize.lg },
    },
    fullWidth: {
      true: { width: '100%' },
    },
  },
  defaultVariants: { variant: 'primary', size: 'md' },
});

export type ButtonVariants = RecipeVariants<typeof button>;
```

```tsx
// components/Button/Button.tsx — Server Component compatible!
import { button, type ButtonVariants } from './Button.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, NonNullable<ButtonVariants> {
  children: React.ReactNode;
}

export function Button({ variant, size, fullWidth, children, className, ...props }: ButtonProps) {
  return (
    <button className={button({ variant, size, fullWidth })} {...props}>
      {children}
    </button>
  );
}
```

**Sprinkles (Tailwind-like utility props)**:

```tsx
// styles/sprinkles.css.ts
import { defineProperties, createSprinkles } from '@vanilla-extract/sprinkles';
import { vars } from './theme.css';

const responsiveProperties = defineProperties({
  conditions: {
    mobile: {},
    tablet: { '@media': 'screen and (min-width: 768px)' },
    desktop: { '@media': 'screen and (min-width: 1024px)' },
  },
  defaultCondition: 'mobile',
  properties: {
    display: ['none', 'flex', 'block', 'grid', 'inline-flex'],
    flexDirection: ['row', 'column'],
    justifyContent: ['stretch', 'center', 'flex-start', 'flex-end', 'space-between'],
    alignItems: ['stretch', 'center', 'flex-start', 'flex-end'],
    gap: vars.space,
    padding: vars.space,
    paddingTop: vars.space,
    paddingBottom: vars.space,
    paddingLeft: vars.space,
    paddingRight: vars.space,
    fontSize: vars.fontSize,
  },
});

const colorProperties = defineProperties({
  properties: {
    color: vars.color.text,
    backgroundColor: {
      primary: vars.color.primary,
      surface: vars.color.surface,
      background: vars.color.background,
    },
  },
});

export const sprinkles = createSprinkles(responsiveProperties, colorProperties);
export type Sprinkles = Parameters<typeof sprinkles>[0];
```

**Advantages of Vanilla Extract**:
1. **Zero runtime** — all CSS computed at build time
2. **Type-safe** — full TypeScript for your styles
3. **Server Component compatible** — no client JS needed
4. **Theming** — `createTheme` for type-safe theme variants
5. **Co-location** — styles live next to components in `.css.ts` files

---

## Q14. (Advanced) How do you build an accessible, animated component library with Tailwind CSS and Framer Motion in Next.js?

**Scenario**: Build a production animation system that respects user preferences (reduced motion), works with Server Components, and provides consistent micro-interactions.

**Answer**:

```tsx
// lib/motion.ts — Animation presets
export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] },
  },
  slideDown: {
    initial: { opacity: 0, y: -10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
    transition: { duration: 0.2 },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
    transition: { duration: 0.2 },
  },
  stagger: {
    container: {
      animate: { transition: { staggerChildren: 0.05 } },
    },
    item: {
      initial: { opacity: 0, y: 10 },
      animate: { opacity: 1, y: 0 },
    },
  },
} as const;
```

```tsx
// components/motion/AnimatedList.tsx
'use client';

import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { animations } from '@/lib/motion';

interface AnimatedListProps<T> {
  items: T[];
  keyExtractor: (item: T) => string;
  renderItem: (item: T, index: number) => React.ReactNode;
  className?: string;
}

export function AnimatedList<T>({
  items,
  keyExtractor,
  renderItem,
  className,
}: AnimatedListProps<T>) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return (
      <div className={className}>
        {items.map((item, i) => (
          <div key={keyExtractor(item)}>{renderItem(item, i)}</div>
        ))}
      </div>
    );
  }

  return (
    <motion.div
      className={className}
      variants={animations.stagger.container}
      initial="initial"
      animate="animate"
    >
      <AnimatePresence mode="popLayout">
        {items.map((item, i) => (
          <motion.div
            key={keyExtractor(item)}
            variants={animations.stagger.item}
            exit={{ opacity: 0, x: -20 }}
            layout
            transition={{ duration: 0.2 }}
          >
            {renderItem(item, i)}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}
```

```tsx
// components/motion/AnimatedPage.tsx
'use client';

import { motion, useReducedMotion } from 'framer-motion';

interface AnimatedPageProps {
  children: React.ReactNode;
  className?: string;
}

export function AnimatedPage({ children, className }: AnimatedPageProps) {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
}
```

```tsx
// components/motion/AnimatedDialog.tsx
'use client';

import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { useEffect, useRef } from 'react';

interface AnimatedDialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title: string;
}

export function AnimatedDialog({ open, onClose, children, title }: AnimatedDialogProps) {
  const shouldReduceMotion = useReducedMotion();
  const dialogRef = useRef<HTMLDivElement>(null);

  // Trap focus and handle Escape
  useEffect(() => {
    if (!open) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleEscape);
    document.body.style.overflow = 'hidden';

    // Focus first focusable element
    const focusable = dialogRef.current?.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusable?.focus();

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  const motionProps = shouldReduceMotion
    ? {}
    : {
        initial: { opacity: 0, scale: 0.95, y: 10 },
        animate: { opacity: 1, scale: 1, y: 0 },
        exit: { opacity: 0, scale: 0.95, y: 10 },
        transition: { type: 'spring', damping: 25, stiffness: 300 },
      };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Dialog */}
          <motion.div
            ref={dialogRef}
            className="relative z-10 w-full max-w-lg rounded-xl bg-white p-6 shadow-xl dark:bg-gray-900"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dialog-title"
            {...motionProps}
          >
            <h2 id="dialog-title" className="text-lg font-semibold">
              {title}
            </h2>
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
```

**CSS-only animations for Server Components** (no Framer Motion needed):

```css
/* app/globals.css — CSS-only animation utilities */
@layer utilities {
  .animate-in {
    animation: animateIn 0.3s ease-out;
  }

  .animate-slide-up {
    animation: slideUp 0.3s ease-out;
  }

  @keyframes animateIn {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* Respect reduced motion */
  @media (prefers-reduced-motion: reduce) {
    .animate-in,
    .animate-slide-up {
      animation: none;
    }
  }
}
```

**Key animation principles for production**:
1. **Always respect `prefers-reduced-motion`** — use `useReducedMotion()` hook
2. **Keep animations short** — 150-300ms for micro-interactions
3. **Use CSS animations for simple cases** — no JS needed, Server Component compatible
4. **Use Framer Motion for complex cases** — layout animations, gestures, exit animations
5. **`AnimatePresence`** is required for exit animations

---

## Q15. (Advanced) How do you architect a scalable styling system for a large Next.js monorepo with shared components?

**Scenario**: Your company has a monorepo with multiple Next.js apps (marketing site, dashboard, admin panel) sharing a common component library. How do you structure styles for consistency and reusability?

**Answer**:

```
┌────────────── Monorepo Structure ──────────────────┐
│                                                    │
│  monorepo/                                         │
│  ├── apps/                                         │
│  │   ├── marketing/     (Next.js — Tailwind)       │
│  │   ├── dashboard/     (Next.js — Tailwind)       │
│  │   └── admin/         (Next.js — Tailwind)       │
│  ├── packages/                                     │
│  │   ├── ui/            (Shared component library) │
│  │   │   ├── src/                                  │
│  │   │   │   ├── Button/                           │
│  │   │   │   ├── Card/                             │
│  │   │   │   └── index.ts                          │
│  │   │   ├── tailwind.config.ts (shared preset)    │
│  │   │   └── package.json                          │
│  │   ├── tokens/        (Design tokens)            │
│  │   │   ├── colors.ts                             │
│  │   │   ├── typography.ts                         │
│  │   │   └── index.ts                              │
│  │   └── tailwind-config/ (Shared Tailwind preset) │
│  │       └── index.ts                              │
│  ├── turbo.json                                    │
│  └── package.json                                  │
└────────────────────────────────────────────────────┘
```

**Shared Tailwind preset** (packages/tailwind-config):

```tsx
// packages/tailwind-config/index.ts
import type { Config } from 'tailwindcss';

export const sharedConfig: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: 'var(--brand-50)',
          100: 'var(--brand-100)',
          500: 'var(--brand-500)',
          600: 'var(--brand-600)',
          700: 'var(--brand-700)',
        },
        surface: {
          DEFAULT: 'var(--surface)',
          elevated: 'var(--surface-elevated)',
          overlay: 'var(--surface-overlay)',
        },
        content: {
          DEFAULT: 'var(--content)',
          secondary: 'var(--content-secondary)',
          tertiary: 'var(--content-tertiary)',
        },
        border: {
          DEFAULT: 'var(--border)',
          strong: 'var(--border-strong)',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
        sm: 'calc(var(--radius) - 2px)',
        md: 'var(--radius)',
        lg: 'calc(var(--radius) + 4px)',
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        dialog: 'var(--shadow-dialog)',
      },
    },
  },
};
```

**Shared UI library** (packages/ui):

```tsx
// packages/ui/src/Button/Button.tsx
import { cn } from '../utils';
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary: 'bg-brand-600 text-white hover:bg-brand-700 shadow-sm',
        secondary: 'bg-surface-elevated border border-border text-content hover:bg-surface',
        ghost: 'text-content hover:bg-surface',
        danger: 'bg-red-600 text-white hover:bg-red-700',
      },
      size: {
        sm: 'h-8 px-3 text-sm gap-1.5',
        md: 'h-10 px-4 text-sm gap-2',
        lg: 'h-12 px-6 text-base gap-2',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export function Button({ variant, size, loading, children, className, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
```

**App-specific Tailwind config**:

```tsx
// apps/dashboard/tailwind.config.ts
import type { Config } from 'tailwindcss';
import { sharedConfig } from '@acme/tailwind-config';

const config: Config = {
  presets: [sharedConfig as Config],
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    '../../packages/ui/src/**/*.{ts,tsx}', // Include shared UI library
  ],
};

export default config;
```

**App-specific theme tokens**:

```css
/* apps/dashboard/app/globals.css */
@import "tailwindcss";

:root {
  --brand-50: #eef2ff;
  --brand-100: #e0e7ff;
  --brand-500: #6366f1;
  --brand-600: #4f46e5;
  --brand-700: #4338ca;

  --surface: #ffffff;
  --surface-elevated: #ffffff;
  --surface-overlay: rgba(0, 0, 0, 0.5);

  --content: #111827;
  --content-secondary: #6b7280;
  --content-tertiary: #9ca3af;

  --border: #e5e7eb;
  --border-strong: #d1d5db;

  --radius: 0.5rem;

  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-dialog: 0 20px 25px rgba(0, 0, 0, 0.15);
}

.dark {
  --surface: #0f172a;
  --surface-elevated: #1e293b;
  --content: #f1f5f9;
  --content-secondary: #94a3b8;
  --border: #334155;
}
```

```css
/* apps/marketing/app/globals.css — Different brand */
@import "tailwindcss";

:root {
  --brand-50: #ecfdf5;
  --brand-100: #d1fae5;
  --brand-500: #10b981;
  --brand-600: #059669;
  --brand-700: #047857;

  /* Same structure, different values */
  --surface: #fafafa;
  --radius: 1rem; /* Marketing site: rounder corners */
}
```

**Key monorepo styling principles**:
1. **Shared preset** — common Tailwind config as a package
2. **CSS variable tokens** — each app defines its own values
3. **Content paths** — include `../../packages/ui/src/` in each app's config
4. **Same components, different themes** — the `@acme/ui` Button looks different in each app because CSS variables change
5. **Build-time composition** — no runtime overhead, each app gets optimized CSS

---

## Q16. (Advanced) How do you implement advanced Tailwind CSS patterns: plugins, arbitrary values, group/peer selectors, and dynamic class generation?

**Scenario**: Your UI requires complex interactive patterns — hover cards that affect siblings, form validation styling, stepped progress indicators, and custom scrollbar styles.

**Answer**:

**Group and peer selectors** for interactive patterns:

```tsx
// components/HoverCard.tsx — Parent hover affects children
export function HoverCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="group relative cursor-pointer rounded-xl border border-gray-200 p-6 transition-all hover:border-brand-300 hover:shadow-lg dark:border-gray-800">
      {/* Icon scales up on parent hover */}
      <div className="mb-4 inline-flex rounded-lg bg-brand-50 p-3 text-brand-600 transition-transform group-hover:scale-110 dark:bg-brand-950">
        {icon}
      </div>

      <h3 className="font-semibold text-gray-900 group-hover:text-brand-600 dark:text-white dark:group-hover:text-brand-400">
        {title}
      </h3>

      <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
        {description}
      </p>

      {/* Arrow appears on hover */}
      <div className="mt-4 flex items-center text-sm font-medium text-brand-600 opacity-0 transition-opacity group-hover:opacity-100">
        Learn more →
      </div>
    </div>
  );
}
```

**Peer selectors for form validation**:

```tsx
// components/FormField.tsx
'use client';

export function FormField({
  label,
  name,
  type = 'text',
  required,
  pattern,
  errorMessage,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  pattern?: string;
  errorMessage?: string;
}) {
  return (
    <div className="space-y-1">
      <label htmlFor={name} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>

      <input
        id={name}
        name={name}
        type={type}
        required={required}
        pattern={pattern}
        className={[
          'peer w-full rounded-lg border px-3 py-2 text-sm transition-colors',
          'border-gray-300 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20',
          'placeholder:text-gray-400',
          // Invalid state (peer-invalid only shows after interaction)
          'peer-invalid:border-red-500 peer-invalid:focus:border-red-500 peer-invalid:focus:ring-red-500/20',
          'dark:border-gray-700 dark:bg-gray-900',
        ].join(' ')}
        placeholder={`Enter ${label.toLowerCase()}`}
      />

      {/* Error message — hidden until input is invalid */}
      {errorMessage && (
        <p className="hidden text-sm text-red-500 peer-invalid:block">
          {errorMessage}
        </p>
      )}

      {/* Valid indicator */}
      <p className="hidden text-sm text-green-600 peer-valid:peer-not-placeholder-shown:block">
        ✓ Looks good!
      </p>
    </div>
  );
}
```

**Custom Tailwind plugin for scrollbar styles**:

```tsx
// tailwind-plugins/scrollbar.ts
import plugin from 'tailwindcss/plugin';

export const scrollbarPlugin = plugin(function ({ addUtilities }) {
  addUtilities({
    '.scrollbar-thin': {
      'scrollbar-width': 'thin',
      '&::-webkit-scrollbar': { width: '6px', height: '6px' },
      '&::-webkit-scrollbar-track': { background: 'transparent' },
      '&::-webkit-scrollbar-thumb': {
        background: '#d1d5db',
        'border-radius': '9999px',
      },
      '&::-webkit-scrollbar-thumb:hover': { background: '#9ca3af' },
    },
    '.scrollbar-none': {
      'scrollbar-width': 'none',
      '&::-webkit-scrollbar': { display: 'none' },
    },
  });
});
```

**Complex stepped progress with arbitrary values**:

```tsx
// components/StepProgress.tsx
import { cn } from '@/lib/utils';

interface StepProgressProps {
  steps: { label: string; status: 'complete' | 'current' | 'upcoming' }[];
}

export function StepProgress({ steps }: StepProgressProps) {
  return (
    <nav aria-label="Progress" className="w-full">
      <ol className="flex items-center">
        {steps.map((step, index) => (
          <li
            key={step.label}
            className={cn(
              'relative flex items-center',
              index < steps.length - 1 && 'flex-1'
            )}
          >
            {/* Step circle */}
            <div
              className={cn(
                'relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold transition-all',
                step.status === 'complete' && 'border-brand-600 bg-brand-600 text-white',
                step.status === 'current' && 'border-brand-600 bg-white text-brand-600 ring-4 ring-brand-100',
                step.status === 'upcoming' && 'border-gray-300 bg-white text-gray-500'
              )}
            >
              {step.status === 'complete' ? (
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              ) : (
                index + 1
              )}
            </div>

            {/* Step label */}
            <span
              className={cn(
                'absolute top-12 whitespace-nowrap text-xs font-medium',
                'left-1/2 -translate-x-1/2',
                step.status === 'complete' && 'text-brand-600',
                step.status === 'current' && 'text-brand-600',
                step.status === 'upcoming' && 'text-gray-500'
              )}
            >
              {step.label}
            </span>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div className="flex-1 mx-2">
                <div
                  className={cn(
                    'h-0.5 w-full transition-colors',
                    step.status === 'complete' ? 'bg-brand-600' : 'bg-gray-200'
                  )}
                />
              </div>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
```

**Arbitrary values and CSS functions in Tailwind**:

```tsx
// components/GradientCard.tsx
export function GradientCard({
  gradientFrom,
  gradientTo,
  children,
}: {
  gradientFrom: string;
  gradientTo: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-xl p-[1px]"
      style={{
        background: `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})`,
      }}
    >
      <div className="rounded-[calc(0.75rem-1px)] bg-white p-6 dark:bg-gray-950">
        {children}
      </div>
    </div>
  );
}
```

These patterns demonstrate that Tailwind CSS can handle complex interactive UI without any runtime CSS-in-JS, keeping everything compatible with Server Components.

---

## Q17. (Advanced) How do you handle CSS architecture for micro-frontends or Module Federation in a Next.js environment?

**Scenario**: Multiple teams develop features independently and their CSS must not conflict. How do you isolate styles across independently deployed modules?

**Answer**:

```
┌──────────── Micro-Frontend CSS Isolation ───────────┐
│                                                     │
│  Host App (Next.js)                                 │
│  ┌─────────────────────────────────────────────┐    │
│  │  Global styles (layout, reset, theme vars)  │    │
│  │                                              │    │
│  │  ┌──────────────┐  ┌──────────────────────┐ │    │
│  │  │ Team A Module│  │ Team B Module        │ │    │
│  │  │ CSS: .team-a_│  │ CSS: .team-b_        │ │    │
│  │  │ [scoped]     │  │ [scoped]             │ │    │
│  │  └──────────────┘  └──────────────────────┘ │    │
│  │                                              │    │
│  │  No CSS conflicts between modules!          │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Strategies:                                        │
│  1. CSS Modules (automatic scoping)                 │
│  2. Tailwind with per-module prefix                 │
│  3. Shadow DOM (Web Components)                     │
│  4. CSS Layers (@layer)                             │
└─────────────────────────────────────────────────────┘
```

**Strategy 1: Tailwind with module prefixes**:

```tsx
// packages/team-a-checkout/tailwind.config.ts
export default {
  prefix: 'ta-', // All classes: ta-flex, ta-bg-blue-500, etc.
  content: ['./src/**/*.{ts,tsx}'],
  corePlugins: {
    preflight: false, // Don't reset globals — host handles this
  },
};
```

```tsx
// packages/team-a-checkout/src/CheckoutForm.tsx
export function CheckoutForm() {
  return (
    <form className="ta-space-y-4 ta-rounded-lg ta-border ta-p-6">
      <input className="ta-w-full ta-rounded ta-border ta-px-3 ta-py-2" />
      <button className="ta-w-full ta-rounded ta-bg-blue-600 ta-py-2 ta-text-white">
        Pay Now
      </button>
    </form>
  );
}
```

**Strategy 2: CSS Layers for precedence control**:

```css
/* Host app: globals.css */
@layer reset, tokens, base, components, team-a, team-b, overrides;

/* Reset layer (lowest priority) */
@layer reset {
  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
  }
}

/* Token layer */
@layer tokens {
  :root {
    --color-primary: #4f46e5;
    --radius: 0.5rem;
    --font-sans: "Inter", sans-serif;
  }
}

/* Base layer */
@layer base {
  body {
    font-family: var(--font-sans);
    color: #111827;
  }
}
```

```css
/* Team A: checkout.css */
@layer team-a {
  .checkout-form {
    padding: 1.5rem;
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
  }

  .checkout-form__input {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: var(--radius);
  }
}
```

**Strategy 3: CSS Modules with namespace convention**:

```tsx
// packages/team-b-dashboard/src/Widget.tsx
import styles from './Widget.module.css';

export function Widget({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className={styles.widget}>
      <h3 className={styles.title}>{title}</h3>
      <div className={styles.content}>{children}</div>
    </div>
  );
}
```

```css
/* Widget.module.css — auto-scoped: .Widget_widget__x7ks2 */
.widget {
  background: var(--surface-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}
```

**Strategy 4: Dynamic CSS import with Module Federation**:

```tsx
// Host app: loading remote module with CSS isolation
import dynamic from 'next/dynamic';

const RemoteCheckout = dynamic(
  () => import('team_a_checkout/CheckoutForm'),
  {
    loading: () => <div className="h-64 animate-pulse rounded-lg bg-gray-100" />,
    ssr: false,
  }
);

export default function CheckoutPage() {
  return (
    <div className="mx-auto max-w-xl p-6">
      {/* Remote module's CSS is isolated via CSS Modules or prefix */}
      <RemoteCheckout />
    </div>
  );
}
```

**Key principles for micro-frontend CSS**:
1. **Never use global selectors** (`h1 { ... }`) in module CSS
2. **Use CSS custom properties for shared tokens** — modules read from host
3. **CSS Modules is the safest default** — automatic scoping
4. **Tailwind prefix** when multiple teams use Tailwind independently
5. **CSS Layers** for explicit precedence control
6. **No `!important`** — use layers instead

---

## Q18. (Advanced) How do you implement performant CSS animations and transitions that work with React Server Components and the View Transitions API?

**Scenario**: Next.js 15/16 supports the View Transitions API for smooth page-to-page transitions. Implement production-ready view transitions with fallbacks.

**Answer**:

```
┌────────── View Transitions API Flow ───────────────┐
│                                                    │
│  Page A (current)      Transition        Page B     │
│  ┌────────────┐    ┌──────────────┐  ┌──────────┐ │
│  │  Content A  │───▶│ Cross-fade   │──▶│Content B │ │
│  │  (snapshot) │    │ or morph     │  │(new page)│ │
│  └────────────┘    └──────────────┘  └──────────┘ │
│                                                    │
│  Browser takes snapshot of old page,               │
│  renders new page underneath, then                 │
│  animates from snapshot to new page.               │
│                                                    │
│  Next.js 15: experimental support                  │
│  Next.js 16: stable support expected               │
└────────────────────────────────────────────────────┘
```

**Enable View Transitions in Next.js**:

```tsx
// next.config.ts
const nextConfig = {
  experimental: {
    viewTransition: true, // Next.js 15+
  },
};

export default nextConfig;
```

**Basic view transition with `unstable_ViewTransition`**:

```tsx
// app/components/PageTransition.tsx
import { unstable_ViewTransition as ViewTransition } from 'react';

export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <ViewTransition>
      {children}
    </ViewTransition>
  );
}
```

```tsx
// app/layout.tsx
import { PageTransition } from './components/PageTransition';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav>{/* Navigation */}</nav>
        <PageTransition>
          <main>{children}</main>
        </PageTransition>
      </body>
    </html>
  );
}
```

**Custom view transition CSS**:

```css
/* app/globals.css */

/* Default cross-fade */
::view-transition-old(root) {
  animation: fade-out 0.2s ease-in;
}

::view-transition-new(root) {
  animation: fade-in 0.3s ease-out;
}

@keyframes fade-out {
  to { opacity: 0; }
}

@keyframes fade-in {
  from { opacity: 0; }
}

/* Named transitions for specific elements */
::view-transition-old(hero-image) {
  animation: scale-down 0.3s ease-in;
}

::view-transition-new(hero-image) {
  animation: scale-up 0.3s ease-out;
}

@keyframes scale-down {
  to { transform: scale(0.9); opacity: 0; }
}

@keyframes scale-up {
  from { transform: scale(1.1); opacity: 0; }
}

/* Slide transition for pages */
::view-transition-old(page) {
  animation: slide-out-left 0.3s ease-in;
}

::view-transition-new(page) {
  animation: slide-in-right 0.3s ease-out;
}

@keyframes slide-out-left {
  to { transform: translateX(-30px); opacity: 0; }
}

@keyframes slide-in-right {
  from { transform: translateX(30px); opacity: 0; }
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(*),
  ::view-transition-new(*) {
    animation-duration: 0.001ms !important;
  }
}
```

**Named view transitions for shared element transitions**:

```tsx
// app/blog/page.tsx — List page
import Link from 'next/link';

export default async function BlogListPage() {
  const posts = await getPosts();

  return (
    <div className="grid gap-6">
      {posts.map((post) => (
        <Link key={post.id} href={`/blog/${post.slug}`}>
          <article className="flex gap-4 rounded-lg border p-4 hover:bg-gray-50">
            <img
              src={post.image}
              alt={post.title}
              className="h-24 w-32 rounded-md object-cover"
              style={{ viewTransitionName: `post-image-${post.id}` }}
            />
            <div>
              <h2
                className="text-lg font-semibold"
                style={{ viewTransitionName: `post-title-${post.id}` }}
              >
                {post.title}
              </h2>
              <p className="text-sm text-gray-500">{post.excerpt}</p>
            </div>
          </article>
        </Link>
      ))}
    </div>
  );
}
```

```tsx
// app/blog/[slug]/page.tsx — Detail page
export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);

  return (
    <article className="max-w-3xl mx-auto">
      <img
        src={post.image}
        alt={post.title}
        className="w-full rounded-xl object-cover"
        style={{ viewTransitionName: `post-image-${post.id}` }}
      />
      <h1
        className="mt-6 text-3xl font-bold"
        style={{ viewTransitionName: `post-title-${post.id}` }}
      >
        {post.title}
      </h1>
      <div className="prose mt-4" dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  );
}
```

The browser automatically creates a smooth morph animation between elements with the same `view-transition-name` across pages.

**Fallback for browsers without View Transitions API support**:

```tsx
// app/components/SafePageTransition.tsx
'use client';

import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

function supportsViewTransitions(): boolean {
  return typeof document !== 'undefined' && 'startViewTransition' in document;
}

export function SafePageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [hasNativeSupport] = useState(supportsViewTransitions);

  // If browser supports View Transitions API, let Next.js handle it
  if (hasNativeSupport) {
    return <>{children}</>;
  }

  // Fallback: use Framer Motion
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
```

**Performance-optimized CSS transitions** (no JS needed):

```css
/* Intersection Observer-triggered animations */
.reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Staggered children */
.reveal-stagger > * {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.reveal-stagger.visible > *:nth-child(1) { transition-delay: 0ms; opacity: 1; transform: translateY(0); }
.reveal-stagger.visible > *:nth-child(2) { transition-delay: 50ms; opacity: 1; transform: translateY(0); }
.reveal-stagger.visible > *:nth-child(3) { transition-delay: 100ms; opacity: 1; transform: translateY(0); }
.reveal-stagger.visible > *:nth-child(4) { transition-delay: 150ms; opacity: 1; transform: translateY(0); }
```

**Key principles**: View Transitions API is the future of page transitions. Use it with CSS for maximum performance. Fall back to Framer Motion for browsers that don't support it. Always respect `prefers-reduced-motion`.

---

## Q19. (Advanced) How do you debug CSS issues in production Next.js apps and implement visual regression testing?

**Scenario**: A CSS bug only appears in production (not development). How do you debug it, and how do you prevent CSS regressions?

**Answer**:

```
┌────────── Common Production CSS Issues ────────────┐
│                                                    │
│  1. CSS ordering differences (dev vs prod)         │
│     Dev: styles loaded on-demand                   │
│     Prod: styles chunked and reordered             │
│                                                    │
│  2. Purged styles (Tailwind)                       │
│     Class used dynamically: not detected           │
│                                                    │
│  3. Hydration mismatch                             │
│     Server: no viewport width                      │
│     Client: window.innerWidth available            │
│                                                    │
│  4. Third-party CSS conflicts                      │
│     Global selectors from libraries                │
│                                                    │
│  5. Font loading flash (FOUT/FOIT)                 │
│     Font not loaded → layout shift                 │
└────────────────────────────────────────────────────┘
```

**Debugging CSS ordering issues**:

```tsx
// next.config.ts — Force consistent CSS ordering
const nextConfig = {
  experimental: {
    optimizeCss: true,
    // strictNextHead: true, // Catch <head> ordering issues
  },
};
```

**CSS specificity debugging utility**:

```tsx
// lib/debug-css.ts (development only)
export function debugCSS(element: HTMLElement) {
  if (process.env.NODE_ENV !== 'development') return;

  const computed = window.getComputedStyle(element);
  const applied: Record<string, string> = {};

  for (const prop of computed) {
    const value = computed.getPropertyValue(prop);
    if (value && value !== 'initial' && value !== 'normal') {
      applied[prop] = value;
    }
  }

  console.table(applied);

  // Show which CSS rules apply
  const rules = document.querySelectorAll('style, link[rel="stylesheet"]');
  console.log('Active stylesheets:', rules.length);
}
```

**Visual regression testing with Playwright**:

```tsx
// tests/visual/screenshots.spec.ts
import { test, expect } from '@playwright/test';

const pages = [
  { name: 'home', path: '/' },
  { name: 'dashboard', path: '/dashboard' },
  { name: 'settings', path: '/settings' },
  { name: 'login', path: '/login' },
];

const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
];

for (const page of pages) {
  for (const viewport of viewports) {
    test(`${page.name} - ${viewport.name}`, async ({ page: pw }) => {
      await pw.setViewportSize({ width: viewport.width, height: viewport.height });
      await pw.goto(page.path);

      // Wait for fonts and images
      await pw.waitForLoadState('networkidle');
      await pw.evaluate(() => document.fonts.ready);

      // Take screenshot
      await expect(pw).toHaveScreenshot(`${page.name}-${viewport.name}.png`, {
        fullPage: true,
        maxDiffPixelRatio: 0.01, // Allow 1% pixel difference
      });
    });
  }
}

// Component-level visual testing
test('Button variants', async ({ page }) => {
  await page.goto('/storybook/button');

  const primaryButton = page.getByRole('button', { name: 'Primary' });
  await expect(primaryButton).toHaveScreenshot('button-primary.png');

  // Test hover state
  await primaryButton.hover();
  await expect(primaryButton).toHaveScreenshot('button-primary-hover.png');

  // Test focus state
  await primaryButton.focus();
  await expect(primaryButton).toHaveScreenshot('button-primary-focus.png');
});

// Dark mode testing
test('Dashboard dark mode', async ({ page }) => {
  await page.goto('/dashboard');

  // Light mode
  await expect(page).toHaveScreenshot('dashboard-light.png');

  // Toggle to dark mode
  await page.evaluate(() => document.documentElement.classList.add('dark'));
  await expect(page).toHaveScreenshot('dashboard-dark.png');
});
```

**CI pipeline for visual regression** (`.github/workflows/visual-regression.yml`):

```yaml
name: Visual Regression
on:
  pull_request:
    paths: ['app/**', 'components/**', '*.css', 'tailwind.config.*']

jobs:
  visual-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npm start &
      - run: npx wait-on http://localhost:3000
      - run: npx playwright test tests/visual/
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: visual-regression-report
          path: test-results/
```

**Safelist for dynamically-generated Tailwind classes**:

```tsx
// tailwind.config.ts
export default {
  safelist: [
    // Ensure dynamic status colors are always included
    { pattern: /^bg-(red|green|blue|yellow)-(100|500|600)$/ },
    { pattern: /^text-(red|green|blue|yellow)-(600|700)$/ },
    // Badge variants
    'bg-green-100', 'text-green-700',
    'bg-red-100', 'text-red-700',
    'bg-yellow-100', 'text-yellow-700',
  ],
};
```

**Debugging production CSS checklist**:
1. Check build output for CSS file sizes and chunk names
2. Compare production HTML source with development
3. Use Chrome DevTools Coverage tab to find unused CSS
4. Check for CSS ordering differences between dev/prod
5. Verify Tailwind content paths include all component files
6. Test with `npm run build && npm run start` locally before deploying

---

## Q20. (Advanced) How do you implement a comprehensive design token pipeline from Figma to Next.js with automated synchronization?

**Scenario**: Your design team maintains tokens in Figma. You need an automated pipeline that converts Figma tokens to CSS variables, Tailwind config, and TypeScript types — with CI/CD integration.

**Answer**:

```
┌────────── Design Token Pipeline ───────────────────┐
│                                                    │
│  Figma (Design)                                    │
│  ├── Colors, typography, spacing, shadows          │
│  └── Figma Tokens plugin exports JSON              │
│       │                                            │
│       ▼                                            │
│  tokens.json (source of truth)                     │
│       │                                            │
│       ▼                                            │
│  Style Dictionary (transform engine)               │
│  ├── CSS Variables (app/tokens.css)                │
│  ├── Tailwind Config (tailwind.tokens.ts)          │
│  ├── TypeScript Types (types/tokens.ts)            │
│  └── JSON (for runtime access)                     │
│       │                                            │
│       ▼                                            │
│  Next.js App (consumes tokens)                     │
│  ├── globals.css imports tokens.css                │
│  ├── tailwind.config.ts imports tailwind.tokens    │
│  └── Components use type-safe token values         │
└────────────────────────────────────────────────────┘
```

**Token source file** (exported from Figma Tokens or Tokens Studio):

```json
// tokens/tokens.json
{
  "color": {
    "primitive": {
      "blue": {
        "50": { "value": "#eff6ff", "type": "color" },
        "100": { "value": "#dbeafe", "type": "color" },
        "500": { "value": "#3b82f6", "type": "color" },
        "600": { "value": "#2563eb", "type": "color" },
        "700": { "value": "#1d4ed8", "type": "color" }
      },
      "gray": {
        "50": { "value": "#f9fafb", "type": "color" },
        "100": { "value": "#f3f4f6", "type": "color" },
        "200": { "value": "#e5e7eb", "type": "color" },
        "500": { "value": "#6b7280", "type": "color" },
        "700": { "value": "#374151", "type": "color" },
        "900": { "value": "#111827", "type": "color" }
      }
    },
    "semantic": {
      "primary": { "value": "{color.primitive.blue.600}", "type": "color" },
      "primary-hover": { "value": "{color.primitive.blue.700}", "type": "color" },
      "background": { "value": "#ffffff", "type": "color" },
      "surface": { "value": "{color.primitive.gray.50}", "type": "color" },
      "text-primary": { "value": "{color.primitive.gray.900}", "type": "color" },
      "text-secondary": { "value": "{color.primitive.gray.500}", "type": "color" },
      "border": { "value": "{color.primitive.gray.200}", "type": "color" }
    },
    "semantic-dark": {
      "primary": { "value": "{color.primitive.blue.500}", "type": "color" },
      "background": { "value": "#0f172a", "type": "color" },
      "surface": { "value": "#1e293b", "type": "color" },
      "text-primary": { "value": "#f1f5f9", "type": "color" },
      "text-secondary": { "value": "#94a3b8", "type": "color" },
      "border": { "value": "#334155", "type": "color" }
    }
  },
  "spacing": {
    "xs": { "value": "4px", "type": "spacing" },
    "sm": { "value": "8px", "type": "spacing" },
    "md": { "value": "16px", "type": "spacing" },
    "lg": { "value": "24px", "type": "spacing" },
    "xl": { "value": "32px", "type": "spacing" },
    "2xl": { "value": "48px", "type": "spacing" },
    "3xl": { "value": "64px", "type": "spacing" }
  },
  "typography": {
    "heading-xl": {
      "value": {
        "fontFamily": "Inter",
        "fontSize": "36px",
        "fontWeight": "700",
        "lineHeight": "44px",
        "letterSpacing": "-0.02em"
      },
      "type": "typography"
    },
    "heading-lg": {
      "value": {
        "fontFamily": "Inter",
        "fontSize": "24px",
        "fontWeight": "600",
        "lineHeight": "32px",
        "letterSpacing": "-0.01em"
      },
      "type": "typography"
    },
    "body": {
      "value": {
        "fontFamily": "Inter",
        "fontSize": "16px",
        "fontWeight": "400",
        "lineHeight": "24px",
        "letterSpacing": "0"
      },
      "type": "typography"
    }
  },
  "radius": {
    "sm": { "value": "4px", "type": "borderRadius" },
    "md": { "value": "8px", "type": "borderRadius" },
    "lg": { "value": "12px", "type": "borderRadius" },
    "full": { "value": "9999px", "type": "borderRadius" }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px rgba(0, 0, 0, 0.05)", "type": "boxShadow" },
    "md": { "value": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)", "type": "boxShadow" },
    "lg": { "value": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)", "type": "boxShadow" }
  }
}
```

**Style Dictionary build script**:

```tsx
// scripts/build-tokens.ts
import StyleDictionary from 'style-dictionary';

const sd = new StyleDictionary({
  source: ['tokens/tokens.json'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'app/',
      files: [
        {
          destination: 'tokens.css',
          format: 'css/variables',
          options: {
            selector: ':root',
            outputReferences: true,
          },
          filter: (token) => !token.path.includes('semantic-dark'),
        },
        {
          destination: 'tokens-dark.css',
          format: 'css/variables',
          options: {
            selector: '.dark',
          },
          filter: (token) => token.path.includes('semantic-dark'),
        },
      ],
    },
    tailwind: {
      transformGroup: 'js',
      buildPath: 'tokens/',
      files: [
        {
          destination: 'tailwind.tokens.ts',
          format: 'custom/tailwind',
        },
      ],
    },
    typescript: {
      transformGroup: 'js',
      buildPath: 'tokens/',
      files: [
        {
          destination: 'types.ts',
          format: 'custom/typescript-types',
        },
      ],
    },
  },
});

// Custom Tailwind format
sd.registerFormat({
  name: 'custom/tailwind',
  format: ({ dictionary }) => {
    const colors: Record<string, any> = {};
    const spacing: Record<string, string> = {};

    dictionary.allTokens.forEach((token) => {
      if (token.type === 'color' && token.path[0] === 'color' && token.path[1] === 'semantic') {
        const name = token.path.slice(2).join('-');
        colors[name] = `var(--color-semantic-${name})`;
      }
      if (token.type === 'spacing') {
        const name = token.path[token.path.length - 1];
        spacing[name] = token.value;
      }
    });

    return `// Auto-generated from design tokens — do not edit manually
export const tokenColors = ${JSON.stringify(colors, null, 2)} as const;
export const tokenSpacing = ${JSON.stringify(spacing, null, 2)} as const;
`;
  },
});

// Custom TypeScript types format
sd.registerFormat({
  name: 'custom/typescript-types',
  format: ({ dictionary }) => {
    const colorNames = dictionary.allTokens
      .filter((t) => t.type === 'color' && t.path[1] === 'semantic')
      .map((t) => `'${t.path.slice(2).join('-')}'`);

    const spacingNames = dictionary.allTokens
      .filter((t) => t.type === 'spacing')
      .map((t) => `'${t.path[t.path.length - 1]}'`);

    return `// Auto-generated from design tokens — do not edit manually
export type ColorToken = ${colorNames.join(' | ')};
export type SpacingToken = ${spacingNames.join(' | ')};
`;
  },
});

async function build() {
  await sd.buildAllPlatforms();
  console.log('Design tokens built successfully!');
}

build();
```

**Package.json script**:

```json
{
  "scripts": {
    "tokens:build": "ts-node scripts/build-tokens.ts",
    "tokens:watch": "chokidar 'tokens/tokens.json' -c 'npm run tokens:build'",
    "prebuild": "npm run tokens:build"
  }
}
```

**CI/CD: Auto-sync from Figma** (`.github/workflows/sync-tokens.yml`):

```yaml
name: Sync Design Tokens
on:
  repository_dispatch:
    types: [figma-tokens-updated]
  schedule:
    - cron: '0 9 * * 1' # Weekly Monday 9am
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Fetch tokens from Figma
        run: |
          curl -H "X-Figma-Token: ${{ secrets.FIGMA_TOKEN }}" \
            "https://api.figma.com/v1/files/${{ secrets.FIGMA_FILE_ID }}/variables/local" \
            -o tokens/figma-raw.json

      - name: Transform tokens
        run: node scripts/transform-figma-tokens.js

      - name: Build token outputs
        run: npm run tokens:build

      - name: Run visual regression
        run: npx playwright test tests/visual/

      - name: Create PR if changed
        uses: peter-evans/create-pull-request@v6
        with:
          title: 'chore: sync design tokens from Figma'
          body: 'Automated sync of design tokens from Figma. Review visual regression screenshots.'
          branch: sync/design-tokens
          commit-message: 'chore: sync design tokens'
```

**Key token pipeline principles**:
1. **Single source of truth** — Figma or `tokens.json` is authoritative
2. **Build-time transformation** — tokens compiled to CSS vars, Tailwind config, TS types
3. **Type safety** — TypeScript types generated from tokens
4. **Automated sync** — CI/CD pipeline keeps tokens in sync
5. **Visual regression** — screenshots verify token changes don't break UI
6. **No manual editing** — generated files have "do not edit" headers
