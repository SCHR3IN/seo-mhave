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

const token = process.env.YANDEX_METRIKA_TOKEN;
const defaultCounterId = process.env.YANDEX_METRIKA_COUNTER;

if (!token) {
  console.error("YANDEX_METRIKA_TOKEN env variable is required");
  process.exit(1);
}

const server = new Server(
  {
    name: "metrika-ai",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

async function request(path, options = {}) {
  const url = `https://api-metrika.yandex.net${path}`;
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
        name: "get_counter_info",
        description: "Get detailed information about a Yandex Metrika counter",
        inputSchema: {
          type: "object",
          properties: {
            counterId: {
              type: "string",
              description: "Optional counter ID. Defaults to env.YANDEX_METRIKA_COUNTER"
            }
          }
        }
      },
      {
        name: "list_goals",
        description: "List all configured goals for the counter",
        inputSchema: {
          type: "object",
          properties: {
            counterId: {
              type: "string",
              description: "Optional counter ID. Defaults to env.YANDEX_METRIKA_COUNTER"
            }
          }
        }
      },
      {
        name: "create_js_event_goal",
        description: "Create a new JavaScript event goal in Yandex Metrika",
        inputSchema: {
          type: "object",
          properties: {
            name: {
              type: "string",
              description: "The human-readable name of the goal"
            },
            eventId: {
              type: "string",
              description: "The JavaScript event ID (parameter) that triggers the goal"
            },
            counterId: {
              type: "string",
              description: "Optional counter ID. Defaults to env.YANDEX_METRIKA_COUNTER"
            }
          },
          required: ["name", "eventId"]
        }
      },
      {
        name: "get_analytics_report",
        description: "Fetch statistical report from Yandex Metrika Stat API",
        inputSchema: {
          type: "object",
          properties: {
            metrics: {
              type: "string",
              description: "Comma-separated list of metrics (e.g. 'ym:s:visits,ym:s:pageviews,ym:s:bounceRate')"
            },
            dimensions: {
              type: "string",
              description: "Comma-separated list of dimensions (e.g. 'ym:s:date', 'ym:s:trafficSource')"
            },
            date1: {
              type: "string",
              description: "Start date in YYYY-MM-DD format (or 'today', 'yesterday', '30daysAgo')"
            },
            date2: {
              type: "string",
              description: "End date in YYYY-MM-DD format (or 'today')"
            },
            counterId: {
              type: "string",
              description: "Optional counter ID. Defaults to env.YANDEX_METRIKA_COUNTER"
            }
          },
          required: ["metrics"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (requestCall) => {
  const { name, arguments: args = {} } = requestCall.params;
  const counterId = args.counterId || defaultCounterId;

  if (!counterId) {
    return {
      content: [{ type: "text", text: "Error: No counter ID specified and YANDEX_METRIKA_COUNTER env variable is not set." }],
      isError: true
    };
  }

  try {
    switch (name) {
      case "get_counter_info": {
        const data = await request(`/management/v1/counter/${counterId}`);
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
        };
      }

      case "list_goals": {
        const data = await request(`/management/v1/counter/${counterId}/goals`);
        return {
          content: [{ type: "text", text: JSON.stringify(data.goals || [], null, 2) }]
        };
      }

      case "create_js_event_goal": {
        const body = {
          goal: {
            name: args.name,
            type: "action",
            is_retargeting: 0,
            conditions: [
              {
                type: "exact",
                parameter: args.eventId
              }
            ]
          }
        };
        const data = await request(`/management/v1/counter/${counterId}/goals`, {
          method: "POST",
          body: JSON.stringify(body)
        });
        return {
          content: [{ type: "text", text: `Successfully created JS Event goal with ID ${data.goal.id}\n${JSON.stringify(data.goal, null, 2)}` }]
        };
      }

      case "get_analytics_report": {
        const params = new URLSearchParams({
          ids: counterId,
          metrics: args.metrics,
          ...(args.dimensions ? { dimensions: args.dimensions } : {}),
          date1: args.date1 || "30daysAgo",
          date2: args.date2 || "today"
        });
        const data = await request(`/stat/v1/data?${params.toString()}`);
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
console.error("Yandex Metrika MCP Server running...");
