# AI Personal Trainer - Frontend Project Knowledge

This document contains project-specific knowledge for frontend development.

---

## Documentation Maintenance

**IMPORTANT: After making significant changes, ALWAYS update the project documentation:**

Update `README.md` (project root) when:
- Adding new pages or major components
- Changing environment variables
- Modifying Docker configuration
- Changing project structure
- Adding new dependencies to `package.json`
- Updating API integration

Update this file (`frontend-project-knowledge.md`) when:
- Adding new architectural patterns
- Creating new component conventions
- Changing design guidelines
- Adding new common tasks/workflows

---

## Package Manager

**IMPORTANT: Always use PNPM as the package manager for the frontend project.**

```bash
# Install dependencies
pnpm install

# Add a package
pnpm add <package-name>

# Add a dev dependency
pnpm add -D <package-name>

# Run scripts
pnpm dev
pnpm build
pnpm start
pnpm lint
```

Do NOT use npm or yarn.

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Next.js 15 | App Router, React framework |
| TypeScript | Type safety |
| Tailwind CSS 4 | Styling |
| ShadCN UI | Component library |
| React Query | Data fetching, polling |
| Axios | HTTP client |
| date-fns | Date formatting (Polish locale) |
| Lucide React | Icons |

---

## Project Structure

```
frontend/
├── app/                        # Next.js App Router pages
│   ├── layout.tsx             # Root layout (Server Component)
│   ├── page.tsx               # Home page (Server Component with metadata)
│   ├── globals.css            # Global styles + dark mode
│   ├── sitemap.ts             # Auto-generated sitemap for SEO
│   ├── robots.ts              # Robots.txt configuration
│   ├── (auth)/                # Auth routes group
│   │   ├── layout.tsx         # Auth layout with no-index metadata
│   │   ├── login/page.tsx     # Login page (Server Component wrapper)
│   │   └── register/page.tsx  # Register page (Server Component wrapper)
│   ├── progress/              # Task polling page
│   ├── profile/page.tsx       # Profile page (Server Component wrapper)
│   └── training/[id]/page.tsx # Training plan (Server Component with SSR)
├── components/
│   ├── auth/                  # Auth components (Client)
│   │   ├── login-form.tsx
│   │   ├── register-form.tsx
│   │   └── user-menu.tsx
│   ├── home/                  # Home page components (Client)
│   │   ├── training-form.tsx
│   │   └── training-list.tsx
│   ├── profile/               # Profile components (Client)
│   │   └── profile-form.tsx
│   ├── training/              # Training display components
│   │   ├── training-plan-client.tsx  # Client wrapper
│   │   ├── training-day-card.tsx     # Server Component
│   │   └── exercise-item.tsx         # Server Component
│   ├── providers/             # Context providers (Client)
│   │   ├── root-providers.tsx
│   │   ├── query-provider.tsx
│   │   ├── google-oauth-provider.tsx
│   │   └── auth-provider.tsx
│   ├── ui/                    # ShadCN UI components
│   └── theme-toggle.tsx       # Dark mode toggle
├── lib/
│   ├── api-client.ts          # API functions + polling
│   ├── auth.ts                # Cookie-based auth helpers
│   ├── types.ts               # TypeScript interfaces
│   └── utils.ts               # Helper functions (cn)
├── .env.local                 # Environment variables
└── package.json
```

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_SITE_URL` | Site URL for sitemap and canonical URLs | `http://localhost:3000` |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | Google OAuth client ID | (optional) |

---

## API Integration

**IMPORTANT: When creating or modifying functionality that uses the API, ALWAYS fetch the OpenAPI specification first:**

```
http://localhost:8000/openapi.json
```

Use `WebFetch` tool to retrieve the current API schema before implementing any API-related features. This ensures you have the most up-to-date endpoint definitions, request/response schemas, and validation rules.

### Current Endpoints

The frontend integrates with the backend API:

1. **POST /trainings** - Create training plan (async)
   - Request body: `{ age?: number, weight?: number, target_weight?: number }`
2. **GET /trainings/tasks/{task_id}** - Poll task status
3. **GET /trainings/{training_id}** - Get full training plan

### Field Names (English snake_case)

| API Field | Description | Range |
|-----------|-------------|-------|
| `age` | Client's age in years | 16-100 |
| `weight` | Current weight in kg | 30-300 |
| `target_weight` | Target weight in kg | 30-300 |

See `lib/api-client.ts` for implementation details.

---

## UI Language

- UI text is in **Polish** to match user requirements
- API messages are in English
- AI-generated content (exercise names, steps) is in Polish

---

## Common Commands

```bash
# Development
cd frontend
pnpm install
pnpm dev          # Start dev server on http://localhost:3000

# Production
pnpm build
pnpm start

# Add ShadCN component
pnpm dlx shadcn@latest add <component-name>
```

---

## Design Guidelines

- Mobile-first responsive design
- Dark mode support (toggle in top-right)
- Card-based layout for exercises
- Smooth animations and transitions
- Clean, modern fitness app aesthetic

---

## SEO Architecture & Server/Client Components

### Server Component Strategy

**Default: Server Components**
All pages are Server Components by default. This provides:
- Better SEO (content rendered server-side)
- Faster initial page load
- Smaller JavaScript bundle
- Automatic code splitting

**Use 'use client' only when:**
- Component uses React hooks (useState, useEffect, etc.)
- Component needs browser APIs
- Component has event handlers (onClick, onChange, etc.)
- Component uses context providers

### Component Patterns

#### Pattern 1: Server Page with Client Form
```typescript
// app/page.tsx (Server Component)
import { Metadata } from 'next';
import { ClientForm } from '@/components/client-form';

export const metadata: Metadata = {
  title: 'Page Title',
  description: 'Page description for SEO',
};

export default function Page() {
  return (
    <main>
      <h1>Static Server-Rendered Header</h1>
      <ClientForm />  {/* Interactive part */}
    </main>
  );
}

// components/client-form.tsx (Client Component)
'use client';
import { useState } from 'react';

export function ClientForm() {
  const [value, setValue] = useState('');
  // ... interactive logic
}
```

#### Pattern 2: Server Component with Server-Side Data
```typescript
// app/training/[id]/page.tsx (Server Component)
import { cookies } from 'next/headers';

export async function generateMetadata({ params }): Promise<Metadata> {
  return {
    title: `Training Plan`,
  };
}

export default async function Page({ params }) {
  const cookieStore = await cookies();
  const token = cookieStore.get('access_token')?.value;

  // Server-side data fetching with auth
  const data = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  return <ClientWrapper data={data} />;
}
```

#### Pattern 3: Nested Server Components
```typescript
// Server Component can import and render other Server Components
// training-day-card.tsx (NO 'use client')
import ExerciseItem from './exercise-item';  // Also Server Component

export default function TrainingDayCard({ day }) {
  return (
    <Card>
      {day.exercises.map(ex => (
        <ExerciseItem exercise={ex} />  // Server Component
      ))}
    </Card>
  );
}
```

### SEO Features Implemented

#### Metadata Exports
Every page exports metadata:
```typescript
export const metadata: Metadata = {
  title: 'Page Title - AI Personal Trainer',
  description: 'Page description',
  keywords: ['keyword1', 'keyword2'],
  openGraph: {
    type: 'website',
    locale: 'pl_PL',
    title: 'OG Title',
    description: 'OG Description',
  },
};
```

#### Dynamic Metadata
For dynamic routes:
```typescript
export async function generateMetadata({ params }): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Dynamic Title for ${id}`,
  };
}
```

#### Sitemap (app/sitemap.ts)
Auto-generates XML sitemap at `/sitemap.xml`:
```typescript
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${baseUrl}`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 1,
    },
  ];
}
```

#### Robots (app/robots.ts)
Controls search engine indexing:
```typescript
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/progress', '/profile'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
```

### Common Pitfalls to Avoid

1. **Don't use 'use client' in pages unnecessarily**
   - Pages should be Server Components by default
   - Extract interactive parts to separate Client Components

2. **Don't try to add metadata to Client Components**
   - Create Server Component wrapper that exports metadata
   - Render Client Component inside

3. **Don't use hooks in Server Components**
   - useState, useEffect, useRouter, useContext require 'use client'
   - Extract those parts to Client Components

4. **Don't forget to handle cookies in Server Components**
   - Use `cookies()` from 'next/headers'
   - Access is async: `const cookieStore = await cookies()`

### Providers Architecture

All Context Providers are consolidated in RootProviders:
```typescript
// components/providers/root-providers.tsx ('use client')
export function RootProviders({ children }) {
  return (
    <QueryProvider>
      <GoogleOAuthProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </GoogleOAuthProvider>
    </QueryProvider>
  );
}

// app/layout.tsx (Server Component)
export default function RootLayout({ children }) {
  return (
    <html lang="pl">
      <body>
        <RootProviders>
          {children}
        </RootProviders>
      </body>
    </html>
  );
}
```

This pattern:
- Keeps layout as Server Component
- Allows all pages to use context
- Centralizes provider logic
- Maintains SEO benefits
