# Context Normalization Layer

A multi-adapter MCP (Model Context Protocol) framework written in Rust.

## Quick Start

### Prerequisites

- Rust 1.75+ (install via [rustup](https://rustup.rs/))
- Cargo (comes with Rust)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/context-normalization-layer
cd context-normalization-layer

# Build the project
cargo build --release

# Install the CLI
cargo install --path crates/cli
```

### Usage

```bash
# Initialize a new project
context-layer init my-project
cd my-project

# Add adapters
context-layer add github
context-layer add postgresql
context-layer add jira

# Edit config.yaml to add your credentials

# Validate configuration
context-layer validate

# Start the MCP server
context-layer serve
```

## Project Structure

```
context-normalization-layer/
├── Cargo.toml                 # Workspace manifest
├── crates/
│   ├── core/                  # Core engine & MCP server
│   ├── adapters/
│   │   ├── adapter-sdk/       # Interface definitions
│   │   ├── github-adapter/    # GitHub implementation
│   │   ├── postgres-adapter/  # PostgreSQL implementation
│   │   └── jira-adapter/      # Jira implementation
│   └── cli/                   # CLI tool
└── examples/                  # Example configurations
```

## Development

```bash
# Run tests
cargo test

# Run specific crate tests
cargo test -p context-layer-core
cargo test -p github-adapter

# Build in debug mode
cargo build

# Run the CLI
cargo run -p context-layer-cli -- --help
```

## Architecture

See `rust-implementation-plan.md` for detailed architecture and implementation plan.

## License

MIT OR Apache-2.0
