# FlowIQ API Testing Guide

**Status:** MVP Complete - Ready for Testing
**Date:** 2026-01-27

This guide shows how to test the FlowIQ analytics API.

---

## Prerequisites

1. **Start Cube.js:**
   ```bash
   docker-compose up cube
   ```

2. **Start FastAPI server:**
   ```bash
   # From project root
   uvicorn app.api.main:app --reload
   ```

3. **Set OpenAI API Key (for chat testing):**
   ```bash
   export OPENAI_API_KEY="sk-proj-your-key-here"
   ```

---

## Health Check Endpoints

### Basic Health Check
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "flowiq",
  "version": "0.1.0"
}
```

### Database Health Check
```bash
curl http://localhost:8000/api/v1/health/db
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Cube.js Health Check
```bash
curl http://localhost:8000/api/v1/health/cube
```

**Expected Response:**
```json
{
  "status": "healthy",
  "cube": "connected",
  "cubes_available": 3,
  "api_url": "http://localhost:4000"
}
```

### Comprehensive Health Check
```bash
curl http://localhost:8000/api/v1/health/all
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "flowiq",
  "version": "0.1.0",
  "components": {
    "database": {
      "status": "healthy",
      "error": null
    },
    "cube": {
      "status": "healthy",
      "cubes_available": 3,
      "error": null
    }
  }
}
```

---

## Chat Endpoint (Requires OpenAI API Key)

### Simple Query
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many customers do we have?"
  }'
```

### Query with Conversation ID
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who are the top 5 customers?",
    "conversation_id": "test-session-123"
  }'
```

### Streaming Response Format

The chat endpoint returns Server-Sent Events (SSE):

```
event: raw_response_event
data: {"delta":"We","type":"text_delta"}

event: raw_response_event
data: {"delta":" have","type":"text_delta"}

event: tool_call_item
data: {"name":"get_customer_analysis","arguments":"...","type":"function_tool_call"}

event: tool_call_output_item
data: {"output":"...","type":"tool_call_output"}

event: raw_response_event
data: {"delta":"599 customers","type":"text_delta"}

event: message_output_item
data: {"output":"We have 599 customers in total.","type":"message_output"}
```

---

## Example Queries for Testing

Once you have a valid OpenAI API key, try these queries:

### Customer Queries
- "How many customers do we have?"
- "Who are the top 10 customers by rental count?"
- "Show me customer analysis"

### Revenue Queries
- "What's our total revenue?"
- "Who are the top 5 customers by revenue?"
- "Show me revenue breakdown by customer"

### Rental Queries
- "How many rentals are currently outstanding?"
- "What's our rental return rate?"
- "Show me rental statistics"

### Complex Queries
- "Who are the customers with the most outstanding rentals?"
- "What's the average payment amount?"
- "Show me revenue for the last month"

### Metadata Queries
- "What metrics can you show me?"
- "What data is available?"

---

## API Documentation

Once the server is running, access interactive API docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Automated Testing

### Test API Routes (No OpenAI Key Required)
```bash
python scripts/test_api_routes.py
```

This tests:
- ✅ Health check endpoints
- ✅ Cube.js connectivity
- ✅ API documentation accessibility
- ✅ Chat endpoint structure

### Test FlowIQ Components (No OpenAI Key Required)
```bash
python scripts/test_flow_iq_components.py
```

This tests:
- ✅ Context builder
- ✅ System prompt generation
- ✅ Agent configuration
- ✅ Tool registration

### Test Analytics Tools (No OpenAI Key Required)
```bash
python scripts/test_analytics_tools.py
```

This tests:
- ✅ Customer queries
- ✅ Revenue queries
- ✅ Rental queries
- ✅ Metadata queries
- ✅ Time dimension queries

### Test Full Agent (Requires OpenAI Key)
```bash
python scripts/test_flow_iq_agent.py
```

This tests:
- Full agent initialization
- Real chat queries
- Tool calling
- Streaming responses

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

### Cube.js not connected
```bash
# Check if Cube.js is running
docker-compose ps

# Check Cube.js logs
docker-compose logs cube

# Restart Cube.js
docker-compose restart cube
```

### Database connection failed
```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5433

# Check database exists
psql -h localhost -p 5433 -U postgres -d neon_sample -c "SELECT 1"
```

### OpenAI API errors
- Check API key is set: `echo $OPENAI_API_KEY`
- Verify key is valid at https://platform.openai.com/api-keys
- Check API usage limits

---

## Success Criteria

### MVP Complete ✅
- [x] Cube.js running and connected
- [x] CubeClient integrated
- [x] 5 analytics tools working
- [x] Agent with full system prompt
- [x] Streaming chat endpoint
- [x] Health checks
- [x] Error handling

### Ready for Production ⏳
- [ ] Valid OpenAI API key configured
- [ ] Full end-to-end testing
- [ ] Load testing
- [ ] Security review
- [ ] Monitoring setup
- [ ] Deployment configuration

---

## Next Steps

1. **Add OpenAI API Key:**
   - Get key from https://platform.openai.com/api-keys
   - Add to `.env`: `OPENAI_API_KEY=sk-proj-...`

2. **Test Chat Flow:**
   - Run: `python scripts/test_flow_iq_agent.py`
   - Try queries via curl or Postman
   - Test in Swagger UI at http://localhost:8000/docs

3. **Phase 6+ (Optional):**
   - Add property management data models
   - Implement RAG system with Pinecone
   - Add authentication/authorization
   - Deploy to production

---

## Quick Start (TL;DR)

```bash
# 1. Start services
docker-compose up cube -d
uvicorn app.api.main:app --reload

# 2. Test health (no API key needed)
python scripts/test_api_routes.py

# 3. Add OpenAI key (for chat)
export OPENAI_API_KEY="sk-proj-your-key"

# 4. Test chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many customers do we have?"}'
```

🎉 **That's it! Your FlowIQ analytics assistant is ready to use!**
