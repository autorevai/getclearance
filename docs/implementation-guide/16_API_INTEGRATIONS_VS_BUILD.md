# API Integrations vs Build from Scratch
**Project:** GetClearance
**Created:** December 2, 2025
**Purpose:** Cost-effective API alternatives to building complex features

---

## Executive Summary

Building everything from scratch is risky and slow. Here's where APIs make sense:

| Feature | Build Cost | API Cost | Recommendation |
|---------|-----------|----------|----------------|
| Face Matching | High risk, ML expertise needed | $0.001/image | **USE API** |
| Liveness Detection | Very high risk, 6+ months | $0.01-0.02/check | **USE API** |
| Device Fingerprinting | Medium risk | $0.0003-0.01/query | **USE API** |
| Email/Phone Validation | Low risk but why bother | Free-$0.01/check | **USE API** |
| VPN/Proxy Detection | Medium risk | $0.0003/query | **USE API** |
| AML Screening | Already done | Free (OpenSanctions) | **KEEP CURRENT** |
| OCR | Already done | $1.50/1000 pages | **KEEP CURRENT** |
| Address Verification | Medium complexity | $0.01-0.05/lookup | **USE API** |
| Government DB Validation | Impossible to build | $$$ per country | **USE API (selective)** |

**Bottom Line:** Use APIs for biometrics, fraud signals, and validation. Keep building core KYC/AML workflow logic.

---

## Detailed API Recommendations by Feature

### 1. Face Matching (1:1 Comparison)

**Why Use API:** Neural network training requires millions of face images, ML expertise, and ongoing maintenance. One bug = massive fraud exposure.

| Provider | Pricing | Accuracy | Best For |
|----------|---------|----------|----------|
| **AWS Rekognition** | ~$0.001/image | 99%+ | Already on AWS, simple integration |
| **Azure Face API** | $1/1,000 tx | 99%+ | Microsoft ecosystem |
| **Luxand.cloud** | $0.0025/request | 98%+ | Budget option |

**Recommendation:** **AWS Rekognition** - You're already using AWS for Textract, same credentials.

```python
# Example integration cost
# 10,000 verifications/month = $10/month
# 100,000 verifications/month = $100/month
```

**Sources:**
- [Amazon Rekognition Pricing](https://www.saasworthy.com/product/amazon-rekognition/pricing)
- [Azure Face API vs Rekognition](https://www.g2.com/compare/amazon-rekognition-vs-azure-face-api)
- [Top Face Matching APIs](https://luxand.cloud/face-recognition-blog/top-face-matching-apis-in-2024)

---

### 2. Liveness Detection (Anti-Spoofing)

**Why Use API:** Detecting photos-of-photos, screens, masks, and deepfakes requires cutting-edge ML. FaceTec has a $100K spoof bounty program - that's how hard this is.

| Provider | Pricing | Features | Notes |
|----------|---------|----------|-------|
| **AWS Rekognition** | $0.001/image | Basic liveness | Same API as face matching |
| **Azure Face API** | $15/1,000 tx | Advanced liveness | More expensive but better |
| **iProov** | Quote-based | Passive liveness | Enterprise, very accurate |
| **FaceTec** | Quote-based | 3D liveness, 1:12.8M FAR | Industry leader, used by Jumio/Onfido |

**Recommendation:** Start with **AWS Rekognition** (cheap, integrated), upgrade to **Azure Liveness** or **FaceTec** if fraud becomes an issue.

```python
# AWS basic liveness
# 10,000 checks/month = $10/month

# Azure advanced liveness
# 10,000 checks/month = $150/month
```

**Sources:**
- [Best Liveness Detection Software 2025](https://www.identomat.com/blog/best-liveness-detection-software)
- [Liveness Detection Comparison](https://blog.humanode.io/liveness-detection-solutions-a-comparison/)
- [Veriff vs Onfido](https://www.veriff.com/brand-comparison/veriff-vs-onfido)

---

### 3. Device Fingerprinting & Fraud Signals

**Why Use API:** Browser fingerprinting is a cat-and-mouse game. Commercial providers update weekly to counter evasion techniques.

| Provider | Pricing | Features | Best For |
|----------|---------|----------|----------|
| **IPQualityScore** | $0.0003/query | VPN, proxy, device, phone, email | Best value, comprehensive |
| **FingerprintJS Pro** | $99-999/mo | 99.5% accuracy, device ID | High accuracy needs |
| **Castle** | $33/mo for 10K | Device + analytics | Multi-accounting detection |
| **SEON** | Free-$299/mo | Device + social lookup | Email/phone enrichment |

**Recommendation:** **IPQualityScore** - Best value, covers VPN/proxy detection, phone validation, email validation, AND device fingerprinting in one API.

```python
# IPQS pricing example
# 100,000 queries/month = ~$30/month
# Covers: VPN detection, proxy detection, device fingerprint, fraud score
```

**Sources:**
- [IPQualityScore Plans & Pricing](https://www.ipqualityscore.com/plans)
- [9 Device Fingerprinting Solutions](https://blog.castle.io/9-device-fingerprinting-solutions-for-developers/)
- [FingerprintJS Pricing](https://fingerprint.com/pricing/)

---

### 4. Email Validation (Disposable Detection)

**Why Use API:** Maintaining a list of 3,000+ disposable email domains is tedious. APIs also check deliverability.

| Provider | Pricing | Features | Notes |
|----------|---------|----------|-------|
| **Abstract API** | Free tier + paid | Disposable, deliverability | Simple, good free tier |
| **ZeroBounce** | $18/2,000 credits | 99% accuracy, 30+ types | Most comprehensive |
| **Kickbox** | $14/1,000 | High accuracy | Good for marketing |
| **Emailable** | 250 free/mo | Fast, Resend partnership | Best free tier |
| **IPQualityScore** | Included | Part of fraud suite | Already recommended |

**Recommendation:** Use **IPQualityScore** (already getting for device fingerprinting) - email validation is included.

**Sources:**
- [Best Email Verification APIs](https://resend.com/blog/best-email-verification-apis)
- [16 Best Email Verification API Services](https://www.usebouncer.com/16-best-email-verification-api-services/)

---

### 5. Phone Number Validation

**Why Use API:** Carrier lookups, VOIP detection, line type - requires telco partnerships.

| Provider | Pricing | Features | Notes |
|----------|---------|----------|-------|
| **IPQualityScore** | $0.0003/query | Line type, carrier, VOIP, risk | Best value |
| **Twilio Lookup** | $0.005/lookup | Carrier, line type | Trusted, simple |
| **NumVerify** | Free-$10/mo | Basic validation | Budget option |

**Recommendation:** **IPQualityScore** - Already included with device fingerprinting subscription.

**Sources:**
- [IPQualityScore Phone Validation](https://www.ipqualityscore.com/solutions/phone-validation)

---

### 6. Address Verification & Geocoding

**Why Use API:** USPS/postal data licensing, international address formats, geocoding databases.

| Provider | Pricing | Coverage | Best For |
|----------|---------|----------|----------|
| **Smarty** | Free-$12,600/yr | US + International | Best accuracy, US focus |
| **Melissa** | Free-$12,600/yr | 240+ countries | Global coverage |
| **Loqate** | Quote-based | Global | Enterprise, rooftop geocoding |
| **Google Places** | $0.017/request | Global | Already have Google? |

**Recommendation:** **Smarty** for US-focused, **Melissa** for global. Start with free tiers.

```python
# Smarty pricing example
# 50,000 lookups/month = Free tier
# 100,000 lookups/year = ~$100
```

**Sources:**
- [Smarty Pricing](https://www.g2.com/products/smarty-smarty/pricing)
- [Melissa Pricing](https://www.g2.com/products/melissa-global-address-verification/pricing)

---

### 7. Government Database Validation (KYC Data Sources)

**Why Use API:** You cannot build this - requires government/financial institution partnerships.

| Provider | Pricing | Coverage | Best For |
|----------|---------|----------|----------|
| **Socure** | Quote (expensive) | US, SSN, govt DBs | Banks, high-volume |
| **Persona** | $250/mo+ | 200+ countries, Enterprise only | Mid-market |
| **Alloy** | Quote-based | Global, 100+ data sources | Orchestration platform |
| **Plaid Identity** | Quote-based | US, bank-verified | Already using Plaid? |

**Recommendation:** **Persona** for MVP (clear pricing), upgrade to **Socure** or **Alloy** at scale.

```python
# Persona pricing
# Essential plan = $250/month
# Includes: govt ID verification, database checks
```

**Sources:**
- [Socure Overview](https://www.capterra.com/p/157006/ID/)
- [Persona Pricing](https://www.capterra.com/p/199701/Persona/)
- [Alloy Data Sources](https://use.alloy.co/rs/915-RMN-264/images/alloy_data-sources.pdf)

---

### 8. Document Verification (ID Templates)

**Why Use API:** Building templates for 10,000+ document types across 220 countries is years of work.

| Provider | Pricing | Documents | Best For |
|----------|---------|-----------|----------|
| **Microblink** | Quote-based | Broadest coverage | Global, all doc types |
| **Regula** | Quote-based | Strong template matching | On-premise option |
| **Jumio** | Quote (expensive) | Full stack | Enterprise, all-in-one |
| **Onfido** | Quote-based | Good coverage | UK/EU focus |

**Recommendation:** Keep your current **AWS Textract** for OCR, consider **Microblink** SDK for document detection/template matching if you need more countries.

**Sources:**
- [Microblink ID Verification](https://microblink.com/resources/blog/id-verification-providers/)
- [Top ID Verification Software](https://microblink.com/resources/blog/id-verification-software/)

---

### 9. AML Screening (Keep Current)

**Current:** OpenSanctions (free, open source) - **Keep this!**

If you need more coverage later:

| Provider | Pricing | Coverage | Notes |
|----------|---------|----------|-------|
| **OpenSanctions** | Free | Sanctions, PEP, basic | Current implementation |
| **ComplyAdvantage** | Quote (mid-range) | Real-time, AI-driven | Good for fintechs |
| **Dow Jones** | Quote (expensive) | Deepest coverage | Enterprise only |
| **Sanction Scanner** | Quote-based | 3000+ sanctions lists | Mid-market option |

**Recommendation:** Stay with **OpenSanctions** unless customers demand specific lists.

**Sources:**
- [Top 10 AML & Sanctions Software 2025](https://www.sanctions.io/blog/blog-top-aml-sanctions-software-2025)
- [ComplyAdvantage Competitors](https://www.planetcompliance.com/anti-money-laundering/complyadvantage-competitors/)

---

### 10. OCR (Keep Current)

**Current:** AWS Textract (~$1.50/1000 pages) - **Keep this!**

Your implementation is already good. Alternatives if needed:

| Provider | Pricing | Accuracy | Notes |
|----------|---------|----------|-------|
| **AWS Textract** | $1.50/1000 pages | 93%+ | Current implementation |
| **Azure Document AI** | Similar | Higher in some benchmarks | Alternative |
| **Google Document AI** | Similar | Weaker on invoices | Not recommended |
| **ABBYY** | Expensive | 99%+ on print | On-premise option |

**Sources:**
- [Top 6 OCR Systems 2025](https://www.marktechpost.com/2025/11/02/comparing-the-top-6-ocr-optical-character-recognition-models-systems-in-2025/)
- [AWS Textract Alternatives](https://www.docsumo.com/compare/amazon-textract-alternative-docsumo)

---

## Recommended API Stack

### Tier 1: Must Have (Implement Now)

| Feature | Provider | Monthly Cost (10K users) | Integration Effort |
|---------|----------|--------------------------|-------------------|
| Face Matching | AWS Rekognition | ~$10 | 1-2 days |
| Liveness Detection | AWS Rekognition | ~$10 | Same as above |
| Email/Phone/Device/VPN | IPQualityScore | ~$30 | 1 day |

**Total Tier 1:** ~$50/month for 10,000 verifications

### Tier 2: Nice to Have (Add When Needed)

| Feature | Provider | Monthly Cost | Integration Effort |
|---------|----------|--------------|-------------------|
| Address Verification | Smarty | Free-$100 | 1 day |
| Advanced Liveness | Azure Face API | ~$150 | 1 day |
| Government DB Validation | Persona | $250+ | 2-3 days |

**Total Tier 2:** ~$400-500/month

### Tier 3: Enterprise (Customer Demand)

| Feature | Provider | Monthly Cost | Notes |
|---------|----------|--------------|-------|
| Full ID Document Coverage | Microblink | Quote | 220+ countries |
| Premium AML Data | ComplyAdvantage | Quote | Real-time updates |
| Video ID | Twilio Video | ~$0.004/min | Major feature |

---

## Updated Sprint Plan with APIs

### Replace Terminal 5 Sprints

Instead of building these features from scratch, integrate APIs:

| Original Sprint | Replace With | Effort | Cost |
|-----------------|--------------|--------|------|
| A1: Face Matching (3-4 days) | AWS Rekognition integration | **1 day** | $0.001/image |
| A2: Liveness Detection (3-4 days) | AWS Rekognition integration | **Same day** | Included |
| A3: Device Intelligence (2-3 days) | IPQualityScore integration | **1 day** | $0.0003/query |
| A4: Reusable KYC (4-5 days) | Keep as planned | 4-5 days | Internal |
| A5: Doc Templates (5-7 days) | Consider Microblink SDK | **2 days** | Quote |
| A6: Video ID (7-10 days) | Twilio Video integration | **3-4 days** | $0.004/min |

**Time Saved:** ~15 days of risky development
**Bug Risk Reduction:** Massive - using battle-tested services

---

## Integration Code Examples

### AWS Rekognition (Face Matching + Liveness)

```python
# backend/app/services/biometrics.py
import boto3
from botocore.exceptions import ClientError

class BiometricsService:
    def __init__(self):
        self.client = boto3.client('rekognition', region_name='us-east-1')

    async def compare_faces(
        self,
        source_image: bytes,  # ID photo
        target_image: bytes,  # Selfie
        similarity_threshold: float = 90.0
    ) -> dict:
        """Compare two faces, return similarity score."""
        try:
            response = self.client.compare_faces(
                SourceImage={'Bytes': source_image},
                TargetImage={'Bytes': target_image},
                SimilarityThreshold=similarity_threshold
            )

            if response['FaceMatches']:
                match = response['FaceMatches'][0]
                return {
                    'match': True,
                    'similarity': match['Similarity'],
                    'confidence': match['Face']['Confidence']
                }
            return {'match': False, 'similarity': 0, 'reason': 'no_match'}

        except ClientError as e:
            return {'match': False, 'error': str(e)}

    async def detect_faces(self, image: bytes) -> dict:
        """Detect faces and quality attributes (basic liveness)."""
        response = self.client.detect_faces(
            Image={'Bytes': image},
            Attributes=['ALL']
        )

        if not response['FaceDetails']:
            return {'valid': False, 'reason': 'no_face_detected'}

        face = response['FaceDetails'][0]
        return {
            'valid': True,
            'confidence': face['Confidence'],
            'quality': {
                'brightness': face['Quality']['Brightness'],
                'sharpness': face['Quality']['Sharpness'],
            },
            'pose': face['Pose'],
            'eyes_open': face.get('EyesOpen', {}).get('Value', True),
            'mouth_open': face.get('MouthOpen', {}).get('Value', False),
        }
```

### IPQualityScore (Device + Email + Phone + VPN)

```python
# backend/app/services/fraud_detection.py
import httpx
from typing import Optional

class FraudDetectionService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.ipqualityscore.com/api/json"

    async def check_ip(self, ip_address: str) -> dict:
        """Check IP for VPN, proxy, TOR, fraud signals."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/ip/{self.api_key}/{ip_address}",
                params={
                    'strictness': 1,
                    'allow_public_access_points': True
                }
            )
            data = response.json()

            return {
                'fraud_score': data.get('fraud_score', 0),
                'is_vpn': data.get('vpn', False),
                'is_tor': data.get('tor', False),
                'is_proxy': data.get('proxy', False),
                'is_bot': data.get('bot_status', False),
                'country': data.get('country_code'),
                'isp': data.get('ISP'),
                'risk_level': 'high' if data.get('fraud_score', 0) > 75 else
                              'medium' if data.get('fraud_score', 0) > 50 else 'low'
            }

    async def check_email(self, email: str) -> dict:
        """Check email for disposable, deliverability, fraud."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/email/{self.api_key}/{email}"
            )
            data = response.json()

            return {
                'valid': data.get('valid', False),
                'disposable': data.get('disposable', False),
                'fraud_score': data.get('fraud_score', 0),
                'deliverability': data.get('deliverability', 'unknown'),
                'leaked': data.get('leaked', False),
                'first_seen': data.get('first_seen', {}).get('human')
            }

    async def check_phone(self, phone: str, country: str = 'US') -> dict:
        """Check phone for VOIP, carrier, fraud."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/phone/{self.api_key}/{phone}",
                params={'country': country}
            )
            data = response.json()

            return {
                'valid': data.get('valid', False),
                'fraud_score': data.get('fraud_score', 0),
                'line_type': data.get('line_type'),  # landline, mobile, voip
                'carrier': data.get('carrier'),
                'prepaid': data.get('prepaid', False),
                'voip': data.get('VOIP', False),
                'risk_level': 'high' if data.get('fraud_score', 0) > 75 else
                              'medium' if data.get('fraud_score', 0) > 50 else 'low'
            }
```

### Smarty (Address Verification)

```python
# backend/app/services/address.py
import httpx

class AddressVerificationService:
    def __init__(self, auth_id: str, auth_token: str):
        self.auth_id = auth_id
        self.auth_token = auth_token
        self.base_url = "https://us-street.api.smarty.com/street-address"

    async def verify_us_address(
        self,
        street: str,
        city: str,
        state: str,
        zipcode: str = None
    ) -> dict:
        """Verify and standardize US address."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    'auth-id': self.auth_id,
                    'auth-token': self.auth_token,
                    'street': street,
                    'city': city,
                    'state': state,
                    'zipcode': zipcode or '',
                    'candidates': 1
                }
            )

            if response.status_code != 200 or not response.json():
                return {'valid': False, 'reason': 'address_not_found'}

            result = response.json()[0]

            return {
                'valid': True,
                'standardized': {
                    'street': result['delivery_line_1'],
                    'city': result['components']['city_name'],
                    'state': result['components']['state_abbreviation'],
                    'zipcode': result['components']['zipcode'],
                },
                'delivery_point': result.get('delivery_point_barcode'),
                'latitude': result.get('metadata', {}).get('latitude'),
                'longitude': result.get('metadata', {}).get('longitude'),
            }
```

---

## Cost Summary

### Minimum Viable API Stack

| Service | Purpose | Monthly Cost |
|---------|---------|--------------|
| AWS Rekognition | Face match + basic liveness | ~$20 |
| IPQualityScore | Device, email, phone, VPN | ~$30 |
| Smarty | Address verification | Free tier |
| **Total** | | **~$50/month** |

### Full Featured Stack

| Service | Purpose | Monthly Cost |
|---------|---------|--------------|
| AWS Rekognition | Face match + basic liveness | ~$50 |
| Azure Face API | Advanced liveness | ~$150 |
| IPQualityScore | Device, email, phone, VPN | ~$100 |
| Smarty | Address verification | ~$100 |
| Persona | Government DB validation | ~$250 |
| **Total** | | **~$650/month** |

Compare to building from scratch:
- 6+ months of development
- ML expertise required
- Ongoing maintenance burden
- High bug/fraud risk
- Probably worse accuracy

**ROI:** APIs pay for themselves immediately.

---

## Implementation Priority

### Week 1: Critical APIs
1. **AWS Rekognition** - Face matching + liveness
2. **IPQualityScore** - All fraud signals in one

### Week 2: Enhancement APIs
3. **Smarty** - Address verification

### Week 3+: As Needed
4. **Persona** - Government DB validation (when customers demand it)
5. **Microblink** - More document templates (when going international)

---

## Environment Variables to Add

```bash
# AWS Rekognition (likely already have from Textract)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1

# IPQualityScore
IPQS_API_KEY=...

# Smarty (address verification)
SMARTY_AUTH_ID=...
SMARTY_AUTH_TOKEN=...

# Optional - Persona (government DB)
PERSONA_API_KEY=...

# Optional - Azure Face (advanced liveness)
AZURE_FACE_ENDPOINT=...
AZURE_FACE_KEY=...
```

---

**Last Updated:** December 2, 2025
