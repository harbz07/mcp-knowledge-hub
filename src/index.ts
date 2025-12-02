// src/index.ts
interface Env {
  KNOWLEDGE_DB: D1Database;
  KNOWLEDGE_FILES: R2Bucket;
}

interface MCPRequest {
  jsonrpc: string;
  id: string | number;
  method: string;
  params?: any;
}

interface MCPResponse {
  jsonrpc: string;
  id: string | number;
  result?: any;
  error?: {
    code: number;
    message: string;
    data?: any;
  };
}

interface Context {
  id?: string;
  content: string;
  tags: string[];
  source: string; // which LLM/tool created this
  timestamp: string;
  metadata?: Record<string, any>;
}

interface EventInput {
  title: string;
  description?: string;
  happened_at?: string;
  who: string[];
  why: string[];
}

interface EventEffect {
  target_id: string;
  target_kind: string;
  summary: string;
  valence: string;
  intensity: number;
}

const DEFAULT_CLIENT_ID = 'public';

const EVENTS_CYPHER_SCHEMA = `Key Blocks Enabling Processes
1. ==Who Block (Participants and Targets)==
==Encodes relationality, identifying who is involved or affected in an event.==
==Utilizes Cypher patterns to map participants and considered targets, ensuring the agent's ID is always included for self-relationality.==
==Memory | participant-map:== cypher FOREACH (name IN ev.who | MERGE (person:Person {name: name}) MERGE (person)-[:PARTICIPATED_IN]->(e) )
==Reflection | relation-consider:== cypher OPTIONAL MATCH (e)-[:HAD_EFFECT_ON]->(f:Effect)-[:WITH_RESPECT_TO]->(t:Target) WHERE t.id = aid OR t.id
IN r.considered_targets
1. Why Block (Catalysts and Reasons)
Captures motivations and tensions as :Catalyst nodes, allowing for reusable and multi-faceted episodes.
Cypher for motivations: cypher FOREACH (reason IN ev.why | MERGE (c:Catalyst {description: reason}) MERGE (e)-[:CATALYZED_BY]->(c) )
Integration with Cerebral SDK
The Hippocampus Module integrates through a two-step process: - Thalamus Module: Creates :Capture nodes, representing intake with scores. - Episodicization:
Transforms captures into :Event nodes, incorporating Who/Why blocks and Effects/Reflections for relational exploration.
This integration supports the biomimetic core of the Cerebral SDK, ensuring stable personality, temporal coherence, and agent partnership, while maintaining a clear
distinction between intake and episodic hubs.
Current Schema Recap
Based on our iterations, the schema we've converged on for the Hippocampus Module (Neo4j) is biomimetic episodic memory: :Capture for thalamic intake (raw, scored
events), :Event as relational hubs (with Who, Why, Effects blocks), and :Reflection for agent-specific slices (prioritizing who_context for relationality). This supports
free agent generation while grounding in shared objectivity, with Thalamus scoring handling significance but not reflections (processed in Prefrontal Cache). No unilateral
noise in core Events; agents generate artifacts via Reflections, which can trigger new Captures.
Write-Memory Snippet (Event Creation)
WITH $event AS ev, $place AS placeName, $effects AS effs
MERGE (e:Event {
 happened_at: datetime(ev.happened_at),
 main_place: placeName
})
SET e.title = ev.title, e.description = ev.description
// Where Block (Place)
MERGE (p:Place {name: placeName})
MERGE (e)-[:HELD_AT]->(p)
// Who Block (Participants)
FOREACH (name IN ev.who |
 MERGE (person:Person {name: name})
 MERGE (person)-[:PARTICIPATED_IN]->(e)
)
// Why Block (Catalysts)
FOREACH (reason IN ev.why |
 MERGE (c:Catalyst {description: reason})
 MERGE (e)-[:CATALYZED_BY]->(c)
)
// Effects Block (Targets)
FOREACH (eff IN effs |
 MERGE (t:Target {id: eff.target_id, kind: eff.target_kind})
 MERGE (f:Effect {summary: eff.summary})
 SET f.valence = eff.valence, f.intensity = eff.intensity
 MERGE (e)-[:HAD_EFFECT_ON]->(f)
 MERGE (f)-[:WITH_RESPECT_TO]->(t)
)
RETURN e
Search-Memory Snippet (Episode Retrieval)
WITH $event_id AS eid, $agent_id AS aid
MATCH (e:Event {id: eid})
OPTIONAL MATCH (e)-[:HELD_AT]->(p:Place) // Where
OPTIONAL MATCH (e)-[:CATALYZED_BY]->(c:Catalyst) // Why
OPTIONAL MATCH (e)-[:PARTICIPATED_IN]<-[:PARTICIPATED_IN]-(person:Person) // Who (participants)
OPTIONAL MATCH (e)-[:HAD_EFFECT_ON]->(f:Effect)-[:WITH_RESPECT_TO]->(t:Target)
WHERE t.id = aid // Agent-relative effects
OPTIONAL MATCH (ref:Reflection)-[:ABOUT_EVENT]->(e)
WHERE ref.from_agent = aid // Prior reflections
RETURN e, p, collect(DISTINCT c) AS catalysts, collect(DISTINCT person) AS participants,
 collect({effect: f, target: t}) AS agent_effects, collect(DISTINCT ref) AS reflections
Reflect and Write-Reflection Snippet (Agent Standpoint)
WITH $event_id AS eid, $agent_id AS aid, $reflection AS r
MATCH (e:Event {id: eid})
MERGE (a:Agent {id: aid})
// Agent-relative who (self + considered)
OPTIONAL MATCH (e)-[:HAD_EFFECT_ON]->(f:Effect)-[:WITH_RESPECT_TO]->(t:Target)
WHERE t.id = aid OR t.id IN r.considered_targets
OPTIONAL MATCH (e)-[:HELD_AT]->(p:Place) // Where
OPTIONAL MATCH (e)-[:CATALYZED_BY]->(c:Catalyst) // How/Why
CREATE (ref:Reflection {
 summary: r.summary,
 valence: r.valence,
 entry_date: datetime(),
 who_context: [aid] + collect(DISTINCT t.id), // Self first for relationality
 where_context: p.name,
 how_context: collect(DISTINCT c.description)
})
MERGE (ref)-[:ABOUT_EVENT]->(e)
MERGE (ref)-[:FROM_AGENT]->(a)
RETURN ref`;

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS for MCP clients
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('MCP server expects POST requests', { status: 405 });
    }

    try {
      const mcpRequest: MCPRequest = await request.json();
      const response = await handleMCPRequest(mcpRequest, env);
      
      return new Response(JSON.stringify(response), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    } catch (error) {
      console.error('MCP request error:', error);
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id: null,
        error: {
          code: -32603,
          message: 'Internal error',
          data: error instanceof Error ? error.message : 'Unknown error'
        }
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  },
};

async function handleMCPRequest(request: MCPRequest, env: Env): Promise<MCPResponse> {
  const { method, params, id } = request;

  try {
    let result: any;

    switch (method) {
      case 'initialize':
        result = {
          protocolVersion: '2024-11-05',
          capabilities: {
            tools: {},
            transports: {
              stdio: true,
              https: true
            }
          },
          serverInfo: {
            name: 'knowledge-hub-mcp',
            version: '1.1.0',
            httpUrl: 'https://knowledge-hub-mcp.harveytagalicud7.workers.dev',
            stdioProxy: 'node scripts/stdio-proxy.js'
          }
        };
        break;

      case 'tools/list':
        result = {
          tools: [
            {
              name: 'store_context',
              description: 'Store a piece of context/knowledge for sharing between LLMs',
              inputSchema: {
                type: 'object',
                properties: {
                  content: { type: 'string', description: 'The content to store' },
                  tags: { type: 'array', items: { type: 'string' }, description: 'Tags for categorization' },
                  source: { type: 'string', description: 'Which LLM/tool is storing this' },
                  metadata: { type: 'object', description: 'Additional metadata' },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                },
                required: ['content', 'source']
              }
            },
            {
              name: 'search_contexts',
              description: 'Search stored contexts by keywords, tags, or source',
              inputSchema: {
                type: 'object',
                properties: {
                  query: { type: 'string', description: 'Text to search for' },
                  tags: { type: 'array', items: { type: 'string' }, description: 'Filter by tags' },
                  source: { type: 'string', description: 'Filter by source LLM/tool' },
                  limit: { type: 'number', description: 'Max results to return', default: 10 },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                }
              }
            },
            {
              name: 'get_recent_contexts',
              description: 'Get the most recently stored contexts',
              inputSchema: {
                type: 'object',
                properties: {
                  limit: { type: 'number', description: 'Max results to return', default: 5 },
                  source: { type: 'string', description: 'Filter by source LLM/tool' },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                }
              }
            },
            {
              name: 'store_file',
              description: 'Store a file in R2 storage for sharing between LLMs',
              inputSchema: {
                type: 'object',
                properties: {
                  filename: { type: 'string', description: 'Name of the file' },
                  content: { type: 'string', description: 'File content (base64 for binary)' },
                  contentType: { type: 'string', description: 'MIME type of the file' },
                  tags: { type: 'array', items: { type: 'string' }, description: 'Tags for categorization' },
                  source: { type: 'string', description: 'Which LLM/tool is storing this' },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                },
                required: ['filename', 'content', 'source']
              }
            },
            {
              name: 'get_file',
              description: 'Retrieve a file from R2 storage',
              inputSchema: {
                type: 'object',
                properties: {
                  filename: { type: 'string', description: 'Name of the file to retrieve' },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                },
                required: ['filename'],
              }
            },
            {
              name: 'list_files',
              description: 'List stored files with optional filtering',
              inputSchema: {
                type: 'object',
                properties: {
                  prefix: { type: 'string', description: 'Filter by filename prefix' },
                  limit: { type: 'number', description: 'Max results to return', default: 20 },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                }
              }
            },
            {
              name: 'ensure_client_bucket',
              description: 'Create or describe a client-scoped knowledge bucket',
              inputSchema: {
                type: 'object',
                properties: {
                  clientId: { type: 'string', description: 'Unique client identifier' },
                  label: { type: 'string', description: 'Friendly label for the client bucket' }
                },
                required: ['clientId']
              }
            },
            {
              name: 'record_event',
              description: 'Capture a structured event into the client-shared events hub',
              inputSchema: {
                type: 'object',
                properties: {
                  event: {
                    type: 'object',
                    properties: {
                      title: { type: 'string' },
                      description: { type: 'string' },
                      happened_at: { type: 'string' },
                      who: { type: 'array', items: { type: 'string' } },
                      why: { type: 'array', items: { type: 'string' } }
                    },
                    required: ['title', 'who', 'why']
                  },
                  place: { type: 'string', description: 'Where the event occurred' },
                  effects: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        target_id: { type: 'string' },
                        target_kind: { type: 'string' },
                        summary: { type: 'string' },
                        valence: { type: 'string' },
                        intensity: { type: 'number' }
                      },
                      required: ['target_id', 'target_kind', 'summary', 'valence', 'intensity']
                    },
                    description: 'Effects block describing targets and impacts'
                  },
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' }
                },
                required: ['event', 'place']
              }
            },
            {
              name: 'list_events',
              description: 'List structured events for a client with newest first',
              inputSchema: {
                type: 'object',
                properties: {
                  clientId: { type: 'string', description: 'Client bucket id (default: public)' },
                  limit: { type: 'number', description: 'Max events to return', default: 10 }
                }
              }
            },
            {
              name: 'get_cypher_event_schema',
              description: 'Return the Cypher schema and templates that back the events hub',
              inputSchema: {
                type: 'object',
                properties: {}
              }
            }
          ]
        };
        break;

      case 'tools/call':
        result = await handleToolCall(params, env);
        break;

      default:
        throw new Error(`Unknown method: ${method}`);
    }
}
}

async function handleToolCall(params: any, env: Env) {
  const { name, arguments: args } = params;

  switch (name) {
    case 'store_context':
      return await storeContext(args, env);
    case 'search_contexts':
      return await searchContexts(args, env);
    case 'get_recent_contexts':
      return await getRecentContexts(args, env);
    case 'store_file':
      return await storeFile(args, env);
    case 'get_file':
      return await getFile(args, env);
    case 'list_files':
      return await listFiles(args, env);
    case 'ensure_client_bucket':
      return await ensureClientBucket(args, env);
    case 'record_event':
      return await recordEvent(args, env);
    case 'list_events':
      return await listEvents(args, env);
    case 'get_cypher_event_schema':
      return {
        content: ['Cypher schema for events hub:', EVENTS_CYPHER_SCHEMA],
        isError: false
      };
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function normalizeClientId(clientId?: string): string {
  if (!clientId) return DEFAULT_CLIENT_ID;
  const trimmed = clientId.trim();
  return trimmed.length > 0 ? trimmed : DEFAULT_CLIENT_ID;
}

async function ensureClientRecord(env: Env, clientId?: string, label?: string): Promise<string> {
  const normalized = normalizeClientId(clientId);
  const createdAt = new Date().toISOString();

  await env.KNOWLEDGE_DB.prepare(`
    INSERT INTO clients (id, label, created_at) VALUES (?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET label = coalesce(?, label)
  `).bind(normalized, label ?? normalized, createdAt, label ?? normalized).run();

  return normalized;
}

async function ensureClientBucket(args: any, env: Env) {
  const { clientId, label } = args;
  const normalized = await ensureClientRecord(env, clientId, label);

  return {
    content: [`Client bucket '${normalized}' is ready`, `label: ${label ?? normalized}`],
    isError: false
  };
}

async function storeContext(args: any, env: Env) {
  const { content, tags = [], source, metadata = {}, clientId } = args;
  const id = crypto.randomUUID();
  const timestamp = new Date().toISOString();
  const scopedClientId = await ensureClientRecord(env, clientId);

  await env.KNOWLEDGE_DB.prepare(`
    INSERT INTO contexts (id, content, tags, source, timestamp, metadata, client_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    content,
    JSON.stringify(tags),
    source,
    timestamp,
    JSON.stringify(metadata),
    scopedClientId
  ).run();

  return {
    content: [`Stored context with ID: ${id} in client bucket '${scopedClientId}'`],
    isError: false
  };
}

async function searchContexts(args: any, env: Env) {
  const { query, tags, source, limit = 10, clientId } = args;

  let sql = 'SELECT * FROM contexts WHERE client_id = ?';
  const scopedClientId = normalizeClientId(clientId);
  const bindings: any[] = [scopedClientId];

  if (query) {
    sql += ' AND content LIKE ?';
    bindings.push(`%${query}%`);
  }

  if (source) {
    sql += ' AND source = ?';
    bindings.push(source);
  }

  if (tags && tags.length > 0) {
    // Simple tag search - in production you'd want proper JSON querying
    const tagConditions = tags.map(() => 'tags LIKE ?').join(' OR ');
    sql += ` AND (${tagConditions})`;
    tags.forEach((tag: string) => bindings.push(`%"${tag}"%`));
  }

  sql += ' ORDER BY timestamp DESC LIMIT ?';
  bindings.push(limit);

  const results = await env.KNOWLEDGE_DB.prepare(sql).bind(...bindings).all();

  const contexts = results.results?.map((row: any) => ({
    id: row.id,
    content: row.content,
    tags: JSON.parse(row.tags || '[]'),
    source: row.source,
    timestamp: row.timestamp,
    metadata: JSON.parse(row.metadata || '{}'),
    clientId: row.client_id
  })) || [];

  return {
    content: [`Found ${contexts.length} contexts for client '${scopedClientId}':`, JSON.stringify(contexts, null, 2)],
    isError: false
  };
}

async function getRecentContexts(args: any, env: Env) {
  const { limit = 5, source, clientId } = args;
  const scopedClientId = normalizeClientId(clientId);

  let sql = 'SELECT * FROM contexts WHERE client_id = ?';
  const bindings: any[] = [scopedClientId];

  if (source) {
    sql += ' AND source = ?';
    bindings.push(source);
  }

  sql += ' ORDER BY timestamp DESC LIMIT ?';
  bindings.push(limit);

  const results = await env.KNOWLEDGE_DB.prepare(sql).bind(...bindings).all();

  const contexts = results.results?.map((row: any) => ({
    id: row.id,
    content: row.content,
    tags: JSON.parse(row.tags || '[]'),
    source: row.source,
    timestamp: row.timestamp,
    metadata: JSON.parse(row.metadata || '{}'),
    clientId: row.client_id
  })) || [];

  return {
    content: [`Recent ${contexts.length} contexts for client '${scopedClientId}':`, JSON.stringify(contexts, null, 2)],
    isError: false
  };
}

async function storeFile(args: any, env: Env) {
  const { filename, content, contentType = 'text/plain', tags = [], source, clientId } = args;
  const scopedClientId = await ensureClientRecord(env, clientId);
  const key = `${scopedClientId}/${filename}`;

  // Store the file in R2 with client scoping
  await env.KNOWLEDGE_FILES.put(key, content, {
    customMetadata: {
      source,
      tags: JSON.stringify(tags),
      uploadTime: new Date().toISOString(),
      clientId: scopedClientId
    },
    httpMetadata: {
      contentType
    }
  });

  return {
    content: [`File '${filename}' stored successfully in client bucket '${scopedClientId}'`],
    isError: false
  };
}

async function getFile(args: any, env: Env) {
  const { filename, clientId } = args;
  const scopedClientId = normalizeClientId(clientId);
  const key = `${scopedClientId}/${filename}`;

  const file = await env.KNOWLEDGE_FILES.get(key);

  if (!file) {
    return {
      content: [`File '${filename}' not found for client '${scopedClientId}'`],
      isError: true
    };
  }

  const content = await file.text();
  const metadata = file.customMetadata || {};

  return {
    content: [
      `File: ${filename}`,
      `Client: ${scopedClientId}`,
      `Source: ${metadata.source || 'unknown'}`,
      `Upload Time: ${metadata.uploadTime || 'unknown'}`,
      `Tags: ${metadata.tags || '[]'}`,
      `Content:`,
      content
    ],
    isError: false
  };
}

async function listFiles(args: any, env: Env) {
  const { prefix, limit = 20, clientId } = args;
  const scopedClientId = normalizeClientId(clientId);

  const options: any = { limit, prefix: `${scopedClientId}/` };
  if (prefix) {
    options.prefix = `${scopedClientId}/${prefix}`;
  }

  const files = await env.KNOWLEDGE_FILES.list(options);

  const fileList = files.objects.map(obj => ({
    name: obj.key.replace(`${scopedClientId}/`, ''),
    size: obj.size,
    modified: obj.uploaded,
    metadata: obj.customMetadata
  }));

  return {
    content: [`Found ${fileList.length} files for client '${scopedClientId}':`, JSON.stringify(fileList, null, 2)],
    isError: false
  };
}

async function recordEvent(args: any, env: Env) {
  const { event, place, effects = [], clientId } = args;

  if (!event?.title || !event?.who || !event?.why) {
    throw new Error('event.title, event.who, and event.why are required');
  }

  const scopedClientId = await ensureClientRecord(env, clientId);
  const id = crypto.randomUUID();
  const happenedAt = event.happened_at || new Date().toISOString();
  const createdAt = new Date().toISOString();

  await env.KNOWLEDGE_DB.prepare(`
    INSERT INTO events (id, client_id, title, description, happened_at, place, who, why, effects, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    scopedClientId,
    event.title,
    event.description ?? '',
    happenedAt,
    place,
    JSON.stringify(event.who ?? []),
    JSON.stringify(event.why ?? []),
    JSON.stringify(effects ?? []),
    createdAt
  ).run();

  return {
    content: [
      `Recorded event '${event.title}' (${id}) for client '${scopedClientId}'`,
      'Cypher schema available via get_cypher_event_schema',
      JSON.stringify({ event, place, effects, id, clientId: scopedClientId }, null, 2)
    ],
    isError: false
  };
}

async function listEvents(args: any, env: Env) {
  const { clientId, limit = 10 } = args;
  const scopedClientId = normalizeClientId(clientId);

  const results = await env.KNOWLEDGE_DB.prepare(`
    SELECT * FROM events WHERE client_id = ? ORDER BY datetime(happened_at) DESC LIMIT ?
  `).bind(scopedClientId, limit).all();

  const events = results.results?.map((row: any) => ({
    id: row.id,
    title: row.title,
    description: row.description,
    happened_at: row.happened_at,
    place: row.place,
    who: JSON.parse(row.who || '[]'),
    why: JSON.parse(row.why || '[]'),
    effects: JSON.parse(row.effects || '[]'),
    clientId: row.client_id,
    created_at: row.created_at
  })) || [];

  return {
    content: [`Found ${events.length} events for client '${scopedClientId}':`, JSON.stringify(events, null, 2)],
    isError: false
  };
}