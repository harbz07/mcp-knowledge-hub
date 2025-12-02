# LLM Knowledge Hub - LLM-Facing Onboarding Guide

## 🧠 What This Is
A shared knowledge base that allows multiple LLMs to store and retrieve context, conversations, and insights. Think of it as a shared brain for AI assistants.

## 🔗 Connection Details

### Endpoint Information
- **HTTPS MCP Server URL**: `https://knowledge-hub-mcp.harveytagalicud7.workers.dev`
- **STDIO bridge (local)**: `node scripts/stdio-proxy.js`
- **Protocol**: JSON-RPC 2.0 (HTTP POST for the worker; newline-delimited JSON via STDIO)
- **Content-Type**: `application/json`

### Authentication
**⚠️ IMPORTANT**: This server currently has **NO AUTHENTICATION**.
- No API tokens required
- No bearer auth headers needed
- Open access (consider this for production use)

### Transport Examples
- **HTTP (e.g., Claude Desktop/Code)**
  ```json
  {
    "mcpServers": {
      "knowledge-hub": {
        "transport": {"type": "http", "url": "https://knowledge-hub-mcp.harveytagalicud7.workers.dev"}
      }
    }
  }
  ```
- **STDIO (local proxy that forwards to HTTPS)**
  ```json
  {
    "mcpServers": {
      "knowledge-hub": {
        "command": "node",
        "args": ["scripts/stdio-proxy.js"],
        "env": {"MCP_HTTPS_ENDPOINT": "https://knowledge-hub-mcp.harveytagalicud7.workers.dev"}
      }
    }
  }
  ```

Both transports expose identical tools and client-scoped storage.

## 🛠️ Available Tools

Buckets are client-scoped by default. Pass `clientId` to isolate storage for a specific organization/user; omit to fall back to the shared `public` bucket.

### 1. store_context
**Purpose**: Store knowledge/context for sharing between LLMs

**Parameters**:
```json
{
  "content": "string (required) - The knowledge to store",
  "tags": "array of strings (optional) - Categorization tags",
  "source": "string (required) - Which LLM/tool is storing this",
  "metadata": "object (optional) - Additional structured data",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

**Example Usage**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "store_context",
    "arguments": {
      "content": "Harvey prefers itemized information due to ADHD",
      "tags": ["harvey", "preferences", "user-info"],
      "source": "chatgpt-session",
      "metadata": {"importance": "high", "category": "user-preference"}
    }
  }
}
```

### 2. search_contexts
**Purpose**: Find relevant stored knowledge by keywords, tags, or source

**Parameters**:
```json
{
  "query": "string (optional) - Text to search for",
  "tags": "array of strings (optional) - Filter by tags",
  "source": "string (optional) - Filter by source LLM/tool",
  "limit": "number (optional, default: 10) - Max results",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

### 3. get_recent_contexts
**Purpose**: Get the most recently stored contexts

**Parameters**:
```json
{
  "limit": "number (optional, default: 5) - Max results",
  "source": "string (optional) - Filter by source LLM/tool",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

### 4. store_file
**Purpose**: Store files in shared R2 storage

**Parameters**:
```json
{
  "filename": "string (required) - Name of the file",
  "content": "string (required) - File content (base64 for binary)",
  "contentType": "string (optional) - MIME type",
  "tags": "array of strings (optional) - Categorization tags",
  "source": "string (required) - Which LLM/tool is storing this",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

### 5. get_file
**Purpose**: Retrieve a stored file

**Parameters**:
```json
{
  "filename": "string (required) - Name of the file to retrieve",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

### 6. list_files
**Purpose**: List stored files with optional filtering

**Parameters**:
```json
{
  "prefix": "string (optional) - Filter by filename prefix",
  "limit": "number (optional, default: 20) - Max results",
  "clientId": "string (optional, default: public) - Client bucket id"
}
```

### 7. ensure_client_bucket
**Purpose**: Create or describe an isolated client bucket for contexts, files, and events.

**Parameters**:
```json
{
  "clientId": "string (required) - Unique client identifier",
  "label": "string (optional) - Friendly label"
}
```

### 8. record_event
**Purpose**: Write a structured event into the client-shared events hub (Who/Why/Effects blocks).

**Parameters**:
```json
{
  "event": {
    "title": "string (required)",
    "description": "string (optional)",
    "happened_at": "ISO string (optional, defaults to now)",
    "who": "array<string> (required) - participants",
    "why": "array<string> (required) - catalysts/reasons"
  },
  "place": "string (required) - where the event occurred",
  "effects": "array<Effect> (optional) - Effects blocks with target_id/target_kind/summary/valence/intensity",
  "clientId": "string (optional, default: public)"
}
```

### 9. list_events
**Purpose**: List recent events for a given client bucket.

**Parameters**:
```json
{
  "clientId": "string (optional, default: public)",
  "limit": "number (optional, default: 10)"
}
```

### 10. get_cypher_event_schema
**Purpose**: Return the Cypher schema and templates that map the events hub into Neo4j.

**Parameters**: _none_

## 🚀 Quick Start for LLMs

### Step 1: Test Connection
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Expected Response**: List of 6 available tools

### Step 2: Store Your First Context
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "store_context",
    "arguments": {
      "content": "Successfully connected to Harvey's knowledge hub",
      "tags": ["onboarding", "test"],
      "source": "your-llm-name-here"
    }
  }
}
```

### Step 3: Search for Existing Knowledge
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "search_contexts",
    "arguments": {
      "query": "harvey",
      "limit": 5
    }
  }
}
```

## 🧭 Events Hub & Cypher Schema
- Use `record_event` to capture Who/Why/Effects blocks inside a client bucket; `list_events` retrieves them with newest first.
- Call `get_cypher_event_schema` to fetch the Neo4j-ready Cypher templates that mirror the in-worker schema for downstream graph syncing.
- Effects blocks (target_id/target_kind/summary/valence/intensity) are stored alongside core event metadata to keep downstream graph materialization lossless.

## 🏷️ Tagging Best Practices

Use consistent tags for better knowledge organization:

**User-related**:
- `harvey` - Anything about the user Harvey
- `preferences` - User preferences and settings
- `user-info` - General user information

**Context types**:
- `conversation` - Conversation excerpts
- `insight` - Important insights or learnings
- `technical` - Technical information
- `project` - Project-related context

**Importance levels**:
- `critical` - Must-remember information
- `important` - Useful to remember
- `reference` - Good to have for reference

## 🔧 Configuration Examples

### For Claude Desktop/Code
Add to your MCP configuration:
```json
{
  "mcpServers": {
    "knowledge-hub": {
      "transport": {
        "type": "http",
        "url": "https://knowledge-hub-mcp.harveytagalicud7.workers.dev"
      }
    }
  }
}
```

### For Continue/Cursor
Add to your MCP servers list:
```json
{
  "mcp": {
    "servers": {
      "knowledge-hub": {
        "command": "node",
        "args": ["-e", "console.log('MCP running')"],
        "transport": {
          "type": "http",
          "url": "https://knowledge-hub-mcp.harveytagalicud7.workers.dev"
        }
      }
    }
  }
}
```

### For Custom Integration
```bash
# Environment variables you might want to set
export MCP_ENDPOINT="https://knowledge-hub-mcp.harveytagalicud7.workers.dev"
export MCP_API_TOKEN=""  # Currently not needed, but reserved for future auth
```

## 🛡️ Security Considerations

**Current State**: No authentication - anyone with the URL can read/write

**Recommendations for Production**:
1. Add API key authentication
2. Implement rate limiting
3. Add request validation
4. Consider IP allowlisting

**For Now**: The server is deployed on Cloudflare's edge, so it's fast and reliable, but consider the open access when storing sensitive information.

## 📝 Response Format

All responses follow JSON-RPC 2.0 format:

**Success**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": ["Response message", "Additional data..."],
    "isError": false
  }
}
```

**Error**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Error description"
  }
}
```

## 🌐 Web Interface

For manual testing and management: Save the provided HTML interface and open in any browser for a GUI to interact with the knowledge hub.

## 📞 Support

If you encounter issues:
1. Test the connection first with `tools/list`
2. Check that you're sending valid JSON-RPC 2.0 requests
3. Verify the endpoint URL is correct
4. Remember: POST requests only, no authentication needed

---

**Ready to connect?** Start with the connection test and then begin sharing knowledge across all your AI assistants!
