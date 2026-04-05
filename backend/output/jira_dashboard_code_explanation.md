---
title: "Jira Dashboard Code Explanation"
slug: /jiradashboardcodeexplanation
---

Jira Dashboard Generator
Code Architecture & Technical Documentation
Multi-Tenant | OAuth 2.0 | MCP Tools | LangGraph + Qwen

## 1. Project Structure

The project consists of four main files:

### 2. mcp_tools.py — Jira Tool Definitions

This file defines what the AI can do with Jira. Each function decorated with `@tool` becomes a callable tool that the LLM (Qwen) can invoke during a conversation.

#### 2.1 Available Tools

#### 2.2 Auth Resolver Pattern

Tools never store credentials directly. Instead, a resolver function is injected at startup:

```python
set_auth_resolver(get_jira_auth)
```

This means every tool call always uses the current logged-in user's OAuth token from their session — not a hardcoded API key. This is what enables multi-tenancy.

## 3. server.py — Main Application

This is the brain of the application. It has seven distinct sections:

### 3.1 Flask + OAuth Setup

Flask is initialised with a fixed secret key (critical for sessions to survive OAuth redirects). The Atlassian OAuth app is registered with authlib:

```python
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fixed-default-string')
atlassian = oauth.register(
    name='atlassian',
    client_id=os.getenv('JIRA_CLIENT_ID'),
    authorize_url='https://auth.atlassian.com/authorize',
    access_token_url='https://auth.atlassian.com/oauth/token',
)
```

### 3.2 Per-User Data Isolation (Multi-Tenant)

All data is scoped to the logged-in user using a hashed user ID:

```python
_user_dashboards: Dict[str, Dict] = {}   # per-user chart store
_user_cache:      Dict[str, Any]  = {}    # per-user Jira cache

def user_id():
    return hashlib.md5(email.encode()).hexdigest()  # stable unique ID

def get_user_dashboards():
    return _user_dashboards.get(user_id(), {})  # only THIS user's data
```

User A on `balajiselliappan.atlassian.net` and User B on `ABCCorp.atlassian.net` will never see each other's dashboards or cache.

### 3.3 Jira Auth — OAuth + API Key Fallback

Every Jira API call goes through `get_jira_auth()` which checks two sources in priority order:

The auth type is logged on every call so you can always see which method is active in the terminal:

```
[OAUTH] GET search/jql      ← using OAuth token
[APIKEY] GET search/jql     ← using .env API key
```

### 3.4 Three-Level Intelligence System

When a user types a prompt, the system tries three levels of intelligence in order — fastest first:

#### Level 1 — Fast Dispatch

Directly calls Jira tools without involving the LLM. Saves 3-5 seconds per request:

```python
def fast_dispatch(prompt_lower, project_key):
    if 'list sprint' in prompt_lower:
        return jira_get_sprints.invoke({'project_key': project_key})
    if 'list issue' in prompt_lower:
        return jira_search_issues.invoke({'jql': f'project={project_key}'})
    return None  # needs LLM
```

#### Level 2 — MCP Agent (ReAct Loop)

The LLM is given all available tools and asked to decide which one to call:

```python
# Step 1: Ask LLM which tool to use
response = llm.invoke([system_prompt, HumanMessage(prompt)])
# LLM responds: {"tool": "jira_search_issues", "args": {"jql": "..."}}
# Step 2: Call the tool
result = tool_map[tool_name].invoke(tool_args)
# Step 3: Ask LLM to format result
final = llm.invoke([..., f'Tool returned: {result}. Give final answer.'])
```

#### Level 3 — Chart Generation

Charts are rendered entirely in memory — no files written to disk:

```python
def generate_chart_b64(chart_type, title, labels, values):
    fig, ax = plt.subplots(figsize=(10, 6))
    # ... draw pie/bar/line/metrics ...
    buf = BytesIO()                            # in-memory buffer
    plt.savefig(buf, format='png', dpi=150)    # save to buffer
    plt.close()
    return 'data:image/png;base64,' + base64.b64encode(buf.read()).decode()
```

The Base64 string is returned in the API response and displayed directly as an `<img>` tag in the browser.

### 3.5 OAuth Routes

The full OAuth flow uses 4 routes:

### 3.6 Login Required Decorator

Every app route is protected by `@login_required` which checks if the user is authenticated:

```python
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            if request.is_json:
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect('/login')   # redirect browser to login page
        return f(*args, **kwargs)
    return decorated
```

### 3.7 Jira Cache

A 60-second TTL cache prevents hitting the Jira API on every single request:

```python
def jira_get_cached(path, params=None):
    key = f'{user_id()}:{path}:{json.dumps(params)}'  # scoped per user
    if key in _user_cache:
        data, ts = _user_cache[key]
        if time.time() - ts < 60:           # 60 second TTL
            logger.info(f'[CACHE HIT] {path}')
            return data
    data = jira_get(path, params)           # fetch fresh
    _user_cache[key] = (data, time.time())
    return data
```

## 4. Complete Authentication Flow

## 5. End-to-End Prompt Flow

Example: User types 'Create a pie chart showing issue status'

## 6. index.html — Frontend Architecture

The frontend is pure HTML + Bootstrap 5 + vanilla JavaScript. No React, no build step required.

### 6.1 Page Layout

### 6.2 JavaScript Flow

All interactions follow the same pattern — call API, check result type, render:

```javascript
async function generateDashboard() {
    var result = await api('/api/generate', {method:'POST', body: prompt});
    if (result.cleared)      // 'clear all' command → remove all chart cards
    if (result.result_type)  // Jira query → show table (sprints/issues/assignees)
    if (result.chart_config) // chart generated → render Base64 img
    if (result.auto_export)  // 'export to excel' → trigger file download
    if (result.response)     // text response → show dismissable card
}
```

### 6.3 401 Handling

If the session expires mid-session, all API calls automatically redirect to login:

```javascript
async function api(url, opts) {
    var res = await fetch(url, opts || {});
    if (res.status === 401) {
        window.location.href = '/login';  // redirect to login
        return;
    }
}
```

## 7. Environment Variables (.env)

## 8. Key Design Decisions

### Table 1:

| File | Purpose |
| --- | --- |
| server.py | Main Flask application — all backend logic, routes, OAuth, agent |
| mcp_tools.py | Jira MCP tool definitions — what the AI can do with Jira |
| templates/index.html | Main dashboard UI — charts, prompts, Jira tasks panel |
| templates/login.html | Login page shown to unauthenticated users |
| templates/select_site.html | Site picker for users with multiple Jira instances |
| templates/select_project.html | Project picker shown after OAuth login |

### Table 2:

| Tool | What it does |
| --- | --- |
| jira_search_issues(jql, max_results) | Search issues using JQL — most flexible tool |
| jira_get_sprints(project_key) | List all sprints for a project board |
| jira_get_issue(issue_key) | Get full details of a specific ticket (e.g. SCRUM-12) |
| jira_create_issue(summary, desc, ...) | Create a new task/bug/story |
| jira_update_issue(key, status, ...) | Change status, assignee, or priority |
| jira_get_project_summary(project_key) | Count issues by status/assignee/priority — used for charts |
| jira_get_my_issues(project_key) | Issues assigned to the currently logged-in user |

### Table 4:

| Priority | Auth Method |
| --- | --- |
| 1st | OAuth token from session (logged-in user's token) |


| 2nd | API key from .env file (fallback for local dev) |

Table 5:
| Level | When used | Speed |
| --- | --- | --- |
| Level 1: Fast Dispatch | Simple queries: list sprints, list issues, who is working on what | Instant — 0 LLM calls |
| Level 2: MCP Agent | Complex queries: charts, specific JQL, multi-step tasks | 2-5 seconds — 1-3 LLM calls |
| Level 3: Chart Generation | Any prompt with chart/pie/bar/line keywords | 1-2 seconds — matplotlib render |

Table 6:
| Route | What it does |
| --- | --- |
| /auth/login | Builds Atlassian URL manually, stores state in cookie, redirects user |
| /auth/callback | Verifies state cookie, exchanges code for token, fetches cloud ID and user info |
| /auth/logout | Clears session + user dashboards, redirects to /login |
| /auth/status | Returns JSON: {connected, auth_type, user, project_key} |

Table 8:
| Step | What happens |
| --- | --- |
| 1. Visit / | Not authenticated → redirect to /login |
| 2. /login page | User sees login card with 'Continue with Atlassian' button |
| 3. Click button | /auth/login generates random state, stores in cookie, builds Atlassian URL |
| 4. Atlassian | User logs in with their Atlassian account (password required after sign out) |
| 5. /auth/callback | Verify state cookie, exchange code for access_token via POST |
| 6. Fetch sites | GET accessible-resources to find user's Jira cloud ID and site name |
| 7. Multiple sites? | Show /select-site page to pick which Jira instance to use |
| 8. /select-project | Fetch and display all projects in the chosen site, user picks one |
| 9. Dashboard | All API calls now use user's token + cloud_id + chosen project_key |
| 10. Sign out | Session cleared + dashboards deleted → back to /login |

Table 9:
| Step | What happens |
| --- | --- |
| 1. Browser | POST /api/generate {prompt: 'Create a pie chart showing issue status'} |
| 2. process_prompt() | Detects: wants_chart=True (has 'pie', 'chart'), jira_ok=True |
| 3. Fast dispatch | Returns None — chart requests skip fast dispatch |
| 4. run_jira_agent() | LLM decides to call jira_get_project_summary |
| 5. Tool call | jira_get_project_summary → {status_counts: {Open:5, Done:3, InProgress:2}} |
| 6. extract_chart_data() | Converts to {labels:[Open,Done,InProgress], values:[5,3,2]} |
| 7. generate_chart_b64() | Matplotlib draws pie chart, saves to BytesIO, returns Base64 |
| 8. save_user_dashboard() | Stores chart in _user_dashboards[user_id] |
| 9. Return JSON | {chart_config: {image_base64: 'data:image/png;base64,...'}} |
| 10. Browser | <img src='data:image/png;base64,...'> renders the chart |

Table 10:
| Section | Contents |
| --- | --- |
| Header | User avatar, name, site, project key, OAuth badge, Sign out |
| Metrics row | 4 tiles: Dashboards / Charts / Jira Tasks / Exports |
| Prompt area | Textarea + Generate button + quick buttons + example prompts |
| Results area | Query tables (sprints/issues) + Dashboard chart cards |
| Jira Tasks panel | Live tasks from current project with status/priority badges |

Table 11:
| Variable | Purpose |
| --- | --- |
| QWEN_BASE_URL | LLM API endpoint (OpenRouter or DashScope) |
| QWEN_API_KEY | LLM API key |
| QWEN_MODEL | Smart model for complex queries (e.g. qwen/qwen-plus) |
| QWEN_MODEL_FAST | Fast model for simple queries (e.g. qwen/qwen-turbo) |
| JIRA_CLIENT_ID | Atlassian OAuth app Client ID |
| JIRA_CLIENT_SECRET | Atlassian OAuth app Client Secret |
| JIRA_SERVER | Fallback: Jira base URL (used if OAuth not connected) |
| JIRA_USER_EMAIL | Fallback: Atlassian account email |
| JIRA_API_TOKEN | Fallback: Atlassian API token |
| JIRA_PROJECT_KEY | Default project key (e.g. SCRUM) |
| FLASK_SECRET_KEY | Session signing key (use fixed string in production) |

Table 12:
| Decision | Reason |
| --- | --- |
| OAuth state in cookie not session | Session cookies can be lost during Atlassian redirect; dedicated cookie is reliable |
| Fixed secret_key | Random key on every restart invalidates sessions and breaks OAuth |
| User ID = hashed email | Stable across sessions, never exposes raw email in memory keys |
| Base64 charts not files | No disk I/O, no file cleanup, works in memory-only environments |
| Fast dispatch before LLM | Saves 3-5 seconds for common queries — LLM only when needed |
| 60s Jira cache per user | Reduces API calls, stays fresh enough for a dashboard context |
| API key fallback | Allows development without OAuth — just add .env keys |
| clear_user_cache on writes | Ensures fresh data after creating or updating issues |
| Auto chart type switch | Single data point bar/line looks broken — auto-switch to metrics card |
