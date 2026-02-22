# 15. Testing Next.js Applications

## Topic Introduction

Testing Next.js 15/16 applications requires understanding the unique challenges posed by the App Router architecture: **Server Components**, **Server Actions**, **Route Handlers**, **middleware**, and the interplay between server and client rendering. A comprehensive test strategy spans unit tests, integration tests, and end-to-end (E2E) tests.

```
┌────────────────────────────────────────────────────────────────┐
│                  Next.js Testing Pyramid                       │
│                                                                │
│                        ╱╲                                      │
│                       ╱  ╲        E2E Tests (Playwright)       │
│                      ╱    ╲       - Full user flows            │
│                     ╱──────╲      - Cross-browser              │
│                    ╱        ╲     - Visual regression           │
│                   ╱──────────╲                                  │
│                  ╱            ╲    Integration Tests            │
│                 ╱   Component  ╲   - Server Components         │
│                ╱    + API Tests ╲   - Server Actions            │
│               ╱──────────────────╲  - Route Handlers           │
│              ╱                    ╲                             │
│             ╱     Unit Tests       ╲  - Utility functions      │
│            ╱    (Jest + RTL)        ╲  - Custom hooks          │
│           ╱──────────────────────────╲ - Pure components       │
│                                                                │
│  Testing Tools:                                                │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │   Jest      │ │ React Testing│ │ Playwright / Cypress   │  │
│  │ + @next/... │ │ Library      │ │ (E2E)                  │  │
│  └─────────────┘ └──────────────┘ └────────────────────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │   Vitest    │ │ MSW (Mock    │ │ Testing Library        │  │
│  │ (alt)       │ │ Service      │ │ User Event             │  │
│  └─────────────┘ │ Worker)      │ └────────────────────────┘  │
│                  └──────────────┘                              │
└────────────────────────────────────────────────────────────────┘
```

**What's challenging about testing Next.js 15/16**:

| Challenge | Details |
|-----------|---------|
| Server Components | Can't use `render()` from RTL directly (async, no client JS) |
| Server Actions | `'use server'` functions need special mocking |
| `cookies()` / `headers()` | Next.js server functions need mocking |
| `fetch` caching | `next: { revalidate }` affects test behavior |
| Middleware | Runs at the edge, different runtime |
| Dynamic imports | `next/dynamic` needs special handling |
| Router mocking | `useRouter`, `useSearchParams`, `usePathname` |

```tsx
// jest.config.ts — Production Jest setup for Next.js 15
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({ dir: './' });

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
  coverageProvider: 'v8',
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
};

export default createJestConfig(config);
```

```tsx
// jest.setup.ts
import '@testing-library/jest-dom';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
  redirect: jest.fn(),
  notFound: jest.fn(),
}));
```

**Why this matters for senior developers**: Testing is the safety net that enables confident refactoring, rapid deployment, and production reliability. In the App Router era, understanding how to test async Server Components, Server Actions, and the new data-fetching patterns is critical for maintaining code quality at scale.

---

## Q1. (Beginner) How do you set up Jest and React Testing Library for a Next.js 15 project?

**Scenario**: You're setting up testing from scratch in a Next.js 15 project. Walk through the full setup.

**Answer**:

```bash
npm install -D jest @jest/types @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom ts-node
```

**Project structure**:

```
project/
├── jest.config.ts
├── jest.setup.ts
├── __tests__/
│   ├── components/
│   │   └── Button.test.tsx
│   ├── lib/
│   │   └── utils.test.ts
│   └── app/
│       └── api/
│           └── users.test.ts
├── app/
├── components/
└── lib/
```

```tsx
// jest.config.ts
import type { Config } from 'jest';
import nextJest from 'next/jest';

const createJestConfig = nextJest({
  dir: './', // Path to Next.js app (loads next.config and .env)
});

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1', // Match tsconfig paths
  },
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/e2e/',      // Playwright tests in separate folder
    '<rootDir>/.next/',
  ],
  coverageProvider: 'v8',
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/__tests__/**',
    '!**/node_modules/**',
  ],
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 70,
      lines: 80,
      statements: 80,
    },
  },
};

export default createJestConfig(config);
```

```tsx
// jest.setup.ts
import '@testing-library/jest-dom';

// Mock IntersectionObserver (used by many UI components)
global.IntersectionObserver = class IntersectionObserver {
  constructor(private callback: IntersectionObserverCallback) {}
  observe() { return null; }
  unobserve() { return null; }
  disconnect() { return null; }
  root = null;
  rootMargin = '';
  thresholds = [];
  takeRecords() { return []; }
} as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
} as any;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
```

```json
// package.json scripts
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:ci": "jest --ci --coverage --maxWorkers=50%",
    "test:e2e": "playwright test"
  }
}
```

**First test — a simple component**:

```tsx
// components/Button.tsx
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
  loading?: boolean;
}

export function Button({ children, onClick, variant = 'primary', disabled, loading }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={variant === 'primary' ? 'bg-blue-600 text-white' : 'border text-gray-700'}
      aria-busy={loading}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}
```

```tsx
// __tests__/components/Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '@/components/Button';

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();

    render(<Button onClick={handleClick}>Click</Button>);
    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button loading>Submit</Button>);

    const button = screen.getByRole('button');
    expect(button).toHaveTextContent('Loading...');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Submit</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

**Run the tests**:

```bash
npm test                 # Run all tests
npm test -- --watch      # Watch mode
npm test -- --coverage   # With coverage report
```

---

## Q2. (Beginner) How do you test Client Components that use Next.js hooks like `useRouter`, `useSearchParams`, and `usePathname`?

**Scenario**: You have a search component that uses `useSearchParams` to read the query string and `useRouter` to update it. How do you test it?

**Answer**:

```tsx
// components/SearchBar.tsx
'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';
import { useCallback, useState, useTransition } from 'react';

export function SearchBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [query, setQuery] = useState(searchParams.get('q') ?? '');

  const handleSearch = useCallback(
    (term: string) => {
      setQuery(term);
      const params = new URLSearchParams(searchParams.toString());

      if (term) {
        params.set('q', term);
      } else {
        params.delete('q');
      }

      startTransition(() => {
        router.replace(`${pathname}?${params.toString()}`);
      });
    },
    [router, pathname, searchParams]
  );

  return (
    <div>
      <input
        type="search"
        placeholder="Search..."
        value={query}
        onChange={(e) => handleSearch(e.target.value)}
        aria-label="Search"
        className="rounded-lg border px-3 py-2"
      />
      {isPending && <span data-testid="loading-indicator">Searching...</span>}
    </div>
  );
}
```

```tsx
// __tests__/components/SearchBar.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from '@/components/SearchBar';

// Mock next/navigation
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockRefresh = jest.fn();
let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    refresh: mockRefresh,
    back: jest.fn(),
    prefetch: jest.fn(),
  }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => '/search',
}));

describe('SearchBar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
  });

  it('renders with empty search input', () => {
    render(<SearchBar />);
    const input = screen.getByRole('searchbox');
    expect(input).toHaveValue('');
  });

  it('initializes from URL search params', () => {
    mockSearchParams = new URLSearchParams('q=react');
    render(<SearchBar />);

    const input = screen.getByRole('searchbox');
    expect(input).toHaveValue('react');
  });

  it('updates URL when user types', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'nextjs');

    // router.replace called with search params
    expect(mockReplace).toHaveBeenCalled();
    const lastCall = mockReplace.mock.calls.at(-1)?.[0];
    expect(lastCall).toContain('q=nextjs');
  });

  it('clears search param when input is emptied', async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams('q=test');
    render(<SearchBar />);

    const input = screen.getByRole('searchbox');
    await user.clear(input);

    expect(mockReplace).toHaveBeenCalled();
  });

  it('has proper accessibility attributes', () => {
    render(<SearchBar />);
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
  });
});
```

**Key patterns**:
1. Mock `next/navigation` hooks using `jest.mock`
2. Control mock state with variables declared outside the mock
3. Reset mocks in `beforeEach`
4. Use `userEvent` (not `fireEvent`) for realistic interactions
5. Test both the initial state and user interactions

---

## Q3. (Beginner) How do you test utility functions and custom hooks in a Next.js project?

**Scenario**: You have utility functions for formatting and a custom hook for debounced search. Test them.

**Answer**:

```tsx
// lib/format.ts
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  });
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + '...';
}
```

```tsx
// __tests__/lib/format.test.ts
import { formatCurrency, formatDate, slugify, truncate } from '@/lib/format';

describe('formatCurrency', () => {
  it('formats USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats negative amounts', () => {
    expect(formatCurrency(-99.99)).toBe('-$99.99');
  });

  it('supports different currencies', () => {
    expect(formatCurrency(1000, 'EUR')).toBe('€1,000.00');
  });

  it('handles large numbers', () => {
    expect(formatCurrency(1_000_000)).toBe('$1,000,000.00');
  });
});

describe('slugify', () => {
  it('converts to lowercase', () => {
    expect(slugify('Hello World')).toBe('hello-world');
  });

  it('replaces special characters', () => {
    expect(slugify('Next.js 15: The Future!')).toBe('next-js-15-the-future');
  });

  it('handles leading/trailing hyphens', () => {
    expect(slugify('--hello world--')).toBe('hello-world');
  });

  it('handles empty string', () => {
    expect(slugify('')).toBe('');
  });
});

describe('truncate', () => {
  it('returns full text if under limit', () => {
    expect(truncate('Hello', 10)).toBe('Hello');
  });

  it('truncates with ellipsis', () => {
    expect(truncate('Hello World', 5)).toBe('Hello...');
  });

  it('handles exact length', () => {
    expect(truncate('Hello', 5)).toBe('Hello');
  });
});
```

**Testing custom hooks** with `renderHook`:

```tsx
// hooks/useDebounce.ts
'use client';

import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

```tsx
// __tests__/hooks/useDebounce.test.ts
import { renderHook, act } from '@testing-library/react';
import { useDebounce } from '@/hooks/useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('hello', 500));
    expect(result.current).toBe('hello');
  });

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'hello', delay: 500 } }
    );

    // Update value
    rerender({ value: 'world', delay: 500 });

    // Before delay: still old value
    expect(result.current).toBe('hello');

    // After delay: new value
    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe('world');
  });

  it('resets timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } }
    );

    rerender({ value: 'ab' });
    act(() => jest.advanceTimersByTime(100));

    rerender({ value: 'abc' });
    act(() => jest.advanceTimersByTime(100));

    rerender({ value: 'abcd' });
    act(() => jest.advanceTimersByTime(100));

    // Only 300ms since last change, not debounced yet
    expect(result.current).toBe('a');

    act(() => jest.advanceTimersByTime(300));
    expect(result.current).toBe('abcd');
  });
});
```

---

## Q4. (Beginner) How do you test a form component with user interactions, validation, and submission?

**Scenario**: You have a contact form with client-side validation. Test the complete user flow including validation errors.

**Answer**:

```tsx
// components/ContactForm.tsx
'use client';

import { useState } from 'react';

interface FormData {
  name: string;
  email: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

export function ContactForm({ onSubmit }: { onSubmit: (data: FormData) => Promise<void> }) {
  const [errors, setErrors] = useState<FormErrors>({});
  const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');

  function validate(data: FormData): FormErrors {
    const errors: FormErrors = {};
    if (!data.name.trim()) errors.name = 'Name is required';
    if (!data.email.trim()) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) errors.email = 'Invalid email format';
    if (!data.message.trim()) errors.message = 'Message is required';
    else if (data.message.length < 10) errors.message = 'Message must be at least 10 characters';
    return errors;
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data: FormData = {
      name: formData.get('name') as string,
      email: formData.get('email') as string,
      message: formData.get('message') as string,
    };

    const validationErrors = validate(data);
    setErrors(validationErrors);

    if (Object.keys(validationErrors).length > 0) return;

    setStatus('submitting');
    try {
      await onSubmit(data);
      setStatus('success');
    } catch {
      setStatus('error');
    }
  }

  if (status === 'success') {
    return <div role="alert">Thank you! Your message has been sent.</div>;
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" name="name" type="text" aria-describedby={errors.name ? 'name-error' : undefined} />
        {errors.name && <span id="name-error" role="alert">{errors.name}</span>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" aria-describedby={errors.email ? 'email-error' : undefined} />
        {errors.email && <span id="email-error" role="alert">{errors.email}</span>}
      </div>

      <div>
        <label htmlFor="message">Message</label>
        <textarea id="message" name="message" aria-describedby={errors.message ? 'message-error' : undefined} />
        {errors.message && <span id="message-error" role="alert">{errors.message}</span>}
      </div>

      {status === 'error' && <div role="alert">Something went wrong. Please try again.</div>}

      <button type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
```

```tsx
// __tests__/components/ContactForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContactForm } from '@/components/ContactForm';

describe('ContactForm', () => {
  const mockSubmit = jest.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<ContactForm onSubmit={mockSubmit} />);

    expect(screen.getByLabelText('Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Message')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send Message' })).toBeInTheDocument();
  });

  it('shows validation errors for empty form', async () => {
    const user = userEvent.setup();
    render(<ContactForm onSubmit={mockSubmit} />);

    await user.click(screen.getByRole('button', { name: 'Send Message' }));

    expect(screen.getByText('Name is required')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByText('Message is required')).toBeInTheDocument();
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('shows email format error', async () => {
    const user = userEvent.setup();
    render(<ContactForm onSubmit={mockSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'John');
    await user.type(screen.getByLabelText('Email'), 'invalid-email');
    await user.type(screen.getByLabelText('Message'), 'This is a test message');

    await user.click(screen.getByRole('button', { name: 'Send Message' }));

    expect(screen.getByText('Invalid email format')).toBeInTheDocument();
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<ContactForm onSubmit={mockSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'Jane Doe');
    await user.type(screen.getByLabelText('Email'), 'jane@example.com');
    await user.type(screen.getByLabelText('Message'), 'Hello, this is a test message!');

    await user.click(screen.getByRole('button', { name: 'Send Message' }));

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledWith({
        name: 'Jane Doe',
        email: 'jane@example.com',
        message: 'Hello, this is a test message!',
      });
    });

    expect(screen.getByText('Thank you! Your message has been sent.')).toBeInTheDocument();
  });

  it('shows error state on submission failure', async () => {
    const user = userEvent.setup();
    mockSubmit.mockRejectedValueOnce(new Error('Network error'));

    render(<ContactForm onSubmit={mockSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'Jane');
    await user.type(screen.getByLabelText('Email'), 'jane@test.com');
    await user.type(screen.getByLabelText('Message'), 'Test message here');

    await user.click(screen.getByRole('button', { name: 'Send Message' }));

    await waitFor(() => {
      expect(screen.getByText('Something went wrong. Please try again.')).toBeInTheDocument();
    });
  });

  it('disables submit button while submitting', async () => {
    const user = userEvent.setup();
    let resolveSubmit: () => void;
    mockSubmit.mockImplementation(() => new Promise<void>((r) => { resolveSubmit = r; }));

    render(<ContactForm onSubmit={mockSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'Jane');
    await user.type(screen.getByLabelText('Email'), 'jane@test.com');
    await user.type(screen.getByLabelText('Message'), 'Test message content');

    await user.click(screen.getByRole('button', { name: 'Send Message' }));

    expect(screen.getByRole('button', { name: 'Sending...' })).toBeDisabled();

    resolveSubmit!();
  });
});
```

---

## Q5. (Beginner) How do you mock `fetch` calls and test components that fetch data?

**Scenario**: A Client Component fetches data from an API endpoint. Test both success and error states.

**Answer**:

```tsx
// components/UserList.tsx
'use client';

import { useEffect, useState } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
}

export function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUsers() {
      try {
        const res = await fetch('/api/users');
        if (!res.ok) throw new Error('Failed to fetch users');
        const data = await res.json();
        setUsers(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }
    fetchUsers();
  }, []);

  if (loading) return <div role="status">Loading users...</div>;
  if (error) return <div role="alert">Error: {error}</div>;
  if (users.length === 0) return <p>No users found.</p>;

  return (
    <ul role="list">
      {users.map((user) => (
        <li key={user.id}>
          <span>{user.name}</span>
          <span>{user.email}</span>
        </li>
      ))}
    </ul>
  );
}
```

```tsx
// __tests__/components/UserList.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { UserList } from '@/components/UserList';

const mockUsers = [
  { id: '1', name: 'Alice', email: 'alice@test.com' },
  { id: '2', name: 'Bob', email: 'bob@test.com' },
];

describe('UserList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading state initially', () => {
    global.fetch = jest.fn(() => new Promise(() => {})) as jest.Mock; // Never resolves
    render(<UserList />);
    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  it('renders users after successful fetch', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUsers,
    }) as jest.Mock;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });

    expect(screen.getByRole('list')).toBeInTheDocument();
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
  });

  it('shows error on fetch failure', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
    }) as jest.Mock;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Failed to fetch users');
    });
  });

  it('shows empty state when no users', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }) as jest.Mock;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('No users found.')).toBeInTheDocument();
    });
  });

  it('handles network error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error')) as jest.Mock;

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Network error');
    });
  });
});
```

**Key patterns**:
- Mock `global.fetch` for each test scenario
- Test loading, success, empty, and error states
- Use `waitFor` for async state changes
- Clean up mocks in `beforeEach`

---

## Q6. (Intermediate) How do you test Server Components in Next.js 15?

**Scenario**: You have an async Server Component that fetches data from a database and renders it. How do you test it?

**Answer**:

Server Components are **async functions that return JSX**. You can test them by calling the function and rendering the result.

```tsx
// app/users/page.tsx — Server Component
import { prisma } from '@/lib/prisma';
import { notFound } from 'next/navigation';

async function getUsers() {
  return prisma.user.findMany({
    select: { id: true, name: true, email: true, role: true },
    orderBy: { createdAt: 'desc' },
    take: 50,
  });
}

export default async function UsersPage() {
  const users = await getUsers();

  if (users.length === 0) {
    return <p className="text-center text-gray-500">No users found.</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Users ({users.length})</h1>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.name}</td>
              <td>{user.email}</td>
              <td>{user.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

```tsx
// __tests__/app/users/page.test.tsx
import { render, screen } from '@testing-library/react';
import UsersPage from '@/app/users/page';

// Mock Prisma
jest.mock('@/lib/prisma', () => ({
  prisma: {
    user: {
      findMany: jest.fn(),
    },
  },
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
  redirect: jest.fn(),
}));

import { prisma } from '@/lib/prisma';

const mockFindMany = prisma.user.findMany as jest.Mock;

describe('UsersPage (Server Component)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user list', async () => {
    mockFindMany.mockResolvedValue([
      { id: '1', name: 'Alice', email: 'alice@test.com', role: 'admin' },
      { id: '2', name: 'Bob', email: 'bob@test.com', role: 'user' },
    ]);

    // Server Components are async — await the component
    const jsx = await UsersPage();
    render(jsx);

    expect(screen.getByText('Users (2)')).toBeInTheDocument();
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('alice@test.com')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
  });

  it('shows empty state when no users', async () => {
    mockFindMany.mockResolvedValue([]);

    const jsx = await UsersPage();
    render(jsx);

    expect(screen.getByText('No users found.')).toBeInTheDocument();
  });

  it('queries with correct parameters', async () => {
    mockFindMany.mockResolvedValue([]);

    await UsersPage();

    expect(mockFindMany).toHaveBeenCalledWith({
      select: { id: true, name: true, email: true, role: true },
      orderBy: { createdAt: 'desc' },
      take: 50,
    });
  });
});
```

**Key pattern for Server Component testing**:
1. The component is an `async function` — `await` it to get JSX
2. Mock all external dependencies (database, APIs)
3. Mock `next/navigation` functions (`notFound`, `redirect`)
4. Render the returned JSX with React Testing Library
5. Assert on the rendered output

---

## Q7. (Intermediate) How do you test Server Actions in Next.js 15?

**Scenario**: You have Server Actions for creating and deleting tasks. Test them including auth checks, validation, and database operations.

**Answer**:

```tsx
// app/tasks/actions.ts
'use server';

import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const createTaskSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100),
  description: z.string().max(500).optional(),
  priority: z.enum(['low', 'medium', 'high']),
});

export async function createTask(formData: FormData) {
  const session = await auth();
  if (!session?.user) {
    return { error: 'Unauthorized' };
  }

  const raw = {
    title: formData.get('title'),
    description: formData.get('description'),
    priority: formData.get('priority'),
  };

  const parsed = createTaskSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  const task = await prisma.task.create({
    data: {
      ...parsed.data,
      userId: session.user.id!,
    },
  });

  revalidatePath('/tasks');
  return { success: true, task };
}

export async function deleteTask(taskId: string) {
  const session = await auth();
  if (!session?.user) {
    return { error: 'Unauthorized' };
  }

  const task = await prisma.task.findUnique({
    where: { id: taskId },
    select: { userId: true },
  });

  if (!task) return { error: 'Task not found' };
  if (task.userId !== session.user.id) return { error: 'Forbidden' };

  await prisma.task.delete({ where: { id: taskId } });
  revalidatePath('/tasks');
  return { success: true };
}
```

```tsx
// __tests__/app/tasks/actions.test.ts
import { createTask, deleteTask } from '@/app/tasks/actions';

// Mock dependencies
jest.mock('@/auth', () => ({
  auth: jest.fn(),
}));

jest.mock('@/lib/prisma', () => ({
  prisma: {
    task: {
      create: jest.fn(),
      findUnique: jest.fn(),
      delete: jest.fn(),
    },
  },
}));

jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';

const mockAuth = auth as jest.Mock;
const mockCreate = prisma.task.create as jest.Mock;
const mockFindUnique = prisma.task.findUnique as jest.Mock;
const mockDelete = prisma.task.delete as jest.Mock;
const mockRevalidate = revalidatePath as jest.Mock;

function createFormData(data: Record<string, string>): FormData {
  const fd = new FormData();
  Object.entries(data).forEach(([key, value]) => fd.set(key, value));
  return fd;
}

describe('createTask', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns error if user is not authenticated', async () => {
    mockAuth.mockResolvedValue(null);

    const result = await createTask(
      createFormData({ title: 'Test', priority: 'low' })
    );

    expect(result).toEqual({ error: 'Unauthorized' });
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('returns validation error for empty title', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });

    const result = await createTask(
      createFormData({ title: '', priority: 'low' })
    );

    expect(result.error).toBeDefined();
    expect(mockCreate).not.toHaveBeenCalled();
  });

  it('creates task with valid data', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });
    mockCreate.mockResolvedValue({
      id: 't1',
      title: 'New Task',
      priority: 'high',
      userId: 'u1',
    });

    const result = await createTask(
      createFormData({
        title: 'New Task',
        description: 'A description',
        priority: 'high',
      })
    );

    expect(result).toEqual({
      success: true,
      task: expect.objectContaining({ id: 't1', title: 'New Task' }),
    });

    expect(mockCreate).toHaveBeenCalledWith({
      data: {
        title: 'New Task',
        description: 'A description',
        priority: 'high',
        userId: 'u1',
      },
    });

    expect(mockRevalidate).toHaveBeenCalledWith('/tasks');
  });
});

describe('deleteTask', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns error if not authenticated', async () => {
    mockAuth.mockResolvedValue(null);

    const result = await deleteTask('t1');
    expect(result).toEqual({ error: 'Unauthorized' });
  });

  it('returns error if task not found', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });
    mockFindUnique.mockResolvedValue(null);

    const result = await deleteTask('nonexistent');
    expect(result).toEqual({ error: 'Task not found' });
  });

  it('returns error if user does not own task', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });
    mockFindUnique.mockResolvedValue({ userId: 'u2' });

    const result = await deleteTask('t1');
    expect(result).toEqual({ error: 'Forbidden' });
  });

  it('deletes task owned by user', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });
    mockFindUnique.mockResolvedValue({ userId: 'u1' });
    mockDelete.mockResolvedValue({});

    const result = await deleteTask('t1');

    expect(result).toEqual({ success: true });
    expect(mockDelete).toHaveBeenCalledWith({ where: { id: 't1' } });
    expect(mockRevalidate).toHaveBeenCalledWith('/tasks');
  });
});
```

**Key patterns for testing Server Actions**:
1. Mock `auth()` to simulate authenticated/unauthenticated states
2. Mock database operations (Prisma)
3. Mock `revalidatePath` / `revalidateTag`
4. Use `FormData` constructor for form-based actions
5. Test all authorization paths (unauthenticated, wrong user, correct user)

---

## Q8. (Intermediate) How do you test Route Handlers (API routes) in Next.js 15?

**Scenario**: You have a Route Handler at `/api/posts` with GET and POST methods. Test them directly.

**Answer**:

```tsx
// app/api/posts/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';
import { z } from 'zod';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const page = parseInt(searchParams.get('page') ?? '1');
  const limit = parseInt(searchParams.get('limit') ?? '10');

  const posts = await prisma.post.findMany({
    skip: (page - 1) * limit,
    take: limit,
    orderBy: { createdAt: 'desc' },
    select: { id: true, title: true, excerpt: true, createdAt: true },
  });

  const total = await prisma.post.count();

  return NextResponse.json({
    posts,
    pagination: { page, limit, total, totalPages: Math.ceil(total / limit) },
  });
}

const createPostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1),
  published: z.boolean().optional(),
});

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const parsed = createPostSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Validation failed', details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const post = await prisma.post.create({
    data: {
      ...parsed.data,
      authorId: session.user.id!,
    },
  });

  return NextResponse.json(post, { status: 201 });
}
```

```tsx
// __tests__/app/api/posts/route.test.ts
import { GET, POST } from '@/app/api/posts/route';

jest.mock('@/auth', () => ({
  auth: jest.fn(),
}));

jest.mock('@/lib/prisma', () => ({
  prisma: {
    post: {
      findMany: jest.fn(),
      count: jest.fn(),
      create: jest.fn(),
    },
  },
}));

import { auth } from '@/auth';
import { prisma } from '@/lib/prisma';

const mockAuth = auth as jest.Mock;

describe('GET /api/posts', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns paginated posts', async () => {
    const mockPosts = [
      { id: '1', title: 'Post 1', excerpt: 'Excerpt 1', createdAt: new Date() },
    ];
    (prisma.post.findMany as jest.Mock).mockResolvedValue(mockPosts);
    (prisma.post.count as jest.Mock).mockResolvedValue(25);

    const request = new Request('http://localhost/api/posts?page=1&limit=10');
    const response = await GET(request);
    const json = await response.json();

    expect(response.status).toBe(200);
    expect(json.posts).toEqual(mockPosts);
    expect(json.pagination).toEqual({
      page: 1,
      limit: 10,
      total: 25,
      totalPages: 3,
    });
  });

  it('uses default pagination when no params', async () => {
    (prisma.post.findMany as jest.Mock).mockResolvedValue([]);
    (prisma.post.count as jest.Mock).mockResolvedValue(0);

    const request = new Request('http://localhost/api/posts');
    await GET(request);

    expect(prisma.post.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ skip: 0, take: 10 })
    );
  });
});

describe('POST /api/posts', () => {
  beforeEach(() => jest.clearAllMocks());

  it('returns 401 when not authenticated', async () => {
    mockAuth.mockResolvedValue(null);

    const request = new Request('http://localhost/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test', content: 'Content' }),
    });

    const response = await POST(request);
    expect(response.status).toBe(401);
  });

  it('returns 400 for invalid data', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });

    const request = new Request('http://localhost/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '' }), // Missing content
    });

    const response = await POST(request);
    expect(response.status).toBe(400);

    const json = await response.json();
    expect(json.error).toBe('Validation failed');
  });

  it('creates post with valid data', async () => {
    mockAuth.mockResolvedValue({ user: { id: 'u1' } });
    (prisma.post.create as jest.Mock).mockResolvedValue({
      id: 'p1',
      title: 'My Post',
      content: 'Content here',
      authorId: 'u1',
    });

    const request = new Request('http://localhost/api/posts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'My Post', content: 'Content here' }),
    });

    const response = await POST(request);
    expect(response.status).toBe(201);

    const json = await response.json();
    expect(json).toEqual(expect.objectContaining({ id: 'p1', title: 'My Post' }));
  });
});
```

**Key pattern**: Route Handlers are regular async functions — construct `Request` objects and assert on the returned `Response` objects.

---

## Q9. (Intermediate) How do you test middleware in Next.js?

**Scenario**: Your middleware handles auth redirects, rate limiting, and header injection. How do you test each behavior?

**Answer**:

```tsx
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

const protectedRoutes = ['/dashboard', '/settings', '/admin'];
const authRoutes = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get('auth-token')?.value;

  // Redirect unauthenticated users from protected routes
  if (protectedRoutes.some((r) => pathname.startsWith(r)) && !token) {
    const url = new URL('/login', request.url);
    url.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(url);
  }

  // Redirect authenticated users from auth routes
  if (authRoutes.some((r) => pathname.startsWith(r)) && token) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Add security headers
  const response = NextResponse.next();
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');

  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

```tsx
// __tests__/middleware.test.ts
import { NextRequest } from 'next/server';
import { middleware } from '@/middleware';

function createRequest(
  pathname: string,
  options?: { cookies?: Record<string, string>; headers?: Record<string, string> }
): NextRequest {
  const url = new URL(pathname, 'http://localhost:3000');
  const request = new NextRequest(url, {
    headers: options?.headers ?? {},
  });

  if (options?.cookies) {
    Object.entries(options.cookies).forEach(([name, value]) => {
      request.cookies.set(name, value);
    });
  }

  return request;
}

describe('middleware', () => {
  describe('protected routes', () => {
    it('redirects unauthenticated users to login', () => {
      const request = createRequest('/dashboard');
      const response = middleware(request);

      expect(response.status).toBe(307);
      const location = response.headers.get('location');
      expect(location).toContain('/login');
      expect(location).toContain('callbackUrl=%2Fdashboard');
    });

    it('allows authenticated users to access protected routes', () => {
      const request = createRequest('/dashboard', {
        cookies: { 'auth-token': 'valid-token' },
      });
      const response = middleware(request);

      expect(response.status).toBe(200); // NextResponse.next()
    });

    it('redirects from /settings when unauthenticated', () => {
      const request = createRequest('/settings/profile');
      const response = middleware(request);

      expect(response.status).toBe(307);
      const location = response.headers.get('location');
      expect(location).toContain('/login');
    });
  });

  describe('auth routes', () => {
    it('redirects authenticated users away from /login', () => {
      const request = createRequest('/login', {
        cookies: { 'auth-token': 'valid-token' },
      });
      const response = middleware(request);

      expect(response.status).toBe(307);
      expect(response.headers.get('location')).toContain('/dashboard');
    });

    it('allows unauthenticated users to access /login', () => {
      const request = createRequest('/login');
      const response = middleware(request);

      expect(response.status).toBe(200);
    });
  });

  describe('security headers', () => {
    it('adds X-Frame-Options header', () => {
      const request = createRequest('/');
      const response = middleware(request);

      expect(response.headers.get('X-Frame-Options')).toBe('DENY');
    });

    it('adds X-Content-Type-Options header', () => {
      const request = createRequest('/about');
      const response = middleware(request);

      expect(response.headers.get('X-Content-Type-Options')).toBe('nosniff');
    });
  });

  describe('public routes', () => {
    it('allows access to public pages without auth', () => {
      const request = createRequest('/');
      const response = middleware(request);

      expect(response.status).toBe(200);
    });

    it('allows access to /about without auth', () => {
      const request = createRequest('/about');
      const response = middleware(request);

      expect(response.status).toBe(200);
    });
  });
});
```

---

## Q10. (Intermediate) How do you set up Mock Service Worker (MSW) for testing Next.js API interactions?

**Scenario**: Instead of mocking `fetch` globally, you want a more robust API mocking solution. Set up MSW for both unit and integration tests.

**Answer**:

```bash
npm install -D msw
```

```tsx
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

const users = [
  { id: '1', name: 'Alice', email: 'alice@test.com', role: 'admin' },
  { id: '2', name: 'Bob', email: 'bob@test.com', role: 'user' },
];

export const handlers = [
  // GET /api/users
  http.get('http://localhost:3000/api/users', ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get('search')?.toLowerCase();

    const filtered = search
      ? users.filter(
          (u) =>
            u.name.toLowerCase().includes(search) ||
            u.email.toLowerCase().includes(search)
        )
      : users;

    return HttpResponse.json({
      users: filtered,
      total: filtered.length,
    });
  }),

  // GET /api/users/:id
  http.get('http://localhost:3000/api/users/:id', ({ params }) => {
    const user = users.find((u) => u.id === params.id);
    if (!user) {
      return HttpResponse.json({ error: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json(user);
  }),

  // POST /api/users
  http.post('http://localhost:3000/api/users', async ({ request }) => {
    const body = (await request.json()) as { name: string; email: string };

    if (!body.name || !body.email) {
      return HttpResponse.json({ error: 'Validation failed' }, { status: 400 });
    }

    const newUser = { id: String(users.length + 1), ...body, role: 'user' };
    return HttpResponse.json(newUser, { status: 201 });
  }),

  // DELETE /api/users/:id
  http.delete('http://localhost:3000/api/users/:id', ({ params }) => {
    const user = users.find((u) => u.id === params.id);
    if (!user) {
      return HttpResponse.json({ error: 'Not found' }, { status: 404 });
    }
    return HttpResponse.json({ success: true });
  }),
];
```

```tsx
// mocks/server.ts — Node.js server for tests
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```tsx
// jest.setup.ts — Add MSW setup
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```tsx
// __tests__/integration/user-management.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import { UserList } from '@/components/UserList';

describe('User Management (Integration)', () => {
  it('loads and displays users', async () => {
    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('Alice')).toBeInTheDocument();
      expect(screen.getByText('Bob')).toBeInTheDocument();
    });
  });

  it('handles server error gracefully', async () => {
    // Override handler for this test only
    server.use(
      http.get('http://localhost:3000/api/users', () => {
        return HttpResponse.json({ error: 'Internal error' }, { status: 500 });
      })
    );

    render(<UserList />);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('handles slow responses with loading state', async () => {
    server.use(
      http.get('http://localhost:3000/api/users', async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return HttpResponse.json({ users: [], total: 0 });
      })
    );

    render(<UserList />);

    // Loading state should be visible
    expect(screen.getByText('Loading users...')).toBeInTheDocument();

    // Wait for data
    await waitFor(() => {
      expect(screen.queryByText('Loading users...')).not.toBeInTheDocument();
    });
  });
});
```

**Advantages of MSW over manual fetch mocking**:
1. **Network-level interception** — tests real fetch calls, not mocked functions
2. **Handler reuse** — same handlers work for unit, integration, and browser tests
3. **Request inspection** — verify request headers, body, and params
4. **Per-test overrides** — use `server.use()` for specific scenarios
5. **Type-safe** — full TypeScript support with `msw` v2

---

## Q11. (Intermediate) How do you test loading and error states (loading.tsx, error.tsx) in the App Router?

**Scenario**: Your route has `loading.tsx` and `error.tsx` files. How do you verify they render correctly?

**Answer**:

```tsx
// app/dashboard/loading.tsx
export default function DashboardLoading() {
  return (
    <div role="status" aria-label="Loading dashboard">
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
      <div className="mt-6 h-64 animate-pulse rounded-lg bg-gray-200" />
    </div>
  );
}

// app/dashboard/error.tsx
'use client';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6">
      <h2 className="text-lg font-semibold text-red-800">Something went wrong!</h2>
      <p className="mt-2 text-sm text-red-600">{error.message}</p>
      {error.digest && (
        <p className="mt-1 text-xs text-red-400">Error ID: {error.digest}</p>
      )}
      <button
        onClick={reset}
        className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
      >
        Try again
      </button>
    </div>
  );
}
```

```tsx
// __tests__/app/dashboard/loading.test.tsx
import { render, screen } from '@testing-library/react';
import DashboardLoading from '@/app/dashboard/loading';

describe('DashboardLoading', () => {
  it('renders loading skeleton', () => {
    render(<DashboardLoading />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByLabelText('Loading dashboard')).toBeInTheDocument();
  });

  it('renders correct number of skeleton cards', () => {
    const { container } = render(<DashboardLoading />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });
});
```

```tsx
// __tests__/app/dashboard/error.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardError from '@/app/dashboard/error';

describe('DashboardError', () => {
  const mockReset = jest.fn();
  const mockError = new Error('Failed to load dashboard data');

  beforeEach(() => jest.clearAllMocks());

  it('displays error message', () => {
    render(<DashboardError error={mockError} reset={mockReset} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Something went wrong!')).toBeInTheDocument();
    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
  });

  it('displays error digest when available', () => {
    const errorWithDigest = Object.assign(new Error('Test error'), {
      digest: 'abc123',
    });

    render(<DashboardError error={errorWithDigest} reset={mockReset} />);
    expect(screen.getByText('Error ID: abc123')).toBeInTheDocument();
  });

  it('calls reset when "Try again" is clicked', async () => {
    const user = userEvent.setup();
    render(<DashboardError error={mockError} reset={mockReset} />);

    await user.click(screen.getByRole('button', { name: 'Try again' }));
    expect(mockReset).toHaveBeenCalledTimes(1);
  });
});
```

---

## Q12. (Intermediate) How do you test dynamic routes with `params` and `searchParams` in Next.js 15?

**Scenario**: A blog post page receives dynamic `params` (slug) and `searchParams` (comment highlight). Both are Promises in Next.js 15.

**Answer**:

```tsx
// app/blog/[slug]/page.tsx
interface BlogPostPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ highlight?: string }>;
}

export default async function BlogPostPage({ params, searchParams }: BlogPostPageProps) {
  const { slug } = await params;
  const { highlight } = await searchParams;

  const post = await fetch(`https://api.example.com/posts/${slug}`).then((r) => r.json());

  if (!post) {
    const { notFound } = await import('next/navigation');
    notFound();
  }

  return (
    <article>
      <h1>{post.title}</h1>
      <p>Published: {post.date}</p>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />
      {highlight && (
        <div id="highlighted" className="bg-yellow-100 p-2 rounded">
          Highlighted comment: {highlight}
        </div>
      )}
    </article>
  );
}
```

```tsx
// __tests__/app/blog/[slug]/page.test.tsx
import { render, screen } from '@testing-library/react';
import BlogPostPage from '@/app/blog/[slug]/page';

// Mock fetch
global.fetch = jest.fn() as jest.Mock;

jest.mock('next/navigation', () => ({
  notFound: jest.fn(),
}));

const mockPost = {
  title: 'Understanding RSC',
  date: '2026-02-15',
  content: '<p>Server Components are powerful.</p>',
};

describe('BlogPostPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      json: async () => mockPost,
    });
  });

  it('renders blog post with correct slug', async () => {
    // In Next.js 15, params is a Promise
    const jsx = await BlogPostPage({
      params: Promise.resolve({ slug: 'understanding-rsc' }),
      searchParams: Promise.resolve({}),
    });

    render(jsx);

    expect(screen.getByText('Understanding RSC')).toBeInTheDocument();
    expect(screen.getByText('Published: 2026-02-15')).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      'https://api.example.com/posts/understanding-rsc'
    );
  });

  it('renders highlighted comment when searchParam is present', async () => {
    const jsx = await BlogPostPage({
      params: Promise.resolve({ slug: 'understanding-rsc' }),
      searchParams: Promise.resolve({ highlight: 'comment-42' }),
    });

    render(jsx);

    expect(screen.getByText('Highlighted comment: comment-42')).toBeInTheDocument();
  });

  it('does not render highlight section without searchParam', async () => {
    const jsx = await BlogPostPage({
      params: Promise.resolve({ slug: 'understanding-rsc' }),
      searchParams: Promise.resolve({}),
    });

    render(jsx);

    expect(screen.queryByText(/Highlighted comment/)).not.toBeInTheDocument();
  });
});
```

---

## Q13. (Advanced) How do you set up end-to-end testing with Playwright for a Next.js application?

**Scenario**: Set up Playwright for E2E testing of a Next.js app with auth flows, navigation, and form submissions.

**Answer**:

```bash
npm install -D @playwright/test
npx playwright install
```

```tsx
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    // Auth setup — runs first and saves state
    { name: 'setup', testMatch: /.*\.setup\.ts/, teardown: 'cleanup' },
    { name: 'cleanup', testMatch: /.*\.teardown\.ts/ },

    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'mobile',
      use: {
        ...devices['iPhone 14'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },

    // Unauthenticated tests (no storageState)
    { name: 'unauthenticated', testMatch: /.*\.unauth\.spec\.ts/ },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

**Auth setup** (runs once, saves cookies for all tests):

```tsx
// e2e/auth.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'e2e/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('testpassword123');
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard');
  expect(page.url()).toContain('/dashboard');

  // Save auth state
  await page.context().storageState({ path: authFile });
});
```

**E2E test for dashboard flow**:

```tsx
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('displays user name and stats', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByText('test@example.com')).toBeVisible();
  });

  test('navigates to settings', async ({ page }) => {
    await page.goto('/dashboard');

    await page.getByRole('link', { name: 'Settings' }).click();
    await expect(page).toHaveURL('/settings');
  });

  test('creates a new task', async ({ page }) => {
    await page.goto('/dashboard');

    await page.getByRole('button', { name: 'New Task' }).click();

    // Fill the dialog form
    await page.getByLabel('Title').fill('E2E Test Task');
    await page.getByLabel('Description').fill('Created by Playwright');
    await page.getByLabel('Priority').selectOption('high');

    await page.getByRole('button', { name: 'Create' }).click();

    // Verify task appears in the list
    await expect(page.getByText('E2E Test Task')).toBeVisible();
  });

  test('deletes a task', async ({ page }) => {
    await page.goto('/dashboard');

    // Find the task and click delete
    const taskRow = page.getByText('E2E Test Task').locator('..');
    await taskRow.getByRole('button', { name: 'Delete' }).click();

    // Confirm deletion
    await page.getByRole('button', { name: 'Confirm' }).click();

    await expect(page.getByText('E2E Test Task')).not.toBeVisible();
  });
});
```

**E2E test for unauthenticated flows**:

```tsx
// e2e/auth.unauth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('redirects to login when accessing protected route', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('wrong@test.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page.getByText(/Invalid/i)).toBeVisible();
  });

  test('redirects to dashboard after login', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('testpassword123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    await expect(page).toHaveURL('/dashboard');
  });

  test('preserves callbackUrl after login', async ({ page }) => {
    await page.goto('/settings/profile');

    // Redirected to login with callbackUrl
    await expect(page).toHaveURL(/\/login\?callbackUrl/);

    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('testpassword123');
    await page.getByRole('button', { name: 'Sign In' }).click();

    // Redirected back to the original URL
    await expect(page).toHaveURL('/settings/profile');
  });
});
```

**Run E2E tests**:

```bash
npx playwright test              # Run all tests
npx playwright test --ui         # Interactive UI mode
npx playwright test --headed     # See the browser
npx playwright show-report       # View HTML report
```

---

## Q14. (Advanced) How do you test caching behavior (fetch caching, revalidation, tags) in Next.js?

**Scenario**: Your Server Components use `fetch` with `next: { revalidate }` and `next: { tags }`. How do you test that caching and revalidation work correctly?

**Answer**:

```tsx
// lib/api.ts
export async function getProducts() {
  const res = await fetch('https://api.example.com/products', {
    next: { revalidate: 3600, tags: ['products'] },
  });
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

export async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: { tags: [`product-${id}`] },
  });
  if (!res.ok) throw new Error('Failed to fetch product');
  return res.json();
}
```

```tsx
// __tests__/lib/api.test.ts
import { getProducts, getProduct } from '@/lib/api';

describe('API functions', () => {
  beforeEach(() => {
    global.fetch = jest.fn() as jest.Mock;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('getProducts', () => {
    it('calls fetch with correct caching options', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => [{ id: '1', name: 'Widget' }],
      });

      await getProducts();

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/products',
        {
          next: { revalidate: 3600, tags: ['products'] },
        }
      );
    });

    it('throws on failed response', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 500 });

      await expect(getProducts()).rejects.toThrow('Failed to fetch products');
    });
  });

  describe('getProduct', () => {
    it('includes product-specific cache tag', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({ id: 'p1', name: 'Widget' }),
      });

      await getProduct('p1');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.example.com/products/p1',
        { next: { tags: ['product-p1'] } }
      );
    });
  });
});
```

**Testing revalidation in Server Actions**:

```tsx
// app/products/actions.ts
'use server';

import { revalidateTag, revalidatePath } from 'next/cache';
import { prisma } from '@/lib/prisma';

export async function updateProduct(id: string, data: { name: string; price: number }) {
  await prisma.product.update({ where: { id }, data });

  // Revalidate specific product and product list
  revalidateTag(`product-${id}`);
  revalidateTag('products');
  revalidatePath('/products');

  return { success: true };
}
```

```tsx
// __tests__/app/products/actions.test.ts
import { updateProduct } from '@/app/products/actions';

jest.mock('next/cache', () => ({
  revalidateTag: jest.fn(),
  revalidatePath: jest.fn(),
}));

jest.mock('@/lib/prisma', () => ({
  prisma: { product: { update: jest.fn() } },
}));

import { revalidateTag, revalidatePath } from 'next/cache';

describe('updateProduct', () => {
  it('revalidates correct tags after update', async () => {
    const { prisma } = require('@/lib/prisma');
    prisma.product.update.mockResolvedValue({});

    await updateProduct('p1', { name: 'Updated Widget', price: 29.99 });

    expect(revalidateTag).toHaveBeenCalledWith('product-p1');
    expect(revalidateTag).toHaveBeenCalledWith('products');
    expect(revalidatePath).toHaveBeenCalledWith('/products');
  });
});
```

**E2E test for caching/revalidation**:

```tsx
// e2e/caching.spec.ts
import { test, expect } from '@playwright/test';

test('revalidation updates the page', async ({ page }) => {
  // Visit products page
  await page.goto('/products');

  const initialPrice = await page.getByTestId('product-p1-price').textContent();

  // Trigger a price update via API
  await page.request.post('/api/products/p1', {
    data: { name: 'Widget', price: 39.99 },
  });

  // Reload page (should get revalidated data)
  await page.reload();

  const updatedPrice = await page.getByTestId('product-p1-price').textContent();

  expect(updatedPrice).not.toBe(initialPrice);
  expect(updatedPrice).toContain('39.99');
});
```

---

## Q15. (Advanced) How do you implement a comprehensive CI/CD test pipeline for a Next.js project?

**Scenario**: Set up a GitHub Actions pipeline that runs linting, type checking, unit tests, integration tests, and E2E tests on every PR.

**Answer**:

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb

jobs:
  # Job 1: Lint + Type Check (fastest — fail fast)
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit

  # Job 2: Unit + Integration Tests
  test-unit:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - name: Setup database
        run: npx prisma db push
      - name: Seed test data
        run: npx prisma db seed
      - name: Run tests
        run: npm run test:ci
        env:
          DATABASE_URL: ${{ env.DATABASE_URL }}
          JWT_SECRET: test-secret-min-32-characters-long
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info

  # Job 3: E2E Tests
  test-e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npx prisma db push
      - run: npx prisma db seed
      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium
      - name: Build Next.js
        run: npm run build
        env:
          DATABASE_URL: ${{ env.DATABASE_URL }}
      - name: Run E2E tests
        run: npx playwright test --project=chromium
        env:
          DATABASE_URL: ${{ env.DATABASE_URL }}
          JWT_SECRET: test-secret-min-32-characters-long
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7

  # Job 4: Build verification
  build:
    name: Production Build
    runs-on: ubuntu-latest
    needs: [test-unit, test-e2e]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - name: Build
        run: npm run build
        env:
          DATABASE_URL: ${{ env.DATABASE_URL }}
      - name: Check bundle size
        run: npx @next/bundle-analyzer
```

```json
// package.json — Test scripts
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:ci": "jest --ci --coverage --maxWorkers=50%",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "npm run test:ci && npm run test:e2e",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  }
}
```

**Pipeline stages**:
1. **Lint + Type Check** — fastest, catches obvious issues
2. **Unit + Integration Tests** — tests logic in isolation
3. **E2E Tests** — tests full user flows
4. **Build** — verifies production build succeeds

---

## Q16. (Advanced) How do you test Server Components that use `cookies()`, `headers()`, and other Next.js server functions?

**Scenario**: Your Server Component reads cookies for theme, headers for locale, and uses `cache()` for deduplication. How do you mock all of these?

**Answer**:

```tsx
// app/dashboard/page.tsx
import { cookies, headers } from 'next/headers';
import { cache } from 'react';
import { prisma } from '@/lib/prisma';

const getUser = cache(async (userId: string) => {
  return prisma.user.findUnique({
    where: { id: userId },
    select: { id: true, name: true, preferences: true },
  });
});

export default async function DashboardPage() {
  const cookieStore = await cookies();
  const headerStore = await headers();

  const theme = cookieStore.get('theme')?.value ?? 'system';
  const locale = headerStore.get('accept-language')?.split(',')[0] ?? 'en';
  const userId = cookieStore.get('user-id')?.value;

  if (!userId) {
    const { redirect } = await import('next/navigation');
    redirect('/login');
  }

  const user = await getUser(userId);

  return (
    <div data-theme={theme} data-locale={locale}>
      <h1>Welcome, {user?.name ?? 'User'}</h1>
      <p>Theme: {theme}</p>
      <p>Locale: {locale}</p>
    </div>
  );
}
```

```tsx
// __tests__/app/dashboard/page.test.tsx
import { render, screen } from '@testing-library/react';
import DashboardPage from '@/app/dashboard/page';

// Mock next/headers
const mockCookies = new Map<string, { value: string }>();
const mockHeaders = new Map<string, string>();

jest.mock('next/headers', () => ({
  cookies: jest.fn(async () => ({
    get: (name: string) => mockCookies.get(name),
    getAll: () => Array.from(mockCookies.entries()).map(([name, { value }]) => ({ name, value })),
    has: (name: string) => mockCookies.has(name),
    set: jest.fn(),
    delete: jest.fn(),
  })),
  headers: jest.fn(async () => ({
    get: (name: string) => mockHeaders.get(name),
    has: (name: string) => mockHeaders.has(name),
    entries: () => mockHeaders.entries(),
    forEach: (cb: (v: string, k: string) => void) => mockHeaders.forEach(cb),
  })),
}));

jest.mock('next/navigation', () => ({
  redirect: jest.fn(),
  notFound: jest.fn(),
}));

jest.mock('@/lib/prisma', () => ({
  prisma: {
    user: { findUnique: jest.fn() },
  },
}));

import { redirect } from 'next/navigation';
import { prisma } from '@/lib/prisma';

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCookies.clear();
    mockHeaders.clear();
  });

  it('redirects if no user-id cookie', async () => {
    const jsx = await DashboardPage();

    expect(redirect).toHaveBeenCalledWith('/login');
  });

  it('renders user name and theme', async () => {
    mockCookies.set('user-id', { value: 'u1' });
    mockCookies.set('theme', { value: 'dark' });
    mockHeaders.set('accept-language', 'fr-FR,fr;q=0.9');

    (prisma.user.findUnique as jest.Mock).mockResolvedValue({
      id: 'u1',
      name: 'Alice',
      preferences: {},
    });

    const jsx = await DashboardPage();
    render(jsx);

    expect(screen.getByText('Welcome, Alice')).toBeInTheDocument();
    expect(screen.getByText('Theme: dark')).toBeInTheDocument();
    expect(screen.getByText('Locale: fr-FR')).toBeInTheDocument();
  });

  it('uses default theme and locale when not set', async () => {
    mockCookies.set('user-id', { value: 'u1' });

    (prisma.user.findUnique as jest.Mock).mockResolvedValue({
      id: 'u1',
      name: 'Bob',
      preferences: {},
    });

    const jsx = await DashboardPage();
    render(jsx);

    expect(screen.getByText('Theme: system')).toBeInTheDocument();
    expect(screen.getByText('Locale: en')).toBeInTheDocument();
  });
});
```

---

## Q17. (Advanced) How do you implement snapshot testing and component visual testing for a Next.js component library?

**Scenario**: Your shared component library needs automated testing to catch unintended UI changes. Implement both Jest snapshots and Playwright visual comparisons.

**Answer**:

**Jest snapshot testing**:

```tsx
// __tests__/components/snapshots/Button.snapshot.test.tsx
import { render } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button Snapshots', () => {
  it('matches default variant snapshot', () => {
    const { container } = render(<Button>Click me</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches destructive variant snapshot', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches outline variant snapshot', () => {
    const { container } = render(<Button variant="outline">Cancel</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches loading state snapshot', () => {
    const { container } = render(<Button loading>Saving...</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('matches all sizes', () => {
    const sizes = ['sm', 'default', 'lg', 'icon'] as const;

    sizes.forEach((size) => {
      const { container } = render(<Button size={size}>Button</Button>);
      expect(container.firstChild).toMatchSnapshot(`Button-size-${size}`);
    });
  });
});
```

**Inline snapshots for smaller, more readable tests**:

```tsx
// __tests__/components/Badge.snapshot.test.tsx
import { render } from '@testing-library/react';
import { Badge } from '@/components/ui/badge';

it('renders success badge', () => {
  const { container } = render(<Badge variant="success">Active</Badge>);

  expect(container.innerHTML).toMatchInlineSnapshot(
    `"<span class="badge badge-success">Active</span>"`
  );
});
```

**Playwright visual regression testing**:

```tsx
// e2e/visual/components.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Component Visual Tests', () => {
  test('Button variants', async ({ page }) => {
    await page.goto('/components/button');

    // Full page screenshot
    await expect(page).toHaveScreenshot('button-all-variants.png', {
      fullPage: true,
    });

    // Individual component screenshots
    const primaryBtn = page.getByTestId('button-primary');
    await expect(primaryBtn).toHaveScreenshot('button-primary.png');

    // Hover state
    await primaryBtn.hover();
    await expect(primaryBtn).toHaveScreenshot('button-primary-hover.png');

    // Disabled state
    const disabledBtn = page.getByTestId('button-disabled');
    await expect(disabledBtn).toHaveScreenshot('button-disabled.png');
  });

  test('Card component', async ({ page }) => {
    await page.goto('/components/card');
    await expect(page.getByTestId('card-default')).toHaveScreenshot('card-default.png');
  });

  test('Dark mode variants', async ({ page }) => {
    await page.goto('/components/button');

    // Light mode screenshot
    await expect(page).toHaveScreenshot('button-light.png');

    // Toggle dark mode
    await page.evaluate(() => document.documentElement.classList.add('dark'));
    await expect(page).toHaveScreenshot('button-dark.png');
  });

  test('Responsive layouts', async ({ page }) => {
    await page.goto('/components/card');

    // Mobile
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page).toHaveScreenshot('card-mobile.png');

    // Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot('card-tablet.png');

    // Desktop
    await page.setViewportSize({ width: 1440, height: 900 });
    await expect(page).toHaveScreenshot('card-desktop.png');
  });
});
```

**Update snapshots**:

```bash
# Jest snapshots
npx jest --updateSnapshot

# Playwright screenshots
npx playwright test --update-snapshots
```

**When to use each**:

| Approach | Best For | Catches |
|----------|----------|---------|
| Jest Snapshots | HTML structure changes | Markup changes, class changes |
| Playwright Visual | Pixel-level rendering | CSS changes, font issues, layout shifts |
| Jest Inline Snapshots | Small components | Quick verification of simple output |

---

## Q18. (Advanced) How do you test performance and Core Web Vitals in a Next.js application?

**Scenario**: You need automated performance testing to prevent regressions in LCP, CLS, and FID/INP across deployments.

**Answer**:

```tsx
// e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('homepage loads within performance budget', async ({ page }) => {
    // Start performance measurement
    await page.goto('/', { waitUntil: 'networkidle' });

    const metrics = await page.evaluate(() => {
      return new Promise<{
        lcp: number | null;
        cls: number;
        fcp: number | null;
        ttfb: number | null;
      }>((resolve) => {
        let lcp: number | null = null;
        let cls = 0;

        // Observe LCP
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          lcp = entries[entries.length - 1]?.startTime ?? null;
        }).observe({ type: 'largest-contentful-paint', buffered: true });

        // Observe CLS
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              cls += (entry as any).value;
            }
          }
        }).observe({ type: 'layout-shift', buffered: true });

        // Get navigation timing
        const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        const fcp = performance.getEntriesByType('paint').find(
          (e) => e.name === 'first-contentful-paint'
        )?.startTime ?? null;

        // Wait a bit for all observers to fire
        setTimeout(() => {
          resolve({
            lcp,
            cls,
            fcp,
            ttfb: nav?.responseStart ?? null,
          });
        }, 3000);
      });
    });

    // Assert performance budgets
    console.log('Performance metrics:', metrics);

    if (metrics.lcp !== null) {
      expect(metrics.lcp).toBeLessThan(2500); // LCP < 2.5s (Good)
    }
    expect(metrics.cls).toBeLessThan(0.1); // CLS < 0.1 (Good)
    if (metrics.fcp !== null) {
      expect(metrics.fcp).toBeLessThan(1800); // FCP < 1.8s
    }
    if (metrics.ttfb !== null) {
      expect(metrics.ttfb).toBeLessThan(800); // TTFB < 800ms
    }
  });

  test('no significant JavaScript bundle size regression', async ({ page }) => {
    const jsBundles: number[] = [];

    page.on('response', (response) => {
      if (response.url().includes('/_next/static') && response.url().endsWith('.js')) {
        const contentLength = response.headers()['content-length'];
        if (contentLength) jsBundles.push(parseInt(contentLength));
      }
    });

    await page.goto('/', { waitUntil: 'networkidle' });

    const totalJsSize = jsBundles.reduce((a, b) => a + b, 0);
    const totalJsSizeKB = totalJsSize / 1024;

    console.log(`Total JS bundle size: ${totalJsSizeKB.toFixed(1)}KB`);

    // Budget: total JS should be under 200KB (compressed)
    expect(totalJsSizeKB).toBeLessThan(200);
  });

  test('images use next/image optimization', async ({ page }) => {
    await page.goto('/');

    const images = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('img')).map((img) => ({
        src: img.src,
        loading: img.loading,
        width: img.width,
        height: img.height,
        hasWidthHeight: img.hasAttribute('width') && img.hasAttribute('height'),
        isSrcSet: !!img.srcset,
      }));
    });

    for (const img of images) {
      // All images should have width and height (prevents CLS)
      expect(img.hasWidthHeight).toBe(true);

      // Non-critical images should be lazy loaded
      if (!img.src.includes('hero') && !img.src.includes('logo')) {
        expect(img.loading).toBe('lazy');
      }
    }
  });
});
```

**Lighthouse CI integration**:

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse CI
on:
  pull_request:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      - run: npm ci
      - run: npm run build
      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v12
        with:
          urls: |
            http://localhost:3000/
            http://localhost:3000/dashboard
          budgetPath: ./lighthouse-budget.json
          uploadArtifacts: true
          configPath: ./lighthouserc.json
```

```json
// lighthouse-budget.json
[
  {
    "path": "/*",
    "timings": [
      { "metric": "first-contentful-paint", "budget": 1800 },
      { "metric": "largest-contentful-paint", "budget": 2500 },
      { "metric": "cumulative-layout-shift", "budget": 0.1 },
      { "metric": "total-blocking-time", "budget": 200 }
    ],
    "resourceSizes": [
      { "resourceType": "script", "budget": 200 },
      { "resourceType": "stylesheet", "budget": 30 },
      { "resourceType": "total", "budget": 500 }
    ]
  }
]
```

---

## Q19. (Advanced) How do you test Next.js applications with complex data dependencies using test factories and seeding?

**Scenario**: Your tests need consistent, type-safe test data for users, projects, and tasks with relationships. Implement a test factory pattern.

**Answer**:

```tsx
// tests/factories/index.ts
import { prisma } from '@/lib/prisma';
import { faker } from '@faker-js/faker';
import bcrypt from 'bcryptjs';

type Override<T> = Partial<T>;

// User factory
export async function createUser(overrides: Override<{
  name: string;
  email: string;
  password: string;
  role: string;
  emailVerified: Date | null;
}> = {}) {
  const password = overrides.password ?? 'TestPassword123!';
  const passwordHash = await bcrypt.hash(password, 4); // Low cost for speed in tests

  return prisma.user.create({
    data: {
      name: overrides.name ?? faker.person.fullName(),
      email: overrides.email ?? faker.internet.email().toLowerCase(),
      passwordHash,
      role: overrides.role ?? 'user',
      emailVerified: overrides.emailVerified ?? new Date(),
      failedLoginAttempts: 0,
      onboardingComplete: true,
    },
  });
}

// Project factory
export async function createProject(overrides: Override<{
  name: string;
  ownerId: string;
}> = {}) {
  const owner = overrides.ownerId
    ? { connect: { id: overrides.ownerId } }
    : { create: { ...(await createUserData()) } };

  return prisma.project.create({
    data: {
      name: overrides.name ?? faker.company.name() + ' Project',
      owner,
    },
    include: { owner: true },
  });
}

// Task factory
export async function createTask(overrides: Override<{
  title: string;
  description: string;
  priority: string;
  status: string;
  projectId: string;
  userId: string;
}> = {}) {
  return prisma.task.create({
    data: {
      title: overrides.title ?? faker.lorem.sentence(),
      description: overrides.description ?? faker.lorem.paragraph(),
      priority: overrides.priority ?? 'medium',
      status: overrides.status ?? 'todo',
      projectId: overrides.projectId!,
      userId: overrides.userId!,
    },
  });
}

async function createUserData() {
  return {
    name: faker.person.fullName(),
    email: faker.internet.email().toLowerCase(),
    passwordHash: await bcrypt.hash('TestPassword123!', 4),
    role: 'user',
    emailVerified: new Date(),
    failedLoginAttempts: 0,
    onboardingComplete: true,
  };
}

// Scenario builder — creates a complete test scenario
export async function createDashboardScenario() {
  const admin = await createUser({ role: 'admin', email: 'admin@test.com' });
  const user = await createUser({ role: 'user', email: 'user@test.com' });

  const project = await createProject({ name: 'Test Project', ownerId: admin.id });

  const tasks = await Promise.all([
    createTask({ title: 'Task 1', priority: 'high', status: 'todo', projectId: project.id, userId: admin.id }),
    createTask({ title: 'Task 2', priority: 'medium', status: 'in_progress', projectId: project.id, userId: user.id }),
    createTask({ title: 'Task 3', priority: 'low', status: 'done', projectId: project.id, userId: admin.id }),
  ]);

  return { admin, user, project, tasks };
}

// Cleanup helper
export async function cleanupDatabase() {
  const tablenames = await prisma.$queryRaw<
    Array<{ tablename: string }>
  >`SELECT tablename FROM pg_tables WHERE schemaname='public'`;

  for (const { tablename } of tablenames) {
    if (tablename !== '_prisma_migrations') {
      try {
        await prisma.$executeRawUnsafe(`TRUNCATE TABLE "public"."${tablename}" CASCADE;`);
      } catch (error) {
        console.error(`Failed to truncate ${tablename}:`, error);
      }
    }
  }
}
```

**Using factories in tests**:

```tsx
// __tests__/integration/dashboard.test.ts
import { createDashboardScenario, cleanupDatabase, createUser } from '@/tests/factories';

describe('Dashboard Integration', () => {
  let scenario: Awaited<ReturnType<typeof createDashboardScenario>>;

  beforeAll(async () => {
    scenario = await createDashboardScenario();
  });

  afterAll(async () => {
    await cleanupDatabase();
  });

  it('admin sees all tasks', async () => {
    // Mock auth as admin
    jest.mocked(auth).mockResolvedValue({
      user: { id: scenario.admin.id, role: 'admin' },
    } as any);

    const page = await DashboardPage();
    render(page);

    expect(screen.getByText('Task 1')).toBeInTheDocument();
    expect(screen.getByText('Task 2')).toBeInTheDocument();
    expect(screen.getByText('Task 3')).toBeInTheDocument();
  });

  it('user sees only assigned tasks', async () => {
    jest.mocked(auth).mockResolvedValue({
      user: { id: scenario.user.id, role: 'user' },
    } as any);

    // ... assert user only sees their tasks
  });
});
```

---

## Q20. (Advanced) How do you implement a test coverage strategy and testing best practices for a production Next.js codebase?

**Scenario**: You're the tech lead establishing testing standards for a 50-developer team. Define the strategy, coverage requirements, and best practices.

**Answer**:

```
┌───────────────── Test Coverage Strategy ──────────────────────┐
│                                                               │
│  Layer          │ Coverage │ Tools          │ Runs When       │
│  ═══════════════╪══════════╪════════════════╪═════════════════│
│  Unit Tests     │   80%+   │ Jest + RTL     │ Every commit    │
│  Server Actions │   90%+   │ Jest           │ Every commit    │
│  Route Handlers │   90%+   │ Jest           │ Every commit    │
│  Integration    │   70%+   │ Jest + MSW     │ Every PR        │
│  E2E (critical) │ 100%     │ Playwright     │ Every PR        │
│  E2E (full)     │   80%+   │ Playwright     │ Pre-deploy      │
│  Visual         │ Key pages│ Playwright     │ PR (CSS change) │
│  Performance    │ Budgets  │ Lighthouse     │ Pre-deploy      │
│                                                               │
│  Overall Target: 80% line coverage                            │
│  Critical paths: 95%+ coverage                                │
└───────────────────────────────────────────────────────────────┘
```

**Testing standards document**:

```tsx
// testing-guidelines.ts — Team testing conventions

/**
 * TESTING STANDARDS
 *
 * 1. TEST NAMING:
 *    - Describe the behavior, not the implementation
 *    - Good: "redirects unauthenticated users to login"
 *    - Bad:  "calls redirect function"
 *
 * 2. TEST STRUCTURE (AAA):
 *    - Arrange: Set up test data and mocks
 *    - Act: Perform the action
 *    - Assert: Verify the result
 *
 * 3. WHAT TO TEST:
 *    - ✅ User-visible behavior
 *    - ✅ Edge cases and error states
 *    - ✅ Accessibility (roles, labels)
 *    - ✅ Auth boundary enforcement
 *    - ❌ Implementation details
 *    - ❌ Third-party library internals
 *    - ❌ CSS class names
 *
 * 4. MOCKING RULES:
 *    - Mock at the boundary (database, APIs, auth)
 *    - Don't mock what you own (test real components)
 *    - Use MSW for API mocking over manual fetch mocks
 *
 * 5. FILE ORGANIZATION:
 *    - __tests__/components/  — Component tests
 *    - __tests__/lib/         — Utility tests
 *    - __tests__/app/         — Server Component & Action tests
 *    - __tests__/integration/ — Integration tests
 *    - e2e/                   — Playwright tests
 */
```

**Coverage configuration with thresholds**:

```tsx
// jest.config.ts — Coverage thresholds
const config: Config = {
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80,
    },
    // Stricter thresholds for critical paths
    './lib/permissions/': {
      branches: 95,
      functions: 95,
      lines: 95,
      statements: 95,
    },
    './app/**/actions.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './app/api/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
  },
};
```

**Test helpers library**:

```tsx
// tests/helpers.tsx
import { render, type RenderOptions } from '@testing-library/react';
import { SessionProvider } from 'next-auth/react';

// Custom render with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  session?: any;
}

export function renderWithProviders(ui: React.ReactElement, options: CustomRenderOptions = {}) {
  const { session, ...renderOptions } = options;

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <SessionProvider session={session}>
        {children}
      </SessionProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Helper to create mock session
export function createMockSession(overrides: Record<string, any> = {}) {
  return {
    user: {
      id: 'test-user-id',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      ...overrides,
    },
    expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  };
}

// Helper to wait for async operations
export function waitForMs(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Helper to create FormData from object
export function createFormData(data: Record<string, string>): FormData {
  const fd = new FormData();
  Object.entries(data).forEach(([k, v]) => fd.set(k, v));
  return fd;
}
```

**What to test per component type**:

| Component Type | What to Test | Not to Test |
|---------------|-------------|-------------|
| Server Component | Data rendering, auth guards, redirect behavior | Internal data fetching implementation |
| Client Component | User interactions, state changes, event handlers | Implementation details |
| Server Action | Auth, validation, DB operations, revalidation | Internal helper functions |
| Route Handler | Status codes, response body, auth, validation | Internal parsing logic |
| Middleware | Redirects, header injection, cookie handling | Exact URL construction |
| Utility Functions | Input/output, edge cases, error handling | — |
| Custom Hooks | State changes, side effects, cleanup | React internals |

**Critical paths that must have 95%+ coverage**:
1. Authentication flows (login, logout, token refresh)
2. Authorization checks (middleware, Server Actions)
3. Payment processing
4. Data mutation operations
5. User-facing error handling

**Testing anti-patterns to avoid**:

```tsx
// ❌ BAD: Testing implementation details
it('calls useState with initial value', () => {
  const spy = jest.spyOn(React, 'useState');
  render(<Counter />);
  expect(spy).toHaveBeenCalledWith(0);
});

// ✅ GOOD: Testing behavior
it('starts at zero and increments', async () => {
  const user = userEvent.setup();
  render(<Counter />);
  expect(screen.getByText('Count: 0')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Increment' }));
  expect(screen.getByText('Count: 1')).toBeInTheDocument();
});

// ❌ BAD: Snapshot everything
it('matches snapshot', () => {
  const { container } = render(<ComplexPage />);
  expect(container).toMatchSnapshot(); // Brittle, 1000+ line snapshot
});

// ✅ GOOD: Test specific behavior + targeted snapshots
it('renders header with user name', () => {
  render(<ComplexPage />);
  expect(screen.getByRole('heading', { name: /Dashboard/ })).toBeInTheDocument();
});
```

**Production testing checklist**:
1. Every Server Action has auth + validation + happy path + error path tests
2. Every Route Handler has status code + response body tests
3. Every protected route has middleware redirect tests
4. Critical user flows have E2E tests
5. Performance budgets are enforced in CI
6. Visual regression tests cover key pages in light/dark mode
7. Test coverage is tracked and has minimum thresholds
8. Tests run in < 5 minutes (unit) + < 15 minutes (E2E)
