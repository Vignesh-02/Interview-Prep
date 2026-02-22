# 28. Saga Pattern & Distributed Transactions — Senior

## Q1. (Beginner) What is a distributed transaction? Why can’t you always use a single database transaction?

**Answer:**  
**Distributed transaction**: multiple **operations** across **multiple services** (or DBs) that should **succeed or fail** together. **Single DB transaction** (ACID) works only when all data is in **one** database. When you have **multiple services** (e.g. Payment, Inventory, Shipping), each has its own DB; there is **no** single 2PC (two-phase commit) across them in practice. So you use **saga** or **eventual consistency** with **compensation**.

---

## Q2. (Beginner) What is the Saga pattern? What is a compensating transaction?

**Answer:**  
**Saga**: a **sequence** of **local** transactions (one per service); if **one fails**, run **compensating** transactions (undo) in **reverse** order. **Compensating transaction**: the “undo” (e.g. refund after payment, release inventory after reserve). **Result**: **eventual consistency**; no single atomic commit. **Choreography** (events) or **orchestration** (central coordinator) can implement saga.

---

## Q3. (Intermediate) You have Order, Payment, and Inventory services. Payment succeeds but Inventory fails. How do you handle rollback without a shared database?

**Answer:**  
**Saga**: (1) **Order** created. (2) **Payment** charged. (3) **Inventory** reserve — **fails**. (4) **Compensate**: **refund** (Payment); optionally **cancel** order (Order). **Implementation**: **Orchestrator** (e.g. **Step Functions**) calls Payment → then Inventory; on **Inventory failure**, call **Refund** step (Payment API); then mark order failed. **Idempotency**: Refund must be **idempotent** (e.g. by orderId) so retries don’t double-refund.

---

## Q4. (Intermediate) What is Step Functions good for in a saga? What is the difference between Standard and Express workflows for this?

**Answer:**  
**Step Functions**: **orchestration** — define steps (Lambda, API calls); **Catch** for failure and **compensation** branch; **state** and **history** for audit. **Standard**: **exactly-once** execution; **long** retention; good for **saga** (order, payment, inventory). **Express**: **high volume**, **short** duration; **at-least-once**; less retention. **Use Standard** for saga (need reliability and audit); use **Express** for high-throughput, short workflows without saga.

---

## Q5. (Intermediate) Production scenario: Implement “place order” saga: reserve inventory → charge payment → create shipment. If any step fails, run compensations in reverse order. Use Step Functions. Outline the state machine.

**Answer:**  
**States**: (1) **ReserveInventory** (Lambda); **Catch** → **ReleaseInventory** (compensate) → **FailOrder**. (2) **ChargePayment** (Lambda); **Catch** → **RefundPayment** → **ReleaseInventory** → **FailOrder**. (3) **CreateShipment** (Lambda); **Catch** → **CancelShipment** (if supported) → **RefundPayment** → **ReleaseInventory** → **FailOrder**. (4) **Success**. **Flow**: ReserveInventory → ChargePayment → CreateShipment → Success. Each **Catch** runs its **compensation chain** then FailOrder. **Idempotency**: every step and compensation is idempotent (keyed by orderId).

---

## Q6. (Advanced) How do you ensure exactly-once or at-most-once semantics for a saga step (e.g. “charge payment”) when Step Functions may retry?

**Answer:**  
**Idempotency**: (1) **Client token** (e.g. orderId) passed to **ChargePayment** Lambda. (2) **Lambda** checks **DynamoDB** (e.g. Payments table): if orderId already has “charged”, return **success** (no double charge). (3) Else call payment provider; on success write “charged” with orderId. (4) **Retry** from Step Functions hits same Lambda with same orderId → Lambda returns success from DB. **Result**: **at-most-once** charge (or exactly-once from business view). **Payment provider**: use idempotency key if supported.

---

## Q7. (Advanced) What is event-driven saga (choreography) vs orchestration? When would you use each?

**Answer:**  
**Choreography**: each service **publishes events** (e.g. OrderCreated, PaymentCompleted); **consumers** react and publish next events; **compensation** via events (e.g. PaymentFailed → Inventory releases). **Orchestration**: **central** coordinator (e.g. Step Functions) **calls** each service and handles **compensation**. **Choreography**: **decoupled**, scales; **harder** to see full flow and to compensate (everyone must emit compensation events). **Orchestration**: **clear** flow and compensation; **coordinator** is single point. **Use orchestration** (Step Functions) when you want **explicit** saga and audit; use **choreography** when services are very independent and you accept eventual consistency.

---

## Q8. (Advanced) Production scenario: Payment service is external (third-party). It can timeout or succeed asynchronously (webhook). How do you design the saga so you don’t double-charge and you compensate correctly?

**Answer:**  
(1) **Step**: “ChargePayment” Lambda calls **third-party** with **idempotency key** (orderId); third-party returns **pending** or **success**. (2) **Wait**: use Step Functions **Wait** or **callback** (task token); Lambda returns task token to third-party; **webhook** (your API) receives result and **resumes** Step Functions with success/failure. (3) **Idempotency**: webhook checks orderId; if already processed, return 200 (no double apply). (4) **Compensation**: if webhook says **failed**, Step Functions runs **Refund** (call third-party refund API, idempotent by orderId). (5) **Timeout**: if no webhook in N minutes, **cancel** payment (or query status) and compensate. **Result**: async payment with correct success/failure and compensation.

---

## Q9. (Advanced) Compare saga implementation for startup vs enterprise. What does each typically need?

**Answer:**  
**Startup**: **orchestration** (Step Functions) with 2–3 steps; **manual** or simple compensation; idempotency in app. **Medium**: **Step Functions** with **Catch** and **compensation**; **DLQ** for failed steps; **alarms**. **Enterprise**: **saga** with **audit** (every step and compensation logged); **idempotency** and **idempotency store** (DynamoDB); **timeout** and **retry** policy; **runbooks** for stuck sagas.

---

## Q10. (Advanced) Senior red flags to avoid with saga

**Answer:**  
- **No compensation** (partial state when a step fails).  
- **Non-idempotent** steps or compensations (retries cause double charge or double release).  
- **Assuming** “success” from external API without **webhook** or **polling** (timeout vs success).  
- **No timeout** (saga stuck forever).  
- **No audit** (can’t trace which step failed and what was compensated).  
- **Order-dependent** compensation (always compensate in **reverse** order).  
- **Ignoring** DLQ and failed executions (monitor and replay or fix).

---

**Tradeoffs:** Startup: Step Functions, 2–3 steps, idempotency. Medium: full compensation, DLQ. Enterprise: audit, idempotency store, runbooks.
