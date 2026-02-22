# 28. Serverless & Edge Computing

## Topic Introduction

Serverless lets you run code without managing servers. You write functions, deploy them, and the cloud provider handles scaling, patching, and infrastructure. **Edge computing** pushes that code closer to users (CDN edge locations) for ultra-low latency.

```
Traditional:   Request → Load Balancer → Server (always running, you manage) → Response
Serverless:    Request → API Gateway → Lambda (spins up on demand, auto-scales) → Response
Edge:          Request → Nearest CDN Edge → Run code right there → Response (5ms!)
```

**Key platforms**: AWS Lambda, Vercel Functions, Cloudflare Workers, AWS Lambda@Edge, Deno Deploy, Netlify Functions.

**Go/Java tradeoff**: Go has the best cold start times (~5ms). Java has the worst (~2-5 seconds without GraalVM). Node.js is in the middle (~200-500ms). For serverless, cold starts matter — Node.js and Go are the best choices.

---

## Q1. (Beginner) What is serverless computing? How does it differ from traditional servers?

**Answer**:

| | **Traditional (EC2/VPS)** | **Serverless (Lambda)** |
|---|---|---|
| Scaling | Manual (add servers) | Automatic (0 to 1000 instances) |
| Cost | Pay for idle time | Pay per execution only |
| Infrastructure | You manage OS, updates | Provider manages everything |
| Cold starts | None (always running) | Yes (first request slower) |
| State | Stateful (files, memory) | Stateless (no persistent state) |
| Execution limit | Unlimited | 15 minutes (Lambda) |
| Best for | Long-running, stateful apps | Event-driven, bursty workloads |

```js
// AWS Lambda function (Node.js)
exports.handler = async (event) => {
  const { httpMethod, pathParameters, body } = event;

  if (httpMethod === 'GET') {
    const user = await db.query('SELECT * FROM users WHERE id = $1', [pathParameters.id]);
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user),
    };
  }

  if (httpMethod === 'POST') {
    const data = JSON.parse(body);
    const user = await db.query('INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *', [data.name, data.email]);
    return { statusCode: 201, body: JSON.stringify(user) };
  }
};
```

---

## Q2. (Beginner) What are cold starts and how do they affect performance?

```js
// Cold start: Lambda creates a new execution environment
// 1. Download code (10-100ms)
// 2. Start Node.js runtime (50-100ms)
// 3. Initialize your code (variable — DB connections, imports)
// Total cold start: 200ms - 2s

// Code OUTSIDE handler runs once (during cold start)
const db = new Pool({ connectionString: process.env.DATABASE_URL }); // initialized once

exports.handler = async (event) => {
  // Code INSIDE handler runs on every invocation
  const result = await db.query('SELECT * FROM users');
  return { statusCode: 200, body: JSON.stringify(result.rows) };
};
```

**Reducing cold starts**:
```js
// 1. Keep functions small (fewer dependencies)
// 2. Use provisioned concurrency (pre-warm instances)
// 3. Use lightweight imports
const { DynamoDB } = require('@aws-sdk/client-dynamodb'); // specific import
// NOT: const AWS = require('aws-sdk'); // imports EVERYTHING

// 4. Lazy load heavy dependencies
let sharp;
function getSharp() {
  if (!sharp) sharp = require('sharp'); // only loaded when needed
  return sharp;
}
```

---

## Q3. (Beginner) How do you deploy a REST API as serverless functions?

```js
// Using Serverless Framework
// serverless.yml
const serverlessConfig = `
service: my-api
provider:
  name: aws
  runtime: nodejs20.x
  region: us-east-1
  environment:
    DATABASE_URL: \${env:DATABASE_URL}

functions:
  getUser:
    handler: handlers/users.get
    events:
      - httpApi:
          path: /users/{id}
          method: GET

  createUser:
    handler: handlers/users.create
    events:
      - httpApi:
          path: /users
          method: POST

  processImage:
    handler: handlers/images.process
    events:
      - s3:
          bucket: uploads
          event: s3:ObjectCreated:*
    timeout: 60

  dailyReport:
    handler: handlers/reports.daily
    events:
      - schedule: cron(0 0 * * ? *)
`;

// handlers/users.js
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

module.exports.get = async (event) => {
  const { id } = event.pathParameters;
  const result = await pool.query('SELECT * FROM users WHERE id = $1', [id]);
  if (result.rows.length === 0) return { statusCode: 404, body: JSON.stringify({ error: 'Not found' }) };
  return { statusCode: 200, body: JSON.stringify(result.rows[0]) };
};

module.exports.create = async (event) => {
  const data = JSON.parse(event.body);
  const result = await pool.query('INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *', [data.name, data.email]);
  return { statusCode: 201, body: JSON.stringify(result.rows[0]) };
};
```

---

## Q4. (Beginner) What are the limitations of serverless?

**Answer**:

| Limitation | Impact | Workaround |
|---|---|---|
| Cold starts (200ms-2s) | Latency-sensitive APIs | Provisioned concurrency |
| 15 min timeout | Long-running tasks | Step Functions, ECS |
| Stateless | No file system, no in-memory cache | S3, DynamoDB, Redis |
| 6MB payload (API Gateway) | Large file uploads | Pre-signed S3 URLs |
| 10GB disk (/tmp) | Large file processing | Stream to S3 |
| Vendor lock-in | AWS-specific code | Use frameworks (Serverless, SST) |
| No WebSockets (HTTP) | Real-time features | API Gateway WebSocket |
| Debugging difficulty | Hard to reproduce locally | SAM CLI, serverless-offline |

---

## Q5. (Beginner) When should you use serverless vs containers vs VMs?

| Use case | Serverless | Containers (ECS/K8s) | VMs (EC2) |
|---|---|---|---|
| API with bursty traffic | Best | Good | Wasteful |
| Event processing (S3, SQS) | Best | Good | Overkill |
| Cron jobs / scheduled tasks | Best | Good | Wasteful |
| Long-running processes | Bad (15 min limit) | Best | Good |
| WebSocket/real-time | Limited | Best | Good |
| ML model serving | Bad (cold starts) | Best | Good |
| Legacy applications | Bad (refactoring needed) | Good | Best |
| Cost at steady high load | Expensive | Moderate | Cheapest |

---

## Q6. (Intermediate) How do you handle database connections in serverless?

**Scenario**: Lambda scales to 1000 concurrent instances. Each opens a DB connection. Your PostgreSQL max is 100 connections. 900 Lambdas can't connect.

```js
// Problem: too many connections
const pool = new Pool({ max: 1 }); // even 1 per Lambda × 1000 Lambdas = 1000 connections

// Solution 1: RDS Proxy (AWS managed connection pooler)
const pool = new Pool({
  host: 'my-rds-proxy.proxy-xyz.us-east-1.rds.amazonaws.com', // RDS Proxy endpoint
  max: 1, // Lambda uses 1 connection, proxy manages pooling
});

// Solution 2: Use DynamoDB (no connection limits)
const { DynamoDBClient, GetItemCommand } = require('@aws-sdk/client-dynamodb');
const client = new DynamoDBClient({});

exports.handler = async (event) => {
  const result = await client.send(new GetItemCommand({
    TableName: 'users',
    Key: { id: { S: event.pathParameters.id } },
  }));
  return { statusCode: 200, body: JSON.stringify(result.Item) };
};

// Solution 3: Connection reuse across invocations
let cachedDb;
async function getDb() {
  if (cachedDb) return cachedDb;
  cachedDb = new Pool({ connectionString: process.env.DATABASE_URL, max: 1 });
  return cachedDb;
}

exports.handler = async (event) => {
  const db = await getDb(); // reused across warm invocations
  const result = await db.query('SELECT * FROM users WHERE id = $1', [event.pathParameters.id]);
  return { statusCode: 200, body: JSON.stringify(result.rows[0]) };
};
```

---

## Q7. (Intermediate) How do you implement event-driven processing with Lambda?

```js
// S3 trigger: process uploaded images
exports.processImage = async (event) => {
  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key);

    const { Body } = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    const buffer = await streamToBuffer(Body);

    // Generate thumbnails
    const thumb = await sharp(buffer).resize(200, 200).webp().toBuffer();
    const medium = await sharp(buffer).resize(800, 800).webp().toBuffer();

    await Promise.all([
      s3.send(new PutObjectCommand({ Bucket: bucket, Key: key.replace('uploads/', 'thumbnails/'), Body: thumb })),
      s3.send(new PutObjectCommand({ Bucket: bucket, Key: key.replace('uploads/', 'medium/'), Body: medium })),
    ]);
  }
};

// SQS trigger: process messages from queue
exports.processQueue = async (event) => {
  const results = [];
  for (const record of event.Records) {
    try {
      const message = JSON.parse(record.body);
      await processOrder(message);
      results.push({ messageId: record.messageId, success: true });
    } catch (err) {
      results.push({ messageId: record.messageId, success: false });
      // Return failed messages to retry
    }
  }

  // Partial batch failure reporting
  return {
    batchItemFailures: results
      .filter(r => !r.success)
      .map(r => ({ itemIdentifier: r.messageId })),
  };
};

// DynamoDB Streams: react to database changes
exports.onUserChange = async (event) => {
  for (const record of event.Records) {
    if (record.eventName === 'INSERT') {
      const newUser = record.dynamodb.NewImage;
      await sendWelcomeEmail(newUser.email.S);
    }
    if (record.eventName === 'MODIFY') {
      const oldImage = record.dynamodb.OldImage;
      const newImage = record.dynamodb.NewImage;
      if (oldImage.email.S !== newImage.email.S) {
        await sendEmailChangeNotification(oldImage.email.S, newImage.email.S);
      }
    }
  }
};
```

---

## Q8. (Intermediate) What is edge computing? How do Cloudflare Workers differ from Lambda?

```js
// Cloudflare Worker — runs at 300+ edge locations worldwide
// Response time: 5-50ms (vs 100-500ms for Lambda)
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/api/hello') {
      return new Response(JSON.stringify({
        message: 'Hello from the edge!',
        location: request.cf?.colo, // which edge location served this
      }), { headers: { 'Content-Type': 'application/json' } });
    }

    // A/B testing at the edge (no backend call needed)
    if (url.pathname.startsWith('/app')) {
      const variant = Math.random() < 0.5 ? 'A' : 'B';
      const response = await fetch(`https://origin.example.com/app-${variant}${url.pathname}`);
      return new Response(response.body, {
        headers: { ...response.headers, 'X-Variant': variant },
      });
    }

    return fetch(request); // pass through to origin
  },
};
```

| | **AWS Lambda** | **Cloudflare Workers** |
|---|---|---|
| Location | Region (us-east-1) | 300+ edge locations |
| Latency | 50-500ms | 5-50ms |
| Runtime | Node.js, Python, Go, etc. | V8 isolates (JS/Wasm) |
| Cold start | 200ms-2s | <5ms (no cold starts!) |
| Execution limit | 15 minutes | 30 seconds (free), 15 min (paid) |
| Memory | Up to 10GB | 128MB |
| Storage | S3, DynamoDB | KV, R2, D1 (SQLite), Durable Objects |
| Best for | Backend APIs, event processing | Auth, redirects, A/B testing, API routing |

---

## Q9. (Intermediate) How do you handle authentication and authorization in serverless?

```js
// Lambda Authorizer (custom authentication)
exports.authorizer = async (event) => {
  const token = event.authorizationToken?.replace('Bearer ', '');

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return {
      principalId: decoded.userId,
      policyDocument: {
        Version: '2012-10-17',
        Statement: [{
          Action: 'execute-api:Invoke',
          Effect: 'Allow',
          Resource: event.methodArn,
        }],
      },
      context: {
        userId: decoded.userId,
        email: decoded.email,
        role: decoded.role,
      },
    };
  } catch (err) {
    throw new Error('Unauthorized');
  }
};

// Protected function accesses user context
exports.getProfile = async (event) => {
  const userId = event.requestContext.authorizer.userId;
  const user = await getUser(userId);
  return { statusCode: 200, body: JSON.stringify(user) };
};
```

---

## Q10. (Intermediate) How do you test serverless functions locally?

```js
// Using serverless-offline plugin
// serverless.yml:
// plugins:
//   - serverless-offline

// Run: npx sls offline
// Simulates API Gateway + Lambda locally

// Unit testing Lambda handlers
describe('getUser handler', () => {
  it('returns user for valid ID', async () => {
    const event = {
      httpMethod: 'GET',
      pathParameters: { id: '42' },
      requestContext: { authorizer: { userId: '42' } },
    };

    const result = await handler(event);
    expect(result.statusCode).toBe(200);
    expect(JSON.parse(result.body).id).toBe('42');
  });

  it('returns 404 for non-existent user', async () => {
    const event = {
      httpMethod: 'GET',
      pathParameters: { id: '999' },
      requestContext: { authorizer: { userId: '42' } },
    };

    const result = await handler(event);
    expect(result.statusCode).toBe(404);
  });
});

// AWS SAM CLI for more realistic testing
// sam local invoke GetUserFunction -e events/get-user.json
// sam local start-api  (simulates API Gateway)
```

---

## Q11. (Intermediate) How do you implement Step Functions for complex serverless workflows?

```json
{
  "Comment": "Order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:validate-order",
      "Next": "CheckInventory",
      "Catch": [{ "ErrorEquals": ["ValidationError"], "Next": "OrderFailed" }]
    },
    "CheckInventory": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:check-inventory",
      "Next": "ProcessPayment",
      "Catch": [{ "ErrorEquals": ["OutOfStockError"], "Next": "OrderFailed" }]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:process-payment",
      "Retry": [{ "ErrorEquals": ["TransientError"], "MaxAttempts": 3, "BackoffRate": 2 }],
      "Next": "SendConfirmation",
      "Catch": [{ "ErrorEquals": ["States.ALL"], "Next": "RefundAndFail" }]
    },
    "SendConfirmation": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:send-confirmation",
      "End": true
    },
    "RefundAndFail": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123:function:refund-payment",
      "Next": "OrderFailed"
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed"
    }
  }
}
```

**Answer**: Step Functions orchestrate multi-step serverless workflows with built-in retry, error handling, parallel execution, and visual debugging. Use for anything that takes multiple Lambda functions in sequence.

---

## Q12. (Intermediate) How do you handle environment variables and secrets in serverless?

```js
// serverless.yml
const config = `
provider:
  environment:
    NODE_ENV: production
    API_URL: https://api.example.com

functions:
  processPayment:
    handler: handlers/payment.process
    environment:
      STRIPE_SECRET_KEY: \${ssm:/myapp/stripe-secret-key}  # AWS SSM Parameter Store
      DB_PASSWORD: \${ssm:/myapp/db-password~true}          # encrypted parameter
`;

// Runtime: access environment variables normally
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

// For sensitive values, use AWS Secrets Manager
const { SecretsManagerClient, GetSecretValueCommand } = require('@aws-sdk/client-secrets-manager');

let cachedSecrets;
async function getSecrets() {
  if (cachedSecrets) return cachedSecrets;
  const client = new SecretsManagerClient({});
  const result = await client.send(new GetSecretValueCommand({ SecretId: 'myapp/credentials' }));
  cachedSecrets = JSON.parse(result.SecretString);
  return cachedSecrets;
}
```

---

## Q13. (Advanced) How do you optimize Lambda performance and reduce costs?

```js
// 1. Right-size memory (more memory = more CPU = faster execution)
// Lambda charges: (memory allocated × execution time)
// 128MB × 1000ms = same cost as 512MB × 250ms, but 512MB is faster!

// 2. Provisioned concurrency for latency-sensitive functions
// Keeps N instances warm — no cold starts
// serverless.yml:
// provisionedConcurrency: 5

// 3. Minimize package size
// Use esbuild/webpack to bundle and tree-shake
// serverless.yml with serverless-esbuild:
// plugins: [serverless-esbuild]

// 4. Reuse connections across invocations
const https = require('https');
const agent = new https.Agent({ keepAlive: true });
// Use this agent for all HTTP calls

// 5. Use ARM architecture (20% cheaper, often faster)
// serverless.yml:
// architecture: arm64

// 6. Use Lambda Layers for shared dependencies
// Upload node_modules as a layer, reference from multiple functions
```

---

## Q14. (Advanced) How do you implement API caching with API Gateway?

```yaml
# API Gateway caching
# Responses cached at API Gateway level — Lambda not invoked for cache hits

# serverless.yml
provider:
  apiGateway:
    caching:
      enabled: true
      ttlInSeconds: 300
      dataEncrypted: true

functions:
  getProducts:
    handler: handlers/products.list
    events:
      - http:
          path: /products
          method: GET
          caching:
            enabled: true
            ttlInSeconds: 600
            cacheKeyParameters:
              - name: request.querystring.category
              - name: request.querystring.page
```

```js
// Cache invalidation from Lambda
const { APIGatewayClient, FlushStageCacheCommand } = require('@aws-sdk/client-api-gateway');

exports.updateProduct = async (event) => {
  await updateProductInDb(event);

  // Invalidate cache
  const client = new APIGatewayClient({});
  await client.send(new FlushStageCacheCommand({
    restApiId: process.env.API_ID,
    stageName: 'prod',
  }));
};
```

---

## Q15. (Advanced) How do you implement edge-side rendering?

```js
// Cloudflare Workers: render HTML at the edge
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Personalized content at the edge
    const country = request.cf?.country || 'US';
    const language = request.headers.get('Accept-Language')?.split(',')[0] || 'en';

    // Fetch page from cache or origin
    let response = await caches.default.match(request);
    if (!response) {
      response = await fetch(`https://origin.example.com${url.pathname}`);
    }

    // Transform HTML at the edge
    return new HTMLRewriter()
      .on('#greeting', {
        element(element) {
          element.setInnerContent(`Welcome from ${country}!`);
        },
      })
      .on('[data-lang]', {
        element(element) {
          if (element.getAttribute('data-lang') !== language) {
            element.remove();
          }
        },
      })
      .transform(response);
  },
};
```

---

## Q16. (Advanced) How do you monitor and debug serverless applications?

```js
// AWS X-Ray integration
const AWSXRay = require('aws-xray-sdk-core');
const AWS = AWSXRay.captureAWS(require('aws-sdk'));
const https = AWSXRay.captureHTTPs(require('https'));

// CloudWatch structured logging
function log(level, message, context = {}) {
  console.log(JSON.stringify({
    level,
    message,
    timestamp: new Date().toISOString(),
    requestId: context.requestId,
    functionName: process.env.AWS_LAMBDA_FUNCTION_NAME,
    functionVersion: process.env.AWS_LAMBDA_FUNCTION_VERSION,
    coldStart: isColdStart,
    ...context,
  }));
}

let isColdStart = true;
exports.handler = async (event, context) => {
  log('info', 'Handler invoked', {
    requestId: context.awsRequestId,
    coldStart: isColdStart,
  });
  isColdStart = false;

  // CloudWatch Insights query:
  // fields @timestamp, @message
  // | filter level = "error"
  // | filter coldStart = true
  // | stats count(*) by bin(5m)
};

// Custom CloudWatch metrics
const { CloudWatchClient, PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');
const cw = new CloudWatchClient({});

async function publishMetric(name, value, unit = 'Count') {
  await cw.send(new PutMetricDataCommand({
    Namespace: 'MyApp',
    MetricData: [{ MetricName: name, Value: value, Unit: unit }],
  }));
}
```

---

## Q17. (Advanced) How do you implement serverless WebSockets?

```js
// AWS API Gateway WebSocket API

// $connect: called when client connects
exports.connect = async (event) => {
  const connectionId = event.requestContext.connectionId;
  await dynamodb.put({
    TableName: 'Connections',
    Item: { connectionId, connectedAt: Date.now() },
  }).promise();
  return { statusCode: 200 };
};

// $disconnect: called when client disconnects
exports.disconnect = async (event) => {
  await dynamodb.delete({
    TableName: 'Connections',
    Key: { connectionId: event.requestContext.connectionId },
  }).promise();
  return { statusCode: 200 };
};

// sendMessage: broadcast to all connected clients
exports.sendMessage = async (event) => {
  const body = JSON.parse(event.body);
  const connections = await dynamodb.scan({ TableName: 'Connections' }).promise();

  const apiGateway = new ApiGatewayManagementApi({
    endpoint: `${event.requestContext.domainName}/${event.requestContext.stage}`,
  });

  await Promise.all(connections.Items.map(async ({ connectionId }) => {
    try {
      await apiGateway.postToConnection({
        ConnectionId: connectionId,
        Data: JSON.stringify({ message: body.message }),
      }).promise();
    } catch (err) {
      if (err.statusCode === 410) {
        await dynamodb.delete({ TableName: 'Connections', Key: { connectionId } }).promise();
      }
    }
  }));

  return { statusCode: 200 };
};
```

---

## Q18. (Advanced) How do you migrate from Express to serverless?

```js
// Option 1: Use serverless-http wrapper (minimal changes)
const serverless = require('serverless-http');
const app = require('./app'); // existing Express app

module.exports.handler = serverless(app);
// That's it! Your Express app runs in Lambda

// Option 2: Gradual migration — move specific routes to Lambda
// Keep Express for most routes, Lambda for new/heavy routes

// Option 3: Rewrite as individual functions
// Before (Express):
app.get('/api/users/:id', getUser);
app.post('/api/users', createUser);
app.get('/api/orders', listOrders);

// After (serverless functions):
// handlers/users/get.js → GET /users/{id}
// handlers/users/create.js → POST /users
// handlers/orders/list.js → GET /orders
```

---

## Q19. (Advanced) How do you handle serverless at scale (1 million requests/day)?

```
1M req/day = ~12 req/sec average, ~100 req/sec peak

Architecture:
CloudFront (CDN) → API Gateway (caching) → Lambda → DynamoDB/Aurora Serverless
                                          → S3 (file storage)
                                          → SQS → Lambda (async processing)

Cost estimate:
- Lambda: 1M × 200ms × 128MB = ~$0.40/month
- API Gateway: 1M × $1/million = $1/month
- DynamoDB: depends on read/write units
- Total: $5-50/month (vs $100-500/month for EC2)
```

```js
// Optimization for high scale:
// 1. API Gateway response caching (reduce Lambda invocations by 80%)
// 2. DynamoDB with on-demand capacity (auto-scales)
// 3. SQS batching (process 10 messages per Lambda invocation)
// 4. Reserved concurrency (prevent runaway scaling)
// 5. Provisioned concurrency for latency-sensitive paths
```

---

## Q20. (Advanced) Senior red flags in serverless architectures.

**Answer**:

1. **Ignoring cold starts** — user-facing API with 2s cold start on every scale-up
2. **Lambda monolith** — entire Express app in one Lambda (defeats the purpose)
3. **No connection pooling** — 1000 Lambdas × 1 DB connection each = connection exhaustion
4. **Synchronous chains** — Lambda A calls Lambda B calls Lambda C (latency compounds, hard to debug)
5. **No idempotency** — SQS/EventBridge can deliver messages more than once
6. **No dead letter queue** — failed events disappear forever
7. **Oversized Lambda packages** — 50MB package = slow cold starts. Bundle and tree-shake.
8. **No monitoring** — CloudWatch logs with no structure, no alerting, no dashboards
9. **Vendor lock-in without abstraction** — AWS-specific code everywhere, impossible to migrate
10. **Using serverless for everything** — WebSocket servers, long-running tasks, and ML inference don't fit

**Senior interview answer**: "I use serverless for event-driven workloads, bursty APIs, and scheduled tasks. I keep functions small and focused, use provisioned concurrency for latency-sensitive paths, RDS Proxy for database connections, and SQS for async processing. I monitor with structured CloudWatch logs, X-Ray tracing, and custom metrics. For long-running or stateful workloads, I use containers (ECS/Fargate) instead. I implement the Strangler Fig pattern to gradually migrate from Express to serverless, running both in parallel during transition."
