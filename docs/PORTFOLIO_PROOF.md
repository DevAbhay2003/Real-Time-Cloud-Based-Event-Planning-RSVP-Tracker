# Portfolio Proof Strategy & Screenshot Verification Guide

---

## 1. 14-Day Development Log & Git Commit Milestones

| Day | Milestone Title | Key Files Created / Modified | Functionality Implemented | Git Commit Message |
| :---: | :--- | :--- | :--- | :--- |
| **Day 1** | System Scaffolding | `.gitignore`, `backend/config.py`, `requirements.txt` | Environment variable validation, Pydantic BaseSettings, project layout | `chore: setup project scaffolding, dependencies and settings configuration` |
| **Day 2** | Cloud Database Schema | `backend/database.py`, `backend/models.py` | SQLAlchemy ORM tables (Users, Events, RSVPs, Waitlist, Notifications) | `feat(database): implement SQLAlchemy database engine and concurrency-safe schema models` |
| **Day 3** | Authentication & RBAC | `cloud/auth_service.py`, `backend/routes/auth_routes.py` | Bcrypt hashing, JWT generation, Organizer vs Attendee role authorization | `feat(auth): implement role-based JWT authentication and registration routes` |
| **Day 4** | Event Management CRUD | `backend/routes/event_routes.py` | Event creation, date/time validation, deadline rules, organizer ownership check | `feat(events): add event CRUD operations with deadline and ownership authorization` |
| **Day 5** | Concurrency-Safe RSVP | `backend/services/rsvp_service.py`, `backend/routes/rsvp_routes.py` | Atomic capacity verification, row locking, duplicate prevention | `feat(rsvp): add concurrency-safe capacity check, FIFO waitlist promotion and token invites` |
| **Day 6** | Real-Time WebSockets | `realtime/realtime_service.py`, `backend/main.py` | WebSocket `ConnectionManager`, pub/sub broadcast room per event | `feat(realtime): implement WebSocket connection manager and live RSVP broadcast` |
| **Day 7** | FIFO Waitlist Engine | `backend/services/rsvp_service.py` | Automatic promotion of waitlist attendees when seats open up | `feat(rsvp): add concurrency-safe capacity check, FIFO waitlist promotion and token invites` |
| **Day 8** | Announcements & Fan-out | `backend/routes/announcement_routes.py`, `cloud/notification_service.py` | Organizer announcements with automated fan-out to registered attendees | `feat(notifications): add announcements with auto fan-out notifications and audit logging` |
| **Day 9** | Real-Time Telemetry UI | `frontend/src/pages/OrganizerDashboard.jsx`, `frontend/src/hooks/useEventRealtime.js` | Live KPI cards updating without page refresh via WebSocket | `feat(frontend): create live organizer telemetry dashboard with real-time counters` |
| **Day 10** | VIP Invites & Attendee Portal | `frontend/src/pages/AttendeeEvents.jsx`, `frontend/src/pages/PublicTokenRSVP.jsx` | 1-click RSVP buttons, cryptographic token invites with QR pass display | `feat(frontend): implement attendee discovery portal, frictionless public RSVP, and SPA routing` |
| **Day 11** | QR Camera Scanner Kiosk | `backend/routes/checkin_routes.py`, `frontend/src/pages/CheckinKiosk.jsx` | In-browser webcam QR scanning with duplicate check-in prevention | `feat(checkin): implement QR code generation and on-site check-in verification` |
| **Day 12** | AI Predictive Analytics | `analytics/attendance_model.py`, `backend/routes/analytics_routes.py` | Scikit-learn Logistic Regression attendance probability predictor | `feat(analytics): add real-time event analytics calculation and ML attendance predictor` |
| **Day 13** | Verification Test Suite | `tests/test_full_suite.py` | 25 automated unit, integration, and concurrency test scenarios | `feat(frontend & tests): complete React Vite frontend with real-time UI, and add 25 automated tests` |
| **Day 14** | DevOps & Documentation | `Dockerfile`, `docker-compose.yml`, `README.md`, `docs/*` | Multi-stage Docker build, CI workflow, academic report, interview preparation | `chore(devops): configure multi-stage Docker build, CI workflow, and free-tier cloud deployment` |

---

## 2. 28-Item Screenshot Checklist

Capture and store the following screenshots in `screenshots/` for capstone presentation and GitHub proof:

1. `01_project_structure.png` - Visual tree of backend, frontend, realtime, cloud, and test directories.
2. `02_cloud_architecture_diagram.png` - Render of Mermaid architecture flow.
3. `03_user_registration.png` - Attendee and Organizer registration form.
4. `04_jwt_auth_login.png` - Login page and Bearer token generation.
5. `05_organizer_dashboard_empty.png` - Organizer dashboard showing initial 0 counters.
6. `06_create_event_modal.png` - Modal with venue, date, capacity, and deadline inputs.
7. `07_published_event_card.png` - Event card displayed in published status.
8. `08_attendee_events_portal.png` - Attendee discovery portal with event listings.
9. `09_authenticated_rsvp_going.png` - Attendee clicking "Going" with confirmation feedback.
10. `10_organizer_live_counter_increment.png` - Live "Going" counter incrementing from 0 to 1 without refresh.
11. `11_multi_browser_split_screen.png` - Side-by-side view of Organizer and Attendee windows showing instant sync.
12. `12_frictionless_invite_qr.png` - VIP digital invitation with dynamic QR pass code.
13. `13_database_rsvp_unique_record.png` - SQLite/PostgreSQL table view showing unique `(event_id, user_id)`.
14. `14_capacity_reached_full_status.png` - Event status badge automatically switching to `FULL`.
15. `15_waitlist_queued.png` - Attendee placed on FIFO waitlist after capacity reaches limit.
16. `16_waitlist_auto_promotion.png` - Waitlisted attendee automatically promoted to `GOING` when another attendee cancels.
17. `17_organizer_announcement_dispatch.png` - Organizer sending announcement to attendees.
18. `18_attendee_notification_bell.png` - Attendee portal receiving the announcement alert.
19. `19_ai_attendance_scoring.png` - Attendance prediction widget displaying likelihood percentage.
20. `20_webcam_qr_checkin_success.png` - Kiosk webcam scanning attendee QR code with green success feedback.
21. `21_duplicate_checkin_rejected.png` - Kiosk rejecting duplicate scan with `ALREADY_CHECKED_IN` warning.
22. `22_unauthorized_action_403.png` - Network inspector showing 403 Forbidden on illegal event update.
23. `23_pytest_25_passed.png` - Terminal output displaying 25 passed test cases in green.
24. `24_fastapi_swagger_docs.png` - Interactive Swagger UI at `http://localhost:8000/docs`.
25. `25_docker_build_success.png` - Multi-stage container compilation logs.
26. `26_docker_compose_up.png` - Docker container running live on port 8000.
27. `27_github_actions_ci_pass.png` - Green checkmark on GitHub Actions pipeline run.
28. `28_github_repository_readme.png` - Polished GitHub repository landing page with badges.
