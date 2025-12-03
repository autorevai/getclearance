"""
Get Clearance - Questionnaire Models
=====================================
Custom questionnaires for collecting additional KYC information.

Questionnaires allow tenants to:
- Define custom questions with various input types
- Assign risk scores to specific answers
- Associate questionnaires with applicants or companies
- Contribute to overall risk assessment

Question Types:
- text: Free text input
- textarea: Multi-line text
- select: Single selection from options
- multi_select: Multiple selections
- date: Date picker
- number: Numeric input
- file: File upload
- boolean: Yes/No toggle
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    String, Integer, DateTime, Text, Boolean,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.tenant import Tenant, User
    from app.models.applicant import Applicant
    from app.models.company import Company


class Questionnaire(Base, UUIDMixin, TimestampMixin):
    """
    Questionnaire template with configurable questions.

    Questions are stored as JSONB array with the following structure:
    [
        {
            "id": "q1",
            "type": "select",
            "label": "Source of funds",
            "description": "Please indicate your primary source of funds",
            "required": true,
            "options": ["Employment", "Business", "Investment", "Inheritance", "Other"],
            "risk_scores": {
                "Employment": 0,
                "Business": 10,
                "Investment": 15,
                "Inheritance": 5,
                "Other": 25
            },
            "order": 1,
            "conditional": null  // or {"question_id": "q0", "value": "Yes"}
        }
    ]
    """
    __tablename__ = "questionnaires"
    __table_args__ = (
        Index("idx_questionnaires_tenant_active", "tenant_id", "is_active"),
        Index("idx_questionnaires_type", "tenant_id", "questionnaire_type"),
    )

    # Tenant
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Questionnaire identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    internal_notes: Mapped[str | None] = mapped_column(Text)

    # Type/purpose
    questionnaire_type: Mapped[str] = mapped_column(String(50), default="general")
    # Types: 'general', 'source_of_funds', 'source_of_wealth', 'pep_declaration',
    #        'tax_residency', 'business_nature', 'enhanced_due_diligence'

    # Questions configuration (JSONB array)
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Scoring
    max_risk_score: Mapped[int | None] = mapped_column(Integer)
    # Max possible risk score from this questionnaire

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    # If required, must be completed before applicant can be approved

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Metadata
    created_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Statistics
    times_completed: Mapped[int] = mapped_column(Integer, default=0)
    average_risk_score: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    responses: Mapped[list["QuestionnaireResponse"]] = relationship(
        "QuestionnaireResponse", back_populates="questionnaire"
    )
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])

    def __repr__(self) -> str:
        return f"<Questionnaire {self.id} {self.name}>"

    @property
    def question_count(self) -> int:
        """Number of questions in questionnaire."""
        return len(self.questions) if self.questions else 0

    @property
    def required_questions(self) -> list[dict]:
        """Get list of required questions."""
        if not self.questions:
            return []
        return [q for q in self.questions if q.get("required", False)]


class QuestionnaireResponse(Base, UUIDMixin, TimestampMixin):
    """
    Submitted answers to a questionnaire.

    Links to either an applicant (KYC) or company (KYB).
    """
    __tablename__ = "questionnaire_responses"
    __table_args__ = (
        Index("idx_questionnaire_responses_questionnaire", "questionnaire_id"),
        Index("idx_questionnaire_responses_applicant", "applicant_id"),
        Index("idx_questionnaire_responses_company", "company_id"),
    )

    # Parent questionnaire
    questionnaire_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Link to applicant or company (one must be set)
    applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("applicants.id", ondelete="CASCADE"),
    )
    company_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
    )

    # Submitted answers (JSONB)
    # Format: {"q1": "Employment", "q2": ["Option A", "Option B"], "q3": "2024-01-15"}
    answers: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Calculated risk score from answers
    risk_score: Mapped[int | None] = mapped_column(Integer)
    risk_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Format: {"q1": {"answer": "Business", "score": 10}, "q2": {...}}

    # Status
    status: Mapped[str] = mapped_column(String(50), default="submitted")
    # Status: 'draft', 'submitted', 'reviewed', 'flagged'

    # Submission details
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Review
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    review_notes: Mapped[str | None] = mapped_column(Text)

    # IP/device tracking for fraud prevention
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    # Relationships
    questionnaire: Mapped["Questionnaire"] = relationship(
        "Questionnaire", back_populates="responses"
    )
    applicant: Mapped["Applicant | None"] = relationship("Applicant")
    company: Mapped["Company | None"] = relationship("Company")
    submitter: Mapped["User | None"] = relationship("User", foreign_keys=[submitted_by])
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<QuestionnaireResponse {self.id} score={self.risk_score}>"

    @property
    def is_complete(self) -> bool:
        """Check if all required questions have been answered."""
        if not self.questionnaire or not self.answers:
            return False

        required_ids = [
            q["id"] for q in (self.questionnaire.questions or [])
            if q.get("required", False)
        ]

        for q_id in required_ids:
            if q_id not in self.answers or self.answers[q_id] in (None, "", []):
                return False

        return True


# Default questionnaire templates
DEFAULT_QUESTIONNAIRES = [
    {
        "name": "Source of Funds",
        "description": "Declaration of the source of funds for this transaction",
        "questionnaire_type": "source_of_funds",
        "is_required": True,
        "questions": [
            {
                "id": "sof_primary",
                "type": "select",
                "label": "Primary source of funds",
                "description": "What is the primary source of the funds you are using?",
                "required": True,
                "options": [
                    "Employment/Salary",
                    "Business Income",
                    "Investment Returns",
                    "Property Sale",
                    "Inheritance/Gift",
                    "Pension/Retirement",
                    "Savings",
                    "Loan",
                    "Other"
                ],
                "risk_scores": {
                    "Employment/Salary": 0,
                    "Business Income": 10,
                    "Investment Returns": 5,
                    "Property Sale": 5,
                    "Inheritance/Gift": 15,
                    "Pension/Retirement": 0,
                    "Savings": 0,
                    "Loan": 10,
                    "Other": 25
                },
                "order": 1
            },
            {
                "id": "sof_amount",
                "type": "select",
                "label": "Expected transaction volume",
                "description": "What is your expected monthly transaction volume?",
                "required": True,
                "options": [
                    "Less than $10,000",
                    "$10,000 - $50,000",
                    "$50,000 - $100,000",
                    "$100,000 - $500,000",
                    "More than $500,000"
                ],
                "risk_scores": {
                    "Less than $10,000": 0,
                    "$10,000 - $50,000": 5,
                    "$50,000 - $100,000": 10,
                    "$100,000 - $500,000": 20,
                    "More than $500,000": 30
                },
                "order": 2
            },
            {
                "id": "sof_other_detail",
                "type": "textarea",
                "label": "Additional details",
                "description": "If you selected 'Other' above, please provide details",
                "required": False,
                "conditional": {"question_id": "sof_primary", "value": "Other"},
                "order": 3
            }
        ]
    },
    {
        "name": "PEP Declaration",
        "description": "Politically Exposed Person declaration form",
        "questionnaire_type": "pep_declaration",
        "is_required": True,
        "questions": [
            {
                "id": "pep_self",
                "type": "boolean",
                "label": "Are you a Politically Exposed Person (PEP)?",
                "description": "A PEP is someone who holds or has held a prominent public function",
                "required": True,
                "risk_scores": {"true": 40, "false": 0},
                "order": 1
            },
            {
                "id": "pep_family",
                "type": "boolean",
                "label": "Are you a close family member of a PEP?",
                "description": "Including spouse, children, parents, and siblings",
                "required": True,
                "risk_scores": {"true": 25, "false": 0},
                "order": 2
            },
            {
                "id": "pep_associate",
                "type": "boolean",
                "label": "Are you a close associate of a PEP?",
                "description": "Close business or personal relationship with a PEP",
                "required": True,
                "risk_scores": {"true": 20, "false": 0},
                "order": 3
            },
            {
                "id": "pep_position",
                "type": "text",
                "label": "If PEP, please state the position held",
                "required": False,
                "conditional": {"question_id": "pep_self", "value": True},
                "order": 4
            },
            {
                "id": "pep_country",
                "type": "text",
                "label": "Country of political exposure",
                "required": False,
                "conditional": {"question_id": "pep_self", "value": True},
                "order": 5
            }
        ]
    },
    {
        "name": "Tax Residency",
        "description": "Tax residency and FATCA/CRS declaration",
        "questionnaire_type": "tax_residency",
        "is_required": False,
        "questions": [
            {
                "id": "tax_us_person",
                "type": "boolean",
                "label": "Are you a US person for tax purposes?",
                "description": "US citizen, resident, or green card holder",
                "required": True,
                "risk_scores": {"true": 5, "false": 0},
                "order": 1
            },
            {
                "id": "tax_countries",
                "type": "multi_select",
                "label": "Countries of tax residency",
                "description": "Select all countries where you are tax resident",
                "required": True,
                "options": [
                    "United States",
                    "United Kingdom",
                    "Canada",
                    "Australia",
                    "Germany",
                    "France",
                    "Other"
                ],
                "order": 2
            },
            {
                "id": "tax_tin",
                "type": "text",
                "label": "Tax Identification Number (TIN)",
                "description": "Your primary tax identification number",
                "required": True,
                "order": 3
            }
        ]
    },
    # ============================================
    # CRYPTO/DIGITAL ASSETS QUESTIONNAIRES
    # ============================================
    {
        "name": "Crypto Source of Funds",
        "description": "Declaration of crypto asset sources and transaction history (FATF Travel Rule compliant)",
        "questionnaire_type": "crypto_source_of_funds",
        "is_required": True,
        "questions": [
            {
                "id": "crypto_source",
                "type": "multi_select",
                "label": "Source of cryptocurrency holdings",
                "description": "Select all that apply",
                "required": True,
                "options": [
                    "Mining",
                    "Staking rewards",
                    "Exchange purchase (fiat to crypto)",
                    "DeFi yield farming",
                    "NFT sales",
                    "Payment for goods/services",
                    "Airdrop",
                    "ICO/IDO participation",
                    "Peer-to-peer transfer",
                    "Inheritance/Gift",
                    "Other"
                ],
                "risk_scores": {
                    "Mining": 5,
                    "Staking rewards": 5,
                    "Exchange purchase (fiat to crypto)": 0,
                    "DeFi yield farming": 15,
                    "NFT sales": 15,
                    "Payment for goods/services": 10,
                    "Airdrop": 20,
                    "ICO/IDO participation": 25,
                    "Peer-to-peer transfer": 30,
                    "Inheritance/Gift": 20,
                    "Other": 35
                },
                "order": 1
            },
            {
                "id": "crypto_experience",
                "type": "select",
                "label": "Experience with cryptocurrency",
                "description": "How long have you been trading/holding cryptocurrency?",
                "required": True,
                "options": [
                    "Less than 1 year",
                    "1-3 years",
                    "3-5 years",
                    "More than 5 years"
                ],
                "risk_scores": {
                    "Less than 1 year": 10,
                    "1-3 years": 5,
                    "3-5 years": 0,
                    "More than 5 years": 0
                },
                "order": 2
            },
            {
                "id": "crypto_volume",
                "type": "select",
                "label": "Expected monthly transaction volume",
                "description": "Approximate value in USD equivalent",
                "required": True,
                "options": [
                    "Less than $10,000",
                    "$10,000 - $50,000",
                    "$50,000 - $250,000",
                    "$250,000 - $1,000,000",
                    "More than $1,000,000"
                ],
                "risk_scores": {
                    "Less than $10,000": 0,
                    "$10,000 - $50,000": 5,
                    "$50,000 - $250,000": 15,
                    "$250,000 - $1,000,000": 25,
                    "More than $1,000,000": 40
                },
                "order": 3
            },
            {
                "id": "crypto_custodial",
                "type": "select",
                "label": "Primary wallet type",
                "description": "How do you primarily store your cryptocurrency?",
                "required": True,
                "options": [
                    "Custodial exchange wallet",
                    "Software/hot wallet",
                    "Hardware/cold wallet",
                    "Multi-signature wallet",
                    "Smart contract wallet"
                ],
                "risk_scores": {
                    "Custodial exchange wallet": 0,
                    "Software/hot wallet": 10,
                    "Hardware/cold wallet": 5,
                    "Multi-signature wallet": 5,
                    "Smart contract wallet": 15
                },
                "order": 4
            },
            {
                "id": "crypto_mixer",
                "type": "boolean",
                "label": "Have you used cryptocurrency mixing/tumbling services?",
                "description": "Services that obscure transaction history",
                "required": True,
                "risk_scores": {"true": 50, "false": 0},
                "order": 5
            },
            {
                "id": "crypto_privacy_coins",
                "type": "boolean",
                "label": "Do you transact in privacy coins?",
                "description": "Monero, Zcash (shielded), Dash (PrivateSend), etc.",
                "required": True,
                "risk_scores": {"true": 35, "false": 0},
                "order": 6
            },
            {
                "id": "crypto_unhosted",
                "type": "boolean",
                "label": "Will you transact with unhosted/self-custody wallets?",
                "description": "Non-custodial wallets not controlled by a financial institution",
                "required": True,
                "risk_scores": {"true": 15, "false": 0},
                "order": 7
            },
            {
                "id": "crypto_exchanges",
                "type": "textarea",
                "label": "List exchanges you regularly use",
                "description": "Include names of centralized exchanges where you hold accounts",
                "required": True,
                "order": 8
            }
        ]
    },
    {
        "name": "Crypto Transaction Purpose",
        "description": "Purpose and destination of cryptocurrency transactions",
        "questionnaire_type": "crypto_transaction_purpose",
        "is_required": False,
        "questions": [
            {
                "id": "crypto_purpose",
                "type": "multi_select",
                "label": "Primary purpose of cryptocurrency transactions",
                "description": "Select all that apply",
                "required": True,
                "options": [
                    "Investment/long-term holding",
                    "Trading/speculation",
                    "Payment for goods/services",
                    "Remittance/cross-border transfers",
                    "DeFi participation",
                    "NFT collection/trading",
                    "Business operations",
                    "Other"
                ],
                "risk_scores": {
                    "Investment/long-term holding": 0,
                    "Trading/speculation": 5,
                    "Payment for goods/services": 10,
                    "Remittance/cross-border transfers": 20,
                    "DeFi participation": 15,
                    "NFT collection/trading": 15,
                    "Business operations": 10,
                    "Other": 25
                },
                "order": 1
            },
            {
                "id": "crypto_destination_countries",
                "type": "multi_select",
                "label": "Countries where you send/receive crypto",
                "description": "Select primary jurisdictions",
                "required": True,
                "options": [
                    "United States",
                    "United Kingdom",
                    "European Union",
                    "Switzerland",
                    "Singapore",
                    "Japan",
                    "Hong Kong",
                    "UAE/Dubai",
                    "Other (high-risk jurisdiction)",
                    "Other (standard jurisdiction)"
                ],
                "risk_scores": {
                    "United States": 0,
                    "United Kingdom": 0,
                    "European Union": 0,
                    "Switzerland": 0,
                    "Singapore": 0,
                    "Japan": 0,
                    "Hong Kong": 5,
                    "UAE/Dubai": 10,
                    "Other (high-risk jurisdiction)": 40,
                    "Other (standard jurisdiction)": 5
                },
                "order": 2
            }
        ]
    },
    # ============================================
    # FINTECH/NEOBANK QUESTIONNAIRES
    # ============================================
    {
        "name": "Fintech Account Purpose",
        "description": "Account opening questionnaire for fintech/neobank services",
        "questionnaire_type": "fintech_account_purpose",
        "is_required": True,
        "questions": [
            {
                "id": "account_purpose",
                "type": "multi_select",
                "label": "How will you use this account?",
                "description": "Select all that apply",
                "required": True,
                "options": [
                    "Day-to-day spending",
                    "Salary/income deposits",
                    "Bill payments",
                    "Online shopping",
                    "Savings",
                    "Investment",
                    "Business transactions",
                    "International transfers",
                    "Freelance/gig economy income"
                ],
                "risk_scores": {
                    "Day-to-day spending": 0,
                    "Salary/income deposits": 0,
                    "Bill payments": 0,
                    "Online shopping": 0,
                    "Savings": 0,
                    "Investment": 5,
                    "Business transactions": 15,
                    "International transfers": 20,
                    "Freelance/gig economy income": 10
                },
                "order": 1
            },
            {
                "id": "income_source",
                "type": "select",
                "label": "Primary source of income",
                "description": "Main source of funds deposited to this account",
                "required": True,
                "options": [
                    "Employed - salary/wages",
                    "Self-employed",
                    "Business owner",
                    "Freelancer/contractor",
                    "Pension/retirement",
                    "Investment income",
                    "Government benefits",
                    "Student (loans/grants/support)",
                    "Unemployed",
                    "Other"
                ],
                "risk_scores": {
                    "Employed - salary/wages": 0,
                    "Self-employed": 10,
                    "Business owner": 15,
                    "Freelancer/contractor": 10,
                    "Pension/retirement": 0,
                    "Investment income": 5,
                    "Government benefits": 0,
                    "Student (loans/grants/support)": 0,
                    "Unemployed": 15,
                    "Other": 20
                },
                "order": 2
            },
            {
                "id": "monthly_income",
                "type": "select",
                "label": "Expected monthly deposits",
                "description": "Approximate monthly income/deposits to this account",
                "required": True,
                "options": [
                    "Less than $1,000",
                    "$1,000 - $5,000",
                    "$5,000 - $15,000",
                    "$15,000 - $50,000",
                    "More than $50,000"
                ],
                "risk_scores": {
                    "Less than $1,000": 0,
                    "$1,000 - $5,000": 0,
                    "$5,000 - $15,000": 5,
                    "$15,000 - $50,000": 15,
                    "More than $50,000": 25
                },
                "order": 3
            },
            {
                "id": "international_activity",
                "type": "select",
                "label": "International transaction frequency",
                "description": "How often will you send/receive international transfers?",
                "required": True,
                "options": [
                    "Never or rarely",
                    "A few times per year",
                    "Monthly",
                    "Weekly",
                    "Daily"
                ],
                "risk_scores": {
                    "Never or rarely": 0,
                    "A few times per year": 5,
                    "Monthly": 10,
                    "Weekly": 20,
                    "Daily": 30
                },
                "order": 4
            },
            {
                "id": "cash_activity",
                "type": "select",
                "label": "Cash deposit/withdrawal frequency",
                "description": "How often will you use ATMs or cash deposits?",
                "required": True,
                "options": [
                    "Never or rarely",
                    "A few times per month",
                    "Weekly",
                    "Multiple times per week"
                ],
                "risk_scores": {
                    "Never or rarely": 0,
                    "A few times per month": 5,
                    "Weekly": 15,
                    "Multiple times per week": 25
                },
                "order": 5
            }
        ]
    },
    {
        "name": "Business Account - Fintech",
        "description": "Enhanced due diligence for fintech business accounts",
        "questionnaire_type": "fintech_business",
        "is_required": True,
        "questions": [
            {
                "id": "business_type",
                "type": "select",
                "label": "Type of business",
                "description": "Select the category that best describes your business",
                "required": True,
                "options": [
                    "Retail/E-commerce",
                    "Professional services",
                    "Technology/SaaS",
                    "Food & hospitality",
                    "Healthcare",
                    "Construction/trades",
                    "Financial services",
                    "Cryptocurrency/blockchain",
                    "Gaming/gambling",
                    "Adult entertainment",
                    "Cannabis/CBD",
                    "Other"
                ],
                "risk_scores": {
                    "Retail/E-commerce": 5,
                    "Professional services": 0,
                    "Technology/SaaS": 5,
                    "Food & hospitality": 5,
                    "Healthcare": 10,
                    "Construction/trades": 10,
                    "Financial services": 20,
                    "Cryptocurrency/blockchain": 35,
                    "Gaming/gambling": 40,
                    "Adult entertainment": 35,
                    "Cannabis/CBD": 40,
                    "Other": 15
                },
                "order": 1
            },
            {
                "id": "business_age",
                "type": "select",
                "label": "How long has the business been operating?",
                "required": True,
                "options": [
                    "Not yet launched",
                    "Less than 1 year",
                    "1-3 years",
                    "3-5 years",
                    "More than 5 years"
                ],
                "risk_scores": {
                    "Not yet launched": 25,
                    "Less than 1 year": 15,
                    "1-3 years": 10,
                    "3-5 years": 5,
                    "More than 5 years": 0
                },
                "order": 2
            },
            {
                "id": "monthly_volume",
                "type": "select",
                "label": "Expected monthly transaction volume",
                "required": True,
                "options": [
                    "Less than $10,000",
                    "$10,000 - $50,000",
                    "$50,000 - $250,000",
                    "$250,000 - $1,000,000",
                    "More than $1,000,000"
                ],
                "risk_scores": {
                    "Less than $10,000": 0,
                    "$10,000 - $50,000": 5,
                    "$50,000 - $250,000": 10,
                    "$250,000 - $1,000,000": 20,
                    "More than $1,000,000": 30
                },
                "order": 3
            },
            {
                "id": "customer_geography",
                "type": "multi_select",
                "label": "Where are your customers located?",
                "description": "Select all regions where you do business",
                "required": True,
                "options": [
                    "Domestic only",
                    "North America",
                    "Europe",
                    "Asia-Pacific",
                    "Middle East",
                    "Africa",
                    "Latin America",
                    "Worldwide"
                ],
                "risk_scores": {
                    "Domestic only": 0,
                    "North America": 0,
                    "Europe": 0,
                    "Asia-Pacific": 5,
                    "Middle East": 15,
                    "Africa": 15,
                    "Latin America": 10,
                    "Worldwide": 10
                },
                "order": 4
            },
            {
                "id": "payment_types",
                "type": "multi_select",
                "label": "Payment methods you accept/use",
                "required": True,
                "options": [
                    "Bank transfers",
                    "Credit/debit cards",
                    "Mobile payments (Apple Pay, etc.)",
                    "Cash",
                    "Cryptocurrency",
                    "Wire transfers",
                    "Checks",
                    "Third-party processors (PayPal, Stripe)"
                ],
                "risk_scores": {
                    "Bank transfers": 0,
                    "Credit/debit cards": 0,
                    "Mobile payments (Apple Pay, etc.)": 0,
                    "Cash": 20,
                    "Cryptocurrency": 25,
                    "Wire transfers": 10,
                    "Checks": 5,
                    "Third-party processors (PayPal, Stripe)": 0
                },
                "order": 5
            },
            {
                "id": "regulated_activity",
                "type": "boolean",
                "label": "Is your business subject to financial regulation?",
                "description": "Licensed money transmitter, broker-dealer, etc.",
                "required": True,
                "risk_scores": {"true": 15, "false": 0},
                "order": 6
            },
            {
                "id": "third_party_payments",
                "type": "boolean",
                "label": "Will you process payments on behalf of third parties?",
                "description": "Acting as a payment facilitator or marketplace",
                "required": True,
                "risk_scores": {"true": 25, "false": 0},
                "order": 7
            }
        ]
    },
    # ============================================
    # ENHANCED DUE DILIGENCE (EDD)
    # ============================================
    {
        "name": "Enhanced Due Diligence",
        "description": "Additional questions for high-risk customers requiring enhanced scrutiny",
        "questionnaire_type": "enhanced_due_diligence",
        "is_required": False,
        "questions": [
            {
                "id": "edd_wealth_source",
                "type": "textarea",
                "label": "Detailed source of wealth",
                "description": "Please provide a detailed explanation of how you accumulated your wealth",
                "required": True,
                "order": 1
            },
            {
                "id": "edd_business_relationships",
                "type": "textarea",
                "label": "Key business relationships",
                "description": "Describe your primary business relationships and counterparties",
                "required": True,
                "order": 2
            },
            {
                "id": "edd_transaction_rationale",
                "type": "textarea",
                "label": "Transaction rationale",
                "description": "Explain the purpose and expected pattern of your transactions",
                "required": True,
                "order": 3
            },
            {
                "id": "edd_third_party_acting",
                "type": "boolean",
                "label": "Are you acting on behalf of a third party?",
                "description": "Managing funds or acting as agent for another person",
                "required": True,
                "risk_scores": {"true": 40, "false": 0},
                "order": 4
            },
            {
                "id": "edd_third_party_details",
                "type": "textarea",
                "label": "Third party details",
                "description": "If acting on behalf of others, provide their details",
                "required": False,
                "conditional": {"question_id": "edd_third_party_acting", "value": True},
                "order": 5
            },
            {
                "id": "edd_complex_structures",
                "type": "boolean",
                "label": "Do you use complex corporate structures?",
                "description": "Multiple holding companies, trusts, offshore entities",
                "required": True,
                "risk_scores": {"true": 30, "false": 0},
                "order": 6
            },
            {
                "id": "edd_structure_details",
                "type": "textarea",
                "label": "Corporate structure details",
                "description": "Please describe your corporate/ownership structure",
                "required": False,
                "conditional": {"question_id": "edd_complex_structures", "value": True},
                "order": 7
            },
            {
                "id": "edd_adverse_media",
                "type": "boolean",
                "label": "Have you been subject to negative media coverage?",
                "description": "News articles regarding legal, financial, or regulatory issues",
                "required": True,
                "risk_scores": {"true": 35, "false": 0},
                "order": 8
            },
            {
                "id": "edd_media_details",
                "type": "textarea",
                "label": "Media coverage details",
                "description": "Please explain any negative media coverage",
                "required": False,
                "conditional": {"question_id": "edd_adverse_media", "value": True},
                "order": 9
            }
        ]
    }
]
