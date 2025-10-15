# 🧪 Stripe Local Testing Guide

Quick guide to test Stripe integration locally without creating products first.

## Step 1: Set Up Stripe CLI

```bash
# Install Stripe CLI (if not already installed)
brew install stripe/stripe-cli/stripe

# Login to your Stripe account
stripe login
```

## Step 2: Create Test Products (Required Before Testing)

You need to create products in Stripe Dashboard first:

1. Go to https://dashboard.stripe.com/test/products
2. Click "**Add product**"

### Standard Plan
- **Name**: LLMReady Standard
- **Price**: €29.00
- **Billing period**: Monthly
- Click **Save product**
- **COPY THE PRICE ID** (starts with `price_...`)

### Pro Plan  
- **Name**: LLMReady Pro
- **Price**: €59.00
- **Billing period**: Monthly
- Click **Save product**
- **COPY THE PRICE ID** (starts with `price_...`)

## Step 3: Update .env with Real Price IDs

```bash
# Edit backend/.env and replace these lines:
STRIPE_PRICE_STANDARD=price_YOUR_ACTUAL_STANDARD_PRICE_ID
STRIPE_PRICE_PRO=price_YOUR_ACTUAL_PRO_PRICE_ID
```

## Step 4: Start Webhook Forwarding

```bash
# In a new terminal, forward webhooks to your local server
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

This will output a webhook signing secret like:
```
> Ready! Your webhook signing secret is whsec_xxxxx
```

**COPY THIS SECRET** and update your `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

## Step 5: Start Your Backend

```bash
# In another terminal
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Step 6: Test Checkout Flow

### Option A: Using curl

```bash
# 1. Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Copy the access_token from response

# 3. Create checkout session
curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "plan_type": "standard"
  }'

# 4. Open the checkout_url in your browser
```

### Option B: Using Swagger UI

1. Open http://localhost:8000/api/docs
2. Register a user via `/api/v1/auth/register`
3. Login via `/api/v1/auth/login` and copy the access token
4. Click **Authorize** button and enter: `Bearer YOUR_ACCESS_TOKEN`
5. Try `/api/v1/subscriptions/checkout` with `plan_type: "standard"`
6. Open the returned `checkout_url` in browser

## Step 7: Complete Test Payment

1. Open the checkout URL from step 6
2. Use Stripe test card: **4242 4242 4242 4242**
3. Any future expiry date (e.g., 12/34)
4. Any 3-digit CVC (e.g., 123)
5. Complete the checkout

## Step 8: Verify Webhook Processing

In your Stripe CLI terminal, you should see:
```
2024-01-15 10:00:00   --> checkout.session.completed [evt_xxx]
2024-01-15 10:00:00   <-- [200] POST http://localhost:8000/api/v1/webhooks/stripe [evt_xxx]
```

Check your backend logs for:
```
INFO:     Subscription created/updated for user xxx, plan standard
```

## Step 9: Verify in Database

```bash
# Connect to database
docker exec -it llmready_postgres psql -U postgres -d llmready_dev

# Check subscription was created
SELECT user_id, plan_type, status, stripe_subscription_id 
FROM subscriptions;

# Exit
\q
```

---

## 🎯 Testing Checklist

- [ ] Stripe CLI installed and logged in
- [ ] Products created in Stripe Dashboard (Standard & Pro)
- [ ] Price IDs copied to `.env`
- [ ] Webhook forwarding running (`stripe listen`)
- [ ] Webhook secret updated in `.env`
- [ ] Backend server running
- [ ] Test user created and logged in
- [ ] Checkout session creates successfully
- [ ] Payment completes with test card
- [ ] Webhook received and processed
- [ ] Subscription created in database

---

## 🐛 Common Issues

### "Invalid URL" Error
✅ **Fixed!** Make sure `FRONTEND_URL=http://localhost:3000` is in your `.env`

### "Price not found" Error
- You need to create products in Stripe Dashboard first
- Update `.env` with actual price IDs (not placeholders)

### Webhook Not Receiving Events
- Make sure `stripe listen` is running
- Check webhook secret in `.env` matches output from `stripe listen`
- Ensure backend is running on port 8000

### "No subscription found for user"
- Make sure webhook was processed successfully
- Check Stripe CLI logs for webhook delivery
- Check backend logs for webhook processing
- Verify in database: `SELECT * FROM subscriptions;`

---

## 📊 Test Different Scenarios

```bash
# Test Standard plan
curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_type": "standard"}'

# Test Pro plan
curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_type": "pro"}'

# Check current subscription
curl http://localhost:8000/api/v1/subscriptions/current \
  -H "Authorization: Bearer TOKEN"

# Check usage
curl http://localhost:8000/api/v1/subscriptions/usage \
  -H "Authorization: Bearer TOKEN"

# Get customer portal link
curl -X POST http://localhost:8000/api/v1/subscriptions/portal \
  -H "Authorization: Bearer TOKEN"
```

---

## 🎉 Success!

If all steps work, you should have:
- ✅ Working checkout flow
- ✅ Webhook processing subscription events
- ✅ Subscription created in database
- ✅ User can access subscription info

You're ready to integrate with the frontend! 🚀