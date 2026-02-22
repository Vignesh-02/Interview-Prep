# 25. File Uploads, Streaming & Object Storage

## Topic Introduction

File handling is one of the most common backend tasks — profile pictures, documents, CSV imports, video uploads. A senior engineer knows how to handle files **safely** (validation, virus scanning), **efficiently** (streaming, no memory bloat), and at **scale** (object storage, CDN).

```
Client → Upload → Backend (validate, process) → Object Storage (S3/GCS) → CDN → Client
```

**Key principle**: Never store files on the application server filesystem. Use **object storage** (S3, GCS, Azure Blob). Servers are ephemeral in cloud — files disappear on redeploy.

**Go/Java tradeoff**: Go's `io.Reader/Writer` interfaces make streaming natural. Java uses `InputStream/OutputStream`. Node.js uses Streams (Readable, Writable, Transform) which are powerful but have tricky backpressure semantics.

---

## Q1. (Beginner) How do you handle file uploads in Express with Multer?

```js
const multer = require('multer');
const path = require('path');

// Configure Multer
const upload = multer({
  storage: multer.memoryStorage(), // store in memory (for small files)
  limits: {
    fileSize: 5 * 1024 * 1024,  // 5MB max
    files: 5,                    // max 5 files
  },
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.webp', '.pdf'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${ext} not allowed`));
    }
  },
});

// Single file upload
app.post('/api/avatar', auth, upload.single('avatar'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

  const url = await uploadToS3(req.file.buffer, req.file.originalname, req.file.mimetype);
  await User.update(req.user.id, { avatarUrl: url });

  res.json({ url });
});

// Multiple file upload
app.post('/api/documents', auth, upload.array('files', 5), async (req, res) => {
  const urls = await Promise.all(
    req.files.map(file => uploadToS3(file.buffer, file.originalname, file.mimetype))
  );
  res.json({ urls });
});
```

---

## Q2. (Beginner) How do you upload files to AWS S3 from Node.js?

```js
const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { randomUUID } = require('crypto');

const s3 = new S3Client({ region: process.env.AWS_REGION });
const BUCKET = process.env.S3_BUCKET;

async function uploadToS3(buffer, filename, mimetype) {
  const key = `uploads/${Date.now()}-${randomUUID()}-${filename}`;

  await s3.send(new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    Body: buffer,
    ContentType: mimetype,
    // Optional: make publicly readable via CloudFront
    // ACL: 'public-read',
  }));

  return `https://${BUCKET}.s3.amazonaws.com/${key}`;
}

// Generate pre-signed URL for direct client upload (skip backend)
async function getUploadUrl(filename, mimetype) {
  const key = `uploads/${Date.now()}-${randomUUID()}-${filename}`;
  const command = new PutObjectCommand({
    Bucket: BUCKET,
    Key: key,
    ContentType: mimetype,
  });
  const url = await getSignedUrl(s3, command, { expiresIn: 3600 }); // 1 hour
  return { url, key };
}
```

---

## Q3. (Beginner) What is the difference between storing files in the database vs object storage?

| | **Database (BLOB)** | **Object Storage (S3)** |
|---|---|---|
| Cost | Expensive (DB storage $) | Cheap ($0.023/GB/month on S3) |
| Scalability | Limited by DB size | Virtually unlimited |
| Performance | Slows down DB queries | Optimized for file serving |
| Backup | Included in DB backup | Separate backup/versioning |
| CDN | Not possible | Easy (CloudFront, CloudFlare) |
| Transactions | Can be in same transaction | Separate from DB transaction |
| Best for | Small config files (<1KB) | All user uploads, media |

**Answer**: Always use object storage for user uploads. Store the URL/key in the database, not the file itself. The only exception: tiny config blobs (<1KB) where transactional consistency with other data matters.

---

## Q4. (Beginner) How do you validate uploaded files (type, size, content)?

```js
const fileType = require('file-type');

async function validateFile(buffer, expectedTypes = ['image/jpeg', 'image/png', 'image/webp']) {
  // 1. Check file size
  if (buffer.length > 10 * 1024 * 1024) {
    throw new AppError(400, 'FILE_TOO_LARGE', 'File must be under 10MB');
  }

  // 2. Check REAL file type (not just extension — extensions can be faked)
  const type = await fileType.fromBuffer(buffer);
  if (!type || !expectedTypes.includes(type.mime)) {
    throw new AppError(400, 'INVALID_FILE_TYPE', `Allowed types: ${expectedTypes.join(', ')}`);
  }

  // 3. Check for common attack patterns
  const header = buffer.toString('utf8', 0, 100);
  if (header.includes('<?php') || header.includes('<script') || header.includes('#!/')) {
    throw new AppError(400, 'MALICIOUS_FILE', 'File contains suspicious content');
  }

  return { mime: type.mime, ext: type.ext };
}

// Usage
app.post('/upload', upload.single('file'), async (req, res) => {
  const { mime, ext } = await validateFile(req.file.buffer);
  // Safe to process...
});
```

**Answer**: Never trust the file extension or Content-Type header from the client — they can be spoofed. Always check the actual file content (magic bytes) using `file-type`. Also scan for embedded scripts and enforce size limits.

---

## Q5. (Beginner) How do you serve files securely (pre-signed URLs)?

```js
// DON'T: serve files through your Node.js server (wastes CPU/bandwidth)
app.get('/files/:key', async (req, res) => {
  const stream = s3.getObject({ Bucket: BUCKET, Key: req.params.key });
  stream.Body.pipe(res); // Your server becomes a file proxy — doesn't scale
});

// DO: generate pre-signed URLs (client downloads directly from S3/CDN)
app.get('/api/files/:id/download-url', auth, async (req, res) => {
  const file = await File.findById(req.params.id);
  if (!file) return res.status(404).json({ error: 'File not found' });

  // Check authorization
  if (file.userId !== req.user.id && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' });
  }

  const command = new GetObjectCommand({ Bucket: BUCKET, Key: file.s3Key });
  const url = await getSignedUrl(s3, command, {
    expiresIn: 3600, // URL valid for 1 hour
  });

  res.json({ url, expiresIn: 3600 });
});
```

**Answer**: Pre-signed URLs let the client download directly from S3 — your server doesn't touch the file data. This scales infinitely and costs nothing in server resources. The URL is temporary and can include auth checks.

---

## Q6. (Intermediate) How do you handle large file uploads with streaming (no memory buffering)?

**Scenario**: User uploads a 2GB video. Loading it entirely into memory would crash your server.

```js
const { Upload } = require('@aws-sdk/lib-storage');
const Busboy = require('busboy');

app.post('/api/upload/large', auth, (req, res) => {
  const busboy = Busboy({
    headers: req.headers,
    limits: { fileSize: 2 * 1024 * 1024 * 1024 }, // 2GB
  });

  busboy.on('file', async (fieldname, fileStream, { filename, mimeType }) => {
    const key = `videos/${req.user.id}/${Date.now()}-${filename}`;

    try {
      // Stream directly to S3 — never buffered in memory
      const upload = new Upload({
        client: s3,
        params: {
          Bucket: BUCKET,
          Key: key,
          Body: fileStream,         // readable stream piped directly
          ContentType: mimeType,
        },
        queueSize: 4,              // parallel upload parts
        partSize: 10 * 1024 * 1024, // 10MB parts (S3 multipart)
      });

      upload.on('httpUploadProgress', (progress) => {
        console.log(`Upload progress: ${progress.loaded}/${progress.total}`);
      });

      await upload.done();

      res.json({ key, url: `https://${BUCKET}.s3.amazonaws.com/${key}` });
    } catch (err) {
      res.status(500).json({ error: 'Upload failed' });
    }
  });

  req.pipe(busboy);
});
```

**Answer**: Use streaming (Busboy + S3 multipart upload) for large files. The file data flows from the client through the server to S3 without ever being fully loaded into memory. Memory usage stays constant regardless of file size.

---

## Q7. (Intermediate) How do you implement direct client-to-S3 uploads (pre-signed POST)?

**Scenario**: Skip the backend entirely for uploads. Client uploads directly to S3.

```js
// Backend: generate pre-signed upload URL
const { createPresignedPost } = require('@aws-sdk/s3-presigned-post');

app.post('/api/upload/presign', auth, async (req, res) => {
  const { filename, contentType } = req.body;
  const key = `uploads/${req.user.id}/${Date.now()}-${filename}`;

  const { url, fields } = await createPresignedPost(s3, {
    Bucket: BUCKET,
    Key: key,
    Conditions: [
      ['content-length-range', 0, 50 * 1024 * 1024], // max 50MB
      ['eq', '$Content-Type', contentType],
    ],
    Fields: { 'Content-Type': contentType },
    Expires: 300, // 5 minutes
  });

  // Save file record to DB (pending status)
  await File.create({ userId: req.user.id, key, filename, status: 'pending' });

  res.json({ url, fields, key });
});

// Client-side: upload directly to S3
async function uploadFile(file) {
  // 1. Get pre-signed URL from backend
  const { url, fields, key } = await fetch('/api/upload/presign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: file.name, contentType: file.type }),
  }).then(r => r.json());

  // 2. Upload directly to S3
  const formData = new FormData();
  Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
  formData.append('file', file);

  await fetch(url, { method: 'POST', body: formData });

  // 3. Confirm upload
  await fetch('/api/upload/confirm', {
    method: 'POST',
    body: JSON.stringify({ key }),
  });
}
```

**Answer**: Pre-signed POST lets the client upload directly to S3 — zero bandwidth through your server. Backend only generates the signed URL and records the file metadata. Best for large files (video, documents).

---

## Q8. (Intermediate) How do you process uploaded images (resize, compress)?

```js
const sharp = require('sharp');

async function processImage(buffer, options = {}) {
  const { width = 800, height = 800, quality = 80, format = 'webp' } = options;

  const processed = await sharp(buffer)
    .resize(width, height, { fit: 'inside', withoutEnlargement: true })
    .toFormat(format, { quality })
    .toBuffer();

  return processed;
}

// Generate multiple sizes for responsive images
async function generateThumbnails(buffer, key) {
  const sizes = [
    { name: 'thumb', width: 150, height: 150 },
    { name: 'medium', width: 600, height: 600 },
    { name: 'large', width: 1200, height: 1200 },
  ];

  const results = await Promise.all(sizes.map(async (size) => {
    const processed = await sharp(buffer)
      .resize(size.width, size.height, { fit: 'cover' })
      .webp({ quality: 80 })
      .toBuffer();

    const sizeKey = key.replace(/\.[^.]+$/, `-${size.name}.webp`);
    await uploadToS3(processed, sizeKey, 'image/webp');
    return { size: size.name, key: sizeKey };
  }));

  return results;
}

// Usage in upload handler
app.post('/api/avatar', auth, upload.single('avatar'), async (req, res) => {
  await validateFile(req.file.buffer, ['image/jpeg', 'image/png', 'image/webp']);

  const key = `avatars/${req.user.id}/${Date.now()}`;
  const thumbnails = await generateThumbnails(req.file.buffer, key);

  await User.update(req.user.id, {
    avatarThumb: thumbnails.find(t => t.size === 'thumb').key,
    avatarMedium: thumbnails.find(t => t.size === 'medium').key,
    avatarLarge: thumbnails.find(t => t.size === 'large').key,
  });

  res.json({ thumbnails });
});
```

---

## Q9. (Intermediate) How do you handle CSV/Excel file imports?

```js
const csv = require('csv-parser');
const { Readable } = require('stream');

app.post('/api/import/users', auth, upload.single('file'), async (req, res) => {
  const results = [];
  const errors = [];
  let lineNumber = 0;

  const stream = Readable.from(req.file.buffer);

  await new Promise((resolve, reject) => {
    stream
      .pipe(csv())
      .on('data', (row) => {
        lineNumber++;
        // Validate each row
        const { error, value } = userImportSchema.validate(row);
        if (error) {
          errors.push({ line: lineNumber, error: error.message, data: row });
        } else {
          results.push(value);
        }
      })
      .on('end', resolve)
      .on('error', reject);
  });

  if (errors.length > 0 && errors.length > results.length * 0.1) {
    return res.status(400).json({
      error: 'Too many errors in file',
      errorCount: errors.length,
      sampleErrors: errors.slice(0, 10),
    });
  }

  // Batch insert valid rows
  const BATCH_SIZE = 1000;
  let imported = 0;
  for (let i = 0; i < results.length; i += BATCH_SIZE) {
    const batch = results.slice(i, i + BATCH_SIZE);
    await db('users').insert(batch).onConflict('email').ignore();
    imported += batch.length;
  }

  res.json({ imported, errors: errors.length, sampleErrors: errors.slice(0, 5) });
});
```

---

## Q10. (Intermediate) How do you implement file download with streaming?

```js
// Stream large file from S3 to client
app.get('/api/export/orders', auth, async (req, res) => {
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename="orders.csv"');

  // Write CSV header
  res.write('id,customer,total,status,date\n');

  // Stream from database in batches
  const BATCH_SIZE = 1000;
  let offset = 0;
  let hasMore = true;

  while (hasMore) {
    const orders = await db('orders')
      .orderBy('created_at', 'desc')
      .offset(offset)
      .limit(BATCH_SIZE);

    if (orders.length < BATCH_SIZE) hasMore = false;
    offset += orders.length;

    // Write batch to response
    for (const order of orders) {
      res.write(`${order.id},${order.customer_name},${order.total},${order.status},${order.created_at}\n`);
    }
  }

  res.end();
});

// Stream from S3
app.get('/api/files/:key', auth, async (req, res) => {
  const command = new GetObjectCommand({ Bucket: BUCKET, Key: req.params.key });
  const { Body, ContentType, ContentLength } = await s3.send(command);

  res.setHeader('Content-Type', ContentType);
  res.setHeader('Content-Length', ContentLength);
  Body.pipe(res); // stream directly
});
```

---

## Q11. (Intermediate) How do you implement resumable uploads?

```js
// Resumable upload using tus protocol
const { Server } = require('@tus/server');
const { S3Store } = require('@tus/s3-store');

const tusServer = new Server({
  path: '/uploads',
  datastore: new S3Store({
    s3ClientConfig: { region: process.env.AWS_REGION },
    bucket: BUCKET,
    partSize: 8 * 1024 * 1024, // 8MB parts
  }),
  maxSize: 5 * 1024 * 1024 * 1024, // 5GB
  onUploadFinish: async (req, res, upload) => {
    // Post-processing after upload completes
    await File.create({
      key: upload.id,
      size: upload.size,
      metadata: upload.metadata,
    });
  },
});

app.all('/uploads/*', (req, res) => tusServer.handle(req, res));
```

**Answer**: The tus protocol (tus.io) provides resumable uploads. If the connection drops at 50%, the client resumes from byte 50% — not from the beginning. Essential for large files on unreliable networks (mobile).

---

## Q12. (Intermediate) How do you implement file versioning and lifecycle management?

```js
// S3 versioning — keep all versions of a file
// Enable: aws s3api put-bucket-versioning --bucket my-bucket --versioning-configuration Status=Enabled

// Application-level versioning
app.put('/api/documents/:id', auth, upload.single('file'), async (req, res) => {
  const doc = await Document.findById(req.params.id);

  // Save current version to history
  await DocumentVersion.create({
    documentId: doc.id,
    version: doc.version,
    s3Key: doc.s3Key,
    modifiedBy: req.user.id,
    modifiedAt: new Date(),
  });

  // Upload new version
  const newKey = `documents/${doc.id}/v${doc.version + 1}-${req.file.originalname}`;
  await uploadToS3(req.file.buffer, newKey, req.file.mimetype);

  // Update document record
  await Document.update(doc.id, {
    s3Key: newKey,
    version: doc.version + 1,
    lastModifiedBy: req.user.id,
  });

  res.json({ version: doc.version + 1 });
});

// S3 lifecycle rules (auto-cleanup)
// aws s3api put-bucket-lifecycle-configuration:
// - Move to Glacier after 90 days
// - Delete old versions after 365 days
// - Delete incomplete multipart uploads after 7 days
```

---

## Q13. (Advanced) How do you implement virus scanning for uploaded files?

```js
const NodeClam = require('clamscan');

const clam = await new NodeClam().init({
  clamdscan: { socket: '/var/run/clamav/clamd.ctl' },
  preference: 'clamdscan',
});

async function scanFile(buffer) {
  const { isInfected, viruses } = await clam.scanBuffer(buffer);
  if (isInfected) {
    throw new AppError(400, 'MALWARE_DETECTED', `Malware detected: ${viruses.join(', ')}`);
  }
}

// Upload flow with virus scanning
app.post('/api/upload', auth, upload.single('file'), async (req, res) => {
  // 1. Validate file type
  await validateFile(req.file.buffer);

  // 2. Scan for viruses
  await scanFile(req.file.buffer);

  // 3. Upload to quarantine bucket first
  const quarantineKey = `quarantine/${randomUUID()}`;
  await uploadToS3(req.file.buffer, quarantineKey, req.file.mimetype);

  // 4. Move to production bucket after scan passes
  const finalKey = `uploads/${req.user.id}/${req.file.originalname}`;
  await s3.send(new CopyObjectCommand({
    Bucket: BUCKET,
    CopySource: `${BUCKET}/${quarantineKey}`,
    Key: finalKey,
  }));
  await s3.send(new DeleteObjectCommand({ Bucket: BUCKET, Key: quarantineKey }));

  res.json({ key: finalKey });
});
```

---

## Q14. (Advanced) How do you implement a CDN for serving uploaded files?

```js
// CloudFront distribution in front of S3
// Users download from CDN (edge servers worldwide) instead of S3 directly

// Generate CloudFront signed URL for private content
const { getSignedUrl } = require('@aws-sdk/cloudfront-signer');

function getCdnUrl(key, expiresInSeconds = 3600) {
  return getSignedUrl({
    url: `https://${process.env.CLOUDFRONT_DOMAIN}/${key}`,
    keyPairId: process.env.CLOUDFRONT_KEY_PAIR_ID,
    privateKey: process.env.CLOUDFRONT_PRIVATE_KEY,
    dateLessThan: new Date(Date.now() + expiresInSeconds * 1000).toISOString(),
  });
}

app.get('/api/files/:id', auth, async (req, res) => {
  const file = await File.findById(req.params.id);
  const url = getCdnUrl(file.s3Key);
  res.json({ url });
});

// Cache-Control headers for different file types
// Images: Cache-Control: public, max-age=31536000 (1 year, immutable)
// Documents: Cache-Control: private, max-age=3600 (1 hour)
// User-specific: Cache-Control: private, no-cache
```

---

## Q15. (Advanced) How do you handle file uploads in a microservices architecture?

```
Architecture:
Client → API Gateway → Upload Service → S3
                     → Notification: "file uploaded"
                     → Processing Service (resize, transcode, OCR)
                     → Notification: "file processed"
                     → Client receives processed file URL
```

```js
// Upload Service: accepts file, stores in S3, publishes event
app.post('/upload', auth, async (req, res) => {
  const key = await storeInS3(req);

  await kafka.publish('file-events', {
    type: 'FILE_UPLOADED',
    data: { key, userId: req.user.id, contentType: req.file.mimetype },
  });

  res.json({ key, status: 'processing' });
});

// Processing Service: listens for events, processes files
consumer.on('FILE_UPLOADED', async (event) => {
  const { key, contentType } = event.data;

  if (contentType.startsWith('image/')) {
    await generateThumbnails(key);
  } else if (contentType === 'application/pdf') {
    await extractText(key); // OCR
  } else if (contentType.startsWith('video/')) {
    await transcodeVideo(key); // FFmpeg
  }

  await kafka.publish('file-events', {
    type: 'FILE_PROCESSED',
    data: { key, userId: event.data.userId },
  });
});
```

---

## Q16. (Advanced) How do you implement chunked file uploads with progress tracking?

```js
// Server: handle chunked uploads
const chunks = new Map(); // uploadId → { chunks: [], metadata }

app.post('/api/upload/init', auth, async (req, res) => {
  const uploadId = randomUUID();
  const totalChunks = Math.ceil(req.body.fileSize / (5 * 1024 * 1024)); // 5MB chunks

  chunks.set(uploadId, {
    userId: req.user.id,
    filename: req.body.filename,
    totalChunks,
    receivedChunks: new Set(),
    s3Parts: [],
  });

  // Start S3 multipart upload
  const { UploadId } = await s3.send(new CreateMultipartUploadCommand({
    Bucket: BUCKET,
    Key: `uploads/${req.user.id}/${uploadId}-${req.body.filename}`,
  }));

  chunks.get(uploadId).s3UploadId = UploadId;
  res.json({ uploadId, totalChunks });
});

app.post('/api/upload/chunk/:uploadId', auth, upload.single('chunk'), async (req, res) => {
  const { uploadId } = req.params;
  const chunkIndex = parseInt(req.body.chunkIndex);
  const state = chunks.get(uploadId);

  // Upload chunk as S3 part
  const { ETag } = await s3.send(new UploadPartCommand({
    Bucket: BUCKET,
    Key: `uploads/${state.userId}/${uploadId}-${state.filename}`,
    UploadId: state.s3UploadId,
    PartNumber: chunkIndex + 1,
    Body: req.file.buffer,
  }));

  state.receivedChunks.add(chunkIndex);
  state.s3Parts.push({ PartNumber: chunkIndex + 1, ETag });

  const progress = state.receivedChunks.size / state.totalChunks;

  if (state.receivedChunks.size === state.totalChunks) {
    // All chunks received — complete multipart upload
    await s3.send(new CompleteMultipartUploadCommand({
      Bucket: BUCKET,
      Key: `uploads/${state.userId}/${uploadId}-${state.filename}`,
      UploadId: state.s3UploadId,
      MultipartUpload: { Parts: state.s3Parts.sort((a, b) => a.PartNumber - b.PartNumber) },
    }));
    chunks.delete(uploadId);
  }

  res.json({ progress, complete: state.receivedChunks.size === state.totalChunks });
});
```

---

## Q17. (Advanced) How do you handle file storage costs and optimization?

```js
// S3 storage tiers and lifecycle
// Standard: $0.023/GB — frequently accessed files
// Infrequent Access: $0.0125/GB — files accessed < 1x/month
// Glacier: $0.004/GB — archival, retrieval takes minutes-hours

// Lifecycle policy:
// 1. User uploads → Standard (first 30 days)
// 2. After 30 days → Infrequent Access
// 3. After 90 days → Glacier Deep Archive
// 4. After 365 days → Delete

// Track storage usage per user
async function getUserStorageUsage(userId) {
  const files = await db('files').where({ user_id: userId, deleted_at: null });
  const totalBytes = files.reduce((sum, f) => sum + f.size_bytes, 0);
  return {
    totalBytes,
    totalMB: (totalBytes / 1024 / 1024).toFixed(2),
    fileCount: files.length,
    limit: getUserStorageLimit(userId), // based on plan
  };
}

// Enforce storage limits
app.post('/api/upload', auth, async (req, res) => {
  const usage = await getUserStorageUsage(req.user.id);
  if (usage.totalBytes + req.file.size > usage.limit) {
    return res.status(413).json({ error: 'Storage limit exceeded', usage });
  }
  // ... proceed with upload
});
```

---

## Q18. (Advanced) How do you implement image optimization pipeline?

```js
// Automatic image optimization on upload
async function optimizeImage(buffer, key) {
  const metadata = await sharp(buffer).metadata();

  // Generate optimized versions
  const variants = [
    { suffix: 'original', transform: sharp(buffer).rotate() }, // auto-rotate only
    { suffix: 'webp', transform: sharp(buffer).webp({ quality: 80 }) },
    { suffix: 'avif', transform: sharp(buffer).avif({ quality: 65 }) },
    { suffix: 'thumb-200', transform: sharp(buffer).resize(200, 200, { fit: 'cover' }).webp({ quality: 75 }) },
    { suffix: 'medium-800', transform: sharp(buffer).resize(800, 800, { fit: 'inside' }).webp({ quality: 80 }) },
  ];

  const results = {};
  await Promise.all(variants.map(async ({ suffix, transform }) => {
    const processed = await transform.toBuffer();
    const variantKey = key.replace(/\.[^.]+$/, `-${suffix}.webp`);
    await uploadToS3(processed, variantKey, 'image/webp');
    results[suffix] = { key: variantKey, size: processed.length };
  }));

  return results;
}

// Serve the right variant based on client hints
app.get('/api/images/:id', async (req, res) => {
  const accept = req.headers.accept || '';
  const width = parseInt(req.query.w) || 800;

  let variant = 'medium-800';
  if (width <= 200) variant = 'thumb-200';
  if (accept.includes('image/avif')) variant = variant.replace('webp', 'avif');

  const url = getCdnUrl(`${imageKey}-${variant}.webp`);
  res.redirect(302, url);
});
```

---

## Q19. (Advanced) How do you handle file uploads in serverless (Lambda)?

```js
// Lambda has 6MB payload limit → can't handle large uploads directly

// Pattern 1: Pre-signed URL (recommended)
// API Gateway → Lambda (generate presigned URL) → Client uploads to S3 directly
exports.handler = async (event) => {
  const { filename, contentType } = JSON.parse(event.body);
  const key = `uploads/${event.requestContext.authorizer.userId}/${Date.now()}-${filename}`;

  const url = await getSignedUrl(s3, new PutObjectCommand({
    Bucket: BUCKET, Key: key, ContentType: contentType,
  }), { expiresIn: 3600 });

  return { statusCode: 200, body: JSON.stringify({ url, key }) };
};

// Pattern 2: S3 trigger for post-processing
// S3 event → Lambda → process file
exports.processUpload = async (event) => {
  const bucket = event.Records[0].s3.bucket.name;
  const key = event.Records[0].s3.object.key;

  const { Body } = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
  const buffer = await streamToBuffer(Body);

  // Process (resize, scan, etc.)
  const thumbnails = await generateThumbnails(buffer, key);

  // Update database
  await db('files').where({ s3_key: key }).update({ status: 'processed', thumbnails });
};
```

---

## Q20. (Advanced) Senior red flags in file handling.

**Answer**:

1. **Storing files on local filesystem** — lost on redeploy, can't scale horizontally
2. **No file type validation** — accepting any file type leads to security vulnerabilities
3. **Trusting file extension** — checking `.jpg` instead of actual content type (magic bytes)
4. **Loading entire file into memory** — OOM for large files. Use streaming.
5. **No virus scanning** — uploaded files can contain malware
6. **No file size limits** — 10GB upload crashes server or fills disk
7. **Serving files through Node.js** — Node becomes a file proxy instead of using S3/CDN
8. **No pre-signed URLs** — files publicly accessible or requiring backend proxy
9. **No storage quotas per user** — one user uploads 1TB and costs skyrocket
10. **No cleanup of orphaned files** — files in S3 with no DB reference → wasted money

**Senior interview answer**: "I use pre-signed URLs for direct S3 upload/download, validate file content (not just extension) with magic byte checking, implement virus scanning with ClamAV, generate responsive image variants with Sharp, stream large files without buffering in memory, serve through CloudFront CDN with signed URLs, and enforce per-user storage quotas. Files never touch the application server's filesystem."
