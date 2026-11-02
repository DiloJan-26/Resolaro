# Resolaro

Resolaro is an original resolution operations application for small B2B SaaS teams. This repository currently holds the Phase 1 foundation; workflow automation and agent execution are later capabilities.

The API lives in `apps/api` (Python 3.11, uv) and the web application in `apps/web` (Node 22, npm). Use the committed lockfiles. GitHub Actions performs builds and tests; deployed validation uses approved staging services. Do not put credentials in this repository.
