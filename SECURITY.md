# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it privately — **do not open a public GitHub issue**.

Email **code@radcrew.org** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce (proof-of-concept code or requests, if applicable)
- Any relevant logs, screenshots, or affected endpoints/files

We will acknowledge your report within **3 business days** and aim to provide a status update (triage result, expected fix timeline) within **7 business days**.

## Scope

This covers the `real-estate-consultant` application: the FastAPI backend, the Next.js frontend, and their Supabase/OpenRouter integrations as configured in this repository. Third-party services we depend on (Supabase, OpenRouter, Vercel, Apify, etc.) should be reported directly to those vendors.

## Supported Versions

This is an actively developed internal MVP tracked on `main`. Only the latest state of `main` is supported; there are no maintained release branches.

## Disclosure

Please give us a reasonable amount of time to investigate and remediate a report before disclosing it publicly. We'll credit reporters who wish to be credited once a fix ships.
