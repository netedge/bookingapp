# Kelika Database Structure

This document describes the MongoDB database structure for the Kelika multi-tenant SaaS platform.

## Database Name
`kelika_db`

## Collections

### 1. users
Stores all user accounts (Super Admin, Tenant Admin, Staff, Customer)

```javascript
{
  _id: ObjectId,
  email: String (unique, lowercase),
  password_hash: String (bcrypt),
  name: String,
  role: String (enum: "super_admin", "tenant_admin", "staff", "customer"),
  tenant_id: String (null for super_admin),
  created_at: DateTime
}
```

**Indexes:**
- `email: unique`

### 2. tenants
Stores tenant/business information

```javascript
{
  _id: ObjectId,
  business_name: String,
  subdomain: String (unique),
  logo_url: String (optional),
  primary_color: String (hex color),
  timezone: String,
  currency: String,
  created_at: DateTime,
  status: String (enum: "active", "suspended")
}
```

**Indexes:**
- `subdomain: unique`

### 3. venues
Stores sports venues per tenant

```javascript
{
  _id: ObjectId,
  tenant_id: String,
  name: String,
  description: String,
  address: String,
  image_url: String,
  created_at: DateTime
}
```

### 4. courts
Stores courts/units within venues

```javascript
{
  _id: ObjectId,
  tenant_id: String,
  venue_id: String,
  name: String,
  sport_type: String,
  capacity: Number,
  indoor: Boolean,
  created_at: DateTime
}
```

### 5. bookings
Stores booking records

```javascript
{
  _id: ObjectId,
  court_id: String,
  customer_email: String,
  customer_name: String,
  customer_phone: String (optional),
  date: String (YYYY-MM-DD),
  start_time: String (HH:MM),
  end_time: String (HH:MM),
  total_price: Number,
  status: String (enum: "pending", "confirmed", "cancelled", "completed"),
  payment_status: String (enum: "pending", "paid", "refunded"),
  created_at: DateTime
}
```

### 6. pricing_rules
Stores pricing configurations

```javascript
{
  _id: ObjectId,
  tenant_id: String,
  court_id: String,
  rule_type: String (enum: "hourly", "peak", "weekend"),
  price: Number,
  start_time: String (optional),
  end_time: String (optional),
  days_of_week: Array<Number> (optional, 0-6),
  created_at: DateTime
}
```

### 7. customers
Stores customer database per tenant

```javascript
{
  _id: ObjectId,
  tenant_id: String,
  email: String,
  name: String,
  phone: String (optional),
  created_at: DateTime
}
```

### 8. payment_transactions
Stores payment transaction records

```javascript
{
  _id: ObjectId,
  booking_id: String,
  session_id: String (Stripe session ID),
  amount: Number,
  currency: String,
  payment_status: String (enum: "pending", "paid", "failed", "refunded"),
  created_at: DateTime
}
```

### 9. login_attempts
Stores failed login attempts for brute force protection

```javascript
{
  _id: ObjectId,
  identifier: String (format: "ip:email"),
  attempts: Number,
  last_attempt: DateTime,
  locked_until: DateTime
}
```

**Indexes:**
- `identifier: 1`

### 10. password_reset_tokens
Stores password reset tokens

```javascript
{
  _id: ObjectId,
  user_id: String,
  token: String,
  expires_at: DateTime,
  used: Boolean,
  created_at: DateTime
}
```

**Indexes:**
- `expires_at: TTL (expireAfterSeconds: 0)`

## Import Instructions

To import this structure into your MongoDB:

1. Connect to your MongoDB instance:
```bash
mongosh "mongodb://your-connection-string"
```

2. Switch to the Kelika database:
```javascript
use kelika_db
```

3. Create collections (MongoDB will auto-create, but you can do it manually):
```javascript
db.createCollection("users")
db.createCollection("tenants")
db.createCollection("venues")
db.createCollection("courts")
db.createCollection("bookings")
db.createCollection("pricing_rules")
db.createCollection("customers")
db.createCollection("payment_transactions")
db.createCollection("login_attempts")
db.createCollection("password_reset_tokens")
```

4. Create indexes:
```javascript
db.users.createIndex({ "email": 1 }, { unique: true })
db.tenants.createIndex({ "subdomain": 1 }, { unique: true })
db.login_attempts.createIndex({ "identifier": 1 })
db.password_reset_tokens.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
```

5. Seed Super Admin (replace with your credentials):
```javascript
db.users.insertOne({
  email: "admin@kelika.com",
  password_hash: "$2b$12$...", // Generate using bcrypt
  name: "Super Admin",
  role: "super_admin",
  tenant_id: null,
  created_at: new Date()
})
```

## Multi-Tenant Data Isolation

All tenant-specific data includes a `tenant_id` field to ensure data isolation:
- venues
- courts
- bookings
- pricing_rules
- customers

When querying, always filter by `tenant_id` (except for super_admin role).

## Sample Data

You can insert sample data for testing:

```javascript
// Sample Tenant
db.tenants.insertOne({
  business_name: "Champions Arena",
  subdomain: "champions",
  logo_url: null,
  primary_color: "#059669",
  timezone: "UTC",
  currency: "USD",
  created_at: new Date(),
  status: "active"
})

// Sample Venue (use actual tenant_id from above)
db.venues.insertOne({
  tenant_id: "TENANT_ID_HERE",
  name: "Downtown Sports Complex",
  description: "Premier sports facility in the heart of the city",
  address: "123 Main St, City, State 12345",
  image_url: "https://images.unsplash.com/photo-1765124540460-b884e248ac2b",
  created_at: new Date()
})
```
