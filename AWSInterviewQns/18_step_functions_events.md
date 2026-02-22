# 18. Step Functions & Event-Driven Architecture — Senior

## Q1. (Beginner) What is Step Functions? What is a state machine?

**Answer:**  
**Step Functions** orchestrates **workflows** (state machines): a **state machine** is a graph of **states** (tasks, choice, wait, parallel, etc.) and transitions. Each execution has **input/output** and **history**; you pay per state transition. Use for **multi-step** workflows, **retries**, and **human approval**. **Standard** vs **Express** workflows: Standard has longer retention and exactly-once; Express is high-volume, short-duration, at-least-once.

---

## Q2. (Beginner) What is EventBridge? How does it differ from SNS?

**Answer:**  
**EventBridge** is a **event bus**: **sources** (AWS services, custom apps) publish **events** (JSON); **rules** match events and **target** (Lambda, SQS, SNS, etc.). **Filtering** by pattern (e.g. detail-type, source). **vs SNS**: SNS is **pub/sub** (topic → subscribers); EventBridge has **schema registry**, **filtering**, **archive/replay**, and many AWS sources. Use **EventBridge** for **event-driven** architecture and decoupling; use **SNS** for simple fan-out to subscribers.

---

## Q3. (Intermediate) When would you use Step Functions instead of a single Lambda that calls other services in sequence?

**Answer:**  
Use **Step Functions** when: (1) **Long duration** (> 15 min) or **wait** (e.g. human approval, callback). (2) **Visibility** — need **audit trail** and **retry** per step. (3) **Conditional** or **parallel** flow (branching, fan-out). (4) **Partial failure** — retry or compensate one step without rerunning all. **Single Lambda** is fine for short, linear flows (< 15 min) when you don’t need per-step visibility or long waits.

---

## Q4. (Intermediate) Production scenario: Order flow: validate payment → reserve inventory → ship. If inventory fails, refund payment. How do you model this with Step Functions?

**Answer:**  
**States**: (1) **ValidatePayment** (Lambda); on success → (2) **ReserveInventory** (Lambda); on success → (3) **Ship** (Lambda). **On ReserveInventory failure**: **Catch** → (4) **RefundPayment** (Lambda). Use **Catch** on ReserveInventory with **Next: RefundPayment**; RefundPayment receives error and order context. **Input**: pass orderId, amount through chain; RefundPayment uses them. **Alternative**: **Saga** — each step has a **compensating** step; use **Choice** or **Map** to run compensations in reverse order on failure.

---

## Q5. (Intermediate) What is the “storage-first” pattern with API Gateway and SQS? How do you implement it?

**Answer:**  
**Storage-first**: API Gateway **directly** invokes **SQS** (or DynamoDB) **without** Lambda — request body is sent as message or stored. **Implementation**: **REST API** with **AWS integration**; integration type = AWS; action = SQS SendMessage; map `application/json` body to MessageBody (VTL). **Benefit**: no Lambda cold start; lower cost; good for **ingest** (e.g. events, webhooks). **Limitation**: no custom validation or auth in the middle (use API Gateway request validator or authorizer).

---

## Q6. (Advanced) Production scenario: Payment succeeds but inventory reservation fails. You need to refund without double-refunding. Design a saga-style flow with Step Functions and idempotency.

**Answer:**  
(1) **States**: Payment (Lambda) → Inventory (Lambda); **Catch** on Inventory → **Refund** (Lambda). (2) **Idempotency**: **Refund** Lambda checks **DynamoDB** (e.g. key = orderId, attribute = refundStatus); if already “refunded”, return success; else call payment API refund, then set refunded. (3) **Step Functions** may **retry** Refund on timeout; idempotency ensures one refund. (4) **Payment service**: make **Refund** API idempotent (e.g. idempotency key = orderId). (5) **Compensation**: Refund is the compensation for Payment; no compensation for Inventory (it failed). **Result**: at-most-once refund, retry-safe.

---

## Q7. (Advanced) What is EventBridge schema registry and discovery? When would you use it?

**Answer:**  
**Schema registry**: store **schemas** (JSON Schema) for events; **discovery** generates code (types, SDK) from schemas for producers/consumers. **Use**: when **many** services produce/consume events and you want **consistent** event shape and **typed** code. **Optional** for small teams; **useful** for enterprise (governance, validation). EventBridge can **validate** incoming events against a schema if configured.

---

## Q8. (Advanced) How do you fan-out with EventBridge: one event triggers Lambda A, SQS queue B, and Step Functions C, but only when event.detail.type is "OrderCreated"?

**Answer:**  
**EventBridge rule**: (1) **Event pattern**: `{ "detail": { "type": ["OrderCreated"] } }`. (2) **Targets**: add three targets — **Lambda A**, **SQS queue B**, **Step Functions** (start execution) **C**. (3) Each target gets the **full event** (or optionally transformed). (4) **Permissions**: EventBridge needs permission to invoke Lambda, send to SQS, start execution. **Result**: only OrderCreated events trigger all three; other events are ignored by this rule.

---

## Q9. (Advanced) Compare event-driven design for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: SNS + SQS or EventBridge; one or two rules; Lambda consumers. **Medium**: **EventBridge** with **rules** and **filtering**; **Step Functions** for critical workflows; **DLQ** and retry. **Enterprise**: **Schema registry**; **cross-account** events; **archive/replay**; **Saga** and compensation; audit and compliance.

---

## Q10. (Advanced) Senior red flags to avoid with Step Functions / EventBridge

**Answer:**  
- **No error handling** (Catch) in Step Functions (failed step stops execution).  
- **No idempotency** in saga compensations (double refund, double release).  
- **Sensitive data** in event payload (encrypt or reference by ID).  
- **No DLQ** for EventBridge targets (failed invocations lost).  
- **Standard workflow** for high-volume, short workflows (use Express).  
- **Ignoring** event schema evolution (breaking consumers).  
- **No visibility** (Step Functions execution history, CloudWatch for EventBridge).

---

**Tradeoffs:** Startup: SNS/SQS or simple EventBridge. Medium: Step Functions for workflows, EventBridge for events. Enterprise: Saga, schema registry, cross-account.
