# Spancle - Multi-Tenant SaaS Venue Booking Platform

## Original Problem Statement
Create a full-fledged multi-tenant SaaS application for venue booking ("Spancle"). Use the 5 elements of earth for the color scheme. Needs to be mobile responsive. Provide database structure export for live migration. Features must include multi-gateway payment integrations (Razorpay, Stripe, PayPal, Skrill) and email notifications (Resend). Must be production-ready and deployable on an Ubuntu server.

## Tech Stack
- Frontend: React.js (CRA), Tailwind CSS, Phosphor Icons, Framer Motion
- Backend: FastAPI, Python 3.11+ (lifespan context manager)
- Database: MongoDB (Motor async driver)
- Architecture: Modular backend (routes/, shared modules), multi-tenant via tenant_id

## Backend Architecture
```
/app/backend/
├── server.py          (Entry point, lifespan, CORS, router imports)
├── database.py, config.py, auth.py, models.py, email_service.py
├── routes/ (auth, tenants, venues, courts, bookings, customers, payments, analytics, public, qr)
```

## What's Been Implemented (All Complete)
- Full auth: login, register, self-serve tenant registration, forgot/reset password, brute force protection
- Super admin global view: courts, customers, pricing visible across all tenants with optional ?tenant_id filter
- Tenant Dashboard: Overview, Venues, Courts, Bookings, Tenants
- Public booking pages (path + subdomain routing)
- Multi-gateway payments (Stripe, Razorpay, PayPal, Skrill)
- Email notifications via Resend
- Analytics charts + CSV exports
- Subscription billing tiers, QR codes, bulk import, recurring bookings
- Mobile responsive, Ubuntu deployment script, full Spancle branding
- Backend modular refactoring + FastAPI lifespan migration

## Backlog
- P3: Frontend "All Tenants" view on Courts tab for super_admin (backend supports it, UI requires venue selection)
- P3: Mobile App (deferred until maturity)
