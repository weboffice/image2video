# PRD — Photo-to-Video Web App (React front, Python back)

## 1) Product summary

Create a single-page web application where users upload photos, pick a template, receive a short job **code**, and later open a dedicated **viewer page** to watch/download the rendered video. The system supports **multiple simultaneous uploads**, shows **upload progress**, and streams **processing status** until completion.

## 2) Goals & KPIs

* Time-to-video (p95): ≤ 120 s for ≤ 20 photos, 1080p template.
* Successful render rate: ≥ 99%.
* Upload success rate: ≥ 99.5%.
* Abandonment during upload: ≤ 10%.
* Average concurrent jobs supported per node: target and monitor (e.g., 200 SSE connections/node).

## 3) Users & scenarios

* **Creator**: uploads images, picks template, gets job code, revisits viewer page to watch/download.
* **Viewer**: opens a link or enters code to watch/download the finished video.
* **Operator** (internal): monitors queues, failures, retries.

## 4) Scope (MVP)

* Web-only, desktop and mobile browsers.
* Anonymous usage (no login) with server-generated **job code**.
* Templates: at least 3 prebuilt options (e.g., slideshow, zoom/pan, dynamic captions).
* Input: JPEG/PNG images; optional title and background music (MVP can use default track).
* Output: MP4, 1080p30, H.264 + AAC.
* Storage: object storage for inputs and final outputs.
* Realtime status: **Server-Sent Events (SSE)** stream for job status and progress.
* Job retention: assets and results kept for 7 days (configurable).

Out of scope (MVP): payments, user accounts, template editor, collaborative editing, subtitles generation.

## 5) UX flows

### 5.1 Uploader (single page)

1. User selects one or more photos (drag-and-drop and file picker).
2. App creates a **job** and displays the **code**.
3. Parallel, resumable uploads with per-file progress bars.
4. Template selector (radio or cards); default preselected.
5. CTA “Generate video” becomes enabled after all uploads complete.
6. On click: job transitions to “queued” then “processing”; user is redirected to the **viewer** page.

Empty/error states:

* Invalid file type/oversize → inline error next to file.
* Network errors → retry control per file.
* Upload completed but job fails later → viewer page shows failure message and retry action.

Accessibility:

* Keyboard navigation; focus states; ARIA live region for status updates.

### 5.2 Viewer

* Shows job code, template name, current **status** and global **progress**.
* If done: embedded HTML5 video player with “Download” button and file size.
* If failed: failure reason, “Report issue” and “Try again” (re-enqueue if assets still present).
* Sharing: copyable URL containing the job code.

## 6) Functional requirements

### 6.1 Job lifecycle

* States: created → uploading → queued → processing → done | error | expired.
* Transitions:

  * created on job creation.
  * uploading while files are being sent.
  * queued when user triggers processing.
  * processing once worker picks the job.
  * done when result is written and available at a public URL.
  * error on unrecoverable failure (store error code + message).
  * expired by retention policy.

### 6.2 Uploads

* Generate **pre-signed PUT URLs** for each file.
* Client uploads directly to object storage.
* Constraints:

  * Max files per job (MVP: 50).
  * Max file size (MVP: 20 MB).
  * Allowed MIME types: image/jpeg, image/png.
* Deduplicate by content hash within the same job (optional for MVP).

### 6.3 Templates

* Each template defines:

  * Input constraints (min/max images, aspect ratio handling).
  * Transition style and duration.
  * Music track policy (default, none, or user-supplied).
  * Output resolution and frame rate.
* Template catalog is served by the backend and cached on the client.

### 6.4 Processing (workers)

* Worker pulls job, downloads images, validates dimensions, orders frames, renders via FFmpeg/MoviePy or equivalent, uploads MP4, sets job to done with result URL.
* Report progress milestones: 0, 10, 25, 50, 75, 90, 100 (configurable).
* Retries: up to 3 automatic retries on transient errors; exponential backoff.
* Idempotency: reprocessing a job does not duplicate outputs; use deterministic output key.

### 6.5 Status streaming

* SSE endpoint per job streams events:

  * status (string state)
  * progress (0–100)
  * done (result URL)
  * error (code, message)
* Heartbeat comments at an interval to keep connections alive.
* Multiple viewers per job code supported.

### 6.6 Retrieval

* Viewer route accepts job code.
* If job is done: show video and download link.
* If job is processing: auto-subscribe to SSE, update UI live.
* If job unknown/expired: user-friendly message and option to create a new job.

### 6.7 Cleanup & retention

* Auto-expire jobs and delete assets after retention period.
* Garbage collect orphaned uploads from abandoned jobs.

## 7) Non-functional requirements

### 7.1 Performance

* First contentful paint for uploader ≤ 2 s on 4G mid-range device.
* Upload progress latency: visible update within 500 ms of browser event.
* SSE event delivery: ≤ 1 s end-to-end for status changes.
* Video availability after “done” event: immediate public read.

### 7.2 Scalability

* Horizontal scale for:

  * API nodes (stateless).
  * Workers (CPU-bound, autoscaled by queue depth).
* Object storage must support parallel PUTs and high egress.
* Queue/broker to decouple API and workers.

### 7.3 Reliability

* API availability ≥ 99.9%.
* At-least-once delivery of worker progress updates; client handles duplicates.
* Safe restarts: jobs persist in durable store.

### 7.4 Security & privacy

* All endpoints over HTTPS.
* Pre-signed URLs expire within 15 minutes.
* Result URLs are unguessable; optionally time-limited signed GETs.
* Basic DoS controls: file count/size limits, rate limiting on upload-URL creation.
* PII: images treated as user content; no third-party sharing; retention policy enforced.

### 7.5 Observability

* Structured logs with job code correlation.
* Metrics: queue depth, jobs started/completed/failed, render duration, worker CPU.
* Tracing for API → queue → worker → storage path.
* Alerts: spike in errors, rising render duration, stalled workers.

## 8) Architecture constraints

* Frontend: React SPA  with shadcn/ui.
* Backend: Python (FastAPI or similar).
* Realtime: SSE for downstream status (WebSocket optional future).
* Storage: S3-compatible object storage.
* Queue/broker: Redis, SQS, or similar managed service.
* CDN for result delivery (optional MVP; recommended for scale).

## 9) Data model (conceptual)

### Entities

* Job

  * code (unique)
  * templateId
  * state, progress, errorCode, errorMessage
  * createdAt, updatedAt, expiresAt
  * resultUrl
* Asset

  * jobCode (FK)
  * objectKey
  * originalFilename
  * contentType
  * sizeBytes
  * orderIndex
* Template

  * id, name, constraints, output specs, music policy

## 10) API surface (contracts, no code)

* Create job
  Method: POST
  Path: /api/jobs
  Request: templateId (optional)
  Response: code, status

* Get pre-signed upload URL
  Method: POST
  Path: /api/upload-url
  Request: filename, contentType, code
  Response: url (signed PUT), objectKey, publicUrl (for reference)

* Start processing
  Method: POST
  Path: /api/jobs/{code}/start
  Response: ok

* Job status stream
  Method: GET
  Path: /api/jobs/{code}/stream
  Response: text/event-stream with events: status, progress, done, error

* Worker progress push (internal, authenticated)
  Method: POST
  Path: /internal/jobs/{code}/push
  Body fields: status, progress, resultUrl, errorCode, errorMessage
  Response: ok

* Fetch job (polled fallback)
  Method: GET
  Path: /api/jobs/{code}
  Response: job fields (state, progress, resultUrl, etc.)

## 11) Validation rules

* Reject upload-URL requests if job not in created/uploading state.
* Enforce file type/size limits server-side and client-side.
* Validate templateId exists and constraints match provided media count.

## 12) Error taxonomy

* UPLOAD\_LIMIT\_EXCEEDED (too many files)
* FILE\_TOO\_LARGE
* UNSUPPORTED\_MEDIA\_TYPE
* TEMPLATE\_CONSTRAINT\_VIOLATION
* RENDER\_FAILED\_TRANSIENT (retryable)
* RENDER\_FAILED\_PERMANENT
* JOB\_NOT\_FOUND
* JOB\_EXPIRED

Each error carries a user message and an operator detail.

## 13) Privacy & compliance

* Consent banner that uploads may be processed to generate a video.
* Clear retention and deletion policy in UI and docs.
* Provide a “Delete my job now” action on viewer page.

## 14) Rollout plan

* Phase 1 (MVP): single region, ≤ 1080p, 3 templates, SSE, anonymous jobs, 7-day retention.
* Phase 2: authentication, template marketplace, custom music, captioning, e-mail notifications, CDN, WebSocket control channel.
* Phase 3: payments, team workspaces, watermark removal for paid users, 4K output.

## 15) Risks & mitigations

* Heavy CPU load during render → autoscale workers; queue-based backpressure; job concurrency caps.
* Large uploads on mobile → chunked uploads and resume; explicit limits and client compression hints.
* SSE blocked by proxies → polling fallback endpoint.
* Storage costs → lifecycle rules to transition or delete after retention.

## 16) Acceptance criteria (MVP)

* User can upload 1–50 photos, see per-file progress, start processing, and receive a playable MP4 on the viewer page.
* Refreshing the viewer page mid-process continues to show live status via SSE.
* Invalid files produce friendly inline errors without crashing the page.
* Jobs expire and assets are removed after the configured retention period.
* Operator dashboard (basic) can list jobs and see states and error counts (can be CLI or minimal admin page in MVP).

This PRD defines the functional behavior and technical expectations without implementation code, aligned with a React front and Python backend.
