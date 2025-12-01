# Sumsub Reverse Engineering Context
**Project:** GetClearance / SignalWeave  
**Mission:** Build an AI-native KYC/AML platform that competes with Sumsub  
**Strategy:** Reverse engineer Sumsub's best features, add AI differentiation

---

## 🎯 Project Mission

### What We're Building
**An AI-native KYC/AML compliance platform** that:
- Matches Sumsub's core functionality
- Exceeds Sumsub with deep AI integration
- Offers better developer experience
- Provides transparent pricing
- Delivers faster processing times

### Why This Matters
Every implementation decision should be guided by:
1. **Feature Parity:** Can Sumsub do this? We should too.
2. **AI Differentiation:** Where can AI make this 10x better?
3. **Developer Experience:** Is this easier than Sumsub's approach?
4. **Speed:** Can we process this faster?

---

## 📚 Sumsub Documentation (Source of Truth)

### Core Identity Verification
Essential reading for understanding how ID verification should work:

**ID Verification Workflow:**
- https://docs.sumsub.com/docs/how-id-verification-works
- https://docs.sumsub.com/docs/get-started-with-identity-verification
- https://docs.sumsub.com/docs/conduct-id-verification

**Document Verification:**
- https://docs.sumsub.com/docs/customize-supported-id-documents
- https://docs.sumsub.com/docs/verification-document-templates
- https://docs.sumsub.com/docs/database-validation
- https://docs.sumsub.com/docs/database-validation-matching-configurations

**Liveness Detection:**
- https://docs.sumsub.com/docs/liveness
- https://docs.sumsub.com/docs/live-capture
- https://docs.sumsub.com/docs/short-video-fragment

---

### AML Screening (Critical)
**Must-read for screening implementation:**

**Core Screening:**
- https://docs.sumsub.com/docs/aml-screening
- https://docs.sumsub.com/docs/aml-how-it-works
- https://docs.sumsub.com/docs/fuzzy-matching ⭐ **CRITICAL** - Our fuzzy matching algorithm
- https://docs.sumsub.com/docs/process-aml-screening-results

**Data Sources:**
- https://docs.sumsub.com/docs/data-sources-and-refreshment-times
- https://docs.sumsub.com/docs/ongoing-aml-monitoring

**Screening Presets:**
- https://docs.sumsub.com/docs/complyadvantage-mesh-presets
- https://docs.sumsub.com/docs/best-approval-rate-preset
- https://docs.sumsub.com/docs/extensive-screening-preset

**Review Process:**
- https://docs.sumsub.com/docs/review-aml-cases
- https://docs.sumsub.com/docs/aml-screening-report
- https://docs.sumsub.com/docs/aml-screening-events

---

### Reusable KYC
**For Phase 8+ (future):**
- https://docs.sumsub.com/docs/reusable-identity
- https://docs.sumsub.com/docs/reusable-kyc
- https://docs.sumsub.com/docs/reusable-kyc-via-api
- https://docs.sumsub.com/docs/manage-sharing-partners

---

### Applicant Management
**For understanding applicant lifecycle:**
- https://docs.sumsub.com/docs/applicant-profile-overview
- https://docs.sumsub.com/docs/applicant-statuses
- https://docs.sumsub.com/docs/applicant-risk-labels
- https://docs.sumsub.com/docs/manage-profiles
- https://docs.sumsub.com/docs/approve-and-decline-applicants-manually

---

### API Reference
**For understanding API patterns:**
- https://docs.sumsub.com/reference/about-sumsub-api
- https://docs.sumsub.com/docs/receive-and-interpret-results-via-api

---

## 🔍 What We've Reverse Engineered

Based on comprehensive analysis of Sumsub documentation, we've mapped:

### 1. Entity Mappings
**Sumsub → GetClearance:**
- `Applicant` → `applicants` table
- `Level` → `workflows` + `workflow_versions`
- `Inspection` → `applicant_steps`
- `Review` → `status` field + `cases` table
- `ScreeningCheck` → `screening_checks` table
- `ScreeningHit` → `screening_hits` table

### 2. State Machines
**Applicant Lifecycle:**
```
init → incomplete → pending → in_progress → [approved | rejected | awaiting_service | resubmission_requested]
```

**Document Processing:**
```
pending → processing → [verified | rejected | review]
```

**Screening Workflow:**
```
Create check → Query APIs → Fuzzy matching → Classify hits → Create cases
```

### 3. Critical Algorithms

**Fuzzy Matching (0-100 confidence score):**
- Name matching: 60% weight (Levenshtein + Soundex)
- DOB matching: 30% weight
- Country matching: 10% weight

**Match Classification:**
- 90-100: TRUE_POSITIVE (exact match)
- 60-89: POTENTIAL_MATCH (likely match, needs review)
- 40-59: FALSE_POSITIVE (probably different person)
- <40: UNKNOWN (can't determine)

**PEP Tier Classification:**
- Tier 1: Senior politicians, high-ranking officials
- Tier 2: Mid-level officials, family members
- Tier 3: Close associates
- Tier 4: Former PEPs

### 4. Security Features to Detect
From document verification analysis:
- MRZ checksum validation (CRITICAL - easiest fraud detection)
- Hologram detection
- UV features
- Microprinting
- Watermarks
- Laser engraving
- Template matching

---

## 🎯 Competitive Advantages (Why We'll Win)

### What Sumsub Does Well (Match These)
1. ✅ 220+ country document templates
2. ✅ 40+ language OCR support
3. ✅ Extensive security feature detection
4. ✅ Fuzzy matching with confidence scoring
5. ✅ Comprehensive screening data sources
6. ✅ Level-based verification workflows

### What We Do Better (Our Differentiators)
1. 🚀 **AI-Native Core** - Claude integrated throughout, not bolted on
   - Intelligent document fraud detection (vision AI)
   - Natural language risk summaries with citations
   - Automated case resolution suggestions
   - Applicant-facing assistant

2. 🚀 **Better Developer Experience**
   - Clean REST API (vs Sumsub's complex multipart endpoints)
   - Transparent pricing (vs enterprise-only sales)
   - Self-serve onboarding
   - Better documentation

3. 🚀 **Faster Processing**
   - Parallel processing (screening + OCR + AI simultaneously)
   - Target: <30 seconds (vs Sumsub's "minutes")
   - Auto-approval for low-risk (>70% approval rate)

4. 🚀 **Cost Advantages**
   - Target: <$0.50 per verification
   - No minimum contracts
   - Pay-as-you-go pricing

---

## 📋 Feature Parity Checklist

### Must-Have (For MVP)
- [x] Multi-tenant architecture
- [x] Document upload with presigned URLs
- [x] OpenSanctions screening with fuzzy matching
- [x] AI risk summaries
- [ ] Background workers for async processing
- [ ] OCR with structured data extraction
- [ ] MRZ checksum validation
- [ ] Document fraud detection
- [ ] Webhook notifications
- [ ] Evidence pack export

### Nice-to-Have (Post-MVP)
- [ ] Liveness detection (passive + active)
- [ ] Face matching
- [ ] NFC passport reading
- [ ] Database validation (govt cross-check)
- [ ] Reusable KYC tokens
- [ ] Multi-language support
- [ ] Questionnaires
- [ ] Periodic re-verification
- [ ] Ongoing monitoring

---

## 🏗️ Architecture Principles (From Reverse Engineering)

### 1. Idempotency
**Sumsub Pattern:**
- POST /applicants with same `externalUserId` returns existing (200 OK)
- All mutations support `Idempotency-Key` header

**Our Implementation:**
- Same pattern - check `external_id` before creating
- Support idempotency keys in headers
- Critical for network failures + retries

### 2. Webhook Retry Logic
**Sumsub Pattern:**
- 3 retry attempts with exponential backoff
- Delays: 0s, 30s, 5 minutes
- HMAC signature for verification

**Our Implementation:**
- Exact same retry pattern
- Store in `webhook_deliveries` table
- Background worker handles retries

### 3. List Version Tracking
**Sumsub Pattern:**
- Every screening hit references exact list version
- Format: `{source}-{YYYYMMDD}-{sequence}`
- Example: `OFAC_SDN-20251128-001`

**Our Implementation:**
- `screening_lists` table with version tracking
- `screening_hits.list_version_id` required
- Critical for regulatory audits

### 4. Fuzzy Matching Transparency
**Sumsub Pattern:**
- Return 0-100 confidence score
- Classify: True Positive, Potential Match, False Positive, Unknown
- Show which fields matched (name, DOB, country)

**Our Implementation:**
- Same confidence algorithm
- Same classification buckets
- Store in `screening_hits.match_type`

---

## 💡 When to Reference Sumsub Docs

### During Implementation
**Ask yourself:**
1. "How does Sumsub handle this?"
2. "Is there a Sumsub doc that explains this pattern?"
3. "Are we matching Sumsub's behavior?"

**If unsure, check the docs:**
- Screening: https://docs.sumsub.com/docs/fuzzy-matching
- Documents: https://docs.sumsub.com/docs/database-validation
- Workflows: https://docs.sumsub.com/docs/how-id-verification-works

### During Design Decisions
**Before choosing an approach:**
1. Check what Sumsub does (docs above)
2. Decide: Match exactly, or improve with AI?
3. Document the decision

**Example:**
- Sumsub: Manual fraud detection
- Us: AI-powered fraud detection (better!)
- Decision: Use AI, but support manual override

---

## 🚫 What NOT to Copy from Sumsub

### 1. Complex Multipart APIs
**Sumsub:**
```
POST /applicants/{id}/info/idDoc
Content-Type: multipart/form-data
```

**Us (Better):**
```
POST /documents/upload-url  → Get presigned URL
Client uploads directly to R2
POST /documents/{id}/confirm → Confirm upload
```

### 2. Opaque Pricing
**Sumsub:** Enterprise sales only, no public pricing

**Us:** Transparent pricing, self-serve signup

### 3. Monolithic Verification Levels
**Sumsub:** Complex level configurations

**Us:** Simple workflow steps with conditions

---

## 📊 Success Metrics (vs Sumsub)

| Metric | Sumsub | GetClearance Target |
|--------|--------|---------------------|
| Time to Verification | "Minutes" | <30 seconds |
| Auto-Approval Rate | ~50-60% | >70% |
| False Positive Rate | 10-15% | <5% |
| OCR Accuracy | ~93% | >95% |
| API Latency | ~1-2s | <500ms |
| Cost per Verification | $1-3 | <$0.50 |

---

## 🎓 How to Use This Context

### In Every Chat
1. **Read this file first** - Understand the mission
2. **Check Sumsub docs** - See how they do it
3. **Match or exceed** - Build feature parity + AI
4. **Document decisions** - Why we chose this approach

### When Stuck
1. **Check Sumsub docs** - Is there a pattern we should follow?
2. **Check reverse engineering analysis** - Did we already figure this out?
3. **Ask for clarification** - Better to ask than guess

### When Making Decisions
1. **Feature parity first** - Can Sumsub do this? We should too.
2. **AI differentiation second** - How can AI make this better?
3. **Developer experience third** - Is this easier to use?

---

## 🔗 Quick Reference Links

### Most Important (Read These)
1. **Fuzzy Matching:** https://docs.sumsub.com/docs/fuzzy-matching
2. **AML How It Works:** https://docs.sumsub.com/docs/aml-how-it-works
3. **ID Verification:** https://docs.sumsub.com/docs/how-id-verification-works
4. **Database Validation:** https://docs.sumsub.com/docs/database-validation

### When Implementing Specific Features
- **Screening:** https://docs.sumsub.com/docs/process-aml-screening-results
- **Documents:** https://docs.sumsub.com/docs/customize-supported-id-documents
- **Applicants:** https://docs.sumsub.com/docs/applicant-statuses
- **Liveness:** https://docs.sumsub.com/docs/liveness

---

## ✅ Critical Reminders

1. **We're competing with Sumsub** - Every feature decision matters
2. **Sumsub docs are the spec** - Reference them constantly
3. **AI is our differentiator** - But feature parity comes first
4. **Developer experience matters** - Make it easier than Sumsub
5. **Speed is critical** - <30 seconds vs "minutes"

---

**Remember: We're not just cloning Sumsub, we're building the AI-native version they can't easily become.** 🚀
