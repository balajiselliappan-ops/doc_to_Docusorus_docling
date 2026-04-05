---
title: "Portal Documentation"
slug: /portaldocumentation
---

# Portal Documentation
slug: /portaldocumentation

## Jira AI Chatbot Portal
### Technical Documentation & User Guide
**March 2026  |  POC Version 1.0**


## 2. AI Commands — Complete Reference

All commands are typed in natural language in the chat box. No special syntax required.

### 2.1 Display & Query Commands

These commands make the AI answer from Jira data directly — no action is taken.

### 2.2 Create Ticket Commands

These commands create a new Jira issue in the sprint selected in the dropdown.

### 2.3 Update Ticket Commands

These commands update existing Jira tickets.

### 2.4 Move Ticket Commands

These commands move tickets between sprints.

### 2.5 Rebalance & Assign Commands

These commands automatically distribute work across team members.

### 2.6 Export Commands

These commands trigger data export.

### 2.7 Email Report Commands

These commands generate and email a sprint report.

### 2.8 Voice Commands

Click the microphone icon and speak any of the above commands. Groq Whisper transcribes your speech to text automatically. Same commands work — just spoken instead of typed.


## 4. Comparison — Our Portal vs Jira Cloud App

The Jira Cloud App refers to the official Jira web interface at `company.atlassian.net` and the MS Teams Jira App.

### 4.1 Feature Comparison

### 4.2 Key Differentiators

#### What Our Portal Does That Jira Cloud Cannot

- Natural language queries — ask questions in plain English, get intelligent answers
- AI-powered analysis — 'who is overloaded?' or 'what is at risk?' gives instant insights
- Agentic actions — AI creates, updates, moves tickets based on your intent
- Auto rebalancing — AI automatically redistributes workload across team
- Voice commands — speak instead of type
- Custom dashboard — designed specifically for sprint management at a glance
- Excel export with charts — one-click download including visual charts
- Email reports on demand — type a command and AI emails the report

#### What Jira Cloud Does Better

- Full Jira feature set — epics, roadmaps, custom workflows, automation rules
- Mobile native app — iOS and Android with push notifications
- Enterprise admin — user management, permissions, SSO
- Official support — Atlassian backed with SLA
- Deep integrations — Confluence, Bitbucket, all Atlassian products
- Compliance certifications — SOC2, ISO27001, GDPR certified

### 4.3 vs MS Teams Jira App Specifically

### 4.4 Ideal Use Case

---

## 5. Technology Stack Summary

Jira AI Chatbot Portal — POC Documentation — March 2026

| Route | Method | What it Does |
| --- | --- | --- |
| `/chat` | POST | Receives user message, fetches Jira data, calls AI, returns reply |
| `/sprint` | GET | Returns active sprint data — used by keep-alive ping |
| `/sprint/by-id` | POST | Returns data for a specific sprint selected in dropdown |
| `/sprints/list` | GET | Returns all sprints for the dropdown selector |
| `/export` | POST | Generates and downloads Excel file with sprint data + charts |
| `/transcribe` | POST | Receives audio file, sends to Groq Whisper, returns text |

| Function | What it Does |
| --- | --- |
| `get_boards()` | Fetches all Jira boards in your workspace |
| `get_active_sprint(board_id)` | Finds the currently running sprint |
| `get_sprint_issues(board_id, sprint_id)` | Fetches all issues in a given sprint |
| `get_sprint_summary()` | Returns complete sprint data including stats — used by `/chat` and `/sprint` |

| Function | What it Does |
| --- | --- |
| `run_agent(user_message, jira_data)` | Main function — sends message to Groq AI with sprint context and tool definitions |
| `TOOLS list` | Defines all 5 actions the AI can take: create, update, move, rebalance, send report |
| Tool routing logic | After AI picks a tool, routes to the correct agent_tools function |
| Final summary call | Second AI call to summarise what action was taken in plain English |

| Function | What it Does |
| --- | --- |
| `create_issue(project_key, summary, ...)` | Creates a new Jira ticket and adds it to the selected sprint |
| `update_issue(issue_key, status, ...)` | Updates status, assignee or title of an existing ticket |
| `move_to_sprint(issue_keys, target)` | Moves one or more tickets to a different sprint |
| `rebalance_tasks()` | Analyses workload per team member and reassigns from overloaded to underloaded |
| `send_sprint_report(to_email)` | Generates HTML sprint report and emails it via Gmail SMTP |

| Section | What it Contains |
| --- | --- |


# UI Components

| Component | Description |
| --- | --- |
| Sidebar | Navigation links for Dashboard, Sprints, Resources, Reports tabs + Export button |
| Topbar | Page title display |
| Dashboard tab | Sprint dropdown, donut chart canvas, bar chart canvas, chat area, input box |
| Sprints tab | Container for sprint issues table rendered by JavaScript |
| Resources tab | Container for team workload bar chart rendered by JavaScript |
| Reports tab | Container for summary and assignee report tables rendered by JavaScript |
| Script tags | Loads Chart.js from CDN, loads app.js, runs keep-alive ping every 4 minutes |

# CSS Classes

| Class | What it Styles |
| --- | --- |
| .app | Main flex container — sidebar + main area side by side |
| .sidebar | Left navigation panel — width, background, padding |
| .nav-link / .nav-link.active | Sidebar navigation items and highlighted active state |
| .tab-content / .hidden | Shows/hides tabs when switching between Dashboard, Sprints etc. |
| .chat-area | Scrollable message history area |
| .message.bot / .message.user | Chat bubble styling — white for bot, blue for user |
| .input-area | Bottom input box and send button container |
| .panel-card | White card containers used in Sprints, Resources, Reports tabs |
| .stat-box / .stat-num | KPI summary boxes showing Total, Done, Blocked counts |
| .pill-done/prog/todo/block | Colour-coded status badges on issue rows |
| .bar-wrap / .bar-fill | Horizontal progress bars in Resources tab |
| table / th / td | Issue table styling across all tabs |

# JavaScript Functions

| Function | What it Does |
| --- | --- |
| const API | Single variable holding Render backend URL — change this to switch environments |
| formatMarkdown(text) | Converts AI markdown replies (bold, bullets, headings) to HTML for display |
| addMessage(text, sender) | Creates and appends a chat bubble to the chat area |
| addExportMessage(text) | Creates a special bot message with a Download Excel button embedded |
| showTyping() / removeTyping() | Shows and removes the '...' typing indicator while AI is thinking |
| loadSprintDropdown() | Fetches all sprints from /sprints/list and populates the dropdown |
| loadSprintData() | Fetches data for the currently selected sprint from /sprint/by-id |
| onSprintChange() | Triggered when dropdown changes — reloads all tabs with new sprint data |
| showTab(name, e) | Switches between Dashboard, Sprints, Resources, Reports tabs |
| sendMessage() | Sends user message to /chat, shows reply, handles export action |
| renderCharts(force) | Draws donut and bar charts using Chart.js with sprint data |
| renderSprints() | Builds the full issues table for the Sprints tab |
| renderResources() | Builds the workload bar chart for the Resources tab |
| renderReports() | Builds summary and assignee tables for the Reports tab |
| exportExcel() | Captures chart images from canvas, sends to /export, triggers download |
| toggleRecording() | Starts/stops microphone recording for voice input |
| startRecording() | Accesses microphone, records audio, auto-stops after 30 seconds |
| transcribeAudio(blob) | Sends audio to /transcribe endpoint, puts result in input box |
| wakeAndLoad() | Pings Render on page load to wake server, retries up to 5 times |
| setInterval keep-alive | Pings /sprint every 4 minutes to prevent Render from sleeping |

# Project Files

| File | Purpose | Used By |
| --- | --- | --- |
| .env | Stores all secret API keys and credentials — never committed to GitHub | Local development only |
| .gitignore | Tells Git which files to exclude from GitHub — keeps .env safe | GitHub |
| requirements.txt | Lists all Python libraries needed — flask, groq, openpyxl etc. | Render (installs on deploy) |
| Procfile | Tells Render how to start the server: gunicorn server:app | Render |

# Command Examples

## Sprint Status

| Command Example | What AI Returns |
| --- | --- |
| show me the sprint status | Summary of sprint name, completion %, total/done/blocked counts |
| show me sprint status, assigned to and dates | Full issue list with assignees, due dates, start/end dates |
| list all issues in this sprint | Complete table of all tickets with status and assignee |
| which issues are blocked? | Filtered list of blocked tickets only |
| which issues are in progress? | Filtered list of in-progress tickets |
| which issues are done? | Filtered list of completed tickets |
| who has the most tickets assigned? | Workload breakdown per team member |
| what is the sprint completion percentage? | Completion % with done/total counts |
| how many issues are in this sprint? | Total count with breakdown by status |
| summarise this sprint | AI-written paragraph summary of sprint health |
| which tasks are at risk? | AI analysis of overdue or blocked items |
| show me all unassigned issues | List of tickets with no assignee |
| list all high priority issues | Filtered by priority field |
| what is the sprint end date? | Sprint start and end dates |
| give me a sprint overview | Full sprint health report in plain English |

## Creating Tickets

| Command Example | What Happens in Jira |
| --- | --- |
| create a task called "Fix login bug" in project SCRUM | New Task ticket created in selected sprint |
| create a bug called "Dashboard not loading" in SCRUM | New Bug ticket created in selected sprint |
| create a story called "Add user authentication" in SCRUM | New Story ticket created in selected sprint |
| create a task for fixing the payment gateway | AI infers project key and creates ticket |
| add a new ticket called "Performance optimisation" | New Task created in selected sprint |

## Updating Tickets

| Command Example | What Happens in Jira |
| --- | --- |
| mark SCRUM-1 as Done | Ticket status changed to Done |
| mark SCRUM-7 as In Progress | Ticket status changed to In Progress |
| mark SCRUM-2 as In Review | Ticket status changed to In Review |
| assign SCRUM-3 to balaji@gmail.com | Ticket reassigned to specified user |
| update SCRUM-1 summary to "New title here" | Ticket title updated |
| close SCRUM-5 | Ticket moved to Done status |

## Moving Tickets

| Command Example | What Happens in Jira |
| --- | --- |
| move SCRUM-1 to the next sprint | Ticket moved from current to next future sprint |
| move SCRUM-7 to the active sprint | Ticket moved to currently running sprint |
| move SCRUM-1 and SCRUM-2 to next sprint | Multiple tickets moved in one command |
| move all blocked issues to next sprint | AI identifies blocked tickets and moves them |

## Workload Management

| Command Example | What Happens |
| --- | --- |
| rebalance tasks across the team | AI calculates average load, moves tickets from overloaded to underloaded members |
| auto assign tasks evenly | Same as rebalance — distributes workload equally |
| who is overloaded? | Displays workload analysis without making changes |

## Exporting Data

| Command Example | What Happens |
| --- | --- |
| export to excel | AI confirms and shows Download Excel button in chat |
| download my sprint data | Same as above — triggers export flow |
| give me a spreadsheet | Same as above — triggers export flow |
| export | Single word triggers export detection |

| send sprint report to manager@company.com | HTML sprint report emailed to specified address |
| email sprint summary to balaji@gmail.com | Same — emails formatted report |
| send report to the team at team@company.com | Report sent to team email |
| Environment | URL |
| --- | --- |
| Live (deployed) | https://jirachatbotv2.netlify.app |
| Local development | http://127.0.0.1:5500/index.html |
| Backend API | https://your-render-url.onrender.com |
| Feature | Our Portal | Jira Cloud App |
| --- | --- | --- |
| Natural language chat | ✅ Full AI chat — ask anything | ❌ Not available |
| Sprint dashboard | ✅ Custom charts | ✅ Built-in boards |
| Issue creation | ✅ Via AI chat command | ✅ Via forms |
| Issue updates | ✅ Via AI chat command | ✅ Via UI clicks |
| Sprint switching | ✅ Dropdown in portal | ✅ Board switching |
| Resource utilisation | ✅ Auto-calculated bar chart | ⚠️ Limited view |
| Excel export | ✅ One click with charts | ⚠️ Basic CSV only |
| AI-powered reports | ✅ Ask AI to summarise | ❌ Not available |
| Voice commands | ✅ Speak your commands | ❌ Not available |
| Auto task rebalancing | ✅ AI redistributes workload | ❌ Manual only |
| Email sprint reports | ✅ Type command to send | ❌ Manual process |
| Agentic AI actions | ✅ AI takes actions autonomously | ❌ Not available |
| Custom branding | ✅ Fully customisable | ❌ Fixed Atlassian UI |
| Offline access | ✅ Cached in browser | ❌ Always needs internet |
| Mobile app | ❌ Browser only | ✅ Native mobile app |
| Push notifications | ❌ Not built | ✅ Built-in |
| Full Jira features | ⚠️ Core features only | ✅ Complete |
| Workflow management | ❌ Not built | ✅ Full workflows |
| User management | ❌ Not built | ✅ Full admin |
| Cost | ✅ Free / ~$10/month | 💰 Atlassian subscription |
| Feature | Our Portal | MS Teams Jira App |
| --- | --- | --- |
| Works inside Teams | ❌ Separate browser tab | ✅ Native Teams tab |
| Chat commands | ✅ Full AI natural language | ⚠️ Rule-based commands only |
| Sprint dashboard | ✅ Charts + AI analysis | ⚠️ Basic view |
| Create tickets via chat | ✅ Natural language | ✅ /jira command only |
| Resource utilisation | ✅ Auto-calculated | ❌ Not available |
| Excel export | ✅ With charts | ❌ Not built-in |
| Teams notifications | ❌ Not built | ✅ Built-in |
| Setup required | ✅ URL in browser | ⚠️ IT admin required |
| Cost | ✅ Free | 💰 Atlassian licence |
| Use Case | Best Tool |
| --- | --- |
| Quick sprint status check | Our Portal — type or speak the question |
| Creating and managing detailed epics | Jira Cloud — full feature set |
| Daily standup prep — who has what | Our Portal — Resources tab at a glance |
| Workflow automation rules | Jira Cloud — built-in automation |
| Sending sprint report to stakeholder | Our Portal — type 'send report to email' |
| Mobile issue updates on the go | Jira Cloud mobile app |
| AI analysis of sprint health | Our Portal — only option |
| Enterprise user management | Jira Cloud — admin panel |
| Rebalancing overloaded team members | Our Portal — auto rebalance command |
| Agile ceremonies and planning | Jira Cloud — full planning tools |
| Layer | Technology | Purpose | Cost |
| --- | --- | --- | --- |
| Frontend UI | HTML + CSS + Vanilla JS | Portal interface and charts | Free |
| Charts | Chart.js (CDN) | Donut and bar chart rendering | Free |
| Backend | Python Flask | API server and business logic | Free |
| Jira Integration | Jira REST API | Read/write Jira data | Free |
| AI Model | Groq Llama 3.3 70B | Natural language understanding and tool calling | Free |
| Speech to Text | Groq Whisper Large v3 | Voice command transcription | Free |
| Excel Export | openpyxl (Python) | Generate .xlsx files | Free |
| Frontend Hosting | Netlify | Serve HTML/CSS/JS files | Free |
| Backend Hosting | Render | Run Flask server | Free (sleeps) / $7/month |
| Source Control | GitHub | Code storage and deployment trigger | Free |
