#!/usr/bin/env node
// Simple STDIO bridge that forwards MCP JSON-RPC messages to the HTTPS worker
const readline = require('node:readline');
const { stdin: input, stdout: output } = require('node:process');

const endpoint = process.env.MCP_HTTPS_ENDPOINT || 'https://knowledge-hub-mcp.harveytagalicud7.workers.dev';

const rl = readline.createInterface({ input, crlfDelay: Infinity });

rl.on('line', async (line) => {
  if (!line.trim()) return;
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: line
    });
    const text = await response.text();
    output.write(text + '\n');
  } catch (error) {
    const errPayload = {
      jsonrpc: '2.0',
      id: null,
      error: {
        code: -32001,
        message: 'STDIO proxy error',
        data: error instanceof Error ? error.message : String(error)
      }
    };
    output.write(JSON.stringify(errPayload) + '\n');
  }
});

rl.on('close', () => {
  process.exit(0);
});
