---
title: "Jira Q&A"
slug: /jira-qa
---

# Jira Q&A

## How do we secure credentials and tokens?

Based on the actual code in [`server.py`](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) and the `.env` file:

### What is currently in place:

### OAuth Tokens

- Access tokens are never stored in the browser — they live in a server-side Flask session.
- Session cookie is [httponly=True](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) (JS cannot read it) and [samesite=Lax](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) (CSRF protection).
- Sessions are stored in [jira\_dashboard\_sessions](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) on the server, not in the cookie payload.
- Tokens include `offline_access` scope for refresh without re-login.

### App Secrets (Client ID / Secret)

- Loaded at runtime via [os.getenv()](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) from the `.env` file — never hardcoded in source.
- `.env` should be in [.gitignore](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) so it is never committed to version control.

### Session Security

- Session cookie name is custom (`jira_dashboard_session`) to avoid fingerprinting.
- `SESSION_COOKIE_SECURE = False` currently — this must be set to `True` in production (HTTPS only).

### What still needs to be done (gaps):

| **Gap**                                             | **Risk**                                             | **Fix**                                           |
|-----------------------------------------------------|------------------------------------------------------|---------------------------------------------------|
| `.env` currently has live secrets visible in the file | High — if repo is public or shared, credentials leak | Rotate keys immediately; add `.env` to `.gitignore`   |
| `SESSION_COOKIE_SECURE = False`                       | Tokens could transmit over HTTP                      | Set to `True` behind HTTPS in production            |
| No token expiry/rotation handling visible           | Stale tokens could persist                           | Add refresh token logic and session expiry checks |
| No secret scanning in CI                            | Future accidental commits go undetected              | Add `truffleHog` or `gitleaks` pre-commit hook        |

### Recommended immediate actions:

1. Rotate `JIRA_CLIENT_SECRET` and `QWEN_API_KEY` — both are currently exposed in the shared `.env`.
2. Add `.env` to [.gitignore](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) if not already there.
3. Use a secrets manager (e.g. AWS Secrets Manager, Doppler, or GitHub Secrets for CI) for production deployment.

## What if Atlassian API permissions vary by tenant?

Based directly on the code in [`server.py:734-770`](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html), here is exactly what happens:

### The app has a 3-tier fallback chain:

### Tier 1 — Atlassian `/me` endpoint

- Called first after token exchange.
- Works on most standard tenants.
- Returns: name, email, profile picture.

### Tier 2 — Jira `/rest/api/3/myself` endpoint

- Triggered automatically if `/me` returns 403.
- Uses the cloud ID of the user's first accessible Jira site.
- Returns: `displayName`, `emailAddress`, avatar URL.
- This covers tenants where the identity scope is restricted but Jira API access is permitted.

### Tier 3 — Graceful degradation

- If both endpoints fail (any exception), the app falls back to using the Jira site name as the user identity.
- The user still gets logged in and can use the dashboard.
- Name and email fields will be empty, but the session is valid.

### In practice:

- The user never sees an error due to tenant permission differences.
- The login flow completes regardless of which tier succeeds.
- Only the displayed user name/email may be less detailed if lower tiers are used.

### The one gap to be aware of:

- If a tenant blocks all three paths AND has no accessible sites, the app correctly shows a "no Jira sites found" error and stops the login — which is the right behavior since the user genuinely has no accessible data.

## How is user access controlled?

Based on the actual code in [`server.py`](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html), here is how user access is controlled:

### 1. OAuth Authentication (Atlassian)

- Every user must log in via Atlassian OAuth. No shared/hardcoded Jira account is used.
- The app requests scopes: `read:jira-work`, `write:jira-work`, [read:jira-user](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html), `offline_access`, `openid`, [email](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html).
- Only users with a valid Atlassian account and access to at least one Jira site can proceed.

### 2. Session-based Access

- After login, the user's OAuth token, identity, selected site, and selected project are stored in a server-side session.
- All subsequent API calls use that user's own token — not a shared app token.

### 3. `@login_required` Decorator

- Every protected route is guarded by a [login_required](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) decorator.
- If no valid session exists, the user is redirected to the login page.

### 4. Per-user Data Scoping

- Jira data is fetched using the logged-in user's token, so they only see sites and projects their Atlassian account has permission to access.
- Dashboard data and cache are keyed per user to prevent cross-user data leakage.

### 5. Site and Project Selection

- After login, the user explicitly selects which Jira site and project to work with — they cannot access sites outside their Atlassian permissions.


# In short

Access is controlled at three layers — Atlassian identity, session validity, and route-level guards — with all data scoped to the authenticated user's own Jira permissions.

Based on the current state of the codebase (app is already running, OAuth flow is working, dashboard and metrics are functional), here is a realistic phased rollout:

## Phase 1 — Internal Validation (Week 1–2)

- Run the app with 1–2 internal users on real Jira projects
- Verify OAuth flow, site/project selection, and metrics accuracy
- Fix any environment-specific issues (venv, Python version, config)
- Rotate exposed credentials and add `.env` to [.gitignore](vscode-file://vscode-app/Applications/Visual%20Studio%20Code.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html)

## Phase 2 — Pilot with Small Team (Week 3–4)

- Onboard 3–5 users from one team
- Collect feedback on dashboard usefulness and UX gaps
- Identify missing metrics or workflow steps
- Document setup process for repeatable onboarding

## Phase 3 — Hardening (Week 5–6)

- Add automated tests for critical API flows
- Improve error messages and edge case handling
- Add secret scanning, basic CI checks
- Address any findings from pilot feedback

## Phase 4 — Broader Rollout (Week 7–8)

- Onboard additional teams or projects
- Enable multi-project support if needed
- Begin roadmap items: role-based access, forecasting widgets

## What would accelerate this

- Stable hosting environment (not just local `python server.py`)
- A shared deployment (e.g. internal server or cloud VM) so others don't need local setup
- A registered Atlassian OAuth app with correct redirect URIs for the hosted URL

## What could delay it

- Atlassian OAuth app not approved/configured for non-localhost redirects
- Office network proxy blocking Atlassian/AI API calls
- Credential rotation and secret management setup taking time
