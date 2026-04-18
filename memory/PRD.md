# Spancle - Multi-Tenant SaaS Venue Booking Platform

## Original Problem Statement
Create a full-fledged multi-tenant SaaS application for venue booking ("Spancle"). Use the 5 elements of earth for the color scheme. Needs to be mobile responsive. Provide database structure export for live migration. Features must include multi-gateway payment integrations (Razorpay, Stripe, PayPal, Skrill) and email notifications (Resend). Must be production-ready and deployable on an Ubuntu server.

## User Personas
- **Super Admin**: Platform owner managing all tenants
- **Tenant Admin**: Venue owner managing their venues, courts, bookings
- **Customer (B2C)**: End user booking venue slots via public booking pages

## Core Requirements
- Multi-tenant architecture with tenant isolation via tenant_id
- User auth (JWT via HTTP-only cookies)
- Venue and Court management (CRUD)
- Booking calendar with time slot management
- Recurring bookings support
- Multi-gateway payments: Stripe, Razorpay, PayPal, Skrill
- Email notifications via Resend
- Analytics dashboard with charts
- CSV export for bookings and analytics
- Subscription billing tiers (Basic, Pro, Enterprise)
- Public customer booking pages
- QR code generation for venues
- Bulk import for venues
- Mobile responsive design
- Password reset / Forgot password flow

## Tech Stack
- Frontend: React.js (CRA), Tailwind CSS, Phosphor Icons, Framer Motion
- Backend: FastAPI, Python 3.11+
- Database: MongoDB (Motor async driver)
- Architecture: Modular backend (routes/, shared modules), multi-tenant via tenant_id

## Backend Architecture (Refactored Apr 18, 2026)
```
/app/backend/
├── server.py          (92 lines - App creation, CORS, startup, router imports)
├── database.py        (MongoDB connection)
├── config.py          (Environment variables, payment client init)
├── auth.py            (Password hashing, JWT, get_current_user)
├── models.py          (All Pydantic request models)
├── email_service.py   (Email HTML templates + send functions)
├── routes/
│   ├── auth.py        (register, login, logout, me, forgot/reset password)
│   ├── tenants.py     (Tenant CRUD + subscription plans)
│   ├── venues.py      (Venue CRUD + bulk import)
│   ├── courts.py      (Court CRUD)
│   ├── bookings.py    (Booking CRUD + recurring + cancellation)
│   ├── customers.py   (Customer CRUD)
│   ├── payments.py    (Stripe, Razorpay, PayPal, Skrill + webhooks)
│   ├── analytics.py   (Dashboard + charts + CSV exports)
│   ├── public.py      (Public endpoints - no auth)
│   └── qr.py          (QR code generation + pricing rules)
```

## What's Been Implemented (All Complete)
- Landing page with hero, features, pricing sections
- Login/Register with cookie-based auth
- Forgot Password / Password Reset flow (token-based via Resend email)
- Brute force protection (5 failed attempts = 15 min lockout)
- Tenant Dashboard: Overview, Venues, Courts, Bookings, Tenants
- Venue management with image cards
- Court management with venue selector
- Booking calendar with time slots
- Public booking pages for customers (path-based and subdomain-based)
- Subdomain routing (e.g., elite-sports.spancle.com)
- Multi-gateway payment integrations (Stripe, Razorpay, PayPal, Skrill)
- Email notifications via Resend
- Analytics charts (Revenue Trend, Court Occupancy)
- CSV export (Bookings, Analytics)
- Subscription billing tiers
- QR code generation
- Bulk venue import
- Recurring bookings
- Mobile responsive design
- Ubuntu 24.04 deployment script
- Full rebranding to Spancle (no Emergent references)
- Backend modular refactoring (server.py split into 17 clean files)

## Key Database Collections
users, tenants, venues, courts, bookings, customers, payment_transactions, pricing_rules, password_reset_tokens, login_attempts

## 3rd Party Integrations
- Stripe, Razorpay, PayPal, Skrill (payments - require user API keys)
- Resend (email notifications - requires user API key)

## Backlog
- P1: Mobile App functionality (deferred by user until maturity)
- P2: Super admin global view for courts/pricing/customers (currently filtered by tenant_id)
- P2: Migrate deprecated @app.on_event to FastAPI lifespan context manager
