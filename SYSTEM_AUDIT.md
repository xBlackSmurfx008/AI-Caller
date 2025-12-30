# AI Caller System Audit Report

**Run ID:** `46be3db8`
**Date:** 2025-12-29 08:23:19 UTC
**Duration:** 0.6s
**Environment:** test

## Final Status: ✅ GO

## Summary

| Metric | Count |
|--------|-------|
| Total Tests | 29 |
| ✅ Passed | 24 |
| ❌ Failed | 0 |
| ⚠️ Warnings | 0 |
| ⏭️ Skipped | 5 |

## Detailed Results

### Calendar Integration

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `calendar_connectivity` | ✅ PASS | 0.21s | Test completed successfully |
| `calendar_create_event` | ⏭️ SKIP | 0.00s | Skipping in quick mode (requires API) |
| `calendar_update_event` | ⏭️ SKIP | 0.00s | Skipping in quick mode (requires API) |
| `calendar_delete_event` | ⏭️ SKIP | 0.00s | Skipping in quick mode (requires API) |

### Twilio Messaging

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `twilio_client_init` | ✅ PASS | 0.00s | Test completed successfully |
| `twilio_message_normalization` | ✅ PASS | 0.19s | Test completed successfully |
| `twilio_store_inbound` | ✅ PASS | 0.02s | Test completed successfully |
| `twilio_create_draft` | ✅ PASS | 0.01s | Test completed successfully |

### Memory Pipeline

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `memory_store_interaction` | ✅ PASS | 0.01s | Test completed successfully |
| `memory_generate_summary` | ⏭️ SKIP | 0.00s | OpenAI API key not configured |
| `memory_get_context` | ✅ PASS | 0.01s | Test completed successfully |

### Preferences Resolver

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `preferences_create_entries` | ✅ PASS | 0.01s | Test completed successfully |
| `preferences_resolve` | ⏭️ SKIP | 0.01s | OpenAI API key not configured |
| `preferences_ranking` | ✅ PASS | 0.00s | Test completed successfully |

### Scheduler Engine

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `scheduler_create_tasks` | ✅ PASS | 0.00s | Test completed successfully |
| `scheduler_priority_sort` | ✅ PASS | 0.00s | Test completed successfully |
| `scheduler_dependency_check` | ✅ PASS | 0.00s | Test completed successfully |

### Cost Monitoring

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `cost_create_pricing_rules` | ✅ PASS | 0.00s | Test completed successfully |
| `cost_log_events` | ✅ PASS | 0.00s | Test completed successfully |
| `cost_aggregation` | ✅ PASS | 0.00s | Test completed successfully |
| `cost_budget_check` | ✅ PASS | 0.00s | Test completed successfully |

### Guardrails

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `guardrails_risk_classification` | ✅ PASS | 0.00s | Test completed successfully |
| `guardrails_confirmation_decision` | ✅ PASS | 0.00s | Test completed successfully |
| `guardrails_godfather_check` | ✅ PASS | 0.00s | Test completed successfully |
| `guardrails_outbound_approval` | ✅ PASS | 0.00s | Test completed successfully |

### PEC Gating

| Test | Status | Duration | Message |
|------|--------|----------|---------|
| `pec_create_project` | ✅ PASS | 0.00s | Test completed successfully |
| `pec_generate` | ✅ PASS | 0.00s | Test completed successfully |
| `pec_execution_gate` | ✅ PASS | 0.00s | Test completed successfully |
| `pec_approval` | ✅ PASS | 0.00s | Test completed successfully |

## Evidence

### Created Record IDs

```
contact:1f89add4-8699-4950-b34c-18698a9aeb03
message:80ffcb86-e4b4-4520-8a9d-bb2d40ba4c99
conversation:1f89add4-8699-4950-b34c-18698a9aeb03:sms
draft_message:8a057482-bb41-4132-b56d-b967be682c5b
approval:c02b30b4-248d-40f8-8ac4-1e20c357994b
contact:84bb048b-8d78-48b7-a763-5ca94713fb32
interaction:0263469a-b62a-4369-81e4-19908a199718
category:9262b947-db04-4997-9b46-13991c87d058
primary_pref:146d8164-28e3-40cf-ac05-9472798a6c68
secondary_pref:e5c9f091-cae5-4ecb-bf9e-1f16ea1f8716
avoid_pref:cd17aacf-5b76-4880-835a-d948a24ea997
healthcare_pref:1d379952-96f5-428d-9538-7defd5d9f794
project:dc5e4531-6a81-45c0-8d50-fd3b40760f7b
task_hard:59da3233-262b-4a0d-82a9-36f2b95b5962
task_flex:e102a9ed-b5c8-4fa1-8373-49a80ceb9477
task_dep:5c0a40b3-1b5e-49d4-84dd-6097d199ba4b
pricing_rule:82308116-a58d-44a9-a9ec-4fe653ba1843
pricing_rule:3a1524a7-0d36-43e5-8d8a-d152a1ac331e
cost_event:fedf8a75-234c-4e82-a730-6dab900cbaae
cost_event:d9afc787-b5ab-4e17-8721-fbc16f4e7038
budget:9fd81e12-f890-45a4-b4cb-5f9604b5683c
message:0b7c0572-a6ce-4e4a-9729-bd66993b00b1
approval:3f2d3563-4876-4a80-a324-0eddd54bc845
project:7a68f0c0-367a-431c-b83a-b6b82ab3f0f2
task:d9859c68-9445-4332-819e-e95b3e060c45
task:b38bf146-3546-47a4-b1e1-98322f9bbe5d
pec:9a21fe1a-8fc2-44d4-bf81-9a2f0aa0b646
pec:52b060d4-ce32-4956-bc47-5ac87c9ba258
```

### Cost Events Summary

- OpenAI cost: $0.0450
- Twilio cost: $0.0075
- Total audit costs: $0.0525
- Current spend: $0.0525

## Acceptance Criteria Status

- ✅ All major subsystems pass core tests
- ✅ At least one full E2E scenario completes
- ✅ Failures produce actionable errors
- ✅ Cost tracking matches aggregation
- ✅ No outbound message sent without approval

---
*Generated by audit.py on 2025-12-29T08:23:20.419353+00:00*