# 17. WebSockets & Real-Time Systems

## Topic Introduction

WebSockets provide **full-duplex, persistent connections** between client and server. Unlike HTTP (request-response), WebSockets keep the connection open for bidirectional streaming — ideal for chat, live dashboards, gaming, and collaborative editing.

```
HTTP:       Client → Request → Server → Response → Connection closed
WebSocket:  Client ↔ Server (persistent, bidirectional, real-time)

WebSocket Handshake:
  Client: GET /ws HTTP/1.1
          Upgrade: websocket
          Connection: Upgrade
  Server: HTTP/1.1 101 Switching Protocols
          Upgrade: websocket
  → Now: full-duplex binary/text frames flow both directions
```

Node.js is exceptionally suited for WebSockets because the event loop efficiently manages thousands of persistent connections with minimal memory per connection (~10-50KB). No thread-per-connection — just callbacks on a single thread.

**Go/Java tradeoff**: Go uses `gorilla/websocket` with one goroutine per connection (cheap, ~4KB stack). Java uses Spring WebSocket or Vert.x. Node.js uses `ws` (raw, fast) or Socket.IO (rooms, namespaces, auto-fallback). Node's event-driven model is the most natural fit for managing many idle connections.

---

## Q1. (Beginner) What is WebSocket? How does it differ from HTTP?

**Scenario**: You need to build a live notifications feature. Should you poll with HTTP or use WebSocket?

**Answer**:

| | **HTTP** | **WebSocket** |
|---|---|---|
| Connection | New connection per request | Single persistent connection |
| Direction | Client → Server (request/response) | Bidirectional |
| Overhead | Headers on every request (~800 bytes) | Minimal frame overhead (~2 bytes) |
| Latency | Polling delay (seconds) | Real-time (milliseconds) |
| Server push | Not native (requires SSE or polling) | Native |

```js
// HTTP polling (wasteful — new TCP connection every 5 seconds)
setInterval(async () => {
  const res = await fetch('/api/notifications');
  updateUI(await res.json());
}, 5000);

// WebSocket (efficient — single persistent connection)
const ws = new WebSocket('wss://api.example.com/notifications');
ws.onmessage = (event) => {
  updateUI(JSON.parse(event.data)); // instant, no polling
};
```

**When to use WebSocket**: Chat, live dashboards, multiplayer games, collaborative editing, stock tickers.
**When HTTP is fine**: REST APIs, file uploads, infrequent data that doesn't need real-time.

---

## Q2. (Beginner) How do you set up a basic WebSocket server in Node.js with the `ws` library?

```js
const http = require('http');
const WebSocket = require('ws');

const server = http.createServer(); // can share with Express
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws, req) => {
  console.log('New client connected from:', req.socket.remoteAddress);

  // Receive messages from client
  ws.on('message', (data) => {
    const message = JSON.parse(data.toString());
    console.log('Received:', message);

    // Echo back
    ws.send(JSON.stringify({ echo: message, timestamp: Date.now() }));
  });

  // Handle disconnection
  ws.on('close', (code, reason) => {
    console.log(`Client disconnected: ${code} ${reason}`);
  });

  // Handle errors
  ws.on('error', (err) => {
    console.error('WebSocket error:', err.message);
  });

  // Send welcome message
  ws.send(JSON.stringify({ type: 'welcome', message: 'Connected to server' }));
});

server.listen(3000, () => console.log('Server running on :3000'));
```

**Answer**: The `ws` library is the fastest Node.js WebSocket implementation. It creates a WebSocket server that can share the same HTTP server as Express. Each connection gets `message`, `close`, and `error` events.

---

## Q3. (Beginner) What is Socket.IO? How does it differ from raw WebSocket?

**Answer**:

| | **ws (raw WebSocket)** | **Socket.IO** |
|---|---|---|
| Protocol | Standard WebSocket (RFC 6455) | Custom protocol on top of WebSocket |
| Fallback | None (WebSocket only) | Long-polling, HTTP streaming |
| Rooms/namespaces | Manual implementation | Built-in |
| Auto-reconnection | Manual | Built-in |
| Binary support | Native | Built-in |
| Broadcasting | Manual loop | `io.to(room).emit()` |
| Client size | 0KB (browser native) | ~40KB |

```js
// Socket.IO server
const { Server } = require('socket.io');
const io = new Server(server, { cors: { origin: '*' } });

io.on('connection', (socket) => {
  console.log('Connected:', socket.id);

  // Join a room
  socket.join('room-123');

  // Listen for events (custom event names)
  socket.on('chat-message', (data) => {
    // Broadcast to everyone in the room except sender
    socket.to('room-123').emit('chat-message', {
      userId: socket.userId,
      text: data.text,
      timestamp: Date.now(),
    });
  });

  socket.on('disconnect', (reason) => {
    console.log('Disconnected:', socket.id, reason);
  });
});
```

**Recommendation**: Use `ws` for performance-critical server-to-server or when you control both client and server. Use Socket.IO for browser-facing apps where you need rooms, reconnection, and fallback transport.

---

## Q4. (Beginner) What is the WebSocket connection lifecycle? Explain open, message, close, and error events.

```js
const ws = new WebSocket('wss://api.example.com/ws');

// 1. CONNECTING (readyState = 0) — handshake in progress
ws.onopen = () => {
  // 2. OPEN (readyState = 1) — connected, can send/receive
  console.log('Connected');
  ws.send(JSON.stringify({ type: 'subscribe', channel: 'prices' }));
};

ws.onmessage = (event) => {
  // Receive data (text or binary)
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onclose = (event) => {
  // 3. CLOSED (readyState = 3) — connection ended
  console.log(`Closed: code=${event.code} reason=${event.reason} clean=${event.wasClean}`);
  // Common close codes: 1000 (normal), 1001 (going away), 1006 (abnormal)
};

ws.onerror = (error) => {
  // Error occurred (always followed by close)
  console.error('WebSocket error:', error);
};
```

**Answer**: WebSocket lifecycle: CONNECTING → OPEN → (messages flow) → CLOSING → CLOSED. The `close` event includes a code (1000 = normal, 1006 = abnormal disconnect, 1011 = server error). Always handle all four events.

---

## Q5. (Beginner) How do you implement heartbeat/ping-pong to detect dead connections?

**Scenario**: A client disconnects abruptly (network drops, laptop closes). The server doesn't know — the socket stays "open" consuming memory.

```js
const wss = new WebSocket.Server({ server });

// Heartbeat check — server side
function heartbeat() { this.isAlive = true; }

wss.on('connection', (ws) => {
  ws.isAlive = true;
  ws.on('pong', heartbeat); // client responds to ping
  ws.on('message', () => { ws.isAlive = true; }); // any message = alive
});

// Check every 30 seconds — terminate dead connections
const interval = setInterval(() => {
  wss.clients.forEach((ws) => {
    if (ws.isAlive === false) {
      console.log('Terminating dead connection');
      return ws.terminate(); // hard close — no close frame
    }
    ws.isAlive = false;
    ws.ping(); // send ping, expect pong back
  });
}, 30000);

wss.on('close', () => clearInterval(interval));
```

**Answer**: Without heartbeats, dead connections (half-open sockets) accumulate and waste memory. The server sends a `ping` frame every 30s. If no `pong` returns before the next check, the connection is terminated. This is a **production essential** — never skip it.

---

## Q6. (Intermediate) How do you authenticate WebSocket connections?

**Scenario**: Your chat app needs to verify user identity on WebSocket connect. You can't use session cookies easily with WebSocket.

```js
const jwt = require('jsonwebtoken');

// Option 1: Auth via query parameter during handshake
wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'http://localhost');
  const token = url.searchParams.get('token');

  try {
    ws.user = jwt.verify(token, process.env.JWT_SECRET);
    console.log('Authenticated:', ws.user.userId);
  } catch (err) {
    ws.close(4001, 'Authentication failed');
    return;
  }
  // ... handle messages
});

// Option 2: Auth via first message (token sent after connect)
wss.on('connection', (ws) => {
  ws.isAuthenticated = false;

  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());

    if (!ws.isAuthenticated) {
      if (msg.type !== 'auth') return ws.close(4001, 'Must authenticate first');
      try {
        ws.user = jwt.verify(msg.token, process.env.JWT_SECRET);
        ws.isAuthenticated = true;
        ws.send(JSON.stringify({ type: 'auth_success' }));
      } catch {
        ws.close(4001, 'Invalid token');
      }
      return;
    }

    // Handle authenticated messages
    handleMessage(ws, msg);
  });

  // Auto-close if not authenticated within 5 seconds
  setTimeout(() => {
    if (!ws.isAuthenticated) ws.close(4001, 'Auth timeout');
  }, 5000);
});
```

**Answer**: Two approaches — (1) Token in query string during handshake (simpler, but token visible in logs), (2) First message authentication (more secure, adds complexity). Always set an auth timeout to prevent unauthenticated connections from lingering.

---

## Q7. (Intermediate) How do you implement rooms/channels for group messaging?

```js
// Room management without Socket.IO
const rooms = new Map(); // roomId → Set<ws>

function joinRoom(ws, roomId) {
  if (!rooms.has(roomId)) rooms.set(roomId, new Set());
  rooms.get(roomId).add(ws);
  ws.rooms = ws.rooms || new Set();
  ws.rooms.add(roomId);
}

function leaveRoom(ws, roomId) {
  rooms.get(roomId)?.delete(ws);
  ws.rooms?.delete(roomId);
  if (rooms.get(roomId)?.size === 0) rooms.delete(roomId);
}

function broadcastToRoom(roomId, message, excludeWs = null) {
  const members = rooms.get(roomId);
  if (!members) return;
  const data = JSON.stringify(message);
  members.forEach((ws) => {
    if (ws !== excludeWs && ws.readyState === WebSocket.OPEN) {
      ws.send(data);
    }
  });
}

// Usage in message handler
ws.on('message', (raw) => {
  const msg = JSON.parse(raw.toString());
  switch (msg.type) {
    case 'join': joinRoom(ws, msg.roomId); break;
    case 'leave': leaveRoom(ws, msg.roomId); break;
    case 'chat': broadcastToRoom(msg.roomId, { type: 'chat', userId: ws.user.userId, text: msg.text }, ws); break;
  }
});

ws.on('close', () => {
  // Leave all rooms on disconnect
  ws.rooms?.forEach((roomId) => leaveRoom(ws, roomId));
});
```

**Answer**: Rooms are a map of room IDs to sets of WebSocket connections. On disconnect, clean up all room memberships. This is what Socket.IO does internally — implementing it manually gives you full control.

---

## Q8. (Intermediate) How do you handle client reconnection with message replay?

**Scenario**: Client loses connection for 5 seconds. Messages sent during that window are lost. How do you ensure delivery?

```js
// Server: store recent messages per room with timestamps
const messageHistory = new Map(); // roomId → [{ id, timestamp, data }]
const MAX_HISTORY = 1000;

function storeMessage(roomId, message) {
  if (!messageHistory.has(roomId)) messageHistory.set(roomId, []);
  const history = messageHistory.get(roomId);
  history.push(message);
  if (history.length > MAX_HISTORY) history.shift();
}

// Client sends last seen message ID on reconnect
ws.on('message', (raw) => {
  const msg = JSON.parse(raw.toString());
  if (msg.type === 'reconnect') {
    const history = messageHistory.get(msg.roomId) || [];
    const missedMessages = history.filter((m) => m.timestamp > msg.lastSeenTimestamp);
    ws.send(JSON.stringify({ type: 'replay', messages: missedMessages }));
    return;
  }
  // ... normal message handling
});

// Client side reconnection logic
class ReconnectingWebSocket {
  constructor(url) {
    this.url = url;
    this.lastSeenTimestamp = 0;
    this.reconnectDelay = 1000;
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.reconnectDelay = 1000; // reset backoff
      this.ws.send(JSON.stringify({ type: 'reconnect', lastSeenTimestamp: this.lastSeenTimestamp }));
    };
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.lastSeenTimestamp = data.timestamp || Date.now();
      this.onmessage?.(data);
    };
    this.ws.onclose = () => {
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // exponential backoff
    };
  }
}
```

**Answer**: Store recent message history server-side. On reconnect, client sends its last seen timestamp/ID. Server replays missed messages. Client implements exponential backoff for reconnection to avoid thundering herd.

---

## Q9. (Intermediate) What is Server-Sent Events (SSE)? When would you choose it over WebSocket?

```js
// SSE endpoint — simple server push
app.get('/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // Send event every second
  const interval = setInterval(() => {
    const data = JSON.stringify({ price: Math.random() * 100, timestamp: Date.now() });
    res.write(`data: ${data}\n\n`);
  }, 1000);

  // Named events
  res.write(`event: notification\ndata: {"message": "Welcome!"}\n\n`);

  req.on('close', () => {
    clearInterval(interval);
    console.log('SSE client disconnected');
  });
});

// Client
const source = new EventSource('/events');
source.onmessage = (e) => console.log(JSON.parse(e.data));
source.addEventListener('notification', (e) => console.log('Notification:', e.data));
```

**Answer**:

| | **WebSocket** | **SSE** |
|---|---|---|
| Direction | Bidirectional | Server → Client only |
| Protocol | Custom (ws://) | HTTP (regular) |
| Reconnection | Manual | Automatic (built-in) |
| Binary data | Yes | No (text only) |
| Browser support | All modern | All modern |
| Proxy/CDN friendly | Sometimes blocked | Always works (it's HTTP) |
| Best for | Chat, games, collaboration | Notifications, live feeds, dashboards |

**Choose SSE** when you only need server-push (live scores, notifications, stock prices). **Choose WebSocket** when you need bidirectional communication (chat, gaming, collaboration).

---

## Q10. (Intermediate) How do you rate-limit WebSocket messages per connection?

**Scenario**: A malicious client sends 10,000 messages per second to your chat server, overloading the event loop.

```js
class MessageRateLimiter {
  constructor(maxPerSecond = 10, maxPerMinute = 100) {
    this.maxPerSecond = maxPerSecond;
    this.maxPerMinute = maxPerMinute;
    this.secondCount = 0;
    this.minuteCount = 0;
    this.lastSecondReset = Date.now();
    this.lastMinuteReset = Date.now();
  }

  allow() {
    const now = Date.now();
    if (now - this.lastSecondReset > 1000) { this.secondCount = 0; this.lastSecondReset = now; }
    if (now - this.lastMinuteReset > 60000) { this.minuteCount = 0; this.lastMinuteReset = now; }

    this.secondCount++;
    this.minuteCount++;
    return this.secondCount <= this.maxPerSecond && this.minuteCount <= this.maxPerMinute;
  }
}

wss.on('connection', (ws) => {
  const limiter = new MessageRateLimiter(10, 200);
  let warnings = 0;

  ws.on('message', (data) => {
    if (!limiter.allow()) {
      warnings++;
      if (warnings > 3) {
        ws.close(4008, 'Rate limit exceeded — disconnected');
        return;
      }
      ws.send(JSON.stringify({ type: 'error', code: 'RATE_LIMITED', message: 'Slow down' }));
      return;
    }
    handleMessage(ws, data);
  });
});
```

**Answer**: Rate limit per connection with a token bucket or simple counter. Warn first, then disconnect repeat offenders. Also limit message **size** (`ws.on('message')` — check `data.length`). Without rate limiting, a single bad client can DOS your entire WebSocket server.

---

## Q11. (Intermediate) How do you handle binary data (images, files) over WebSocket?

```js
// Server: handle both text and binary messages
wss.on('connection', (ws) => {
  ws.on('message', (data, isBinary) => {
    if (isBinary) {
      // Binary data — save to file or forward
      const buffer = Buffer.from(data);
      console.log(`Received binary: ${buffer.length} bytes`);

      // Example: save uploaded image
      const filename = `upload-${Date.now()}.png`;
      fs.writeFileSync(`./uploads/${filename}`, buffer);
      ws.send(JSON.stringify({ type: 'upload_complete', filename }));
    } else {
      // Text data — parse as JSON
      const msg = JSON.parse(data.toString());
      handleTextMessage(ws, msg);
    }
  });
});

// Client: send binary data
const ws = new WebSocket('ws://localhost:3000');
// Send image as ArrayBuffer
const fileInput = document.querySelector('input[type="file"]');
fileInput.onchange = async (e) => {
  const buffer = await e.target.files[0].arrayBuffer();
  ws.send(buffer); // sent as binary frame
};
```

**Answer**: WebSocket natively supports binary frames alongside text. The `isBinary` flag distinguishes them. Use binary for: images, audio chunks (voice chat), screen sharing, protocol buffers. Limit binary message size on the server to prevent memory abuse.

---

## Q12. (Intermediate) How do you broadcast to all connected clients efficiently without blocking the event loop?

**Scenario**: 10,000 connected clients. You need to send a price update to all of them. Serializing 10k `JSON.stringify` + `ws.send` calls takes 200ms — blocking the event loop.

```js
// BAD: synchronous broadcast blocks event loop for 200ms
function broadcastBlocking(data) {
  const msg = JSON.stringify(data);
  wss.clients.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) ws.send(msg);
  });
}

// GOOD: serialize ONCE, batch with setImmediate
function broadcastBatched(data, batchSize = 500) {
  const msg = JSON.stringify(data); // serialize once
  const clients = [...wss.clients].filter(ws => ws.readyState === WebSocket.OPEN);

  let i = 0;
  function sendBatch() {
    const end = Math.min(i + batchSize, clients.length);
    for (; i < end; i++) {
      clients[i].send(msg);
    }
    if (i < clients.length) {
      setImmediate(sendBatch); // yield to event loop between batches
    }
  }
  sendBatch();
}
```

**Answer**: Two optimizations: (1) Serialize the message **once** (not per client), (2) Use `setImmediate` to yield between batches so the event loop can handle other events (HTTP requests, new connections). This prevents a single broadcast from blocking everything.

**Tradeoff with Go**: In Go, you'd use goroutines per broadcast (`go ws.WriteMessage(...)`) which are preemptively scheduled. No batching needed.

---

## Q13. (Advanced) How do you scale WebSockets across multiple Node.js servers?

**Scenario**: Single server handles 10k connections. You need 100k. You deploy 10 servers behind a load balancer. User A connects to Server 1, User B to Server 2 — they can't chat because they're on different servers.

```
Solution: Redis Pub/Sub as a message bus

Server 1 (10k connections)  ←→  Redis Pub/Sub  ←→  Server 2 (10k connections)
                             ←→                ←→  Server 3 (10k connections)
```

```js
const Redis = require('ioredis');
const pub = new Redis();
const sub = new Redis();

// Subscribe to channels
sub.subscribe('chat:room-123', 'chat:room-456');

// When a message arrives from any server via Redis
sub.on('message', (channel, message) => {
  const roomId = channel.replace('chat:', '');
  const members = rooms.get(roomId);
  if (!members) return;

  // Forward to local connections only
  members.forEach((ws) => {
    if (ws.readyState === WebSocket.OPEN) ws.send(message);
  });
});

// When a client sends a message
ws.on('message', (raw) => {
  const msg = JSON.parse(raw.toString());
  if (msg.type === 'chat') {
    const payload = JSON.stringify({ userId: ws.user.id, text: msg.text, timestamp: Date.now() });
    // Publish to ALL servers via Redis
    pub.publish(`chat:${msg.roomId}`, payload);
  }
});
```

**Answer**: Redis Pub/Sub acts as a message bus between servers. When Server 1 receives a chat message, it publishes to Redis. All servers subscribed to that channel receive it and forward to their local connections. Socket.IO has a built-in Redis adapter (`@socket.io/redis-adapter`) that does this automatically.

**Tradeoff with Go**: Go would use the same pattern (Redis Pub/Sub), but Go processes can handle more connections per instance (goroutines vs event loop), potentially needing fewer servers.

---

## Q14. (Advanced) How do you handle sticky sessions for WebSocket with a load balancer?

**Scenario**: WebSocket connections are long-lived. If a client reconnects after a brief network blip, the load balancer might route to a different server — losing room state.

```nginx
# nginx sticky sessions by IP hash
upstream websocket_servers {
    ip_hash;  # same client IP → same server
    server node1:3000;
    server node2:3000;
    server node3:3000;
}

server {
    location /ws {
        proxy_pass http://websocket_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;  # keep connection alive for 1 hour
        proxy_send_timeout 3600s;
    }
}
```

**Answer**: Sticky sessions ensure the same client always reaches the same server. Options: (1) IP hash (simple but breaks behind NAT), (2) Cookie-based (load balancer sets a cookie), (3) **Avoid stickiness entirely** by externalizing state to Redis (best for scalability).

**Best practice**: Don't rely on sticky sessions. Store all connection state (rooms, user data) in Redis. Any server can serve any reconnecting client.

---

## Q15. (Advanced) How do you implement real-time collaborative editing (like Google Docs)?

**Scenario**: Multiple users editing the same document simultaneously. Each keystroke is sent to the server and broadcast to all other editors.

```js
// Operational Transformation (OT) — simplified
class Document {
  constructor(content = '') { this.content = content; this.version = 0; }

  applyOperation(op) {
    switch (op.type) {
      case 'insert':
        this.content = this.content.slice(0, op.position) + op.text + this.content.slice(op.position);
        break;
      case 'delete':
        this.content = this.content.slice(0, op.position) + this.content.slice(op.position + op.count);
        break;
    }
    this.version++;
    return this;
  }

  // Transform operation against concurrent operation
  static transform(op1, op2) {
    if (op1.type === 'insert' && op2.type === 'insert') {
      if (op1.position <= op2.position) {
        return { ...op2, position: op2.position + op1.text.length };
      }
      return op2;
    }
    // ... more transform rules for insert/delete combinations
    return op2;
  }
}

// Server: receive operations, transform, apply, broadcast
const documents = new Map();

ws.on('message', (raw) => {
  const msg = JSON.parse(raw.toString());
  if (msg.type === 'operation') {
    const doc = documents.get(msg.docId);
    let op = msg.operation;

    // Transform against any concurrent operations since client's known version
    const pendingOps = doc.operationLog.slice(msg.baseVersion);
    for (const serverOp of pendingOps) {
      op = Document.transform(serverOp, op);
    }

    doc.applyOperation(op);
    doc.operationLog.push(op);

    // Broadcast transformed operation to all other editors
    broadcastToRoom(msg.docId, { type: 'operation', operation: op, version: doc.version }, ws);
  }
});
```

**Answer**: Real-time collaboration requires either **OT (Operational Transformation)** or **CRDTs (Conflict-free Replicated Data Types)**. OT transforms concurrent operations to maintain consistency. CRDTs (like Yjs, Automerge) are mathematically guaranteed to converge. For production, use libraries like **Yjs** (CRDT-based) rather than building from scratch.

---

## Q16. (Advanced) How do you monitor WebSocket connection health and performance in production?

```js
// Metrics to track
const metrics = {
  connectionsTotal: new Counter({ name: 'ws_connections_total', help: 'Total connections' }),
  connectionsActive: new Gauge({ name: 'ws_connections_active', help: 'Active connections' }),
  messagesReceived: new Counter({ name: 'ws_messages_received_total', help: 'Messages in' }),
  messagesSent: new Counter({ name: 'ws_messages_sent_total', help: 'Messages out' }),
  messageSize: new Histogram({ name: 'ws_message_size_bytes', help: 'Message size', buckets: [64, 256, 1024, 4096, 16384] }),
  connectionDuration: new Histogram({ name: 'ws_connection_duration_seconds', help: 'Connection lifetime' }),
};

wss.on('connection', (ws) => {
  const connectTime = Date.now();
  metrics.connectionsTotal.inc();
  metrics.connectionsActive.inc();

  ws.on('message', (data) => {
    metrics.messagesReceived.inc();
    metrics.messageSize.observe(data.length);
  });

  const originalSend = ws.send.bind(ws);
  ws.send = (data, ...args) => {
    metrics.messagesSent.inc();
    return originalSend(data, ...args);
  };

  ws.on('close', () => {
    metrics.connectionsActive.dec();
    metrics.connectionDuration.observe((Date.now() - connectTime) / 1000);
  });
});

// Alert rules:
// ws_connections_active > 50000 → "Approaching connection limit"
// rate(ws_messages_received_total[1m]) / ws_connections_active > 100 → "Message flood detected"
// ws_connection_duration_seconds_p50 < 10 → "Connections dropping quickly (network issue?)"
```

---

## Q17. (Advanced) How do you handle WebSocket connection limits and backpressure?

**Scenario**: Your server has 50k connections. A sudden spike to 80k causes OOM.

```js
const MAX_CONNECTIONS = 50000;
const MAX_MESSAGE_SIZE = 64 * 1024; // 64KB
const MAX_BUFFERED = 1024 * 1024; // 1MB per connection

wss.on('connection', (ws, req) => {
  // Reject new connections if at capacity
  if (wss.clients.size >= MAX_CONNECTIONS) {
    ws.close(1013, 'Server at capacity'); // 1013 = Try Again Later
    return;
  }

  ws.on('message', (data) => {
    // Reject oversized messages
    if (data.length > MAX_MESSAGE_SIZE) {
      ws.close(1009, 'Message too large'); // 1009 = Message Too Big
      return;
    }
    handleMessage(ws, data);
  });

  // Monitor backpressure — if we're sending faster than the client can receive
  const originalSend = ws.send.bind(ws);
  ws.send = (data, cb) => {
    if (ws.bufferedAmount > MAX_BUFFERED) {
      console.warn('Client too slow, dropping message');
      return; // drop message instead of buffering infinitely
    }
    originalSend(data, cb);
  };
});
```

**Answer**: Protect against: (1) Too many connections (reject with 1013), (2) Oversized messages (close with 1009), (3) Slow clients (check `bufferedAmount` before sending). Without backpressure handling, slow clients cause memory to grow unbounded.

---

## Q18. (Advanced) How does WebSocket compare to gRPC streaming for real-time backend communication?

**Answer**:

| | **WebSocket** | **gRPC Streaming** |
|---|---|---|
| Transport | TCP (ws:// or wss://) | HTTP/2 (h2) |
| Serialization | JSON (typically) | Protocol Buffers (binary, typed) |
| Schema | None (ad-hoc) | Strongly typed (.proto files) |
| Browser support | Native | Requires grpc-web proxy |
| Bidirectional | Yes | Yes (bidirectional streaming) |
| Use case | Browser ↔ Server | Service ↔ Service |
| Performance | Good | Better (binary, multiplexed) |

```protobuf
// gRPC streaming definition
service ChatService {
  rpc StreamMessages(stream ChatMessage) returns (stream ChatMessage);
}
```

```js
// Node.js gRPC bidirectional stream
const call = client.StreamMessages();
call.on('data', (message) => console.log('Received:', message));
call.write({ text: 'Hello', userId: '123' });
```

**When to use which**: WebSocket for browser-facing real-time features. gRPC streaming for service-to-service real-time communication (microservices, internal APIs). gRPC's strong typing and binary protocol make it more efficient for backend-to-backend.

---

## Q19. (Advanced) Design a notification system that handles 1M users with real-time delivery.

**Scenario**: Push notifications to 1M connected users when events occur (order shipped, payment received, etc).

```
Event Source (microservices) → Kafka → Notification Service → Redis Pub/Sub → WebSocket Servers
                                                                                   │
                                                                          ┌────────┼────────┐
                                                                     Server 1   Server 2   Server N
                                                                     (50k conn) (50k conn) (50k conn)
```

```js
// Notification Service — consume events and route to correct WS server
const consumer = kafka.consumer({ groupId: 'notification-service' });
await consumer.subscribe({ topic: 'user-events' });

await consumer.run({
  eachMessage: async ({ message }) => {
    const event = JSON.parse(message.value);

    // For targeted notifications: publish to user-specific channel
    await redis.publish(`user:${event.userId}`, JSON.stringify({
      type: 'notification',
      title: event.title,
      body: event.body,
      timestamp: Date.now(),
    }));
  },
});

// WebSocket server — subscribe to user channels on connect
wss.on('connection', (ws) => {
  const userId = ws.user.id;
  const sub = new Redis();
  sub.subscribe(`user:${userId}`);
  sub.on('message', (channel, msg) => {
    if (ws.readyState === WebSocket.OPEN) ws.send(msg);
  });

  ws.on('close', () => sub.unsubscribe().then(() => sub.quit()));
});
```

**Key architecture decisions**:
- **Kafka** buffers events (survives WS server restarts)
- **Redis Pub/Sub** routes to the correct WS server
- **Per-user channels** avoid broadcasting to all connections
- **Offline users**: store notifications in DB, deliver on next connect
- **Scale**: 20 WS servers × 50k connections each = 1M users

---

## Q20. (Advanced) Senior red flags in WebSocket implementations.

**Answer**:

1. **No heartbeat/ping-pong** — dead connections accumulate, consuming memory and file descriptors until OOM
2. **No authentication on WebSocket upgrade** — anyone can connect and listen to data
3. **No message size limit** — a single 1GB message crashes the server
4. **No rate limiting per connection** — one client can DOS the server with message floods
5. **Broadcasting in a synchronous loop** — blocks the event loop for 10k+ clients
6. **In-memory room state without Redis** — scaling to multiple servers is impossible; deploy loses all state
7. **No reconnection logic on client** — network blip = permanent disconnect
8. **Using `ws.send()` without checking `readyState`** — throws errors on closed connections
9. **No backpressure check** (`bufferedAmount`) — slow clients cause unbounded memory growth
10. **Sending user-specific data to broadcast channels** — data leaks between users

```js
// RED FLAG: sending without readyState check
wss.clients.forEach(ws => ws.send(data)); // crashes if any ws is CLOSING

// FIX: always check
wss.clients.forEach(ws => {
  if (ws.readyState === WebSocket.OPEN) ws.send(data);
});
```

**Senior interview answer**: "I design WebSocket systems with heartbeats for connection health, JWT auth on upgrade, Redis Pub/Sub for multi-server scaling, rate limiting and message size caps for abuse prevention, and batched broadcasting with `setImmediate` to protect the event loop. I externalize all state to Redis so any server can serve any client on reconnection."
