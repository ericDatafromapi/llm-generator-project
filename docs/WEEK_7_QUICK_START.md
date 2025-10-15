# 🚀 Week 7 Quick Start Guide

**Website Management is Ready!** Let's test it.

---

## Prerequisites

✅ Weeks 1-6 completed  
✅ FastAPI running on port 8000  
✅ PostgreSQL & Redis running via Docker  
✅ You have a valid JWT token from login

---

## 🎯 Quick Test (5 minutes)

### Step 1: Login and Get Token

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "your_password"
  }'

# Save the access_token
TOKEN="paste_your_access_token_here"
```

### Step 2: Check Your Current Plan

```bash
# Check subscription
curl -X GET "http://localhost:8000/api/v1/subscriptions/current" \
  -H "Authorization: Bearer $TOKEN"

# Note your plan: free (1 website), standard (5 websites), or pro (unlimited)
```

### Step 3: Create Your First Website

```bash
# Create a website
curl -X POST "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "My First Website",
    "description": "Testing the website management system",
    "max_pages": 50
  }'

# Save the website ID from response
WEBSITE_ID="paste_website_id_here"
```

### Step 4: List Your Websites

```bash
# List all websites
curl -X GET "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN"

# You should see your newly created website!
```

### Step 5: View Your Statistics

```bash
# Get user stats
curl -X GET "http://localhost:8000/api/v1/websites/stats/user" \
  -H "Authorization: Bearer $TOKEN"

# Expected output:
{
  "total_websites": 1,
  "active_websites": 1,
  "total_generations": 0,
  "successful_generations": 0,
  "failed_generations": 0,
  "generations_this_month": 0,
  "generations_remaining": 1,
  "success_rate": 0.0
}
```

### Step 6: Update Website

```bash
# Update the website
curl -X PUT "http://localhost:8000/api/v1/websites/$WEBSITE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Website Name",
    "max_pages": 100
  }'
```

### Step 7: Test Plan Limits

```bash
# Try to create a second website (will fail if you're on free plan)
curl -X POST "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://another-site.com",
    "name": "Second Website"
  }'

# Expected error if on free plan:
{
  "detail": "Website limit reached. Your free plan allows 1 website. Please upgrade your plan to add more websites."
}
```

---

## 🎨 Full Feature Test

### Test URL Normalization

```bash
# Create website without https:// (will be auto-added)
curl -X POST "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "example.org",
    "name": "Auto HTTPS Test"
  }'

# URL will automatically become "https://example.org"
```

### Test Duplicate Prevention

```bash
# Try to create duplicate (will fail)
curl -X POST "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "Duplicate Test"
  }'

# Expected error:
{
  "detail": "You already have a website with URL: https://example.com"
}
```

### Test Filtering

```bash
# List only active websites
curl -X GET "http://localhost:8000/api/v1/websites?is_active=true" \
  -H "Authorization: Bearer $TOKEN"

# List inactive websites
curl -X GET "http://localhost:8000/api/v1/websites?is_active=false" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Pagination

```bash
# Get page 1 with 5 items per page
curl -X GET "http://localhost:8000/api/v1/websites?page=1&per_page=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Website Statistics

```bash
# Get statistics for a specific website
curl -X GET "http://localhost:8000/api/v1/websites/$WEBSITE_ID/stats" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Delete Protection

```bash
# Start a generation first
curl -X POST "http://localhost:8000/api/v1/generations/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"website_id\": \"$WEBSITE_ID\"}"

# Try to delete (will fail while generation is active)
curl -X DELETE "http://localhost:8000/api/v1/websites/$WEBSITE_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected error:
{
  "detail": "Cannot delete website with generations in progress. Please wait for them to complete."
}
```

---

## 🔗 Integration Test: Complete Flow

Test the full workflow from website creation to generation:

```bash
#!/bin/bash
# Save as test_week7.sh

TOKEN="your_token_here"

echo "1. Creating website..."
WEBSITE_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/websites" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://docs.python.org",
    "name": "Python Docs",
    "description": "Testing with real documentation",
    "include_patterns": "tutorial,library",
    "max_pages": 20
  }')

WEBSITE_ID=$(echo $WEBSITE_RESPONSE | jq -r '.id')
echo "✓ Website created: $WEBSITE_ID"

echo "2. Checking quota..."
QUOTA_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/generations/quota/check" \
  -H "Authorization: Bearer $TOKEN")
echo "$QUOTA_RESPONSE" | jq '.'

echo "3. Starting generation..."
GENERATION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/generations/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"website_id\": \"$WEBSITE_ID\"}")

GENERATION_ID=$(echo $GENERATION_RESPONSE | jq -r '.generation_id')
echo "✓ Generation started: $GENERATION_ID"

echo "4. Waiting for generation to complete..."
sleep 30

echo "5. Checking generation status..."
curl -s -X GET "http://localhost:8000/api/v1/generations/$GENERATION_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo "6. Checking website statistics..."
curl -s -X GET "http://localhost:8000/api/v1/websites/$WEBSITE_ID/stats" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo "7. Checking user statistics..."
curl -s -X GET "http://localhost:8000/api/v1/websites/stats/user" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

echo "✓ Complete workflow test finished!"
```

---

## 📊 Verify API Documentation

Open your browser and check the auto-generated API docs:

```bash
# Open Swagger UI
open http://localhost:8000/api/docs

# Look for the "websites" section - you should see 8 endpoints:
# - POST   /api/v1/websites
# - GET    /api/v1/websites
# - GET    /api/v1/websites/{website_id}
# - PUT    /api/v1/websites/{website_id}
# - DELETE /api/v1/websites/{website_id}
# - GET    /api/v1/websites/{website_id}/stats
# - GET    /api/v1/websites/stats/user
# - GET    /api/v1/generations/history (enhanced)
```

---

## 🐛 Common Issues

### Issue: "No subscription found"

**Solution:** Create a subscription first (should happen automatically on user registration)

```bash
# Check if you have a subscription
curl -X GET "http://localhost:8000/api/v1/subscriptions/current" \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: Can't create website

**Check:**
1. Your plan limits (free = 1 website)
2. Token is valid and not expired
3. URL format is correct

### Issue: Statistics show 0 for everything

**Normal:** If you haven't run any generations yet, stats will be zero

---

## ✅ Success Criteria

After testing, you should be able to:

- ✅ Create websites within your plan limits
- ✅ List websites with pagination
- ✅ Update website configurations
- ✅ View website-specific statistics
- ✅ View user-wide statistics
- ✅ See plan limits enforced
- ✅ URLs automatically normalized
- ✅ Duplicates prevented
- ✅ Delete websites (when no active generations)

---

## 🎯 What's Next?

Now that website management is complete, you're ready for:

**Week 8-9: React Frontend**
- Build the UI for website management
- Display statistics dashboards
- Create website forms
- Integrate with all backend APIs

---

## 📞 Need Help?

1. Check [`WEEK_7_WEBSITES_COMPLETE.md`](WEEK_7_WEBSITES_COMPLETE.md:1) for detailed docs
2. Look at FastAPI logs for errors
3. Verify database records: `docker exec -it llmready_postgres psql -U postgres -d llmready_dev -c "SELECT * FROM websites;"`

**Week 7 is complete and ready to test!** 🎉