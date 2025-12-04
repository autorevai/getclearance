# Terminal 5: Advanced Features via API Integrations
**Project:** GetClearance / SignalWeave
**Created:** December 4, 2025
**Last Updated:** December 4, 2025
**Purpose:** Integrate AWS Rekognition, IPQualityScore, Claude Vision, and other APIs for production-ready biometrics and fraud detection

---

## Overview

Terminal 5 focuses on replacing placeholder implementations with real third-party API integrations. These are **table-stakes features** for crypto exchange KYC:

| Sprint | Feature | API Provider | Effort | Priority | Status |
|--------|---------|--------------|--------|----------|--------|
| A1 | Face Matching + Liveness | AWS Rekognition | 1-2 days | **CRITICAL** | ✅ DONE |
| A2 | Fraud Detection Suite | IPQualityScore | 1 day | HIGH | ✅ DONE |
| A3 | Address Verification | Smarty | 0.5 days | MEDIUM | ✅ DONE |
| A4 | Reusable KYC Tokens | Internal | - | MEDIUM | ✅ DONE |
| A5 | Document Type Detection | Claude Vision | 1 day | MEDIUM | ✅ DONE |
| A6 | Video Identification | Twilio Video | 3-4 days | LOW | TODO |

**Total Effort:** A1-A5 COMPLETE, A6 optional (3-4 days)

---

## Pre-requisites Checklist

Before starting Terminal 5, verify these are configured:

```bash
# Required Environment Variables (verify in Railway/production)
AWS_ACCESS_KEY_ID=<your-aws-key>           # ✅ For Rekognition + Textract
AWS_SECRET_ACCESS_KEY=<your-aws-secret>    # ✅ For Rekognition + Textract
AWS_REGION=us-east-1                       # ✅ Default region

# For Sprint A2 - IPQualityScore
IPQS_API_KEY=<your-ipqualityscore-key>     # Get from ipqualityscore.com

# For Sprint A3 - Smarty Address Verification
SMARTY_AUTH_ID=<your-smarty-auth-id>       # Get from smarty.com
SMARTY_AUTH_TOKEN=<your-smarty-auth-token>

# For Sprint A5 - Claude Vision (already have this)
ANTHROPIC_API_KEY=<your-anthropic-key>     # Already configured for AI features
```

### AWS IAM Policy Required

Your AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:DetectDocumentText",
        "textract:AnalyzeDocument",
        "rekognition:CompareFaces",
        "rekognition:DetectFaces",
        "rekognition:DetectLabels"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Sprint A1: AWS Rekognition Face Matching + Liveness ✅ DONE

**Priority:** CRITICAL - Required for crypto exchange KYC
**Effort:** 1-2 days
**Cost:** ~$0.001/image (~$20/month for 10K verifications)
**Status:** ✅ IMPLEMENTED

### Implementation Summary

**File:** `backend/app/services/biometrics.py`

**Features Implemented:**
- `compare_faces()` - AWS Rekognition CompareFaces for ID photo vs selfie matching
- `detect_liveness()` - Passive liveness detection via quality analysis (brightness, sharpness, pose, eyes open)
- `detect_faces()` - Face detection with emotions, age range, landmarks
- `verify_applicant_selfie()` - Complete verification workflow combining face match + liveness

**API Endpoints:** `backend/app/api/v1/biometrics.py`
- `POST /api/v1/biometrics/compare` - Compare two faces
- `POST /api/v1/biometrics/liveness` - Check liveness
- `POST /api/v1/biometrics/detect` - Detect faces
- `POST /api/v1/biometrics/verify/{applicant_id}` - Full verification
- `GET /api/v1/biometrics/status` - Service status

### Sprint A1 Prompt (For Reference)

```
## Sprint A1: Implement AWS Rekognition for Face Matching + Liveness

### Context
The file `backend/app/services/biometrics.py` needs to integrate real AWS Rekognition APIs. AWS credentials are already configured in the environment.

### Requirements

1. **Update `backend/app/services/biometrics.py`:**
   - Keep the existing data classes (FaceQuality, FaceComparisonResult, LivenessResult, etc.)
   - Replace mock methods with real `rekognition.compare_faces()` and `rekognition.detect_faces()`
   - Add boto3 client initialization
   - Handle AWS errors gracefully (InvalidParameterException, ImageTooLargeException, etc.)

2. **AWS Rekognition API Reference:**
   ```python
   # Compare Faces
   response = rekognition.compare_faces(
       SourceImage={'Bytes': source_bytes},
       TargetImage={'Bytes': target_bytes},
       SimilarityThreshold=80.0,
       QualityFilter='AUTO'
   )

   # Detect Faces (for liveness/quality)
   response = rekognition.detect_faces(
       Image={'Bytes': image_bytes},
       Attributes=['ALL']  # Returns quality, emotions, landmarks
   )
   ```

3. **Liveness Detection Strategy:**
   - Use quality metrics as proxy: Brightness > 40, Sharpness > 40, Pose within ±30 degrees
   - Eyes must be open, no sunglasses
   - Return confidence based on quality score average

4. **Error Handling:**
   - InvalidParameterException: Bad image format
   - ImageTooLargeException: Image > 5MB
   - Return graceful error results, don't raise exceptions

### Files Modified
- `backend/app/services/biometrics.py` (main implementation)

### Success Criteria
- Face comparison returns real similarity scores from AWS
- Quality metrics extracted from AWS response
- `is_mock: false` in API responses
```

---

## Sprint A2: IPQualityScore Fraud Detection Suite ✅ DONE

**Priority:** HIGH - Recommended for crypto KYC
**Effort:** 1 day
**Cost:** ~$0.0003/query (~$30/month for 100K queries)
**Status:** ✅ IMPLEMENTED

### Implementation Summary

**File:** `backend/app/services/device_intel.py`

**Features Implemented:**
- `check_ip()` - VPN, proxy, TOR, datacenter, bot, crawler detection
- `check_email()` - Disposable email, deliverability, fraud score
- `check_phone()` - VOIP, carrier, line type, fraud score
- `check_device()` - Device fingerprint analysis
- `check_all()` - Combined check with aggregated risk

**Data Classes:**
- `IPCheckResult` - IP reputation with fraud_score, is_vpn, is_tor, etc.
- `EmailCheckResult` - Email validation with disposable, deliverability
- `PhoneCheckResult` - Phone validation with line_type, carrier
- `DeviceCheckResult` - Device fingerprint with risk indicators

**API Endpoints:** `backend/app/api/v1/device_intel.py`
- `POST /api/v1/device-intel/ip` - Check IP address
- `POST /api/v1/device-intel/email` - Validate email
- `POST /api/v1/device-intel/phone` - Validate phone
- `POST /api/v1/device-intel/check-all` - Combined check
- `GET /api/v1/device-intel/status` - Service status

### Sprint A2 Prompt (For Reference)

```
## Sprint A2: Implement IPQualityScore Fraud Detection

### Context
We need device intelligence and fraud detection for crypto KYC. IPQualityScore provides IP, email, phone, and device fraud detection in one API.

### Requirements

1. **Create `backend/app/services/device_intel.py`:**
   - IPQualityScore API integration
   - Async HTTP client with httpx
   - Data classes for each check type (IP, Email, Phone, Device)
   - Risk level calculation based on fraud scores

2. **IPQualityScore API Reference:**
   ```
   # IP Check
   GET https://ipqualityscore.com/api/json/ip/{api_key}/{ip}

   # Email Check
   GET https://ipqualityscore.com/api/json/email/{api_key}/{email}

   # Phone Check
   GET https://ipqualityscore.com/api/json/phone/{api_key}/{phone}
   ```

3. **Risk Level Thresholds:**
   - Critical: fraud_score >= 85
   - High: fraud_score >= 75
   - Medium: fraud_score >= 50
   - Low: fraud_score < 50

4. **Integration with Risk Engine:**
   - VPN = 30 risk points
   - TOR = 50 risk points
   - Datacenter = 25 risk points
   - Disposable email = 40 risk points
   - VOIP phone = 30 risk points

5. **Create API endpoints at `backend/app/api/v1/device_intel.py`**

### Files Created
- `backend/app/services/device_intel.py`
- `backend/app/api/v1/device_intel.py`

### Success Criteria
- All 4 fraud check endpoints working
- Risk engine incorporates device signals
- Graceful fallback if API key not configured
```

---

## Sprint A3: Address Verification (Smarty) ✅ DONE

**Priority:** MEDIUM
**Effort:** 0.5 days
**Cost:** Free tier available (~$100/month for high volume)
**Status:** ✅ IMPLEMENTED

### Implementation Summary

**File:** `backend/app/services/address_verification.py`

**Features Implemented:**
- `verify_address()` - US address verification via Smarty API
- `verify_international()` - International address verification via Google Places fallback
- `get_high_risk_countries()` - FATF grey/black list countries
- Address standardization and geocoding
- Risk assessment based on country and verification status

**Data Classes:**
- `StandardizedAddress` - Normalized address with geocoding
- `AddressVerificationResult` - Verification status and confidence

**API Endpoints:** `backend/app/api/v1/addresses.py`
- `POST /api/v1/addresses/verify` - Verify standalone address
- `POST /api/v1/addresses/applicants/{id}/verify` - Verify applicant address
- `GET /api/v1/addresses/countries` - Get country list with risk levels

### Sprint A3 Prompt (For Reference)

```
## Sprint A3: Address Verification with Smarty

### Context
Address verification is required for AML compliance. Smarty provides US address validation, and we need international fallback.

### Requirements

1. **Update `backend/app/services/address_verification.py`:**
   - Smarty API integration for US addresses
   - Google Places API fallback for international
   - High-risk country detection (FATF list)
   - Address standardization and geocoding

2. **Smarty API Reference:**
   ```
   GET https://us-street.api.smartystreets.com/street-address
   ?auth-id={auth_id}&auth-token={auth_token}
   &street={street}&city={city}&state={state}&zipcode={zip}
   ```

3. **High-Risk Countries (FATF):**
   - Black list: KP, IR
   - Grey list: AF, BY, CF, CD, CU, GW, HT, IQ, LB, LY, ML, MM, NI, PK, PA, RU, SO, SS, SD, SY, VE, YE, ZW

4. **Verification Levels:**
   - verified: Exact match found
   - partial_match: Address found with corrections
   - unverified: Could not verify
   - invalid: Address does not exist

### Success Criteria
- US addresses verified via Smarty
- High-risk countries flagged
- Address standardized and geocoded
```

---

## Sprint A4: Reusable KYC Tokens ✅ DONE

**Priority:** MEDIUM
**Effort:** Already implemented
**Status:** ✅ IMPLEMENTED (Internal feature)

### Implementation Summary

**Files:**
- `backend/app/services/kyc_share.py` - Token generation, validation, access tracking
- `backend/app/models/kyc_share.py` - ShareToken, ShareAccess models
- `backend/app/api/v1/kyc_share.py` - Token management endpoints
- `frontend/src/components/kyc-share/` - Frontend components

**Features:**
- Generate shareable KYC tokens with permission scoping
- Time-limited and use-limited tokens
- Access history tracking
- Consent flow for sharing
- Token revocation

---

## Sprint A5: Document Type Detection (Claude Vision) ✅ DONE

**Priority:** MEDIUM
**Effort:** 1 day
**Cost:** ~$0.01/classification (uses existing Claude API)
**Status:** ✅ IMPLEMENTED

### Implementation Summary

**File:** `backend/app/services/document_classifier.py`

**Features Implemented:**
- `classify()` - Document type detection using Claude Vision
- Detects: passport, drivers_license, id_card, residence_permit, visa, utility_bill, bank_statement, selfie
- Country of issue detection (ISO 3166-1 alpha-2)
- Document side detection (front/back/single)
- OCR template suggestion based on classification

**Data Classes:**
- `DocumentType` - Enum of supported document types
- `DocumentSide` - front/back/single
- `ClassificationResult` - Classification with confidence and detected fields

**Integration:**
- Automatically runs before OCR in `document_worker.py`
- Classification result selects appropriate OCR template
- Results stored in `extracted_data["_classification"]`

**API Endpoints:** `backend/app/api/v1/documents.py`
- `POST /api/v1/documents/{id}/classify` - Classify existing document
- `POST /api/v1/documents/classify` - Classify uploaded image (preview)

### Sprint A5 Prompt (For Reference)

```
## Sprint A5: Document Type Detection with Claude Vision

### Context
Before running OCR, we should auto-detect document type and country using Claude Vision.

### Requirements

1. **Create `backend/app/services/document_classifier.py`:**
   ```python
   class DocumentClassifier:
       DOCUMENT_TYPES = [
           "passport", "drivers_license", "id_card",
           "residence_permit", "visa", "utility_bill",
           "bank_statement", "selfie", "unknown"
       ]

       async def classify(self, image_bytes: bytes) -> ClassificationResult:
           """Classify document type and extract metadata."""
           pass
   ```

2. **Claude Vision Prompt:**
   ```
   Analyze this identity document image and return JSON:
   {
     "document_type": "passport|drivers_license|id_card|...",
     "country_code": "US|GB|...",
     "side": "front|back|single",
     "confidence": 85,
     "detected_fields": ["photo", "mrz", "name", "dob", "expiry"]
   }
   ```

3. **Integration with Document Worker:**
   - Call classifier before OCR
   - Store document_type in documents table
   - Route to appropriate OCR template

4. **Tests:**
   - Create `backend/tests/test_document_classifier.py`
   - Test classification for each document type
   - Test error handling

### Files Created
- `backend/app/services/document_classifier.py`
- `backend/tests/test_document_classifier.py`

### Success Criteria
- Document type detected before OCR
- Country code extracted
- OCR template selection based on document type
- 35+ tests passing
```

---

## Sprint A6: Video Identification (Twilio Video) - TODO

**Priority:** LOW - Only if regulatory requirements demand it
**Effort:** 3-4 days
**Cost:** ~$0.004/minute (~$12/month for 3000 minutes)

### Overview

Video identification allows real-time video calls between applicants and compliance officers for enhanced verification. This is typically required for high-value transactions or specific regulatory regimes.

### Sprint A6 Prompt

```
## Sprint A6: Video Identification with Twilio Video

### Context
Some regulatory environments require video identification for KYC. This sprint implements real-time video calls between applicants and compliance officers.

### Requirements

1. **Create `backend/app/services/video_verification.py`:**
   ```python
   from twilio.rest import Client
   from twilio.jwt.access_token import AccessToken
   from twilio.jwt.access_token.grants import VideoGrant

   class VideoVerificationService:
       def __init__(self):
           self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

       async def create_room(self, applicant_id: str) -> VideoRoom:
           """Create a video room for verification session."""
           room = self.client.video.rooms.create(
               unique_name=f"kyc-{applicant_id}",
               type='group',
               record_participants_on_connect=True
           )
           return VideoRoom(
               room_sid=room.sid,
               room_name=room.unique_name,
               recording_enabled=True
           )

       async def generate_token(self, identity: str, room_name: str) -> str:
           """Generate access token for participant."""
           token = AccessToken(
               settings.twilio_account_sid,
               settings.twilio_api_key,
               settings.twilio_api_secret,
               identity=identity
           )
           token.add_grant(VideoGrant(room=room_name))
           return token.to_jwt()

       async def get_recording(self, room_sid: str) -> bytes:
           """Get video recording after session."""
           recordings = self.client.video.rooms(room_sid).recordings.list()
           if recordings:
               # Download recording
               pass

       async def complete_session(self, room_sid: str, result: str, notes: str):
           """Mark session as complete with result."""
           pass
   ```

2. **Create `backend/app/api/v1/video.py`:**
   - `POST /api/v1/video/rooms` - Create video room
   - `POST /api/v1/video/rooms/{id}/join` - Get token to join
   - `POST /api/v1/video/rooms/{id}/complete` - Mark session complete
   - `GET /api/v1/video/rooms/{id}/recording` - Get recording

3. **Create frontend components:**
   ```
   frontend/src/components/video/
   ├── VideoRoom.jsx          - Main video room component
   ├── VideoControls.jsx      - Mute, camera, end call
   ├── ParticipantView.jsx    - Remote participant video
   ├── VerificationChecklist.jsx - Checklist for operator
   └── index.js
   ```

4. **Database Schema:**
   ```python
   class VideoSession(TenantBase):
       __tablename__ = "video_sessions"

       applicant_id = Column(UUID, ForeignKey("applicants.id"))
       room_sid = Column(String, unique=True)
       room_name = Column(String)
       status = Column(String)  # pending, in_progress, completed, failed
       started_at = Column(DateTime)
       ended_at = Column(DateTime)
       duration_seconds = Column(Integer)
       recording_url = Column(String)
       operator_id = Column(UUID, ForeignKey("users.id"))
       verification_result = Column(String)  # verified, failed, inconclusive
       notes = Column(Text)
   ```

5. **Update config.py:**
   ```python
   # Twilio Video
   twilio_account_sid: str = Field(default="", repr=False)
   twilio_auth_token: str = Field(default="", repr=False)
   twilio_api_key: str = Field(default="", repr=False)
   twilio_api_secret: str = Field(default="", repr=False)
   ```

6. **Frontend Integration:**
   - Use twilio-video SDK for WebRTC
   - Display remote video in main view
   - Show verification checklist to operator
   - Record operator's verification decision

### Environment Variables
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_API_KEY=SKxxxxxxxx
TWILIO_API_SECRET=xxxxxxxx
```

### Files to Create
- `backend/app/services/video_verification.py`
- `backend/app/api/v1/video.py`
- `backend/app/models/video_session.py`
- `backend/migrations/versions/xxxxx_add_video_sessions.py`
- `frontend/src/components/video/VideoRoom.jsx`
- `frontend/src/components/video/VideoControls.jsx`
- `frontend/src/components/video/ParticipantView.jsx`
- `frontend/src/components/video/VerificationChecklist.jsx`
- `frontend/src/services/video.js`
- `frontend/src/hooks/useVideo.js`

### Success Criteria
- Video rooms can be created for applicants
- Both applicant and operator can join with video/audio
- Sessions are recorded
- Operator can mark verification result
- Recordings stored and accessible for audit
```

---

## Implementation Status Summary

| Sprint | Feature | Files | Status |
|--------|---------|-------|--------|
| A1 | Face Matching + Liveness | `services/biometrics.py`, `api/v1/biometrics.py` | ✅ DONE |
| A2 | Fraud Detection | `services/device_intel.py`, `api/v1/device_intel.py` | ✅ DONE |
| A3 | Address Verification | `services/address_verification.py`, `api/v1/addresses.py` | ✅ DONE |
| A4 | Reusable KYC | `services/kyc_share.py`, `api/v1/kyc_share.py`, `models/kyc_share.py` | ✅ DONE |
| A5 | Document Classification | `services/document_classifier.py`, integrated in `workers/document_worker.py` | ✅ DONE |
| A6 | Video Identification | Not yet implemented | TODO |

---

## API Cost Summary

| Sprint | API | Cost per Call | Monthly @ 10K |
|--------|-----|---------------|---------------|
| A1 | AWS Rekognition | $0.001/image | ~$20 |
| A2 | IPQualityScore | $0.0003/query | ~$10 |
| A3 | Smarty | Free-$0.01/lookup | ~$0-100 |
| A5 | Claude Vision | $0.01/image | ~$100 |
| A6 | Twilio Video | $0.004/min | ~$12 |
| **Total** | | | **~$150-250/month** |

---

## Post-Sprint Verification

After completing Terminal 5 sprints, verify:

```bash
# 1. Biometrics working (A1)
curl -X GET https://your-api/api/v1/biometrics/status
# Should return: {"status": "operational", "provider": "aws_rekognition", "is_mock": false}

# 2. Fraud detection working (A2)
curl -X GET https://your-api/api/v1/device-intel/status
# Should return: {"status": "operational", "provider": "ipqualityscore"}

# 3. Address verification working (A3)
curl -X POST https://your-api/api/v1/addresses/verify \
  -d '{"street": "1600 Pennsylvania Ave", "city": "Washington", "state": "DC", "postal_code": "20500"}'
# Should return verified address with geocoding

# 4. Document classification working (A5)
curl -X POST https://your-api/api/v1/documents/classify \
  -F "file=@passport.jpg"
# Should return: {"document_type": "passport", "country_code": "US", "confidence": 95}

# 5. Full applicant verification
curl -X POST https://your-api/api/v1/biometrics/verify/{applicant_id}
# Should compare selfie vs ID photo and return real scores
```

---

## Ready for Production

With Terminal 5 Sprints A1-A5 complete, your crypto exchange customer can now:

| Capability | Status | API |
|------------|--------|-----|
| **Face Matching** (ID vs Selfie) | ✅ READY | AWS Rekognition |
| **Liveness Detection** | ✅ READY | AWS Rekognition |
| **VPN/Proxy Detection** | ✅ READY | IPQualityScore |
| **Email Validation** | ✅ READY | IPQualityScore |
| **Phone Validation** | ✅ READY | IPQualityScore |
| **Address Verification** | ✅ READY | Smarty |
| **Document Classification** | ✅ READY | Claude Vision |
| **Reusable KYC** | ✅ READY | Internal |

---

**Last Updated:** December 4, 2025
**Status:** Sprints A1-A5 COMPLETE, A6 optional
