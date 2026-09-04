# AutoMessage

An interactive product prototype for an open-source, self-hosted DM automation platform. It demonstrates the core MVP experience: operations dashboard, automation library, visual flow builder, shared inbox, contact management, and AI knowledge sources.

## Run locally

```bash
npm install
npm run dev
```

Open the URL printed by Vite. The prototype uses realistic local demo data and does not require credentials or external services.

## Available scripts

- `npm run dev` — start the development server
- `npm run build` — type-check and create a production build
- `npm run lint` — run static analysis
- `npm run preview` — preview the production build

## Prototype scope

This frontend validates the interaction model and visual direction in the MVP specification. The visual flow editor uses React Flow and supports canvas navigation and node repositioning. Navigation, filters, inbox takeover, message sending, source upload feedback, and flow publishing are interactive.

The production FastAPI API, PostgreSQL persistence, Redis worker, channel adapters, and LLM runtime described by the specification are not part of this prototype slice.
