# Technical Placement & Interview Preparation Guide
## Project: Real-Time Cloud-Based Event Planning & RSVP Tracker

---

### Question 1: Explain your project.
**Answer:**
"I developed a Real-Time Cloud-Based Event Planning & RSVP Tracker designed to solve the chaos of spreadsheets and uncoordinated event invitations. Organizers can create and manage events, set capacity constraints, generate cryptographic tokenized QR invites, and track attendance on a live telemetry dashboard. Attendees can respond with Going, Maybe, or Not Going, either authenticated or frictionlessly via unique invite links. The backend is built with FastAPI and SQLAlchemy using ACID transactions with row-level locking to prevent race conditions during concurrent RSVPs. It incorporates WebSockets for sub-second live dashboard updates without polling, an automated FIFO waitlist auto-promotion engine, in-app notifications, on-site QR ticket check-ins, and a scikit-learn Logistic Regression attendance predictor. The entire application is containerized with Docker and verified with a 25-scenario automated test suite."

---

### Question 2: What does “real-time” mean in your project, and how is it implemented?
**Answer:**
"In this project, real-time means push-based state synchronization. When an attendee anywhere in the world clicks 'Going' or updates their RSVP, connected organizer dashboards update their counters immediately without requiring a manual page refresh. Rather than having the browser poll the server every few seconds—which wastes bandwidth and server CPU—I implemented a persistent WebSocket connection managed by a FastAPI `ConnectionManager`. When an RSVP mutation commits to the database, a JSON payload is broadcast across all active WebSocket connections in that event's room."

---

### Question 3: Why did you use cloud computing for this project?
**Answer:**
"Cloud computing enables centralized data integrity across heterogeneous client devices (organizer laptops, attendee smartphones, check-in kiosks). By hosting the application and database in the cloud, all clients query a single source of truth. Furthermore, cloud architectures provide scalable elasticity to handle sudden registration spikes during popular event launches, PaaS deployment options (like GCP Cloud Run and Render), and containerized portability via Docker."

---

### Question 4: How did you prevent duplicate RSVPs?
**Answer:**
"Duplicate RSVPs are prevented at both the application and database layers. In the relational database schema, I enforced a composite unique constraint on `(event_id, user_id)` for registered users, and a unique constraint on `invite_token` for guest invitees. In the business logic, when a user submits an RSVP for an event they've already responded to, the system performs an update mutation on their existing record rather than creating a duplicate row, ensuring counts remain strictly accurate."

---

### Question 5: How did you handle event capacity, and how do you prevent overbooking?
**Answer:**
"Every event defines a `maximum_capacity`. When an RSVP with status `GOING` arrives, the backend computes whether `current_going + requested_seats <= maximum_capacity`. To make this concurrency-safe against simultaneous requests, this check and the subsequent seat allocation are executed inside an atomic database transaction. In databases supporting row locking like PostgreSQL, I apply `with_for_update()`, serializing concurrent transactions so no two requests can read the same remaining seat count simultaneously."

---

### Question 6: What is a race condition, and how could it happen in an RSVP system?
**Answer:**
"A race condition occurs when multiple threads or processes concurrently read and manipulate shared state, and the outcome depends on the non-deterministic order of execution. For example, if an event has a capacity of 100 and currently has 99 attendees, 1 seat remains. If User A and User B both submit 'Going' at the same millisecond, a naive implementation without transaction isolation might allow both threads to read `current_going = 99`. Both threads see that 99 < 100, approve the request, and increment the count to 101, violating the physical capacity limit. I prevent this by locking the event row during the transaction, guaranteeing serializability."

---

### Question 7: What is the difference between REST APIs and WebSockets in your application?
**Answer:**
"REST APIs are stateless and follow a request-response model over HTTP/HTTPS. They are ideal for transactional operations such as authenticating users, creating events, issuing invites, and submitting RSVPs where request validation and HTTP status codes are necessary. In contrast, WebSockets provide a persistent, full-duplex TCP connection. WebSockets are used for push notifications and live metrics broadcasting, allowing the server to proactively send data to connected clients as soon as state changes without waiting for a request."

---

### Question 8: How would you scale this architecture to support 100,000 users attempting to RSVP within 5 minutes?
**Answer:**
"To handle a flash registration spike of 100,000 users:
1. **Frontend & Static Ingress:** Distribute static assets globally using a CDN (CloudFront / Cloudflare).
2. **Horizontal Scaling:** Deploy stateless backend containers across an autoscaling group or serverless platform behind a load balancer.
3. **Queueing Architecture:** Decouple incoming RSVP requests by pushing them into a high-throughput message queue like Apache Kafka or AWS SQS to smooth out database write spikes.
4. **Caching & Hotspot Reduction:** Cache static event details in Redis with short TTLs to absorb read traffic.
5. **WebSocket Scaling:** Use Redis Pub/Sub to broadcast WebSocket messages across multiple server nodes so that dashboard clients connected to different server instances still receive updates."

---

### Question 9: How did you test your project?
**Answer:**
"I developed an automated test suite with PyTest containing 25 distinct verification scenarios. The suite validates user registration, duplicate email rejection, JWT authentication, organizer role permissions, event CRUD, capacity enforcement, registration deadline expiration, and on-site QR ticket verification. Most importantly, I wrote test cases simulating simultaneous requests for the last available seat to empirically confirm that race conditions are prevented and that excess attendees are cleanly routed to the FIFO waitlist."

---

### Question 10: How can this project be improved in the future?
**Answer:**
"Future improvements include:
1. **Biometric & Apple Wallet Tickets:** Generating native PKPass files with NFC badges.
2. **Payment Gateway Integration:** Integrating Stripe or Razorpay for ticketed events.
3. **Advanced AI Recommendations:** Leveraging vector embeddings to recommend events to attendees based on past interests.
4. **Geographic Check-ins:** Utilizing geofencing to auto-check-in attendees when they enter the venue perimeter."
