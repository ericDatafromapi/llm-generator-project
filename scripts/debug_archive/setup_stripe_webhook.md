# Setup Stripe Webhook - Step by Step

## 🎯 The Problem

Stripe doesn't know where to send payment notifications, so your backend never learns about successful payments.

## ✅ The Solution - Create Webhook in Stripe

### Step 1: Open Stripe Dashboard

1. Go to: https://dashboard.stripe.com/webhooks
2. **Make sure you're in TEST mode** (toggle in top right)

### Step 2: Add Endpoint

1. Click the **"Add endpoint"** button
2. For **Endpoint URL**, enter:
   ```
   http://157.180.73.104/api/v1/webhooks/stripe
   ```
   (Use your actual server IP or domain)

3. Click **"Select events"**

### Step 3: Select These Events

Select these events (required for subscriptions):

**Checkout:**
- ✅ `checkout.session.completed`

**Subscriptions:**
- ✅ `customer.subscription.created`
- ✅ `customer.subscription.updated`
- ✅ `customer.subscription.deleted`

**Payments:**
- ✅ `invoice.payment_succeeded`
- ✅ `invoice.payment_failed`
- ✅ `invoice.payment_action_required`

**Optional (for refunds/chargebacks):**
- ✅ `charge.dispute.created`
- ✅ `charge.refunded`
- ✅ `customer.deleted`

### Step 4: Save and Get Signing Secret

1. Click **"Add endpoint"**
2. The webhook is now created
3. Click on the webhook you just created
4. Click **"Reveal"** next to "Signing secret"
5. **Copy the secret** (starts with `whsec_`)

### Step 5: Add Secret to Backend

```bash
# SSH to production server
ssh user@your-server

# Edit .env file
nano /opt/llmready/backend/.env

# Find the line:
# STRIPE_WEBHOOK_SECRET=whsec_...

# Replace with your actual secret:
# STRIPE_WEBHOOK_SECRET=whsec_abc123xyz...

# Save and exit (Ctrl+X, Y, Enter)

# Restart backend
sudo systemctl restart llmready-backend
```

### Step 6: Test the Webhook

Back in Stripe Dashboard, on your webhook page:

1. Click **"Send test webhook"**
2. Select event: `checkout.session.completed`
3. Click **"Send test webhook"**
4. Check the response - should show 200 OK

### Step 7: Verify in Backend Logs

```bash
# Watch backend logs
sudo journalctl -u llmready-backend -f
```

When webhook is sent, you should see:
```
Received webhook event: checkout.session.completed
```

---

## ✅ After Setup

Once webhook is configured:

1. Subscribe to a plan again (test with new email if needed)
2. Complete payment on Stripe
3. Come back to your site
4. **Plan should update immediately!**

---

## 📝 Checklist

- [ ] Webhook endpoint created in Stripe Dashboard
- [ ] URL: http://YOUR_IP/api/v1/webhooks/stripe
- [ ] All required events selected
- [ ] Signing secret copied and added to .env
- [ ] Backend restarted
- [ ] Test webhook sent successfully (200 OK)
- [ ] Ready to test real subscription!

---

**Follow these steps and subscription updates will work!** 🎉