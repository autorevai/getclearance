# Current Production Fixes - GetClearance
**Created:** 2025-12-02 9:52 PM
**Last Updated:** 2025-12-02 10:00 PM

---

## Issue Summary

| # | Issue | Status | Priority |
|---|-------|--------|----------|
| 1 | WebSocket connection failing (1006 error) | FIXED | High |
| 2 | Cases API `limit=0` validation error (422) | FIXED | High |
| 3 | API request timeouts on screening endpoints | Monitoring | Medium |
| 4 | Seed Demo Companies (KYB) | PENDING | Low |
| 5 | Seed Demo Cases | PENDING | Low |

---

## Issue 1: WebSocket Connection Failing

### Problem
Frontend attempts to connect to WebSocket at `wss://getclearance-production.up.railway.app/ws` but fails with error code 1006 (abnormal closure).

**Console Errors:**
```
WebSocket connection to 'wss://getclearance-production.up.railway.app/ws?token=...' failed
WebSocket error: Event
WebSocket closed: 1006
Max WebSocket reconnection attempts reached
```

### Root Cause
The backend does not have a WebSocket endpoint implemented. The frontend `useRealtimeUpdates.js` hook expects a `/ws` endpoint that doesn't exist.

### Solution
1. Add WebSocket endpoint to backend using FastAPI's WebSocket support
2. Implement connection manager for handling multiple clients
3. Add authentication via JWT token query parameter

### Files Modified
- `backend/app/api/websocket.py` - New file for WebSocket handler
- `backend/app/main.py` - Add WebSocket route
- `docs/RAILWAY_DEPLOYMENT.md` - Document WebSocket configuration

---

## Issue 2: Cases API Limit Validation Error

### Problem
Dashboard and other pages request case counts with `limit=0` to get only the total count, but the backend validation requires `limit >= 1`.

**Console Errors:**
```
GET https://getclearance-production.up.railway.app/api/v1/cases?status=open&limit=0 422 (Unprocessable Content)
ApiError: limit: Input should be greater than or equal to 1
```

### Root Cause
Frontend `useCaseCounts` hook in `useCases.js` line 265-267 requests:
```javascript
service.list({ status: 'open', limit: 0 }, { signal })
```

Backend `cases.py` line 138 validates:
```python
limit: Annotated[int, Query(ge=1, le=100)] = 50
```

### Solution
Add a dedicated `/cases/counts` endpoint that returns counts without fetching items, and update frontend to use it.

### Files Modified
- `backend/app/api/v1/cases.py` - Add `/counts` endpoint
- `frontend/src/hooks/useCases.js` - Update `useCaseCounts` to use new endpoint
- `frontend/src/services/cases.js` - Add `getCounts()` method

---

## Issue 3: API Request Timeouts

### Problem
Some API requests timeout (screening checks, lists), causing promise rejections.

**Console Errors:**
```
ApiError: Request timed out
```

### Root Cause
- Screening endpoints may be slow due to external API calls
- Database queries may be slow without proper indexes
- Railway cold starts

### Status
Monitoring - may need further investigation with actual slow queries.

---

## Issue 4: Seed Demo Companies

### Problem
Companies page is empty - needs demo data for crypto funds onboarding

### Solution
Create seed script with realistic crypto/fintech companies

### Status
PENDING - Lower priority than fixing errors

---

## Issue 5: Seed Demo Cases

### Problem
Case Management page is empty - needs demo compliance cases

### Solution
Create seed script with realistic compliance cases

### Status
PENDING - Lower priority than fixing errors

---

## Deployment Notes

After implementing fixes:

1. **Backend changes** - Push to trigger Railway auto-deploy
2. **Frontend changes** - Push to trigger Vercel auto-deploy
3. **Verify WebSocket** - Check browser console for successful connection
4. **Verify counts** - Check Cases page loads without 422 errors

### Testing Checklist

- [ ] WebSocket connects successfully (or fails gracefully)
- [ ] No 422 errors on Dashboard
- [ ] No 422 errors on Cases page
- [ ] Case counts display correctly
- [ ] Real-time updates work (create applicant, see toast)

---

## Progress Log

| Time | Fix | Status |
|------|-----|--------|
| 10:00 PM | Created fix plan document | DONE |
| 10:05 PM | Added WebSocket endpoint (`backend/app/api/websocket.py`) | DONE |
| 10:06 PM | Added `/cases/counts` endpoint | DONE |
| 10:07 PM | Updated frontend `useCaseCounts` hook | DONE |
| 10:08 PM | Updated deployment documentation | DONE |

---

## Related Documentation

- `RAILWAY_DEPLOYMENT.md` - Railway configuration
- `AUTH0_INTEGRATION.md` - Auth0 setup
- `README.md` - Project overview
