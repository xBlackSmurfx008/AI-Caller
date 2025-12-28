# E2E Testing Setup

This directory contains end-to-end tests for the AI Caller application.

## Setup

Install Playwright:
```bash
npm install -D @playwright/test
npx playwright install
```

## Running Tests

```bash
npx playwright test
```

## Test Structure

- `auth.spec.ts` - Authentication flow tests
- `calls.spec.ts` - Call management flow tests
- `config.spec.ts` - Configuration management tests
- `analytics.spec.ts` - Analytics viewing tests

## Configuration

Tests are configured in `playwright.config.ts`. Update baseURL to match your test environment.

