# Performance Optimization Guide

## Overview

This document describes the performance optimization strategies implemented in URIS-AI to meet the performance requirements specified in Requirements 8.1, 8.2, and 8.3.

**Performance Requirements:**

- Response time ≤5 seconds for 95% of requests under normal load (Requirement 8.1)
- Handle 500 concurrent users (Requirement 8.2)
- Auto-scaling when concurrent users exceed 500 (Requirement 8.3)

## 1. Database Query Optimization

### 1.1 Performance Indexes

Additional indexes have been implemented to optimize frequently accessed queries:

#### Weather Data Indexes

- `idx_weather_date_desc`: Optimizes latest weather data queries with descending date order
- Improves performance of real-time weather data retrieval

#### Flood Events Indexes

- `idx_flood_severity`: Optimizes queries filtering by severity level
- Enables fast retrieval of high-severity flood events

#### Risk Scores Indexes

- `idx_risk_date_desc`: Optimizes latest risk score queries
- `idx_risk_region_date_desc`: Composite index for region-specific trend queries
- Significantly improves performance of risk trend analysis

#### Recommendations Indexes

- `idx_recommendations_active_urgency`: Optimizes active recommendations queries
- `idx_recommendations_expires`: Optimizes expired recommendations cleanup
- Enables efficient filtering of urgent recommendations

#### Public Facilities Indexes

- `idx_facilities_coords`: Optimizes spatial proximity queries
- `idx_facilities_operational`: Optimizes operational facilities queries
- Improves performance of alternative facility searches

#### Roads Indexes

- `idx_roads_main`: Optimizes main road queries
- Enables fast retrieval of critical road infrastructure

#### Users Indexes

- `idx_users_active`: Optimizes active users queries
- Improves authentication and authorization performance

### 1.2 Using Database Utilities

```python
from uris_ai.database.db_utils import create_performance_indexes
from uris_ai.models.database import get_db

# Create all performance indexes
db = next(get_db())
results = create_performance_indexes(db)

print(f"Created: {len(results['created'])} indexes")
print(f"Already exists: {len(results['already_exists'])} indexes")
print(f"Failed: {len(results['failed'])} indexes")
```

### 1.3 Query Performance Analysis

```python
from uris_ai.database.db_utils import analyze_query_performance, get_slow_queries

# Analyze a specific query
query = "SELECT * FROM risk_scores WHERE region_id = 1 ORDER BY date DESC"
plan = analyze_query_performance(db, query)

# Get slow queries
slow_queries = get_slow_queries(db, min_duration_ms=1000)
for query in slow_queries:
    print(f"Query ID: {query['query_id']}")
    print(f"Avg Duration: {query['avg_duration_ms']}ms")
    print(f"Executions: {query['execution_count']}")
```

### 1.4 Statistics Optimization

```python
from uris_ai.database.db_utils import optimize_table_statistics

# Update statistics for frequently queried tables
tables = ['risk_scores', 'weather_data', 'recommendations']
for table in tables:
    optimize_table_statistics(db, table)
```

## 2. Caching Strategy

### 2.1 Cache Architecture

URIS-AI uses Azure Cache for Redis to cache frequently accessed data:

- **Risk Scores**: Cached for 5 minutes (300 seconds)
- **Recommendations**: Cached for 5 minutes (300 seconds)
- **Region List**: Cached for 1 hour (3600 seconds)
- **User Info**: Cached for 10 minutes (600 seconds)

### 2.2 Cache Warming

Cache warming preloads frequently accessed data into cache on application startup or after cache invalidation.

#### Automatic Cache Warming on Startup

```python
from uris_ai.services.cache_service import CacheService
from uris_ai.models.database import get_db

cache = CacheService()
db = next(get_db())

# Warm all caches
results = cache.warm_all_caches(db)

print(f"Success: {results['success']}")
print(f"Total regions warmed: {results['total_regions_warmed']}")
```

#### Individual Cache Warming

```python
# Warm risk scores cache only
risk_results = cache.warm_risk_scores_cache(db)

# Warm recommendations cache only
rec_results = cache.warm_recommendations_cache(db)
```

### 2.3 Cache Invalidation

Cache is automatically invalidated when data changes:

```python
# Invalidate cache for a specific region
cache.invalidate_region_cache(region_id=1)

# Invalidate specific cache keys
cache.delete("risk:all_regions")
cache.delete_pattern("risk:trend:*")
```

### 2.4 Cache Monitoring

```python
# Get cache statistics
stats = cache.get_cache_stats()

print(f"Available: {stats['available']}")
print(f"Total Keys: {stats['total_keys']}")
print(f"Hit Rate: {stats['hit_rate']}%")
print(f"Used Memory: {stats['used_memory']}")
```

### 2.5 Cache Integration in API Endpoints

All API endpoints automatically use caching:

```python
@router.get("/{region_id}/risk")
async def get_region_risk(
    region_id: int,
    db: Session = Depends(get_db),
    cache: CacheService = Depends(lambda: CacheService()),
):
    # Try cache first
    cached = cache.get_risk_score(region_id)
    if cached is not None:
        return RiskScoreResponse(**cached)

    # Query database if cache miss
    # ... database query ...

    # Store in cache for future requests
    cache.set_risk_score(region_id, response.model_dump())

    return response
```

## 3. Auto-Scaling Configuration

### 3.1 Azure App Service Auto-Scaling

Auto-scaling is configured in Terraform for production environments:

#### Scaling Triggers

**CPU-based Scaling:**

- Scale out when CPU > 70% (average over 5 minutes)
- Scale in when CPU < 30% (average over 10 minutes)

**Memory-based Scaling:**

- Scale out when Memory > 75% (average over 5 minutes)

**HTTP Queue-based Scaling:**

- Scale out when HTTP Queue Length > 100 requests
- Adds 2 instances for faster response to traffic spikes

**Response Time-based Scaling:**

- Scale out when Average Response Time > 5 seconds
- Ensures SLA compliance (Requirement 8.1)

#### Scaling Profiles

**Default Profile:**

- Minimum: 1 instance
- Default: 2 instances
- Maximum: 10 instances

**Peak Hours Profile (Weekdays 7 AM - 7 PM):**

- Minimum: 2 instances
- Default: 3 instances
- Maximum: 10 instances
- Ensures capacity during high-traffic periods

**Off-Peak Hours Profile (Weekdays 7 PM - 7 AM, Weekends):**

- Minimum: 1 instance
- Default: 1 instance
- Maximum: 5 instances
- Reduces costs during low-traffic periods

### 3.2 Scaling Cooldown Periods

- Scale out cooldown: 5 minutes
- Scale in cooldown: 10 minutes
- Prevents rapid scaling oscillations

### 3.3 Monitoring Auto-Scaling

Auto-scaling events are logged in Azure Monitor and Application Insights:

```bash
# View auto-scaling events
az monitor autoscale show \
  --resource-group uris-ai-rg \
  --name uris-ai-autoscale-production

# View scaling history
az monitor autoscale show \
  --resource-group uris-ai-rg \
  --name uris-ai-autoscale-production \
  --query "profiles[].rules[].scaleAction"
```

### 3.4 Manual Scaling Override

For planned events or maintenance:

```bash
# Manually scale to specific instance count
az appservice plan update \
  --name uris-ai-asp-production \
  --resource-group uris-ai-rg \
  --number-of-workers 5

# Re-enable auto-scaling
az monitor autoscale update \
  --resource-group uris-ai-rg \
  --name uris-ai-autoscale-production \
  --enabled true
```

## 4. Performance Testing

### 4.1 Load Testing with Locust

Comprehensive load tests are implemented in `tests/load/` to verify performance requirements.

#### Quick Start

```bash
# Setup test users (first time only)
python tests/load/setup_test_users.py

# Run baseline test (100 users)
python tests/load/run_load_tests.py baseline --host http://localhost:8000

# Run target load test (500 users - Requirement 8.2)
python tests/load/run_load_tests.py target --host http://localhost:8000

# Run stress test (750 users - Requirement 8.3)
python tests/load/run_load_tests.py stress --host http://localhost:8000

# Analyze results
python tests/load/analyze_results.py tests/load/results/*_stats.csv
```

#### Test Scenarios

1. **Baseline Test**: 100 users, 5 minutes
   - Establishes baseline performance metrics
2. **Target Load Test**: 500 users, 10 minutes
   - Verifies Requirement 8.2 (handle 500 concurrent users)
   - Validates Requirement 8.1 (response time SLA)

3. **Stress Test**: 750 users, 15 minutes
   - Verifies Requirement 8.3 (auto-scaling)
   - Tests system behavior under high load

4. **Spike Test**: 500 users, rapid spawn
   - Tests response to sudden traffic spikes

#### User Behavior Simulation

Load tests simulate realistic user behavior:

- 40% viewing all region risk scores
- 25% viewing individual region risk scores
- 15% viewing risk trends
- 10% viewing recommendations
- 10% finding safe routes

See `tests/load/README.md` for detailed documentation.

### 4.2 Performance Benchmarks

Target benchmarks based on requirements:

- **Response Time**: ≤5 seconds for 95% of requests (Requirement 8.1)
- **Throughput**: Support 500 concurrent users (Requirement 8.2)
- **Availability**: 99% uptime (Requirement 8.4)

### 4.3 Monitoring Performance Metrics

Key metrics to monitor in Azure Application Insights:

- Average response time
- 95th percentile response time
- Request rate (requests per second)
- Error rate
- CPU and memory utilization
- Cache hit rate
- Database query duration

## 5. Best Practices

### 5.1 Database Optimization

1. **Use indexes wisely**: Create indexes for frequently queried columns
2. **Update statistics regularly**: Keep query optimizer informed
3. **Monitor slow queries**: Identify and optimize problematic queries
4. **Use connection pooling**: Reuse database connections efficiently

### 5.2 Caching Best Practices

1. **Cache frequently accessed data**: Risk scores, recommendations, region lists
2. **Set appropriate TTLs**: Balance freshness vs. performance
3. **Warm cache on startup**: Preload critical data
4. **Invalidate on updates**: Keep cache consistent with database
5. **Monitor cache hit rate**: Aim for >80% hit rate

### 5.3 Auto-Scaling Best Practices

1. **Set appropriate thresholds**: Based on actual load patterns
2. **Use multiple metrics**: CPU, memory, queue length, response time
3. **Configure cooldown periods**: Prevent scaling oscillations
4. **Test scaling behavior**: Verify scaling works under load
5. **Monitor scaling events**: Track when and why scaling occurs

### 5.4 Application-Level Optimization

1. **Use async/await**: For I/O-bound operations
2. **Batch database queries**: Reduce round trips
3. **Implement pagination**: For large result sets
4. **Compress responses**: Reduce network transfer time
5. **Use CDN**: For static assets

## 6. Troubleshooting

### 6.1 Slow Response Times

1. Check cache hit rate - low hit rate indicates cache warming needed
2. Review slow query logs - identify problematic database queries
3. Check auto-scaling status - ensure sufficient instances are running
4. Monitor external API latency - weather API, OSM API delays

### 6.2 High CPU Usage

1. Review application logs for errors or infinite loops
2. Check for inefficient queries or missing indexes
3. Verify auto-scaling is enabled and working
4. Consider upgrading App Service Plan SKU

### 6.3 Cache Issues

1. Verify Redis connection - check connection string and firewall rules
2. Monitor Redis memory usage - ensure sufficient capacity
3. Check cache TTL settings - adjust if needed
4. Review cache invalidation logic - ensure consistency

### 6.4 Auto-Scaling Not Working

1. Verify auto-scaling is enabled in Azure Portal
2. Check scaling rules and thresholds
3. Review cooldown periods - may be preventing scaling
4. Check App Service Plan SKU - some SKUs don't support auto-scaling

## 7. Deployment Checklist

Before deploying performance optimizations:

- [ ] Create all performance indexes in database
- [ ] Configure cache warming on application startup
- [ ] Enable auto-scaling in Terraform configuration
- [ ] Set up performance monitoring in Application Insights
- [ ] Run load tests to verify performance requirements
- [ ] Document baseline performance metrics
- [ ] Configure alerting for performance degradation
- [ ] Test cache invalidation logic
- [ ] Verify auto-scaling triggers work correctly
- [ ] Update runbook with troubleshooting procedures

## 8. References

- [Azure App Service Auto-Scaling](https://docs.microsoft.com/en-us/azure/app-service/manage-scale-up)
- [Azure Cache for Redis Best Practices](https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/cache-best-practices)
- [SQL Server Index Design Guide](https://docs.microsoft.com/en-us/sql/relational-databases/sql-server-index-design-guide)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
