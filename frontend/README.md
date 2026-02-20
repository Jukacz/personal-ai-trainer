# AI Personal Trainer - Frontend

Modern, responsive React frontend for the AI Personal Trainer application built with Next.js, TypeScript, and Tailwind CSS.

## Tech Stack

- **Next.js 15** - App Router with Server Components
- **TypeScript** - Type-safe code
- **Tailwind CSS** - Utility-first styling
- **ShadCN UI** - Beautiful, accessible components
- **React Query** - Data fetching and state management
- **Axios** - HTTP client
- **date-fns** - Date formatting with Polish locale
- **Lucide React** - Modern icon library

## Features

- Clean, modern fitness app design
- Dark mode support with theme toggle
- Responsive mobile-first layout
- Form validation for user inputs
- Real-time task polling with progress indicators
- Expandable exercise cards with video instructions
- Calendar-based training schedule view
- Polish language UI

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm
- Backend API running on `http://localhost:8000`
- dotenvx (optional)

### Installation

```bash
# Install dependencies
pnpm install
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Development

```bash
# Start development server
pnpm dev
pnpm dev:dotenvx

# Open browser to http://localhost:3000
```

### Build

```bash
# Build for production
pnpm build
pnpm build:dotenvx

# Start production server
pnpm start
pnpm start:dotenvx
```

### dotenvx (Optional)

Use dotenvx when you want to inject values from `.env.local` explicitly at runtime:

```bash
pnpm dev:dotenvx
```

### Linting

```bash
pnpm lint
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Home page with form
│   ├── progress/            # Task polling page
│   │   └── page.tsx
│   └── training/            # Training plan display
│       └── [id]/
│           └── page.tsx
├── components/
│   ├── providers/           # React Query provider
│   ├── theme-toggle.tsx     # Dark mode toggle
│   └── ui/                  # ShadCN UI components
├── lib/
│   ├── api-client.ts        # API client and polling logic
│   ├── types.ts             # TypeScript types
│   └── utils.ts             # Utility functions
└── public/                  # Static assets
```

## Pages

### 1. Home (`/`)
- Form for entering user data (age, weight, target weight)
- Input validation with error messages
- Submits to backend and redirects to progress page

### 2. Progress (`/progress?task_id=...`)
- Polls task status every 3 seconds
- Shows animated loading indicators
- Auto-redirects to training plan when complete
- Error handling with retry option

### 3. Training Plan (`/training/[id]`)
- Calendar view of training days
- Expandable exercise cards
- Video player for exercise demonstrations
- Step-by-step instructions
- Option to generate a new plan

## API Integration

The frontend integrates with these backend endpoints:

- `POST /api/v1/trainings` - Create training plan (returns task_id)
- `GET /api/v1/trainings/tasks/{task_id}` - Poll task status
- `GET /api/v1/trainings/{training_id}` - Get full training plan

All API calls are handled by `lib/api-client.ts` using Axios.

## Component Patterns

### Server vs Client Components
- Layout and static pages use Server Components by default
- Interactive pages use `'use client'` directive
- React Query for client-side data fetching

### State Management
- Local state with `useState` for form inputs
- React Query for server state
- Custom polling hook for task status

### Styling
- Tailwind utility classes for styling
- ShadCN components for consistent design
- Dark mode with CSS variables
- Mobile-first responsive design

## Accessibility

- Semantic HTML elements
- Proper ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast meeting WCAG 2.1 AA standards
- Loading states for screen readers

## Performance Optimizations

- Next.js automatic code splitting
- Lazy loading of exercise details (accordion)
- Video preload="metadata" to reduce bandwidth
- Optimized polling interval (3s)
- Suspense boundaries for loading states

## Dark Mode

Dark mode is implemented with:
- CSS custom properties in `globals.css`
- Client-side theme persistence in localStorage
- System preference detection on first load
- Fixed toggle button in top-right corner

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### "Cannot connect to API"
- Ensure backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

### Dark mode not working
- Clear localStorage and refresh
- Check browser console for errors

### Videos not playing
- Ensure video URLs from MuscleWiki API are valid
- Check browser video format support

## Contributing

1. Follow the existing code style
2. Use TypeScript strict mode
3. Add Polish translations for all UI text
4. Test on mobile devices
5. Run `pnpm lint` before committing

## License

Private project for AI Personal Trainer application.
