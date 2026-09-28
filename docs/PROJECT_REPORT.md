# Academic Capstone Project Report
## Title: Real-Time Cloud-Based Event Planning & RSVP Tracker

**Course:** Cloud Computing & Distributed Systems  
**Domain:** Cloud Architecture, Real-Time Systems, Database Concurrency, Machine Learning  

---

### 1. Abstract
In modern distributed computing, real-time coordination and concurrency control are paramount for web-scale applications. Traditional event coordination systems relying on asynchronous batch processing or static spreadsheets frequently fail during high-contention traffic spikes, resulting in overbooking, stale attendance reporting, and high operational friction. This project presents the design and implementation of a production-grade, distributed Cloud-Based Event Planning & RSVP Tracker. The architecture combines Python FastAPI, SQLAlchemy ORM, WebSockets, and React 18, demonstrating core cloud computing concepts including SaaS/PaaS virtualization, persistent bi-directional communication, atomic database transactions with row-level locking, automated FIFO waitlist promotion, and predictive machine learning. 

### 2. Introduction & Problem Statement
Event management platforms manage scarce physical resources (venue capacity) under high concurrency. During flash registration windows, thousands of requests compete for a limited pool of seats within seconds. Naive implementations suffer from race conditions where read-then-write checks lead to seat counts exceeding venue capacity. Furthermore, organizers require instant visual telemetry without degrading server performance through constant HTTP polling.

### 3. Objectives
1. **Centralized Cloud Tenancy:** Provide multi-tenant access with strict Role-Based Access Control (RBAC) separating Organizers, Attendees, and System Administrators.
2. **Concurrency-Safe Capacity Enforcement:** Guarantee that zero overbooking occurs under concurrent requests using database transaction isolation and row-level locks (`SELECT ... FOR UPDATE`).
3. **Reactive Real-Time Telemetry:** Employ WebSockets to push live RSVP state changes directly to connected dashboards with sub-second latency.
4. **Frictionless VIP Invites:** Provide unique tokenized URLs enabling guests to respond without mandatory pre-registration.
5. **On-Site QR Verification:** Enable in-browser camera-based QR code ticket scanning with duplicate scan rejection.
6. **Predictive Attendance AI:** Train and serve a machine learning model to estimate attendance probability based on historical behavioral metrics.

### 4. Cloud Computing Concepts Demonstrated
- **SaaS:** Cloud application delivered over HTTPS/WSS across any modern browser.
- **PaaS Deployment:** Configured for frictionless deployment on container clouds (GCP Cloud Run, Render, Fly.io).
- **Virtualization & Containerization:** Multi-stage Docker builds bundling Node.js production assets and slim Python runtimes.
- **Bi-directional WebSockets:** Push architecture reducing server network egress compared to repetitive polling.
- **ACID Transactions:** Atomicity, Consistency, Isolation, and Durability preserved during high-contention RSVP mutations.
- **Micro-service & Cloud Service Abstraction:** Decoupled modules for authentication, notification fan-out, and telemetry aggregation.

### 5. Architectural Design & Concurrency Handling
When an attendee submits a `GOING` response:
1. An atomic database transaction is initiated.
2. The event row is locked using `with_for_update()`.
3. If `current_going + (1 + plus_ones) <= maximum_capacity`, the seats are reserved and `current_going` is incremented.
4. If capacity is exhausted, the user is automatically queued into a FIFO `Waitlist` record.
5. When any existing confirmed attendee cancels or modifies their status to `NOT_GOING`, the database transaction immediately selects the earliest waitlist candidate (`ORDER BY joined_at ASC`) and promotes them to `GOING`, simultaneously dispatching an in-app notification.
6. Upon commit, the event's updated metrics are broadcast to all connected WebSocket subscribers in the event's room.

### 6. Results & Verification
The platform was subjected to 25 automated integration and concurrency scenarios:
- **Zero Race Conditions:** Under simulated concurrent requests for the final available seat, exactly 1 seat was granted and all surplus requests were diverted to the FIFO waitlist.
- **Real-Time Push Latency:** WebSocket notifications delivered in under 15ms locally.
- **Build & Artifact Performance:** React SPA production bundle compiled to 628 kB with full client-side routing and camera QR scanning.

### 7. Conclusion & Future Scope
The project demonstrates that by pairing modern cloud API frameworks with rigorous database transaction semantics and reactive WebSockets, developers can eliminate concurrency errors while providing responsive user experiences. Future work will integrate Amazon SNS for SMS notifications, WebAuthn for biometric logins, and distributed Redis pub/sub clusters for horizontal WebSocket scaling across multiple container instances.
