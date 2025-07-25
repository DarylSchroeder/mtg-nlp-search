# 🚀 Path to Done: From MVP → Amazon Q Integration

## Overview
Transform the MTG NLP Search FastAPI service into an Amazon Q Developer tool using Model Context Protocol (MCP).

## Current Status: Step 1 ✅

---

## 1. Finalize Your MVP FastAPI Service (Current Stage)
- ✅ Validate /search endpoint and Swagger UI
- 🔍 Add error handling and logging as needed
- 🧹 Ensure your codebase is clean, modular, and testable

## 2. Enhance the Service for Production Readiness
- [ ] Add `python-dotenv` to load .env
- [ ] Improve parsing resilience (handle GPT responses gracefully)
- [ ] Add caching if performance is required (Redis or simple LRU)
- [ ] Add TCGPlayer price lookup (with affiliate links) for enrichment
- [ ] Fix deprecated OpenAI API usage
- [ ] Replace unsafe `eval()` with proper JSON parsing
- [ ] Add input validation

## 3. Create an MCP Server Wrapper
Amazon Q uses Model Context Protocol (MCP) to interact with external tools. You'll need to wrap your search API inside an MCP-compatible server:

- [ ] Define tools (e.g. `search_cards_nlp`) with JSON Schema inputs and outputs
- [ ] Spin up an MCP server to expose your tool over HTTP or gRPC
- [ ] Reference: [Using MCP with Amazon Q Developer documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp.html)

## 4. Register the MCP Tool with Amazon Q Developer
- [ ] Install and configure Q Developer CLI
- [ ] Point it to your MCP server, so Q can discover:
  - Tool name, description, input schema (prompt), output schema (cards)
- [ ] Q Developer CLI will auto-load your tool and make it available in Q sessions

## 5. Seed Amazon Q Prompts
Train Q (or create Q prompts) like:
- [ ] `SearchMTG(prompts: string) -> structured card responses`
- [ ] Build prompt templates describing tasks: "Find me a 2-mana instant that …"

## 6. Test Interactions in Q Developer CLI
- [ ] Run Amazon Q Developer
- [ ] Use `/tools` to verify availability of your MCP tool
- [ ] Test sample queries:
  - "Find a 2 mana instant that counters spells and creates tokens."

## 7. Finalize and Go Live
- [ ] Polish tool descriptions and validation based on feedback
- [ ] Optionally create help prompts and guardrails
- [ ] Deploy to production (AWS Lambda, EC2, or container)
- [ ] If using Amazon Q Business, use `CreatePlugin` or `CreateDataSource` APIs to register the tool for your organization

---

## 🗺 Summary at a Glance

| Step | Action |
|------|--------|
| 1 | Finalize and test your FastAPI /search endpoint |
| 2 | Add error handling, caching, enrichment |
| 3 | Wrap your API as an MCP server with defined tools/schema |
| 4 | Register the tool in Q Developer CLI → Q can invoke it |
| 5 | Write and seed task prompts for card search use cases |
| 6 | Test within Amazon Q Developer interactively |
| 7 | Optionally promote to Q Business: register plugin or data source via API |

## Key Resources
- [Amazon Q Developer MCP Documentation](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp.html)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Scryfall API Documentation](https://scryfall.com/docs/api)
- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)

## Example Queries to Test
- "Find a 2 mana instant that counters spells and creates tokens"
- "Show me red creatures with power 4 or greater that cost 3 mana"
- "I need a planeswalker that can draw cards and costs less than 5 mana"
- "Find artifacts that can tap for mana and have converted mana cost 2"
