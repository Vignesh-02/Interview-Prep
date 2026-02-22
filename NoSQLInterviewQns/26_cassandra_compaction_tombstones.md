# 26. Cassandra Compaction, Tombstones & Tuning — Senior

## Q1. (Beginner) What is compaction in Cassandra? Why is it needed?

**Answer:**  
**Compaction** is the process of merging **SSTables** (immutable on-disk files) to reduce number of files, reclaim space from overwritten/deleted data, and improve read performance. Without compaction, reads would touch many SSTables and space would grow. Compaction strategies: SizeTieredCompactionStrategy (STCS), LeveledCompactionStrategy (LCS), TimeWindowCompactionStrategy (TWCS), etc.

---

## Q2. (Beginner) What is a tombstone? When is one created?

**Answer:**  
A **tombstone** is a marker that a cell or row was **deleted**. It’s created when you DELETE a row or column (or insert null for a nullable column in some cases). Tombstones are stored like regular writes so they propagate to replicas. They are removed only after **gc_grace_seconds** during compaction; until then they are needed for repair and consistency.

---

## Q3. (Intermediate) What is gc_grace_seconds? What happens if you drop it too low?

**Answer:**  
**gc_grace_seconds** is the time (default 10 days) before a tombstone can be removed during compaction. It must be longer than the repair window so that **repair** can propagate the delete to all replicas. If you set it too low and don’t run repair, a replica that missed the delete could **resurrect** the row (delete lost). Keep gc_grace_seconds at least as long as your repair interval.

---

## Q4. (Intermediate) What is the difference between STCS and LCS? When would you use TWCS?

**Answer:**  
**STCS** (SizeTieredCompactionStrategy): merges SSTables of similar size; good for write-heavy, can have many overlapping SSTables and slower reads. **LCS** (LeveledCompactionStrategy): leveled tiers; better read performance and more predictable space; higher write amplification. **TWCS** (TimeWindowCompactionStrategy): compact by time window; good for **time-series** (e.g. one window per day); old windows are compacted once and don’t get mixed with new data.

---

## Q5. (Intermediate) What is read repair and hinted handoff? How do they affect consistency?

**Answer:**  
**Read repair**: on a read, if replicas return different data, Cassandra coordinates a **repair** (update stale replica). Can be blocking (before response) or background. **Hinted handoff**: when a replica is down, the coordinator stores a **hint** and later replays it to the replica. Hints are temporary (e.g. 3 hours); they don’t replace **nodetool repair** for long outages. Both help eventual consistency; repair is required for strong guarantees.

---

## Q6. (Advanced) Production scenario: Your time-series table has a lot of deletes (e.g. TTL or explicit delete). Reads are slow and disk is growing. What could be wrong and how do you fix it?

**Answer:**  
**Likely**: **tombstone** accumulation — many deletes create tombstones; reads merge many SSTables and process tombstones; compaction may not keep up. **Fixes**: (1) **Reduce deletes**: use TTL instead of explicit DELETE where possible; batch deletes. (2) **Compaction**: use TWCS for time-series so compaction is efficient; run **nodetool compact** (with care). (3) **gc_grace_seconds**: don’t lower below repair interval. (4) **Limit per-partition deletes**: avoid deleting huge partitions row-by-row; drop partition or use buckets. (5) **Monitor**: tombstone count and read latency; add metrics.

---

## Q7. (Advanced) What is write path and read path in Cassandra? Why does compaction matter for reads?

**Answer:**  
**Write path**: write goes to **memtable**; when full, memtable is flushed to an **SSTable** (immutable). **Read path**: read checks **memtable** then **SSTables** (Bloom filter, then partition key index, then read row); results from multiple SSTables are merged. **Compaction** merges SSTables so fewer files are read and overwritten/deleted data is merged away; so compaction reduces read amplification and improves latency.

---

## Q8. (Advanced) How do you choose compaction strategy for: (1) time-series events, (2) user profile (read-heavy, few overwrites)?

**Answer:**  
(1) **Time-series**: **TWCS** — compact by time window (e.g. 1 day); recent data in one window, old data compacted once; good for append and TTL/delete by time. (2) **User profile** (read-heavy, few overwrites): **LCS** — predictable read latency and fewer SSTables per partition; higher write amplification is acceptable. Avoid STCS for read-heavy if you need stable read latency.

---

## Q9. (Advanced) What is incremental repair vs full repair? What is subrange repair?

**Answer:**  
**Full repair** (nodetool repair): compares and syncs all data for the node with its replicas (Merke tree). **Incremental repair**: only repair data that has changed since last repair (tracks merkle tree per range). **Subrange repair**: repair a subset of token ranges (e.g. one range at a time) to reduce load and time. Use incremental and subrange in production to avoid long repair windows and load spikes.

---

## Q10. (Advanced) How does the backend (or ops) run repair and compaction? What are best practices?

**Answer:**  
**Repair**: `nodetool repair` (full) or `nodetool repair -pr` (primary range only). Schedule **regular** repair (e.g. weekly) within **gc_grace_seconds**. Use **incremental** and **subrange** to spread load. **Compaction**: usually automatic; `nodetool compact` triggers compaction (can be heavy). **Best practices**: (1) Repair within gc_grace_seconds. (2) Don’t run full repair on all nodes at once; stagger. (3) Monitor repair duration and compaction backlog. (4) For time-series, use TWCS and avoid excessive deletes.
