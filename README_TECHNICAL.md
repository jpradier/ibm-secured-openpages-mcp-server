# GRC MCP Server — Technical Reference

A Model Context Protocol (MCP) server that enables AI agents to interact with IBM OpenPages GRC platform through a standardized interface. Supports both remote (HTTP) and local (stdio) modes for flexible deployment.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.9.4+-green.svg)](https://modelcontextprotocol.io/)

> **Note**: For the end-to-end guide on setting up the OpenPages AI Chat integration with watsonx Orchestrate and Code Engine, see the main [README.md](README.md).

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [First-Time Setup (Required for All Options)](#first-time-setup-required-for-all-options)
  - [Installation Options](#installation-options)
  - [Verify Installation](#verify-installation)
  - [Next Steps](#next-steps)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Authentication Methods](#authentication-methods)
  - [Object Types Configuration](#object-types-configuration)
- [Available Tools](#available-tools)
- [MCP Resources](#mcp-resources)
- [MCP Prompts](#mcp-prompts)
- [API Endpoints](#api-endpoints)
- [Using with AI Agents](#using-with-ai-agents)
- [AI Agent Instructions](#ai-agent-instructions)
- [Testing the Server](#testing-the-server)
- [Observability & Monitoring](#observability--monitoring)
- [Deployment Architectures](#deployment-architectures)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Known Issues](#known-issues)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Features

- **🔌 Dual Mode Operation**: Remote (HTTP) and Local (stdio) transport
- **🔐 Multiple Authentication Methods**: Basic, IBM Cloud IAM, MCSP, and CP4D
- **👤 Per-User Request Auth**: Ordered resolver over HTTP bearer, `op_auth_header`, and embedded-chat `op_auth_ticket` for true multi-tenant access
- **🛠️ Flexible Tool Exposure**: Choose between ontology-based (generic) or type-based (specific) tools
- **🎯 Dynamic Object Management**: Configurable tools for any OpenPages object type
- **📊 Advanced Query Tool**: SQL-like query execution with full OpenPages syntax support
- **📚 Ontology Resources**: Dynamic ontology discovery for AI agents
- **🚀 High Performance**: Compact ontology mode reduces response size by 70-90%
- **🔄 Real-time Schema Sync**: RabbitMQ-based automatic schema updates (no server restart needed)
- **🐳 Docker Support**: Containerized deployment with optional NGINX proxy
- **📈 Observability**: Built-in metrics, tracing, and structured logging
- **🔄 MCP Compliant**: Full protocol support (tools, resources, prompts)

## Quick Start

### Prerequisites

- **Python 3.12 or higher** ([Download](https://www.python.org/downloads/))
- **Docker and Docker Compose** (for containerized deployment)
- **Access to IBM OpenPages GRC instance** with:
  - Base URL
  - Valid credentials (username/password or API key)
  - Network connectivity to OpenPages server
- **Git** (to clone repository)

### First-Time Setup (Required for All Options)

Before using any deployment option, complete these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/IBM/ibm-openpages-mcp-server.git
   cd ibm-openpages-mcp-server 
   ```

2. **Configure environment variables**:
   
   Choose your configuration approach:
   
   **Quick Start** - Minimal configuration (recommended for first-time setup):
   ```bash
   # For Basic Authentication
   cp .env.example.minimal.basic .env
   
   # OR for Bearer Token Authentication
   cp .env.example.minimal.bearer .env
   
   # Edit .env with your OpenPages credentials
   ```
   
   **Full Configuration** - All available options:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
   
   **Minimum required settings in `.env`**:
   
   For Basic Authentication:
   ```env
   OPENPAGES_BASE_URL=https://your-instance.openpages.ibm.com
   OPENPAGES_AUTHENTICATION_TYPE=basic
   OPENPAGES_USERNAME=your-username
   OPENPAGES_PASSWORD=your-password
   ```
   
   For Bearer Token Authentication (recommended for production):
   ```env
   OPENPAGES_BASE_URL=https://your-instance.openpages.ibm.com
   OPENPAGES_AUTHENTICATION_TYPE=bearer
   OPENPAGES_AUTH_TOKEN=your-token
   ```

3. **Choose your installation option below**:
   - **Option 1: Docker (Remote/HTTP Mode)** - Production-ready, runs in background with optional monitoring
   - **Option 2: Local Python (Remote/HTTP Mode)** - Good for development and testing
   - **Option 3: Stdio Mode** - For desktop AI clients (Claude Desktop, Cline, etc.)

---

### Installation Options

#### Option 1: Docker Deployment (Remote/HTTP Mode) - Recommended for Production

Fastest way to get started with a production-ready remote server.

1. **Start the server**:
   ```bash
   # Standard deployment
   docker compose up -d
   
   # OR with full monitoring stack (Prometheus, Grafana, Jaeger)
   docker compose -f docker-compose.monitoring.yml up -d
   ```

2. **Verify it's running**:
   ```bash
   curl http://localhost:8080/health
   ```

3. **View logs**:
   ```bash
   docker compose logs -f openpages-mcp
   ```

4. **Stop the server**:
   ```bash
   docker compose down
   ```

#### Option 2: Local Python (Remote/HTTP Mode) - Good for Development

Run the HTTP server directly with Python.

1. **Install uv (Python package installer)**:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

3. **Start the server**:
   ```bash
   python main.py
   ```
   
   Server runs at `http://localhost:8080` (or `PORT` from `.env`).

#### Option 3: Stdio Mode (For Desktop AI Clients)

Run as a subprocess communicating via standard input/output. Perfect for desktop AI assistants like Claude Desktop, Cline, Roo Code, etc.

1. **Install dependencies**:
   ```bash
   uv pip install -e .
   ```

2. **Run in stdio mode**:
   ```bash
   python main.py --mode stdio
   # Or using environment variable:
   # MCP_SERVER_MODE=stdio python main.py
   ```

3. **Configure your AI client**:
   
   See [Using with AI Agents](#using-with-ai-agents) for configuration examples.

---

### Verify Installation

Test that your server is working correctly:

```bash
# For Remote/HTTP mode:
curl http://localhost:8080/health
# Response: {"status":"healthy",...}

# Check MCP endpoint:
curl http://localhost:8080/mcp
```

### Next Steps

- **Configure your AI Agent**: See [Using with AI Agents](#using-with-ai-agents) for Claude Desktop, Cline, and other clients
- **Set Up System Prompt**: See [AI Agent Instructions](#ai-agent-instructions) for essential agent guidelines
- **Explore Tools**: See [Available Tools](#available-tools) to understand what the server can do
- **Explore Resources**: See [MCP Resources](#mcp-resources) to access OpenPages ontology and schemas

---

## Configuration

### Environment Variables

Key configuration options in `.env`:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENPAGES_BASE_URL` | OpenPages instance URL | - | Yes |
| `OPENPAGES_AUTHENTICATION_TYPE` | Auth method: `basic`, `bearer`, `ibm_cloud`, `mcsp`, `cp4d` | `basic` | Yes |
| `OPENPAGES_USERNAME` | Username (for basic auth) | - | If basic |
| `OPENPAGES_PASSWORD` | Password (for basic auth) | - | If basic |
| `OPENPAGES_AUTH_TOKEN` | Bearer token | - | If bearer |
| `MCP_SERVER_MODE` | Server mode: `http` or `stdio` | `http` | No |
| `PORT` | HTTP server port | `8080` | No |
| `MCP_API_TOKEN` | Required bearer token to access MCP endpoints | - | No |
| `TOOL_EXPOSURE_MODE` | `ontology` (generic) or `type_based` (specific) | `ontology` | No |
| `ALLOWED_OBJECT_TYPES` | Comma-separated object types for type_based mode | See below | No |

See [Configuration Documentation](docs/CONFIGURATION_DEFAULTS.md) for all options.

### Authentication Methods

The server supports multiple authentication methods:

1. **Basic Authentication** (`basic`): Standard username/password
2. **Bearer Token** (`bearer`): Direct JWT or access token (Recommended)
3. **IBM Cloud IAM** (`ibm_cloud`): API key with automatic token management
4. **MCSP** (`mcsp`): Multi-Cloud SaaS Platform authentication
5. **Cloud Pak for Data** (`cp4d`): CP4D username and API key

See [Authentication Documentation](docs/AUTHENTICATION.md) for detailed setup for each method.

### Per-User Request Authentication

In addition to static instance credentials, the server supports per-request user authentication via:
1. **HTTP Authorization Header**: `Bearer <token>` passed in incoming requests
2. **`op_auth_header` parameter**: Explicit authorization header
3. **`op_auth_ticket` parameter**: Embedded-chat single-use authentication ticket

---

## Available Tools

The server provides two tool exposure modes:

### 1. Ontology Mode (`TOOL_EXPOSURE_MODE=ontology`) — Default

Generic tools that operate dynamically on any OpenPages object type:

- `execute_openpages_query`: Execute OpenPages query statements
- `get_resource`: Read resources (schemas, catalog, relationships)
- `list_resources`: List available resources
- `openpages_associate_objects`: Manage parent/child associations
- `echo`: Health/echo check tool

### 2. Type-Based Mode (`TOOL_EXPOSURE_MODE=type_based`)

Generates dedicated CRUD tools for configured object types (e.g., `get_risk`, `create_control`, `update_issue`).

---

## MCP Resources

Available resources via `openpages://` URI scheme:

- `openpages://catalog/object_types`: List of all available object types
- `openpages://catalog/relationships`: Entity relationship catalog
- `openpages://schema/{ObjectType}`: Schema definition for a specific type (compact or full)

---

## Testing the Server

Run automated tests:

```bash
# Run unit tests
PYTHONPATH=. pytest tests/test_token_validator.py

# Run all tests
PYTHONPATH=. pytest
```

---

## Observability & Monitoring

The server includes OpenTelemetry instrumentation:
- Prometheus metrics at `/metrics`
- Health endpoints at `/health` and `/live`
- Distributed tracing with OTLP export

See [Observability Documentation](docs/OBSERVABILITY.md) for details.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code standards, pull requests, and development workflows.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
