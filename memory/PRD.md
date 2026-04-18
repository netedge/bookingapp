# Spancle - Multi-Tenant SaaS Venue Booking Platform

## Original Problem Statement
Create a full-fledged multi-tenant SaaS application for venue booking ("Spancle"). Use the 5 elements of earth for the color scheme. Needs to be mobile responsive. Provide database structure export for live migration. Features must include multi-gateway payment integrations (Razorpay, Stripe, PayPal, Skrill) and email notifications (Resend). Must be production-ready and deployable on an Ubuntu server.

## User Personas
- **Super Admin**: Platform owner managing all tenants
- **Tenant Admin**: Venue owner managing their venues, courts, bookings
- **Customer (B2C)**: End user booking venue slots via public booking pages

## Tech Stack
- Frontend: React.js (CRA), Tailwind CSS, Phosphor Icons, Framer Motion
- Backend: FastAPI, Python 3.11+
- Database: MongoDB (Motor async driver)
- Architecture: Modular backend (routes/, shared modules), multi-tenant via tenant_id

## Backend Architecture
```
/app/backend/
├── server.py          (Entry point, CORS, startup, router imports)
├── database.py, config.py, auth.py, models.py, email_service.py
├── routes/ (auth, tenants, venues, courts, bookings, customers, payments, analytics, public, qr)
```

## What's Been Implemented
- Full auth: login, register, self-serve tenant registration, forgot/reset password, brute force protection
- Tenant Dashboard: Overview, Venues, Courts, Bookings, Tenants
- Public booking pages (path + subdomain routing)
- Multi-gateway payments (Stripe, Razorpay, PayPal, Skrill)
- Email notifications via Resend
- Analytics charts + CSV exports
- Subscription billing tiers, QR codes, bulk import, recurring bookings
- Mobile responsive, Ubuntu deployment script, full Spancle branding

## Code Quality (Apr 18, 2026)
- Hardcoded secrets moved to env vars in test files
- Empty catch blocks replaced with proper error handling (state resets)
- AuthContext value prop memoized with useMemo
- Motion animation objects extracted to module-level constants (Landing, PublicBooking)
- Dashboard split further: VenueGrid, BookingPanel extracted
- PaymentGatewaySelector handler map replaces if-else chain
- Python type hints added to server.py lifecycle functions
- All linting passes (ESLint + Ruff)

## Backlog
- P2: Super admin global view for courts/pricing/customers
- P2: Backend subdomain format validation (reject reserved words)
- P2: FastAPI lifespan migration (deprecated @app.on_event)
- P3: Mobile App (deferred until maturity)
