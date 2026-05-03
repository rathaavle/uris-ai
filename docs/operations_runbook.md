# URIS-AI Operations Runbook

**Urban Risk Intelligence System - Operations & Incident Response Guide**

**Version:** 1.0.0  
**Last Updated:** January 20, 2024

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Monitoring & Alerting](#monitoring--alerting)
4. [Incident Response Procedures](#incident-response-procedures)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Escalation Procedures](#escalation-procedures)
8. [Contact Information](#contact-information)

**Requirements:** 8.4

---

## Overview

### Purpose

This runbook provides operational procedures for monitoring, maintaining, and troubleshooting the URIS-AI system. It is intended for DevOps engineers, SREs, and on-call personnel.

### System Overview

URIS-AI is a cloud-based flood risk intelligence system deployed on Microsoft Azure, consisting of:

- **FastAPI Backend** - REST API for risk data and recommendations
- **Streamlit Dashboard** - Interactive web dashboard
- **Azure SQL Database** - Operational data storage
- **Azure Blob Storage** - Raw data and ML models
- **Azure Cache for Redis** - Response caching
- **Azure Application Insights** - Monitoring and telemetry
- **Azure Key Vault** - Secrets management

### Service Level Objectives (SLOs)

- **Availability:** 99% uptime (30-day rolling window)
- **Response Time:** <5 seconds for 95% of requests
- **Data Freshness:** <60 seconds latency for risk updates
- **Error Rate:** <1% of total requests

### On-Call Responsibilities

- Monitor system health and alerts
- Respond to incidents within 15 minutes
- Escalate critical issues appropriately
- Document all incidents and resolutions
- Perform routine maintenance tasks

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Azure Front Door                          │
│                  (Load Balancer + CDN)                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        ↓                                           ↓
┌──────────────────┐                      ┌──────────────────┐
│  FastAPI Backend │                      │ Streamlit Dashboard│
│  (App Service)   │                      │  (App Service)    │
└──────────────────┘                      └──────────────────┘
        ↓                                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   Azure Cache for Redis                      │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Azure SQL Database                         │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Azure Blob Storage                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Azure Resources

| Resource                | Name                           | Purpose                     |
| ----------------------- | ------------------------------ | --------------------------- |
| Resource Group          | `uris-ai-rg`                   | Container for all resources |
| App Service Plan        | `uris-ai-asp-production`       | Hosting plan for web apps   |
| App Service (API)       | `uris-ai-api-production`       | FastAPI backend             |
| App Service (Dashboard) | `uris-ai-dashboard-production` | Streamlit dashboard         |
| SQL Server              | `uris-ai-sql-server`           | Database server             |
| SQL Database            | `uris-ai-db`                   | Operational database        |
| Storage Account         | `urisaistorage`                | Blob storage                |
| Redis Cache             | `uris-ai-redis`                | Caching layer               |
| Key Vault               | `uris-ai-keyvault`             | Secrets management          |
| Application Insights    | `uris-ai-appinsights`          | Monitoring                  |

---

## Monitoring & Alerting

### Monitoring Dashboard

**Azure Portal:**

1. Navigate to: https://portal.azure.com
2. Go to Resource Group: `uris-ai-rg`
3. Select: `uris-ai-appinsights`
4. View: Application Dashboard

**Key Metrics to Monitor:**

- **Request Rate** - Requests per minute
- **Response Time** - Average response time (ms)
- **Error Rate** - Percentage of failed requests
- **Availability** - Uptime percentage
- **CPU Usage** - App Service CPU utilization
- **Memory Usage** - App Service memory utilization
- **Database DTU** - Database resource utilization
- **Cache Hit Rate** - Redis cache effectiveness

### Alert Types

#### Critical Alerts (P1)

**1. System Down**

- **Trigger:** Health check fails for 2 consecutive minutes
- **Impact:** Complete service outage
- **Response Time:** Immediate (within 5 minutes)
- **Notification:** PagerDuty, SMS, Email

**2. Database Connection Failure**

- **Trigger:** 3 consecutive database connection failures
- **Impact:** API requests failing, data not accessible
- **Response Time:** Immediate (within 5 minutes)
- **Notification:** PagerDuty, SMS, Email

**3. High Error Rate**

- **Trigger:** Error rate >10% for 5 minutes
- **Impact:** Degraded service, user experience affected
- **Response Time:** Within 15 minutes
- **Notification:** PagerDuty, Email

**4. Security Breach**

- **Trigger:** Unauthorized access attempt detected
- **Impact:** Potential data breach, system compromise
- **Response Time:** Immediate (within 5 minutes)
- **Notification:** PagerDuty, SMS, Email, Security Team

#### Warning Alerts (P2)

**1. Slow Response Time**

- **Trigger:** Average response time >5 seconds for 5 minutes
- **Impact:** Poor user experience
- **Response Time:** Within 30 minutes
- **Notification:** Email, Slack

**2. High Resource Utilization**

- **Trigger:** CPU or memory >80% for 10 minutes
- **Impact:** Potential performance degradation
- **Response Time:** Within 1 hour
- **Notification:** Email, Slack

**3. Data Staleness**

- **Trigger:** Data not updated for >10 minutes
- **Impact:** Outdated risk predictions
- **Response Time:** Within 30 minutes
- **Notification:** Email, Slack

**4. Cache Unavailable**

- **Trigger:** Redis cache connection fails
- **Impact:** Increased database load, slower responses
- **Response Time:** Within 1 hour
- **Notification:** Email, Slack

### Accessing Alerts

**Azure Portal:**

```bash
# View active alerts
az monitor alert list --resource-group uris-ai-rg --output table

# View alert history
az monitor activity-log list --resource-group uris-ai-rg --max-events 50
```

**Application Insights:**

1. Navigate to Application Insights in Azure Portal
2. Go to: Alerts → Alert Rules
3. View: Active Alerts and Alert History

---

## Incident Response Procedures

### Incident Response Workflow

```
Incident Detected
       ↓
Acknowledge Alert (within 5 min)
       ↓
Assess Severity (P1/P2/P3)
       ↓
Investigate Root Cause
       ↓
Implement Fix or Workaround
       ↓
Verify Resolution
       ↓
Document Incident
       ↓
Post-Mortem (for P1 incidents)
```

### Severity Levels

| Severity      | Description                        | Response Time     | Examples                                       |
| ------------- | ---------------------------------- | ----------------- | ---------------------------------------------- |
| P1 (Critical) | Complete outage or security breach | 5 minutes         | System down, database failure, security breach |
| P2 (High)     | Degraded service                   | 30 minutes        | Slow response, high error rate, data staleness |
| P3 (Medium)   | Minor issues                       | 4 hours           | Non-critical feature broken, cosmetic issues   |
| P4 (Low)      | Informational                      | Next business day | Feature requests, documentation updates        |

### P1 Incident Response

**1. System Down**

**Symptoms:**

- Health check endpoint returns 503 or times out
- Users cannot access dashboard or API
- Application Insights shows no requests

**Immediate Actions:**

```bash
# 1. Check App Service status
az webapp show --resource-group uris-ai-rg --name uris-ai-api-production --query state

# 2. Check recent deployments
az webapp deployment list --resource-group uris-ai-rg --name uris-ai-api-production

# 3. Check application logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-api-production

# 4. Restart App Service if needed
az webapp restart --resource-group uris-ai-rg --name uris-ai-api-production
```

**Escalation:**

- If restart doesn't resolve: Escalate to DevOps Lead
- If infrastructure issue: Escalate to Azure Support

**2. Database Connection Failure**

**Symptoms:**

- API returns 500 errors
- Logs show "database connection failed"
- Readiness check shows database: "error"

**Immediate Actions:**

```bash
# 1. Check database status
az sql db show --resource-group uris-ai-rg --server uris-ai-sql-server --name uris-ai-db --query status

# 2. Check firewall rules
az sql server firewall-rule list --resource-group uris-ai-rg --server uris-ai-sql-server

# 3. Check connection string in Key Vault
az keyvault secret show --vault-name uris-ai-keyvault --name AZURE-SQL-CONNECTION-STRING

# 4. Test database connectivity
# From App Service console:
python -c "import sqlalchemy; engine = sqlalchemy.create_engine('connection-string'); engine.connect()"
```

**Workaround:**

- If database is down: Enable read-only mode (serves cached data only)
- If firewall issue: Add App Service IP to firewall rules

**Escalation:**

- If database is down: Escalate to Database Admin
- If Azure issue: Open Azure Support ticket

**3. High Error Rate**

**Symptoms:**

- Error rate >10% in Application Insights
- Multiple 500 errors in logs
- Users reporting errors

**Immediate Actions:**

```bash
# 1. Check error logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-api-production | grep ERROR

# 2. Check Application Insights for error patterns
# Navigate to Application Insights → Failures

# 3. Check recent code changes
git log --oneline -10

# 4. Rollback if recent deployment caused issue
./scripts/rollback_deployment.sh
```

**Investigation:**

- Identify error pattern (specific endpoint, user role, time of day)
- Check external API dependencies (weather API, etc.)
- Review recent configuration changes

**Escalation:**

- If code issue: Escalate to Development Team
- If external API issue: Contact API provider

**4. Security Breach**

**Symptoms:**

- Unauthorized access attempts in logs
- Unusual traffic patterns
- Security alerts from Azure Security Center

**Immediate Actions:**

```bash
# 1. Review security logs
az monitor activity-log list --resource-group uris-ai-rg --max-events 100 | grep -i "security"

# 2. Check for unauthorized access
# Review Application Insights → Users → Authentication failures

# 3. Rotate compromised credentials
az keyvault secret set --vault-name uris-ai-keyvault --name SECRET-KEY --value "new-secret-key"

# 4. Block malicious IPs
az webapp config access-restriction add \
  --resource-group uris-ai-rg \
  --name uris-ai-api-production \
  --rule-name block-malicious-ip \
  --action Deny \
  --ip-address 192.168.1.1 \
  --priority 100
```

**Escalation:**

- **Immediately** escalate to Security Team
- Document all findings
- Preserve logs for forensic analysis

### P2 Incident Response

**1. Slow Response Time**

**Symptoms:**

- Average response time >5 seconds
- Users reporting slow dashboard
- Application Insights shows high latency

**Investigation:**

```bash
# 1. Check App Service metrics
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/uris-ai-rg/providers/Microsoft.Web/sites/uris-ai-api-production \
  --metric "AverageResponseTime" \
  --start-time 2024-01-20T00:00:00Z \
  --end-time 2024-01-20T23:59:59Z

# 2. Check database performance
az sql db show --resource-group uris-ai-rg --server uris-ai-sql-server --name uris-ai-db --query currentServiceObjectiveName

# 3. Check slow queries in Application Insights
# Navigate to: Performance → Dependencies → SQL queries

# 4. Check cache hit rate
az redis show --resource-group uris-ai-rg --name uris-ai-redis --query enableNonSslPort
```

**Mitigation:**

- Scale up App Service if CPU/memory high
- Optimize slow database queries
- Increase cache TTL for frequently accessed data
- Enable query result caching

**2. High Resource Utilization**

**Symptoms:**

- CPU or memory >80%
- App Service performance degraded
- Potential for service disruption

**Investigation:**

```bash
# 1. Check current resource usage
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/uris-ai-rg/providers/Microsoft.Web/sites/uris-ai-api-production \
  --metric "CpuPercentage,MemoryPercentage" \
  --start-time 2024-01-20T00:00:00Z

# 2. Check number of instances
az appservice plan show --resource-group uris-ai-rg --name uris-ai-asp-production --query sku

# 3. Check active requests
# Navigate to Application Insights → Live Metrics
```

**Mitigation:**

```bash
# Scale out (add instances)
az appservice plan update \
  --resource-group uris-ai-rg \
  --name uris-ai-asp-production \
  --number-of-workers 5

# Scale up (larger instance)
az appservice plan update \
  --resource-group uris-ai-rg \
  --name uris-ai-asp-production \
  --sku P2V2
```

**3. Data Staleness**

**Symptoms:**

- Data not updated for >10 minutes
- "Last Updated" timestamp is old
- Users seeing outdated risk scores

**Investigation:**

```bash
# 1. Check Azure Function status (data ingestion)
az functionapp show --resource-group uris-ai-rg --name uris-ai-functions --query state

# 2. Check function logs
az functionapp log tail --resource-group uris-ai-rg --name uris-ai-functions

# 3. Check external API connectivity
curl -I https://api.weather.com/health

# 4. Check database for recent updates
# Query: SELECT MAX(date) FROM risk_scores;
```

**Mitigation:**

- Restart Azure Function if stopped
- Check external API credentials
- Manually trigger data ingestion if needed
- Verify network connectivity to external APIs

---

## Troubleshooting Guide

### Common Issues

#### Issue: API Returns 401 Unauthorized

**Symptoms:**

- API requests return 401 status code
- Error message: "Token tidak valid atau telah kadaluarsa"

**Diagnosis:**

```bash
# 1. Check if token is expired
# Decode JWT token at https://jwt.io

# 2. Check SECRET_KEY in Key Vault
az keyvault secret show --vault-name uris-ai-keyvault --name SECRET-KEY

# 3. Check authentication service logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-api-production | grep "auth"
```

**Resolution:**

- User needs to login again to get new token
- If SECRET_KEY changed, all existing tokens are invalid
- Check Azure AD configuration if using Azure AD

#### Issue: Dashboard Not Loading

**Symptoms:**

- Dashboard shows blank page or loading spinner
- Browser console shows errors
- Users cannot access dashboard

**Diagnosis:**

```bash
# 1. Check dashboard App Service status
az webapp show --resource-group uris-ai-rg --name uris-ai-dashboard-production --query state

# 2. Check dashboard logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-dashboard-production

# 3. Check API connectivity from dashboard
# From dashboard App Service console:
curl https://uris-ai-api-production.azurewebsites.net/health

# 4. Check browser console for JavaScript errors
```

**Resolution:**

- Restart dashboard App Service
- Check API_BASE_URL environment variable
- Clear browser cache
- Check CORS configuration in API

#### Issue: Cache Not Working

**Symptoms:**

- Slow API responses
- High database load
- Cache hit rate is 0%

**Diagnosis:**

```bash
# 1. Check Redis status
az redis show --resource-group uris-ai-rg --name uris-ai-redis --query provisioningState

# 2. Check Redis connectivity
az redis list-keys --resource-group uris-ai-rg --name uris-ai-redis

# 3. Test Redis connection
# From App Service console:
python -c "import redis; r = redis.from_url('redis-url'); r.ping()"

# 4. Check cache service logs
az webapp log tail --resource-group uris-ai-rg --name uris-ai-api-production | grep "cache"
```

**Resolution:**

- Verify REDIS_URL in Key Vault
- Check Redis firewall rules
- Restart Redis cache if needed
- Check cache service initialization in code

#### Issue: Database Query Timeout

**Symptoms:**

- API returns 500 errors
- Error message: "database query timeout"
- Slow response times

**Diagnosis:**

```bash
# 1. Check database DTU usage
az sql db show --resource-group uris-ai-rg --server uris-ai-sql-server --name uris-ai-db --query currentServiceObjectiveName

# 2. Check active queries
# Connect to database and run:
# SELECT * FROM sys.dm_exec_requests WHERE status = 'running';

# 3. Check for blocking queries
# SELECT * FROM sys.dm_exec_requests WHERE blocking_session_id <> 0;

# 4. Check database metrics
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/uris-ai-rg/providers/Microsoft.Sql/servers/uris-ai-sql-server/databases/uris-ai-db \
  --metric "dtu_consumption_percent"
```

**Resolution:**

- Kill long-running queries if needed
- Optimize slow queries (add indexes)
- Scale up database tier if DTU usage high
- Review query execution plans

#### Issue: External API Failure

**Symptoms:**

- Weather data not updating
- Error logs show "API request failed"
- Data staleness alerts

**Diagnosis:**

```bash
# 1. Test external API connectivity
curl -I https://api.weather.com/health

# 2. Check API credentials
az keyvault secret show --vault-name uris-ai-keyvault --name WEATHER-API-KEY

# 3. Check API rate limits
# Review API provider dashboard

# 4. Check network connectivity
# From App Service console:
ping api.weather.com
```

**Resolution:**

- Verify API credentials are valid
- Check API rate limits (may need to upgrade plan)
- Implement retry logic with exponential backoff
- Use cached data as fallback

### Diagnostic Commands

**Check App Service Health:**

```bash
# Status
az webapp show --resource-group uris-ai-rg --name uris-ai-api-production --query state

# Recent restarts
az webapp show --resource-group uris-ai-rg --name uris-ai-api-production --query lastModifiedTimeUtc

# Configuration
az webapp config appsettings list --resource-group uris-ai-rg --name uris-ai-api-production
```

**Check Database Health:**

```bash
# Status
az sql db show --resource-group uris-ai-rg --server uris-ai-sql-server --name uris-ai-db --query status

# DTU usage
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/uris-ai-rg/providers/Microsoft.Sql/servers/uris-ai-sql-server/databases/uris-ai-db \
  --metric "dtu_consumption_percent"

# Storage usage
az sql db show --resource-group uris-ai-rg --server uris-ai-sql-server --name uris-ai-db --query maxSizeBytes
```

**Check Redis Health:**

```bash
# Status
az redis show --resource-group uris-ai-rg --name uris-ai-redis --query provisioningState

# Metrics
az monitor metrics list \
  --resource /subscriptions/{sub-id}/resourceGroups/uris-ai-rg/providers/Microsoft.Cache/Redis/uris-ai-redis \
  --metric "cacheHits,cacheMisses"
```

**Check Application Insights:**

```bash
# Recent exceptions
az monitor app-insights query \
  --app uris-ai-appinsights \
  --analytics-query "exceptions | where timestamp > ago(1h) | summarize count() by type"

# Request rate
az monitor app-insights query \
  --app uris-ai-appinsights \
  --analytics-query "requests | where timestamp > ago(1h) | summarize count() by bin(timestamp, 5m)"
```

---

## Maintenance Procedures

### Routine Maintenance

**Daily Tasks:**

- Review Application Insights dashboard
- Check for active alerts
- Review error logs for patterns
- Verify data freshness

**Weekly Tasks:**

- Review performance metrics
- Check database backup status
- Review security logs
- Update documentation if needed

**Monthly Tasks:**

- Review and optimize slow queries
- Clean up old logs and data
- Review and update alert thresholds
- Conduct disaster recovery drill

### Planned Maintenance

**Before Maintenance:**

1. Schedule maintenance window (off-peak hours)
2. Notify users via dashboard banner
3. Create backup of database
4. Document rollback plan

**During Maintenance:**

1. Enable maintenance mode (optional)
2. Perform maintenance tasks
3. Run smoke tests
4. Monitor for issues

**After Maintenance:**

1. Verify all services are healthy
2. Check Application Insights for errors
3. Notify users maintenance is complete
4. Document changes made

### Database Maintenance

**Backup Database:**

```bash
# Manual backup
az sql db export \
  --resource-group uris-ai-rg \
  --server uris-ai-sql-server \
  --name uris-ai-db \
  --admin-user sqladmin \
  --admin-password <password> \
  --storage-key <storage-key> \
  --storage-key-type StorageAccessKey \
  --storage-uri https://urisaistorage.blob.core.windows.net/backups/uris-ai-db-$(date +%Y%m%d).bacpac
```

**Restore Database:**

```bash
# Restore from backup
az sql db import \
  --resource-group uris-ai-rg \
  --server uris-ai-sql-server \
  --name uris-ai-db-restored \
  --admin-user sqladmin \
  --admin-password <password> \
  --storage-key <storage-key> \
  --storage-key-type StorageAccessKey \
  --storage-uri https://urisaistorage.blob.core.windows.net/backups/uris-ai-db-20240120.bacpac
```

**Optimize Database:**

```sql
-- Update statistics
EXEC sp_updatestats;

-- Rebuild indexes
ALTER INDEX ALL ON risk_scores REBUILD;
ALTER INDEX ALL ON recommendations REBUILD;

-- Check fragmentation
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    ips.index_id,
    ips.avg_fragmentation_in_percent
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
WHERE ips.avg_fragmentation_in_percent > 30;
```

### Scaling Procedures

**Scale Out (Add Instances):**

```bash
az appservice plan update \
  --resource-group uris-ai-rg \
  --name uris-ai-asp-production \
  --number-of-workers 5
```

**Scale Up (Larger Instance):**

```bash
az appservice plan update \
  --resource-group uris-ai-rg \
  --name uris-ai-asp-production \
  --sku P2V2
```

**Scale Database:**

```bash
az sql db update \
  --resource-group uris-ai-rg \
  --server uris-ai-sql-server \
  --name uris-ai-db \
  --service-objective S3
```

---

## Escalation Procedures

### Escalation Matrix

| Issue Type      | L1 (On-Call)          | L2 (DevOps Lead)   | L3 (Engineering Manager) |
| --------------- | --------------------- | ------------------ | ------------------------ |
| System Down     | Investigate & restart | Code/config issues | Architecture decisions   |
| Database Issues | Check connectivity    | Query optimization | Database architecture    |
| Security Breach | Block & document      | Forensic analysis  | Legal/compliance         |
| Performance     | Scale resources       | Code optimization  | Capacity planning        |

### Escalation Contacts

**L1 - On-Call Engineer:**

- **Primary:** on-call@uris-ai.go.id
- **Phone:** +62-XXX-XXXX-XXXX
- **Slack:** #uris-ai-oncall

**L2 - DevOps Lead:**

- **Name:** [DevOps Lead Name]
- **Email:** devops-lead@uris-ai.go.id
- **Phone:** +62-XXX-XXXX-XXXX
- **Slack:** @devops-lead

**L3 - Engineering Manager:**

- **Name:** [Engineering Manager Name]
- **Email:** eng-manager@uris-ai.go.id
- **Phone:** +62-XXX-XXXX-XXXX
- **Slack:** @eng-manager

**Security Team:**

- **Email:** security@uris-ai.go.id
- **Phone:** +62-XXX-XXXX-XXXX (24/7)
- **Slack:** #security-incidents

**Azure Support:**

- **Portal:** https://portal.azure.com → Support
- **Phone:** +62-XXX-XXXX-XXXX
- **Severity:** P1 (Critical), P2 (High), P3 (Medium)

### When to Escalate

**Escalate to L2 if:**

- Issue not resolved within 30 minutes
- Root cause requires code changes
- Database performance issues
- Complex configuration issues

**Escalate to L3 if:**

- Issue not resolved within 2 hours
- Architectural changes needed
- Multiple systems affected
- Business impact is severe

**Escalate to Security Team if:**

- Security breach suspected
- Unauthorized access detected
- Data leak suspected
- Compliance violation

---

## Contact Information

### Team Contacts

**Operations Team:**

- **Email:** ops@uris-ai.go.id
- **Slack:** #uris-ai-ops
- **On-Call:** on-call@uris-ai.go.id

**Development Team:**

- **Email:** dev@uris-ai.go.id
- **Slack:** #uris-ai-dev

**Security Team:**

- **Email:** security@uris-ai.go.id
- **Slack:** #security-incidents

**Management:**

- **Email:** management@uris-ai.go.id

### External Contacts

**Azure Support:**

- **Portal:** https://portal.azure.com
- **Phone:** +62-XXX-XXXX-XXXX

**Weather API Provider:**

- **Support:** support@weatherapi.com
- **Status:** https://status.weatherapi.com

### Documentation Links

- **Architecture:** [architecture.md](architecture.md)
- **API Documentation:** [api_documentation.md](api_documentation.md)
- **Developer Guide:** [developer_documentation.md](developer_documentation.md)
- **User Guide:** [user_guide.md](user_guide.md)
- **Deployment Guide:** [deployment.md](deployment.md)
- **Monitoring Guide:** [monitoring_logging.md](monitoring_logging.md)

### Useful Links

- **Azure Portal:** https://portal.azure.com
- **Application Insights:** https://portal.azure.com → uris-ai-appinsights
- **GitHub Repository:** https://github.com/your-org/uris-ai
- **CI/CD Pipeline:** https://github.com/your-org/uris-ai/actions
- **Status Page:** https://status.uris-ai.go.id

---

## Appendix

### Incident Report Template

```markdown
# Incident Report

**Incident ID:** INC-YYYYMMDD-XXX
**Date:** YYYY-MM-DD
**Severity:** P1/P2/P3
**Status:** Open/Resolved/Closed

## Summary

Brief description of the incident.

## Timeline

- HH:MM - Incident detected
- HH:MM - On-call acknowledged
- HH:MM - Root cause identified
- HH:MM - Fix implemented
- HH:MM - Incident resolved

## Impact

- Users affected: XXX
- Duration: XX minutes
- Services affected: API/Dashboard/Database

## Root Cause

Detailed explanation of what caused the incident.

## Resolution

Steps taken to resolve the incident.

## Action Items

- [ ] Action item 1
- [ ] Action item 2

## Lessons Learned

What we learned and how to prevent similar incidents.
```

### Runbook Change Log

| Date       | Version | Changes         | Author      |
| ---------- | ------- | --------------- | ----------- |
| 2024-01-20 | 1.0.0   | Initial version | DevOps Team |

---

**End of Operations Runbook**

For questions or updates to this runbook, contact: ops@uris-ai.go.id
