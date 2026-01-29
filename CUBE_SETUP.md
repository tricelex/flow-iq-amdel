# Cube.js Setup Guide

This guide walks you through setting up Cube.js for FlowIQ property analytics.

---

## What is Cube.js?

Cube.js is a **semantic layer** that sits between your database and the AI agent. It provides:

- **Centralized metric definitions** - Define "occupancy rate" once, use everywhere
- **Automatic SQL generation** - AI doesn't write SQL, it uses high-level API
- **Pre-aggregations** - Fast query performance through caching
- **Security** - Row-level security and access control
- **Consistency** - Same business logic across all queries

---

## Architecture

```
AI Agent
   │
   ├─> query_analytics(measures=["units.occupancy_rate"], dimensions=["properties.name"])
   │
   ▼
Cube.js Server
   │
   ├─> Validates query against semantic model (cube/model/cubes/*.yml)
   ├─> Generates optimized SQL
   ├─> Checks cache
   │
   ▼
Azure SQL Server
   │
   └─> Returns data
```

---

## Files Structure

```
cube/
├── cube.js                    # Cube.js configuration
└── model/
    └── cubes/
        ├── properties.yml     # Property metrics
        ├── units.yml          # Unit & occupancy metrics
        ├── tenants.yml        # Tenant & lease metrics
        └── transactions.yml   # Revenue metrics
```

---

## Setup Steps

### 1. Update Environment Variables

Your `.env` file should have:

```bash
# Cube.js Configuration
CUBE_API_URL=http://localhost:4000
CUBE_API_SECRET=flowiq-dev-secret-key

# Database Configuration (Azure SQL Server)
DB_DRIVER="ODBC Driver 18 for SQL Server"
DB_PORT=1433
DB_DATABASE="flow"
DB_USER="flowadmin"
DB_PASSWORD="your-password-here"
DB_SERVER="flow-app.database.windows.net"
```

### 2. Start Cube.js

The docker-compose.yml has been updated to include Cube.js.

**Option A: Start only Cube.js**
```bash
docker-compose up -d cube
```

**Option B: Start all services**
```bash
docker-compose up -d
```

### 3. Verify Cube.js is Running

Check container status:
```bash
docker-compose ps
```

You should see:
```
NAME                IMAGE                  STATUS
flowiq_cube         cubejs/cube:latest     Up
```

View logs:
```bash
docker-compose logs -f cube
```

You should see:
```
🔥 Cube.js server is listening on 4000
```

### 4. Test Cube.js API

**Manual test with curl:**
```bash
curl -H "Authorization: flowiq-dev-secret-key" \
     http://localhost:4000/cubejs-api/v1/meta
```

Should return JSON with cube definitions.

**Automated test:**
```bash
python scripts/test_cube.py
```

This will test:
1. ✅ Metadata fetch (available cubes, measures, dimensions)
2. ✅ Simple query execution
3. ✅ Occupancy query with filters

---

## Cube Models Explained

### Properties Cube (`cube/model/cubes/properties.yml`)

**Measures:**
- `properties.count` - Total number of properties

**Dimensions:**
- `properties.name` - Property name
- `properties.neighborhood` - Location (downtown, suburbs, etc.)
- `properties.property_type` - Type (residential, commercial, mixed)
- `properties.year_built` - Year built

**Usage:**
```javascript
{
  measures: ["properties.count"],
  dimensions: ["properties.neighborhood"]
}
```

---

### Units Cube (`cube/model/cubes/units.yml`)

**Key Measures:**
- `units.count` - Total units
- `units.occupied_count` - Occupied units
- `units.vacant_count` - Vacant units
- `units.occupancy_rate` - **Occupancy percentage** (most important!)
- `units.vacancy_rate` - Vacancy percentage
- `units.average_rent` - Average rent across units
- `units.total_potential_rent` - Sum of all rents

**Key Dimensions:**
- `units.status` - Unit status (occupied, vacant, maintenance)
- `units.unit_type` - Size (Studio, 1 Bedroom, 2 Bedroom, etc.)
- `units.bedrooms` - Number of bedrooms
- `properties.name` - Property name (via join)

**Usage - Get occupancy by property:**
```javascript
{
  measures: ["units.occupancy_rate", "units.count"],
  dimensions: ["properties.name"],
  order: {"units.occupancy_rate": "desc"}
}
```

**Usage - Filter downtown properties below 80%:**
```javascript
{
  measures: ["units.occupancy_rate"],
  dimensions: ["properties.name"],
  filters: [
    {member: "properties.neighborhood", operator: "equals", values: ["downtown"]},
    {member: "units.occupancy_rate", operator: "lt", values: ["80"]}
  ]
}
```

---

### Tenants Cube (`cube/model/cubes/tenants.yml`)

**Key Measures:**
- `tenants.count` - Total tenants
- `tenants.expiring_30_days` - Leases expiring in 30 days
- `tenants.expiring_60_days` - Leases expiring in 60 days
- `tenants.expiring_90_days` - Leases expiring in 90 days
- `tenants.revenue_at_risk_30_days` - Monthly revenue at risk (30 days)
- `tenants.total_monthly_rent` - Sum of all tenant rents

**Key Dimensions:**
- `tenants.full_name` - Tenant name
- `tenants.email` - Email address
- `tenants.phone` - Phone number
- `tenants.lease_end` - Lease expiration date (time dimension)
- `tenants.monthly_rent` - Rent amount
- `tenants.status` - Tenant status (active, notice, past)

**Usage - Get expiring leases:**
```javascript
{
  measures: ["tenants.count", "tenants.revenue_at_risk_30_days"],
  dimensions: ["tenants.full_name", "tenants.lease_end", "tenants.monthly_rent"],
  timeDimensions: [{
    dimension: "tenants.lease_end",
    dateRange: "next 30 days"
  }],
  order: {"tenants.lease_end": "asc"}
}
```

---

### Transactions Cube (`cube/model/cubes/transactions.yml`)

**Key Measures:**
- `transactions.net_revenue` - Revenue after refunds
- `transactions.gross_revenue` - Total revenue before refunds
- `transactions.rent_revenue` - Rent payments only
- `transactions.late_fee_revenue` - Late fees only
- `transactions.collection_rate` - Percentage of payments collected
- `transactions.count` - Number of transactions

**Key Dimensions:**
- `transactions.transaction_type` - Type (rent, late_fee, deposit, refund)
- `transactions.transaction_date` - Date (time dimension)
- `transactions.status` - Status (pending, completed, failed)

**Usage - Get revenue for last quarter:**
```javascript
{
  measures: ["transactions.net_revenue", "transactions.collection_rate"],
  dimensions: ["properties.name"],
  timeDimensions: [{
    dimension: "transactions.transaction_date",
    dateRange: "last quarter"
  }],
  order: {"transactions.net_revenue": "desc"}
}
```

---

## Common Query Patterns

### 1. Occupancy Overview

**Question:** "What's the occupancy rate for all properties?"

**Query:**
```javascript
{
  measures: ["units.occupancy_rate", "units.count", "units.occupied_count"],
  dimensions: ["properties.name"],
  order: {"units.occupancy_rate": "desc"}
}
```

---

### 2. Filtered Occupancy

**Question:** "Which downtown properties have occupancy below 80%?"

**Query:**
```javascript
{
  measures: ["units.occupancy_rate", "units.count"],
  dimensions: ["properties.name"],
  filters: [
    {member: "properties.neighborhood", operator: "equals", values: ["downtown"]},
    {member: "units.occupancy_rate", operator: "lt", values: ["80"]}
  ]
}
```

---

### 3. Expiring Leases

**Question:** "Show me leases expiring in the next 30 days"

**Query:**
```javascript
{
  measures: ["tenants.count"],
  dimensions: ["tenants.full_name", "tenants.email", "tenants.lease_end", "tenants.monthly_rent"],
  timeDimensions: [{
    dimension: "tenants.lease_end",
    dateRange: "next 30 days"
  }],
  order: {"tenants.lease_end": "asc"}
}
```

---

### 4. Revenue Summary

**Question:** "What was our revenue last month?"

**Query:**
```javascript
{
  measures: ["transactions.net_revenue", "transactions.gross_revenue"],
  dimensions: ["properties.name"],
  timeDimensions: [{
    dimension: "transactions.transaction_date",
    dateRange: "last month"
  }]
}
```

---

### 5. Period Comparison

**Question:** "Compare this quarter's occupancy to last quarter"

**Query (This Quarter):**
```javascript
{
  measures: ["units.occupancy_rate"],
  dimensions: ["properties.name"],
  timeDimensions: [{
    dimension: "tenants.lease_start",
    dateRange: "this quarter"
  }]
}
```

**Query (Last Quarter):**
```javascript
{
  measures: ["units.occupancy_rate"],
  dimensions: ["properties.name"],
  timeDimensions: [{
    dimension: "tenants.lease_start",
    dateRange: "last quarter"
  }]
}
```

Then calculate the difference in your tool.

---

## Troubleshooting

### Cube.js Won't Start

**Check logs:**
```bash
docker-compose logs cube
```

**Common issues:**

1. **Database connection error**
   - Verify DB credentials in .env
   - Check Azure SQL Server firewall allows Docker container IP
   - Ensure DB_SERVER is correct

2. **Model syntax error**
   - Check YAML syntax in cube/model/cubes/*.yml
   - Ensure indentation is correct
   - Look for missing required fields

3. **Port conflict**
   - Ensure port 4000 is not in use
   - Check: `lsof -i :4000`

### Queries Return No Data

**Possible causes:**

1. **Tables are empty**
   - Verify data exists: `SELECT COUNT(*) FROM properties`
   - Add sample data if needed

2. **Schema mismatch**
   - Cube models expect specific table/column names
   - Check `sql_table` in cube/*.yml matches your database
   - Verify column names match

3. **Filters too restrictive**
   - Try query without filters first
   - Verify dimension values exist (e.g., "downtown" neighborhood)

### Queries Are Slow

**Solutions:**

1. **Add pre-aggregations**
   - Already defined in cube models
   - Cube.js will build them automatically
   - Check logs: "Building pre-aggregations..."

2. **Add database indexes**
   ```sql
   CREATE INDEX idx_units_property_id ON units(property_id);
   CREATE INDEX idx_units_status ON units(status);
   CREATE INDEX idx_tenants_lease_end ON tenants(lease_end);
   ```

3. **Limit result size**
   - Add `limit: 100` to queries
   - Use pagination for large datasets

---

## Next Steps

Once Cube.js is running and tests pass:

1. ✅ **Create sample data** (if tables are empty)
   - Add 2-3 properties
   - Add 10-15 units
   - Add 5-10 tenants
   - Add some transactions

2. ✅ **Create Cube.js client** in `src/app/infra/cube/cube_client.py`
   - Async HTTP client using httpx
   - Methods: `get_meta()`, `query()`, `format_meta_for_prompt()`

3. ✅ **Create analytics tools** in `src/app/infra/flow_iq_agent/tools/`
   - `query_analytics` - Main flexible query tool
   - `get_occupancy_overview` - Pre-built occupancy query
   - `get_expiring_leases` - Pre-built lease expiration query
   - `get_revenue_summary` - Pre-built revenue query

4. ✅ **Enhance agent** with Cube.js context
   - Build system prompt with cube metadata
   - Add all tools to agent
   - Test with real queries

---

## Resources

- [Cube.js Documentation](https://cube.dev/docs)
- [Cube.js Data Schema](https://cube.dev/docs/schema/fundamentals/concepts)
- [Cube.js SQL Server Driver](https://cube.dev/docs/config/databases/mssql)
- [Our Architecture Plan](./PROJECT_ANALYSIS.md)
- [Integration Checklist](./INTEGRATION_CHECKLIST.md)
