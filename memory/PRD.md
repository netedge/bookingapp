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
- Subscription billing tiers (Free, Pro, Enterprise)
- Public customer booking pages
- QR code generation for venues
- Bulk import for venues
- Mobile responsive design
- Password reset / Forgot password flow

## Tech Stack
- Frontend: React.js (CRA), Tailwind CSS, Phosphor Icons, Framer Motion
- Backend: FastAPI, Python 3.11+
- Database: MongoDB (Motor async driver)
- Architecture: Monolithic MVP, multi-tenant via tenant_id

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
- Tenant "My Public Booking Links" section with copy-to-clipboard
- Subdomain routing (e.g., elite-sports.spancle.com auto-redirects to booking page)
- Multi-gateway payment integrations (Stripe, Razorpay, PayPal, Skrill)
- Email notifications via Resend
- Analytics charts (Revenue Trend, Court Occupancy)
- CSV export (Bookings, Analytics)
- Subscription billing tiers
- QR code generation
- Bulk venue import
- Recurring bookings
- Database structure documentation
- Mobile responsive design
- Public API endpoints (no auth required for customer booking)
- Ubuntu 24.04 installation script
- Full rebranding from Emergent to Spancle

## Key Database Collections
- users, tenants, venues, courts, bookings, customers, payment_transactions, pricing_rules, password_reset_tokens, login_attempts

## API Endpoints
Auth: register, login, logout, me, forgot-password, reset-password
Tenants: CRUD + subscription management
Venues: CRUD + bulk import
Courts: CRUD
Bookings: CRUD + recurring + cancellation
Customers: CRUD
Payments: Stripe, Razorpay, PayPal, Skrill
Analytics: dashboard, revenue-trend, court-occupancy
Exports: bookings CSV, analytics CSV
QR Codes, Webhooks (Stripe, Skrill), Public endpoints

## 3rd Party Integrations
- Stripe, Razorpay, PayPal, Skrill (payments - require user API keys)
- Resend (email notifications - requires user API key)

## Bug Fixes (Apr 18, 2026)
- Fixed: GET /api/venues, /api/courts, /api/pricing, /api/bookings, /api/customers all now return `id` field (was missing due to MongoDB `{"_id": 0}` projection)
- Fixed: Brute force protection now locks after 5 failed attempts (was locking after 1)
- Fixed: Timezone-aware datetime comparison in brute force check (was causing TypeError)
- Fixed: All user-visible "Emergent" branding replaced with "Spancle"

## Backlog
- P1: Mobile App functionality (deferred)
- P2: Backend refactoring (server.py into route modules)
