# Context Normalization Layer - Implementation Plan

## Overview

A multi-adapter MCP (Model Context Protocol) framework that acts as a bridge between AI applications and existing systems. This package provides standardized access to Code Repositories, Databases, and Sprint Planning Tools through the MCP protocol.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (Claude, etc.)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────────────┐
│              Your Context Normalization Package              │
│  ┌──────────────┬──────────────┬────────────────────────┐  │
│  │   Adapters   │   Adapters   │       Adapters         │  │
│  │  (GitHub)    │  (Postgres)  │      (Jira)            │  │
│  └──────┬───────┴──────┬───────┴──────────┬─────────────┘  │
│         │              │                  │                │
│         └──────────────┼──────────────────┘                │
│                        ▼                                    │
│              ┌──────────────────┐                          │
│              │  Normalization   │  ← Transforms to MCP     │
│              │     Engine       │     primitives           │
│              └────────┬─────────┘                          │
└───────────────────────┼─────────────────────────────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      [GitHub API] [DB Connection] [Jira API]
```

## Phase 1: Foundation (Week 1-2)

### 1.1 Core Interfaces

#### Adapter Interface

```typescript
interface SystemAdapter {
  readonly systemType: string;
  readonly version: string;
  
  // Discovery
  getCapabilities(): AdapterCapabilities;
  
  // Resources (read-only data)
  listResources(): Promise<Resource[]>;
  readResource(uri: string): Promise<ResourceContent>;
  
  // Tools (actions)
  listTools(): Promise<Tool[]>;
  executeTool(name: string, args: any): Promise<ToolResult>;
  
  // Connection management
  connect(config: AdapterConfig): Promise<void>;
  disconnect(): Promise<void>;
  healthCheck(): Promise<HealthStatus>;
}
```

#### Adapter Capabilities

```typescript
interface AdapterCapabilities {
  resources: boolean;
  tools: boolean;
  prompts: boolean;  // Future
  realTimeUpdates: boolean;  // Webhooks/SSE support
}
```

### 1.2 Configuration Schema

```yaml
# config.yaml
adapters:
  - type: github
    name: main-repo
    config:
      token: ${GITHUB_TOKEN}
      owner: myorg
      repos: ["repo1", "repo2"]
    enabled: true
    
  - type: postgresql
    name: prod-db
    config:
      connectionString: ${DB_URL}
      allowedTables: ["users", "projects"]
      readOnly: true
      
  - type: jira
    name: sprint-board
    config:
      host: https://mycompany.atlassian.net
      project: PROJ
      auth:
        type: token
        token: ${JIRA_TOKEN}
```

### 1.3 Package Structure

```
context-normalization-layer/
├── packages/
│   ├── core/                    # Core engine & MCP server
│   ├── adapters/
│   │   ├── github-adapter/      # GitHub implementation
│   │   ├── gitlab-adapter/      # GitLab implementation
│   │   ├── postgres-adapter/    # PostgreSQL implementation
│   │   ├── mysql-adapter/       # MySQL implementation
│   │   ├── jira-adapter/        # Jira implementation
│   │   ├── linear-adapter/       # Linear implementation
│   │   └── adapter-sdk/         # Interface definitions
│   └── cli/                     # Setup & configuration tool
├── examples/
│   ├── basic-setup/
│   └── advanced-config/
└── docs/
```

## Phase 2: Adapter Development (Week 3-6)

### 2.1 Code Repository Adapter (GitHub)

#### Resources

| Resource URI | Description |
|--------------|-------------|
| `repo://{owner}/{repo}/files/{path}` | File contents |
| `repo://{owner}/{repo}/commits` | Commit history |
| `repo://{owner}/{repo}/pulls` | Pull requests |
| `repo://{owner}/{repo}/issues` | Issues |
| `repo://{owner}/{repo}/branches` | Branch list |

#### Tools

- `github_search_code` - Search across repos
- `github_create_pr` - Create pull request
- `github_review_pr` - Review/comment on PR
- `github_get_file` - Fetch file with line numbers
- `github_list_directory` - Browse repo structure

### 2.2 Database Adapter (PostgreSQL)

#### Resources

| Resource URI | Description |
|--------------|-------------|
| `db://{connection}/schema` | Database schema |
| `db://{connection}/tables/{table}/structure` | Table structure |
| `db://{connection}/tables/{table}/sample` | Sample data |

#### Tools

- `db_query` - Execute SELECT queries (configurable)
- `db_explain_query` - Get query execution plan
- `db_list_tables` - List available tables
- `db_describe_table` - Get column info

#### Safety Considerations

- Read-only by default
- Query whitelist/blacklist
- Row limits
- Timeout controls

### 2.3 Sprint Planning Adapter (Jira)

#### Resources

| Resource URI | Description |
|--------------|-------------|
| `sprint://{board}/backlog` | Product backlog |
| `sprint://{board}/active` | Active sprint |
| `sprint://{board}/issues/{key}` | Issue details |

#### Tools

- `jira_create_issue` - Create ticket
- `jira_update_status` - Move ticket through workflow
- `jira_add_comment` - Comment on issue
- `jira_search_issues` - JQL search
- `jira_get_sprint_report` - Sprint metrics

## Phase 3: Normalization Engine (Week 4-5)

### 3.1 Cross-System Linking

Enable relationships across adapters:

```typescript
interface EntityLink {
  source: {
    adapter: string;
    resourceUri: string;
  };
  target: {
    adapter: string;
    resourceUri: string;
  };
  relationship: "implements" | "fixes" | "related";
  confidence: number;  // AI-detected vs manual
}
```

### 3.2 Unified Query Interface

```typescript
interface CrossSystemQuery {
  // Example: "Find all PRs related to Jira tickets in current sprint"
  filter: {
    adapters: ["github", "jira"];
    relationships: ["implements"];
    conditions: [...];
  };
}
```

## Phase 4: Developer Experience (Week 6-8)

### 4.1 CLI Tool

```bash
# Initialize new project
npx context-layer init my-project

# Add adapters interactively
npx context-layer add github
npx context-layer add postgres
npx context-layer add jira

# Validate configuration
npx context-layer validate

# Test connections
npx context-layer test-connection github
```

### 4.2 Configuration Wizard

Interactive setup for:
- OAuth flows (GitHub, Jira)
- Database connection strings
- Permission scoping (read-only vs read-write)
- Resource filtering (which tables/repos/projects)

### 4.3 MCP Server Generator

```bash
# Generate MCP server from config
npx context-layer build

# Options
npx context-layer build --transport stdio    # Local
npx context-layer build --transport http     # Remote
npx context-layer build --watch             # Dev mode
```

## Phase 5: Distribution & Usage (Week 8+)

### 5.1 Usage Patterns

#### As a Library

```typescript
import { ContextLayer } from '@context-layer/core';

const layer = new ContextLayer({
  configPath: './context-layer.yaml'
});

await layer.start();
```

#### As a CLI

```bash
context-layer serve --config ./config.yaml
```

#### Docker Container

```bash
docker run -v $(pwd)/config.yaml:/config.yaml context-layer:latest
```

## Implementation Priority

| Phase | Priority | Effort | Value |
|-------|----------|--------|-------|
| 1. Core interfaces & config | 🔴 High | Medium | Critical |
| 2a. GitHub adapter | 🔴 High | Medium | High |
| 2b. PostgreSQL adapter | 🟡 Medium | Medium | High |
| 2c. Jira adapter | 🟡 Medium | Medium | Medium |
| 3. Normalization engine | 🟢 Low | High | Medium |
| 4. CLI & DX | 🟡 Medium | Medium | High |
| 5. Distribution | 🟢 Low | Low | Medium |

## Key Design Decisions

1. **Transport**: STDIO for local, HTTP for remote?
2. **Auth**: Environment variables, keychain, or secret manager?
3. **Extensibility**: Plugin architecture for custom adapters?
4. **Caching**: Cache resources locally? For how long?
5. **Multi-tenancy**: One server per user or shared with permissions?

## Next Steps

1. **Deep-dive on Phase 1** - Design the core interfaces in detail
2. **Start Phase 2** - Pick one adapter and design its MCP mapping
3. **Create a PoC** - Build a minimal version with one system
4. **Review the architecture** - Refine based on team constraints

---

*Last updated: February 11, 2026*