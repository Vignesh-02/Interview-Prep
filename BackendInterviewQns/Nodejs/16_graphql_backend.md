# 16. GraphQL Backend

## Topic Introduction

GraphQL is a **query language for APIs** where the client specifies exactly what data it needs. Unlike REST where each endpoint returns a fixed shape, GraphQL has a single endpoint (`/graphql`) and the client describes the response structure.

```graphql
# Client asks for exactly what it needs
query {
  user(id: 42) {
    name
    email
    orders(last: 5) {
      id
      total
      items { name, price }
    }
  }
}
```

**Key advantages**: No over-fetching (get only requested fields), no under-fetching (get related data in one request), strong typing (schema defines all possible queries). **Key challenges**: N+1 query problem, query complexity attacks, caching is harder than REST.

**Go/Java tradeoff**: Go uses `gqlgen` (code-first, type-safe). Java uses Spring GraphQL or Netflix DGS. Node.js uses Apollo Server or `graphql-yoga`. Node's dynamic nature makes GraphQL resolver writing very natural.

---

## Q1. (Beginner) What is GraphQL? How does it differ from REST?

| | **REST** | **GraphQL** |
|---|---|---|
| Endpoints | Multiple (`/users`, `/orders`) | Single (`/graphql`) |
| Data shape | Fixed per endpoint | Client chooses |
| Over-fetching | Common (get all fields) | None (request specific fields) |
| Under-fetching | Common (multiple round trips) | None (nested queries) |
| Caching | HTTP caching (easy) | Custom (harder) |
| Versioning | URL versioning (`/v1/`) | Schema evolution (no versioning) |

```js
// REST: 3 requests for a user profile page
// GET /users/42
// GET /users/42/orders
// GET /users/42/notifications

// GraphQL: 1 request
// POST /graphql
// { query: "{ user(id: 42) { name orders { id } notifications { message } } }" }
```

---

## Q2. (Beginner) How do you set up a basic GraphQL server in Node.js?

```js
const { ApolloServer } = require('@apollo/server');
const { startStandaloneServer } = require('@apollo/server/standalone');

const typeDefs = `
  type User {
    id: ID!
    name: String!
    email: String!
    posts: [Post!]!
  }
  type Post {
    id: ID!
    title: String!
    content: String!
    author: User!
  }
  type Query {
    user(id: ID!): User
    users: [User!]!
    post(id: ID!): Post
  }
  type Mutation {
    createPost(title: String!, content: String!): Post!
  }
`;

const resolvers = {
  Query: {
    user: (_, { id }) => db.query('SELECT * FROM users WHERE id = $1', [id]).then(r => r.rows[0]),
    users: () => db.query('SELECT * FROM users').then(r => r.rows),
  },
  User: {
    posts: (parent) => db.query('SELECT * FROM posts WHERE author_id = $1', [parent.id]).then(r => r.rows),
  },
  Mutation: {
    createPost: (_, { title, content }, ctx) => {
      return db.query('INSERT INTO posts(title, content, author_id) VALUES($1,$2,$3) RETURNING *',
        [title, content, ctx.user.id]).then(r => r.rows[0]);
    },
  },
};

const server = new ApolloServer({ typeDefs, resolvers });
startStandaloneServer(server, { listen: { port: 4000 } });
```

---

## Q3. (Beginner) What is the N+1 problem in GraphQL? How does DataLoader solve it?

```js
// WITHOUT DataLoader — N+1 queries
// Query: { users { name posts { title } } }
// 1 query: SELECT * FROM users (10 users)
// 10 queries: SELECT * FROM posts WHERE author_id = 1, 2, 3...

// WITH DataLoader — 2 queries total
const DataLoader = require('dataloader');

const postsByAuthorLoader = new DataLoader(async (authorIds) => {
  const posts = await db.query('SELECT * FROM posts WHERE author_id = ANY($1)', [authorIds]);
  const postsByAuthor = {};
  posts.rows.forEach(p => { (postsByAuthor[p.author_id] ||= []).push(p); });
  return authorIds.map(id => postsByAuthor[id] || []);
});

const resolvers = {
  User: {
    posts: (parent) => postsByAuthorLoader.load(parent.id), // batched!
  },
};
```

**Answer**: DataLoader batches and caches individual `load()` calls within a single tick of the event loop. Instead of 10 separate queries, it collects all IDs and makes ONE batched query.

---

## Q4. (Beginner) What are mutations? How do you handle input validation?

```js
const typeDefs = `
  input CreateUserInput {
    name: String!
    email: String!
    age: Int
  }
  type Mutation {
    createUser(input: CreateUserInput!): User!
  }
`;

const resolvers = {
  Mutation: {
    createUser: async (_, { input }, ctx) => {
      // Validate with Zod
      const schema = z.object({
        name: z.string().min(1).max(100),
        email: z.string().email(),
        age: z.number().int().min(13).optional(),
      });
      const validated = schema.parse(input);

      const result = await db.query(
        'INSERT INTO users(name, email, age) VALUES($1,$2,$3) RETURNING *',
        [validated.name, validated.email, validated.age]
      );
      return result.rows[0];
    },
  },
};
```

---

## Q5. (Beginner) How do you handle authentication in GraphQL?

```js
const server = new ApolloServer({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  context: async ({ req }) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    let user = null;
    if (token) {
      try { user = jwt.verify(token, SECRET); } catch {}
    }
    return { user, db, redis };
  },
});

// In resolvers, check auth
const resolvers = {
  Mutation: {
    createPost: (_, args, ctx) => {
      if (!ctx.user) throw new GraphQLError('Not authenticated', { extensions: { code: 'UNAUTHENTICATED' } });
      return createPost(args, ctx.user.id);
    },
  },
};
```

---

## Q6. (Intermediate) How do you prevent query complexity attacks (deeply nested or expensive queries)?

```js
const depthLimit = require('graphql-depth-limit');
const { createComplexityLimitRule } = require('graphql-validation-complexity');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    depthLimit(5), // max 5 levels of nesting
    createComplexityLimitRule(1000, { // max 1000 complexity points
      scalarCost: 1,
      objectCost: 10,
      listFactor: 20,
    }),
  ],
});

// Malicious query (blocked):
// { user { posts { comments { author { posts { comments { ... } } } } } } }
```

---

## Q7. (Intermediate) How do you implement pagination in GraphQL (Relay-style connections)?

```js
const typeDefs = `
  type PostConnection {
    edges: [PostEdge!]!
    pageInfo: PageInfo!
  }
  type PostEdge {
    cursor: String!
    node: Post!
  }
  type PageInfo {
    hasNextPage: Boolean!
    endCursor: String
  }
  type Query {
    posts(first: Int!, after: String): PostConnection!
  }
`;

const resolvers = {
  Query: {
    posts: async (_, { first, after }) => {
      const limit = Math.min(first, 100);
      const cursor = after ? Buffer.from(after, 'base64').toString() : null;
      const query = cursor
        ? 'SELECT * FROM posts WHERE id < $1 ORDER BY id DESC LIMIT $2'
        : 'SELECT * FROM posts ORDER BY id DESC LIMIT $1';
      const params = cursor ? [cursor, limit + 1] : [limit + 1];
      const result = await db.query(query, params);
      const hasMore = result.rows.length > limit;
      const nodes = result.rows.slice(0, limit);

      return {
        edges: nodes.map(n => ({ cursor: Buffer.from(n.id.toString()).toString('base64'), node: n })),
        pageInfo: {
          hasNextPage: hasMore,
          endCursor: nodes.length ? Buffer.from(nodes[nodes.length - 1].id.toString()).toString('base64') : null,
        },
      };
    },
  },
};
```

---

## Q8. (Intermediate) How do you implement subscriptions (real-time) in GraphQL?

```js
const { createServer } = require('http');
const { WebSocketServer } = require('ws');
const { useServer } = require('graphql-ws/lib/use/ws');
const { PubSub } = require('graphql-subscriptions');

const pubsub = new PubSub();

const typeDefs = `
  type Subscription {
    messageAdded(roomId: ID!): Message!
  }
`;

const resolvers = {
  Subscription: {
    messageAdded: {
      subscribe: (_, { roomId }) => pubsub.asyncIterator(`MESSAGE_ADDED_${roomId}`),
    },
  },
  Mutation: {
    sendMessage: async (_, { roomId, content }, ctx) => {
      const msg = await db.query('INSERT INTO messages ... RETURNING *', [roomId, content, ctx.user.id]);
      pubsub.publish(`MESSAGE_ADDED_${roomId}`, { messageAdded: msg.rows[0] });
      return msg.rows[0];
    },
  },
};

// Setup WebSocket server for subscriptions
const httpServer = createServer(app);
const wsServer = new WebSocketServer({ server: httpServer, path: '/graphql' });
useServer({ schema }, wsServer);
```

---

## Q9. (Intermediate) GraphQL vs REST — when should you choose each?

**Answer**:

| Choose **GraphQL** when | Choose **REST** when |
|---|---|
| Multiple client types (web, mobile, TV) need different data | Simple CRUD with standard shapes |
| Deeply nested related data | File uploads/downloads |
| Rapid frontend iteration | Simple caching (HTTP caching) |
| Bandwidth-sensitive (mobile) | Public API (REST is more universally understood) |
| Complex data requirements | Webhooks |

---

## Q10. (Intermediate) How do you handle errors in GraphQL properly?

**Scenario**: Your resolver throws a database error. By default, GraphQL returns it in the `errors` array — potentially leaking internal details.

```js
// BAD: Raw errors leak to clients
const resolvers = {
  Query: {
    user: async (_, { id }) => {
      return await db.query('SELECT * FROM users WHERE id = $1', [id]); // DB error leaks
    },
  },
};

// GOOD: Structured error handling with custom error classes
const { GraphQLError } = require('graphql');

class NotFoundError extends GraphQLError {
  constructor(resource, id) {
    super(`${resource} not found`, {
      extensions: { code: 'NOT_FOUND', resource, id },
    });
  }
}

class ValidationError extends GraphQLError {
  constructor(field, message) {
    super(message, {
      extensions: { code: 'VALIDATION_ERROR', field },
    });
  }
}

const resolvers = {
  Mutation: {
    updateUser: async (_, { id, input }) => {
      if (input.email && !isValidEmail(input.email)) {
        throw new ValidationError('email', 'Invalid email format');
      }
      const user = await User.findById(id);
      if (!user) throw new NotFoundError('User', id);

      try {
        return await user.update(input);
      } catch (err) {
        console.error('Update failed:', err); // log full error
        throw new GraphQLError('Failed to update user', {
          extensions: { code: 'INTERNAL_ERROR' }, // safe message to client
        });
      }
    },
  },
};
```

**Answer**: GraphQL returns errors in a top-level `errors` array. Use `extensions.code` for machine-readable error codes. Never leak database or stack trace details. Use a `formatError` function to sanitize unexpected errors in production.

```js
// Apollo Server error formatting
const server = new ApolloServer({
  typeDefs,
  resolvers,
  formatError: (formattedError, error) => {
    // Log full error internally
    console.error(error);
    // In production, hide unexpected errors
    if (formattedError.extensions?.code === 'INTERNAL_SERVER_ERROR') {
      return { message: 'Internal server error', extensions: { code: 'INTERNAL_SERVER_ERROR' } };
    }
    return formattedError;
  },
});
```

---

## Q11. (Intermediate) What is schema-first vs code-first GraphQL design? Which is better?

**Answer**:

```
Schema-first: Write .graphql schema files → generate resolver types
Code-first:   Write code → schema is generated from code
```

```js
// SCHEMA-FIRST (Apollo Server — write SDL first)
// schema.graphql
// type User { id: ID!, name: String!, email: String! }
// type Query { user(id: ID!): User }

// Then write resolvers to match
const resolvers = {
  Query: { user: (_, { id }) => User.findById(id) },
};

// CODE-FIRST (Nexus — write code, schema generated)
const { objectType, queryType, makeSchema } = require('nexus');

const User = objectType({
  name: 'User',
  definition(t) {
    t.nonNull.id('id');
    t.nonNull.string('name');
    t.nonNull.string('email');
    t.list.field('orders', {
      type: 'Order',
      resolve: (parent, _, ctx) => ctx.db.order.findMany({ where: { userId: parent.id } }),
    });
  },
});

const schema = makeSchema({ types: [User, queryType({ definition(t) { t.field('user', { type: 'User', args: { id: idArg() }, resolve: (_, { id }, ctx) => ctx.db.user.findUnique({ where: { id } }) }); } })] });
```

| | **Schema-first** | **Code-first** |
|---|---|---|
| Source of truth | `.graphql` files | Code |
| Type safety | Needs codegen (e.g., GraphQL Code Generator) | Built-in (TypeScript types auto-generated) |
| Frontend collaboration | Designers can read SDL | Need to read code |
| Refactoring | Schema + resolver can drift apart | Always in sync |
| Best for | Teams with frontend/backend split | Full-stack teams, TypeScript projects |

---

## Q12. (Intermediate) How do you implement pagination in GraphQL?

```graphql
# Relay-style cursor pagination (recommended)
type Query {
  users(first: Int, after: String): UserConnection!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  cursor: String!
  node: User!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

```js
// Resolver implementation
const resolvers = {
  Query: {
    users: async (_, { first = 20, after }) => {
      const limit = Math.min(first, 100); // cap at 100
      let query = db('users').orderBy('created_at', 'desc').limit(limit + 1);

      if (after) {
        const cursor = Buffer.from(after, 'base64').toString('utf8');
        query = query.where('created_at', '<', cursor);
      }

      const rows = await query;
      const hasNextPage = rows.length > limit;
      const nodes = hasNextPage ? rows.slice(0, limit) : rows;

      return {
        edges: nodes.map((node) => ({
          cursor: Buffer.from(node.created_at.toISOString()).toString('base64'),
          node,
        })),
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: nodes[0] ? Buffer.from(nodes[0].created_at.toISOString()).toString('base64') : null,
          endCursor: nodes.length > 0 ? Buffer.from(nodes[nodes.length - 1].created_at.toISOString()).toString('base64') : null,
        },
        totalCount: async () => {
          const [{ count }] = await db('users').count('* as count');
          return parseInt(count);
        },
      };
    },
  },
};
```

**Answer**: Two styles — (1) **Offset-based** (`skip/take`) — simple but breaks with inserts/deletes, (2) **Cursor-based** (Relay connection spec) — stable, performant, works with real-time data. Always use cursor-based for production. Cap the `first` argument to prevent fetching millions of rows.

---

## Q13. (Advanced) How does Apollo Federation work for GraphQL in microservices?

**Scenario**: You have 5 microservices (Users, Orders, Products, Reviews, Inventory). Each needs its own GraphQL schema but clients should see a unified API.

```
Client → Apollo Gateway → [Users subgraph, Orders subgraph, Products subgraph, ...]
```

```js
// Users subgraph
const { buildSubgraphSchema } = require('@apollo/subgraph');
const { gql } = require('graphql-tag');

const typeDefs = gql`
  type User @key(fields: "id") {
    id: ID!
    name: String!
    email: String!
  }

  type Query {
    user(id: ID!): User
  }
`;

const resolvers = {
  User: {
    __resolveReference: (ref) => User.findById(ref.id), // called by other subgraphs
  },
  Query: {
    user: (_, { id }) => User.findById(id),
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema({ typeDefs, resolvers }),
});

// Orders subgraph — extends User from Users subgraph
const ordersTypeDefs = gql`
  type Order @key(fields: "id") {
    id: ID!
    total: Float!
    items: [OrderItem!]!
  }

  extend type User @key(fields: "id") {
    id: ID! @external
    orders: [Order!]!
  }

  type Query {
    order(id: ID!): Order
  }
`;

const ordersResolvers = {
  User: {
    orders: (user) => Order.findByUserId(user.id), // resolves user.orders
  },
};
```

```js
// Apollo Gateway — composes all subgraphs
const { ApolloGateway } = require('@apollo/gateway');

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'users', url: 'http://users-service:4001/graphql' },
      { name: 'orders', url: 'http://orders-service:4002/graphql' },
      { name: 'products', url: 'http://products-service:4003/graphql' },
    ],
  }),
});

const server = new ApolloServer({ gateway });
```

**Answer**: Federation allows each microservice to own its portion of the graph. The `@key` directive defines entity primary keys. `__resolveReference` lets other subgraphs fetch data from this service. The Gateway composes everything into a unified schema. This is how companies like Netflix and Airbnb run GraphQL at scale.

---

## Q14. (Advanced) How do you implement caching in GraphQL?

**Answer**: GraphQL caching is harder than REST because queries are dynamic. Strategies:

```js
// 1. Persisted Queries — client sends hash instead of full query
// Reduces bandwidth and prevents arbitrary queries
// Client: GET /graphql?extensions={"persistedQuery":{"sha256Hash":"abc123"}}

// Apollo Server automatic persisted queries
const server = new ApolloServer({
  typeDefs,
  resolvers,
  persistedQueries: {
    cache: new KeyValueCache(), // Redis-backed in production
  },
});

// 2. Response caching with @cacheControl directive
const typeDefs = gql`
  type User @cacheControl(maxAge: 300) {      # cache 5 minutes
    id: ID!
    name: String! @cacheControl(maxAge: 3600) # name changes rarely
    email: String!
    orderCount: Int! @cacheControl(maxAge: 60) # changes more often
  }
`;

// 3. DataLoader as a per-request cache (deduplication)
// If 10 resolvers request User#42, DataLoader fetches it once
const userLoader = new DataLoader(async (ids) => {
  const users = await User.findByIds(ids);
  return ids.map((id) => users.find((u) => u.id === id));
});
// userLoader.load(42) — cached within this request

// 4. Redis-level result caching for expensive queries
const responseCachePlugin = require('@apollo/server-plugin-response-cache');
const server = new ApolloServer({
  plugins: [
    responseCachePlugin.default({
      sessionId: (ctx) => ctx.request.http.headers.get('authorization') || null,
    }),
  ],
});
```

| **Layer** | **Scope** | **Best for** |
|---|---|---|
| DataLoader | Per-request | Deduplicate DB queries |
| `@cacheControl` | HTTP/CDN | Public, rarely-changing data |
| Persisted queries | Network | Reduce query size, security |
| Redis cache | Cross-request | Expensive computations |

---

## Q15. (Advanced) How do you handle file uploads in GraphQL?

```js
// Using graphql-upload package
const { GraphQLUpload } = require('graphql-upload-ts');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');

const typeDefs = gql`
  scalar Upload

  type File {
    url: String!
    filename: String!
    mimetype: String!
    size: Int!
  }

  type Mutation {
    uploadAvatar(file: Upload!): File!
  }
`;

const resolvers = {
  Upload: GraphQLUpload,
  Mutation: {
    uploadAvatar: async (_, { file }, { user }) => {
      const { createReadStream, filename, mimetype } = await file;

      // Validate
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!allowedTypes.includes(mimetype)) throw new Error('Invalid file type');

      const stream = createReadStream();
      const chunks = [];
      for await (const chunk of stream) {
        chunks.push(chunk);
        if (Buffer.concat(chunks).length > 5 * 1024 * 1024) {
          throw new Error('File too large (max 5MB)');
        }
      }
      const buffer = Buffer.concat(chunks);

      // Upload to S3
      const key = `avatars/${user.id}/${Date.now()}-${filename}`;
      await s3.send(new PutObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: key,
        Body: buffer,
        ContentType: mimetype,
      }));

      return {
        url: `https://${process.env.S3_BUCKET}.s3.amazonaws.com/${key}`,
        filename,
        mimetype,
        size: buffer.length,
      };
    },
  },
};
```

**Answer**: GraphQL file uploads use the multipart request spec. For large files, many teams prefer a hybrid: get a pre-signed S3 URL via GraphQL mutation, upload directly to S3 from client, then confirm via another mutation.

---

## Q16. (Advanced) How do you test GraphQL resolvers and queries?

```js
const { ApolloServer } = require('@apollo/server');
const { createTestClient } = require('@apollo/server/testing');
const { describe, it, expect, beforeAll, afterAll } = require('@jest/globals');

describe('User queries', () => {
  let server;
  let query;

  beforeAll(async () => {
    server = new ApolloServer({ typeDefs, resolvers });
    await server.start();
  });

  afterAll(async () => { await server.stop(); });

  it('fetches a user by ID', async () => {
    const response = await server.executeOperation({
      query: `query GetUser($id: ID!) {
        user(id: $id) { id name email }
      }`,
      variables: { id: '42' },
    });

    expect(response.body.singleResult.errors).toBeUndefined();
    expect(response.body.singleResult.data.user).toEqual({
      id: '42',
      name: 'John Doe',
      email: 'john@example.com',
    });
  });

  it('returns error for non-existent user', async () => {
    const response = await server.executeOperation({
      query: `query { user(id: "999") { id name } }`,
    });

    expect(response.body.singleResult.errors[0].extensions.code).toBe('NOT_FOUND');
  });

  it('validates mutation input', async () => {
    const response = await server.executeOperation({
      query: `mutation { createUser(input: { name: "", email: "invalid" }) { id } }`,
    });

    expect(response.body.singleResult.errors[0].extensions.code).toBe('VALIDATION_ERROR');
  });
});
```

**Answer**: Test at three levels: (1) Unit test resolvers directly (pass mock context), (2) Integration test with `server.executeOperation()` (no network), (3) E2E test with actual HTTP requests. Always test error paths, validation, and auth.

---

## Q17. (Advanced) How do you implement real-time subscriptions in GraphQL?

```js
const { createServer } = require('http');
const { WebSocketServer } = require('ws');
const { useServer } = require('graphql-ws/lib/use/ws');
const { PubSub } = require('graphql-subscriptions');

const pubsub = new PubSub(); // in production, use Redis PubSub

const typeDefs = gql`
  type Subscription {
    messageAdded(channelId: ID!): Message!
    orderStatusChanged(orderId: ID!): Order!
  }
`;

const resolvers = {
  Subscription: {
    messageAdded: {
      subscribe: (_, { channelId }, { user }) => {
        // Auth check
        if (!user) throw new Error('Not authenticated');
        return pubsub.asyncIterator(`CHANNEL_${channelId}`);
      },
    },
    orderStatusChanged: {
      subscribe: (_, { orderId }, { user }) => {
        // Only subscribe to your own orders
        return pubsub.asyncIterator(`ORDER_${orderId}`);
      },
    },
  },
  Mutation: {
    sendMessage: async (_, { channelId, text }, { user }) => {
      const message = await Message.create({ channelId, text, userId: user.id });
      // Publish to subscribers
      pubsub.publish(`CHANNEL_${channelId}`, { messageAdded: message });
      return message;
    },
  },
};

// Setup WebSocket server for subscriptions
const httpServer = createServer(app);
const wsServer = new WebSocketServer({ server: httpServer, path: '/graphql' });

useServer({
  schema,
  context: async (ctx) => {
    const token = ctx.connectionParams?.authToken;
    const user = token ? verifyToken(token) : null;
    return { user };
  },
  onConnect: async (ctx) => {
    console.log('Subscription client connected');
  },
  onDisconnect: () => {
    console.log('Subscription client disconnected');
  },
}, wsServer);
```

**Answer**: Subscriptions use WebSockets under the hood (`graphql-ws` library). The server publishes events via PubSub, and clients subscribe via GraphQL subscription queries. In production, replace `PubSub` with `RedisPubSub` for multi-server support.

---

## Q18. (Advanced) How do you secure a GraphQL API against common attacks?

```js
const depthLimit = require('graphql-depth-limit');
const costAnalysis = require('graphql-cost-analysis');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    depthLimit(7), // max query depth = 7 levels
  ],
  plugins: [
    // Query complexity analysis
    {
      requestDidStart: () => ({
        didResolveOperation({ request, document }) {
          const complexity = getComplexity({
            schema,
            query: document,
            variables: request.variables,
            estimators: [
              fieldExtensionsEstimator(),
              simpleEstimator({ defaultComplexity: 1 }),
            ],
          });
          if (complexity > 1000) {
            throw new GraphQLError(`Query too complex: ${complexity}. Max: 1000`);
          }
        },
      }),
    },
  ],
  introspection: process.env.NODE_ENV !== 'production', // disable in prod
});

// Rate limiting per client
const rateLimit = require('express-rate-limit');
app.use('/graphql', rateLimit({
  windowMs: 60 * 1000,
  max: 100,
  message: 'Too many requests',
}));
```

**Security checklist**:
1. **Depth limiting** — prevent `{ user { friends { friends { friends { ... } } } } }`
2. **Complexity analysis** — limit total cost of a query
3. **Persisted queries** — only allow pre-approved queries in production
4. **Disable introspection** in production — don't expose your schema
5. **Rate limiting** — per IP or per user
6. **Input validation** — validate all arguments beyond GraphQL type checks
7. **Authentication** — verify tokens in context factory
8. **Field-level authorization** — check permissions per field

---

## Q19. (Advanced) How do you monitor and optimize GraphQL resolver performance?

```js
// Apollo Server plugin for resolver timing
const resolverTimingPlugin = {
  requestDidStart() {
    const resolverTimings = [];
    return {
      executionDidStart() {
        return {
          willResolveField({ info }) {
            const start = process.hrtime.bigint();
            return () => {
              const duration = Number(process.hrtime.bigint() - start) / 1e6;
              if (duration > 10) { // log slow resolvers (>10ms)
                resolverTimings.push({
                  field: `${info.parentType.name}.${info.fieldName}`,
                  duration: `${duration.toFixed(2)}ms`,
                });
              }
            };
          },
        };
      },
      willSendResponse({ response }) {
        if (resolverTimings.length > 0) {
          console.warn('Slow resolvers:', resolverTimings);
          // Send to Prometheus/Datadog
          resolverTimings.forEach(({ field, duration }) => {
            resolverDurationHistogram.observe({ field }, parseFloat(duration));
          });
        }
      },
    };
  },
};

// Track query patterns
const queryTrackingPlugin = {
  requestDidStart({ request }) {
    const operationName = request.operationName || 'anonymous';
    queryCounter.inc({ operation: operationName });

    return {
      didEncounterErrors({ errors }) {
        errors.forEach((err) => {
          errorCounter.inc({ operation: operationName, code: err.extensions?.code || 'UNKNOWN' });
        });
      },
    };
  },
};
```

**Key metrics to monitor**:
- Resolver execution time (p50, p95, p99)
- Query complexity distribution
- Error rates per operation
- Cache hit rates (DataLoader, persisted queries)
- N+1 query detection (resolvers that fire excessive DB queries)

---

## Q20. (Advanced) Senior GraphQL red flags and best practices.

**Answer**:

1. **No DataLoader** → N+1 queries everywhere (10 users × 10 orders = 100 DB queries instead of 2)
2. **No depth/complexity limits** → DoS via deeply nested queries
3. **Introspection enabled in production** → attackers see your entire schema
4. **No persisted queries** → arbitrary queries accepted from anyone
5. **Returning database errors to clients** → information leak
6. **No monitoring of resolver performance** → can't find slow fields
7. **Over-fetching in resolvers** (`SELECT *` when client needs 2 fields)
8. **No input validation** beyond GraphQL types — GraphQL only checks types, not business rules
9. **Using in-memory PubSub for subscriptions** — breaks with multiple servers
10. **No circuit breaker on resolver dependencies** — one slow service brings down the entire graph

```js
// SMELL: resolver that doesn't use DataLoader
user: async (_, { id }) => {
  // If this resolver runs in a list, each call is a separate DB query
  return await db.query('SELECT * FROM users WHERE id = $1', [id]); // N+1!
};

// FIX: Always use DataLoader for entities referenced in lists
user: async (_, { id }, { loaders }) => {
  return loaders.user.load(id); // batched + deduplicated
};
```

**Senior interview answer**: "I use GraphQL when clients need flexible data fetching — mobile and web often need different fields. I always implement DataLoader for batching, depth and complexity limits for security, persisted queries for production, and per-field performance monitoring. For simple CRUD or public APIs, I prefer REST. In microservices, I use Apollo Federation with each team owning their subgraph."
