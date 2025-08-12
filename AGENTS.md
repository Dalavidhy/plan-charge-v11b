# Repository Guidelines

## Project Structure & Modules
- docs/: primary content and assets.
  - PRD.md: product requirements (authoritative spec).
  - openapi_v9.yaml: OpenAPI source; keep as single source of truth.
  - *_swagger.html / *_redoc.html: rendered API docs for quick preview.
  - *_swagger.json: vendor API descriptions used for reference.
  - ERD_v9.mmd: Mermaid ER diagram for data model.

## Build, Test, and Development
- Preview API docs (macOS): `open docs/openapi_v9_redoc.html`
- Serve docs locally: `cd docs && python3 -m http.server 8080`
- Lint OpenAPI (optional): `npx @stoplight/spectral lint docs/openapi_v9.yaml`
- Lint YAML (optional): `yamllint docs/openapi_v9.yaml`
- Validate JSON: `jq . docs/gryzzly_swagger.json > /dev/null`
- Render ERD (if mermaid-cli installed): `mmdc -i docs/ERD_v9.mmd -o docs/ERD_v9.png`

## Coding Style & Naming
- Markdown: use ATX headings (`#`, `##`), concise sections, lists for steps.
- Line length: prefer readable 80–100 columns; wrap paragraphs.
- OpenAPI: keep consistent schema and path naming; describe fields clearly; examples > prose.
- Filenames: preserve existing patterns (e.g., `openapi_v9.yaml`, `ERD_v9.mmd`, `PRD.md`).
- Keep generated artifacts in `docs/` with explicit version suffixes.

## Testing Guidelines
- OpenAPI: lint before commit; ensure `*_redoc.html` renders with no console errors when served.
- Markdown: proofread headings hierarchy; check relative links within `docs/`.
- Artifacts: if `openapi_v9.yaml` changes, consider refreshing HTML renders; attach screenshots in PR.

## Commit & Pull Requests
- Commit style: Conventional Commits (e.g., `feat(api): add invoice endpoints`, `chore(docs): update PRD`).
- Scope small, focused changes; reference issue IDs when applicable.
- PRs must include: summary of changes, affected files, testing notes (how you previewed/linted), and screenshots for rendered docs when relevant.
- Keep PR titles user-facing and body developer-facing.

## Security & Configuration
- Do not commit real credentials. Treat `.env` as example only.
- Avoid embedding tokens/PII in examples; redact with placeholders (e.g., `YOUR_API_KEY`).
- For external samples, note source and license in the PR.

