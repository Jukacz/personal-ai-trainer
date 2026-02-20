---
name: backend-project-knowledge
description: Backend architecture and implementation conventions for AI Personal Trainer FastAPI services. Use when creating or changing backend endpoints, schemas, controllers, repositories, services, MongoDB models/collections, async task flows, or backend environment/configuration.
---

# Backend Project Knowledge

Use this skill as the canonical backend rulebook.

## Read detailed backend reference

Load `references/backend-project-knowledge.md` before implementing backend features.

It contains:
- Current VCR architecture and directory layout
- Async task pattern for training generation
- API conventions, naming conventions, and schema flow
- MongoDB collections and required fields
- Standard endpoint implementation order
- Environment variables and local run commands
- Backend change checklists

## Apply on every backend change

- Keep API messages in English.
- Keep AI-generated training content in Polish.
- Preserve URL and identifier naming conventions.
- Follow Schema -> Repository -> Service -> Controller -> View order for new endpoints.
- Update `README.md` when backend changes impact usage or architecture.
