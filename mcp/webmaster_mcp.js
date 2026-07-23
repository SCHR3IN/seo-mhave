import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import fs from 'fs';
import path from 'path';

function loadEnv() {
  try {
    const envPath = path.join(process.cwd(), '.env');
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf8');
      content.split('\n').forEach(line => {
        const match = line.match(/^\s*([\w.\-]+)\s*=\s*(.*)?\s*$/);
        if (match) {
          const key = match[1];
          let value = match[2] || '';
          if (value.length > 0 && value.startsWith('"') && value.endsWith('"')) {
            value = value.substring(1, value.length - 1);
          }
          process.env[key] = value;
        }
      });
    }
  } catch (e) {
    console.error("Failed to load local .env:", e);
  }
}
loadEnv();

const token = process.env.YANDEX_WEBMASTER_TOKEN;
const defaultUserId = process.env.YANDEX_WEBMASTER_USER_ID;
const defaultHostId = process.env.YANDEX_WEBMASTER_HOST_ID;

if (!token) {
  console.error("YANDEX_WEBMASTER_TOKEN env variable is required");
  process.exit(1);
}

const server = new Server(
  {
    name: "webmaster-ai",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

async function request(path, options = {}) {
  const url = `https://api.webmaster.yandex.net${path}`;
  const headers = {
    "Authorization": `OAuth ${token}`,
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const text = await response.text();
  let json;
  try {
    json = JSON.parse(text);
  } catch (e) {
    throw new Error(`Failed to parse response: ${text}`);
  }

  if (!response.ok) {
    throw new Error(json.message || json.errors?.[0]?.message || `HTTP error ${response.status}`);
  }

  return json;
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_host_summary",
        description: "Get summary indexation and health status of a verified site in Webmaster",
        inputSchema: {
          type: "object",
          properties: {
            hostId: {
              type: "string",
              description: "Optional host ID (e.g. 'https:mhave.ru:443'). Defaults to env.YANDEX_WEBMASTER_HOST_ID"
            },
            userId: {
              type: "string",
              description: "Optional user ID. Defaults to env.YANDEX_WEBMASTER_USER_ID"
            }
          }
        }
      },
      {
        name: "list_sitemaps",
        description: "List all sitemaps registered for the site in Yandex Webmaster",
        inputSchema: {
          type: "object",
          properties: {
            hostId: {
              type: "string",
              description: "Optional host ID. Defaults to env"
            },
            userId: {
              type: "string",
              description: "Optional user ID. Defaults to env"
            }
          }
        }
      },
      {
        name: "add_sitemap",
        description: "Submit a new Sitemap file path to Yandex Webmaster",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "Full URL of the sitemap file (e.g., 'https://mhave.ru/sitemap.xml')"
            },
            hostId: {
              type: "string",
              description: "Optional host ID. Defaults to env"
            },
            userId: {
              type: "string",
              description: "Optional user ID. Defaults to env"
            }
          },
          required: ["url"]
        }
      },
      {
        name: "reindex_url",
        description: "Submit a specific page URL to Yandex Webmaster for prioritized re-indexing (recrawl queue)",
        inputSchema: {
          type: "object",
          properties: {
            url: {
              type: "string",
              description: "Full page URL to re-index (e.g. 'https://mhave.ru/catalog/odezhda/')"
            },
            hostId: {
              type: "string",
              description: "Optional host ID. Defaults to env"
            },
            userId: {
              type: "string",
              description: "Optional user ID. Defaults to env"
            }
          },
          required: ["url"]
        }
      },
      {
        name: "get_popular_queries",
        description: "Fetch popular search queries bringing traffic to the site",
        inputSchema: {
          type: "object",
          properties: {
            hostId: {
              type: "string",
              description: "Optional host ID. Defaults to env"
            },
            userId: {
              type: "string",
              description: "Optional user ID. Defaults to env"
            },
            limit: {
              type: "number",
              description: "Optional limit of results, max 500"
            }
          }
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (requestCall) => {
  const { name, arguments: args = {} } = requestCall.params;
  const userId = args.userId || defaultUserId;
  const hostId = args.hostId || defaultHostId;

  if (!userId || !hostId) {
    return {
      content: [{ type: "text", text: "Error: userId or hostId not specified and defaults not set in environment." }],
      isError: true
    };
  }

  try {
    switch (name) {
      case "get_host_summary": {
        const data = await request(`/v4/user/${userId}/hosts/${hostId}/summary`);
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
        };
      }

      case "list_sitemaps": {
        const data = await request(`/v4/user/${userId}/hosts/${hostId}/sitemaps`);
        return {
          content: [{ type: "text", text: JSON.stringify(data.sitemaps || [], null, 2) }]
        };
      }

      case "add_sitemap": {
        const body = {
          url: args.url
        };
        const data = await request(`/v4/user/${userId}/hosts/${hostId}/sitemaps`, {
          method: "POST",
          body: JSON.stringify(body)
        });
        return {
          content: [{ type: "text", text: `Successfully submitted sitemap: ${JSON.stringify(data, null, 2)}` }]
        };
      }

      case "reindex_url": {
        const body = {
          url: args.url
        };
        const data = await request(`/v4/user/${userId}/hosts/${hostId}/recrawl/queue`, {
          method: "POST",
          body: JSON.stringify(body)
        });
        return {
          content: [{ type: "text", text: `Successfully queued page for re-indexing:\n${JSON.stringify(data, null, 2)}` }]
        };
      }

      case "get_popular_queries": {
        const params = new URLSearchParams({
          order_by: "TOTAL_SHOWS"
        });
        params.append("query_indicator", "TOTAL_SHOWS");
        params.append("query_indicator", "TOTAL_CLICKS");
        params.append("query_indicator", "AVG_SHOW_POSITION");
        const data = await request(`/v4/user/${userId}/hosts/${hostId}/search-queries/popular?${params.toString()}`);
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error executing tool ${name}: ${error.message}` }],
      isError: true
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Yandex Webmaster MCP Server running...");
