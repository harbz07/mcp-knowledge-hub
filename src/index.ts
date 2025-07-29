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
            tools: {}
          },
          serverInfo: {
            name: 'knowledge-hub-mcp',
            version: '1.0.0'
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
                  metadata: { type: 'object', description: 'Additional metadata' }
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
                  limit: { type: 'number', description: 'Max results to return', default: 10 }
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
                  source: { type: 'string', description: 'Filter by source LLM/tool' }
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
                  source: { type: 'string', description: 'Which LLM/tool is storing this' }
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
                  filename: { type: 'string', description: 'Name of the file to retrieve' }
                },
                required: ['filename']
              }
            },
            {
              name: 'list_files',
              description: 'List stored files with optional filtering',
              inputSchema: {
                type: 'object',
                properties: {
                  prefix: { type: 'string', description: 'Filter by filename prefix' },
                  limit: { type: 'number', description: 'Max results to return', default: 20 }
                }
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

    return {
      jsonrpc: '2.0',
      id,
      result
    };
  } catch (error) {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32602,
        message: error instanceof Error ? error.message : 'Unknown error'
      }
    };
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
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

async function storeContext(args: any, env: Env) {
  const { content, tags = [], source, metadata = {} } = args;
  const id = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  await env.KNOWLEDGE_DB.prepare(`
    INSERT INTO contexts (id, content, tags, source, timestamp, metadata)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(
    id,
    content,
    JSON.stringify(tags),
    source,
    timestamp,
    JSON.stringify(metadata)
  ).run();

  return {
    content: [`Stored context with ID: ${id}`],
    isError: false
  };
}

async function searchContexts(args: any, env: Env) {
  const { query, tags, source, limit = 10 } = args;
  
  let sql = 'SELECT * FROM contexts WHERE 1=1';
  const bindings: any[] = [];

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
    metadata: JSON.parse(row.metadata || '{}')
  })) || [];

  return {
    content: [`Found ${contexts.length} contexts:`, JSON.stringify(contexts, null, 2)],
    isError: false
  };
}

async function getRecentContexts(args: any, env: Env) {
  const { limit = 5, source } = args;
  
  let sql = 'SELECT * FROM contexts';
  const bindings: any[] = [];

  if (source) {
    sql += ' WHERE source = ?';
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
    metadata: JSON.parse(row.metadata || '{}')
  })) || [];

  return {
    content: [`Recent ${contexts.length} contexts:`, JSON.stringify(contexts, null, 2)],
    isError: false
  };
}

async function storeFile(args: any, env: Env) {
  const { filename, content, contentType = 'text/plain', tags = [], source } = args;
  
  // Store the file in R2
  await env.KNOWLEDGE_FILES.put(filename, content, {
    customMetadata: {
      source,
      tags: JSON.stringify(tags),
      uploadTime: new Date().toISOString()
    },
    httpMetadata: {
      contentType
    }
  });

  return {
    content: [`File '${filename}' stored successfully`],
    isError: false
  };
}

async function getFile(args: any, env: Env) {
  const { filename } = args;
  
  const file = await env.KNOWLEDGE_FILES.get(filename);
  
  if (!file) {
    return {
      content: [`File '${filename}' not found`],
      isError: true
    };
  }

  const content = await file.text();
  const metadata = file.customMetadata || {};

  return {
    content: [
      `File: ${filename}`,
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
  const { prefix, limit = 20 } = args;
  
  const options: any = { limit };
  if (prefix) {
    options.prefix = prefix;
  }

  const files = await env.KNOWLEDGE_FILES.list(options);
  
  const fileList = files.objects.map(obj => ({
    name: obj.key,
    size: obj.size,
    modified: obj.uploaded,
    metadata: obj.customMetadata
  }));

  return {
    content: [`Found ${fileList.length} files:`, JSON.stringify(fileList, null, 2)],
    isError: false
  };
}