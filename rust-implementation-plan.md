# Context Normalization Layer - Rust Implementation Plan

## Overview

A multi-adapter MCP (Model Context Protocol) framework written in Rust, acting as a bridge between AI applications and existing systems. Provides standardized access to Code Repositories, Databases, and Sprint Planning Tools through the MCP protocol with type safety, performance, and reliability.

## Why Rust?

- **Type Safety**: Catch errors at compile time with Rust's ownership system
- **Performance**: Zero-cost abstractions and efficient async runtime
- **Reliability**: No null pointer exceptions or data races
- **Ecosystem**: Excellent async/await support, serialization (serde), HTTP clients (reqwest), and database drivers
- **Deployment**: Single binary with no runtime dependencies

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Host (Claude, etc.)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol
┌─────────────────────▼───────────────────────────────────────┐
│              Context Normalization Package (Rust)            │
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

## Rust Technology Stack

| Component | Crate | Purpose |
|-----------|-------|---------|
| Async Runtime | `tokio` | Async/await runtime |
| Serialization | `serde` + `serde_json` | JSON/YAML handling |
| Configuration | `config` + `serde_yaml` | Config management |
| HTTP Client | `reqwest` | API calls |
| Database | `sqlx` | Async PostgreSQL |
| CLI | `clap` | Command-line interface |
| Error Handling | `thiserror` | Custom error types |
| Logging | `tracing` | Structured logging |
| Testing | `tokio::test` | Async testing |
| MCP Protocol | Custom + `serde_json` | MCP JSON-RPC |

## Phase 1: Foundation (Week 1-2)

### 1.1 Core Traits (Rust Interfaces)

```rust
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[async_trait]
pub trait SystemAdapter: Send + Sync {
    fn system_type(&self) -> &str;
    fn version(&self) -> &str;
    
    // Discovery
    async fn get_capabilities(&self) -> AdapterCapabilities;
    
    // Resources (read-only data)
    async fn list_resources(&self) -> Result<Vec<Resource>, AdapterError>;
    async fn read_resource(&self, uri: &str) -> Result<ResourceContent, AdapterError>;
    
    // Tools (actions)
    async fn list_tools(&self) -> Result<Vec<Tool>, AdapterError>;
    async fn execute_tool(&self, name: &str, args: serde_json::Value) 
        -> Result<ToolResult, AdapterError>;
    
    // Connection management
    async fn connect(&mut self, config: AdapterConfig) -> Result<(), AdapterError>;
    async fn disconnect(&mut self) -> Result<(), AdapterError>;
    async fn health_check(&self) -> Result<HealthStatus, AdapterError>;
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AdapterCapabilities {
    pub resources: bool,
    pub tools: bool,
    pub prompts: bool,
    pub real_time_updates: bool,
}

#[derive(Debug, thiserror::Error)]
pub enum AdapterError {
    #[error("Connection failed: {0}")]
    ConnectionError(String),
    #[error("Resource not found: {0}")]
    NotFound(String),
    #[error("Invalid configuration: {0}")]
    ConfigError(String),
    #[error("Tool execution failed: {0}")]
    ToolError(String),
}
```

### 1.2 Configuration Schema (Rust + YAML)

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
      connection_string: ${DB_URL}
      allowed_tables: ["users", "projects"]
      read_only: true
      
  - type: jira
    name: sprint-board
    config:
      host: https://mycompany.atlassian.net
      project: PROJ
      auth:
        type: token
        token: ${JIRA_TOKEN}
```

```rust
use config::{Config, ConfigError, Environment, File};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct AppConfig {
    pub adapters: Vec<AdapterDefinition>,
}

#[derive(Debug, Deserialize)]
pub struct AdapterDefinition {
    pub r#type: String,
    pub name: String,
    pub config: HashMap<String, serde_json::Value>,
    pub enabled: bool,
}

impl AppConfig {
    pub fn new() -> Result<Self, ConfigError> {
        let s = Config::builder()
            .add_source(File::with_name("config"))
            .add_source(Environment::with_prefix("APP"))
            .build()?;
        
        s.try_deserialize()
    }
}
```

### 1.3 Project Structure

```
context-normalization-layer/
├── Cargo.toml                 # Workspace manifest
├── crates/
│   ├── core/                  # Core engine & MCP server
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── server.rs      # MCP server implementation
│   │       └── normalization.rs
│   ├── adapters/
│   │   ├── github-adapter/    # GitHub implementation
│   │   ├── postgres-adapter/  # PostgreSQL implementation
│   │   ├── jira-adapter/      # Jira implementation
│   │   └── adapter-sdk/       # Interface definitions
│   │       ├── Cargo.toml
│   │       └── src/
│   │           ├── lib.rs
│   │           ├── traits.rs   # SystemAdapter trait
│   │           └── types.rs    # Shared types
│   └── cli/                   # CLI tool
│       ├── Cargo.toml
│       └── src/
│           └── main.rs
├── examples/
│   ├── basic-setup/
│   └── advanced-config/
└── docs/
```

### 1.4 Workspace Cargo.toml

```toml
[workspace]
members = [
    "crates/core",
    "crates/adapters/adapter-sdk",
    "crates/adapters/github-adapter",
    "crates/adapters/postgres-adapter",
    "crates/adapters/jira-adapter",
    "crates/cli",
]

[workspace.dependencies]
tokio = { version = "1.35", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
async-trait = "0.1"
thiserror = "1.0"
anyhow = "1.0"
tracing = "0.1"
config = "0.14"
serde_yaml = "0.9"
reqwest = { version = "0.11", features = ["json"] }
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres"] }
clap = { version = "4.4", features = ["derive"] }
```

## Phase 2: Adapter Development (Week 3-6)

### 2.1 GitHub Adapter

```rust
use adapter_sdk::{SystemAdapter, AdapterConfig, Resource, Tool};
use async_trait::async_trait;
use reqwest::Client;

pub struct GitHubAdapter {
    client: Client,
    token: String,
    owner: String,
    repos: Vec<String>,
}

#[async_trait]
impl SystemAdapter for GitHubAdapter {
    fn system_type(&self) -> &str { "github" }
    fn version(&self) -> &str { "0.1.0" }
    
    async fn list_resources(&self) -> Result<Vec<Resource>, AdapterError> {
        // List repos, PRs, issues as resources
        todo!()
    }
    
    async fn execute_tool(&self, name: &str, args: serde_json::Value) 
        -> Result<ToolResult, AdapterError> {
        match name {
            "github_search_code" => self.search_code(args).await,
            "github_create_pr" => self.create_pr(args).await,
            "github_get_file" => self.get_file(args).await,
            _ => Err(AdapterError::ToolError(format!("Unknown tool: {}", name)))
        }
    }
    
    async fn connect(&mut self, config: AdapterConfig) -> Result<(), AdapterError> {
        self.token = config.get_required("token")?;
        self.owner = config.get_required("owner")?;
        self.repos = config.get_array("repos")?;
        Ok(())
    }
    
    // ... other methods
}
```

**Resources:**
- `repo://{owner}/{repo}/files/{path}` - File contents
- `repo://{owner}/{repo}/commits` - Commit history
- `repo://{owner}/{repo}/pulls` - Pull requests

**Tools:**
- `github_search_code` - Search across repos
- `github_create_pr` - Create pull request
- `github_get_file` - Fetch file with line numbers

### 2.2 PostgreSQL Adapter

```rust
use sqlx::PgPool;

pub struct PostgresAdapter {
    pool: Option<PgPool>,
    allowed_tables: Vec<String>,
    read_only: bool,
}

#[async_trait]
impl SystemAdapter for PostgresAdapter {
    async fn execute_tool(&self, name: &str, args: serde_json::Value) 
        -> Result<ToolResult, AdapterError> {
        match name {
            "db_query" => {
                if self.read_only {
                    self.execute_read_query(args).await
                } else {
                    Err(AdapterError::ToolError("Write operations disabled".to_string()))
                }
            }
            "db_list_tables" => self.list_tables().await,
            _ => Err(AdapterError::ToolError(format!("Unknown tool: {}", name)))
        }
    }
    
    async fn connect(&mut self, config: AdapterConfig) -> Result<(), AdapterError> {
        let connection_string: String = config.get_required("connection_string")?;
        self.pool = Some(PgPool::connect(&connection_string).await
            .map_err(|e| AdapterError::ConnectionError(e.to_string()))?);
        Ok(())
    }
}
```

### 2.3 Jira Adapter

```rust
pub struct JiraAdapter {
    client: Client,
    host: String,
    project: String,
    token: String,
}

#[async_trait]
impl SystemAdapter for JiraAdapter {
    async fn list_resources(&self) -> Result<Vec<Resource>, AdapterError> {
        // List sprints, issues as resources
        todo!()
    }
    
    async fn execute_tool(&self, name: &str, args: serde_json::Value) 
        -> Result<ToolResult, AdapterError> {
        match name {
            "jira_create_issue" => self.create_issue(args).await,
            "jira_search_issues" => self.search_issues(args).await,
            _ => Err(AdapterError::ToolError(format!("Unknown tool: {}", name)))
        }
    }
}
```

## Phase 3: Normalization Engine (Week 4-5)

### 3.1 Cross-System Linking

```rust
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct EntityLink {
    pub id: Uuid,
    pub source: LinkEndpoint,
    pub target: LinkEndpoint,
    pub relationship: RelationshipType,
    pub confidence: f32,  // 0.0 - 1.0
}

#[derive(Debug, Clone)]
pub struct LinkEndpoint {
    pub adapter: String,
    pub resource_uri: String,
}

#[derive(Debug, Clone, Copy)]
pub enum RelationshipType {
    Implements,
    Fixes,
    Related,
}

pub struct NormalizationEngine {
    links: Vec<EntityLink>,
    adapters: HashMap<String, Box<dyn SystemAdapter>>,
}

impl NormalizationEngine {
    pub async fn resolve_cross_system_query(&self, query: CrossSystemQuery) 
        -> Result<Vec<LinkedResource>, AdapterError> {
        // Query across multiple adapters and resolve links
        todo!()
    }
}
```

### 3.2 Unified Query Interface

```rust
#[derive(Debug, Deserialize)]
pub struct CrossSystemQuery {
    pub adapters: Vec<String>,
    pub relationships: Vec<RelationshipType>,
    pub conditions: Vec<QueryCondition>,
}

#[derive(Debug, Deserialize)]
pub struct QueryCondition {
    pub field: String,
    pub operator: Operator,
    pub value: serde_json::Value,
}
```

## Phase 4: Developer Experience (Week 6-8)

### 4.1 CLI Tool

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "context-layer")]
#[command(about = "Context Normalization Layer CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize new project
    Init {
        name: String,
    },
    /// Add an adapter
    Add {
        #[arg(value_enum)]
        adapter_type: AdapterType,
    },
    /// Validate configuration
    Validate,
    /// Test connection to adapter
    TestConnection {
        adapter: String,
    },
    /// Build and serve MCP server
    Serve {
        #[arg(short, long, default_value = "config.yaml")]
        config: String,
        #[arg(short, long, default_value = "stdio")]
        transport: String,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    
    match cli.command {
        Commands::Init { name } => init_project(&name).await?,
        Commands::Add { adapter_type } => add_adapter(adapter_type).await?,
        Commands::Validate => validate_config().await?,
        Commands::TestConnection { adapter } => test_adapter(&adapter).await?,
        Commands::Serve { config, transport } => serve(&config, &transport).await?,
    }
    
    Ok(())
}
```

### 4.2 MCP Server Implementation

```rust
use serde_json::Value;
use tokio::io::{stdin, stdout};

pub struct McpServer {
    engine: NormalizationEngine,
}

impl McpServer {
    pub async fn run_stdio(&self) -> anyhow::Result<()> {
        let mut reader = BufReader::new(stdin());
        let mut writer = stdout();
        
        loop {
            let mut line = String::new();
            reader.read_line(&mut line).await?;
            
            let request: McpRequest = serde_json::from_str(&line)?;
            let response = self.handle_request(request).await;
            
            writeln!(writer, "{}", serde_json::to_string(&response)?).await?;
            writer.flush().await?;
        }
    }
    
    async fn handle_request(&self, request: McpRequest) -> McpResponse {
        match request.method.as_str() {
            "initialize" => self.handle_initialize(request).await,
            "resources/list" => self.handle_list_resources(request).await,
            "tools/list" => self.handle_list_tools(request).await,
            "tools/call" => self.handle_tool_call(request).await,
            _ => McpResponse::error(request.id, "Method not found".to_string()),
        }
    }
}
```

## Phase 5: Distribution & Usage (Week 8+)

### 5.1 As a Library

```rust
use context_layer_core::{ContextLayer, Config};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let config = Config::from_file("./context-layer.yaml")?;
    let layer = ContextLayer::new(config).await?;
    
    layer.start().await?;
    
    Ok(())
}
```

### 5.2 As a CLI

```bash
# Install
cargo install context-layer-cli

# Initialize
context-layer init my-project

# Add adapters
context-layer add github
context-layer add postgres

# Serve
context-layer serve --config config.yaml --transport stdio
```

### 5.3 Docker Distribution

```dockerfile
FROM rust:1.75 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates
COPY --from=builder /app/target/release/context-layer /usr/local/bin/
ENTRYPOINT ["context-layer"]
CMD ["serve", "--config", "/config.yaml"]
```

```bash
docker build -t context-layer:latest .
docker run -v $(pwd)/config.yaml:/config.yaml context-layer:latest
```

## Implementation Priority

| Phase | Priority | Effort | Value |
|-------|----------|--------|-------|
| 1. Core traits & config | 🔴 High | Medium | Critical |
| 2a. GitHub adapter | 🔴 High | Medium | High |
| 2b. PostgreSQL adapter | 🟡 Medium | Medium | High |
| 2c. Jira adapter | 🟡 Medium | Medium | Medium |
| 3. Normalization engine | 🟢 Low | High | Medium |
| 4. CLI & DX | 🟡 Medium | Medium | High |
| 5. Distribution | 🟢 Low | Low | Medium |

## Key Rust Design Decisions

1. **Async Runtime**: Tokio for async/await
2. **Error Handling**: `thiserror` for custom errors, `anyhow` for application errors
3. **Configuration**: `config` crate with environment variable support
4. **Serialization**: `serde` with JSON/YAML support
5. **Traits**: `async_trait` for async traits
6. **Testing**: `tokio::test` with `wiremock` for HTTP mocking
7. **Database**: `sqlx` for compile-time checked queries
8. **CLI**: `clap` with derive macros
9. **Logging**: `tracing` for structured logging

## Next Steps

1. Set up Rust workspace with Cargo
2. Implement `adapter-sdk` crate with core traits
3. Create first GitHub adapter
4. Write integration tests with mocked APIs
5. Build CLI scaffolding
6. Create MCP server skeleton

---

*Ported to Rust: February 14, 2026*

---

# 2-Week Rust Learning Plan

## Goal
Learn Rust fundamentals well enough to contribute to the Context Normalization Layer project.

---

## Week 1: Rust Foundations

### Day 1: Environment & Basics
**Morning (2 hours)**
- Install Rust via rustup: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Set up IDE (VS Code + rust-analyzer or RustRover)
- Create first project: `cargo new hello_rust`
- Read: [The Rust Book - Ch 1-3](https://doc.rust-lang.org/book/)

**Afternoon (2 hours)**
- Variables, mutability, data types
- Functions and control flow
- Practice: Write a CLI calculator

**Resources:**
- [Rust Book Ch 1-3](https://doc.rust-lang.org/book/)
- [Rustlings exercises](https://github.com/rust-lang/rustlings)

### Day 2: Ownership & Borrowing
**Morning (2 hours)**
- Ownership rules
- Move semantics
- Borrowing (&T, &mut T)

**Afternoon (2 hours)**
- Lifetimes introduction
- Practice: Build a string reverser with proper borrowing

**Key Concepts:**
- Every value has an owner
- Only one mutable reference OR multiple immutable references
- References must not outlive the data they reference

### Day 3: Structs, Enums & Pattern Matching
**Morning (2 hours)**
- Structs and methods
- Enums and Option/Result
- Pattern matching with `match`

**Afternoon (2 hours)**
- Error handling with Result
- The `?` operator
- Practice: Build a simple file reader with error handling

### Day 4: Collections & Iterators
**Morning (2 hours)**
- Vec, HashMap, HashSet
- String vs &str
- Iterators and combinators (map, filter, collect)

**Afternoon (2 hours)**
- Practice: Process a CSV file using iterators
- Read: [Rust Book Ch 8](https://doc.rust-lang.org/book/ch08-00-common-collections.html)

### Day 5: Traits & Generics
**Morning (2 hours)**
- Defining and implementing traits
- Generic types and functions
- Trait bounds

**Afternoon (2 hours)**
- Practice: Build a generic `Stack<T>` and `Queue<T>`
- Implement custom traits (Display, Debug)

### Day 6-7: Weekend Project
**Build: HTTP Client CLI Tool**
- Use `reqwest` crate
- Fetch JSON from an API
- Parse with `serde_json`
- Handle errors gracefully

---

## Week 2: Async Rust & Project Prep

### Day 8: Modules, Crates & Testing
**Morning (2 hours)**
- Module system (mod, pub, use)
- Cargo workspaces
- Publishing crates

**Afternoon (2 hours)**
- Unit testing with `#[test]`
- Integration testing
- Practice: Write tests for your HTTP client

### Day 9: Async/Await Fundamentals
**Morning (2 hours)**
- Why async? (concurrency vs parallelism)
- Futures and the async runtime
- Tokio basics

**Afternoon (2 hours)**
- Spawning tasks
- `async fn` and `.await`
- Practice: Convert HTTP client to async

**Key Code:**
```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let resp = reqwest::get("https://api.github.com/users/octocat").await?;
    println!("{:#?}", resp.json::<serde_json::Value>().await?);
    Ok(())
}
```

### Day 10: Advanced Async & Error Handling
**Morning (2 hours)**
- `thiserror` for custom errors
- `anyhow` for application errors
- Converting errors

**Afternoon (2 hours)**
- Channels (mpsc, oneshot)
- Shared state (Arc, Mutex)
- Practice: Build a concurrent URL fetcher

### Day 11: Serialization & Configuration
**Morning (2 hours)**
- Serde derive macros
- JSON and YAML parsing
- Custom serializers

**Afternoon (2 hours)**
- Environment variables
- Configuration files
- Practice: Build a config loader with validation

### Day 12: CLI Development
**Morning (2 hours)**
- `clap` derive macros
- Subcommands and arguments
- Environment variables integration

**Afternoon (2 hours)**
- Practice: Build a full-featured CLI tool
- Add logging with `tracing`

### Day 13-14: Capstone Project
**Build: Mini MCP Server**
- Create a simple MCP server framework
- Implement one resource (e.g., file system)
- Implement one tool (e.g., file reader)
- Use stdio transport
- Write comprehensive tests

**Stretch Goals:**
- Add async trait support
- Implement multiple adapters
- Add configuration via YAML

---

## Daily Practice Routine (30 min/day)

1. **Rustlings** (15 min): Complete 5-10 exercises
2. **Exercism Rust Track** (15 min): Solve one problem

## Resources

### Essential
- [The Rust Book](https://doc.rust-lang.org/book/) - Free, comprehensive
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/) - Learn by coding
- [Rustlings](https://github.com/rust-lang/rustlings) - Interactive exercises

### Async
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial) - Essential for async
- [Async Rust Book](https://rust-lang.github.io/async-book/) - Deep dive

### Practice
- [Exercism Rust](https://exercism.org/tracks/rust) - Coding challenges
- [Rust Codewars](https://www.codewars.com/?language=rust) - Kata practice
- [Advent of Code](https://adventofcode.com/) - Yearly challenges

### Community
- [Rust Discord](https://discord.gg/rust-lang)
- [r/rust](https://reddit.com/r/rust)
- [This Week in Rust](https://this-week-in-rust.org/) - Newsletter

## Success Metrics

By end of Week 2, you should be able to:
- [ ] Write async Rust code with Tokio
- [ ] Create and use traits effectively
- [ ] Handle errors with `Result` and custom types
- [ ] Build a CLI with clap
- [ ] Parse JSON/YAML with serde
- [ ] Write unit and integration tests
- [ ] Understand ownership and borrowing
- [ ] Contribute to the Context Normalization Layer codebase

## Pre-Reading (Before Starting)

Read these articles to understand why Rust:
- [Why Rust?](https://www.rust-lang.org/)
- [Rust vs Go/TypeScript comparisons](https://bitfieldconsulting.com/posts/rust-vs-go)
- [Zero-cost abstractions](https://boats.gitlab.io/blog/post/zero-cost-abstractions/)

---

**Total Time Commitment:** ~40 hours (20 hrs/week)

**Outcome:** Ready to contribute to Rust projects with confidence!
