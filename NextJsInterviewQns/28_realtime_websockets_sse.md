# 28. Real-time: WebSockets, SSE & Live Data in Next.js

## Topic Introduction

**Real-time** in Next.js usually means **client-side** connections: **WebSockets** or **Server-Sent Events (SSE)**. The App Router doesn’t run a long-lived server per request, so WebSocket **servers** are typically run **outside** Next.js (e.g. separate Node server, or API route that upgrades only in a Node runtime). **SSE** can be implemented via a **Route Handler** that streams responses. Senior developers know where to put the socket server, how to stream from Route Handlers, and how to secure and scale.

```
Real-time options:
┌─────────────────────────────────────────────────────────────┐
│  WebSocket server: Separate process (e.g. ws on port 3001)   │
│  SSE: app/api/stream/route.ts → ReadableStream response      │
│  Client: use useEffect + new WebSocket() or EventSource      │
│  Auth: Token in query or first message; validate on server   │
└─────────────────────────────────────────────────────────────┘
```

---

## Q1. (Beginner) Can you handle a WebSocket connection inside a Next.js API Route (App Router route.ts)?

**Answer**:

**Not in a scalable way.** Route Handlers are **request–response**. They can’t keep a connection open for the lifetime of a WebSocket. Some setups **upgrade** the request in a **custom server** (Node **http** + **ws**), but that’s outside the default Vercel/serverless model. For production, run a **separate WebSocket server** (e.g. Node + **ws** on another port or host) and connect from the client to that URL.

---

## Q2. (Beginner) What is Server-Sent Events (SSE) and how does it differ from WebSockets?

**Answer**:

**SSE** is **one-way**: server → client over HTTP. The client uses **EventSource(url)**; the server sends text chunks in a specific format (e.g. `data: ...\n\n`). **WebSockets** are **two-way** and binary-capable. Use SSE for live updates (notifications, progress, logs); use WebSockets when the client must send frequent messages (chat, collaboration).

---

## Q3. (Beginner) In a Client Component, where should you open a WebSocket or EventSource connection?

**Answer**:

Inside **useEffect**. Open the connection when the component mounts; close it in the effect’s cleanup (return function). That avoids opening during SSR and ensures one connection per mounted instance. Store the socket/event source in a ref if you need to send messages or close from elsewhere.

---

## Q4. (Beginner) Why shouldn’t you open a WebSocket in the body of a React component (without useEffect)?

**Answer**:

The body runs on **every render** (and once on the server in SSR). So you’d create a new connection every render, never close the old ones, and possibly run browser-only APIs during SSR, which can crash or behave incorrectly. **useEffect** runs after mount (client-only) and only when dependencies change, so it’s the right place for side effects like opening a connection.

---

## Q5. (Beginner) How do you send authentication (e.g. JWT) when connecting to a WebSocket from the browser?

**Answer**:

WebSocket constructor doesn’t support headers in all browsers. Common approaches: (1) **Query string**: `wss://api.example.com/ws?token=JWT`. (2) **First message**: Send `{ type: 'auth', token }` after connection; server validates and drops if invalid. (3) **Cookie**: If the WS server shares the same origin (or credentials), send cookies. Prefer **query** or **first message** and keep tokens short-lived; validate on the server on connect.

---

## Q6. (Intermediate) Implement an SSE endpoint in the App Router that streams the current time every second for 10 seconds.

**Scenario**: GET /api/time-stream returns a stream of timestamps.

**Answer**:

Use a **Route Handler** that returns a **ReadableStream**. In the stream, write SSE-formatted lines (`data: ...\n\n`) on an interval; close after 10 seconds.

```tsx
// app/api/time-stream/route.ts
export async function GET() {
  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      let count = 0;
      const id = setInterval(() => {
        count++;
        controller.enqueue(encoder.encode(`data: ${new Date().toISOString()}\n\n`));
        if (count >= 10) {
          clearInterval(id);
          controller.close();
        }
      }, 1000);
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-store, no-cache',
      Connection: 'keep-alive',
    },
  });
}
```

---

## Q7. (Intermediate) Write a Client Component that subscribes to the SSE endpoint above and displays the latest timestamp.

**Answer**:

Use **useEffect** to create **EventSource**, listen for **message**, set state with **event.data**, and clean up **EventSource** on unmount.

```tsx
'use client';

import { useEffect, useState } from 'react';

export function TimeStream() {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    const es = new EventSource('/api/time-stream');
    es.onmessage = (e) => setTime(e.data);
    es.onerror = () => es.close();
    return () => es.close();
  }, []);

  return <p>Latest: {time ?? '—'}</p>;
}
```

---

## Q8. (Intermediate) Production scenario: Your SSE stream works locally but disconnects after ~30s on Vercel. Why?

**Answer**:

**Serverless function timeout.** Vercel (and many runtimes) limit execution time (e.g. 10–60s). A long-lived SSE response holds the function open; when it hits the limit, the connection is cut. **Options**: (1) Use a **streaming** pattern that ends within the limit (e.g. short-lived stream). (2) Host the SSE endpoint on a **long-running server** (e.g. VPS, container) or a platform that allows long-lived responses. (3) Use a **third-party** real-time service (e.g. Pusher, Ably) and keep Next.js for HTTP only.

---

## Q9. (Intermediate) How would you run a WebSocket server alongside a Next.js app for a self-hosted deployment?

**Answer**:

Run **two processes**: (1) Next.js (e.g. `node .next/standalone/server.js` or `next start`). (2) A small Node script that creates an **http.Server** and attaches **ws** (or similar). They can share the same server only if you use a **custom server** (e.g. Node **http** + **next** and **ws** on the same port), which is not supported on Vercel. For Docker, run both in the same container (e.g. supervisord) or as two containers behind a reverse proxy that routes `/ws` to the WS server and `/` to Next.js.

---

## Q10. (Intermediate) Find the bug: The client reconnects to the WebSocket every time the component re-renders.

**Wrong code**:

```tsx
'use client';
function Chat() {
  const [msgs, setMsgs] = useState([]);
  const ws = new WebSocket('wss://api.example.com/ws');
  ws.onmessage = (e) => setMsgs((m) => [...m, JSON.parse(e.data)]);
  return <ul>{msgs.map((m) => <li key={m.id}>{m.text}</li>)}</ul>;
}
```

**Answer**:

**WebSocket is created in the render path.** Every re-render (e.g. when **setMsgs** runs) creates a **new** WebSocket. **Fix**: Create the WebSocket inside **useEffect** and store it in a **ref** (or state if you need to trigger re-renders on open/close). Clean up in the effect return.

```tsx
const [msgs, setMsgs] = useState([]);
const wsRef = useRef<WebSocket | null>(null);

useEffect(() => {
  const ws = new WebSocket('wss://api.example.com/ws');
  wsRef.current = ws;
  ws.onmessage = (e) => setMsgs((m) => [...m, JSON.parse(e.data)]);
  return () => {
    ws.close();
    wsRef.current = null;
  };
}, []);
```

---

## Q11. (Intermediate) How do you avoid memory leaks when the user navigates away from a page that has an open WebSocket or EventSource?

**Answer**:

Close the connection in the **cleanup** of **useEffect** (the function you return). When the component unmounts (e.g. user navigates away), React runs the cleanup, so the socket is closed and the **onmessage** handler is no longer attached. Don’t call **setState** after unmount; if you do async work in **onmessage**, guard with a mounted flag or abort signal.

---

## Q12. (Intermediate) You need to broadcast a message from a Server Action to all connected WebSocket clients. How do you structure this?

**Answer**:

The Server Action runs in the Next.js server; the WebSocket server is a **separate process**. So the Server Action cannot directly push to sockets. **Options**: (1) **Pub/Sub**: Server Action publishes to Redis (or similar); the WebSocket server subscribes and broadcasts to its clients. (2) **HTTP callback**: Server Action calls an endpoint on the WebSocket server (e.g. POST /broadcast), and that server pushes to all clients. (3) **Database + polling**: Clients poll or use SSE from Next.js that reads from a DB that the Server Action updates (less real-time but no separate WS server).

---

## Q13. (Advanced) Implement a Route Handler that streams JSON array chunks (NDJSON) for a large list, and a client that consumes it and renders incrementally.

**Scenario**: GET /api/users returns 10k users; stream as newline-delimited JSON.

**Answer**:

**Route Handler**: Fetch or generate users in chunks; for each chunk, encode as JSON + `\n` and enqueue. Return **ReadableStream** with **Content-Type: application/x-ndjson** (or **application/json** with streaming).

**Client**: Use **fetch** with **body.getReader()**, decode chunks, parse lines, accumulate users, set state (or append to a list). Render the list as it grows (e.g. virtual list for performance). This gives progressive loading without loading 10k items in one JSON blob.

---

## Q14. (Advanced) How do you secure an SSE endpoint so only authenticated users can subscribe?

**Answer**:

- **Cookie/session**: Read **cookies()** in the Route Handler; validate the session. If invalid, return **401**. If valid, proceed to stream. The browser sends cookies with **EventSource** for same-origin requests.
- **Token in query**: e.g. **/api/stream?token=...**. Validate the token in the Route Handler; return **401** if invalid. Prefer short-lived tokens; avoid logging tokens in URLs.
- **Header**: **EventSource** doesn’t support custom headers. So for cross-origin or token-based auth, use **fetch** + **ReadableStream** and pass **Authorization** header; then parse the stream in client code (no **EventSource**).

---

## Q15. (Advanced) What are the trade-offs of using a third-party real-time service (Pusher, Ably, Socket.io Cloud) vs your own WebSocket server with Next.js?

**Answer**:

- **Third-party**: No server to run; scales automatically; often has SDKs and fallbacks (e.g. long polling). Cost at scale; vendor lock-in; data goes through their servers.
- **Own WS server**: Full control; data stays in your infra; no per-message cost. You operate and scale it (e.g. sticky sessions, Redis adapter for multi-instance); you handle reconnection and backoff in the client.

Use third-party for speed-to-market and when you don’t want to operate real-time infra; use your own when you need control, compliance, or cost optimization at high volume.

---

## Q16. (Advanced) How does the Edge runtime affect SSE or WebSocket in Next.js?

**Answer**:

**Edge** Route Handlers run in a short-lived environment; they can **stream** responses (SSE is fine for responses that end or are short-lived). They **cannot** host a long-lived WebSocket server. So: **SSE from Edge** = OK for bounded streams. **WebSocket server** = must run in Node or another long-lived runtime, not in Edge.

---

## Q17. (Advanced) Design a simple “live cursor” feature: multiple users see each other’s cursor position. What do you use on the client and “server”?

**Answer**:

- **Client**: On mouse move (throttled), send position to a backend (WebSocket message to your WS server, or POST to an API that broadcasts via pub/sub). Subscribe to other users’ positions (WebSocket or SSE) and render them.
- **Server**: WebSocket server that keeps a map of connection → user id; on message, broadcast to other connections (or use Redis pub/sub across instances). Alternatively, use a service (e.g. Ably) with presence/channel API.
- **Next.js**: Can host the HTTP API that receives cursor updates and/or the SSE feed; the actual WebSocket server (if used) runs separately.

---

## Q18. (Advanced) How do you test an SSE or WebSocket client in a Next.js app (unit or integration)?

**Answer**:

- **Unit**: Mock **EventSource** or **WebSocket** (e.g. set **global.EventSource = jest.fn()** returning a mock that triggers **onmessage**). Test that the component updates state and cleans up.
- **Integration**: Start a real SSE endpoint (or mock server) and a real WebSocket server in the test env; render the component, assert it receives and displays data, then unmount and assert the connection is closed.
- **E2E**: Point the app at a test SSE/WS endpoint and assert visible updates in the UI.

---

## Q19. (Advanced) Next.js 15/16: Does the default fetch cache or request deduplication affect SSE or WebSocket?

**Answer**:

**No.** SSE is a **streaming** response; the client holds the connection open. Fetch cache applies to **request–response** fetches. WebSocket is a different protocol. So your SSE Route Handler and WS client are not affected by **fetch** cache or **requestMemo** in Next.js. The only thing to avoid is caching the **Route Handler** response (don’t add cache headers that would store the stream).

---

## Q20. (Advanced) Production scenario: Under load, the WebSocket server has too many connections per process. How do you scale?

**Answer**:

- **Horizontal scaling**: Run multiple WS server instances behind a load balancer with **sticky sessions** (same client always to the same instance) so one connection stays on one process.
- **Redis adapter**: Use **socket.io-redis** (or similar) so that messages are pub/subbed across instances; any instance can broadcast to all clients.
- **Dedicated service**: Use a managed service (e.g. Pusher, Ably) that scales connections for you.
- **Connection limits**: Limit connections per user (e.g. one per user id) and per IP to avoid abuse.
