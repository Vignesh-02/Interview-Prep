# 10. Redis Transactions, Lua & Pipelining

## Q1. (Beginner) What does MULTI/EXEC do in Redis? Is it like a database transaction?

**Answer:**  
**MULTI** starts a transaction; subsequent commands are **queued**; **EXEC** runs them **in sequence, atomically** (no other command runs in between). It does **not** provide rollback: if one command fails, the rest still run; there is no undo. So it’s “atomic batching,” not ACID transactions. Use for grouping commands so they run together without interleaving.

---

## Q2. (Beginner) What is Redis pipelining? Why use it?

**Answer:**  
**Pipelining**: send **multiple commands** to the server without waiting for each response; then read all replies. Reduces **round-trips** (latency). Use when you have many sequential commands (e.g. 100 GETs); throughput improves significantly. In Node with ioredis: `const pipeline = redis.pipeline(); pipeline.get('a'); pipeline.get('b'); await pipeline.exec();`

---

## Q3. (Intermediate) Write Node.js code that uses pipelining to get 10 keys in one round-trip and return an array of values.

**Answer:**
```javascript
async function getMany(redis, keys) {
  const pipeline = redis.pipeline();
  keys.forEach(k => pipeline.get(k));
  const results = await pipeline.exec();
  return results.map(([err, val]) => (err ? null : val));
}
// Usage: getMany(redis, ['user:1', 'user:2', ...])
```

---

## Q4. (Intermediate) What is WATCH? How do you use it for optimistic locking?

**Answer:**  
**WATCH key**: if the key is modified before EXEC, the transaction is **aborted** (EXEC returns nil). So: WATCH key, read value, MULTI, do conditional updates, EXEC; if another client changed the key, EXEC fails and you retry. This is **optimistic locking** — no explicit lock, but you detect conflict and retry.

---

## Q5. (Intermediate) When would you use a Lua script instead of MULTI/EXEC?

**Answer:**  
Use **Lua** when: (1) You need **logic** (conditionals, loops) that can’t be expressed as a fixed sequence of commands. (2) You need **atomic read-modify-write** that depends on the read (e.g. “increment only if &lt; 100”). (3) You want to reduce round-trips: one EVAL = one round-trip. MULTI/EXEC is for a fixed list of commands; Lua is for scriptable, atomic logic.

---

## Q6. (Advanced) Write a Lua script that increments a key only if its value is less than 10. Return the new value. How do you call it from Node.js?

**Answer:**  
**Lua:**
```lua
local current = redis.call('GET', KEYS[1])
if current == false then current = '0' end
current = tonumber(current)
if current < 10 then
  redis.call('INCR', KEYS[1])
  return current + 1
end
return current
```

**Node (ioredis):**
```javascript
const script = `
  local current = redis.call('GET', KEYS[1])
  if current == false then current = '0' end
  current = tonumber(current)
  if current < 10 then
    redis.call('INCR', KEYS[1])
    return current + 1
  end
  return current
`;
const result = await redis.eval(script, 1, 'mykey');
```

---

## Q7. (Advanced) Production scenario: Implement a distributed lock in Redis: acquire lock with a unique value and 30s TTL; release only if the value matches. Use Lua for release so it’s atomic.

**Answer:**  
**Acquire**: `SET lock:resource1 &lt;unique_value&gt; NX EX 30` — NX = only if not exists. **Release**: only DEL if value matches (avoid deleting another client’s lock). Do release in Lua:

**Lua (release):**
```lua
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
```

**Node:**
```javascript
const uuid = require('crypto').randomUUID();
async function acquireLock(redis, resource, ttl = 30) {
  const key = `lock:${resource}`;
  const ok = await redis.set(key, uuid, 'NX', 'EX', ttl);
  return ok ? uuid : null;
}
async function releaseLock(redis, resource, token) {
  const script = `if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) end; return 0`;
  await redis.eval(script, 1, `lock:${resource}`, token);
}
```

---

## Q8. (Advanced) What are the limitations of Redis “transactions” (MULTI/EXEC) compared to an RDBMS?

**Answer:**  
No **rollback** on failure; no **isolation** (other clients can read uncommitted state between commands); no **durability** guarantee within the transaction (depends on AOF/RDB); commands are only queued and executed in order. For true atomic conditional logic and rollback semantics, use Lua or design idempotent operations and retries.

---

## Q9. (Advanced) How does Redis run Lua scripts? What about replication and consistency?

**Answer:**  
Lua is executed **atomically** — no other command runs during the script. Redis replicates the script (or its SHA) to replicas; on replica it runs the same script. Scripts should be **deterministic** (no random, no time-dependent behavior that differs across nodes) so replication is consistent. Scripts can be long-running; Redis blocks during execution, so keep scripts short.

---

## Q10. (Advanced) When would pipelining be insufficient and you’d prefer a Lua script or MULTI/EXEC?

**Answer:**  
**Pipelining** only batches round-trips; each command is still independent. Use **MULTI/EXEC** when you need a batch of commands to run **atomically** (no other commands in between). Use **Lua** when the next command **depends on the result** of a previous one (e.g. “if GET &lt; 10 then INCR”) and must be atomic. Pipelining doesn’t provide atomicity; MULTI/EXEC and Lua do for their scope.
