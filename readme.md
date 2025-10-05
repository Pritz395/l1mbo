# 🔥 Limbo - MCP Aggregator

> Give your AI assistant extra limbs. Dynamically load MCP tools on-demand.

[![Docker](https://img.shields.io/badge/Docker-pr33th4m%2Fl1mbo-blue?logo=docker)](https://hub.docker.com/r/pr33th4m/l1mbo)
[![License](https://img.shields.io/badge/License-AGPL%203.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)

Limbo is a meta-MCP server that lets AI assistants install and manage their own tools dynamically. No restarts, no manual configuration—just ask.

## 🎯 The Problem

Setting up Model Context Protocol (MCP) tools is tedious:

- Edit config files manually
- Restart everything for changes
- Manage 10+ server configurations
- Debug connection issues repeatedly

**It's like requiring your AI to request permission for every tool it needs.**

## 💡 The Solution

Limbo aggregates multiple MCP servers into one unified interface and lets your AI dynamically:

- ✅ Install new tools on-demand
- ✅ Remove unused tools
- ✅ Manage configurations automatically
- ✅ Scale without manual intervention

**Think: Package manager, but for AI capabilities.**

## 🚀 Quick Start

### Docker (Recommended)

```bash
# Pull and run
docker pull pr33th4m/l1mbo:latest
docker run -p 8000:8000 pr33th4m/l1mbo:latest

# With persistent config
docker run -p 8000:8000 -v limbo-config:/home/limbo/.limbo pr33th4m/l1mbo:latest
```

### Local Installation

```bash
# Clone repository
git clone https://github.com/Pritz395/limbo.git
cd limbo

# Install with uv (recommended)
uv sync
limbo serve --http

# Or with pip
pip install -e .
limbo serve --http
```

## 🎮 Usage

### Stdio Mode (for Claude Desktop, Cursor, etc.)

```bash
limbo serve
```

### HTTP Mode (for system-wide access)

```bash
limbo serve --http --port 8000
```

### Hybrid Mode (both stdio + HTTP)

```bash
limbo serve --hybrid
```

## 🛠️ Example Workflow

**Without Limbo:**

```
You: "I need filesystem access"
AI: "Please configure the filesystem tool, restart me, and try again."
You: *manually configures, restarts*
AI: "Okay, ready now."
```

**With Limbo:**

```
You: "I need filesystem access"
AI: *calls limbo_add_server()* → Tool installed
AI: "Done. Which file do you need?"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│     Your AI Assistant (Cursor)     │
└──────────────┬──────────────────────┘
               │
               ├──→ Docker MCP Gateway
               │    ├─ Essential tools (always on)
               │    │  ├─ GitHub
               │    │  ├─ Obsidian
               │    │  └─ Time
               │    │
               │    └─ Limbo (your "extra limbs")
               │         ├─ Calculator (on-demand)
               │         ├─ Memory (on-demand)
               │         └─ [AI installs more as needed]
```

## 📦 Management Tools

Once connected, Limbo provides 16 management tools:

| Tool                    | Purpose                          |
| ----------------------- | -------------------------------- |
| `limbo_add_server`      | Dynamically install MCP servers  |
| `limbo_list_servers`    | View all configured servers      |
| `limbo_remove_server`   | Remove servers                   |
| `limbo_enable_server`   | Enable disabled servers          |
| `limbo_disable_server`  | Temporarily disable servers      |
| `limbo_status`          | Health check and statistics      |
| `limbo_search_servers`  | Find MCP servers online          |
| `limbo_list_tools`      | List all available tools         |
| `limbo_smart_configure` | Auto-configure from URL          |
| `limbo_analyze_servers` | Analyze and suggest improvements |
| `limbo_check`           | Health check with repair actions |
| `limbo_reload_config`   | Reload config without restart    |
| `limbo_load_kit`        | Load server bundles              |
| `limbo_unload_kit`      | Unload server bundles            |
| `limbo_list_kits`       | List available kits              |
| `limbo_kit_info`        | Get kit information              |

## 🎛️ Configuration

Limbo stores configuration in `.limbo/config.json` with automatic hot-reloading.

### Environment Variables

| Variable            | Description               | Default              |
| ------------------- | ------------------------- | -------------------- |
| `LIMBO_CONFIG_PATH` | Config file location      | `.limbo/config.json` |
| `LIMBO_LOG_LEVEL`   | Logging level             | `INFO`               |
| `LIMBO_AUTO_RELOAD` | Enable config auto-reload | `true`               |
| `LIMBO_SELF_PREFIX` | Tool prefix               | `limbo`              |
| `LIMBO_READ_ONLY`   | Read-only mode            | `false`              |

### Example Configuration

```json
{
  "servers": {
    "calculator": {
      "command": "npx -y @modelcontextprotocol/server-calculator",
      "prefix": "calc",
      "enabled": true
    },
    "filesystem": {
      "command": "npx -y @modelcontextprotocol/server-filesystem /workspace",
      "prefix": "fs",
      "enabled": true
    }
  }
}
```

## 🔐 Authentication

Limbo supports optional JWT-based authentication:

```bash
# Initialize authentication
limbo auth init

# Generate token
limbo auth token

# Use with clients
export LIMBO_JWT=$(limbo auth token -q)
```

## 🐳 Docker MCP Gateway Integration

Add Limbo to Docker MCP Gateway:

```bash
# Download catalog
curl -O https://raw.githubusercontent.com/Pritz395/limbo/main/limbo-catalog.yaml

# Add to Docker MCP
docker mcp catalog create custom
docker mcp catalog add custom limbo ./limbo-catalog.yaml
docker mcp server enable limbo
```

## 📚 CLI Commands

```bash
# Server management
limbo server list                    # List all servers
limbo server add <name> <command>    # Add new server
limbo server remove <name>           # Remove server
limbo server enable <name>           # Enable server
limbo server disable <name>          # Disable server
limbo server info <name>             # Server details

# Kit management
limbo kit list                       # List available kits
limbo kit load <name>                # Load a kit
limbo kit info <name>                # Kit information
limbo kit export <name>              # Export current config as kit

# Authentication
limbo auth init                      # Setup authentication
limbo auth status                    # Check auth status
limbo auth token                     # Generate JWT token

# Configuration
limbo config path                    # Show config location
```

## 🎓 Use Cases

### Development

Install tools as you need them during development without context switching.

### CI/CD

Dynamically provision tools based on pipeline requirements.

### Multi-tenant

Provide different tool sets to different users without separate deployments.

### Cost Optimization

Only run the tools you actually need at any given time.

## 🏆 Features

- **Dynamic Tool Loading** - Add/remove tools without restart
- **Auto-Reload Configuration** - Changes apply instantly
- **Tool Prefixing** - Prevent naming conflicts
- **Health Monitoring** - Built-in status checks
- **Kit System** - Bundle related tools
- **JWT Authentication** - Optional security layer
- **Docker Ready** - Production-ready containers
- **Multiple Transports** - stdio, HTTP, or hybrid

## 🛣️ Roadmap

- [ ] Tool marketplace/discovery
- [ ] Metrics and analytics dashboard
- [ ] Webhook support for notifications
- [ ] Plugin system for custom tools
- [ ] Cloud deployment templates

## 🤝 Contributing

Contributions welcome! This project is open source under AGPL-3.0.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📜 License

AGPL-3.0 - see [LICENSE](license.md) for details.

## 🙏 Acknowledgments

Based on [Magg](https://github.com/sitbon/magg) by Phillip Sitbon. Thank you for the amazing foundation!

## 🔗 Links

- **Docker Hub**: https://hub.docker.com/r/pr33th4m/l1mbo
- **GitHub**: https://github.com/Pritz395/limbo
- **MCP Docs**: https://modelcontextprotocol.io/

## 📧 Contact

Built by [Preetham](https://github.com/Pritz395)

---

<p align="center">
  <sub>Give your AI the tools it needs, when it needs them.</sub>
</p>
