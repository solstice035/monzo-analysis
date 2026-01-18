# Monzo Analysis

## Overview

Personal finance tracking and analytics using the Monzo API. Scheduled data extraction with budget comparison, trend analysis, and spending insights.

**Key approach:** Polling/scheduled extraction (not webhooks). Focus is analytics, not real-time notifications.

## PRD Reference

Original PRD: [[PRD-monzo-webhook]] in Obsidian
Local copy: [docs/PRD.md](docs/PRD.md)

## API Documentation

Monzo API reference docs are in [docs/api-reference/](docs/api-reference/)

Key endpoints:
- `GET /accounts` - List accounts (personal, joint)
- `GET /pots` - List savings pots
- `GET /transactions` - Fetch transactions (with pagination via `since`, `before`)
- `PATCH /transactions/{id}` - Add custom metadata (for reclassification)

## Core Features

1. **Scheduled Data Extraction** - Configurable sync frequency (daily recommended)
2. **Budget Tracking** - Import spreadsheet budget, map Monzo categories
3. **Category Management** - Use Monzo categories + custom overrides via metadata
4. **Analytics** - Trends, recurring payments, spend vs budget

## Monzo Categories

Transactions include one of: `general`, `eating_out`, `expenses`, `transport`, `cash`, `bills`, `entertainment`, `shopping`, `holidays`, `groceries`

## Tech Stack

*To be determined - create TRD before implementation*

## Quick Start

*Setup instructions to be added*

## Project Status

- Status: In Progress
- Started: 2026-01-17
- PRD Gate: Gate 1 PASS
- Brainstorm: Complete (features validated, user journeys mapped)

## Next Steps

1. Create TRD with tech stack decisions
2. Begin MVP implementation
