# Launch Stabilisation

T-041 prepares the T-040 planner for repeatable local development and the
commercial work that follows. It does not add affiliate, booking, payment, or
production-provider behaviour.

## Supported local endpoints

| Service | URL |
|---|---|
| Web app | `http://localhost:3001` |
| API | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |

Port `3000` is deliberately not used because it is reserved for Luxorahut POS.

## Windows start

From the repository root:

```powershell
.\scripts\start-local.ps1
```

The script opens the API and web app in separate PowerShell windows. Individual
launchers are `scripts/start-api.ps1` and `scripts/start-web.ps1`.

## Correct Python import path

The API imports from both `services/api/app` and the repository-level `ai` and
`travelos` packages. It must therefore be launched with both the repository
root and `services/api` on `PYTHONPATH`. The PowerShell and Docker launchers set
this automatically.

## Frontend dependency policy

- Next.js and `eslint-config-next` are pinned to `15.5.20`, the current Next 15
  backport at the time of T-041.
- `package-lock.json` is committed and CI uses `npm ci` for reproducible builds.
- `npm audit --omit=dev` still reports two moderate findings in the PostCSS
  version nested inside Next.js. npm offers no non-breaking remediation; its
  suggested forced remediation would install Next 9. This is recorded rather
  than applying an unsafe downgrade.

## Validation

- 1,191 backend/AI/platform tests pass.
- Ruff passes.
- Frontend lint, type checking, production build, and local port 3001 startup pass.
- The API starts at port 8000; `/health`, `/openapi.json`, and `POST /planner/plan` pass.
- CORS preflight from `http://localhost:3001` is covered by an automated test.
- Docker Compose YAML and service/build paths are structurally validated. A
  Docker-engine build must still be run on a machine with Docker installed.
