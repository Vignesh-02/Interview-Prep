# 2. Streams & Backpressure

## Topic Introduction

Streams are Node.js's answer to processing data **piece by piece** instead of loading everything into memory. A 10GB file? Stream it. A million database rows? Stream them. HTTP request/response bodies? Already streams.

```
Producer (Readable)  ──pipe──►  Consumer (Writable)
                                   │
                    ◄──backpressure─┘  (slow down if I can't keep up)
```

There are four stream types: **Readable**, **Writable**, **Duplex** (both), and **Transform** (modify data flowing through). Backpressure is the mechanism that **slows the producer** when the consumer can't keep up, preventing memory explosion.

**Why this matters for senior engineers**: Without streams, a single 1GB upload can consume 1GB of RAM. With 100 concurrent uploads, that's 100GB. Streams keep memory constant regardless of data size.

**Go/Java tradeoff**: Go uses `io.Reader`/`io.Writer` interfaces with explicit buffering. Java uses `InputStream`/`OutputStream` (blocking) or reactive streams (Project Reactor, RxJava). Node streams are event-driven and non-blocking by default, but the backpressure API is more complex.

---

Piping a Stream
"Piping" means connecting a readable stream directly to a writable stream, so data flows chunk-by-chunk without ever holding the full thing in memory.


[Readable Source] ──pipe──> [Writable Destination]
Example: File upload saved to disk
Without pipe (buffering — bad for large files):


app.post('/upload', (req, res) => {
  const chunks = []
  req.on('data', chunk => chunks.push(chunk))  // collecting ALL chunks in memory
  req.on('end', () => {
    const fullFile = Buffer.concat(chunks)       // entire file now in RAM
    fs.writeFileSync('output.txt', fullFile)     // then write to disk
    res.send('done')
  })
})
If someone uploads a 2GB file, you hold 2GB in RAM.

With pipe (streaming — memory efficient):


const fs = require('fs')

app.post('/upload', (req, res) => {
  const writeStream = fs.createWriteStream('output.txt')
  req.pipe(writeStream)                          // chunk comes in → immediately written to disk
  writeStream.on('finish', () => res.send('done'))
})
Memory usage stays tiny — each chunk is written to disk as it arrives, then discarded.

What .pipe() does internally

req  ──[chunk 1]──>  writeStream
     ──[chunk 2]──>  writeStream
     ──[chunk 3]──>  writeStream
         ...
Reads a chunk from the source (req)
Writes it to the destination (file, another response, S3, etc.)
Handles backpressure automatically — if the destination is slow, it pauses reading from the source
That last point is why .pipe() is preferred over manually wiring data events — it manages the flow rate for you.

Common pipe destinations

Use case	Destination
Save upload to disk	    fs.createWriteStream()
Forward to another server	    another http.request()
Compress on the fly	z           lib.createGzip()
Upload to S3	                AWS SDK stream upload

The key mental model: data flows through your Node process like water through a pipe — it doesn't pool up.

## Q1. (Beginner) What are the four types of Node.js streams? Give a real-world example of each.

**Answer**:

| Type | Purpose | Example |
|------|---------|---------|
| **Readable** | Data source | `fs.createReadStream()`, `http.IncomingMessage` (request body) |
| **Writable** | Data destination | `fs.createWriteStream()`, `http.ServerResponse` |
| **Duplex** | Both read and write | TCP socket (`net.Socket`), WebSocket |
| **Transform** | Modify data passing through | `zlib.createGzip()`, `crypto.createCipher()` |

```js
const fs = require('fs');

// Readable → Transform (gzip) → Writable
fs.createReadStream('input.txt')
  .pipe(require('zlib').createGzip())
  .pipe(fs.createWriteStream('input.txt.gz'));
```

---

## Q2. (Beginner) How do you read a file using streams vs loading it all into memory? Show both.

**Scenario**: Process a 5GB log file. Your server has 512MB RAM.

```js
// BAD — loads entire file into memory (OOM crash with 5GB file)
const data = fs.readFileSync('huge.log', 'utf8');
const lines = data.split('\n').filter(line => line.includes('ERROR'));

// GOOD — streams, constant memory usage (~64KB buffer)
const readline = require('readline');
const rl = readline.createInterface({
  input: fs.createReadStream('huge.log'),
});
const errors = [];
rl.on('line', (line) => {
  if (line.includes('ERROR')) errors.push(line);
});
rl.on('close', () => console.log(`Found ${errors.length} errors`));
```

**Answer**: Streaming uses a fixed-size buffer (`highWaterMark`, default 64KB for fs). Memory stays constant regardless of file size. `readFileSync` loads the entire file — impossible for files larger than available RAM.

---


The BAD version

const data = fs.readFileSync('huge.log', 'utf8');
const lines = data.split('\n').filter(line => line.includes('ERROR'));
Step by step:

fs.readFileSync — reads the entire file synchronously, blocking the event loop until done
The whole file is loaded into data as a single string in RAM
.split('\n') — creates an array of every line (another copy in memory)
.filter(...) — iterates over that array
For a 5GB file:

data = 5GB string in RAM
lines array = potentially another few GB
Node.js crashes with OOM (Out of Memory) because V8's heap limit is typically ~1.5GB by default
Also — readFileSync blocks the entire Node process while reading. No other requests can be handled during that time.

The GOOD version — broken down piece by piece

const readline = require('readline');
readline is a built-in Node.js module that knows how to read a stream line by line. It handles the complexity of chunks not aligning with line boundaries for you.


const rl = readline.createInterface({
  input: fs.createReadStream('huge.log'),
});
fs.createReadStream('huge.log') — opens the file and reads it in small chunks (default ~64KB at a time), not all at once
readline.createInterface({ input: ... }) — wraps that stream and emits a 'line' event each time it sees a \n
So the flow looks like:


File on disk
  → [64KB chunk] → readline buffers it, finds newlines
  → emits 'line' event for each complete line
  → [next 64KB chunk] → same thing
  → ...

const errors = [];
rl.on('line', (line) => {
  if (line.includes('ERROR')) errors.push(line);
});
rl.on('line', callback) — your callback fires once per line, not once per chunk
At any moment, only ~64KB of the file is in memory (the current chunk)
Lines that don't match ERROR are never stored — they're just garbage collected immediately

rl.on('close', () => console.log(`Found ${errors.length} errors`));
'close' fires when the entire file has been read and processed
Only now do you have the final result
The key insight: chunk boundary problem
Why do you need readline at all? Why not just listen to data events on the stream directly?

Because chunks don't respect line boundaries:


Chunk 1: "first line\nsecond li"
Chunk 2: "ne\nthird line\n"
readline buffers incomplete lines across chunks so you always get clean, complete lines in your 'line' handler.

Memory comparison
BAD	GOOD
Peak RAM	~5GB+	~64KB
Blocks event loop	Yes	No
Crashes on large files	Yes	No
Speed	Slower (all I/O then process)	Faster (I/O + processing overlap)
One caveat in the GOOD version

const errors = [];
// pushing matching lines here
If there are millions of ERROR lines, errors itself can grow large. For truly memory-safe processing you'd either stream the output too (write matches directly to a file as you find them) or count instead of collecting:


let count = 0;
rl.on('line', (line) => {
  if (line.includes('ERROR')) count++;  // no array growth
});

## Q3. (Beginner) What is `.pipe()` and why is it important?

**Scenario**: Serve a large file over HTTP.

```js
const http = require('http');
const fs = require('fs');

http.createServer((req, res) => {
  // Streams the file — never loads it all into memory
  fs.createReadStream('./video.mp4').pipe(res);
}).listen(3000);
```

Readable vs Writable
Think of them as roles:

Type	What it does	Examples
Readable	Produces data (you read FROM it)	fs.createReadStream(), req (incoming request), process.stdin
Writable	Consumes data (you write TO it)	fs.createWriteStream(), res (outgoing response), process.stdout
.pipe() connects them so data flows from the Readable into the Writable automatically.

Concrete example: copy a file

const fs = require('fs')

const readable = fs.createReadStream('input.txt')   // SOURCE — produces chunks
const writable = fs.createWriteStream('output.txt') // DESTINATION — consumes chunks

readable.pipe(writable)  // connect them
Without pipe, you'd have to do this manually:


// What .pipe() does under the hood (simplified)
readable.on('data', (chunk) => {
  const canContinue = writable.write(chunk)  // write chunk to destination
  
  if (!canContinue) {           // destination buffer is full (backpressure!)
    readable.pause()            // stop reading
    writable.once('drain', () => {
      readable.resume()         // destination caught up, start reading again
    })
  }
})

readable.on('end', () => {
  writable.end()  // signal no more data coming
})
.pipe() handles all of that for you in one line.

Another example: HTTP request → file

const http = require('http')
const fs = require('fs')

http.createServer((req, res) => {
  // req  = Readable (incoming upload)
  // file = Writable (disk)
  
  const file = fs.createWriteStream('uploaded.txt')
  req.pipe(file)              // connect: upload flows into disk

  file.on('finish', () => res.end('saved!'))
})
Visual mental model

Readable                    Writable
─────────                   ────────
[input.txt]  ──.pipe()──>  [output.txt]
[req body]   ──.pipe()──>  [disk file]
[req body]   ──.pipe()──>  [res]        ← proxy: forward request to response
The last one is interesting — you can even pipe a readable HTTP request directly to a writable HTTP response (a basic proxy):


req.pipe(res)  // whatever the client sends, immediately echo it back
In short: "connecting" just means — every chunk that comes out of the Readable automatically gets pushed into the Writable, without you writing any loop or event handler manually.


**Answer**: `.pipe(destination)` connects a Readable to a Writable and **automatically handles backpressure**. When the destination (e.g., a slow network connection) can't keep up, `.pipe()` pauses the source. When the destination drains, `.pipe()` resumes reading.

Without `.pipe()`, you'd need to manually listen for `data`, `drain`, and `end` events and handle pausing/resuming yourself.

---

## Q4. (Beginner) What is `highWaterMark`? What happens if you set it too high or too low?

**Answer**: `highWaterMark` is the **buffer size threshold** (in bytes) that controls when backpressure kicks in.

```js
// Default: 16KB for object mode, 16384 bytes (16KB) for normal streams
const stream = fs.createReadStream('file.txt', { highWaterMark: 64 * 1024 }); // 64KB
```

| Setting | Effect |
|---------|--------|
| **Too high** (e.g., 100MB) | More memory used per stream; less backpressure signaling |
| **Too low** (e.g., 16 bytes) | More frequent reads; higher overhead; lower throughput |
| **Sweet spot** | Depends on workload; 64KB–1MB typical for file I/O |

When the internal buffer reaches `highWaterMark`, the readable stream stops pushing data until the consumer drains.

---

## Q5. (Beginner) What is the difference between "flowing" and "paused" mode in readable streams?

**Answer**:

| Mode | How data is consumed | Triggered by |
|------|---------------------|-------------|
| **Flowing** | Data emitted automatically via `'data'` events | `.pipe()`, `.on('data')`, `.resume()` |
| **Paused** | Data must be explicitly pulled with `.read()` | Default mode; `.pause()` switches back |

```js
const readable = fs.createReadStream('file.txt');

// Paused mode — explicit pull
readable.on('readable', () => {
  let chunk;
  while ((chunk = readable.read()) !== null) {
    process.stdout.write(chunk);
  }
});

// Flowing mode — automatic push
readable.on('data', (chunk) => {
  process.stdout.write(chunk);
});
```

**Senior tip**: `.pipe()` handles mode switching automatically. Prefer `stream.pipeline()` over manual mode management.

---

## Q6. (Intermediate) What is backpressure? Show what happens without it.

**Scenario**: A fast producer (reading from SSD) and a slow consumer (writing to a remote API over a 1Mbps link).

```js
// WITHOUT backpressure — memory grows unbounded
const readable = fs.createReadStream('10gb-file.bin');
readable.on('data', (chunk) => {
  slowRemoteApi.send(chunk); // doesn't wait for completion
  // chunks pile up in memory → OOM
});

// WITH backpressure (using pipe)
const { pipeline } = require('stream');
pipeline(
  fs.createReadStream('10gb-file.bin'),
  slowRemoteApi.createWriteStream(),
  (err) => { if (err) console.error('Pipeline failed:', err); }
);
```

**Answer**: Backpressure is the mechanism where the **consumer signals the producer to slow down**. When `writable.write(chunk)` returns `false`, the buffer is full. The producer should stop pushing until the `'drain'` event fires.

`.pipe()` and `pipeline()` handle this automatically. Manual handling:
```js
readable.on('data', (chunk) => {
  const canContinue = writable.write(chunk);
  if (!canContinue) {
    readable.pause();
    writable.once('drain', () => readable.resume());
  }
});
```

---

## Q7. (Intermediate) Why should you use `stream.pipeline()` instead of `.pipe()`?

**Scenario**: Your file processing pipeline silently drops errors.

```js
// BAD — errors from middle streams are NOT propagated
source.pipe(transform).pipe(destination);
// If transform throws, destination never closes, and source may leak

// GOOD — pipeline handles error propagation and cleanup
const { pipeline } = require('stream');
pipeline(source, transform, destination, (err) => {
  if (err) console.error('Pipeline failed:', err);
  else console.log('Pipeline succeeded');
});

// Or with async/await (Node 15+)
const { pipeline } = require('stream/promises');
await pipeline(source, transform, destination);
```

**Answer**: `pipeline()` advantages over `.pipe()`:
1. **Error propagation**: If any stream errors, all streams are destroyed and the callback/promise is called
2. **Cleanup**: All streams are properly closed on error (no leaked file descriptors)
3. **AbortController support**: Can cancel mid-stream
4. **Promise API**: Works with async/await

---

## Q8. (Intermediate) Write a Transform stream that converts CSV lines to JSON objects.

**Scenario**: Process a 50GB CSV file and output JSON lines.

```js
const { Transform } = require('stream');

class CsvToJson extends Transform {
  constructor(options) {
    super({ ...options, objectMode: true });
    this.headers = null;
  }

  _transform(chunk, encoding, callback) {
    const line = chunk.toString().trim();
    if (!this.headers) {
      this.headers = line.split(',');
      callback();
      return;
    }
    const values = line.split(',');
    const obj = {};
    this.headers.forEach((h, i) => { obj[h] = values[i]; });
    callback(null, JSON.stringify(obj) + '\n');
  }
}

// Usage
const readline = require('readline');
const { pipeline } = require('stream');
const rl = readline.createInterface({ input: fs.createReadStream('data.csv') });
// Each line from readline → CsvToJson → output file
```

**Answer**: Transform streams let you **modify data in flight** with constant memory. The `_transform` method receives chunks, processes them, and pushes results via `callback(null, data)` or `this.push(data)`.

**Tradeoff with Go**: Go would use `bufio.Scanner` + `encoding/csv` — explicit, but no built-in backpressure. You'd manage buffering manually or use channels.

---

## Q9. (Intermediate) How do you handle file uploads without loading them into memory?

**Scenario**: Your API accepts file uploads up to 5GB. Server has 1GB RAM.

```js
const Busboy = require('busboy');
const { pipeline } = require('stream/promises');

app.post('/upload', async (req, res) => {
  const bb = Busboy({ headers: req.headers, limits: { fileSize: 5 * 1024 ** 3 } });

  bb.on('file', async (name, file, info) => {
    // Stream directly to S3 — never touch disk or memory
    const upload = new S3Upload({ Bucket: 'uploads', Key: info.filename, Body: file });
    await upload.done();
  });

  bb.on('finish', () => res.json({ status: 'uploaded' }));
  bb.on('error', (err) => res.status(500).json({ error: err.message }));

  req.pipe(bb);
});
```

**Answer**: The HTTP request body (`req`) IS a readable stream. Pipe it through a multipart parser (Busboy) which emits file streams. Pipe those directly to storage (S3, disk) — the file never fully loads into memory.

**Key**: Never use `req.on('data')` to accumulate buffers for file uploads. Always stream.

---

## Q10. (Intermediate) What is object mode in streams? When would you use it?

**Answer**: By default, streams handle `Buffer` or `string` chunks. **Object mode** lets you stream JavaScript objects.

```js
const { Transform } = require('stream');

const userTransform = new Transform({
  objectMode: true,
  transform(user, encoding, callback) {
    // user is a JS object, not a Buffer
    callback(null, { ...user, processedAt: Date.now() });
  }
});
```

**Use cases**: Database cursor → transform → output. Each "chunk" is a row object.

```js
// Stream from database cursor (e.g., PostgreSQL)
const cursor = db.query(new Cursor('SELECT * FROM users'));
const readable = new Readable({
  objectMode: true,
  async read(size) {
    const rows = await cursor.read(size);
    rows.forEach(row => this.push(row));
    if (rows.length === 0) this.push(null); // end
  }
});
```

**Note**: In object mode, `highWaterMark` counts **objects** (default 16), not bytes.

---

## Q11. (Intermediate) How do you proxy an HTTP response (e.g., from a microservice) using streams?

**Scenario**: Your BFF proxies requests to an internal API. Large responses (10MB JSON) must not buffer in memory.

```js
const http = require('http');
const { pipeline } = require('stream/promises');

app.get('/api/data', async (req, res) => {
  const proxyReq = http.request('http://internal-api:3001/data', async (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    await pipeline(proxyRes, res);
  });
  proxyReq.on('error', (err) => res.status(502).json({ error: 'Upstream failed' }));
  proxyReq.end();
});
```

**Answer**: `proxyRes` (the upstream response) is a Readable stream. `res` (the client response) is a Writable stream. `pipeline()` connects them with backpressure and error handling. Memory stays constant even for multi-GB responses.

---

## Q12. (Intermediate) How do you limit the rate of a readable stream (throttle)?

**Scenario**: You're reading from a fast database cursor but need to limit writes to an external API to 100 records/sec.

```js
const { Transform } = require('stream');

class Throttle extends Transform {
  constructor(recordsPerSecond) {
    super({ objectMode: true });
    this.interval = 1000 / recordsPerSecond;
    this.lastSend = 0;
  }

  _transform(chunk, encoding, callback) {
    const now = Date.now();
    const wait = Math.max(0, this.interval - (now - this.lastSend));
    setTimeout(() => {
      this.lastSend = Date.now();
      callback(null, chunk);
    }, wait);
  }
}

// Usage
pipeline(dbCursor, new Throttle(100), apiWriter, (err) => { /* ... */ });
```

**Answer**: Wrap a Transform stream that delays `callback()` by the required interval. Backpressure naturally propagates — the readable slows because the transform isn't calling `callback` immediately.

---

## Q13. (Advanced) Production scenario: Your Node.js service processes a 50GB CSV nightly import. Memory keeps growing until OOM. Debug and fix.

**Answer**:

**Root cause checklist**:
1. **Accumulating results in memory**: `results.push(row)` for every row → OOM
2. **Unhandled backpressure**: Not checking `writable.write()` return value
3. **String concatenation**: Building a giant output string
4. **Leaked event listeners**: Each row adds a listener that's never removed

**Fix**: Stream end-to-end with constant memory:
```js
const { pipeline } = require('stream/promises');
const { createReadStream, createWriteStream } = require('fs');
const { Transform } = require('stream');
const csv = require('csv-parse');

const transform = new Transform({
  objectMode: true,
  transform(record, enc, cb) {
    // Process one record at a time — no accumulation
    const result = processRecord(record);
    cb(null, JSON.stringify(result) + '\n');
  }
});

await pipeline(
  createReadStream('import.csv'),
  csv.parse({ columns: true }),
  transform,
  createWriteStream('output.jsonl')
);
// Peak memory: ~tens of MB regardless of file size
```

**Monitoring**: Track `process.memoryUsage().heapUsed` during import. Should stay flat.

---

## Q14. (Advanced) How do you stream JSON responses for large datasets from an API endpoint?

**Scenario**: `GET /export/users` returns 10M rows. JSON.stringify on the array takes 30s and 8GB RAM.

```js
// BAD — loads all users into memory
app.get('/export/users', async (req, res) => {
  const users = await db.query('SELECT * FROM users'); // 10M rows in memory
  res.json(users); // JSON.stringify another 8GB
});

// GOOD — stream JSON array
app.get('/export/users', async (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.write('[');

  const cursor = db.query(new Cursor('SELECT * FROM users'));
  let first = true;

  while (true) {
    const rows = await cursor.read(1000); // batch of 1000
    if (rows.length === 0) break;

    for (const row of rows) {
      if (!first) res.write(',');
      first = false;

      // Check backpressure
      const ok = res.write(JSON.stringify(row));
      if (!ok) await new Promise(resolve => res.once('drain', resolve));
    }
  }

  res.end(']');
  cursor.close();
});
```

**Answer**: Stream the JSON array manually — write `[`, then each object with commas, then `]`. Check `res.write()` return value for backpressure. Memory stays constant.

**Tradeoff with Go**: Go's `json.NewEncoder(w).Encode()` writes directly to the response writer. No built-in backpressure on HTTP writes — Go's goroutine blocks until the write completes (simpler model but wastes a goroutine if the client is slow).

---

## Q15. (Advanced) How do you implement a streaming ETL pipeline with error handling, retries, and metrics?

**Scenario**: Read from Kafka → transform → write to PostgreSQL. 100k messages/sec. Some messages will fail validation.

```js
const { pipeline } = require('stream/promises');
const { Transform, Writable } = require('stream');

const transformer = new Transform({
  objectMode: true,
  transform(message, enc, cb) {
    try {
      const parsed = JSON.parse(message.value);
      const validated = schema.parse(parsed); // Zod validation
      metrics.increment('transform.success');
      cb(null, validated);
    } catch (err) {
      metrics.increment('transform.error');
      // Send to dead-letter, don't crash the pipeline
      deadLetterQueue.add({ message, error: err.message });
      cb(); // skip this message (no output)
    }
  }
});

const dbWriter = new Writable({
  objectMode: true,
  highWaterMark: 500, // batch 500 objects
  async write(record, enc, cb) {
    try {
      await db.query('INSERT INTO events ...', [record.id, record.data]);
      metrics.increment('db.write.success');
      cb();
    } catch (err) {
      metrics.increment('db.write.error');
      cb(err); // pipeline will handle
    }
  }
});

await pipeline(kafkaConsumerStream, transformer, dbWriter);
```

**Answer**: Production stream pipelines need: (1) **Error isolation** — bad messages go to DLQ, don't crash pipeline, (2) **Metrics** — count success/failure/throughput, (3) **Backpressure** — `highWaterMark` on writer controls batch size, (4) **Graceful shutdown** — handle SIGTERM by draining.

---

## Q16. (Advanced) What are web streams (WHATWG Streams API) in Node.js? Should you use them?

**Answer**: Node.js (v16+) supports the WHATWG Streams API alongside the classic Node streams.

```js
// WHATWG ReadableStream
const response = await fetch('https://example.com/large-file');
const reader = response.body.getReader();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  process.stdout.write(value);
}
```

| | **Node Streams** | **WHATWG Streams** |
|---|---|---|
| **API** | Event-based (`.on('data')`) | Pull-based (`.read()`) |
| **Backpressure** | `.pipe()` / `pipeline()` | `pipeTo()` / `pipeThrough()` |
| **Ecosystem** | Vast (all of npm) | Growing (fetch, Web APIs) |
| **Recommendation** | Use for server-side | Use when interoping with fetch/Web APIs |

**Senior take**: Use Node streams for server-side work (better ecosystem, more battle-tested). Use WHATWG streams when working with `fetch()` or isomorphic code.

---

## Q17. (Advanced) How do you implement connection pooling with streams for database exports?

**Scenario**: 50 concurrent users request CSV exports. Each opens a DB cursor. You have a pool of 20 connections.

```js
const { Pool } = require('pg');
const pool = new Pool({ max: 20 });

app.get('/export', async (req, res) => {
  const client = await pool.connect(); // waits if pool exhausted

  try {
    res.setHeader('Content-Type', 'text/csv');
    res.write('id,name,email\n');

    const cursor = client.query(new Cursor('SELECT * FROM users WHERE active = true'));
    let rows;
    do {
      rows = await cursor.read(1000);
      for (const row of rows) {
        const ok = res.write(`${row.id},${row.name},${row.email}\n`);
        if (!ok) await new Promise(r => res.once('drain', r));
      }
    } while (rows.length > 0);

    res.end();
  } finally {
    client.release(); // ALWAYS release back to pool
  }
});
```

**Answer**: Key patterns: (1) `pool.connect()` limits concurrent DB connections, (2) Cursor-based reads limit memory, (3) Backpressure check on `res.write()`, (4) `finally` block ensures connection release even on error.

If pool is exhausted (20 active), the 21st request **waits** for a connection — natural backpressure.

---

## Q18. (Advanced) How do you benchmark stream throughput and find bottlenecks?

```js
const { Transform, Readable, pipeline } = require('stream');
const { performance } = require('perf_hooks');

let count = 0;
const start = performance.now();

const counter = new Transform({
  transform(chunk, enc, cb) {
    count += chunk.length;
    cb(null, chunk);
  }
});

const interval = setInterval(() => {
  const elapsed = (performance.now() - start) / 1000;
  const mbps = (count / 1024 / 1024) / elapsed;
  console.log(`Throughput: ${mbps.toFixed(2)} MB/s, Processed: ${(count / 1024 / 1024).toFixed(0)} MB`);
}, 1000);

await pipeline(source, counter, destination);
clearInterval(interval);
```

**Answer**: Insert a passthrough Transform that counts bytes and calculates throughput. If throughput is lower than expected, the bottleneck is usually the **slowest stage** — typically the writable (network, disk) or a CPU-heavy transform.

**Diagnosis**: If removing one stage doubles throughput, that stage is the bottleneck. Use `--prof` or flamegraphs to find hot code in Transform stages.

---

## Q19. (Advanced) How does Go handle the equivalent of Node.js streams? Compare the approaches.

**Answer**:

**Go approach** — `io.Reader`/`io.Writer` with `io.Copy`:
```go
// Go: copy file with automatic buffering
src, _ := os.Open("input.txt")
dst, _ := os.Create("output.txt")
io.Copy(dst, src) // buffers internally, blocking goroutine
```

**Node.js approach** — streams with async backpressure:
```js
await pipeline(
  fs.createReadStream('input.txt'),
  fs.createWriteStream('output.txt')
);
```

| | **Node.js Streams** | **Go io.Reader/Writer** |
|---|---|---|
| Backpressure | Event-driven, automatic with pipe | Blocking — goroutine sleeps |
| Complexity | Higher (events, modes, highWaterMark) | Lower (synchronous-looking) |
| Parallelism | Single thread, must yield | Goroutine per stream (cheap) |
| Error handling | Pipeline callback or try/catch | Return error from Read/Write |

**Tradeoff**: Node streams are powerful but complex. Go's approach is simpler because blocking a goroutine is cheap ($2KB stack). Python's asyncio streams are similar to Node's but less mature. Java's NIO Channels + Reactive Streams add even more complexity.

---

## Q20. (Advanced) Senior red flags to catch in code review related to streams.

**Answer**:

1. **`readFileSync` or `writeFileSync` in any request handler** — blocks the entire server
2. **Accumulating stream data in an array** — defeats the purpose of streaming
```js
// RED FLAG
const chunks = [];
stream.on('data', chunk => chunks.push(chunk));
stream.on('end', () => { const all = Buffer.concat(chunks); /* process */ });
// This loads everything into memory. Only acceptable for small known-bounded data.
```
3. **Not checking `write()` return value** — ignoring backpressure
4. **Using `.pipe()` without error handling** — errors on middle streams are swallowed
5. **Forgetting to destroy streams on error** — leaked file descriptors
```js
// RED FLAG
const stream = fs.createReadStream('file');
stream.on('error', (err) => { /* forgot stream.destroy() */ });
// FIX: use pipeline() which handles cleanup automatically
```
6. **Setting huge `highWaterMark` on many concurrent streams** — multiplied memory usage
7. **Mixing streams with `await` incorrectly** — causing deadlocks or uncaught errors

**Senior interview answer**: "I always use `pipeline()` over `.pipe()`, check backpressure on writes, never accumulate unbounded data, and monitor memory during stream-heavy operations."
