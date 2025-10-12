# 🔍 How to Find Your Stripe Price IDs

## The Problem

You currently have in your `.env`:
```bash
STRIPE_PRICE_STANDARD=prod_TDcHAcGgTicRAk  ❌ This is a PRODUCT ID
STRIPE_PRICE_PRO=prod_TDcHPI2YMsB0i9      ❌ This is a PRODUCT ID
```

You need **PRICE IDs** (start with `price_`), not Product IDs.

---

## How to Find Price IDs

### Method 1: From Stripe Dashboard (Recommended)

1. Go to https://dashboard.stripe.com/test/products
2. Click on your **"LLMReady Standard"** product
3. Look for the **"Pricing"** section
4. You'll see something like:
   ```
   €29.00 per month
   API ID: price_1Q2gm8RHXxKeqU7yXXXXXXXX  ← THIS IS WHAT YOU NEED!
   ```
5. **Copy this Price ID** (starts with `price_`)
6. Repeat for the Pro product

### Method 2: Using Stripe CLI

```bash
# List all products with their prices
stripe products list

# Or get a specific product's details
stripe products retrieve prod_TDcHAcGgTicRAk
```

Look for the `default_price` field in the output.

---

## Update Your .env File

Once you have the correct Price IDs, update `backend/.env`:

```bash
# Replace these lines with your actual Price IDs:
STRIPE_PRICE_STANDARD=price_1Q2gm8RHXxKeqU7yXXXXXXXX  ✅ Starts with price_
STRIPE_PRICE_PRO=price_1Q2gm8RHXxKeqU7yYYYYYYYY      ✅ Starts with price_
```

---

## Quick Visual Guide

When you click on a product in Stripe Dashboard, you should see:

```
┌─────────────────────────────────────────┐
│ LLMReady Standard                       │
│                                         │
│ Pricing                                 │
│ ┌─────────────────────────────────────┐ │
│ │ €29.00 per month                    │ │
│ │ Recurring • Created Dec 11, 2024    │ │
│ │                                     │ │
│ │ API ID: price_1Q2gm8RHXxKeqU7y...  │ │  ← COPY THIS!
│ │                                     │ │
│ │ [Edit price]                        │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## After Updating

1. Save the `.env` file
2. **Restart your backend server**:
   ```bash
   # Stop the server (Ctrl+C)
   # Then restart
   uvicorn app.main:app --reload
   ```

3. Try the checkout again:
   ```bash
   curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"plan_type": "standard"}'
   ```

---

## Verify It's Working

The response should contain:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

✅ If you see this, it's working!
❌ If you still see "No such price", double-check the Price ID

---

## Still Having Issues?

Check if your products have prices:
```bash
stripe products retrieve prod_TDcHAcGgTicRAk --expand default_price
```

If `default_price` is null, you need to create a price for the product:
```bash
stripe prices create \
  --product prod_TDcHAcGgTicRAk \
  --unit-amount 2900 \
  --currency eur \
  --recurring[interval]=month
```

This will output a Price ID you can use.