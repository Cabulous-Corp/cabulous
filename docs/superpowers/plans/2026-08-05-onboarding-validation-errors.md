# Onboarding Validation Errors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show backend onboarding validation errors clearly in the frontend, preserve server-side rules, and verify success/failure end to end.

**Architecture:** Keep Django as the source of truth for password and field validation. Format structured API errors in the shared frontend API hook so server actions surface human-readable messages. Add focused unit/serializer coverage and a browser flow against the running backend/frontend.

**Tech Stack:** Django REST Framework, Django password validators, Next.js server actions, Ky, Vitest, Python Playwright.

## Global Constraints

- Use the existing `service/` Django API and `app/web/` Next.js app.
- Keep Bun for frontend and `uv` for backend.
- Do not expose passwords or tokens in logs or test output.
- Run frontend quality commands before completion.

## Tasks

- [ ] Add focused frontend tests for formatting structured API validation errors.
- [ ] Make the shared API error hook preserve and expose backend validation messages.
- [ ] Add backend serializer coverage for onboarding password and field validation variants.
- [ ] Run an end-to-end browser flow covering successful onboarding and representative failures.
- [ ] Run the required quality checks and inspect the final diff.
