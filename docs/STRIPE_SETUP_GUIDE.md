# 🎯 Stripe Integration Setup Guide

This guide walks you through setting up Stripe for LLMReady's subscription system.

## 📋 Prerequisites

- A Stripe account (sign up at [stripe.com](https://stripe.com))
- Access to your Stripe Dashboard
- Backend environment configured and running

---

## 🔧 Step 1: Create Your Stripe Account

1. Go to [https://stripe.com](https://stripe.com) and sign up
2. Complete the account verification (business details, banking info)
3. You'll start in **Test Mode** - perfect for development

---

## 💳 Step 2: Create Products and Prices

### Navigate to Products

1. In Stripe Dashboard, go to **Products** → **Add Product**

### Create Standard Plan

1. Click **Add product**
2. Fill in:
   - **Name**: `LLMReady Standard`
   - **Description**: `10 generations per month, 5 websites, up to 500 pages`
3. Under **Pricing**:
   - **Pricing model**: Standard pricing
   - **Price**: `€29.00`
   - **Billing period**: Monthly
4. Click **Save product**
5. **Copy the Price ID** (starts with `price_...`) - you'll need this!

### Create Pro Plan

1. Click **Add product** again
2. Fill in:
   - **Name**: `LLMReady Pro`
   - **Description**: `25 generations per month, unlimited websites, up to 1000 pages`
3. Under **Pricing**:
   - **Pricing model**: Standard pricing
   - **Price**: `€59.00`
   - **Billing period**: Monthly
4. Click **Save product**
5. **Copy the Price ID** (starts with `price_...`)

---

## 🔑 Step 3: Get Your API Keys

### Get Secret Key

1. In Stripe Dashboard, go to **Developers** → **API keys**
2. Find **Secret key** (starts with `sk_test_...` in test mode)
3. Click **Reveal test key** and copy it

### Get Publishable Key

1. On the same page, find **Publishable key** (starts with `pk_test_...`)
2. Copy this key as well

### Update Your Environment

Open `backend/.env` and update:

```bash
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_PUBLISHABLE_KEY_HERE
STRIPE_PRICE_STANDARD=price_YOUR_STANDARD_PRICE_ID
STRIPE_PRICE_PRO=price_YOUR_PRO_PRICE_ID
```

---

## 🔔 Step 4: Set Up Webhooks

Webhooks allow Stripe to notify your backend about subscription events.

### Install Stripe CLI (for local testing)

```bash
# macOS
brew install stripe/stripe-cli/stripe

# Login to your account
stripe login
```

### Create Webhook Endpoint

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. For **Endpoint URL**, enter:
   - **Local testing**: Use Stripe CLI (see below)
   - **Production**: `https://yourdomain.com/api/v1/webhooks/stripe`
4. Click **Select events** and choose:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. **Copy the Signing secret** (starts with `whsec_...`)

### Update Environment with Webhook Secret

```bash
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
```

---

## 🧪 Step 5: Test Locally with Stripe CLI

### Forward Webhooks to Your Local Server

```bash
# Start your backend first
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# In a new terminal, forward webhooks
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
```

This will give you a webhook signing secret for local testing. Copy it and update your `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LOCAL_WEBHOOK_SECRET
```

---

## ✅ Step 6: Test the Integration

### Test Checkout Flow

```bash
# Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Create checkout session (use the access_token from login)
curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "plan_type": "standard"
  }'
```

### Test with Stripe Test Cards

Stripe provides test cards for different scenarios:

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 9995 | Card declined |
| 4000 0025 0000 3155 | Requires authentication (3D Secure) |

Use any future expiry date and any 3-digit CVC.

### Verify Webhooks

1. Complete a test checkout
2. Check your Stripe CLI terminal - you should see webhook events
3. Check your backend logs - subscription should be created
4. Verify in database:

```bash
# Connect to database
docker exec -it llmready_postgres psql -U postgres -d llmready_dev

# Check subscriptions
SELECT user_id, plan_type, status, stripe_subscription_id 
FROM subscriptions;
```

---

## 🚀 Step 7: Go Live (Production)

### Switch to Live Mode

1. In Stripe Dashboard, toggle from **Test mode** to **Live mode**
2. Repeat Steps 2-4 to create live products and get live API keys
3. Update your production `.env`:

```bash
STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_WEBHOOK_SECRET
STRIPE_PRICE_STANDARD=price_YOUR_LIVE_STANDARD_PRICE_ID
STRIPE_PRICE_PRO=price_YOUR_LIVE_PRO_PRICE_ID
```

### Production Webhook Setup

1. Create webhook endpoint with your production URL
2. Ensure your server is accessible from Stripe's webhooks
3. Test thoroughly before announcing

---

## 📊 Monitoring Subscriptions

### Stripe Dashboard

- View all subscriptions: **Customers** → **Subscriptions**
- Check payments: **Payments**
- Monitor failed payments: **Payments** → Filter by Failed
- View webhooks: **Developers** → **Webhooks** → **Logs**

### Your Application

Check subscription status via API:

```bash
# Get current subscription
curl -X GET http://localhost:8000/api/v1/subscriptions/current \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get usage stats
curl -X GET http://localhost:8000/api/v1/subscriptions/usage \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🐛 Troubleshooting

### Webhook Not Receiving Events

1. Check webhook endpoint is accessible
2. Verify signing secret is correct
3. Check Stripe Dashboard → Webhooks → Logs for errors
4. Ensure webhook handler doesn't timeout (< 30s response time)

### Checkout Session Not Creating

1. Verify API keys are correct
2. Check product and price IDs are valid
3. Ensure user has a subscription record in database
4. Check backend logs for detailed error messages

### Subscription Not Updating

1. Verify webhook events are being received
2. Check database for subscription record
3. Ensure Stripe customer ID matches
4. Review webhook processing logs

### Testing Failed Payments

```bash
# Use Stripe CLI to trigger events
stripe trigger customer.subscription.updated
stripe trigger invoice.payment_failed
```

---

## 📚 Available Endpoints

### Public

- `GET /api/v1/subscriptions/plans` - Get all available plans

### Authenticated

- `POST /api/v1/subscriptions/checkout` - Create checkout session
- `GET /api/v1/subscriptions/current` - Get current subscription
- `GET /api/v1/subscriptions/usage` - Get usage statistics
- `POST /api/v1/subscriptions/portal` - Get customer portal link
- `GET /api/v1/subscriptions/quota/check` - Check generation quota
- `GET /api/v1/subscriptions/website-limit/check` - Check website limit

### Webhooks (No Auth)

- `POST /api/v1/webhooks/stripe` - Stripe webhook endpoint

---

## 💡 Best Practices

1. **Always test in Test Mode first**
2. **Monitor webhook logs regularly**
3. **Set up email alerts for failed payments**
4. **Keep API keys secure** - never commit to git
5. **Use Customer Portal** for self-service management
6. **Test edge cases**: cancellations, upgrades, downgrades
7. **Handle webhook retries gracefully**
8. **Log all payment events** for audit trail

---

## 🔒 Security Checklist

- [ ] API keys stored in environment variables
- [ ] Webhook signature verification enabled
- [ ] HTTPS enabled in production
- [ ] Rate limiting configured
- [ ] Idempotency keys used for payments
- [ ] PCI compliance maintained (Stripe handles card data)
- [ ] Access logs monitored
- [ ] Regular security updates applied

---

## 📞 Support

- **Stripe Documentation**: [stripe.com/docs](https://stripe.com/docs)
- **Stripe Support**: Available in Dashboard
- **Test Cards**: [stripe.com/docs/testing](https://stripe.com/docs/testing)

---

## 🎉 Next Steps

Once Stripe is configured:

1. Test full checkout flow
2. Verify webhook processing
3. Test quota enforcement
4. Set up frontend integration (Week 8-9)
5. Configure email notifications for payment events
6. Set up monitoring and alerts

Your subscription system is now ready! 🚀