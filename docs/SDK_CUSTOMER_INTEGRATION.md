# GetClearance SDK - Customer Integration Guide

**For: Pax Markets and other customers**
**Last Updated:** December 4, 2025

This guide explains how to integrate GetClearance identity verification into your website so your users can complete KYC.

---

## Quick Start (5 minutes)

### Step 1: Get Your API Key

1. Log into GetClearance dashboard
2. Go to **Settings > Integrations > API Keys**
3. Click **Create API Key**
4. Copy the key (starts with `sk_live_` or `sk_test_`)

### Step 2: Configure Webhooks (Optional but Recommended)

1. Go to **Settings > Integrations > Webhooks**
2. Enter your webhook URL (e.g., `https://api.paxmarkets.com/webhooks/getclearance`)
3. Select events to receive:
   - `applicant.submitted` - User completed SDK flow
   - `applicant.reviewed` - Verification approved/rejected
4. Copy the webhook secret for signature verification

### Step 3: Add SDK to Your Website

When a user needs to verify their identity:

```javascript
// Frontend: User clicks "Verify Identity"
async function startKYC() {
  // 1. Call YOUR backend to get an SDK token
  const response = await fetch('/api/kyc/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: currentUser.id })
  });

  const { sdk_url } = await response.json();

  // 2. Redirect user to GetClearance SDK
  window.location.href = sdk_url;
}
```

### Step 4: Backend Endpoint to Generate Token

**Node.js Example:**
```javascript
// YOUR backend: /api/kyc/start
app.post('/api/kyc/start', async (req, res) => {
  const user = await getUser(req.body.user_id);

  const response = await fetch('https://getclearance-production.up.railway.app/api/v1/sdk/access-token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.GETCLEARANCE_API_KEY
    },
    body: JSON.stringify({
      external_user_id: user.id,           // YOUR user ID
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName,
      redirect_url: 'https://paxmarkets.com/kyc/complete'  // Where to send user after
    })
  });

  const data = await response.json();
  res.json({ sdk_url: data.sdk_url });
});
```

**Python Example:**
```python
# YOUR backend: /api/kyc/start
@app.post("/api/kyc/start")
async def start_kyc(user_id: str):
    user = await get_user(user_id)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://getclearance-production.up.railway.app/api/v1/sdk/access-token",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": os.environ["GETCLEARANCE_API_KEY"]
            },
            json={
                "external_user_id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "redirect_url": "https://paxmarkets.com/kyc/complete"
            }
        )

    data = response.json()
    return {"sdk_url": data["sdk_url"]}
```

---

## What Happens Next

### User Flow
```
Your Website                    GetClearance SDK
     │                               │
     │  1. User clicks "Verify"      │
     ├──────────────────────────────►│
     │                               │
     │                        ┌──────┴──────┐
     │                        │ Consent     │
     │                        │ Upload ID   │
     │                        │ Selfie      │
     │                        │ Submit      │
     │                        └──────┬──────┘
     │                               │
     │◄──────────────────────────────┤
     │  2. Redirect to your site     │
     │     /kyc/complete             │
     │                               │
     │  3. Webhook: applicant.submitted
     │◄──────────────────────────────┤
     │                               │
     │  4. Webhook: applicant.reviewed
     │◄──────────────────────────────┤ (when approved/rejected)
```

### Webhook Events

**`applicant.submitted`** - Sent immediately when user completes SDK:
```json
{
  "event_type": "applicant.submitted",
  "event_id": "uuid",
  "timestamp": "2025-12-04T10:00:00Z",
  "data": {
    "applicant_id": "uuid",
    "external_id": "your_user_123",
    "status": "in_progress",
    "submitted_at": "2025-12-04T10:00:00Z",
    "documents_count": 2,
    "steps_completed": ["consent", "document", "selfie"]
  }
}
```

**`applicant.reviewed`** - Sent when verification is approved/rejected:
```json
{
  "event_type": "applicant.reviewed",
  "event_id": "uuid",
  "timestamp": "2025-12-04T10:05:00Z",
  "data": {
    "applicant_id": "uuid",
    "external_id": "your_user_123",
    "status": "approved",
    "risk_score": 15,
    "risk_level": "low",
    "review_decision": "manual_approved",
    "reviewed_at": "2025-12-04T10:05:00Z",
    "flags": []
  }
}
```

### Handling Webhooks

```javascript
// YOUR backend: /webhooks/getclearance
app.post('/webhooks/getclearance', async (req, res) => {
  // Verify signature (optional but recommended)
  const signature = req.headers['x-webhook-signature'];
  // ... verify using your webhook secret

  const event = req.body;

  switch (event.event_type) {
    case 'applicant.submitted':
      // User completed the SDK - verification in progress
      await updateUserKYCStatus(event.data.external_id, 'pending');
      break;

    case 'applicant.reviewed':
      if (event.data.status === 'approved') {
        // Unlock user account
        await updateUserKYCStatus(event.data.external_id, 'verified');
        await unlockTradingFeatures(event.data.external_id);
      } else {
        // Handle rejection
        await updateUserKYCStatus(event.data.external_id, 'rejected');
        await notifyUserRejection(event.data.external_id);
      }
      break;
  }

  res.status(200).send('OK');
});
```

---

## API Reference

### Generate SDK Access Token

```
POST https://getclearance-production.up.railway.app/api/v1/sdk/access-token

Headers:
  X-API-Key: sk_live_xxxxx
  Content-Type: application/json

Body:
{
  "external_user_id": "your_user_123",  // Required: Your unique user ID
  "email": "user@example.com",           // Optional but recommended
  "first_name": "John",                  // Optional
  "last_name": "Doe",                    // Optional
  "phone": "+1234567890",                // Optional
  "redirect_url": "https://...",         // Where to redirect after completion
  "flow_name": "default",                // Verification flow (default works)
  "expires_in": 3600                     // Token validity in seconds (default 1 hour)
}

Response:
{
  "access_token": "sdk_xxxxx",
  "applicant_id": "uuid",
  "expires_at": "2025-12-04T11:00:00Z",
  "flow_name": "default",
  "sdk_url": "https://getclearance.vercel.app/sdk/verify?token=sdk_xxxxx"
}
```

### Check Applicant Status (Optional)

If you need to check status without webhooks:

```
GET https://getclearance-production.up.railway.app/api/v1/applicants?external_id=your_user_123

Headers:
  Authorization: Bearer <your_jwt_token>
```

---

## Testing

### Sandbox Mode

Use API keys starting with `sk_test_` for testing. Test mode:
- Creates real applicant records
- Accepts any document images
- Skips actual AML screening
- Allows manual approval in dashboard

### Test Flow

1. Generate a test token
2. Open the SDK URL
3. Complete the flow with any images
4. Go to GetClearance dashboard
5. Manually approve/reject the applicant
6. Receive webhook

---

## Troubleshooting

### "Invalid API Key"
- Check you're using the correct key for environment (test vs live)
- Ensure key hasn't been revoked

### "CORS Error"
- SDK must be opened via redirect, not embedded in iframe (yet)
- Your redirect_url domain must be configured in GetClearance settings

### Webhook Not Received
- Check webhook URL is publicly accessible
- Check webhook is enabled in settings
- Check you're subscribed to the event type
- Look at webhook delivery logs in dashboard

---

## Support

- **Dashboard**: https://getclearance.vercel.app
- **API Docs**: https://getclearance-production.up.railway.app/docs
- **Email**: support@getclearance.ai

---

## Checklist

- [ ] Got API key from Settings > Integrations
- [ ] Added backend endpoint to generate SDK tokens
- [ ] Added frontend button to start verification
- [ ] Set up webhook endpoint
- [ ] Configured webhook URL in GetClearance settings
- [ ] Tested full flow in sandbox mode
- [ ] Switched to live API key for production
