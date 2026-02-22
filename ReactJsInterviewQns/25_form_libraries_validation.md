# Form Libraries & Validation — React 18 Interview Questions

## Topic Introduction

Form management is one of the most nuanced challenges in React development. At a glance, forms seem simple — capture user input, validate it, submit it. But production forms involve deeply interconnected concerns: field-level vs. form-level validation, dynamic fields that add and remove themselves, multi-step wizards with partial persistence, file uploads with progress tracking, accessibility for screen readers, and server-side validation errors that must be mapped back to specific fields. In React 18, the choice of how you manage form state has direct performance implications because every keystroke can trigger a re-render of the entire form tree if you rely naively on controlled components with `useState`. This is precisely why libraries like **React Hook Form (RHF)** emerged — by embracing uncontrolled components and refs under the hood, RHF isolates re-renders to only the fields that change, resulting in drastically fewer renders in large forms. Paired with **Zod** for schema-based validation, you get a type-safe, performant, and declarative form layer that scales from simple login forms to complex enterprise data-entry systems.

**React Hook Form** leverages the native browser form API and `useRef` internally so that input values are tracked without re-rendering the host component on every change. Its API surface — `register`, `handleSubmit`, `formState`, `watch`, `control`, `useFieldArray`, `useController` — is designed around progressive disclosure: simple forms need only `register` and `handleSubmit`, while complex forms can opt into `Controller` for third-party UI libraries or `useFieldArray` for dynamic lists. **Zod**, on the other hand, is a TypeScript-first schema declaration and validation library that lets you define the *shape* of your data in one place and derive TypeScript types from it, eliminating the duplication between your form types and your validation rules. The `@hookform/resolvers` package bridges these two worlds with `zodResolver`, feeding your Zod schema into RHF's validation pipeline. This combination has become the de facto standard in the React 18 ecosystem, used by Next.js starters, T3 Stack, and countless production applications.

Below is a foundational example that ties together RHF, Zod, and React 18. It shows a registration form with schema-based validation, inline error display, and type-safe form values:

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// 1. Define the schema — single source of truth
const registrationSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

// 2. Derive the TypeScript type from the schema
// type RegistrationForm = z.infer<typeof registrationSchema>;

function RegistrationPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registrationSchema),
    defaultValues: { username: '', email: '', password: '', confirmPassword: '' },
  });

  const onSubmit = async (data) => {
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Registration failed');
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div>
        <label htmlFor="username">Username</label>
        <input id="username" {...register('username')} />
        {errors.username && <span role="alert">{errors.username.message}</span>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input id="password" type="password" {...register('password')} />
        {errors.password && <span role="alert">{errors.password.message}</span>}
      </div>

      <div>
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input id="confirmPassword" type="password" {...register('confirmPassword')} />
        {errors.confirmPassword && (
          <span role="alert">{errors.confirmPassword.message}</span>
        )}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Registering…' : 'Register'}
      </button>
    </form>
  );
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What is the difference between controlled and uncontrolled form patterns in React, and when would you choose one over the other?

**Answer:**

In **controlled** components, React state is the single source of truth for the input value. Every keystroke triggers a state update via `onChange`, and the input always renders the current state value. In **uncontrolled** components, the DOM itself holds the value — you read it via a `ref` when needed (typically on submit).

**Controlled** components give you fine-grained access to the value on every render, which is essential for features like live character counts, inline validation on each keystroke, or conditional UI that depends on the current field value. The downside is that every keystroke calls `setState`, which re-renders the component (and potentially its children).

**Uncontrolled** components are simpler and faster for forms where you only need the value at submission time. They avoid the re-render overhead entirely. React Hook Form is built on this principle — it registers inputs as uncontrolled by default, only triggering re-renders when specific observed values (like errors) change.

```jsx
import { useState, useRef } from 'react';

// Controlled — React state drives the input
function ControlledInput() {
  const [value, setValue] = useState('');

  return (
    <div>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <p>Characters: {value.length}</p> {/* Live feedback */}
    </div>
  );
}

// Uncontrolled — DOM holds the value, read via ref
function UncontrolledInput() {
  const inputRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Submitted value:', inputRef.current.value);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input ref={inputRef} defaultValue="" />
      <button type="submit">Submit</button>
    </form>
  );
}

// React Hook Form — uncontrolled under the hood, controlled API surface
import { useForm } from 'react-hook-form';

function RHFInput() {
  const { register, handleSubmit } = useForm();

  const onSubmit = (data) => console.log(data);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* register() returns ref + onChange + onBlur — all uncontrolled */}
      <input {...register('email')} />
      <button type="submit">Submit</button>
    </form>
  );
}
```

---

### Q2. What are the core APIs of React Hook Form — `register`, `handleSubmit`, and `formState` — and how do they work together?

**Answer:**

React Hook Form's `useForm` hook returns an object with methods and state that orchestrate the entire form lifecycle:

- **`register(name, options?)`** — Returns an object containing `ref`, `onChange`, `onBlur`, and `name`. Spreading this onto an `<input>` tells RHF to track that field. The `ref` is how RHF reads the DOM value without re-rendering. Options let you add native validation rules like `required`, `minLength`, `pattern`, etc.

- **`handleSubmit(onValid, onInvalid?)`** — Returns an event handler that, when the form submits, first runs validation. If valid, it calls `onValid(data)` with the collected form values. If invalid, it calls `onInvalid(errors)` (optional) and populates `formState.errors`.

- **`formState`** — A reactive object containing `errors`, `isDirty`, `isValid`, `isSubmitting`, `isSubmitted`, `touchedFields`, `dirtyFields`, `submitCount`, and more. RHF uses a Proxy to track which properties you access, so it only re-renders when those specific properties change.

```jsx
import { useForm } from 'react-hook-form';

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty, isSubmitting, isValid, touchedFields },
  } = useForm({
    mode: 'onBlur',           // validate on blur (not on every change)
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data) => {
    // data is { email: string, password: string } — fully typed if using TS
    await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address',
            },
          })}
        />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          {...register('password', {
            required: 'Password is required',
            minLength: { value: 8, message: 'At least 8 characters' },
          })}
        />
        {errors.password && <span role="alert">{errors.password.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting || !isDirty}>
        {isSubmitting ? 'Logging in…' : 'Log In'}
      </button>

      {/* Debug info */}
      <pre>
        Dirty: {String(isDirty)} | Valid: {String(isValid)} |
        Touched: {JSON.stringify(touchedFields)}
      </pre>
    </form>
  );
}
```

---

### Q3. How do you define validation schemas with Zod, and what makes it different from other validation libraries like Yup?

**Answer:**

Zod is a **TypeScript-first** schema declaration and validation library. You define the shape and constraints of your data using a chainable API, and Zod can both **validate runtime data** and **infer static TypeScript types** from the same schema. This eliminates the common problem of having a TypeScript interface and a separate Yup schema that can drift apart.

Key differences from Yup:
1. **Type inference** — `z.infer<typeof schema>` gives you the exact TypeScript type. Yup added `InferType` later, but Zod was designed around it from day one.
2. **Immutable schemas** — Every Zod method returns a new schema instance. Yup mutates internally.
3. **Composability** — Zod supports discriminated unions, intersections, recursive types, transformations, and refinements natively.
4. **No dependencies** — Zod is zero-dependency. Yup depends on property-expr, tiny-case, and toposort.
5. **Stricter by default** — Zod does not coerce types. `z.string()` rejects numbers. Yup's `string()` coerces by default.

```jsx
import { z } from 'zod';

// Basic schema definition
const UserSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  email: z.string().email('Must be a valid email'),
  age: z.number().int().min(18, 'Must be at least 18').max(120),
  role: z.enum(['admin', 'editor', 'viewer']),
  bio: z.string().optional(),   // optional field
  tags: z.array(z.string()).default([]),  // default value
});

// Infer TypeScript type — stays in sync automatically
// type User = z.infer<typeof UserSchema>;
// Result: { name: string; email: string; age: number; role: 'admin' | 'editor' | 'viewer'; bio?: string; tags: string[] }

// Parsing (throws ZodError on failure)
try {
  const validUser = UserSchema.parse({
    name: 'Alice',
    email: 'alice@example.com',
    age: 30,
    role: 'admin',
  });
  console.log(validUser); // { name: 'Alice', email: '...', age: 30, role: 'admin', tags: [] }
} catch (err) {
  console.error(err.issues); // Array of detailed error objects
}

// Safe parsing (no throw — returns { success, data } or { success, error })
const result = UserSchema.safeParse({ name: '', email: 'bad', age: 15, role: 'hacker' });
if (!result.success) {
  result.error.issues.forEach((issue) => {
    console.log(`${issue.path.join('.')}: ${issue.message}`);
    // "name: Name is required"
    // "email: Must be a valid email"
    // "age: Must be at least 18"
    // "role: Invalid enum value. Expected 'admin' | 'editor' | 'viewer', received 'hacker'"
  });
}

// Transformations — parse and transform in one step
const CurrencySchema = z.string().transform((val) => parseFloat(val.replace(/[$,]/g, '')));
console.log(CurrencySchema.parse('$1,234.56')); // 1234.56
```

---

### Q4. How do you integrate Zod with React Hook Form using `zodResolver`, and what benefits does this integration provide?

**Answer:**

The `@hookform/resolvers` package provides `zodResolver`, which acts as a bridge between Zod's schema validation and React Hook Form's validation pipeline. You pass `zodResolver(schema)` as the `resolver` option in `useForm()`. When the form is submitted (or on blur/change depending on the `mode`), RHF feeds the form values into the Zod schema. If validation fails, the Zod errors are automatically mapped to RHF's `formState.errors` object, keyed by field name.

**Benefits:**
1. **Single source of truth** — Your schema defines both validation rules and TypeScript types.
2. **Decoupled validation** — Validation logic lives outside the component, making it testable in isolation.
3. **Consistent error format** — Zod errors are normalised into RHF's `{ message, type }` structure automatically.
4. **Cross-field validation** — Zod's `.refine()` and `.superRefine()` handle dependent field validation (e.g., password confirmation) natively.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Schema — portable, testable, framework-agnostic
const contactSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  subject: z.enum(['general', 'support', 'billing'], {
    errorMap: () => ({ message: 'Please select a subject' }),
  }),
  message: z.string().min(10, 'Message must be at least 10 characters').max(1000),
});

function ContactForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(contactSchema),
    defaultValues: { name: '', email: '', subject: '', message: '' },
  });

  const onSubmit = async (data) => {
    // data is already validated and typed
    await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    reset(); // clear form on success
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div>
        <label htmlFor="name">Name</label>
        <input id="name" {...register('name')} />
        {errors.name && <p role="alert">{errors.name.message}</p>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register('email')} />
        {errors.email && <p role="alert">{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="subject">Subject</label>
        <select id="subject" {...register('subject')}>
          <option value="">Select…</option>
          <option value="general">General</option>
          <option value="support">Support</option>
          <option value="billing">Billing</option>
        </select>
        {errors.subject && <p role="alert">{errors.subject.message}</p>}
      </div>

      <div>
        <label htmlFor="message">Message</label>
        <textarea id="message" rows={5} {...register('message')} />
        {errors.message && <p role="alert">{errors.message.message}</p>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending…' : 'Send Message'}
      </button>
    </form>
  );
}
```

---

### Q5. What are common patterns for displaying form errors in React, and how does React Hook Form facilitate error rendering?

**Answer:**

There are several patterns for displaying form errors, ranging from simple inline messages to toast notifications. The most common approaches are:

1. **Inline field errors** — Display the error message directly below the offending input. This is the most user-friendly pattern for field-level validation.
2. **Error summary** — Display all errors in a list at the top of the form, often linked to the corresponding fields for keyboard navigation. This is an accessibility best practice (WCAG).
3. **Toast / banner errors** — For server-side or submission-level errors that don't map to a specific field.
4. **Validation mode** — `onBlur` (validate when the user leaves the field), `onChange` (validate on every keystroke), `onSubmit` (validate only on submit), or `onTouched` (validate on first blur, then on every change). RHF supports all via the `mode` option.

RHF provides `formState.errors` as a nested object mirroring the field structure. For nested fields like `address.city`, errors are at `errors.address?.city`. The `ErrorMessage` component from `@hookform/error-message` simplifies rendering.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ErrorMessage } from '@hookform/error-message';

const schema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email'),
});

// Reusable error component
function FieldError({ errors, name }) {
  return (
    <ErrorMessage
      errors={errors}
      name={name}
      render={({ message }) => (
        <p role="alert" style={{ color: 'red', fontSize: '0.85rem', marginTop: 4 }}>
          {message}
        </p>
      )}
    />
  );
}

function SignUpForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    mode: 'onTouched', // validate on first blur, then re-validate on change
  });

  const onSubmit = (data) => console.log(data);

  // Collect all error messages for the summary
  const errorEntries = Object.entries(errors);

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      {/* Pattern 1: Error Summary at the top */}
      {errorEntries.length > 0 && (
        <div role="alert" aria-label="Form errors" style={{ border: '1px solid red', padding: 12 }}>
          <p>Please fix the following errors:</p>
          <ul>
            {errorEntries.map(([field, error]) => (
              <li key={field}>
                <a href={`#${field}`}>{error.message}</a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Pattern 2: Inline errors */}
      <div>
        <label htmlFor="firstName">First Name</label>
        <input
          id="firstName"
          {...register('firstName')}
          aria-invalid={!!errors.firstName}
          aria-describedby={errors.firstName ? 'firstName-error' : undefined}
        />
        <FieldError errors={errors} name="firstName" />
      </div>

      <div>
        <label htmlFor="lastName">Last Name</label>
        <input
          id="lastName"
          {...register('lastName')}
          aria-invalid={!!errors.lastName}
        />
        <FieldError errors={errors} name="lastName" />
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          {...register('email')}
          aria-invalid={!!errors.email}
        />
        <FieldError errors={errors} name="email" />
      </div>

      <button type="submit">Sign Up</button>
    </form>
  );
}
```

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you build dynamic form fields using `useFieldArray` in React Hook Form, and what are the common production pitfalls?

**Answer:**

`useFieldArray` is RHF's hook for managing an array of fields — line items in an invoice, multiple addresses, dynamic tag inputs, etc. It provides `fields`, `append`, `remove`, `insert`, `move`, `swap`, `prepend`, `replace`, and `update` methods. The key insight is that it manages a **stable identity** for each item via an auto-generated `id` field, which must be used as the React `key` — never use the array index, because that causes state mismatches when items are reordered or removed.

**Production pitfalls:**
1. **Using index as key** — Causes inputs to retain stale values when items are removed from the middle.
2. **Not setting default values** — `useFieldArray` needs `defaultValues` on the parent `useForm` to initialise properly.
3. **Validation on nested arrays** — Use Zod's `z.array().min(1)` to enforce at least one item.
4. **Performance** — Each append/remove triggers a re-render of the entire field array. For very large lists (100+ items), consider virtualising with `react-window`.

```jsx
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const lineItemSchema = z.object({
  description: z.string().min(1, 'Description required'),
  quantity: z.coerce.number().min(1, 'Min 1'),
  unitPrice: z.coerce.number().min(0.01, 'Min $0.01'),
});

const invoiceSchema = z.object({
  invoiceNumber: z.string().min(1, 'Invoice number required'),
  lineItems: z.array(lineItemSchema).min(1, 'At least one line item is required'),
});

function InvoiceForm() {
  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(invoiceSchema),
    defaultValues: {
      invoiceNumber: '',
      lineItems: [{ description: '', quantity: 1, unitPrice: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'lineItems',
  });

  const watchedItems = watch('lineItems');
  const total = watchedItems?.reduce(
    (sum, item) => sum + (Number(item.quantity) || 0) * (Number(item.unitPrice) || 0),
    0
  ) ?? 0;

  const onSubmit = (data) => {
    console.log('Invoice:', data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>Invoice #</label>
        <input {...register('invoiceNumber')} />
        {errors.invoiceNumber && <span role="alert">{errors.invoiceNumber.message}</span>}
      </div>

      <h3>Line Items</h3>
      {errors.lineItems?.root && (
        <p role="alert" style={{ color: 'red' }}>{errors.lineItems.root.message}</p>
      )}

      {fields.map((field, index) => (
        // IMPORTANT: use field.id as key, NOT index
        <div key={field.id} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <div>
            <input
              placeholder="Description"
              {...register(`lineItems.${index}.description`)}
            />
            {errors.lineItems?.[index]?.description && (
              <span role="alert">{errors.lineItems[index].description.message}</span>
            )}
          </div>

          <div>
            <input
              type="number"
              placeholder="Qty"
              {...register(`lineItems.${index}.quantity`)}
            />
            {errors.lineItems?.[index]?.quantity && (
              <span role="alert">{errors.lineItems[index].quantity.message}</span>
            )}
          </div>

          <div>
            <input
              type="number"
              step="0.01"
              placeholder="Unit Price"
              {...register(`lineItems.${index}.unitPrice`)}
            />
            {errors.lineItems?.[index]?.unitPrice && (
              <span role="alert">{errors.lineItems[index].unitPrice.message}</span>
            )}
          </div>

          <button type="button" onClick={() => remove(index)} disabled={fields.length === 1}>
            Remove
          </button>
        </div>
      ))}

      <button type="button" onClick={() => append({ description: '', quantity: 1, unitPrice: 0 })}>
        + Add Line Item
      </button>

      <p><strong>Total: ${total.toFixed(2)}</strong></p>
      <button type="submit">Submit Invoice</button>
    </form>
  );
}
```

---

### Q7. How do you implement a multi-step form wizard with per-step validation using React Hook Form and Zod?

**Answer:**

A multi-step wizard presents form fields across several pages/steps, validating each step independently before allowing the user to proceed. The key architectural decisions are:

1. **Single `useForm` instance** shared across all steps — This preserves all values in one place and avoids synchronisation issues. Each step validates only its own fields using `trigger()` for partial validation.
2. **Per-step Zod schemas** — Define a schema for each step and a combined schema for final submission. Use Zod's `.pick()` or define separate schemas.
3. **Navigation state** — Track the current step index, allow back/next with validation gates, and optionally persist progress.

```jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Per-step schemas
const personalInfoSchema = z.object({
  firstName: z.string().min(1, 'First name required'),
  lastName: z.string().min(1, 'Last name required'),
  email: z.string().email('Invalid email'),
});

const addressSchema = z.object({
  street: z.string().min(1, 'Street required'),
  city: z.string().min(1, 'City required'),
  state: z.string().min(2, 'State required'),
  zip: z.string().regex(/^\d{5}(-\d{4})?$/, 'Invalid ZIP code'),
});

const paymentSchema = z.object({
  cardNumber: z.string().regex(/^\d{16}$/, 'Must be 16 digits'),
  expiry: z.string().regex(/^(0[1-9]|1[0-2])\/\d{2}$/, 'MM/YY format'),
  cvv: z.string().regex(/^\d{3,4}$/, '3-4 digits'),
});

// Combined schema for final validation
const fullSchema = personalInfoSchema.merge(addressSchema).merge(paymentSchema);

// Step configuration
const steps = [
  { title: 'Personal Info', fields: ['firstName', 'lastName', 'email'] },
  { title: 'Address', fields: ['street', 'city', 'state', 'zip'] },
  { title: 'Payment', fields: ['cardNumber', 'expiry', 'cvv'] },
  { title: 'Review', fields: [] },
];

function MultiStepWizard() {
  const [currentStep, setCurrentStep] = useState(0);

  const {
    register,
    handleSubmit,
    trigger,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(fullSchema),
    defaultValues: {
      firstName: '', lastName: '', email: '',
      street: '', city: '', state: '', zip: '',
      cardNumber: '', expiry: '', cvv: '',
    },
    mode: 'onTouched',
  });

  const goNext = async () => {
    const fieldsToValidate = steps[currentStep].fields;
    const isStepValid = await trigger(fieldsToValidate);
    if (isStepValid) setCurrentStep((prev) => prev + 1);
  };

  const goBack = () => setCurrentStep((prev) => prev - 1);

  const onSubmit = async (data) => {
    await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    alert('Order placed!');
  };

  const allValues = getValues();

  return (
    <div>
      {/* Progress indicator */}
      <nav aria-label="Form progress">
        <ol style={{ display: 'flex', gap: 16, listStyle: 'none' }}>
          {steps.map((step, i) => (
            <li key={step.title} style={{ fontWeight: i === currentStep ? 'bold' : 'normal' }}>
              {step.title}
            </li>
          ))}
        </ol>
      </nav>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step 1: Personal Info */}
        {currentStep === 0 && (
          <fieldset>
            <legend>Personal Information</legend>
            <div>
              <label>First Name</label>
              <input {...register('firstName')} />
              {errors.firstName && <span role="alert">{errors.firstName.message}</span>}
            </div>
            <div>
              <label>Last Name</label>
              <input {...register('lastName')} />
              {errors.lastName && <span role="alert">{errors.lastName.message}</span>}
            </div>
            <div>
              <label>Email</label>
              <input type="email" {...register('email')} />
              {errors.email && <span role="alert">{errors.email.message}</span>}
            </div>
          </fieldset>
        )}

        {/* Step 2: Address */}
        {currentStep === 1 && (
          <fieldset>
            <legend>Address</legend>
            <div>
              <label>Street</label>
              <input {...register('street')} />
              {errors.street && <span role="alert">{errors.street.message}</span>}
            </div>
            <div>
              <label>City</label>
              <input {...register('city')} />
              {errors.city && <span role="alert">{errors.city.message}</span>}
            </div>
            <div>
              <label>State</label>
              <input {...register('state')} />
              {errors.state && <span role="alert">{errors.state.message}</span>}
            </div>
            <div>
              <label>ZIP Code</label>
              <input {...register('zip')} />
              {errors.zip && <span role="alert">{errors.zip.message}</span>}
            </div>
          </fieldset>
        )}

        {/* Step 3: Payment */}
        {currentStep === 2 && (
          <fieldset>
            <legend>Payment</legend>
            <div>
              <label>Card Number</label>
              <input {...register('cardNumber')} maxLength={16} />
              {errors.cardNumber && <span role="alert">{errors.cardNumber.message}</span>}
            </div>
            <div>
              <label>Expiry (MM/YY)</label>
              <input {...register('expiry')} placeholder="MM/YY" />
              {errors.expiry && <span role="alert">{errors.expiry.message}</span>}
            </div>
            <div>
              <label>CVV</label>
              <input {...register('cvv')} maxLength={4} />
              {errors.cvv && <span role="alert">{errors.cvv.message}</span>}
            </div>
          </fieldset>
        )}

        {/* Step 4: Review */}
        {currentStep === 3 && (
          <div>
            <h3>Review Your Order</h3>
            <p><strong>Name:</strong> {allValues.firstName} {allValues.lastName}</p>
            <p><strong>Email:</strong> {allValues.email}</p>
            <p><strong>Address:</strong> {allValues.street}, {allValues.city}, {allValues.state} {allValues.zip}</p>
            <p><strong>Card:</strong> ****{allValues.cardNumber?.slice(-4)}</p>
          </div>
        )}

        {/* Navigation */}
        <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
          {currentStep > 0 && (
            <button type="button" onClick={goBack}>Back</button>
          )}
          {currentStep < steps.length - 1 ? (
            <button type="button" onClick={goNext}>Next</button>
          ) : (
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Placing Order…' : 'Place Order'}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
```

---

### Q8. How does React Hook Form compare to Formik? What are the key performance and API differences, and how would you migrate from Formik to RHF?

**Answer:**

**Formik** and **React Hook Form** solve the same problem — managing form state, validation, and submission — but with fundamentally different architectures:

| Aspect | Formik | React Hook Form |
|--------|--------|-----------------|
| **State model** | Controlled — stores values in React state, re-renders on every change | Uncontrolled — stores values in refs, minimal re-renders |
| **Re-renders** | Every keystroke re-renders the entire `<Formik>` subtree | Only re-renders when observed `formState` properties change |
| **Bundle size** | ~12.7 kB gzip | ~8.5 kB gzip |
| **API style** | Render props / `useFormik` hook + `<Field>`, `<Form>`, `<ErrorMessage>` | `useForm` hook + `register`, `handleSubmit`, `Controller` |
| **Validation** | Built-in + `validationSchema` (Yup) | `resolver` pattern (Zod, Yup, Joi, Superstruct, etc.) |
| **TypeScript** | Good, but inferred types can be loose | Excellent, especially with Zod resolver |
| **Maintenance** | Less active (Formik v2 released 2019, v3 stalled) | Very active (v7 stable, frequent releases) |
| **Mount/unmount perf** | 6x slower with 1000 fields (benchmark by RHF team) | Near-instant because no state subscriptions per field |

**Migration strategy (Formik → RHF):**

```jsx
// BEFORE: Formik
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';

const validationSchema = Yup.object({
  email: Yup.string().email('Invalid').required('Required'),
  password: Yup.string().min(8).required('Required'),
});

function LoginFormik() {
  return (
    <Formik
      initialValues={{ email: '', password: '' }}
      validationSchema={validationSchema}
      onSubmit={(values, { setSubmitting }) => {
        fetch('/api/login', { method: 'POST', body: JSON.stringify(values) })
          .finally(() => setSubmitting(false));
      }}
    >
      {({ isSubmitting }) => (
        <Form>
          <Field name="email" type="email" />
          <ErrorMessage name="email" component="span" />

          <Field name="password" type="password" />
          <ErrorMessage name="password" component="span" />

          <button type="submit" disabled={isSubmitting}>Login</button>
        </Form>
      )}
    </Formik>
  );
}

// AFTER: React Hook Form + Zod
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Invalid').min(1, 'Required'),
  password: z.string().min(8, 'Min 8 characters'),
});

function LoginRHF() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data) => {
    await fetch('/api/login', { method: 'POST', body: JSON.stringify(data) });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input type="email" {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}

      <input type="password" {...register('password')} />
      {errors.password && <span>{errors.password.message}</span>}

      <button type="submit" disabled={isSubmitting}>Login</button>
    </form>
  );
}
```

**Key migration steps:**
1. Replace `Yup.object()` with `z.object()` — API is similar but stricter.
2. Replace `<Field name="x">` with `<input {...register('x')}>`.
3. Replace `<ErrorMessage name="x">` with conditional rendering on `errors.x`.
4. Replace `<Formik onSubmit>` wrapper with `useForm()` + `handleSubmit()`.
5. Replace `setFieldValue`/`setFieldError` with `setValue`/`setError` from RHF.

---

### Q9. How do you implement file upload forms with validation using React Hook Form and Zod?

**Answer:**

File uploads require special handling because file inputs are inherently uncontrolled in the browser (you cannot set their value programmatically for security reasons). With RHF, you use `register` on the file input and access the `FileList` from the form data. Validation typically includes file type (MIME), file size, and file count constraints. Zod can validate these using `z.custom()` or `z.instanceof(FileList)` with refinements.

**Production considerations:**
- Validate on the client for UX, but **always re-validate on the server**.
- Show a preview for image uploads.
- Track upload progress with `XMLHttpRequest` or `fetch` with a `ReadableStream`.
- Support drag-and-drop by combining with a drop zone component.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const profileSchema = z.object({
  displayName: z.string().min(1, 'Name is required'),
  avatar: z
    .custom()
    .refine((files) => files?.length === 1, 'Avatar is required')
    .refine(
      (files) => files?.[0]?.size <= MAX_FILE_SIZE,
      'File must be less than 5MB'
    )
    .refine(
      (files) => ACCEPTED_IMAGE_TYPES.includes(files?.[0]?.type),
      'Only .jpg, .png, and .webp formats are accepted'
    ),
  resume: z
    .custom()
    .refine((files) => files?.length <= 1, 'Only one resume allowed')
    .refine(
      (files) => !files?.[0] || files[0].size <= 10 * 1024 * 1024,
      'Resume must be less than 10MB'
    )
    .refine(
      (files) => !files?.[0] || files[0].type === 'application/pdf',
      'Only PDF format is accepted'
    )
    .optional(),
});

function ProfileUploadForm() {
  const [preview, setPreview] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(profileSchema),
  });

  const handleAvatarChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const onSubmit = async (data) => {
    const formData = new FormData();
    formData.append('displayName', data.displayName);
    formData.append('avatar', data.avatar[0]);
    if (data.resume?.[0]) formData.append('resume', data.resume[0]);

    // Upload with progress tracking using XMLHttpRequest
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          setUploadProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) resolve();
        else reject(new Error(`Upload failed: ${xhr.status}`));
      });
      xhr.addEventListener('error', () => reject(new Error('Network error')));
      xhr.open('POST', '/api/profile');
      xhr.send(formData);
    });
  };

  const { onChange: avatarOnChange, ...avatarRegister } = register('avatar');

  return (
    <form onSubmit={handleSubmit(onSubmit)} encType="multipart/form-data">
      <div>
        <label htmlFor="displayName">Display Name</label>
        <input id="displayName" {...register('displayName')} />
        {errors.displayName && <span role="alert">{errors.displayName.message}</span>}
      </div>

      <div>
        <label htmlFor="avatar">Profile Photo</label>
        {preview && <img src={preview} alt="Preview" style={{ width: 100, height: 100 }} />}
        <input
          id="avatar"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          {...avatarRegister}
          onChange={(e) => {
            avatarOnChange(e);       // let RHF track the file
            handleAvatarChange(e);   // update preview
          }}
        />
        {errors.avatar && <span role="alert">{errors.avatar.message}</span>}
      </div>

      <div>
        <label htmlFor="resume">Resume (optional)</label>
        <input id="resume" type="file" accept=".pdf" {...register('resume')} />
        {errors.resume && <span role="alert">{errors.resume.message}</span>}
      </div>

      {isSubmitting && uploadProgress > 0 && (
        <div>
          <progress value={uploadProgress} max={100} />
          <span>{uploadProgress}%</span>
        </div>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Uploading…' : 'Save Profile'}
      </button>
    </form>
  );
}
```

---

### Q10. Why is React Hook Form faster than Formik, and how do you optimise form performance in large forms?

**Answer:**

The fundamental performance difference comes down to **rendering architecture**:

**Formik's approach:** Formik stores all form values in React state (via `useReducer`). Every `setFieldValue` call triggers a state update that re-renders the entire `<Formik>` component tree. With 50 fields, typing in one field re-renders all 50. Formik offers `<FastField>` to mitigate this, but it requires explicit `shouldComponentUpdate` logic and doesn't work with all validation modes.

**RHF's approach:** RHF stores values in refs (outside React state). The only React state is `formState`, and RHF uses a Proxy to track which properties each component accesses. If your component only reads `errors.email`, it only re-renders when `errors.email` changes — not when any other field value changes. This is called **subscription-based re-rendering**.

**Benchmarks** (from the RHF documentation, 1000 fields):
- Mount time: Formik ~2000ms, RHF ~200ms
- Typing re-renders: Formik re-renders all fields, RHF re-renders 0-1 fields
- Commit memory: Formik ~50MB, RHF ~5MB

**Optimisation techniques for large forms:**

```jsx
import { useForm, useWatch, useFormContext, FormProvider } from 'react-hook-form';
import { memo } from 'react';

// Technique 1: Isolate re-renders with useWatch
// useWatch subscribes to specific fields without causing the parent to re-render
function PriceCalculator({ control }) {
  // Only this component re-renders when quantity or unitPrice change
  const [quantity, unitPrice] = useWatch({
    control,
    name: ['quantity', 'unitPrice'],
  });

  const total = (quantity || 0) * (unitPrice || 0);
  return <p>Total: ${total.toFixed(2)}</p>;
}

// Technique 2: Memoize field components
const TextField = memo(function TextField({ label, name, error, register }) {
  return (
    <div>
      <label>{label}</label>
      <input {...register(name)} />
      {error && <span role="alert">{error.message}</span>}
    </div>
  );
});

// Technique 3: Use FormProvider to avoid prop drilling
function LargeForm() {
  const methods = useForm({
    defaultValues: {
      // ... many fields
      quantity: 0,
      unitPrice: 0,
    },
  });

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(console.log)}>
        <PersonalSection />
        <AddressSection />
        <PriceCalculator control={methods.control} />
      </form>
    </FormProvider>
  );
}

// Technique 4: Child components use useFormContext — no props needed
function PersonalSection() {
  const { register, formState: { errors } } = useFormContext();

  return (
    <fieldset>
      <legend>Personal</legend>
      <TextField
        label="First Name"
        name="firstName"
        error={errors.firstName}
        register={register}
      />
      <TextField
        label="Last Name"
        name="lastName"
        error={errors.lastName}
        register={register}
      />
    </fieldset>
  );
}

// Technique 5: Debounced validation for expensive async checks
function UsernameField() {
  const { register, setError, clearErrors } = useFormContext();

  const checkUsername = async (value) => {
    if (value.length < 3) return;
    const response = await fetch(`/api/check-username?q=${value}`);
    const { available } = await response.json();
    if (!available) {
      setError('username', { type: 'manual', message: 'Username taken' });
    } else {
      clearErrors('username');
    }
  };

  return (
    <input
      {...register('username', {
        onChange: debounce((e) => checkUsername(e.target.value), 500),
      })}
    />
  );
}

function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
```

---

### Q11. How do you integrate server-side validation errors into React Hook Form after form submission?

**Answer:**

Client-side validation catches most issues, but **server-side validation is always authoritative**. The server may reject values that pass client-side checks — duplicate emails, expired tokens, business rule violations, rate limits, etc. RHF provides `setError()` to programmatically set errors on specific fields after submission, and `formState.errors` will surface them exactly like client-side validation errors.

**Production patterns:**
1. **Field-level server errors** — Map server error responses to specific field names using `setError('fieldName', { type: 'server', message })`.
2. **Global form errors** — Use `setError('root.serverError', { message })` for errors that don't map to a specific field (e.g., "Your session has expired").
3. **Error response contract** — Establish a standard API error format (e.g., `{ errors: [{ field: 'email', message: '...' }] }`) so the mapping is mechanical.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const signupSchema = z.object({
  username: z.string().min(3),
  email: z.string().email(),
  password: z.string().min(8),
});

// Simulated API error response format
// {
//   "success": false,
//   "errors": [
//     { "field": "email", "message": "Email already registered" },
//     { "field": "username", "message": "Username is taken" }
//   ]
// }

function SignupForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(signupSchema),
    defaultValues: { username: '', email: '', password: '' },
  });

  const onSubmit = async (data) => {
    try {
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        // Map server errors to RHF fields
        if (result.errors && Array.isArray(result.errors)) {
          result.errors.forEach((err) => {
            if (err.field) {
              // Field-level error
              setError(err.field, {
                type: 'server',
                message: err.message,
              });
            }
          });
        }

        // Set a root-level error for generic server issues
        if (result.message && !result.errors?.length) {
          setError('root.serverError', {
            type: 'server',
            message: result.message,
          });
        }
        return;
      }

      // Success — redirect, show toast, etc.
      window.location.href = '/dashboard';
    } catch (err) {
      setError('root.serverError', {
        type: 'server',
        message: 'Network error. Please try again.',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      {/* Root-level server error */}
      {errors.root?.serverError && (
        <div role="alert" style={{ background: '#fee', padding: 12, marginBottom: 16 }}>
          {errors.root.serverError.message}
        </div>
      )}

      <div>
        <label>Username</label>
        <input {...register('username')} />
        {errors.username && <span role="alert">{errors.username.message}</span>}
      </div>

      <div>
        <label>Email</label>
        <input type="email" {...register('email')} />
        {errors.email && <span role="alert">{errors.email.message}</span>}
      </div>

      <div>
        <label>Password</label>
        <input type="password" {...register('password')} />
        {errors.password && <span role="alert">{errors.password.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating account…' : 'Sign Up'}
      </button>
    </form>
  );
}
```

---

### Q12. How do you implement cross-field validation (e.g., password confirmation, date ranges) with Zod and React Hook Form?

**Answer:**

Cross-field validation is when the validity of one field depends on the value of another. Examples include password/confirm-password matching, start date before end date, "other" text field required when "other" is selected in a dropdown, and minimum/maximum range fields. Zod handles this with `.refine()` (single refinement) and `.superRefine()` (multiple refinements with granular error paths).

The critical detail is that Zod's `refine` runs **after** all field-level validations pass. You attach it to the **object schema** (not the individual field), and use the `path` option to direct the error to the correct field in RHF's `formState.errors`.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Example 1: Password confirmation
const passwordSchema = z
  .object({
    password: z
      .string()
      .min(8, 'Min 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[0-9]/, 'Must contain a number'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'], // Error appears on confirmPassword field
  });

// Example 2: Date range — start must be before end
const dateRangeSchema = z
  .object({
    startDate: z.coerce.date({ required_error: 'Start date required' }),
    endDate: z.coerce.date({ required_error: 'End date required' }),
  })
  .refine((data) => data.startDate < data.endDate, {
    message: 'Start date must be before end date',
    path: ['endDate'],
  });

// Example 3: Conditional required field + multiple cross-field rules with superRefine
const surveySchema = z
  .object({
    satisfaction: z.enum(['great', 'good', 'poor', 'terrible']),
    feedback: z.string().optional(),
    minBudget: z.coerce.number().min(0),
    maxBudget: z.coerce.number().min(0),
  })
  .superRefine((data, ctx) => {
    // Feedback required if satisfaction is poor or terrible
    if (['poor', 'terrible'].includes(data.satisfaction) && !data.feedback?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Please explain what went wrong',
        path: ['feedback'],
      });
    }

    // Max budget must be >= min budget
    if (data.maxBudget < data.minBudget) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Max budget must be greater than or equal to min budget',
        path: ['maxBudget'],
      });
    }
  });

function SurveyForm() {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(surveySchema),
    defaultValues: {
      satisfaction: 'great',
      feedback: '',
      minBudget: 0,
      maxBudget: 1000,
    },
  });

  const satisfaction = watch('satisfaction');

  const onSubmit = (data) => {
    console.log('Survey submitted:', data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>Satisfaction</label>
        <select {...register('satisfaction')}>
          <option value="great">Great</option>
          <option value="good">Good</option>
          <option value="poor">Poor</option>
          <option value="terrible">Terrible</option>
        </select>
      </div>

      <div>
        <label>
          Feedback {['poor', 'terrible'].includes(satisfaction) && '(required)'}
        </label>
        <textarea {...register('feedback')} rows={4} />
        {errors.feedback && <span role="alert">{errors.feedback.message}</span>}
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div>
          <label>Min Budget ($)</label>
          <input type="number" {...register('minBudget')} />
          {errors.minBudget && <span role="alert">{errors.minBudget.message}</span>}
        </div>
        <div>
          <label>Max Budget ($)</label>
          <input type="number" {...register('maxBudget')} />
          {errors.maxBudget && <span role="alert">{errors.maxBudget.message}</span>}
        </div>
      </div>

      <button type="submit">Submit Survey</button>
    </form>
  );
}
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement form state persistence — draft saving to localStorage and restoring on page reload?

**Answer:**

Form persistence is critical for long forms (applications, surveys, onboarding flows) where losing progress frustrates users. The strategy involves: saving form values to `localStorage` (or `sessionStorage`, IndexedDB) on every change, restoring saved values as `defaultValues` on mount, and clearing saved data on successful submission.

**Key considerations:**
1. **Debounce saves** — Don't write to localStorage on every keystroke. Debounce by 500ms–1s.
2. **Schema versioning** — If the form schema changes between deploys, stale localStorage data may not match. Store a schema version and discard stale data.
3. **Sensitive data** — Never persist passwords, credit card numbers, or tokens. Encrypt or exclude sensitive fields.
4. **File inputs** — `File` objects cannot be serialized to JSON. Store file metadata (name, size) for display, but the user must re-upload.
5. **`useWatch` vs `watch`** — `useWatch` is more performant for persistence because it subscribes only to the fields you specify.

```jsx
import { useEffect, useCallback, useRef } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const STORAGE_KEY = 'application-form-draft';
const SCHEMA_VERSION = 2; // Increment when schema changes

const applicationSchema = z.object({
  fullName: z.string().min(1, 'Required'),
  email: z.string().email(),
  coverLetter: z.string().min(50, 'At least 50 characters'),
  yearsOfExperience: z.coerce.number().min(0).max(50),
  skills: z.string().min(1, 'List at least one skill'),
});

const defaultFormValues = {
  fullName: '',
  email: '',
  coverLetter: '',
  yearsOfExperience: 0,
  skills: '',
};

// Helper: load draft from localStorage with version check
function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed._schemaVersion !== SCHEMA_VERSION) {
      localStorage.removeItem(STORAGE_KEY);
      return null; // Schema changed, discard stale draft
    }
    const { _schemaVersion, _savedAt, ...values } = parsed;
    return { values, savedAt: _savedAt };
  } catch {
    return null;
  }
}

// Helper: save draft to localStorage
function saveDraft(values) {
  const data = {
    ...values,
    _schemaVersion: SCHEMA_VERSION,
    _savedAt: new Date().toISOString(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function clearDraft() {
  localStorage.removeItem(STORAGE_KEY);
}

// Custom hook for form persistence
function useFormPersistence(control, options = {}) {
  const { debounceMs = 1000, exclude = [] } = options;
  const timerRef = useRef(null);

  // Watch all field values
  const watchedValues = useWatch({ control });

  useEffect(() => {
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      // Exclude sensitive fields before saving
      const toSave = { ...watchedValues };
      exclude.forEach((key) => delete toSave[key]);
      saveDraft(toSave);
    }, debounceMs);

    return () => clearTimeout(timerRef.current);
  }, [watchedValues, debounceMs, exclude]);
}

function ApplicationForm() {
  const draft = loadDraft();

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm({
    resolver: zodResolver(applicationSchema),
    defaultValues: draft?.values ?? defaultFormValues,
  });

  // Auto-save to localStorage (debounced)
  useFormPersistence(control, {
    debounceMs: 1000,
    exclude: [], // e.g., exclude: ['password', 'ssn']
  });

  const onSubmit = async (data) => {
    await fetch('/api/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    clearDraft(); // Clear saved draft on successful submission
    alert('Application submitted!');
  };

  const handleDiscard = () => {
    clearDraft();
    reset(defaultFormValues);
  };

  return (
    <div>
      {draft?.savedAt && (
        <div style={{ background: '#ffe', padding: 8, marginBottom: 16 }}>
          Draft restored from {new Date(draft.savedAt).toLocaleString()}
          <button type="button" onClick={handleDiscard} style={{ marginLeft: 12 }}>
            Discard Draft
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label>Full Name</label>
          <input {...register('fullName')} />
          {errors.fullName && <span role="alert">{errors.fullName.message}</span>}
        </div>

        <div>
          <label>Email</label>
          <input type="email" {...register('email')} />
          {errors.email && <span role="alert">{errors.email.message}</span>}
        </div>

        <div>
          <label>Cover Letter</label>
          <textarea {...register('coverLetter')} rows={8} />
          {errors.coverLetter && <span role="alert">{errors.coverLetter.message}</span>}
        </div>

        <div>
          <label>Years of Experience</label>
          <input type="number" {...register('yearsOfExperience')} />
          {errors.yearsOfExperience && (
            <span role="alert">{errors.yearsOfExperience.message}</span>
          )}
        </div>

        <div>
          <label>Skills (comma-separated)</label>
          <input {...register('skills')} />
          {errors.skills && <span role="alert">{errors.skills.message}</span>}
        </div>

        <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting…' : 'Submit Application'}
          </button>
          <button type="button" onClick={handleDiscard} disabled={!isDirty}>
            Discard Draft
          </button>
        </div>
      </form>
    </div>
  );
}
```

---

### Q14. How do you model complex nested form schemas with Zod — nested objects, arrays of objects, discriminated unions, and recursive types?

**Answer:**

Production forms often have deeply nested structures: shipping addresses within orders, multiple phone numbers with types, conditional sections based on a discriminant (e.g., "individual" vs. "business" account), and even recursive structures (comments with replies). Zod's composability makes it the ideal tool for modelling these.

**Key Zod features for complex schemas:**
- `z.object().merge()` / `.extend()` — compose schemas
- `z.array(z.object(...))` — arrays of objects
- `z.discriminatedUnion('type', [...])` — type-safe unions (much faster than plain `z.union()`)
- `z.lazy(() => schema)` — recursive schemas
- `.transform()` — reshape data during parsing
- `.pipe()` — chain schemas (e.g., string → coerce to number → validate range)

```jsx
import { z } from 'zod';

// 1. Nested objects
const addressSchema = z.object({
  street: z.string().min(1),
  city: z.string().min(1),
  state: z.string().length(2),
  zip: z.string().regex(/^\d{5}$/),
  country: z.string().default('US'),
});

const orderSchema = z.object({
  orderId: z.string().uuid(),
  shippingAddress: addressSchema,
  billingAddress: addressSchema.optional(), // Reuse!
  useSameAddress: z.boolean(),
}).refine(
  (data) => data.useSameAddress || data.billingAddress !== undefined,
  { message: 'Billing address is required when different from shipping', path: ['billingAddress'] }
);

// 2. Arrays of objects with constraints
const teamSchema = z.object({
  teamName: z.string().min(1),
  members: z
    .array(
      z.object({
        name: z.string().min(1),
        email: z.string().email(),
        role: z.enum(['lead', 'developer', 'designer', 'qa']),
      })
    )
    .min(1, 'At least one member required')
    .max(20, 'Maximum 20 members')
    .refine(
      (members) => members.filter((m) => m.role === 'lead').length === 1,
      'Exactly one team lead is required'
    ),
});

// 3. Discriminated union — different shapes based on a 'type' field
const paymentSchema = z.discriminatedUnion('method', [
  z.object({
    method: z.literal('credit_card'),
    cardNumber: z.string().regex(/^\d{16}$/),
    expiry: z.string(),
    cvv: z.string().regex(/^\d{3,4}$/),
  }),
  z.object({
    method: z.literal('bank_transfer'),
    bankName: z.string().min(1),
    accountNumber: z.string().min(8),
    routingNumber: z.string().length(9),
  }),
  z.object({
    method: z.literal('paypal'),
    paypalEmail: z.string().email(),
  }),
]);

// 4. Recursive schema (e.g., category tree or threaded comments)
const categorySchema = z.object({
  name: z.string().min(1),
  children: z.lazy(() => z.array(categorySchema)).default([]),
});

// Validates: { name: 'Electronics', children: [{ name: 'Phones', children: [{ name: 'iPhones', children: [] }] }] }

// 5. Transform + pipe for complex coercion
const csvToArraySchema = z
  .string()
  .transform((val) => val.split(',').map((s) => s.trim()).filter(Boolean))
  .pipe(z.array(z.string().email('Each entry must be a valid email')));

// Parses: "alice@x.com, bob@y.com" → ["alice@x.com", "bob@y.com"]

// 6. Using discriminated union in a form
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

const checkoutSchema = z.object({
  name: z.string().min(1),
  payment: paymentSchema,
});

function CheckoutForm() {
  const { register, handleSubmit, control, formState: { errors } } = useForm({
    resolver: zodResolver(checkoutSchema),
    defaultValues: {
      name: '',
      payment: { method: 'credit_card', cardNumber: '', expiry: '', cvv: '' },
    },
  });

  const paymentMethod = useWatch({ control, name: 'payment.method' });

  return (
    <form onSubmit={handleSubmit(console.log)}>
      <input {...register('name')} placeholder="Name" />

      <select {...register('payment.method')}>
        <option value="credit_card">Credit Card</option>
        <option value="bank_transfer">Bank Transfer</option>
        <option value="paypal">PayPal</option>
      </select>

      {paymentMethod === 'credit_card' && (
        <div>
          <input {...register('payment.cardNumber')} placeholder="Card number" />
          {errors.payment?.cardNumber && <span>{errors.payment.cardNumber.message}</span>}
          <input {...register('payment.expiry')} placeholder="MM/YY" />
          <input {...register('payment.cvv')} placeholder="CVV" />
        </div>
      )}

      {paymentMethod === 'bank_transfer' && (
        <div>
          <input {...register('payment.bankName')} placeholder="Bank name" />
          <input {...register('payment.accountNumber')} placeholder="Account #" />
          <input {...register('payment.routingNumber')} placeholder="Routing #" />
        </div>
      )}

      {paymentMethod === 'paypal' && (
        <div>
          <input {...register('payment.paypalEmail')} placeholder="PayPal email" />
          {errors.payment?.paypalEmail && <span>{errors.payment.paypalEmail.message}</span>}
        </div>
      )}

      <button type="submit">Pay</button>
    </form>
  );
}
```

---

### Q15. How do you build custom form components with `Controller` and `useController` in React Hook Form?

**Answer:**

`register` works beautifully with native HTML inputs because it attaches a `ref` directly to the DOM element. But many production forms use third-party UI components (Material UI `<TextField>`, React Select `<Select>`, date pickers, rich text editors) that don't expose a raw `ref` to an underlying `<input>`. This is where **`Controller`** (render-prop component) and **`useController`** (hook) come in — they bridge RHF's internal state with any component that has a `value` + `onChange` interface.

**When to use `Controller` / `useController`:**
- Third-party UI library components (MUI, Ant Design, Chakra UI)
- Custom components that manage their own internal state (date pickers, sliders, rich text)
- Components that accept `value`/`onChange` but don't expose a `ref` to a native input

**`Controller` vs `useController`:**
- `Controller` is a wrapper component with a `render` prop — good for one-off usage.
- `useController` is a hook — better for building reusable, encapsulated form-connected components.

```jsx
import { useForm, Controller, useController } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  priority: z.number().min(1).max(5),
  tags: z.array(z.string()).min(1, 'Select at least one tag'),
  dueDate: z.coerce.date({ required_error: 'Due date required' }),
  description: z.string().min(10, 'At least 10 characters'),
});

// ---- Approach 1: Controller render prop ----
// Good for inline / one-off usage

function TaskFormWithController() {
  const { control, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      title: '',
      priority: 3,
      tags: [],
      dueDate: null,
      description: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(console.log)}>
      {/* Native input — use register normally */}
      <Controller
        name="title"
        control={control}
        render={({ field }) => (
          <input {...field} placeholder="Task title" />
        )}
      />
      {errors.title && <span>{errors.title.message}</span>}

      {/* Custom slider component */}
      <Controller
        name="priority"
        control={control}
        render={({ field: { value, onChange } }) => (
          <div>
            <label>Priority: {value}</label>
            <input
              type="range"
              min={1}
              max={5}
              value={value}
              onChange={(e) => onChange(Number(e.target.value))}
            />
          </div>
        )}
      />

      {/* Multi-select tags (simulated) */}
      <Controller
        name="tags"
        control={control}
        render={({ field: { value, onChange } }) => {
          const allTags = ['bug', 'feature', 'docs', 'refactor', 'test'];
          const toggle = (tag) => {
            onChange(
              value.includes(tag)
                ? value.filter((t) => t !== tag)
                : [...value, tag]
            );
          };
          return (
            <div>
              {allTags.map((tag) => (
                <label key={tag} style={{ marginRight: 8 }}>
                  <input
                    type="checkbox"
                    checked={value.includes(tag)}
                    onChange={() => toggle(tag)}
                  />
                  {tag}
                </label>
              ))}
            </div>
          );
        }}
      />
      {errors.tags && <span>{errors.tags.message}</span>}

      <button type="submit">Create Task</button>
    </form>
  );
}

// ---- Approach 2: useController hook ----
// Better for reusable components

function RichTextArea({ name, control, rules, label, ...props }) {
  const {
    field: { value, onChange, onBlur, ref },
    fieldState: { error, isDirty },
  } = useController({ name, control, rules });

  return (
    <div>
      <label>{label} {isDirty && '(modified)'}</label>
      <textarea
        ref={ref}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        rows={6}
        style={{
          borderColor: error ? 'red' : '#ccc',
          width: '100%',
        }}
        {...props}
      />
      {error && <span role="alert" style={{ color: 'red' }}>{error.message}</span>}
    </div>
  );
}

function NumberStepper({ name, control, label, min = 0, max = 100 }) {
  const {
    field: { value, onChange },
    fieldState: { error },
  } = useController({ name, control });

  return (
    <div>
      <label>{label}</label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button type="button" onClick={() => onChange(Math.max(min, value - 1))}>-</button>
        <span>{value}</span>
        <button type="button" onClick={() => onChange(Math.min(max, value + 1))}>+</button>
      </div>
      {error && <span role="alert">{error.message}</span>}
    </div>
  );
}

// Usage of reusable components
function TaskFormWithHook() {
  const { control, handleSubmit } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { title: '', priority: 3, tags: [], dueDate: null, description: '' },
  });

  return (
    <form onSubmit={handleSubmit(console.log)}>
      <NumberStepper name="priority" control={control} label="Priority" min={1} max={5} />
      <RichTextArea name="description" control={control} label="Description" />
      <button type="submit">Create</button>
    </form>
  );
}
```

---

### Q16. How do you make React forms accessible, including ARIA attributes, focus management, and error announcements for screen readers?

**Answer:**

Accessible forms are not optional — they are a legal requirement (WCAG 2.1 AA) and a moral imperative. Key accessibility patterns include:

1. **Labels** — Every input must have an associated `<label>` via `htmlFor`/`id` pairing. Placeholder text is NOT a substitute.
2. **Error identification** — `aria-invalid="true"` on invalid fields, `aria-describedby` linking to the error message element.
3. **Error announcements** — Use `role="alert"` or `aria-live="assertive"` on error containers so screen readers announce errors without requiring the user to navigate.
4. **Focus management** — On validation failure, move focus to the first invalid field or to the error summary.
5. **Fieldsets and legends** — Group related fields with `<fieldset>` and `<legend>`.
6. **Required indicators** — Use `aria-required="true"` and a visible indicator (asterisk with screen reader text).
7. **Submit feedback** — Announce submission success or failure.

```jsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useEffect, useRef, useId } from 'react';

const schema = z.object({
  name: z.string().min(1, 'Full name is required'),
  email: z.string().email('Please enter a valid email address'),
  phone: z.string().regex(/^\+?[\d\s-]{10,}$/, 'Please enter a valid phone number'),
  message: z.string().min(20, 'Message must be at least 20 characters'),
});

// Accessible form field component
function FormField({ label, name, type = 'text', required, register, error, ...props }) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const descId = `${fieldId}-desc`;

  return (
    <div style={{ marginBottom: 16 }}>
      <label htmlFor={fieldId}>
        {label}
        {required && (
          <>
            <span aria-hidden="true" style={{ color: 'red' }}> *</span>
            <span className="sr-only"> (required)</span>
          </>
        )}
      </label>

      {type === 'textarea' ? (
        <textarea
          id={fieldId}
          {...register(name)}
          aria-invalid={!!error}
          aria-required={required}
          aria-describedby={error ? errorId : props.description ? descId : undefined}
          rows={5}
          {...props}
        />
      ) : (
        <input
          id={fieldId}
          type={type}
          {...register(name)}
          aria-invalid={!!error}
          aria-required={required}
          aria-describedby={error ? errorId : props.description ? descId : undefined}
          {...props}
        />
      )}

      {props.description && !error && (
        <p id={descId} style={{ fontSize: '0.85rem', color: '#666' }}>
          {props.description}
        </p>
      )}

      {error && (
        <p id={errorId} role="alert" style={{ color: 'red', fontSize: '0.85rem' }}>
          {error.message}
        </p>
      )}
    </div>
  );
}

function AccessibleContactForm() {
  const errorSummaryRef = useRef(null);
  const {
    register,
    handleSubmit,
    setFocus,
    formState: { errors, isSubmitSuccessful, submitCount },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { name: '', email: '', phone: '', message: '' },
  });

  const errorEntries = Object.entries(errors);

  // Focus management: move focus to error summary or first error field on submit failure
  useEffect(() => {
    if (submitCount > 0 && errorEntries.length > 0) {
      // Strategy 1: Focus the error summary
      errorSummaryRef.current?.focus();

      // Strategy 2 (alternative): Focus the first invalid field
      // const firstErrorField = errorEntries[0][0];
      // setFocus(firstErrorField);
    }
  }, [submitCount, errorEntries.length, setFocus]);

  const onSubmit = async (data) => {
    await fetch('/api/contact', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  };

  return (
    <div>
      <h1 id="form-heading">Contact Us</h1>

      {/* Success announcement */}
      {isSubmitSuccessful && (
        <div role="status" aria-live="polite" style={{ background: '#efe', padding: 16 }}>
          Thank you! Your message has been sent successfully.
        </div>
      )}

      {/* Error summary — screen reader announces this immediately */}
      {errorEntries.length > 0 && (
        <div
          ref={errorSummaryRef}
          role="alert"
          tabIndex={-1}
          aria-labelledby="error-summary-heading"
          style={{ border: '2px solid red', padding: 16, marginBottom: 16 }}
        >
          <h2 id="error-summary-heading">
            There {errorEntries.length === 1 ? 'is 1 error' : `are ${errorEntries.length} errors`} in
            the form
          </h2>
          <ul>
            {errorEntries.map(([field, err]) => (
              <li key={field}>
                {/* Link to the field for keyboard navigation */}
                <a
                  href={`#${field}`}
                  onClick={(e) => {
                    e.preventDefault();
                    setFocus(field);
                  }}
                >
                  {err.message}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      <form
        onSubmit={handleSubmit(onSubmit)}
        aria-labelledby="form-heading"
        noValidate
      >
        <fieldset>
          <legend>Your Details</legend>

          <FormField
            label="Full Name"
            name="name"
            required
            register={register}
            error={errors.name}
          />

          <FormField
            label="Email Address"
            name="email"
            type="email"
            required
            register={register}
            error={errors.email}
            description="We will never share your email"
          />

          <FormField
            label="Phone Number"
            name="phone"
            type="tel"
            required
            register={register}
            error={errors.phone}
            description="Include country code, e.g., +1 555-123-4567"
          />
        </fieldset>

        <fieldset>
          <legend>Your Message</legend>

          <FormField
            label="Message"
            name="message"
            type="textarea"
            required
            register={register}
            error={errors.message}
          />
        </fieldset>

        <button type="submit">Send Message</button>
      </form>

      {/* Visually hidden but available to screen readers */}
      <style>{`
        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }
      `}</style>
    </div>
  );
}
```

---

### Q17. How do React 19's built-in form Actions compare to React Hook Form, and what are the trade-offs?

**Answer:**

React 19 introduces **Server Actions** and the `useActionState` hook (formerly `useFormState`), allowing forms to submit directly to server functions without client-side JavaScript for the submission logic. The `<form action={serverAction}>` pattern integrates with React's Suspense and transition model, enabling progressive enhancement — the form works even before JavaScript hydrates.

**React 19 form primitives:**
- `<form action={fn}>` — The `action` prop accepts an async function. React handles `pending` state automatically.
- `useActionState(action, initialState)` — Returns `[state, formAction, isPending]`, providing server response state.
- `useFormStatus()` — Access `pending`, `data`, `method`, `action` from a parent `<form>` (must be a child component).
- `useOptimistic(state, updateFn)` — Optimistically update UI while the action is in flight.

**Comparison:**

| Feature | React 19 Actions | React Hook Form |
|---------|-----------------|-----------------|
| **Server-first** | Yes — form submits to server function | No — client-side by default |
| **Progressive enhancement** | Works without JS | Requires JS |
| **Client-side validation** | Not built-in (bring your own) | Full validation pipeline |
| **Re-render perf** | N/A (server-rendered) | Optimised via refs/proxy |
| **Complex client forms** | Limited — no field arrays, no cross-field validation | Full featured |
| **Type safety** | Good with Zod on server | Excellent with zodResolver |
| **File uploads** | Native `FormData` support | Manual `FormData` construction |

**Verdict:** React 19 Actions are ideal for **simple forms** (search, login, contact) in **server-rendered apps** (Next.js App Router). For **complex client-side forms** (wizards, dynamic fields, real-time validation), RHF is still the better choice. In practice, many apps use **both**: RHF for complex client forms, and Server Actions for simple submission flows.

```jsx
// ---- React 19 Server Action approach ----
// (This runs in a Next.js App Router server component setup)

// app/actions.js — Server Action
// 'use server';
//
// import { z } from 'zod';
//
// const feedbackSchema = z.object({
//   name: z.string().min(1, 'Name required'),
//   rating: z.coerce.number().min(1).max(5),
//   comment: z.string().min(10, 'At least 10 characters'),
// });
//
// export async function submitFeedback(prevState, formData) {
//   const raw = {
//     name: formData.get('name'),
//     rating: formData.get('rating'),
//     comment: formData.get('comment'),
//   };
//
//   const result = feedbackSchema.safeParse(raw);
//
//   if (!result.success) {
//     return {
//       success: false,
//       errors: result.error.flatten().fieldErrors,
//     };
//   }
//
//   await db.feedback.create({ data: result.data });
//   return { success: true, errors: {} };
// }

// app/feedback/page.jsx — Client Component
// 'use client';

import { useActionState } from 'react';
import { useFormStatus } from 'react-dom';
// import { submitFeedback } from '../actions';

// Simulated for demonstration
const submitFeedback = async (prevState, formData) => {
  return { success: true, errors: {} };
};

function SubmitButton() {
  const { pending } = useFormStatus(); // Must be child of <form>
  return (
    <button type="submit" disabled={pending}>
      {pending ? 'Submitting…' : 'Submit Feedback'}
    </button>
  );
}

function FeedbackForm() {
  const [state, formAction, isPending] = useActionState(submitFeedback, {
    success: false,
    errors: {},
  });

  return (
    <div>
      {state.success && (
        <div role="status" style={{ color: 'green' }}>
          Thank you for your feedback!
        </div>
      )}

      <form action={formAction}>
        <div>
          <label htmlFor="name">Name</label>
          <input id="name" name="name" />
          {state.errors?.name && <span role="alert">{state.errors.name[0]}</span>}
        </div>

        <div>
          <label htmlFor="rating">Rating (1–5)</label>
          <input id="rating" name="rating" type="number" min={1} max={5} />
          {state.errors?.rating && <span role="alert">{state.errors.rating[0]}</span>}
        </div>

        <div>
          <label htmlFor="comment">Comment</label>
          <textarea id="comment" name="comment" rows={4} />
          {state.errors?.comment && <span role="alert">{state.errors.comment[0]}</span>}
        </div>

        <SubmitButton />
      </form>
    </div>
  );
}

// ---- Hybrid: RHF for client validation + Server Action for submission ----
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const feedbackSchema = z.object({
  name: z.string().min(1, 'Name required'),
  rating: z.coerce.number().min(1).max(5),
  comment: z.string().min(10, 'At least 10 characters'),
});

function HybridFeedbackForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(feedbackSchema),
  });

  const onSubmit = async (data) => {
    // Client-side validation already passed via RHF + Zod
    // Now submit to server action or API
    const formData = new FormData();
    Object.entries(data).forEach(([key, val]) => formData.append(key, String(val)));
    await submitFeedback(null, formData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} placeholder="Name" />
      {errors.name && <span>{errors.name.message}</span>}

      <input type="number" {...register('rating')} min={1} max={5} />
      {errors.rating && <span>{errors.rating.message}</span>}

      <textarea {...register('comment')} rows={4} />
      {errors.comment && <span>{errors.comment.message}</span>}

      <button type="submit" disabled={isSubmitting}>Submit</button>
    </form>
  );
}
```

---

### Q18. How do you comprehensively test React forms — unit testing validation schemas, integration testing form interactions, and end-to-end submission flows?

**Answer:**

Form testing should cover three layers:

1. **Schema unit tests** — Test your Zod schemas in isolation with `schema.safeParse()`. No React rendering needed. These are the fastest and most reliable tests.
2. **Component integration tests** — Use React Testing Library to render the form, fill in fields, submit, and assert on errors, success states, and API calls. Mock the network layer.
3. **E2E tests** — Use Playwright or Cypress to test the full flow including server responses, redirects, and persistence.

**Testing principles:**
- Test behaviour, not implementation. Don't assert on RHF internals.
- Use `userEvent` (not `fireEvent`) for realistic user interactions.
- Always use `waitFor` for async validation and submission.
- Test error display, focus management, and form reset.

```jsx
// ---- schemas/contactSchema.js ----
import { z } from 'zod';

export const contactSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
  message: z.string().min(10, 'At least 10 characters'),
});

// ---- schemas/__tests__/contactSchema.test.js ----
// Layer 1: Schema unit tests — fast, no React needed
import { contactSchema } from '../contactSchema';

describe('contactSchema', () => {
  it('accepts valid data', () => {
    const result = contactSchema.safeParse({
      name: 'Alice',
      email: 'alice@example.com',
      message: 'This is a long enough message',
    });
    expect(result.success).toBe(true);
  });

  it('rejects empty name', () => {
    const result = contactSchema.safeParse({
      name: '',
      email: 'alice@example.com',
      message: 'This is valid',
    });
    expect(result.success).toBe(false);
    expect(result.error.flatten().fieldErrors.name).toContain('Name is required');
  });

  it('rejects invalid email', () => {
    const result = contactSchema.safeParse({
      name: 'Alice',
      email: 'not-an-email',
      message: 'This is valid message',
    });
    expect(result.success).toBe(false);
    expect(result.error.flatten().fieldErrors.email).toContain('Invalid email');
  });

  it('rejects short message', () => {
    const result = contactSchema.safeParse({
      name: 'Alice',
      email: 'alice@example.com',
      message: 'Short',
    });
    expect(result.success).toBe(false);
    expect(result.error.flatten().fieldErrors.message).toContain('At least 10 characters');
  });

  // Test cross-field validation (password example)
  // const pwSchema = z.object({
  //   password: z.string().min(8),
  //   confirm: z.string(),
  // }).refine(d => d.password === d.confirm, { path: ['confirm'], message: 'No match' });
  //
  // it('rejects mismatched passwords', () => {
  //   const result = pwSchema.safeParse({ password: '12345678', confirm: 'different' });
  //   expect(result.error.flatten().fieldErrors.confirm).toContain('No match');
  // });
});

// ---- components/__tests__/ContactForm.test.jsx ----
// Layer 2: Component integration tests with React Testing Library
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
// import { ContactForm } from '../ContactForm';

// Mock fetch
beforeEach(() => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ success: true }),
  });
});

// Example test structure (component would need to exist)
describe('ContactForm integration', () => {
  it('shows validation errors when submitting empty form', async () => {
    const user = userEvent.setup();
    // render(<ContactForm />);

    // Click submit without filling anything
    // await user.click(screen.getByRole('button', { name: /send/i }));

    // Assert errors are shown
    // await waitFor(() => {
    //   expect(screen.getByText('Name is required')).toBeInTheDocument();
    //   expect(screen.getByText('Invalid email')).toBeInTheDocument();
    //   expect(screen.getByText('At least 10 characters')).toBeInTheDocument();
    // });

    // Assert fetch was NOT called
    // expect(fetch).not.toHaveBeenCalled();
  });

  it('submits valid form data and clears the form', async () => {
    const user = userEvent.setup();
    // render(<ContactForm />);

    // Fill in valid data
    // await user.type(screen.getByLabelText(/name/i), 'Alice');
    // await user.type(screen.getByLabelText(/email/i), 'alice@example.com');
    // await user.type(screen.getByLabelText(/message/i), 'This is a valid message that is long enough');

    // Submit
    // await user.click(screen.getByRole('button', { name: /send/i }));

    // Assert fetch was called with correct data
    // await waitFor(() => {
    //   expect(fetch).toHaveBeenCalledWith('/api/contact', expect.objectContaining({
    //     method: 'POST',
    //     body: JSON.stringify({
    //       name: 'Alice',
    //       email: 'alice@example.com',
    //       message: 'This is a valid message that is long enough',
    //     }),
    //   }));
    // });
  });

  it('shows server-side errors returned from API', async () => {
    // global.fetch = jest.fn().mockResolvedValue({
    //   ok: false,
    //   json: async () => ({
    //     errors: [{ field: 'email', message: 'Email already registered' }],
    //   }),
    // });

    // const user = userEvent.setup();
    // render(<ContactForm />);

    // // Fill and submit
    // await user.type(screen.getByLabelText(/name/i), 'Alice');
    // await user.type(screen.getByLabelText(/email/i), 'taken@example.com');
    // await user.type(screen.getByLabelText(/message/i), 'Valid message for testing');
    // await user.click(screen.getByRole('button', { name: /send/i }));

    // // Assert server error is displayed
    // await waitFor(() => {
    //   expect(screen.getByText('Email already registered')).toBeInTheDocument();
    // });
  });

  it('has correct aria attributes on invalid fields', async () => {
    // const user = userEvent.setup();
    // render(<ContactForm />);

    // // Submit empty form
    // await user.click(screen.getByRole('button', { name: /send/i }));

    // await waitFor(() => {
    //   const emailInput = screen.getByLabelText(/email/i);
    //   expect(emailInput).toHaveAttribute('aria-invalid', 'true');
    //   expect(emailInput).toHaveAttribute('aria-describedby');
    //
    //   // Verify the error element has role="alert"
    //   const alerts = screen.getAllByRole('alert');
    //   expect(alerts.length).toBeGreaterThan(0);
    // });
  });
});
```

---

### Q19. How do you implement form analytics and tracking — measuring completion rates, field abandonment, time-to-fill, and error frequency?

**Answer:**

Form analytics reveal critical UX insights: which fields cause the most errors, where users abandon the form, how long each field takes to fill, and what the overall completion funnel looks like. This data drives design decisions — should you split a form into steps? Should you remove a field? Is a validation rule too strict?

**Metrics to track:**
1. **Form start** — User focused on the first field.
2. **Field interaction** — Focus, blur, time spent, error count per field.
3. **Field abandonment** — User focused a field but never completed it before leaving.
4. **Validation errors** — Which fields produce the most errors, which error messages appear most.
5. **Form submission** — Success vs. failure, time from first interaction to submission.
6. **Step completion** (multi-step) — Drop-off rate per step.

**Implementation strategy:** Create a custom hook that subscribes to RHF events and emits analytics events to your tracking system (Mixpanel, Amplitude, Segment, PostHog, or a custom backend).

```jsx
import { useEffect, useRef, useCallback } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Analytics service abstraction
const analytics = {
  track(event, properties) {
    // Replace with your analytics provider
    // mixpanel.track(event, properties);
    // posthog.capture(event, properties);
    console.log(`[Analytics] ${event}`, properties);
  },
};

// Custom hook for form analytics
function useFormAnalytics(formName, { control, formState }) {
  const startTimeRef = useRef(null);
  const fieldTimersRef = useRef({});
  const fieldErrorCountRef = useRef({});
  const hasTrackedStartRef = useRef(false);

  // Track form start (first interaction)
  const handleFormStart = useCallback(() => {
    if (!hasTrackedStartRef.current) {
      hasTrackedStartRef.current = true;
      startTimeRef.current = Date.now();
      analytics.track('form_started', { form: formName });
    }
  }, [formName]);

  // Track individual field focus
  const trackFieldFocus = useCallback(
    (fieldName) => {
      handleFormStart();
      fieldTimersRef.current[fieldName] = Date.now();
      analytics.track('field_focused', { form: formName, field: fieldName });
    },
    [formName, handleFormStart]
  );

  // Track field blur (time spent + whether it has a value)
  const trackFieldBlur = useCallback(
    (fieldName, hasValue) => {
      const focusedAt = fieldTimersRef.current[fieldName];
      const timeSpentMs = focusedAt ? Date.now() - focusedAt : 0;

      analytics.track('field_blurred', {
        form: formName,
        field: fieldName,
        timeSpentMs,
        hasValue,
      });
    },
    [formName]
  );

  // Track validation errors whenever they change
  useEffect(() => {
    const errorFields = Object.keys(formState.errors);
    if (errorFields.length > 0) {
      errorFields.forEach((field) => {
        fieldErrorCountRef.current[field] =
          (fieldErrorCountRef.current[field] || 0) + 1;
      });

      analytics.track('form_validation_errors', {
        form: formName,
        errorFields,
        errorMessages: errorFields.map(
          (f) => formState.errors[f]?.message
        ),
        submitCount: formState.submitCount,
      });
    }
  }, [formState.errors, formState.submitCount, formName]);

  // Track successful submission
  const trackSubmission = useCallback(
    (success, data) => {
      const totalTimeMs = startTimeRef.current
        ? Date.now() - startTimeRef.current
        : 0;

      analytics.track(success ? 'form_submitted' : 'form_submission_failed', {
        form: formName,
        totalTimeMs,
        totalTimeSeconds: Math.round(totalTimeMs / 1000),
        fieldErrorCounts: { ...fieldErrorCountRef.current },
        submitAttempts: formState.submitCount,
      });
    },
    [formName, formState.submitCount]
  );

  // Track abandonment on unmount
  useEffect(() => {
    return () => {
      if (hasTrackedStartRef.current && !formState.isSubmitSuccessful) {
        const totalTimeMs = startTimeRef.current
          ? Date.now() - startTimeRef.current
          : 0;

        analytics.track('form_abandoned', {
          form: formName,
          totalTimeMs,
          lastStepCompleted: formState.submitCount,
          dirtyFields: Object.keys(formState.dirtyFields),
        });
      }
    };
  }, []); // intentionally empty — runs only on unmount

  return { trackFieldFocus, trackFieldBlur, trackSubmission };
}

// Usage in a form
const checkoutSchema = z.object({
  email: z.string().email(),
  cardNumber: z.string().regex(/^\d{16}$/),
  expiry: z.string(),
});

function TrackedCheckoutForm() {
  const {
    register,
    handleSubmit,
    control,
    formState,
  } = useForm({
    resolver: zodResolver(checkoutSchema),
    defaultValues: { email: '', cardNumber: '', expiry: '' },
  });

  const { trackFieldFocus, trackFieldBlur, trackSubmission } = useFormAnalytics(
    'checkout',
    { control, formState }
  );

  // Wrap register to inject analytics tracking
  const trackedRegister = (name, options) => {
    const registration = register(name, options);
    return {
      ...registration,
      onFocus: (e) => {
        trackFieldFocus(name);
        registration.onFocus?.(e);
      },
      onBlur: (e) => {
        trackFieldBlur(name, !!e.target.value);
        registration.onBlur(e); // RHF's onBlur for validation
      },
    };
  };

  const onSubmit = async (data) => {
    try {
      await fetch('/api/checkout', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      trackSubmission(true, data);
    } catch {
      trackSubmission(false, data);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input type="email" {...trackedRegister('email')} placeholder="Email" />
      {formState.errors.email && <span>{formState.errors.email.message}</span>}

      <input {...trackedRegister('cardNumber')} placeholder="Card number" />
      {formState.errors.cardNumber && <span>{formState.errors.cardNumber.message}</span>}

      <input {...trackedRegister('expiry')} placeholder="MM/YY" />
      {formState.errors.expiry && <span>{formState.errors.expiry.message}</span>}

      <button type="submit">Pay</button>
    </form>
  );
}
```

---

### Q20. How do you architect a production-grade configurable form system with dynamic schemas, conditional fields, and server-side validation?

**Answer:**

A configurable form system is the end-game of form engineering — it allows product teams to define forms via configuration (JSON/database) without writing React code for each form. This is common in CRM tools, admin dashboards, onboarding flows, and survey platforms.

**Architecture components:**
1. **Form Configuration Schema** — A JSON structure that defines fields, their types, validation rules, layout, and conditional visibility.
2. **Schema Generator** — Converts the JSON config into a Zod schema at runtime.
3. **Field Renderer** — Maps field types to React components.
4. **Conditional Logic Engine** — Evaluates visibility/required conditions based on current form values.
5. **Server Validation Layer** — Re-validates using the same schema on the server.
6. **Persistence Layer** — Saves drafts, handles versioning.

```jsx
import { useMemo, useCallback } from 'react';
import { useForm, useWatch, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// ============================================================
// 1. Form Configuration Schema (typically from API/database)
// ============================================================
const formConfig = {
  id: 'employee-onboarding',
  version: 3,
  fields: [
    {
      name: 'employmentType',
      type: 'select',
      label: 'Employment Type',
      required: true,
      options: [
        { value: 'full_time', label: 'Full Time' },
        { value: 'part_time', label: 'Part Time' },
        { value: 'contractor', label: 'Contractor' },
      ],
    },
    {
      name: 'fullName',
      type: 'text',
      label: 'Full Name',
      required: true,
      validation: { minLength: 2, maxLength: 100 },
    },
    {
      name: 'email',
      type: 'email',
      label: 'Work Email',
      required: true,
    },
    {
      name: 'salary',
      type: 'number',
      label: 'Annual Salary',
      required: true,
      validation: { min: 30000, max: 500000 },
      conditions: [
        { field: 'employmentType', operator: 'in', value: ['full_time', 'part_time'] },
      ],
    },
    {
      name: 'hourlyRate',
      type: 'number',
      label: 'Hourly Rate ($)',
      required: true,
      validation: { min: 25, max: 500 },
      conditions: [
        { field: 'employmentType', operator: 'eq', value: 'contractor' },
      ],
    },
    {
      name: 'contractEndDate',
      type: 'date',
      label: 'Contract End Date',
      required: true,
      conditions: [
        { field: 'employmentType', operator: 'eq', value: 'contractor' },
      ],
    },
    {
      name: 'department',
      type: 'select',
      label: 'Department',
      required: true,
      options: [
        { value: 'engineering', label: 'Engineering' },
        { value: 'design', label: 'Design' },
        { value: 'product', label: 'Product' },
        { value: 'other', label: 'Other' },
      ],
    },
    {
      name: 'departmentOther',
      type: 'text',
      label: 'Specify Department',
      required: true,
      conditions: [
        { field: 'department', operator: 'eq', value: 'other' },
      ],
    },
    {
      name: 'startDate',
      type: 'date',
      label: 'Start Date',
      required: true,
    },
    {
      name: 'notes',
      type: 'textarea',
      label: 'Additional Notes',
      required: false,
      validation: { maxLength: 500 },
    },
  ],
};

// ============================================================
// 2. Dynamic Zod Schema Generator
// ============================================================
function buildFieldSchema(fieldConfig) {
  let schema;

  switch (fieldConfig.type) {
    case 'text':
    case 'textarea':
      schema = z.string();
      if (fieldConfig.validation?.minLength) {
        schema = schema.min(fieldConfig.validation.minLength);
      }
      if (fieldConfig.validation?.maxLength) {
        schema = schema.max(fieldConfig.validation.maxLength);
      }
      break;

    case 'email':
      schema = z.string().email(`${fieldConfig.label} must be a valid email`);
      break;

    case 'number':
      schema = z.coerce.number();
      if (fieldConfig.validation?.min !== undefined) {
        schema = schema.min(fieldConfig.validation.min);
      }
      if (fieldConfig.validation?.max !== undefined) {
        schema = schema.max(fieldConfig.validation.max);
      }
      break;

    case 'date':
      schema = z.string().min(1, `${fieldConfig.label} is required`);
      break;

    case 'select':
      if (fieldConfig.options) {
        const values = fieldConfig.options.map((o) => o.value);
        schema = z.enum(values, {
          errorMap: () => ({ message: `Please select a ${fieldConfig.label.toLowerCase()}` }),
        });
      } else {
        schema = z.string();
      }
      break;

    default:
      schema = z.string();
  }

  // Required vs optional
  if (!fieldConfig.required) {
    schema = schema.optional().or(z.literal(''));
  }

  return schema;
}

function buildFormSchema(config) {
  const shape = {};
  config.fields.forEach((field) => {
    shape[field.name] = buildFieldSchema(field);
  });

  return z.object(shape).superRefine((data, ctx) => {
    // Validate conditional required fields
    config.fields.forEach((field) => {
      if (field.conditions && field.required) {
        const isVisible = evaluateConditions(field.conditions, data);
        if (isVisible && !data[field.name]) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `${field.label} is required`,
            path: [field.name],
          });
        }
      }
    });
  });
}

// ============================================================
// 3. Condition Evaluation Engine
// ============================================================
function evaluateConditions(conditions, formValues) {
  return conditions.every((condition) => {
    const fieldValue = formValues[condition.field];
    switch (condition.operator) {
      case 'eq':
        return fieldValue === condition.value;
      case 'neq':
        return fieldValue !== condition.value;
      case 'in':
        return Array.isArray(condition.value) && condition.value.includes(fieldValue);
      case 'notIn':
        return Array.isArray(condition.value) && !condition.value.includes(fieldValue);
      case 'gt':
        return Number(fieldValue) > Number(condition.value);
      case 'lt':
        return Number(fieldValue) < Number(condition.value);
      case 'contains':
        return String(fieldValue).includes(String(condition.value));
      case 'isEmpty':
        return !fieldValue;
      case 'isNotEmpty':
        return !!fieldValue;
      default:
        return true;
    }
  });
}

// ============================================================
// 4. Field Renderer Components
// ============================================================
function DynamicField({ field, register, error }) {
  const baseProps = {
    id: field.name,
    ...register(field.name),
    'aria-invalid': !!error,
  };

  switch (field.type) {
    case 'textarea':
      return <textarea {...baseProps} rows={4} />;

    case 'select':
      return (
        <select {...baseProps}>
          <option value="">Select…</option>
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );

    case 'number':
      return (
        <input
          {...baseProps}
          type="number"
          min={field.validation?.min}
          max={field.validation?.max}
        />
      );

    case 'date':
      return <input {...baseProps} type="date" />;

    case 'email':
      return <input {...baseProps} type="email" />;

    default:
      return <input {...baseProps} type="text" />;
  }
}

// ============================================================
// 5. The Configurable Form Component
// ============================================================
function ConfigurableForm({ config, onSubmit, onSaveDraft }) {
  // Build Zod schema from config
  const schema = useMemo(() => buildFormSchema(config), [config]);

  // Build default values from config
  const defaultValues = useMemo(() => {
    const values = {};
    config.fields.forEach((field) => {
      values[field.name] = field.type === 'number' ? 0 : '';
    });
    return values;
  }, [config]);

  const {
    register,
    handleSubmit,
    control,
    setError,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues,
    mode: 'onBlur',
  });

  // Watch all values for conditional logic
  const watchedValues = useWatch({ control });

  const handleFormSubmit = async (data) => {
    // Strip invisible conditional fields
    const cleanedData = {};
    config.fields.forEach((field) => {
      const isVisible = !field.conditions || evaluateConditions(field.conditions, data);
      if (isVisible) {
        cleanedData[field.name] = data[field.name];
      }
    });

    try {
      const response = await fetch('/api/forms/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          formId: config.id,
          version: config.version,
          data: cleanedData,
        }),
      });

      const result = await response.json();

      if (!response.ok && result.fieldErrors) {
        // Map server validation errors back to form fields
        Object.entries(result.fieldErrors).forEach(([field, message]) => {
          setError(field, { type: 'server', message });
        });
        return;
      }

      onSubmit?.(result);
    } catch (err) {
      setError('root.serverError', {
        type: 'server',
        message: 'Submission failed. Please try again.',
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} noValidate>
      {errors.root?.serverError && (
        <div role="alert" style={{ background: '#fee', padding: 12, marginBottom: 16 }}>
          {errors.root.serverError.message}
        </div>
      )}

      {config.fields.map((field) => {
        // Evaluate conditional visibility
        const isVisible = !field.conditions || evaluateConditions(field.conditions, watchedValues);
        if (!isVisible) return null;

        return (
          <div key={field.name} style={{ marginBottom: 16 }}>
            <label htmlFor={field.name}>
              {field.label}
              {field.required && <span style={{ color: 'red' }}> *</span>}
            </label>

            <DynamicField
              field={field}
              register={register}
              error={errors[field.name]}
            />

            {errors[field.name] && (
              <p role="alert" style={{ color: 'red', fontSize: '0.85rem' }}>
                {errors[field.name].message}
              </p>
            )}
          </div>
        );
      })}

      <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting…' : 'Submit'}
        </button>
        <button
          type="button"
          onClick={() => onSaveDraft?.(watchedValues)}
        >
          Save Draft
        </button>
      </div>
    </form>
  );
}

// ============================================================
// 6. Usage
// ============================================================
function OnboardingPage() {
  const handleSubmit = (result) => {
    console.log('Form submitted successfully:', result);
  };

  const handleSaveDraft = (values) => {
    localStorage.setItem(
      `draft-${formConfig.id}`,
      JSON.stringify({ values, savedAt: new Date().toISOString() })
    );
  };

  return (
    <div>
      <h1>Employee Onboarding</h1>
      <ConfigurableForm
        config={formConfig}
        onSubmit={handleSubmit}
        onSaveDraft={handleSaveDraft}
      />
    </div>
  );
}

// ============================================================
// 7. Server-side validation (Node.js/Express example)
// ============================================================
// On the server, reuse the same schema generator:
//
// app.post('/api/forms/submit', async (req, res) => {
//   const { formId, version, data } = req.body;
//
//   // Load form config from database
//   const config = await db.formConfigs.findOne({ id: formId, version });
//   if (!config) return res.status(404).json({ error: 'Form not found' });
//
//   // Build schema from config (same function as client!)
//   const schema = buildFormSchema(config);
//   const result = schema.safeParse(data);
//
//   if (!result.success) {
//     const fieldErrors = {};
//     result.error.issues.forEach((issue) => {
//       const path = issue.path.join('.');
//       fieldErrors[path] = issue.message;
//     });
//     return res.status(400).json({ success: false, fieldErrors });
//   }
//
//   // Additional server-only validation (e.g., check email uniqueness)
//   const existingUser = await db.users.findByEmail(result.data.email);
//   if (existingUser) {
//     return res.status(400).json({
//       success: false,
//       fieldErrors: { email: 'This email is already registered' },
//     });
//   }
//
//   // Save to database
//   await db.submissions.create({
//     formId, version,
//     data: result.data,
//     submittedAt: new Date(),
//   });
//
//   return res.json({ success: true });
// });
```

**Key architectural decisions in this system:**

1. **Schema sharing** — The `buildFormSchema` function works identically on client and server, ensuring validation parity.
2. **Conditional field stripping** — Invisible fields are stripped before submission so users aren't blocked by hidden required fields.
3. **Version tracking** — The `version` field ensures the server validates against the same schema the client rendered.
4. **Server-only validation** — Uniqueness checks, rate limiting, and business rules that cannot run on the client.
5. **Draft persistence** — Save-as-draft doesn't run validation, allowing partial data to be saved.
6. **Extensibility** — New field types are added by extending the switch statements in `buildFieldSchema` and `DynamicField`. No existing code changes.

---
