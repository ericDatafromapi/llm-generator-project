# 🔧 SendGrid Setup & Troubleshooting Guide

## Step-by-Step SendGrid Setup

### 1. Create SendGrid Account
1. Go to https://sendgrid.com/
2. Sign up for a free account (100 emails/day free tier)
3. Verify your email address

### 2. Verify Your Sender Email

**This is the MOST COMMON issue causing 400 errors!**

#### Option A: Single Sender Verification (Easiest for Testing)
1. Go to https://app.sendgrid.com/settings/sender_auth/senders
2. Click "Create New Sender"
3. Fill in the form:
   - **From Name**: Your Name or Company
   - **From Email**: The email you want to use (e.g., noreply@yourdomain.com)
   - **Reply To**: Your real email
   - **Company Address**: Any address
4. Click "Create"
5. **Important**: Check your email inbox and click the verification link
6. Wait for "Verified" status in SendGrid dashboard

#### Option B: Domain Authentication (For Production)
1. Go to https://app.sendgrid.com/settings/sender_auth
2. Click "Authenticate Your Domain"
3. Follow DNS setup instructions
4. Verify domain

### 3. Create API Key

1. Go to https://app.sendgrid.com/settings/api_keys
2. Click "Create API Key"
3. Choose "Restricted Access"
4. Give it a name (e.g., "LLMReady API Key")
5. Under "Mail Send", select "Full Access"
6. Click "Create & View"
7. **COPY THE KEY IMMEDIATELY** (you can only see it once!)
8. Key format: `SG.xxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyy`

### 4. Configure .env File

Update your `backend/.env` file:

```env
# SendGrid Configuration
SENDGRID_API_KEY=SG.your_actual_key_here
FROM_EMAIL=noreply@yourdomain.com  # MUST match verified sender!
```

**Important Notes:**
- `FROM_EMAIL` must EXACTLY match the verified sender in SendGrid
- No spaces around the `=` sign
- No quotes around the values
- Restart your server after changing .env

### 5. Restart Server

```bash
# Stop server (Ctrl+C)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "HTTP Error 400: Bad Request"

**Most Common Causes:**

#### A. Sender Email Not Verified ⚠️ #1 Cause
```
Error: The from email does not match a verified Sender Identity
```

**Solution:**
1. Check SendGrid dashboard: https://app.sendgrid.com/settings/sender_auth/senders
2. Look for your email - must show "Verified" status
3. If not verified, check your email for verification link
4. Wait 2-3 minutes after clicking verification link

#### B. FROM_EMAIL Doesn't Match Verified Sender
```
FROM_EMAIL=noreply@example.com
But verified sender is: hello@example.com
```

**Solution:**
- Make sure `FROM_EMAIL` in `.env` EXACTLY matches verified sender
- Case doesn't matter (NOREPLY@example.com = noreply@example.com)

#### C. Invalid API Key
```
Error: Unauthorized
```

**Solution:**
1. Generate new API key in SendGrid
2. Make sure it has "Mail Send" permission
3. Update `.env` with new key
4. Restart server

### Issue 2: "Unauthorized" Error

**Cause:** Invalid or expired API key

**Solution:**
1. Go to https://app.sendgrid.com/settings/api_keys
2. Delete old key
3. Create new key with "Mail Send - Full Access"
4. Update `.env`
5. Restart server

### Issue 3: Emails Not Arriving

**Possible Causes:**
- Emails in spam folder
- Wrong recipient email
- Free tier daily limit reached (100/day)

**Solutions:**
1. Check spam/junk folder
2. Use a test email like Gmail or your real email
3. Check SendGrid dashboard → Activity for delivery status

---

## 🧪 Test SendGrid Configuration

I'll create a test script for you. Run it to verify SendGrid is working:

```bash
cd backend
source venv/bin/activate
python test_sendgrid.py
```

---

## 📋 Verification Checklist

Before testing, verify:

- [ ] SendGrid account created
- [ ] Email address verified in SendGrid (shows "Verified" status)
- [ ] API key created with "Mail Send" permission
- [ ] `.env` file updated with correct values
- [ ] `FROM_EMAIL` matches verified sender EXACTLY
- [ ] Server restarted after .env changes
- [ ] No spaces around `=` in .env file

---

## 🔍 Debugging Steps

### Step 1: Check Current Configuration

Look at your `.env` file:
```bash
cd backend
cat .env | grep -E 'SENDGRID|FROM_EMAIL'
```

Should show:
```
SENDGRID_API_KEY=SG.xxxxxxxxxx
FROM_EMAIL=verified@email.com
```

### Step 2: Verify Sender in SendGrid

1. Go to: https://app.sendgrid.com/settings/sender_auth/senders
2. Find your sender
3. Status must be "Verified" (green checkmark)

### Step 3: Check Server Logs

After restarting and trying to send email, look for detailed error:
```
2025-10-11 xx:xx:xx - app.services.email - ERROR - Error sending email to user@example.com: ...
2025-10-11 xx:xx:xx - app.services.email - ERROR - SendGrid error details: ...
```

This will tell you the exact problem!

### Step 4: Try Registration Again

With server running and logs visible:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

Watch the terminal for detailed error messages.

---

## 💡 Quick Fix for Testing

If you can't get SendGrid working right now and want to continue testing:

The system works WITHOUT emails! Just:
1. Register user
2. Get verification token from database
3. Call verify endpoint manually

See main documentation for database query.

---

## 📞 Still Not Working?

Share the complete error message from server logs (after improved logging), including:
- The full error text
- Your FROM_EMAIL (hide sensitive parts)
- Verification status from SendGrid dashboard

I'll help you fix it!