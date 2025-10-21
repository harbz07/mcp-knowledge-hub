# MCP Knowledge Hub - Production Readiness Roadmap

## Executive Summary

This roadmap outlines the path to transform the MCP Knowledge Hub from a functional v1.0 prototype to a production-ready, secure, and scalable service. The project is organized into 3 phases over an estimated 2-3 week timeline.

**Current State**: 7/10 MCP readiness - Functional core with critical security and testing gaps
**Target State**: 9.5/10 - Production-ready multi-user MCP server with security, monitoring, and comprehensive testing

**Estimated Timeline**: 15-20 working days
**Complexity**: Medium
**Risk Level**: Low-Medium (well-defined scope, proven infrastructure)

---

## Phase 1: Critical Security & Foundations (Week 1)

**Duration**: 5-7 days
**Priority**: CRITICAL 🔴
**Goal**: Make the server secure and stable enough for controlled production use

### 1.1 Project Infrastructure (Day 1)
**Effort**: 4-6 hours

- [ ] Create `package.json` with dependencies
  ```json
  {
    "name": "knowledge-hub-mcp",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
      "dev": "wrangler dev",
      "deploy": "wrangler deploy",
      "test": "vitest",
      "test:coverage": "vitest --coverage",
      "typecheck": "tsc --noEmit"
    },
    "devDependencies": {
      "@cloudflare/workers-types": "^4.x",
      "@types/node": "^20.x",
      "typescript": "^5.x",
      "wrangler": "^3.x",
      "vitest": "^1.x"
    }
  }
  ```

- [ ] Create `tsconfig.json` for TypeScript
- [ ] Set up `.npmrc` or `.yarnrc` if needed
- [ ] Add `.nvmrc` for Node.js version locking
- [ ] Update `.gitignore` for node_modules, dist, etc.

**Deliverables**:
- Proper dependency management
- TypeScript type checking enabled
- Development workflow standardized

---

### 1.2 Authentication System (Days 2-3)
**Effort**: 12-16 hours
**Critical Path**: YES

#### Implementation Plan:

**A. API Key Authentication**
```typescript
// Add to wrangler.jsonc
"vars": {
  "AUTH_REQUIRED": "true"
},
"secrets": ["API_KEYS_HASH"] // Set via: wrangler secret put API_KEYS_HASH
```

**B. Middleware Implementation** (`src/auth.ts`)
```typescript
export async function authenticateRequest(
  request: Request,
  env: Env
): Promise<{ authorized: boolean; error?: string }> {
  // Extract API key from header
  const apiKey = request.headers.get('X-API-Key') ||
                 request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!env.AUTH_REQUIRED) {
    return { authorized: true }; // Dev mode
  }

  if (!apiKey) {
    return { authorized: false, error: 'API key required' };
  }

  // Verify against stored hash (use crypto.subtle for secure comparison)
  const isValid = await verifyApiKey(apiKey, env.API_KEYS_HASH);

  return { authorized: isValid, error: isValid ? undefined : 'Invalid API key' };
}
```

**C. Integration Points**:
- [ ] Modify `fetch()` handler in `src/index.ts:35` to call auth middleware
- [ ] Return 401 Unauthorized for invalid keys
- [ ] Add rate limiting per API key (Cloudflare Workers KV)
- [ ] Create API key management CLI tool (`scripts/manage-keys.ts`)

**D. Rate Limiting**
```typescript
// Use Cloudflare Workers KV for rate limiting
interface RateLimitConfig {
  requests_per_minute: 60,
  requests_per_hour: 1000,
  requests_per_day: 10000
}
```

**E. Documentation Updates**:
- [ ] Update README with authentication section
- [ ] Create API key request process document
- [ ] Add authentication examples for all client types

**Deliverables**:
- API key authentication working
- Rate limiting implemented
- 401/429 error responses
- Key management tooling
- Updated documentation

**Testing**:
- [ ] Test with valid API key → 200 OK
- [ ] Test without API key → 401 Unauthorized
- [ ] Test with invalid API key → 401 Unauthorized
- [ ] Test rate limit enforcement → 429 Too Many Requests
- [ ] Test AUTH_REQUIRED=false bypass

---

### 1.3 Input Validation & Sanitization (Day 3)
**Effort**: 6-8 hours

**A. Schema Validation Library**
```typescript
// Add to package.json
"dependencies": {
  "zod": "^3.x"
}
```

**B. Input Schemas** (`src/validators.ts`)
```typescript
import { z } from 'zod';

export const StoreContextSchema = z.object({
  content: z.string().min(1).max(50000), // 50KB limit
  tags: z.array(z.string().max(50)).max(20).optional(),
  source: z.string().min(1).max(100),
  metadata: z.record(z.unknown()).optional()
});

export const SearchContextsSchema = z.object({
  query: z.string().max(500).optional(),
  tags: z.array(z.string()).max(10).optional(),
  source: z.string().max(100).optional(),
  limit: z.number().int().min(1).max(100).default(10)
});

// ... schemas for all 6 tools
```

**C. SQL Injection Prevention**
- [ ] Audit all SQL queries in `src/index.ts`
- [ ] Ensure all use parameterized queries (already mostly done)
- [ ] Add prepared statement helpers
- [ ] Review tag search implementation (line 267)

**D. Content Security**
- [ ] XSS prevention in stored content
- [ ] File upload validation (MIME type verification)
- [ ] Filename sanitization (no path traversal)
- [ ] Maximum file size limits (e.g., 10MB)

**E. Implementation**:
- [ ] Add validation to `handleToolCall()` before dispatching
- [ ] Return 400 Bad Request with detailed validation errors
- [ ] Log validation failures for monitoring

**Deliverables**:
- All tool inputs validated with Zod
- SQL injection vectors eliminated
- Content security measures in place
- Size limits enforced

**Testing**:
- [ ] Test oversized content → 400 error
- [ ] Test SQL injection attempts → safe/rejected
- [ ] Test malformed JSON → 400 error
- [ ] Test XSS payloads → sanitized
- [ ] Test path traversal in filenames → rejected

---

### 1.4 Test Suite Foundation (Days 4-5)
**Effort**: 10-14 hours

**A. Test Infrastructure Setup**
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'miniflare', // Cloudflare Workers test environment
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'dist/']
    }
  }
});
```

**B. Test Structure**
```
tests/
├── unit/
│   ├── auth.test.ts
│   ├── validators.test.ts
│   ├── tools/
│   │   ├── store-context.test.ts
│   │   ├── search-contexts.test.ts
│   │   ├── get-recent-contexts.test.ts
│   │   ├── store-file.test.ts
│   │   ├── get-file.test.ts
│   │   └── list-files.test.ts
│   └── mcp-protocol.test.ts
├── integration/
│   ├── database.test.ts
│   ├── r2-storage.test.ts
│   └── end-to-end.test.ts
└── fixtures/
    ├── mock-contexts.json
    └── mock-files/
```

**C. Critical Tests to Write**

**Unit Tests** (Target: 80%+ coverage)
- [ ] MCP protocol compliance (initialize, tools/list, tools/call)
- [ ] Authentication (valid/invalid keys, rate limiting)
- [ ] Each tool's business logic
- [ ] Input validation (all schemas)
- [ ] Error handling (all error paths)

**Integration Tests**
- [ ] Database operations (CRUD on contexts)
- [ ] R2 file storage (upload, retrieve, list)
- [ ] Full request/response cycle
- [ ] CORS handling

**Example Test**:
```typescript
// tests/unit/tools/store-context.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { storeContext } from '../../../src/index';

describe('store_context', () => {
  it('should store valid context and return UUID', async () => {
    const args = {
      content: 'Test context',
      tags: ['test'],
      source: 'test-suite'
    };

    const result = await storeContext(args, mockEnv);

    expect(result.isError).toBe(false);
    expect(result.content[0]).toMatch(/^Stored context with ID: [a-f0-9-]+$/);
  });

  it('should reject empty content', async () => {
    // validation should catch this before reaching function
    await expect(StoreContextSchema.parse({ content: '' }))
      .rejects.toThrow();
  });
});
```

**D. CI Integration Prep**
- [ ] Create `.github/workflows/test.yml` (for later)
- [ ] Add test coverage reporting
- [ ] Document test running instructions

**Deliverables**:
- Vitest test framework configured
- 40+ unit tests written
- 10+ integration tests written
- 70%+ code coverage
- All tests passing

**Phase 1 Success Criteria**:
✅ Authentication blocks unauthorized access
✅ Rate limiting prevents abuse
✅ Input validation rejects malicious/malformed data
✅ 70%+ test coverage with all tests passing
✅ No critical security vulnerabilities

**Phase 1 Exit Gate**: Security review + penetration testing

---

## Phase 2: Enhanced Reliability & Operations (Week 2)

**Duration**: 5-7 days
**Priority**: HIGH 🟡
**Goal**: Production-grade reliability, monitoring, and operational tooling

### 2.1 Database Improvements (Days 1-2)
**Effort**: 8-10 hours

**A. Better Tag Search**
Current implementation (line 267-270):
```typescript
// REPLACE THIS:
const tagConditions = tags.map(() => 'tags LIKE ?').join(' OR ');
sql += ` AND (${tagConditions})`;
tags.forEach((tag: string) => bindings.push(`%"${tag}"%`));
```

With proper JSON querying:
```typescript
// D1 supports JSON functions since 2024
const tagConditions = tags.map(() =>
  `EXISTS (SELECT 1 FROM json_each(tags) WHERE value = ?)`
).join(' OR ');
sql += ` AND (${tagConditions})`;
tags.forEach((tag: string) => bindings.push(tag));
```

**B. Full-Text Search (Optional but Recommended)**
```sql
-- migrations/0002_add_fts.sql
CREATE VIRTUAL TABLE contexts_fts USING fts5(
  content,
  content='contexts',
  content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER contexts_ai AFTER INSERT ON contexts BEGIN
  INSERT INTO contexts_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER contexts_ad AFTER DELETE ON contexts BEGIN
  DELETE FROM contexts_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER contexts_au AFTER UPDATE ON contexts BEGIN
  UPDATE contexts_fts SET content = new.content WHERE rowid = new.rowid;
END;
```

**C. Pagination Support**
```typescript
// Add cursor-based pagination
interface PaginationParams {
  limit: number;
  cursor?: string; // timestamp or ID of last item
}

// Update search_contexts to support cursors
async function searchContexts(args: any, env: Env) {
  const { query, tags, source, limit = 10, cursor } = args;

  let sql = 'SELECT * FROM contexts WHERE 1=1';
  const bindings: any[] = [];

  if (cursor) {
    sql += ' AND timestamp < ?';
    bindings.push(cursor);
  }

  // ... rest of query

  sql += ' ORDER BY timestamp DESC LIMIT ?';
  bindings.push(limit + 1); // Fetch one extra to detect if there's more

  const results = await env.KNOWLEDGE_DB.prepare(sql).bind(...bindings).all();
  const hasMore = results.results.length > limit;
  const contexts = results.results.slice(0, limit);

  return {
    content: [
      `Found ${contexts.length} contexts`,
      JSON.stringify(contexts, null, 2)
    ],
    nextCursor: hasMore ? contexts[contexts.length - 1].timestamp : null,
    isError: false
  };
}
```

**D. Database Indexes Audit**
- [ ] Analyze query patterns
- [ ] Add composite indexes if needed
- [ ] Document index strategy

**Deliverables**:
- Proper JSON tag querying
- Optional FTS5 implementation
- Cursor-based pagination
- Performance benchmarks (before/after)

---

### 2.2 Observability & Monitoring (Days 2-3)
**Effort**: 10-12 hours

**A. Structured Logging**
```typescript
// src/logger.ts
export interface LogContext {
  requestId: string;
  method?: string;
  toolName?: string;
  source?: string;
  userId?: string;
  duration?: number;
  error?: string;
}

export function log(level: 'info' | 'warn' | 'error', message: string, context: LogContext) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...context
  };

  console.log(JSON.stringify(logEntry));
}

// Usage in handlers
log('info', 'Tool called', {
  requestId: crypto.randomUUID(),
  toolName: 'store_context',
  source: args.source
});
```

**B. Custom Metrics** (Cloudflare Analytics Engine)
```typescript
// Add to wrangler.jsonc
"analytics_engine_datasets": [
  { "binding": "ANALYTICS" }
]

// src/metrics.ts
export async function trackToolUsage(
  env: Env,
  toolName: string,
  source: string,
  success: boolean,
  duration: number
) {
  await env.ANALYTICS.writeDataPoint({
    blobs: [toolName, source],
    doubles: [duration],
    indexes: [success ? 'success' : 'error']
  });
}
```

**C. Health Check Endpoint**
```typescript
// Add to fetch() handler
if (request.method === 'GET' && new URL(request.url).pathname === '/health') {
  try {
    // Check database connectivity
    await env.KNOWLEDGE_DB.prepare('SELECT 1').first();

    // Check R2 connectivity
    await env.KNOWLEDGE_FILES.list({ limit: 1 });

    return new Response(JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      checks: {
        database: 'ok',
        storage: 'ok'
      }
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      status: 'unhealthy',
      error: error.message
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
```

**D. Error Tracking Integration**
```typescript
// Optional: Integrate with Sentry/Axiom/BetterStack
// Add to package.json
"dependencies": {
  "@sentry/browser": "^7.x" // or similar
}

// Initialize in worker
import * as Sentry from '@sentry/browser';

Sentry.init({
  dsn: env.SENTRY_DSN,
  environment: env.ENVIRONMENT || 'production'
});
```

**E. Alerting Setup** (via Cloudflare)
- [ ] Set up Cloudflare Workers alerts for:
  - Error rate > 5%
  - Request latency p95 > 1000ms
  - 5xx responses > 10/minute
- [ ] Configure notification channels (email, Slack, PagerDuty)

**Deliverables**:
- Structured JSON logging implemented
- Custom metrics tracking tool usage
- Health check endpoint at `/health`
- Error tracking configured
- Alerting rules set up

---

### 2.3 Backup & Data Management (Day 3)
**Effort**: 4-6 hours

**A. Database Backup Strategy**
Cloudflare D1 doesn't have built-in backup API yet, so implement export:

```typescript
// scripts/backup-database.ts
import { D1Database } from '@cloudflare/workers-types';

export async function backupDatabase(db: D1Database, bucket: R2Bucket) {
  const timestamp = new Date().toISOString().replace(/:/g, '-');

  // Export all contexts
  const contexts = await db.prepare('SELECT * FROM contexts').all();

  // Store in R2 with compression
  await bucket.put(
    `backups/contexts-${timestamp}.json`,
    JSON.stringify(contexts.results),
    {
      httpMetadata: {
        contentType: 'application/json'
      },
      customMetadata: {
        recordCount: String(contexts.results.length),
        backupDate: new Date().toISOString()
      }
    }
  );

  return { recordCount: contexts.results.length, filename: `contexts-${timestamp}.json` };
}
```

**B. Scheduled Backups** (Cloudflare Cron Triggers)
```typescript
// Add to wrangler.jsonc
"triggers": {
  "crons": ["0 2 * * *"] // Daily at 2 AM UTC
}

// Add to worker
export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(backupDatabase(env.KNOWLEDGE_DB, env.KNOWLEDGE_FILES));
  }
}
```

**C. Data Retention Policy**
```typescript
// Add optional cleanup for old contexts
async function cleanupOldContexts(env: Env, retentionDays: number = 90) {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

  const result = await env.KNOWLEDGE_DB.prepare(`
    DELETE FROM contexts
    WHERE timestamp < ?
    AND metadata NOT LIKE '%"retain":true%'
  `).bind(cutoffDate.toISOString()).run();

  return { deletedCount: result.meta.changes };
}
```

**D. Restore Procedure Documentation**
- [ ] Document manual restore process
- [ ] Create restore script (`scripts/restore-database.ts`)
- [ ] Test restore on staging environment

**Deliverables**:
- Automated daily backups to R2
- Backup verification process
- Restore procedure documented and tested
- Optional data retention policy

---

### 2.4 CI/CD Pipeline (Day 4)
**Effort**: 6-8 hours

**A. GitHub Actions Workflow**
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npm run typecheck

      - name: Run tests
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: deploy --env staging

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production # Requires manual approval
    steps:
      - uses: actions/checkout@v4
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: deploy --env production
```

**B. Environment Configuration**
```jsonc
// wrangler.jsonc - Update with environments
{
  "name": "knowledge-hub-mcp",
  "main": "src/index.ts",
  "compatibility_date": "2025-03-07",

  // Base configuration
  "vars": {
    "ENVIRONMENT": "development",
    "AUTH_REQUIRED": "false"
  },

  // Staging environment
  "env": {
    "staging": {
      "name": "knowledge-hub-mcp-staging",
      "vars": {
        "ENVIRONMENT": "staging",
        "AUTH_REQUIRED": "true"
      },
      "d1_databases": [
        {
          "binding": "KNOWLEDGE_DB",
          "database_name": "knowledge-hub-staging",
          "database_id": "..."
        }
      ]
    },

    // Production environment
    "production": {
      "name": "knowledge-hub-mcp",
      "vars": {
        "ENVIRONMENT": "production",
        "AUTH_REQUIRED": "true"
      },
      "d1_databases": [
        {
          "binding": "KNOWLEDGE_DB",
          "database_name": "knowledge-hub",
          "database_id": "6499cc10-6774-4d1f-80fa-911ef32519bd"
        }
      ]
    }
  }
}
```

**C. Pre-commit Hooks** (Optional)
```json
// package.json
"scripts": {
  "prepare": "husky install"
},
"devDependencies": {
  "husky": "^8.x",
  "lint-staged": "^15.x"
}
```

```bash
# .husky/pre-commit
npm run typecheck
npm run test
```

**Deliverables**:
- Automated testing on every PR
- Staging auto-deployment on develop branch
- Production deployment with manual approval
- Environment separation (dev/staging/prod)

**Phase 2 Success Criteria**:
✅ Search performance improved (FTS5 + proper JSON queries)
✅ Monitoring dashboard shows key metrics
✅ Health check endpoint returns 200
✅ Automated daily backups running
✅ CI/CD pipeline successfully deploys to staging
✅ Zero-downtime deployment verified

---

## Phase 3: MCP Enhancements & Polish (Week 3)

**Duration**: 5-6 days
**Priority**: MEDIUM 🟢
**Goal**: Advanced MCP features, developer experience improvements

### 3.1 MCP Protocol Enhancements (Days 1-2)
**Effort**: 8-10 hours

**A. Resources Capability**
Add browsable resources to MCP protocol:

```typescript
// Add to initialize response
case 'initialize':
  result = {
    protocolVersion: '2024-11-05',
    capabilities: {
      tools: {},
      resources: {} // NEW
    },
    serverInfo: {
      name: 'knowledge-hub-mcp',
      version: '1.0.0'
    }
  };
  break;

// Add resources/list method
case 'resources/list':
  result = {
    resources: [
      {
        uri: 'context://recent',
        name: 'Recent Contexts',
        description: 'View recently stored knowledge',
        mimeType: 'application/json'
      },
      {
        uri: 'context://by-source/{source}',
        name: 'Contexts by Source',
        description: 'Browse contexts from a specific source',
        mimeType: 'application/json'
      },
      {
        uri: 'files://list',
        name: 'Stored Files',
        description: 'Browse all stored files',
        mimeType: 'application/json'
      }
    ]
  };
  break;

// Add resources/read method
case 'resources/read':
  const { uri } = params;

  if (uri === 'context://recent') {
    const contexts = await getRecentContexts({ limit: 20 }, env);
    result = {
      contents: [{
        uri,
        mimeType: 'application/json',
        text: JSON.stringify(contexts, null, 2)
      }]
    };
  }
  // ... handle other URIs
  break;
```

**B. Progress Notifications** (for long operations)
```typescript
// For file uploads or batch operations
interface ProgressNotification {
  method: 'notifications/progress';
  params: {
    progressToken: string;
    progress: number; // 0-100
    total?: number;
  };
}

// Would require WebSocket support or streaming responses
// Consider for future if needed
```

**C. Stdio Transport Option**
```typescript
// Create separate entrypoint for stdio
// src/stdio.ts
import { MCPRequest, handleMCPRequest } from './index';

async function main() {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  rl.on('line', async (line: string) => {
    try {
      const request: MCPRequest = JSON.parse(line);
      const response = await handleMCPRequest(request, env);
      console.log(JSON.stringify(response));
    } catch (error) {
      console.error(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: { code: -32700, message: 'Parse error' }
      }));
    }
  });
}

main();
```

**D. Batch Operations Tool**
```typescript
// Add new tool: batch_store_contexts
{
  name: 'batch_store_contexts',
  description: 'Store multiple contexts in a single operation',
  inputSchema: {
    type: 'object',
    properties: {
      contexts: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            content: { type: 'string' },
            tags: { type: 'array', items: { type: 'string' } },
            source: { type: 'string' },
            metadata: { type: 'object' }
          },
          required: ['content', 'source']
        }
      }
    },
    required: ['contexts']
  }
}

// Implementation
async function batchStoreContexts(args: any, env: Env) {
  const { contexts } = args;

  // Use D1 batch API for efficiency
  const statements = contexts.map((ctx: any) =>
    env.KNOWLEDGE_DB.prepare(`
      INSERT INTO contexts (id, content, tags, source, timestamp, metadata)
      VALUES (?, ?, ?, ?, ?, ?)
    `).bind(
      crypto.randomUUID(),
      ctx.content,
      JSON.stringify(ctx.tags || []),
      ctx.source,
      new Date().toISOString(),
      JSON.stringify(ctx.metadata || {})
    )
  );

  const results = await env.KNOWLEDGE_DB.batch(statements);

  return {
    content: [`Stored ${results.length} contexts successfully`],
    isError: false
  };
}
```

**Deliverables**:
- Resources capability implemented
- Batch operations tool added
- Optional stdio transport
- Updated MCP client examples

---

### 3.2 Advanced Features (Days 3-4)
**Effort**: 10-12 hours

**A. Context Versioning**
```sql
-- migrations/0003_add_versioning.sql
ALTER TABLE contexts ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE contexts ADD COLUMN parent_id TEXT; -- For tracking updates
CREATE INDEX idx_contexts_parent ON contexts(parent_id);
```

```typescript
// Update store_context to support versioning
async function updateContext(args: any, env: Env) {
  const { contextId, content, tags, source, metadata } = args;

  // Get existing context
  const existing = await env.KNOWLEDGE_DB.prepare(
    'SELECT * FROM contexts WHERE id = ?'
  ).bind(contextId).first();

  if (!existing) {
    throw new Error('Context not found');
  }

  // Create new version
  const newVersion = existing.version + 1;
  const newId = crypto.randomUUID();

  await env.KNOWLEDGE_DB.prepare(`
    INSERT INTO contexts (id, content, tags, source, timestamp, metadata, version, parent_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    newId,
    content,
    JSON.stringify(tags),
    source,
    new Date().toISOString(),
    JSON.stringify(metadata),
    newVersion,
    contextId
  ).run();

  return { content: [`Updated context, new version: ${newVersion}`] };
}
```

**B. Soft Deletes**
```sql
ALTER TABLE contexts ADD COLUMN deleted_at TEXT;
CREATE INDEX idx_contexts_deleted ON contexts(deleted_at);
```

```typescript
// Update all queries to filter out deleted
sql += ' AND deleted_at IS NULL';

// Add delete_context tool
async function deleteContext(args: any, env: Env) {
  const { contextId } = args;

  await env.KNOWLEDGE_DB.prepare(
    'UPDATE contexts SET deleted_at = ? WHERE id = ?'
  ).bind(new Date().toISOString(), contextId).run();

  return { content: [`Context ${contextId} deleted`] };
}
```

**C. Semantic Search** (Optional Advanced Feature)
Integration with vector embeddings:

```typescript
// Would require Cloudflare Vectorize (beta)
// Or external service like Pinecone/Weaviate

interface VectorEmbedding {
  contextId: string;
  embedding: number[]; // 1536 dimensions for OpenAI
}

// Add to wrangler.jsonc
"vectorize": [
  { "binding": "VECTORIZE", "index_name": "context-embeddings" }
]

// Store embeddings on context creation
async function storeContextWithEmbedding(args: any, env: Env) {
  // 1. Store context normally
  const contextId = await storeContext(args, env);

  // 2. Generate embedding (call OpenAI/Cloudflare AI)
  const embedding = await generateEmbedding(args.content);

  // 3. Store in Vectorize
  await env.VECTORIZE.upsert([{
    id: contextId,
    values: embedding,
    metadata: { source: args.source }
  }]);

  return contextId;
}

// Semantic search
async function semanticSearch(args: any, env: Env) {
  const { query, limit = 10 } = args;

  // Generate query embedding
  const queryEmbedding = await generateEmbedding(query);

  // Search Vectorize
  const results = await env.VECTORIZE.query(queryEmbedding, {
    topK: limit,
    returnMetadata: true
  });

  // Fetch full contexts
  const contextIds = results.matches.map(m => m.id);
  // ... fetch from D1

  return { contexts, similarities: results.matches.map(m => m.score) };
}
```

**D. Export/Import Tools**
```typescript
// Add export_all tool
async function exportAllData(env: Env) {
  const contexts = await env.KNOWLEDGE_DB.prepare('SELECT * FROM contexts').all();
  const files = await env.KNOWLEDGE_FILES.list();

  return {
    content: [
      'Full data export',
      JSON.stringify({
        exportDate: new Date().toISOString(),
        contexts: contexts.results,
        files: files.objects.map(f => f.key)
      }, null, 2)
    ]
  };
}

// Add import_data tool (with validation)
async function importData(args: any, env: Env) {
  const { data } = args;

  // Validate structure
  // Insert contexts with conflict handling
  // Return import summary
}
```

**Deliverables**:
- Context versioning implemented
- Soft deletes enabled
- Optional semantic search (if time permits)
- Export/import tools

---

### 3.3 Developer Experience (Day 5)
**Effort**: 6-8 hours

**A. API Documentation**
Create OpenAPI/Swagger spec:

```yaml
# docs/openapi.yaml
openapi: 3.1.0
info:
  title: MCP Knowledge Hub API
  version: 1.0.0
  description: Multi-LLM shared knowledge base via MCP protocol

servers:
  - url: https://knowledge-hub-mcp.harveytagalicud7.workers.dev
    description: Production server

paths:
  /:
    post:
      summary: MCP JSON-RPC endpoint
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MCPRequest'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MCPResponse'

components:
  schemas:
    MCPRequest:
      type: object
      required: [jsonrpc, id, method]
      properties:
        jsonrpc:
          type: string
          enum: ['2.0']
        id:
          oneOf:
            - type: string
            - type: number
        method:
          type: string
          enum: [initialize, tools/list, tools/call, resources/list, resources/read]
        params:
          type: object

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

security:
  - ApiKeyAuth: []
```

**B. SDK/Client Libraries**
Create TypeScript client:

```typescript
// sdk/typescript/src/index.ts
export class KnowledgeHubClient {
  private apiUrl: string;
  private apiKey?: string;

  constructor(config: { apiUrl: string; apiKey?: string }) {
    this.apiUrl = config.apiUrl;
    this.apiKey = config.apiKey;
  }

  async storeContext(params: {
    content: string;
    tags?: string[];
    source: string;
    metadata?: Record<string, any>;
  }): Promise<string> {
    const response = await this.callTool('store_context', params);
    const match = response.content[0].match(/ID: (.+)$/);
    return match?.[1] || '';
  }

  async searchContexts(params: {
    query?: string;
    tags?: string[];
    source?: string;
    limit?: number;
  }): Promise<Context[]> {
    const response = await this.callTool('search_contexts', params);
    return JSON.parse(response.content[1]);
  }

  private async callTool(name: string, args: any): Promise<any> {
    const response = await fetch(this.apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'X-API-Key': this.apiKey })
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: Math.random(),
        method: 'tools/call',
        params: { name, arguments: args }
      })
    });

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);
    return data.result;
  }
}

// Usage
const client = new KnowledgeHubClient({
  apiUrl: 'https://knowledge-hub-mcp.harveytagalicud7.workers.dev',
  apiKey: process.env.KNOWLEDGE_HUB_API_KEY
});

const contextId = await client.storeContext({
  content: 'Example knowledge',
  tags: ['example'],
  source: 'my-app'
});
```

Publish to npm:
```json
// sdk/typescript/package.json
{
  "name": "@knowledge-hub/client",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts"
}
```

**C. Enhanced Documentation**
```
docs/
├── README.md (existing)
├── API_REFERENCE.md (detailed tool docs)
├── AUTHENTICATION.md (API key setup)
├── DEPLOYMENT.md (hosting guide)
├── EXAMPLES.md (code examples)
├── TROUBLESHOOTING.md (common issues)
├── CHANGELOG.md (version history)
└── openapi.yaml
```

**D. Example Applications**
```
examples/
├── typescript-client/ (using SDK)
├── python-client/ (requests-based)
├── claude-desktop-config/ (MCP config)
├── cursor-integration/ (IDE integration)
└── web-dashboard/ (improved frontend)
```

**E. Contribution Guidelines**
```markdown
# CONTRIBUTING.md

## Development Setup
1. Clone repository
2. Run `npm install`
3. Copy `.dev.vars.example` to `.dev.vars`
4. Run `npm run dev`

## Running Tests
- Unit tests: `npm test`
- Coverage: `npm run test:coverage`
- Type check: `npm run typecheck`

## Pull Request Process
1. Create feature branch from `develop`
2. Write tests for new features
3. Ensure all tests pass
4. Update documentation
5. Submit PR with description

## Code Style
- Use TypeScript strict mode
- Follow Prettier formatting
- Write JSDoc comments for public APIs
```

**Deliverables**:
- OpenAPI specification
- TypeScript SDK published to npm
- Comprehensive documentation suite
- Example applications
- Contribution guidelines

---

### 3.4 iOS App Completion (Day 6)
**Effort**: 6-8 hours

**A. MCP Client Implementation**
```swift
// ios/LLMKnowledgeHub/MCPClient.swift
import Foundation

class MCPClient: ObservableObject {
    private let apiUrl = URL(string: "https://knowledge-hub-mcp.harveytagalicud7.workers.dev")!
    private var apiKey: String?

    @Published var isConnected = false
    @Published var recentContexts: [Context] = []

    struct Context: Codable, Identifiable {
        let id: String
        let content: String
        let tags: [String]
        let source: String
        let timestamp: String
        let metadata: [String: AnyCodable]
    }

    func storeContext(content: String, tags: [String], source: String) async throws -> String {
        let request = MCPRequest(
            jsonrpc: "2.0",
            id: UUID().uuidString,
            method: "tools/call",
            params: [
                "name": "store_context",
                "arguments": [
                    "content": content,
                    "tags": tags,
                    "source": source
                ]
            ]
        )

        let response: MCPResponse = try await sendRequest(request)
        // Parse and return context ID
        return parseContextId(from: response.result.content[0])
    }

    func getRecentContexts(limit: Int = 10) async throws -> [Context] {
        // Implementation
    }

    private func sendRequest<T: Decodable>(_ request: MCPRequest) async throws -> T {
        var urlRequest = URLRequest(url: apiUrl)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let apiKey = apiKey {
            urlRequest.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        }
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await URLSession.shared.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw MCPError.networkError
        }

        return try JSONDecoder().decode(T.self, from: data)
    }
}
```

**B. SwiftUI Views**
```swift
// ios/LLMKnowledgeHub/ContentView.swift
import SwiftUI

struct ContentView: View {
    @StateObject private var mcpClient = MCPClient()
    @State private var newContext = ""
    @State private var tags = ""

    var body: some View {
        NavigationView {
            VStack {
                // Submit new context
                Form {
                    Section("New Knowledge") {
                        TextEditor(text: $newContext)
                            .frame(height: 100)
                        TextField("Tags (comma-separated)", text: $tags)
                        Button("Submit") {
                            Task {
                                try await mcpClient.storeContext(
                                    content: newContext,
                                    tags: tags.split(separator: ",").map(String.init),
                                    source: "ios-app"
                                )
                                newContext = ""
                                tags = ""
                                await loadRecentContexts()
                            }
                        }
                    }
                }

                // Recent contexts
                List(mcpClient.recentContexts) { context in
                    VStack(alignment: .leading) {
                        Text(context.content)
                            .font(.body)
                        HStack {
                            Text(context.source)
                                .font(.caption)
                                .foregroundColor(.secondary)
                            Spacer()
                            Text(formatDate(context.timestamp))
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Knowledge Hub")
            .task {
                await loadRecentContexts()
            }
        }
    }

    private func loadRecentContexts() async {
        do {
            try await mcpClient.getRecentContexts()
        } catch {
            print("Error loading contexts: \(error)")
        }
    }
}
```

**C. App Configuration**
- [ ] Add API key storage (Keychain)
- [ ] Settings screen for server URL
- [ ] Offline support with local cache
- [ ] Push notifications for shared knowledge (optional)

**Deliverables**:
- Functional iOS app with MCP integration
- Context browsing and submission
- Settings and configuration UI
- TestFlight beta ready

**Phase 3 Success Criteria**:
✅ Resources browsable via MCP protocol
✅ Batch operations working
✅ TypeScript SDK published and documented
✅ Comprehensive docs with examples
✅ iOS app functional and tested

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| **Phase 1: Critical Security** | 5-7 days | Auth, validation, testing |
| **Phase 2: Reliability** | 5-7 days | Monitoring, backups, CI/CD |
| **Phase 3: Enhancements** | 5-6 days | Advanced features, docs, SDK |
| **Buffer** | 2-3 days | Bug fixes, polish |
| **TOTAL** | **17-23 days** | Production-ready MCP server |

---

## Resource Requirements

### Technical Skills Needed
- TypeScript/JavaScript (required)
- Cloudflare Workers experience (helpful)
- Testing frameworks (Vitest) (can learn)
- CI/CD basics (GitHub Actions) (can learn)
- SwiftUI (for iOS app) (optional)

### Infrastructure
- ✅ Cloudflare Workers account (already have)
- ✅ GitHub repository (already have)
- Cloudflare Analytics Engine (optional - free tier)
- Error tracking service (optional - Sentry free tier)
- Domain for production (optional)

### Time Commitment
- **Full-time**: 3 weeks
- **Part-time (20hr/week)**: 6-8 weeks
- **Nights/weekends (10hr/week)**: 12-15 weeks

---

## Risk Mitigation

### Risk 1: Authentication Complexity
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Use battle-tested libraries (no custom crypto)
- Start with simple API key auth (not OAuth)
- Test thoroughly with security tools (OWASP ZAP)

### Risk 2: D1 Database Limitations
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- D1 is production-ready as of 2024
- Keep queries simple and indexed
- Have backup/export strategy
- Consider migration path to Durable Objects if needed

### Risk 3: Scope Creep
**Probability**: High
**Impact**: Medium
**Mitigation**:
- Stick to roadmap phases
- Defer "nice-to-have" features to Phase 4
- Semantic search is explicitly optional
- iOS app can be v1.1 if needed

### Risk 4: Breaking Changes During Development
**Probability**: Low
**Impact**: High
**Mitigation**:
- Maintain staging environment
- Use feature flags for new features
- Version the API (`/v1/` prefix)
- Comprehensive testing before deployment

---

## Success Metrics (KPIs)

### Phase 1 Completion
- [ ] 0 critical security vulnerabilities (per OWASP scan)
- [ ] 70%+ test coverage
- [ ] All tests passing
- [ ] 401/429 error codes working correctly

### Phase 2 Completion
- [ ] Health check 99.9%+ uptime
- [ ] p95 latency < 200ms
- [ ] Daily backups successful for 7 consecutive days
- [ ] CI/CD deploys to staging without manual intervention

### Phase 3 Completion
- [ ] SDK published to npm registry
- [ ] Documentation scores 8+/10 (user survey)
- [ ] iOS app runs on TestFlight
- [ ] 3+ example applications working

### Production Readiness
- [ ] Load tested to 1000 req/min
- [ ] Error rate < 0.1%
- [ ] All documentation complete
- [ ] Rollback procedure tested
- [ ] 90%+ test coverage
- [ ] Security audit passed

---

## Post-Launch Plan (Phase 4 - Future)

### Weeks 4-6: Optimization
- Performance profiling and optimization
- Cost analysis and optimization
- User feedback incorporation
- Bug fixes

### Weeks 7-12: Advanced Features
- Semantic/vector search with Vectorize
- Multi-tenant support (separate namespaces)
- GraphQL API (in addition to MCP)
- Real-time subscriptions (WebSockets)
- Advanced analytics dashboard
- LLM fine-tuning on stored knowledge

### Ongoing
- Monthly security audits
- Quarterly dependency updates
- Community feature requests
- Integration with new MCP clients

---

## Decision Points

At the end of each phase, evaluate:

1. **Quality Gate**: Are all success criteria met?
2. **Scope Review**: Any features to defer/add?
3. **Resource Check**: On time and budget?
4. **Pivot Decision**: Continue to next phase or iterate?

**Go/No-Go Criteria for Production**:
- ✅ All Phase 1 & 2 tasks complete
- ✅ Security audit passed
- ✅ Load testing successful
- ✅ Documentation complete
- ✅ At least 1 successful staging deployment
- ✅ Rollback procedure tested
- ⚠️ Phase 3 can be post-launch if needed

---

## Getting Started

### Immediate Next Steps (Today)

1. **Review this roadmap** - Agree on scope and timeline
2. **Create project board** - Set up GitHub Projects or similar
3. **Initialize Phase 1** - Create branch `feature/phase-1-security`
4. **First task**: Set up `package.json` and TypeScript config

### Week 1 Kickoff Checklist

- [ ] Roadmap approved
- [ ] GitHub Project board created
- [ ] Tasks assigned/prioritized
- [ ] Development environment ready
- [ ] Staging Cloudflare account set up
- [ ] Communication plan established (how often to sync)

---

## Questions for Consideration

Before starting, decide on:

1. **Timeline**: Full-time or part-time development?
2. **Scope**: All 3 phases, or just Phase 1+2 for v1.0?
3. **iOS App**: Priority or defer to v1.1?
4. **Semantic Search**: Build now or wait for user demand?
5. **Authentication**: API keys sufficient or need OAuth later?
6. **Monetization**: Free tier limits or fully open?

---

## Conclusion

This roadmap provides a clear path from your current **7/10 MCP readiness** to a **9.5/10 production-ready service**. The phased approach allows you to:

- Ship security improvements quickly (Phase 1)
- Build operational maturity (Phase 2)
- Add advanced features iteratively (Phase 3)
- Maintain quality throughout

The total investment of **15-20 working days** is realistic for a solo developer or small team, with clear checkpoints and success criteria along the way.

**Ready to start? Let's begin with Phase 1! 🚀**
