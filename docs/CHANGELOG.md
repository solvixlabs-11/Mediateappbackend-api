# Changelog - Mediate Healthcare MR App

## [Unreleased] - Phase 1: Authentication & Security (2026-09-30)

### Added
- **Database Schema**: Phase 1 tables in `mediate_mr_db`: `roles`, `permissions`, `role_permissions`, `users`, `manager_mr_assignments`, `refresh_tokens`, `audit_logs`, `files`.
- **Alembic Baseline**: Initial migration `411b81995e29_phase1_auth_users_baseline`.
- **Seeding Script**: Initial roles (`ADMIN`, `MANAGER`, `MR`), full permission matrix, default admin and demo personnel accounts (`mr@mediatehealthcare.com`, `manager@mediatehealthcare.com`, `admin@mediatehealthcare.com`).
- **Core Security**: Argon2 password hashing, JWT access token issuing (15m expiry), and SHA-256 hashed refresh tokens (30d expiry).
- **Session & Token Rotation**: Refresh token single-flight rotation with token family reuse breach detection.
- **Rate Limiting & Lockout**: 5 consecutive failed attempts trigger a 15-minute account lockout.
- **Audit Logging**: Recorded events for login success/failure, account lockout, logout, logout-all, and password change.
- **Auth Endpoints**: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`, `GET /auth/me`, `POST /auth/change-password`, `POST /auth/register`.
- **Testing**: 11 automated pytest tests passing with 100% coverage on auth lifecycles.
- **Mobile Integration**: OpenAPI schema synchronization, generated TypeScript types, `authApi` service, `useLogin` hook, `Input` UI component, session restore on app launch (`initializeAuth`), and interactive demo role quick-fill on `LoginScreen`.
