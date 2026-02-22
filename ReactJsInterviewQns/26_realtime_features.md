# Real-Time Features in React 18 — WebSockets, SSE & Optimistic UI Interview Questions

## Topic Introduction

Modern web applications demand real-time experiences — chat messages that appear instantly, dashboards that stream live metrics, collaborative editors where multiple users see each other's cursors, and notification bells that light up the moment something happens. React 18 is uniquely positioned to power these experiences thanks to **concurrent rendering**, **automatic batching**, and **transitions**, all of which let you absorb bursts of high-frequency updates without janking the UI. But React itself is agnostic to the transport layer: it does not ship with a WebSocket client or an SSE helper. The developer must choose the right real-time primitive — **polling**, **Server-Sent Events (SSE)**, or **WebSockets** — integrate it into the React lifecycle, and handle a raft of production concerns: reconnection, authentication, message ordering, deduplication, and optimistic UI to mask latency.

Optimistic UI is a pattern that has exploded in importance alongside real-time features. The idea is simple: *assume the server will succeed and update the UI immediately*, then reconcile when the server responds. This makes apps feel lightning-fast even when the network is slow. React 18's `startTransition` and React 19's experimental `useOptimistic` hook provide first-class tools for this pattern, but even without them, the concept can be implemented with `useReducer` and careful state design. Combining optimistic updates with real-time server pushes (WebSocket confirmations, for example) is a pattern used heavily at companies like Meta (Messenger), Figma (collaborative design), and Linear (issue tracking).

The code snippet below illustrates the full spectrum of what we will cover — a component that opens a WebSocket, displays real-time messages, and performs optimistic sends:

```jsx
import { useReducer, useEffect, useRef, useCallback } from 'react';

// Reducer handles both optimistic and confirmed messages
function chatReducer(state, action) {
  switch (action.type) {
    case 'SEND_OPTIMISTIC':
      return {
        ...state,
        messages: [...state.messages, { ...action.payload, status: 'pending' }],
      };
    case 'CONFIRM':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.clientId === action.payload.clientId
            ? { ...action.payload, status: 'confirmed' }
            : m
        ),
      };
    case 'RECEIVE':
      // Deduplicate — ignore if we already have it optimistically
      if (state.messages.some((m) => m.clientId === action.payload.clientId))
        return state;
      return { ...state, messages: [...state.messages, { ...action.payload, status: 'confirmed' }] };
    case 'REJECT':
      return {
        ...state,
        messages: state.messages.map((m) =>
          m.clientId === action.payload.clientId
            ? { ...m, status: 'failed' }
            : m
        ),
      };
    default:
      return state;
  }
}

function useRealtimeChat(url) {
  const [state, dispatch] = useReducer(chatReducer, { messages: [] });
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'confirm') dispatch({ type: 'CONFIRM', payload: msg });
      else dispatch({ type: 'RECEIVE', payload: msg });
    };

    return () => ws.close();
  }, [url]);

  const send = useCallback((text) => {
    const clientId = crypto.randomUUID();
    const payload = { clientId, text, author: 'me', timestamp: Date.now() };
    dispatch({ type: 'SEND_OPTIMISTIC', payload });
    wsRef.current?.send(JSON.stringify(payload));
  }, []);

  return { messages: state.messages, send };
}
```

---

## Beginner Level (Q1–Q5)

---

### Q1. What are the key differences between Polling, WebSockets, and Server-Sent Events (SSE), and when should you use each in a React application?

**Answer:**

These are three fundamentally different approaches to getting data from a server to a client:

| Feature | Polling | SSE | WebSockets |
|---|---|---|---|
| Direction | Client → Server (repeated) | Server → Client (one-way) | Bidirectional |
| Protocol | HTTP | HTTP (text/event-stream) | ws:// or wss:// |
| Reconnection | Manual (setInterval) | Built-in (EventSource auto-reconnects) | Manual |
| Browser support | Universal | All modern (no IE) | All modern |
| Overhead | High (new request each time) | Low (single HTTP connection) | Lowest (persistent TCP) |

**When to use each:**

- **Polling**: When updates are infrequent (every 30s+), the server doesn't support persistent connections, or you need simplicity. Example: checking for new email every minute.
- **SSE**: When data flows *only* from server to client — live scores, stock tickers, notification streams. SSE is simpler than WebSockets and works over HTTP/2 multiplexing.
- **WebSockets**: When you need *bidirectional*, low-latency communication — chat, collaborative editing, multiplayer games, or any scenario where the client also sends frequent messages.

```jsx
// Polling example — simple but wasteful
function usePolling(url, intervalMs = 5000) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const res = await fetch(url);
        const json = await res.json();
        if (active) setData(json);
      } catch (err) {
        console.error('Poll failed:', err);
      }
    };

    poll(); // initial fetch
    const id = setInterval(poll, intervalMs);

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [url, intervalMs]);

  return data;
}

// SSE example — server pushes, auto-reconnect
function useSSE(url) {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const source = new EventSource(url);

    source.onmessage = (e) => {
      setEvents((prev) => [...prev, JSON.parse(e.data)]);
    };

    source.onerror = () => {
      console.warn('SSE connection error — browser will auto-reconnect');
    };

    return () => source.close();
  }, [url]);

  return events;
}

// WebSocket example — full duplex
function useWebSocket(url) {
  const [messages, setMessages] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onmessage = (e) =>
      setMessages((prev) => [...prev, JSON.parse(e.data)]);
    return () => ws.close();
  }, [url]);

  const send = useCallback(
    (msg) => wsRef.current?.send(JSON.stringify(msg)),
    []
  );

  return { messages, send };
}
```

---

### Q2. How do you set up a basic WebSocket connection in React using `useEffect`, and why is cleanup critical?

**Answer:**

A WebSocket connection is a **side effect** — it opens a persistent TCP connection to the server. In React, side effects belong in `useEffect`. The cleanup function returned from `useEffect` must close the socket; otherwise, you leak connections on unmount or when the URL dependency changes (React will run the old cleanup before the new effect).

Key considerations:
1. Open the connection inside `useEffect`, not during render.
2. Attach event listeners (`onopen`, `onmessage`, `onerror`, `onclose`) synchronously after construction.
3. Store the WebSocket instance in a `useRef` so that event handlers and the `send` function always reference the current socket without triggering re-renders.
4. In Strict Mode (development), React mounts → unmounts → remounts your component, so you will see two connections briefly. This is expected and tests that your cleanup works.

```jsx
import { useEffect, useRef, useState, useCallback } from 'react';

function LivePrice({ symbol }) {
  const [price, setPrice] = useState(null);
  const [status, setStatus] = useState('connecting');
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(`wss://prices.example.com/ws?symbol=${symbol}`);
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPrice(data.price);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setStatus('error');
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed: code=${event.code} reason=${event.reason}`);
      setStatus('disconnected');
    };

    // CRITICAL: cleanup closes the socket
    return () => {
      ws.close(1000, 'Component unmounted');
    };
  }, [symbol]); // Re-open if symbol changes

  return (
    <div>
      <span>Status: {status}</span>
      <h2>{symbol}: {price ?? '—'}</h2>
    </div>
  );
}
```

**Why cleanup is critical:**

Without `ws.close()` in the cleanup function:
- Navigating away from the component leaves the socket open, consuming memory and bandwidth.
- Changing the `symbol` prop opens a *new* socket without closing the old one, leading to duplicate connections and stale data writing to state of an unmounted component.
- In Strict Mode development, you get two open connections immediately.

---

### Q3. How do Server-Sent Events (SSE) work in React, and what advantages do they have over WebSockets for one-way data streaming?

**Answer:**

SSE uses the `EventSource` browser API to open a persistent HTTP connection where the **server** pushes text-based events to the client. The protocol is simple: the server responds with `Content-Type: text/event-stream` and writes `data:` lines separated by double newlines.

**Advantages over WebSockets for one-way streaming:**

1. **Built-in reconnection**: If the connection drops, `EventSource` automatically reconnects with a `Last-Event-ID` header, so the server can resume from where it left off. WebSockets require you to build this yourself.
2. **Works through HTTP proxies and CDNs**: SSE is just HTTP, so it passes through corporate proxies and CDNs that may block WebSocket upgrades.
3. **HTTP/2 multiplexing**: Multiple SSE streams share a single TCP connection under HTTP/2, eliminating the per-connection overhead.
4. **Simpler server implementation**: No upgrade handshake, no frame parsing — just print lines to the response stream.

```jsx
import { useEffect, useState } from 'react';

function LiveScoreboard({ matchId }) {
  const [scores, setScores] = useState({ home: 0, away: 0 });
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const source = new EventSource(
      `/api/matches/${matchId}/stream`
    );

    // Default "message" event
    source.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setScores(data.score);
    };

    // Named event — server sends "event: goal\ndata: {...}\n\n"
    source.addEventListener('goal', (e) => {
      const goal = JSON.parse(e.data);
      setEvents((prev) => [...prev, goal]);
    });

    source.addEventListener('card', (e) => {
      const card = JSON.parse(e.data);
      setEvents((prev) => [...prev, card]);
    });

    source.onerror = () => {
      // EventSource auto-reconnects; log for observability
      console.warn('SSE connection error — reconnecting…');
    };

    return () => source.close();
  }, [matchId]);

  return (
    <div>
      <h2>{scores.home} – {scores.away}</h2>
      <ul>
        {events.map((evt, i) => (
          <li key={i}>{evt.minute}′ — {evt.description}</li>
        ))}
      </ul>
    </div>
  );
}
```

**Server side (Node.js/Express) for reference:**

```jsx
app.get('/api/matches/:id/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
  });

  const interval = setInterval(() => {
    const data = getLatestScore(req.params.id);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }, 1000);

  req.on('close', () => clearInterval(interval));
});
```

---

### Q4. How do you integrate Socket.IO with a React application, and how does it differ from raw WebSockets?

**Answer:**

Socket.IO is a library that wraps WebSockets and adds features that raw WebSockets lack:

1. **Automatic reconnection** with configurable back-off.
2. **Rooms and namespaces** for broadcasting to subsets of clients.
3. **Event-based API** — emit named events with structured payloads, not just raw strings.
4. **Fallback to HTTP long-polling** if WebSocket upgrade fails (corporate firewalls).
5. **Acknowledgements** — the server can confirm receipt of a message.
6. **Binary support** out of the box.

**Important caveat:** A Socket.IO client **cannot** connect to a plain WebSocket server and vice versa. Socket.IO uses its own protocol on top of WebSocket/HTTP.

Best practice in React: create the socket instance **outside** the component tree (singleton) or in a context provider, so it survives re-renders and is shared across components.

```jsx
// socket.js — singleton, created once
import { io } from 'socket.io-client';

export const socket = io('https://api.example.com', {
  autoConnect: false,          // connect explicitly after auth
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 30000,
  auth: {
    token: () => localStorage.getItem('accessToken'), // dynamic auth
  },
});

// SocketProvider.jsx — Context for components
import { createContext, useContext, useEffect, useState } from 'react';
import { socket } from './socket';

const SocketContext = createContext(null);

export function SocketProvider({ children }) {
  const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    socket.connect();

    socket.on('connect', () => setIsConnected(true));
    socket.on('disconnect', () => setIsConnected(false));

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
}

export const useSocket = () => useContext(SocketContext);

// ChatRoom.jsx — Consumer component
import { useSocket } from './SocketProvider';
import { useEffect, useState } from 'react';

function ChatRoom({ roomId }) {
  const { socket, isConnected } = useSocket();
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    socket.emit('join-room', roomId);

    socket.on('new-message', (msg) => {
      setMessages((prev) => [...prev, msg]);
    });

    return () => {
      socket.emit('leave-room', roomId);
      socket.off('new-message');
    };
  }, [socket, roomId]);

  const sendMessage = (text) => {
    socket.emit('send-message', { roomId, text }, (ack) => {
      // Server acknowledgement
      console.log('Message delivered:', ack.id);
    });
  };

  return (
    <div>
      <span>{isConnected ? '🟢 Connected' : '🔴 Disconnected'}</span>
      {messages.map((m) => (
        <p key={m.id}>{m.author}: {m.text}</p>
      ))}
    </div>
  );
}
```

---

### Q5. What is Optimistic UI, and how do you implement a basic optimistic update pattern in React?

**Answer:**

**Optimistic UI** means updating the interface *immediately* as if the server action has already succeeded, then reconciling with the actual server response when it arrives. If the server rejects the action, you roll back to the previous state. This eliminates perceived latency and makes apps feel instant.

**The pattern has three phases:**

1. **Optimistic apply** — Update local state immediately with the expected result.
2. **Server round-trip** — Send the request to the server in the background.
3. **Reconcile** — On success, optionally replace the optimistic data with the server-canonical data (which may include server-generated fields like `id` or `createdAt`). On failure, **roll back** to the previous state and show an error.

```jsx
import { useReducer, useCallback } from 'react';

function todoReducer(state, action) {
  switch (action.type) {
    case 'ADD_OPTIMISTIC':
      return [
        ...state,
        {
          ...action.payload,
          id: action.payload.tempId,
          status: 'pending', // visual indicator
        },
      ];
    case 'CONFIRM_ADD':
      return state.map((todo) =>
        todo.id === action.payload.tempId
          ? { ...action.payload.serverTodo, status: 'confirmed' }
          : todo
      );
    case 'ROLLBACK_ADD':
      return state.filter((todo) => todo.id !== action.payload.tempId);
    case 'DELETE_OPTIMISTIC':
      return state.map((todo) =>
        todo.id === action.payload.id
          ? { ...todo, status: 'deleting' }
          : todo
      );
    case 'CONFIRM_DELETE':
      return state.filter((todo) => todo.id !== action.payload.id);
    case 'ROLLBACK_DELETE':
      return state.map((todo) =>
        todo.id === action.payload.id
          ? { ...todo, status: 'confirmed' }
          : todo
      );
    default:
      return state;
  }
}

function TodoApp() {
  const [todos, dispatch] = useReducer(todoReducer, []);

  const addTodo = useCallback(async (text) => {
    const tempId = crypto.randomUUID();

    // Phase 1: Optimistic apply
    dispatch({
      type: 'ADD_OPTIMISTIC',
      payload: { tempId, text, completed: false },
    });

    try {
      // Phase 2: Server round-trip
      const res = await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const serverTodo = await res.json();

      // Phase 3a: Confirm
      dispatch({ type: 'CONFIRM_ADD', payload: { tempId, serverTodo } });
    } catch (err) {
      // Phase 3b: Rollback
      dispatch({ type: 'ROLLBACK_ADD', payload: { tempId } });
      toast.error('Failed to add todo — please try again');
    }
  }, []);

  const deleteTodo = useCallback(async (id) => {
    dispatch({ type: 'DELETE_OPTIMISTIC', payload: { id } });

    try {
      await fetch(`/api/todos/${id}`, { method: 'DELETE' });
      dispatch({ type: 'CONFIRM_DELETE', payload: { id } });
    } catch {
      dispatch({ type: 'ROLLBACK_DELETE', payload: { id } });
      toast.error('Failed to delete todo');
    }
  }, []);

  return (
    <ul>
      {todos.map((todo) => (
        <li
          key={todo.id}
          style={{ opacity: todo.status === 'pending' ? 0.6 : 1 }}
        >
          {todo.text}
          {todo.status === 'pending' && <span> (saving…)</span>}
          {todo.status === 'deleting' && <span> (deleting…)</span>}
          <button onClick={() => deleteTodo(todo.id)}>×</button>
        </li>
      ))}
    </ul>
  );
}
```

**Key takeaways:**
- Use a `tempId` (client-generated UUID) so you can match the optimistic entry to the server response.
- Show a visual indicator (`opacity`, spinner) for pending items so the user knows it hasn't been confirmed yet.
- Always handle the failure path — a silent rollback confuses users.

---

## Intermediate Level (Q6–Q12)

---

### Q6. How do you build a production-grade custom `useWebSocket` hook with automatic reconnection, exponential back-off, and heartbeat?

**Answer:**

A production WebSocket hook must handle far more than just opening a connection. Real networks are unreliable: connections drop silently (especially on mobile), servers restart during deploys, and load balancers have idle timeout limits. A robust hook needs:

1. **Automatic reconnection** with exponential back-off (1s → 2s → 4s → max 30s).
2. **Heartbeat/ping-pong** to detect dead connections that the OS hasn't noticed yet.
3. **Connection state machine** so the UI can show "connecting", "connected", "reconnecting", "disconnected".
4. **Unmount safety** — don't reconnect after the component has unmounted.
5. **Message buffering** — optionally queue messages sent while disconnected and flush on reconnect.

```jsx
import { useEffect, useRef, useState, useCallback } from 'react';

const STATES = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  DISCONNECTED: 'disconnected',
};

export function useWebSocket(url, {
  onMessage,
  onOpen,
  onClose,
  reconnect = true,
  maxRetries = Infinity,
  heartbeatInterval = 30000,
  maxBackoff = 30000,
} = {}) {
  const [connectionState, setConnectionState] = useState(STATES.CONNECTING);
  const wsRef = useRef(null);
  const retriesRef = useRef(0);
  const heartbeatRef = useRef(null);
  const unmountedRef = useRef(false);
  const messageQueueRef = useRef([]);

  const clearHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (unmountedRef.current) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      retriesRef.current = 0;
      setConnectionState(STATES.CONNECTED);
      onOpen?.();

      // Flush queued messages
      while (messageQueueRef.current.length > 0) {
        ws.send(messageQueueRef.current.shift());
      }

      // Start heartbeat
      clearHeartbeat();
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, heartbeatInterval);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'pong') return; // heartbeat response
      onMessage?.(data, event);
    };

    ws.onclose = (event) => {
      clearHeartbeat();
      onClose?.(event);

      if (unmountedRef.current) return;

      if (reconnect && retriesRef.current < maxRetries && event.code !== 1000) {
        const delay = Math.min(
          1000 * Math.pow(2, retriesRef.current),
          maxBackoff
        );
        retriesRef.current += 1;
        setConnectionState(STATES.RECONNECTING);
        console.log(`Reconnecting in ${delay}ms (attempt ${retriesRef.current})`);
        setTimeout(connect, delay);
      } else {
        setConnectionState(STATES.DISCONNECTED);
      }
    };

    ws.onerror = () => {
      // onerror is always followed by onclose — handle reconnection there
    };
  }, [url, reconnect, maxRetries, maxBackoff, heartbeatInterval,
      onMessage, onOpen, onClose, clearHeartbeat]);

  useEffect(() => {
    unmountedRef.current = false;
    connect();

    return () => {
      unmountedRef.current = true;
      clearHeartbeat();
      wsRef.current?.close(1000, 'Hook unmounted');
    };
  }, [connect, clearHeartbeat]);

  const send = useCallback((data) => {
    const message = typeof data === 'string' ? data : JSON.stringify(data);

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    } else {
      // Buffer message for when connection is restored
      messageQueueRef.current.push(message);
    }
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close(1000, 'Manual disconnect');
  }, []);

  return { connectionState, send, disconnect };
}

// Usage
function Dashboard() {
  const { connectionState, send } = useWebSocket('wss://api.example.com/ws', {
    onMessage: (data) => {
      console.log('Received:', data);
    },
    heartbeatInterval: 25000,
  });

  return (
    <div>
      <span className={`status status--${connectionState}`}>
        {connectionState}
      </span>
      <button onClick={() => send({ type: 'subscribe', channel: 'metrics' })}>
        Subscribe
      </button>
    </div>
  );
}
```

---

### Q7. How do you build a real-time notification system in React with prioritization and batching?

**Answer:**

A production notification system involves several layers:
1. **Transport**: A persistent connection (WebSocket or SSE) to receive notifications.
2. **State management**: A store that holds notifications, supports marking as read, and handles deduplication.
3. **Prioritization**: Urgent notifications (security alerts) get shown immediately; low-priority ones (social updates) get batched.
4. **Batching for performance**: When many notifications arrive in a burst (e.g., a mass email campaign), batch them so the UI doesn't re-render on every single one.
5. **Toast/banner layer**: A visual layer that shows transient popups for new notifications.

```jsx
import { useReducer, useEffect, useCallback, useRef } from 'react';

// Notification priorities
const PRIORITY = { URGENT: 0, HIGH: 1, NORMAL: 2, LOW: 3 };

function notificationReducer(state, action) {
  switch (action.type) {
    case 'ADD_BATCH': {
      const newItems = action.payload.filter(
        (n) => !state.byId[n.id] // deduplicate
      );
      if (newItems.length === 0) return state;
      const byId = { ...state.byId };
      newItems.forEach((n) => { byId[n.id] = { ...n, read: false }; });
      const allIds = [...newItems.map((n) => n.id), ...state.allIds];
      // Sort by priority, then timestamp descending
      allIds.sort((a, b) => {
        const diff = byId[a].priority - byId[b].priority;
        return diff !== 0 ? diff : byId[b].timestamp - byId[a].timestamp;
      });
      return { ...state, byId, allIds, unreadCount: state.unreadCount + newItems.length };
    }
    case 'MARK_READ': {
      if (state.byId[action.payload]?.read) return state;
      return {
        ...state,
        byId: { ...state.byId, [action.payload]: { ...state.byId[action.payload], read: true } },
        unreadCount: state.unreadCount - 1,
      };
    }
    case 'MARK_ALL_READ': {
      const byId = { ...state.byId };
      state.allIds.forEach((id) => { byId[id] = { ...byId[id], read: true }; });
      return { ...state, byId, unreadCount: 0 };
    }
    default:
      return state;
  }
}

function useNotifications(wsUrl) {
  const [state, dispatch] = useReducer(notificationReducer, {
    byId: {},
    allIds: [],
    unreadCount: 0,
  });

  const batchRef = useRef([]);
  const timerRef = useRef(null);

  const flushBatch = useCallback(() => {
    if (batchRef.current.length > 0) {
      dispatch({ type: 'ADD_BATCH', payload: batchRef.current });
      batchRef.current = [];
    }
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const notification = JSON.parse(event.data);

      // Urgent notifications bypass batching
      if (notification.priority === PRIORITY.URGENT) {
        dispatch({ type: 'ADD_BATCH', payload: [notification] });
        showUrgentToast(notification);
        return;
      }

      // Batch normal/low-priority notifications — flush every 500ms
      batchRef.current.push(notification);
      if (!timerRef.current) {
        timerRef.current = setTimeout(() => {
          flushBatch();
          timerRef.current = null;
        }, 500);
      }
    };

    return () => {
      ws.close();
      if (timerRef.current) clearTimeout(timerRef.current);
      flushBatch();
    };
  }, [wsUrl, flushBatch]);

  const markRead = useCallback((id) => dispatch({ type: 'MARK_READ', payload: id }), []);
  const markAllRead = useCallback(() => dispatch({ type: 'MARK_ALL_READ' }), []);

  return { ...state, markRead, markAllRead };
}

// NotificationBell component
function NotificationBell() {
  const { allIds, byId, unreadCount, markRead, markAllRead } =
    useNotifications('wss://api.example.com/notifications');
  const [open, setOpen] = useState(false);

  return (
    <div className="notification-bell">
      <button onClick={() => setOpen(!open)}>
        🔔 {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
      </button>

      {open && (
        <div className="dropdown">
          <div className="header">
            <span>Notifications</span>
            <button onClick={markAllRead}>Mark all read</button>
          </div>
          {allIds.map((id) => {
            const n = byId[id];
            return (
              <div
                key={id}
                className={`notification ${n.read ? '' : 'unread'}`}
                onClick={() => markRead(id)}
              >
                <strong>{n.title}</strong>
                <p>{n.body}</p>
                <time>{new Date(n.timestamp).toLocaleTimeString()}</time>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function showUrgentToast(notification) {
  // Integrate with your toast library (react-hot-toast, sonner, etc.)
  console.log('URGENT:', notification.title);
}
```

---

### Q8. How do you build a chat application with typing indicators using WebSockets in React?

**Answer:**

Typing indicators require a separate signaling channel alongside the message channel. The standard approach:

1. When the user starts typing, send a `typing_start` event.
2. Debounce so you don't flood the server with events on every keystroke.
3. Set a timeout — if the user stops typing for ~3 seconds, send `typing_stop`.
4. On the receiving end, show "User is typing…" and auto-clear it after a timeout (in case the `typing_stop` event is lost).
5. Use a `Set` or `Map` to track multiple users typing simultaneously.

```jsx
import { useEffect, useReducer, useCallback, useRef, useState } from 'react';

// Typing indicator hook
function useTypingIndicator(socket, roomId) {
  const [typingUsers, setTypingUsers] = useState(new Map());
  const typingTimersRef = useRef(new Map());
  const isTypingRef = useRef(false);
  const debounceTimerRef = useRef(null);

  // Listen for typing events from other users
  useEffect(() => {
    const handleTypingStart = ({ userId, userName }) => {
      setTypingUsers((prev) => new Map(prev).set(userId, userName));

      // Auto-clear after 4 seconds (safety net)
      if (typingTimersRef.current.has(userId)) {
        clearTimeout(typingTimersRef.current.get(userId));
      }
      typingTimersRef.current.set(
        userId,
        setTimeout(() => {
          setTypingUsers((prev) => {
            const next = new Map(prev);
            next.delete(userId);
            return next;
          });
        }, 4000)
      );
    };

    const handleTypingStop = ({ userId }) => {
      setTypingUsers((prev) => {
        const next = new Map(prev);
        next.delete(userId);
        return next;
      });
      if (typingTimersRef.current.has(userId)) {
        clearTimeout(typingTimersRef.current.get(userId));
      }
    };

    socket.on('typing_start', handleTypingStart);
    socket.on('typing_stop', handleTypingStop);

    return () => {
      socket.off('typing_start', handleTypingStart);
      socket.off('typing_stop', handleTypingStop);
      typingTimersRef.current.forEach(clearTimeout);
    };
  }, [socket]);

  // Emit typing events (debounced)
  const handleInputChange = useCallback(() => {
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      socket.emit('typing_start', { roomId });
    }

    // Reset the "stop typing" timer
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      isTypingRef.current = false;
      socket.emit('typing_stop', { roomId });
    }, 3000);
  }, [socket, roomId]);

  const stopTyping = useCallback(() => {
    if (isTypingRef.current) {
      isTypingRef.current = false;
      socket.emit('typing_stop', { roomId });
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    }
  }, [socket, roomId]);

  const typingLabel = formatTypingLabel([...typingUsers.values()]);

  return { typingUsers, typingLabel, handleInputChange, stopTyping };
}

function formatTypingLabel(names) {
  if (names.length === 0) return '';
  if (names.length === 1) return `${names[0]} is typing…`;
  if (names.length === 2) return `${names[0]} and ${names[1]} are typing…`;
  return `${names[0]} and ${names.length - 1} others are typing…`;
}

// Chat component with typing indicator
function ChatRoom({ socket, roomId, currentUser }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const { typingLabel, handleInputChange, stopTyping } =
    useTypingIndicator(socket, roomId);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    socket.on('message', (msg) => {
      setMessages((prev) => [...prev, msg]);
    });
    return () => socket.off('message');
  }, [socket]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    socket.emit('message', { roomId, text: input, author: currentUser });
    stopTyping();
    setInput('');
  };

  return (
    <div className="chat-room">
      <div className="messages">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message ${msg.author === currentUser ? 'own' : ''}`}
          >
            <strong>{msg.author}</strong>
            <p>{msg.text}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {typingLabel && (
        <div className="typing-indicator">
          <span className="dots">•••</span> {typingLabel}
        </div>
      )}

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            handleInputChange(); // signal typing
          }}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message…"
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  );
}
```

---

### Q9. How do you build a live activity feed (like GitHub's activity stream) with efficient rendering of high-frequency updates?

**Answer:**

A live activity feed has unique challenges:
1. **High throughput**: Hundreds of events per minute in a busy organization.
2. **Prepending**: New items go to the *top* of the list, which triggers a re-layout of the entire list.
3. **Infinite scroll**: Old items load on demand.
4. **Grouping**: Similar events should collapse ("User starred 5 repos" instead of 5 separate entries).
5. **Performance**: Rendering thousands of DOM nodes kills scroll performance.

The solution combines **virtualization** (only render visible items), **batching** (group incoming events), and **React 18's `startTransition`** to keep the UI responsive during bursts.

```jsx
import { useReducer, useEffect, useCallback, useRef, startTransition } from 'react';
import { FixedSizeList as List } from 'react-window';

function feedReducer(state, action) {
  switch (action.type) {
    case 'ADD_BATCH': {
      // Deduplicate by event id
      const existingIds = new Set(state.events.map((e) => e.id));
      const newEvents = action.payload.filter((e) => !existingIds.has(e.id));
      if (newEvents.length === 0) return state;
      return {
        ...state,
        events: [...newEvents.reverse(), ...state.events], // newest first
      };
    }
    case 'LOAD_OLDER':
      return {
        ...state,
        events: [...state.events, ...action.payload],
      };
    default:
      return state;
  }
}

function useLiveActivityFeed(wsUrl) {
  const [state, dispatch] = useReducer(feedReducer, { events: [] });
  const batchRef = useRef([]);
  const batchTimerRef = useRef(null);

  const flushBatch = useCallback(() => {
    if (batchRef.current.length > 0) {
      const batch = [...batchRef.current];
      batchRef.current = [];
      // Use startTransition so incoming events don't block user interactions
      startTransition(() => {
        dispatch({ type: 'ADD_BATCH', payload: batch });
      });
    }
    batchTimerRef.current = null;
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      batchRef.current.push(data);

      // Flush batch every 300ms
      if (!batchTimerRef.current) {
        batchTimerRef.current = setTimeout(flushBatch, 300);
      }
    };

    return () => {
      ws.close();
      if (batchTimerRef.current) clearTimeout(batchTimerRef.current);
    };
  }, [wsUrl, flushBatch]);

  return state;
}

// Activity Feed with virtualization
function ActivityFeed() {
  const { events } = useLiveActivityFeed('wss://api.example.com/activity');

  const Row = useCallback(
    ({ index, style }) => {
      const event = events[index];
      return (
        <div style={style} className="activity-row">
          <img src={event.actor.avatar} alt="" className="avatar" />
          <div className="content">
            <strong>{event.actor.name}</strong> {getActionText(event)}
            <span className="repo">{event.repo}</span>
            <time className="time">
              {formatRelativeTime(event.timestamp)}
            </time>
          </div>
        </div>
      );
    },
    [events]
  );

  return (
    <div className="activity-feed">
      <h2>Activity</h2>
      <List
        height={600}
        itemCount={events.length}
        itemSize={72}
        width="100%"
      >
        {Row}
      </List>
    </div>
  );
}

function getActionText(event) {
  const actions = {
    push: 'pushed to',
    pr_open: 'opened a pull request in',
    pr_merge: 'merged a pull request in',
    issue_open: 'opened an issue in',
    star: 'starred',
    fork: 'forked',
    comment: 'commented on',
  };
  return actions[event.type] || event.type;
}

function formatRelativeTime(timestamp) {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
```

---

### Q10. How do you manage WebSocket connection states (connected, reconnecting, offline) and reflect them in the UI?

**Answer:**

Connection state management is critical for user trust. Users must know whether they are seeing live data or stale data. A proper connection state system combines three signals:

1. **WebSocket readyState**: CONNECTING, OPEN, CLOSING, CLOSED.
2. **Browser online/offline events**: `navigator.onLine` and the `online`/`offline` events.
3. **Application-level heartbeat**: Detecting "zombie" connections where the TCP socket is open but the server has gone away.

The combination forms a state machine:

```
CONNECTING → CONNECTED → DISCONNECTED → RECONNECTING → CONNECTED
                                     ↓
                                  OFFLINE (browser offline)
                                     ↓
                              RECONNECTING (when back online)
```

```jsx
import { useEffect, useReducer, useCallback, useRef } from 'react';

const ConnectionState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  DISCONNECTED: 'disconnected',
  OFFLINE: 'offline',
};

function connectionReducer(state, action) {
  switch (action.type) {
    case 'WS_OPEN':
      return {
        ...state,
        status: ConnectionState.CONNECTED,
        lastConnected: Date.now(),
        retryCount: 0,
      };
    case 'WS_CLOSE':
      return {
        ...state,
        status: state.isOnline
          ? ConnectionState.RECONNECTING
          : ConnectionState.OFFLINE,
      };
    case 'RETRY':
      return {
        ...state,
        status: ConnectionState.RECONNECTING,
        retryCount: state.retryCount + 1,
      };
    case 'ONLINE':
      return { ...state, isOnline: true };
    case 'OFFLINE':
      return { ...state, isOnline: false, status: ConnectionState.OFFLINE };
    case 'GIVE_UP':
      return { ...state, status: ConnectionState.DISCONNECTED };
    default:
      return state;
  }
}

function useConnectionManager(url, { maxRetries = 10 } = {}) {
  const [state, dispatch] = useReducer(connectionReducer, {
    status: ConnectionState.CONNECTING,
    isOnline: navigator.onLine,
    lastConnected: null,
    retryCount: 0,
  });
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => dispatch({ type: 'WS_OPEN' });
    ws.onclose = () => dispatch({ type: 'WS_CLOSE' });
    ws.onerror = () => {}; // handled by onclose
  }, [url]);

  // Browser online/offline
  useEffect(() => {
    const goOnline = () => {
      dispatch({ type: 'ONLINE' });
      connect(); // try immediately when back online
    };
    const goOffline = () => dispatch({ type: 'OFFLINE' });

    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);

    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, [connect]);

  // Reconnection logic
  useEffect(() => {
    if (state.status !== ConnectionState.RECONNECTING) return;
    if (state.retryCount >= maxRetries) {
      dispatch({ type: 'GIVE_UP' });
      return;
    }

    const delay = Math.min(1000 * 2 ** state.retryCount, 30000);
    const timer = setTimeout(() => {
      dispatch({ type: 'RETRY' });
      connect();
    }, delay);

    return () => clearTimeout(timer);
  }, [state.status, state.retryCount, maxRetries, connect]);

  // Initial connect
  useEffect(() => {
    connect();
    return () => wsRef.current?.close(1000);
  }, [connect]);

  return { ...state, ws: wsRef };
}

// UI Component — Connection Status Banner
function ConnectionBanner({ status, lastConnected }) {
  if (status === ConnectionState.CONNECTED) return null;

  const config = {
    [ConnectionState.CONNECTING]: {
      bg: '#fef3c7', color: '#92400e', text: 'Connecting…',
    },
    [ConnectionState.RECONNECTING]: {
      bg: '#fef3c7', color: '#92400e',
      text: `Reconnecting… Last connected ${formatTime(lastConnected)}`,
    },
    [ConnectionState.OFFLINE]: {
      bg: '#fee2e2', color: '#991b1b', text: 'You are offline',
    },
    [ConnectionState.DISCONNECTED]: {
      bg: '#fee2e2', color: '#991b1b',
      text: 'Disconnected. Please refresh the page.',
    },
  };

  const c = config[status];

  return (
    <div style={{ background: c.bg, color: c.color, padding: '8px 16px', textAlign: 'center' }}>
      {c.text}
    </div>
  );
}

function formatTime(ts) {
  if (!ts) return 'never';
  return new Date(ts).toLocaleTimeString();
}
```

---

### Q11. How do you handle message ordering and deduplication in a real-time React application?

**Answer:**

Real-time systems suffer from two classic problems:

1. **Out-of-order delivery**: Network jitter, load-balancer retries, or server clustering can deliver messages in a different order than they were sent.
2. **Duplicate messages**: Network retries, WebSocket reconnections, and "at-least-once" delivery guarantees all produce duplicates.

**Solutions:**

- **Ordering**: Each message carries a monotonically increasing sequence number or a Lamport timestamp. The client maintains a buffer and only applies messages in order, holding back messages that arrive ahead of sequence.
- **Deduplication**: Each message carries a unique `messageId`. The client maintains a `Set` of recently seen IDs and silently drops duplicates.
- **Idempotent operations**: Design state transitions so that applying the same message twice produces the same result (e.g., "set X to 5" is idempotent; "increment X by 1" is not).

```jsx
import { useReducer, useCallback, useRef } from 'react';

function createOrderedMessageReducer(maxDedupeHistory = 5000) {
  return function reducer(state, action) {
    switch (action.type) {
      case 'RECEIVE': {
        const { message } = action.payload;

        // 1. Deduplication — skip if we've seen this messageId
        if (state.seenIds.has(message.id)) {
          return state;
        }

        // 2. Add to seen set (prune if too large)
        const seenIds = new Set(state.seenIds);
        seenIds.add(message.id);
        if (seenIds.size > maxDedupeHistory) {
          // Remove oldest entries (Set preserves insertion order)
          const iter = seenIds.values();
          for (let i = 0; i < 1000; i++) iter.next();
          // Rebuild — simpler approach:
          const arr = [...seenIds];
          const pruned = new Set(arr.slice(arr.length - maxDedupeHistory));
          return processMessage(
            { ...state, seenIds: pruned },
            message
          );
        }

        return processMessage({ ...state, seenIds }, message);
      }
      default:
        return state;
    }
  };
}

function processMessage(state, message) {
  const { seq } = message;
  const expectedSeq = state.nextExpectedSeq;

  // Message is the one we expected — apply it
  if (seq === expectedSeq) {
    let newState = applyMessage(state, message);
    newState = { ...newState, nextExpectedSeq: expectedSeq + 1 };

    // Check buffer for consecutive messages
    while (newState.buffer.has(newState.nextExpectedSeq)) {
      const buffered = newState.buffer.get(newState.nextExpectedSeq);
      const nextBuffer = new Map(newState.buffer);
      nextBuffer.delete(newState.nextExpectedSeq);
      newState = applyMessage(
        { ...newState, buffer: nextBuffer },
        buffered
      );
      newState = { ...newState, nextExpectedSeq: newState.nextExpectedSeq + 1 };
    }
    return newState;
  }

  // Message is ahead of expected — buffer it
  if (seq > expectedSeq) {
    const buffer = new Map(state.buffer);
    buffer.set(seq, message);
    return { ...state, buffer };
  }

  // Message is behind expected (already applied) — drop it
  return state;
}

function applyMessage(state, message) {
  return {
    ...state,
    messages: [...state.messages, message],
  };
}

// Usage in a component
function OrderedChat({ wsUrl }) {
  const orderedReducer = useRef(createOrderedMessageReducer()).current;
  const [state, dispatch] = useReducer(orderedReducer, {
    messages: [],
    seenIds: new Set(),
    buffer: new Map(),
    nextExpectedSeq: 0,
  });

  const handleMessage = useCallback((data) => {
    dispatch({ type: 'RECEIVE', payload: { message: data } });
  }, []);

  // ... WebSocket connection using handleMessage as onMessage callback

  return (
    <div>
      <div className="info">
        Buffered: {state.buffer.size} | Messages: {state.messages.length}
      </div>
      {state.messages.map((msg) => (
        <div key={msg.id}>
          <span>#{msg.seq}</span> {msg.text}
        </div>
      ))}
    </div>
  );
}
```

---

### Q12. How do you broadcast messages to specific rooms or channels using WebSockets in a React application?

**Answer:**

Room/channel-based broadcasting is a pattern where the server groups connections by topic and only sends messages to connections subscribed to that topic. On the client side, this involves:

1. **Subscribing** to rooms when a component mounts.
2. **Unsubscribing** when a component unmounts or when the user navigates away.
3. **Routing messages** — the client receives messages tagged with a channel and dispatches them to the correct handler.
4. **Dynamic subscriptions** — the user may join/leave rooms at runtime (e.g., switching Slack channels).

```jsx
import { createContext, useContext, useEffect, useCallback, useReducer, useRef } from 'react';

// Channel manager — a single WebSocket multiplexes many channels
function channelReducer(state, action) {
  switch (action.type) {
    case 'SUBSCRIBE': {
      const channels = { ...state.channels };
      if (!channels[action.channel]) {
        channels[action.channel] = { messages: [], listeners: new Set() };
      }
      channels[action.channel].listeners.add(action.listenerId);
      return { ...state, channels };
    }
    case 'UNSUBSCRIBE': {
      const channels = { ...state.channels };
      channels[action.channel]?.listeners.delete(action.listenerId);
      // If no more listeners, remove the channel
      if (channels[action.channel]?.listeners.size === 0) {
        delete channels[action.channel];
      }
      return { ...state, channels };
    }
    case 'MESSAGE': {
      const { channel, message } = action;
      if (!state.channels[channel]) return state;
      const channels = { ...state.channels };
      channels[channel] = {
        ...channels[channel],
        messages: [...channels[channel].messages, message],
      };
      return { ...state, channels };
    }
    default:
      return state;
  }
}

const ChannelContext = createContext(null);

function ChannelProvider({ wsUrl, children }) {
  const [state, dispatch] = useReducer(channelReducer, { channels: {} });
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const { channel, ...message } = JSON.parse(event.data);
      dispatch({ type: 'MESSAGE', channel, message });
    };

    return () => ws.close();
  }, [wsUrl]);

  const subscribe = useCallback((channel, listenerId) => {
    dispatch({ type: 'SUBSCRIBE', channel, listenerId });
    // Tell server to add this connection to the room
    wsRef.current?.send(
      JSON.stringify({ action: 'subscribe', channel })
    );
  }, []);

  const unsubscribe = useCallback((channel, listenerId) => {
    dispatch({ type: 'UNSUBSCRIBE', channel, listenerId });
    wsRef.current?.send(
      JSON.stringify({ action: 'unsubscribe', channel })
    );
  }, []);

  const sendToChannel = useCallback((channel, payload) => {
    wsRef.current?.send(
      JSON.stringify({ action: 'message', channel, ...payload })
    );
  }, []);

  return (
    <ChannelContext.Provider value={{ state, subscribe, unsubscribe, sendToChannel }}>
      {children}
    </ChannelContext.Provider>
  );
}

// Custom hook for consuming a specific channel
function useChannel(channelName) {
  const { state, subscribe, unsubscribe, sendToChannel } = useContext(ChannelContext);
  const listenerIdRef = useRef(crypto.randomUUID());

  useEffect(() => {
    const id = listenerIdRef.current;
    subscribe(channelName, id);
    return () => unsubscribe(channelName, id);
  }, [channelName, subscribe, unsubscribe]);

  const messages = state.channels[channelName]?.messages ?? [];
  const send = useCallback(
    (payload) => sendToChannel(channelName, payload),
    [channelName, sendToChannel]
  );

  return { messages, send };
}

// Usage — multiple channels in the same app
function TradingDashboard() {
  return (
    <ChannelProvider wsUrl="wss://api.example.com/ws">
      <StockTicker symbol="AAPL" />
      <StockTicker symbol="GOOGL" />
      <NewsFeed />
    </ChannelProvider>
  );
}

function StockTicker({ symbol }) {
  const { messages } = useChannel(`stock:${symbol}`);
  const latestPrice = messages.at(-1)?.price ?? '—';

  return (
    <div className="ticker">
      <h3>{symbol}</h3>
      <span className="price">${latestPrice}</span>
    </div>
  );
}

function NewsFeed() {
  const { messages } = useChannel('news:breaking');

  return (
    <div className="news">
      {messages.map((m, i) => (
        <article key={i}>
          <h4>{m.headline}</h4>
          <p>{m.summary}</p>
        </article>
      ))}
    </div>
  );
}
```

**Server-side pattern (Node.js):**

```jsx
// When a client subscribes to a channel
ws.on('message', (raw) => {
  const msg = JSON.parse(raw);
  if (msg.action === 'subscribe') {
    rooms.get(msg.channel)?.add(ws) ?? rooms.set(msg.channel, new Set([ws]));
  }
  if (msg.action === 'message') {
    // Broadcast to everyone in the room except the sender
    for (const client of rooms.get(msg.channel) ?? []) {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({ channel: msg.channel, ...msg }));
      }
    }
  }
});
```

---

## Advanced Level (Q13–Q20)

---

### Q13. How do you implement WebSocket authentication and security in a React application?

**Answer:**

WebSocket connections cannot use standard HTTP headers the way REST APIs do (the browser's `WebSocket` constructor doesn't allow custom headers). This creates a unique authentication challenge. There are three established patterns:

**Pattern 1: Token in the URL query string**
Simple but the token appears in server logs, proxy logs, and browser history.

**Pattern 2: Auth-on-connect message**
Open the socket, then send an auth message as the first frame. The server validates the token and either continues or force-closes the connection.

**Pattern 3: Ticket-based authentication (recommended for production)**
Make a REST call to get a short-lived, single-use "ticket" (an opaque token), then open the WebSocket with that ticket. The server validates the ticket, links the connection to the user session, and invalidates the ticket so it can't be reused.

```jsx
import { useEffect, useRef, useState, useCallback } from 'react';

// Pattern 3: Ticket-based authentication (most secure)
async function obtainWebSocketTicket() {
  const res = await fetch('/api/ws/ticket', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${getAccessToken()}`,
      'Content-Type': 'application/json',
    },
  });
  if (!res.ok) throw new Error('Failed to obtain WS ticket');
  const { ticket } = await res.json();
  return ticket; // Short-lived, single-use token
}

function useAuthenticatedWebSocket(baseUrl, options = {}) {
  const [status, setStatus] = useState('authenticating');
  const wsRef = useRef(null);

  const connect = useCallback(async () => {
    try {
      setStatus('authenticating');

      // Step 1: Get a single-use ticket via authenticated REST endpoint
      const ticket = await obtainWebSocketTicket();

      // Step 2: Open WebSocket with the ticket
      const ws = new WebSocket(`${baseUrl}?ticket=${ticket}`);
      wsRef.current = ws;

      ws.onopen = () => setStatus('connected');

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Handle server-initiated auth errors
        if (data.type === 'auth_error') {
          console.error('Auth error:', data.reason);
          ws.close(4001, 'Authentication failed');
          setStatus('auth_error');
          return;
        }

        // Handle token refresh signal
        if (data.type === 'token_expiring') {
          refreshTokenAndNotify(ws);
          return;
        }

        options.onMessage?.(data);
      };

      ws.onclose = (event) => {
        if (event.code === 4001) {
          // Auth failure — redirect to login
          setStatus('auth_error');
          window.location.href = '/login';
          return;
        }

        if (event.code === 4002) {
          // Token expired during connection — reconnect with new ticket
          setStatus('reconnecting');
          setTimeout(connect, 1000);
          return;
        }

        setStatus('disconnected');
      };
    } catch (err) {
      console.error('WebSocket auth failed:', err);
      setStatus('auth_error');
    }
  }, [baseUrl, options]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close(1000);
  }, [connect]);

  return { status, ws: wsRef };
}

// Server-side validation (Node.js)
/*
  const tickets = new Map(); // ticketId -> { userId, expiresAt }

  // REST endpoint to issue ticket
  app.post('/api/ws/ticket', authenticateJWT, (req, res) => {
    const ticket = crypto.randomUUID();
    tickets.set(ticket, {
      userId: req.user.id,
      expiresAt: Date.now() + 30_000, // 30 second expiry
    });
    res.json({ ticket });
  });

  // WebSocket server
  wss.on('connection', (ws, req) => {
    const url = new URL(req.url, 'http://localhost');
    const ticket = url.searchParams.get('ticket');
    const session = tickets.get(ticket);

    if (!session || session.expiresAt < Date.now()) {
      ws.close(4001, 'Invalid or expired ticket');
      return;
    }

    tickets.delete(ticket); // Single use — invalidate immediately
    ws.userId = session.userId;

    // Connection is now authenticated
  });
*/

// Additional security measures
function secureWebSocketConfig() {
  return {
    // Always use wss:// in production (TLS)
    url: process.env.NODE_ENV === 'production'
      ? 'wss://api.example.com/ws'
      : 'ws://localhost:3001/ws',

    // Rate limiting on the server side
    // Max messages per second per connection
    rateLimit: { maxMessages: 50, windowMs: 1000 },

    // Message size limit
    maxPayloadSize: 64 * 1024, // 64 KB

    // Origin validation (server-side)
    allowedOrigins: ['https://app.example.com'],

    // CSRF protection — validate Origin header on upgrade request
  };
}
```

**Key security considerations:**
- **Always use `wss://`** (WebSocket Secure) in production — encrypts traffic with TLS.
- **Validate the `Origin` header** on the server during the HTTP upgrade to prevent cross-site WebSocket hijacking (CSWSH).
- **Rate-limit messages** per connection to prevent DoS.
- **Validate and sanitize** all incoming messages — never trust client data.
- **Use short-lived tickets** instead of long-lived JWTs in URLs.

---

### Q14. How do you integrate real-time WebSocket data with TanStack Query (React Query) for cache invalidation and optimistic updates?

**Answer:**

TanStack Query excels at server-state management — caching, refetching, background updates, and optimistic mutations. Combining it with WebSockets gives you the best of both worlds: TanStack Query manages the cache and provides loading/error states, while WebSockets provide real-time push updates that invalidate or directly update the cache.

There are three integration strategies:

1. **Invalidation-based**: WebSocket events trigger `queryClient.invalidateQueries()`, causing a refetch. Simplest, but adds latency.
2. **Direct cache update**: WebSocket events call `queryClient.setQueryData()` to update the cache directly. No refetch, instant.
3. **Hybrid**: Use direct cache updates for simple changes and invalidation for complex ones.

```jsx
import { useEffect, useCallback } from 'react';
import {
  useQuery,
  useMutation,
  useQueryClient,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';

const queryClient = new QueryClient();

// Hook that connects WebSocket events to TanStack Query cache
function useRealtimeSync(socket) {
  const qc = useQueryClient();

  useEffect(() => {
    // Strategy 1: Direct cache update for granular changes
    socket.on('todo:created', (todo) => {
      qc.setQueryData(['todos'], (old = []) => [...old, todo]);
    });

    socket.on('todo:updated', (updated) => {
      qc.setQueryData(['todos'], (old = []) =>
        old.map((t) => (t.id === updated.id ? updated : t))
      );
      // Also update individual query
      qc.setQueryData(['todo', updated.id], updated);
    });

    socket.on('todo:deleted', ({ id }) => {
      qc.setQueryData(['todos'], (old = []) =>
        old.filter((t) => t.id !== id)
      );
      qc.removeQueries({ queryKey: ['todo', id] });
    });

    // Strategy 2: Invalidation for complex changes
    socket.on('todos:bulk-update', () => {
      qc.invalidateQueries({ queryKey: ['todos'] });
    });

    // Strategy 3: Presence/online data — set directly, no server fetch needed
    socket.on('user:presence', ({ userId, status }) => {
      qc.setQueryData(['presence', userId], { status, updatedAt: Date.now() });
    });

    return () => {
      socket.off('todo:created');
      socket.off('todo:updated');
      socket.off('todo:deleted');
      socket.off('todos:bulk-update');
      socket.off('user:presence');
    };
  }, [socket, qc]);
}

// Optimistic mutation with WebSocket confirmation
function useTodoMutations(socket) {
  const qc = useQueryClient();

  const addTodo = useMutation({
    mutationFn: (newTodo) =>
      fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTodo),
      }).then((r) => r.json()),

    // Optimistic update
    onMutate: async (newTodo) => {
      await qc.cancelQueries({ queryKey: ['todos'] });
      const previous = qc.getQueryData(['todos']);

      const optimisticTodo = {
        ...newTodo,
        id: `temp-${crypto.randomUUID()}`,
        createdAt: new Date().toISOString(),
        _optimistic: true,
      };

      qc.setQueryData(['todos'], (old = []) => [...old, optimisticTodo]);

      return { previous, optimisticTodo };
    },

    onError: (_err, _newTodo, context) => {
      // Rollback on error
      qc.setQueryData(['todos'], context.previous);
    },

    onSettled: () => {
      // The WebSocket 'todo:created' event will provide the
      // server-canonical data, but we invalidate as a safety net
      qc.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  const updateTodo = useMutation({
    mutationFn: ({ id, ...updates }) =>
      fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      }).then((r) => r.json()),

    onMutate: async ({ id, ...updates }) => {
      await qc.cancelQueries({ queryKey: ['todos'] });
      const previous = qc.getQueryData(['todos']);

      qc.setQueryData(['todos'], (old = []) =>
        old.map((t) => (t.id === id ? { ...t, ...updates, _optimistic: true } : t))
      );

      return { previous };
    },

    onError: (_err, _vars, context) => {
      qc.setQueryData(['todos'], context.previous);
    },
  });

  return { addTodo, updateTodo };
}

// Main app
function TodoApp({ socket }) {
  useRealtimeSync(socket);

  const { data: todos = [], isLoading } = useQuery({
    queryKey: ['todos'],
    queryFn: () => fetch('/api/todos').then((r) => r.json()),
    // Don't refetch too aggressively since WebSocket handles updates
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });

  const { addTodo, updateTodo } = useTodoMutations(socket);

  if (isLoading) return <div>Loading…</div>;

  return (
    <ul>
      {todos.map((todo) => (
        <li
          key={todo.id}
          style={{ opacity: todo._optimistic ? 0.6 : 1 }}
        >
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() =>
              updateTodo.mutate({ id: todo.id, completed: !todo.completed })
            }
          />
          {todo.text}
        </li>
      ))}
    </ul>
  );
}
```

---

### Q15. How do you implement collaborative editing with presence awareness (multiple cursors and live updates) in React?

**Answer:**

Collaborative editing is one of the hardest real-time problems. It requires:

1. **Operational Transformation (OT)** or **Conflict-free Replicated Data Types (CRDTs)** for merging concurrent edits without conflicts. Libraries like **Yjs** or **Automerge** handle this.
2. **Presence awareness**: Broadcasting each user's cursor position, selection, and name/avatar to all other users.
3. **Low-latency state sync**: Every keystroke must be propagated with minimal delay.
4. **Undo/redo**: Each user has their own undo stack that doesn't undo other users' changes.

In practice, you use a library like **Yjs** with a WebSocket provider like **y-websocket** and build React bindings around it.

```jsx
import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';

// Awareness states for presence
const COLORS = [
  '#ef4444', '#f59e0b', '#10b981', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316',
];

function useCollaborativeDocument(roomId, user) {
  const ydocRef = useRef(null);
  const providerRef = useRef(null);
  const [text, setText] = useState('');
  const [peers, setPeers] = useState([]);
  const [synced, setSynced] = useState(false);

  useEffect(() => {
    const ydoc = new Y.Doc();
    ydocRef.current = ydoc;

    const provider = new WebsocketProvider(
      'wss://collab.example.com',
      roomId,
      ydoc
    );
    providerRef.current = provider;

    // Set local user awareness
    const color = COLORS[Math.abs(hashString(user.id)) % COLORS.length];
    provider.awareness.setLocalStateField('user', {
      name: user.name,
      color,
      cursor: null,
    });

    // Listen for document changes
    const ytext = ydoc.getText('content');
    const observer = () => setText(ytext.toString());
    ytext.observe(observer);

    // Listen for awareness (presence) changes
    const awarenessHandler = () => {
      const states = [];
      provider.awareness.getStates().forEach((state, clientId) => {
        if (clientId !== ydoc.clientID && state.user) {
          states.push({ clientId, ...state.user });
        }
      });
      setPeers(states);
    };
    provider.awareness.on('change', awarenessHandler);

    provider.on('sync', (isSynced) => setSynced(isSynced));

    return () => {
      ytext.unobserve(observer);
      provider.awareness.off('change', awarenessHandler);
      provider.disconnect();
      ydoc.destroy();
    };
  }, [roomId, user]);

  const updateText = useCallback((newText, cursorPosition) => {
    const ydoc = ydocRef.current;
    const ytext = ydoc.getText('content');

    ydoc.transact(() => {
      ytext.delete(0, ytext.length);
      ytext.insert(0, newText);
    });

    // Update cursor in awareness
    providerRef.current?.awareness.setLocalStateField('user', {
      name: user.name,
      color: COLORS[Math.abs(hashString(user.id)) % COLORS.length],
      cursor: cursorPosition,
    });
  }, [user]);

  const updateCursor = useCallback((position) => {
    const provider = providerRef.current;
    const currentState = provider?.awareness.getLocalState()?.user;
    if (currentState) {
      provider.awareness.setLocalStateField('user', {
        ...currentState,
        cursor: position,
      });
    }
  }, []);

  return { text, peers, synced, updateText, updateCursor };
}

// Collaborative Editor Component
function CollaborativeEditor({ roomId, user }) {
  const { text, peers, synced, updateText, updateCursor } =
    useCollaborativeDocument(roomId, user);
  const editorRef = useRef(null);

  const handleChange = (e) => {
    const cursorPos = e.target.selectionStart;
    updateText(e.target.value, cursorPos);
  };

  const handleSelect = (e) => {
    updateCursor({
      start: e.target.selectionStart,
      end: e.target.selectionEnd,
    });
  };

  return (
    <div className="collaborative-editor">
      {/* Presence bar */}
      <div className="presence-bar">
        <span className="sync-status">
          {synced ? '✓ Synced' : '⟳ Syncing…'}
        </span>
        <div className="avatars">
          {peers.map((peer) => (
            <div
              key={peer.clientId}
              className="avatar"
              style={{ borderColor: peer.color }}
              title={peer.name}
            >
              {peer.name.charAt(0)}
            </div>
          ))}
        </div>
      </div>

      {/* Editor with remote cursors */}
      <div className="editor-container">
        <textarea
          ref={editorRef}
          value={text}
          onChange={handleChange}
          onSelect={handleSelect}
          onKeyUp={handleSelect}
          onClick={handleSelect}
          className="editor"
          spellCheck={false}
        />

        {/* Remote cursor overlays */}
        {peers
          .filter((p) => p.cursor !== null)
          .map((peer) => (
            <RemoteCursor
              key={peer.clientId}
              name={peer.name}
              color={peer.color}
              position={peer.cursor}
              editorRef={editorRef}
            />
          ))}
      </div>
    </div>
  );
}

function RemoteCursor({ name, color, position, editorRef }) {
  // Calculate pixel position from character offset
  // (simplified — production would use a canvas measurement approach)
  const style = useMemo(() => {
    if (!position || !editorRef.current) return { display: 'none' };
    const charWidth = 8.4; // monospace approximation
    const lineHeight = 20;
    const cols = editorRef.current.cols || 80;
    const row = Math.floor(position.start / cols);
    const col = position.start % cols;

    return {
      position: 'absolute',
      left: `${col * charWidth}px`,
      top: `${row * lineHeight}px`,
      borderLeft: `2px solid ${color}`,
      height: `${lineHeight}px`,
      pointerEvents: 'none',
    };
  }, [position, color, editorRef]);

  return (
    <div style={style}>
      <span
        style={{
          background: color,
          color: 'white',
          fontSize: '10px',
          padding: '1px 4px',
          borderRadius: '2px',
          position: 'absolute',
          top: '-16px',
          whiteSpace: 'nowrap',
        }}
      >
        {name}
      </span>
    </div>
  );
}

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}
```

---

### Q16. How do you build a live dashboard with streaming data, graceful degradation, and efficient rendering in React 18?

**Answer:**

Live dashboards (e.g., Datadog, Grafana, real-time analytics) push high-frequency data to the browser — often hundreds of data points per second. The challenge is rendering this data without dropping frames. Key techniques:

1. **Data windowing**: Only keep the last N data points in state (e.g., 5-minute rolling window).
2. **Frame-rate throttling**: Use `requestAnimationFrame` to batch DOM updates to 60fps, not per-message.
3. **Canvas rendering**: For charts with thousands of points, use Canvas or WebGL (via libraries like `react-chartjs-2`, `recharts`, or `visx`) instead of SVG.
4. **`startTransition`**: Mark chart re-renders as transitions so the connection status bar and controls remain responsive.
5. **Web Workers**: Parse and aggregate data off the main thread.
6. **Graceful degradation**: If the connection drops, show the last known data with a "stale data" warning instead of a blank screen.

```jsx
import {
  useEffect, useReducer, useCallback, useRef,
  startTransition, useMemo,
} from 'react';

// Data windowing reducer — keeps only the last windowSize points
function timeseriesReducer(state, action) {
  switch (action.type) {
    case 'APPEND': {
      const { seriesId, points, windowSize = 300 } = action.payload;
      const existing = state[seriesId] || [];
      const merged = [...existing, ...points];
      // Trim to window
      const trimmed =
        merged.length > windowSize
          ? merged.slice(merged.length - windowSize)
          : merged;
      return { ...state, [seriesId]: trimmed };
    }
    case 'CLEAR':
      return {};
    default:
      return state;
  }
}

function useDashboardStream(wsUrl, metrics) {
  const [series, dispatch] = useReducer(timeseriesReducer, {});
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [lastUpdate, setLastUpdate] = useState(null);
  const bufferRef = useRef(new Map()); // buffer per series
  const rafRef = useRef(null);

  // Flush buffered data at screen refresh rate (60fps)
  const flushBuffer = useCallback(() => {
    bufferRef.current.forEach((points, seriesId) => {
      if (points.length > 0) {
        // Use startTransition so chart re-renders don't block UI
        startTransition(() => {
          dispatch({
            type: 'APPEND',
            payload: { seriesId, points: [...points] },
          });
        });
      }
    });
    bufferRef.current.clear();
    setLastUpdate(Date.now());
    rafRef.current = requestAnimationFrame(flushBuffer);
  }, []);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus('connected');
      // Subscribe to desired metrics
      ws.send(JSON.stringify({ action: 'subscribe', metrics }));
      // Start the render loop
      rafRef.current = requestAnimationFrame(flushBuffer);
    };

    ws.onmessage = (event) => {
      const { series: seriesId, value, timestamp } = JSON.parse(event.data);
      // Buffer instead of dispatching immediately
      if (!bufferRef.current.has(seriesId)) {
        bufferRef.current.set(seriesId, []);
      }
      bufferRef.current.get(seriesId).push({ value, timestamp });
    };

    ws.onclose = () => setConnectionStatus('disconnected');

    return () => {
      ws.close();
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [wsUrl, metrics, flushBuffer]);

  return { series, connectionStatus, lastUpdate };
}

// Dashboard Component
function LiveDashboard() {
  const metrics = useMemo(() => ['cpu', 'memory', 'requests', 'latency'], []);
  const { series, connectionStatus, lastUpdate } = useDashboardStream(
    'wss://api.example.com/metrics',
    metrics
  );

  return (
    <div className="dashboard">
      {/* Connection status */}
      <header className="dashboard-header">
        <h1>Live Metrics</h1>
        <div className="status-group">
          <span className={`dot dot--${connectionStatus}`} />
          <span>{connectionStatus}</span>
          {lastUpdate && (
            <span className="last-update">
              Updated: {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {/* Stale data warning */}
      {connectionStatus !== 'connected' && lastUpdate && (
        <div className="stale-banner">
          Showing data from {new Date(lastUpdate).toLocaleTimeString()}.
          Live updates paused.
        </div>
      )}

      {/* Metric panels */}
      <div className="grid">
        {metrics.map((metric) => (
          <MetricPanel
            key={metric}
            title={metric.toUpperCase()}
            data={series[metric] || []}
          />
        ))}
      </div>
    </div>
  );
}

function MetricPanel({ title, data }) {
  const latest = data.at(-1);
  const sparklinePoints = useMemo(() => {
    if (data.length < 2) return '';
    const max = Math.max(...data.map((d) => d.value));
    const min = Math.min(...data.map((d) => d.value));
    const range = max - min || 1;
    const width = 200;
    const height = 50;

    return data
      .map((d, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((d.value - min) / range) * height;
        return `${i === 0 ? 'M' : 'L'}${x},${y}`;
      })
      .join(' ');
  }, [data]);

  return (
    <div className="metric-panel">
      <h3>{title}</h3>
      <div className="current-value">{latest?.value?.toFixed(2) ?? '—'}</div>
      <svg viewBox="0 0 200 50" className="sparkline">
        <path d={sparklinePoints} fill="none" stroke="#3b82f6" strokeWidth="1.5" />
      </svg>
    </div>
  );
}
```

---

### Q17. What are effective strategies for testing WebSocket-based React components?

**Answer:**

Testing real-time components is challenging because WebSockets are stateful, bidirectional, and asynchronous. A comprehensive test strategy has three layers:

1. **Unit tests**: Mock the WebSocket and test the component's reaction to messages.
2. **Integration tests**: Use a fake WebSocket server (like `mock-socket`) to test the full connection lifecycle.
3. **E2E tests**: Use a real server (or a lightweight test server) and test from the browser.

**Key principle**: Your custom hooks (like `useWebSocket`) should accept a WebSocket-like interface so you can inject mocks.

```jsx
// ---- Test Setup: Mock WebSocket ----
// __mocks__/MockWebSocket.js
export class MockWebSocket {
  static instances = [];

  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this._listeners = { open: [], message: [], close: [], error: [] };
    MockWebSocket.instances.push(this);

    // Simulate async connection
    setTimeout(() => this.simulateOpen(), 0);
  }

  addEventListener(type, handler) {
    this._listeners[type]?.push(handler);
  }

  set onopen(fn) { this._listeners.open = fn ? [fn] : []; }
  set onmessage(fn) { this._listeners.message = fn ? [fn] : []; }
  set onclose(fn) { this._listeners.close = fn ? [fn] : []; }
  set onerror(fn) { this._listeners.error = fn ? [fn] : []; }

  send(data) {
    this._lastSent = data;
    this._sentMessages = [...(this._sentMessages || []), data];
  }

  close(code = 1000, reason = '') {
    this.readyState = WebSocket.CLOSED;
    this._emit('close', { code, reason });
  }

  // Test helpers
  simulateOpen() {
    this.readyState = WebSocket.OPEN;
    this._emit('open', {});
  }

  simulateMessage(data) {
    this._emit('message', {
      data: typeof data === 'string' ? data : JSON.stringify(data),
    });
  }

  simulateClose(code = 1000) {
    this.readyState = WebSocket.CLOSED;
    this._emit('close', { code, reason: '' });
  }

  simulateError() {
    this._emit('error', new Event('error'));
  }

  _emit(type, event) {
    this._listeners[type]?.forEach((fn) => fn(event));
  }
}

// ---- Unit Test: Testing a chat component ----
import { render, screen, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MockWebSocket } from './__mocks__/MockWebSocket';
import { ChatRoom } from './ChatRoom';

// Replace global WebSocket with mock
beforeEach(() => {
  MockWebSocket.instances = [];
  global.WebSocket = MockWebSocket;
});

afterEach(() => {
  global.WebSocket = WebSocket; // restore
});

test('displays incoming messages', async () => {
  render(<ChatRoom url="ws://test/chat" />);

  // Wait for WebSocket to connect
  await waitFor(() => {
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  const ws = MockWebSocket.instances[0];

  // Simulate server sending a message
  act(() => {
    ws.simulateMessage({
      id: '1',
      author: 'Alice',
      text: 'Hello world',
      timestamp: Date.now(),
    });
  });

  expect(screen.getByText('Hello world')).toBeInTheDocument();
  expect(screen.getByText('Alice')).toBeInTheDocument();
});

test('sends message when user types and submits', async () => {
  const user = userEvent.setup();
  render(<ChatRoom url="ws://test/chat" />);

  await waitFor(() => {
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  const ws = MockWebSocket.instances[0];
  act(() => ws.simulateOpen());

  const input = screen.getByPlaceholderText('Type a message…');
  await user.type(input, 'Hi there!');
  await user.keyboard('{Enter}');

  const sent = JSON.parse(ws._sentMessages[0]);
  expect(sent.text).toBe('Hi there!');
});

test('handles reconnection on unexpected close', async () => {
  jest.useFakeTimers();
  render(<ChatRoom url="ws://test/chat" />);

  await waitFor(() => expect(MockWebSocket.instances).toHaveLength(1));

  const ws = MockWebSocket.instances[0];
  act(() => ws.simulateOpen());

  // Simulate unexpected close
  act(() => ws.simulateClose(1006));

  expect(screen.getByText(/reconnecting/i)).toBeInTheDocument();

  // Advance timer past reconnection delay
  act(() => jest.advanceTimersByTime(2000));

  // A new WebSocket instance should be created
  expect(MockWebSocket.instances).toHaveLength(2);

  jest.useRealTimers();
});

test('cleans up WebSocket on unmount', () => {
  const { unmount } = render(<ChatRoom url="ws://test/chat" />);

  const ws = MockWebSocket.instances[0];
  const closeSpy = jest.spyOn(ws, 'close');

  unmount();

  expect(closeSpy).toHaveBeenCalledWith(1000, expect.any(String));
});

// ---- Integration Test with mock-socket ----
/*
import { Server } from 'mock-socket';

let mockServer;

beforeEach(() => {
  mockServer = new Server('ws://test/chat');
});

afterEach(() => {
  mockServer.close();
});

test('full round-trip with mock server', async () => {
  mockServer.on('connection', (socket) => {
    socket.on('message', (data) => {
      const msg = JSON.parse(data);
      // Echo back with server-generated id
      socket.send(JSON.stringify({
        ...msg,
        id: 'server-1',
        type: 'confirm',
      }));
    });
  });

  render(<ChatRoom url="ws://test/chat" />);

  // ... interact and assert
});
*/
```

---

### Q18. How do you scale WebSockets in production using Redis Pub/Sub for multi-server architectures?

**Answer:**

A single WebSocket server can handle ~50K–100K concurrent connections (depending on hardware and message rate). Beyond that, or for high availability, you need **horizontal scaling** — multiple WebSocket server instances behind a load balancer. The problem: when User A is connected to Server 1 and User B is connected to Server 2, Server 1 doesn't know about Server 2's connections. You need a **message broker** to relay messages between servers.

**Redis Pub/Sub** is the most common solution:
1. When a server receives a message for a room, it publishes to a Redis channel.
2. All servers subscribe to the same Redis channels.
3. Each server then broadcasts to its local connected clients.

For production, consider **Redis Streams** (persistent, replayable) over plain Pub/Sub (fire-and-forget).

```jsx
// ---- Server-side: Node.js with ws + Redis ----
// server.js
import { WebSocketServer } from 'ws';
import Redis from 'ioredis';
import http from 'http';

const server = http.createServer();
const wss = new WebSocketServer({ server });

// Two Redis clients: one for pub, one for sub (required by Redis)
const redisPub = new Redis(process.env.REDIS_URL);
const redisSub = new Redis(process.env.REDIS_URL);

// Local room registry: roomId -> Set<ws>
const rooms = new Map();

// Subscribe to Redis channels for messages from other servers
redisSub.on('message', (channel, rawMessage) => {
  const { roomId, message, originServer } = JSON.parse(rawMessage);

  // Don't re-broadcast messages from our own server (avoid loops)
  if (originServer === process.env.SERVER_ID) return;

  broadcastToLocalRoom(roomId, message);
});

function broadcastToLocalRoom(roomId, message) {
  const clients = rooms.get(roomId);
  if (!clients) return;

  const data = JSON.stringify(message);
  for (const client of clients) {
    if (client.readyState === 1) { // WebSocket.OPEN
      client.send(data);
    }
  }
}

wss.on('connection', (ws) => {
  ws.rooms = new Set();

  ws.on('message', (raw) => {
    const msg = JSON.parse(raw);

    switch (msg.action) {
      case 'join': {
        const { roomId } = msg;
        ws.rooms.add(roomId);

        if (!rooms.has(roomId)) {
          rooms.set(roomId, new Set());
          // Subscribe to Redis channel for this room
          redisSub.subscribe(`room:${roomId}`);
        }
        rooms.get(roomId).add(ws);
        break;
      }

      case 'leave': {
        const { roomId } = msg;
        ws.rooms.delete(roomId);
        rooms.get(roomId)?.delete(ws);

        if (rooms.get(roomId)?.size === 0) {
          rooms.delete(roomId);
          redisSub.unsubscribe(`room:${roomId}`);
        }
        break;
      }

      case 'message': {
        const { roomId, ...payload } = msg;

        // Broadcast to local clients
        broadcastToLocalRoom(roomId, payload);

        // Publish to Redis so other servers get it
        redisPub.publish(
          `room:${roomId}`,
          JSON.stringify({
            roomId,
            message: payload,
            originServer: process.env.SERVER_ID,
          })
        );
        break;
      }
    }
  });

  ws.on('close', () => {
    // Clean up rooms
    for (const roomId of ws.rooms) {
      rooms.get(roomId)?.delete(ws);
      if (rooms.get(roomId)?.size === 0) {
        rooms.delete(roomId);
        redisSub.unsubscribe(`room:${roomId}`);
      }
    }
  });
});

server.listen(process.env.PORT || 3001);

// ---- Client-side React hook (unchanged from single-server) ----
// The beauty of this architecture: the client code doesn't change at all.
// The client connects to a load balancer which routes to any server instance.

function useScaledChat(roomId) {
  const [messages, setMessages] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    // Load balancer (e.g., Nginx, AWS ALB with sticky sessions) routes this
    const ws = new WebSocket('wss://ws.example.com');
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: 'join', roomId }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };

    return () => {
      ws.send(JSON.stringify({ action: 'leave', roomId }));
      ws.close();
    };
  }, [roomId]);

  const send = useCallback(
    (text) => {
      wsRef.current?.send(
        JSON.stringify({ action: 'message', roomId, text })
      );
    },
    [roomId]
  );

  return { messages, send };
}
```

**Production considerations:**

| Concern | Solution |
|---|---|
| Load balancing | Use sticky sessions (cookie/IP hash) so reconnections hit the same server, or use Redis for full statelessness |
| Connection draining | During deploys, stop accepting new connections, let existing ones finish, then shut down |
| Redis failure | Use Redis Sentinel or Redis Cluster for HA; have a fallback mode (local-only broadcast with degraded experience) |
| Message persistence | Use Redis Streams instead of Pub/Sub if you need message history/replay |
| Monitoring | Track connections per server, message rates, Redis lag, memory usage |

---

### Q19. How does React 19's `useOptimistic` hook work, and how does it improve real-time UX compared to manual optimistic patterns?

**Answer:**

React 19 introduces `useOptimistic`, a first-class hook for optimistic UI updates that integrates directly with React's rendering model and Server Actions. It provides a cleaner API than the manual `useReducer`-based pattern from Q5.

**How `useOptimistic` works:**

```
const [optimisticState, addOptimistic] = useOptimistic(actualState, updateFn);
```

- `actualState`: The "source of truth" state (e.g., from a query or parent).
- `updateFn`: `(currentState, optimisticValue) => newState` — a pure function that produces the optimistic version.
- `optimisticState`: What the component renders — includes pending optimistic values.
- `addOptimistic`: Adds an optimistic value. It's automatically reverted when the async action resolves.

The key insight: **React automatically reverts optimistic state** when the parent form's action completes (succeeds or fails). You don't need to manually manage rollback.

```jsx
import { useOptimistic, useState, useTransition } from 'react';

// Example 1: Basic optimistic likes
function LikeButton({ postId, initialLikes, isLiked: serverIsLiked }) {
  const [isLiked, setIsLiked] = useState(serverIsLiked);
  const [likes, setLikes] = useState(initialLikes);
  const [isPending, startTransition] = useTransition();

  const [optimisticLikes, addOptimisticLike] = useOptimistic(
    { count: likes, liked: isLiked },
    (current, action) => ({
      count: action === 'like' ? current.count + 1 : current.count - 1,
      liked: action === 'like',
    })
  );

  const toggleLike = () => {
    const action = optimisticLikes.liked ? 'unlike' : 'like';
    addOptimisticLike(action);

    startTransition(async () => {
      try {
        const res = await fetch(`/api/posts/${postId}/like`, {
          method: action === 'like' ? 'POST' : 'DELETE',
        });
        const data = await res.json();
        setLikes(data.likes);
        setIsLiked(data.isLiked);
      } catch {
        // useOptimistic auto-reverts on error — no manual rollback needed
        console.error('Like failed');
      }
    });
  };

  return (
    <button
      onClick={toggleLike}
      style={{ opacity: isPending ? 0.7 : 1 }}
    >
      {optimisticLikes.liked ? '❤️' : '🤍'} {optimisticLikes.count}
    </button>
  );
}

// Example 2: Optimistic message sending in a real-time chat
function RealtimeChat({ socket, roomId }) {
  const [confirmedMessages, setConfirmedMessages] = useState([]);
  const [isPending, startTransition] = useTransition();

  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    confirmedMessages,
    (currentMessages, newMessage) => [
      ...currentMessages,
      { ...newMessage, sending: true },
    ]
  );

  // Receive confirmed messages from WebSocket
  useEffect(() => {
    socket.on('message', (msg) => {
      setConfirmedMessages((prev) => {
        // Replace optimistic version with confirmed
        const exists = prev.some((m) => m.clientId === msg.clientId);
        if (exists) {
          return prev.map((m) =>
            m.clientId === msg.clientId ? { ...msg, sending: false } : m
          );
        }
        return [...prev, { ...msg, sending: false }];
      });
    });

    return () => socket.off('message');
  }, [socket]);

  const sendMessage = (text) => {
    const clientId = crypto.randomUUID();
    const newMessage = {
      clientId,
      text,
      author: 'me',
      timestamp: Date.now(),
    };

    // Optimistically add the message
    addOptimisticMessage(newMessage);

    startTransition(async () => {
      // Send via REST (or WebSocket) — the async boundary
      const res = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newMessage, roomId }),
      });

      if (res.ok) {
        const confirmed = await res.json();
        setConfirmedMessages((prev) => [...prev, { ...confirmed, sending: false }]);
      }
      // On failure, useOptimistic automatically reverts
    });
  };

  return (
    <div>
      {optimisticMessages.map((msg) => (
        <div
          key={msg.clientId}
          style={{ opacity: msg.sending ? 0.5 : 1 }}
        >
          <strong>{msg.author}</strong>: {msg.text}
          {msg.sending && <span> (sending…)</span>}
        </div>
      ))}
      <MessageInput onSend={sendMessage} />
    </div>
  );
}

function MessageInput({ onSend }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type a message…"
      />
      <button type="submit">Send</button>
    </form>
  );
}
```

**Comparison: `useOptimistic` vs manual pattern:**

| Aspect | Manual (`useReducer`) | `useOptimistic` |
|---|---|---|
| Rollback | Must implement `ROLLBACK` action | Automatic on async completion/error |
| Boilerplate | High (action types, dispatch) | Low (one hook call) |
| Integration | Works anywhere | Designed for `startTransition` and Server Actions |
| Multiple pending | Must track each with IDs | Composes naturally (multiple `addOptimistic` calls stack) |
| Server-side rendering | Manual | First-class with Server Actions |

---

### Q20. Design a production real-time collaboration platform architecture in React — covering state sync, presence, conflict resolution, offline support, and scaling.

**Answer:**

This question asks you to synthesize everything into a cohesive architecture. Let's design a system like **Notion** or **Linear** — a real-time collaborative workspace where multiple users can edit documents, see each other's presence, and work offline.

**Architecture layers:**

```
┌──────────────────────────────────────────────────┐
│                  React Client                     │
│  ┌────────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ CRDT Layer │ │ Presence │ │ Offline Queue  │  │
│  │   (Yjs)    │ │ (Aware.) │ │ (IndexedDB)    │  │
│  └─────┬──────┘ └────┬─────┘ └───────┬────────┘  │
│        │              │               │           │
│  ┌─────▼──────────────▼───────────────▼────────┐  │
│  │           WebSocket Transport Layer          │  │
│  │    (reconnection, auth, message routing)     │  │
│  └─────────────────────┬───────────────────────┘  │
└────────────────────────┼──────────────────────────┘
                         │ wss://
┌────────────────────────▼──────────────────────────┐
│              Load Balancer (sticky)                │
└────┬──────────────┬───────────────┬───────────────┘
     │              │               │
┌────▼────┐   ┌────▼────┐   ┌─────▼────┐
│  WS #1  │   │  WS #2  │   │  WS #3   │
│ Server  │   │ Server  │   │  Server   │
└────┬────┘   └────┬────┘   └────┬─────┘
     │              │              │
┌────▼──────────────▼──────────────▼────┐
│           Redis Cluster               │
│  (Pub/Sub + Streams + Presence)       │
└───────────────────┬───────────────────┘
                    │
┌───────────────────▼───────────────────┐
│          PostgreSQL + S3              │
│   (document storage, snapshots)       │
└───────────────────────────────────────┘
```

**Full implementation:**

```jsx
// ---- 1. Core Platform Provider ----
import { createContext, useContext, useEffect, useReducer, useRef } from 'react';
import * as Y from 'yjs';
import { IndexeddbPersistence } from 'y-indexeddb';

const PlatformContext = createContext(null);

function CollaborationPlatform({ children, user }) {
  const [state, dispatch] = useReducer(platformReducer, {
    connection: 'connecting',
    syncStatus: 'syncing',
    onlineUsers: [],
    offlineChanges: 0,
  });

  const wsRef = useRef(null);
  const docsRef = useRef(new Map()); // docId -> Y.Doc

  // Centralized WebSocket with multiplexed channels
  useEffect(() => {
    const ws = createResilentWebSocket('wss://collab.example.com/ws', {
      auth: { token: user.token },
      onStatusChange: (status) =>
        dispatch({ type: 'CONNECTION_STATUS', payload: status }),
    });
    wsRef.current = ws;

    ws.on('doc:update', ({ docId, update }) => {
      const doc = docsRef.current.get(docId);
      if (doc) {
        Y.applyUpdate(doc, new Uint8Array(update));
      }
    });

    ws.on('presence:update', ({ users }) => {
      dispatch({ type: 'PRESENCE_UPDATE', payload: users });
    });

    return () => ws.destroy();
  }, [user.token]);

  // Document manager
  const openDocument = (docId) => {
    if (docsRef.current.has(docId)) return docsRef.current.get(docId);

    const doc = new Y.Doc();

    // Offline persistence via IndexedDB
    const persistence = new IndexeddbPersistence(docId, doc);
    persistence.on('synced', () => {
      dispatch({ type: 'LOCAL_SYNC_COMPLETE', payload: docId });
    });

    // Sync outgoing changes to server
    doc.on('update', (update, origin) => {
      if (origin !== 'remote') {
        const binaryUpdate = Array.from(update);
        if (wsRef.current?.isConnected) {
          wsRef.current.send('doc:update', { docId, update: binaryUpdate });
        } else {
          // Queue for later
          dispatch({ type: 'OFFLINE_CHANGE' });
          queueOfflineUpdate(docId, binaryUpdate);
        }
      }
    });

    // Request full document state from server
    wsRef.current?.send('doc:open', { docId });

    docsRef.current.set(docId, doc);
    return doc;
  };

  const closeDocument = (docId) => {
    const doc = docsRef.current.get(docId);
    if (doc) {
      wsRef.current?.send('doc:close', { docId });
      doc.destroy();
      docsRef.current.delete(docId);
    }
  };

  return (
    <PlatformContext.Provider
      value={{
        state,
        user,
        openDocument,
        closeDocument,
        ws: wsRef,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

function platformReducer(state, action) {
  switch (action.type) {
    case 'CONNECTION_STATUS':
      return { ...state, connection: action.payload };
    case 'PRESENCE_UPDATE':
      return { ...state, onlineUsers: action.payload };
    case 'OFFLINE_CHANGE':
      return { ...state, offlineChanges: state.offlineChanges + 1 };
    case 'OFFLINE_FLUSH':
      return { ...state, offlineChanges: 0 };
    case 'LOCAL_SYNC_COMPLETE':
      return { ...state, syncStatus: 'synced' };
    default:
      return state;
  }
}

// ---- 2. Resilient WebSocket with offline queue ----
function createResilentWebSocket(url, { auth, onStatusChange }) {
  let ws = null;
  let retries = 0;
  let destroyed = false;
  const listeners = new Map();
  const offlineQueue = [];

  function connect() {
    if (destroyed) return;
    onStatusChange('connecting');

    ws = new WebSocket(`${url}?token=${auth.token}`);

    ws.onopen = () => {
      retries = 0;
      onStatusChange('connected');
      // Flush offline queue
      while (offlineQueue.length > 0) {
        const msg = offlineQueue.shift();
        ws.send(msg);
      }
    };

    ws.onmessage = (event) => {
      const { type, ...payload } = JSON.parse(event.data);
      const handlers = listeners.get(type) || [];
      handlers.forEach((fn) => fn(payload));
    };

    ws.onclose = (event) => {
      if (destroyed) return;
      if (event.code === 4001) {
        onStatusChange('auth_error');
        return;
      }
      onStatusChange('reconnecting');
      const delay = Math.min(1000 * 2 ** retries, 30000);
      retries++;
      setTimeout(connect, delay);
    };
  }

  connect();

  return {
    get isConnected() {
      return ws?.readyState === WebSocket.OPEN;
    },
    on(type, handler) {
      if (!listeners.has(type)) listeners.set(type, []);
      listeners.get(type).push(handler);
    },
    off(type, handler) {
      const handlers = listeners.get(type) || [];
      listeners.set(type, handlers.filter((h) => h !== handler));
    },
    send(type, payload) {
      const msg = JSON.stringify({ type, ...payload });
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(msg);
      } else {
        offlineQueue.push(msg);
      }
    },
    destroy() {
      destroyed = true;
      ws?.close(1000);
    },
  };
}

// ---- 3. Document Editor with CRDT + Presence ----
function DocumentEditor({ docId }) {
  const { openDocument, closeDocument, ws, state } = useContext(PlatformContext);
  const [content, setContent] = useState('');
  const [cursors, setCursors] = useState([]);
  const docRef = useRef(null);

  useEffect(() => {
    const doc = openDocument(docId);
    docRef.current = doc;
    const ytext = doc.getText('content');

    const observer = () => setContent(ytext.toString());
    ytext.observe(observer);
    setContent(ytext.toString()); // initial

    return () => {
      ytext.unobserve(observer);
      closeDocument(docId);
    };
  }, [docId, openDocument, closeDocument]);

  // Remote cursor presence
  useEffect(() => {
    const handler = ({ docId: d, cursors: c }) => {
      if (d === docId) setCursors(c);
    };
    ws.current?.on('cursors:update', handler);
    return () => ws.current?.off('cursors:update', handler);
  }, [docId, ws]);

  const handleEdit = (newText) => {
    const doc = docRef.current;
    const ytext = doc.getText('content');
    doc.transact(() => {
      ytext.delete(0, ytext.length);
      ytext.insert(0, newText);
    });
  };

  return (
    <div className="document-editor">
      <StatusBar
        connection={state.connection}
        syncStatus={state.syncStatus}
        offlineChanges={state.offlineChanges}
        users={state.onlineUsers}
      />
      <div className="editor-area">
        <textarea
          value={content}
          onChange={(e) => handleEdit(e.target.value)}
        />
        {cursors.map((cursor) => (
          <RemoteCursorOverlay key={cursor.userId} {...cursor} />
        ))}
      </div>
    </div>
  );
}

// ---- 4. Status Bar showing connection, sync, and presence ----
function StatusBar({ connection, syncStatus, offlineChanges, users }) {
  return (
    <div className="status-bar">
      <div className="left">
        <ConnectionIndicator status={connection} />
        {offlineChanges > 0 && (
          <span className="offline-badge">
            {offlineChanges} unsaved changes
          </span>
        )}
      </div>
      <div className="right">
        <span className="sync">{syncStatus}</span>
        <div className="presence-avatars">
          {users.map((u) => (
            <img
              key={u.id}
              src={u.avatar}
              alt={u.name}
              title={u.name}
              className="presence-avatar"
              style={{ borderColor: u.color }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function ConnectionIndicator({ status }) {
  const colors = {
    connected: '#22c55e',
    connecting: '#eab308',
    reconnecting: '#f59e0b',
    disconnected: '#ef4444',
    auth_error: '#ef4444',
  };

  return (
    <span className="connection-indicator">
      <span
        className="dot"
        style={{ backgroundColor: colors[status] || '#6b7280' }}
      />
      {status === 'connected' ? 'Live' : status}
    </span>
  );
}

function RemoteCursorOverlay({ userId, name, color, position }) {
  if (!position) return null;
  return (
    <div className="remote-cursor" style={{ left: position.x, top: position.y }}>
      <div className="cursor-line" style={{ borderColor: color }} />
      <span className="cursor-label" style={{ background: color }}>
        {name}
      </span>
    </div>
  );
}

// ---- 5. Offline Queue Manager (IndexedDB) ----
async function queueOfflineUpdate(docId, update) {
  const db = await openDB('collab-offline', 1, {
    upgrade(db) {
      db.createObjectStore('updates', { autoIncrement: true });
    },
  });
  await db.add('updates', { docId, update, timestamp: Date.now() });
}

async function flushOfflineQueue(ws) {
  const db = await openDB('collab-offline', 1);
  const tx = db.transaction('updates', 'readwrite');
  const store = tx.objectStore('updates');
  const allUpdates = await store.getAll();
  const allKeys = await store.getAllKeys();

  for (let i = 0; i < allUpdates.length; i++) {
    const { docId, update } = allUpdates[i];
    ws.send('doc:update', { docId, update });
    await store.delete(allKeys[i]);
  }
}
```

**Production checklist for this architecture:**

| Concern | Solution |
|---|---|
| **State sync** | Yjs CRDTs for conflict-free merging; server stores Y.Doc snapshots |
| **Presence** | WebSocket awareness protocol; Redis for cross-server presence |
| **Conflict resolution** | CRDTs handle concurrent edits automatically — no OT needed |
| **Offline support** | `y-indexeddb` persists CRDTs locally; offline queue for non-CRDT actions |
| **Scaling** | Redis Pub/Sub between WebSocket servers; Redis Streams for durability |
| **Auth** | Ticket-based WebSocket auth (Q13); per-document permission checks |
| **Monitoring** | Track: connections/server, message throughput, CRDT doc sizes, Redis lag |
| **Graceful deploys** | Drain connections to new servers; clients auto-reconnect |
| **Data persistence** | Periodic Y.Doc snapshots to PostgreSQL; S3 for large binary assets |
| **Rate limiting** | Per-connection message rate limits; server-side throttling |

This architecture handles hundreds of concurrent editors per document and thousands of documents across the platform, with seamless offline support and sub-100ms latency for collaborative edits.
