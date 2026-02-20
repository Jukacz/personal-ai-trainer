---
name: frontend-project-knowledge
description: Frontend architecture and implementation conventions for AI Personal Trainer Next.js app. Use when creating or changing pages/components, API integration, SEO metadata, provider wiring, routing, styling patterns, package management, or frontend environment/configuration.
---

# Frontend Project Knowledge

Use this skill as the canonical frontend rulebook.

## Read detailed frontend reference

Load `references/frontend-project-knowledge.md` before implementing frontend features.

It contains:
- Stack and project structure for Next.js 15 app router
- Package manager rule (`pnpm` only)
- API integration rules and endpoint contract
- SEO metadata/sitemap/robots patterns
- Server vs Client component patterns and pitfalls
- Providers architecture and localization rules
- Environment variables and common commands

## Apply on every frontend change

- Use `pnpm`; do not switch to `npm` or `yarn`.
- Treat Vercel as the default production hosting platform for frontend.
- Do not add frontend service to root `docker-compose.yml` (frontend runs outside Docker Compose).
- Fetch `http://localhost:8000/openapi.json` before API-related implementation.
- Default to Server Components; isolate interactivity in Client Components.
- Keep UI copy in Polish and API contract fields in English snake_case.
- Update `README.md` when frontend changes impact setup, architecture, or usage.
