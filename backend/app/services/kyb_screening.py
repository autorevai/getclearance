"""
Get Clearance - KYB Screening Service
=====================================
Know Your Business screening for companies and beneficial owners.

Screens:
- Company legal name and trading name against sanctions lists
- All beneficial owners against PEP and sanctions lists
- Aggregates risk from company + UBO screening
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company, BeneficialOwner
from app.models.screening import ScreeningCheck, ScreeningHit
from app.services.screening import screening_service
from app.schemas.company import CompanyScreeningResult


class KYBScreeningService:
    """
    Service for screening companies and their beneficial owners.

    Performs:
    1. Company name screening (legal + trading name)
    2. UBO screening for each beneficial owner
    3. Risk aggregation and scoring
    """

    async def screen_company(
        self,
        db: AsyncSession,
        company: Company,
        tenant_id: UUID,
        user_id: UUID,
    ) -> CompanyScreeningResult:
        """
        Screen a company and all its beneficial owners.

        Args:
            db: Database session
            company: Company to screen
            tenant_id: Tenant ID
            user_id: User running the screening

        Returns:
            CompanyScreeningResult with hit counts and details
        """
        company_hits = 0
        ubo_hits = 0
        screening_details: dict[str, Any] = {
            "company": {},
            "ubos": [],
        }

        # Screen company name
        company_result = await self._screen_company_name(
            db=db,
            company=company,
            tenant_id=tenant_id,
        )
        company_hits = company_result["hits"]
        screening_details["company"] = company_result

        # Screen each beneficial owner
        for ubo in company.beneficial_owners or []:
            ubo_result = await self._screen_ubo(
                db=db,
                ubo=ubo,
                tenant_id=tenant_id,
            )
            ubo_hits += ubo_result["hits"]
            screening_details["ubos"].append(ubo_result)

        # Calculate total hits and risk level
        total_hits = company_hits + ubo_hits
        risk_level = self._calculate_risk_level(company_hits, ubo_hits)

        # Update company screening status
        company.screening_status = "hits_pending" if total_hits > 0 else "clear"
        company.last_screened_at = datetime.utcnow()

        # Update risk level if hits found
        if total_hits > 0:
            company.risk_level = risk_level
            # Add flags based on hit types
            flags = set(company.flags or [])
            if company_result.get("has_sanctions"):
                flags.add("sanctions")
            if any(u.get("has_pep") for u in screening_details["ubos"]):
                flags.add("pep_ubo")
            company.flags = list(flags)

        return CompanyScreeningResult(
            company_id=company.id,
            company_name=company.legal_name,
            company_hits=company_hits,
            ubo_hits=ubo_hits,
            total_hits=total_hits,
            risk_level=risk_level,
            screening_status=company.screening_status,
            screened_at=datetime.utcnow(),
            details=screening_details,
        )

    async def _screen_company_name(
        self,
        db: AsyncSession,
        company: Company,
        tenant_id: UUID,
    ) -> dict[str, Any]:
        """
        Screen company legal name and trading name.

        Returns:
            Dict with screening results
        """
        result = {
            "company_id": str(company.id),
            "legal_name": company.legal_name,
            "trading_name": company.trading_name,
            "hits": 0,
            "has_sanctions": False,
            "has_adverse_media": False,
            "checks": [],
        }

        # Screen legal name
        if company.legal_name:
            legal_check = await self._run_name_screening(
                db=db,
                tenant_id=tenant_id,
                name=company.legal_name,
                entity_type="company",
                entity_id=company.id,
                check_type="company_legal_name",
            )
            result["checks"].append(legal_check)
            result["hits"] += legal_check["hit_count"]
            result["has_sanctions"] = result["has_sanctions"] or legal_check.get("has_sanctions", False)

        # Screen trading name if different
        if company.trading_name and company.trading_name != company.legal_name:
            trading_check = await self._run_name_screening(
                db=db,
                tenant_id=tenant_id,
                name=company.trading_name,
                entity_type="company",
                entity_id=company.id,
                check_type="company_trading_name",
            )
            result["checks"].append(trading_check)
            result["hits"] += trading_check["hit_count"]
            result["has_sanctions"] = result["has_sanctions"] or trading_check.get("has_sanctions", False)

        return result

    async def _screen_ubo(
        self,
        db: AsyncSession,
        ubo: BeneficialOwner,
        tenant_id: UUID,
    ) -> dict[str, Any]:
        """
        Screen a beneficial owner.

        Returns:
            Dict with screening results
        """
        result = {
            "ubo_id": str(ubo.id),
            "full_name": ubo.full_name,
            "hits": 0,
            "has_sanctions": False,
            "has_pep": False,
            "has_adverse_media": False,
            "check": None,
        }

        # Skip if already linked to verified KYC applicant
        if ubo.applicant_id and ubo.verification_status == "linked":
            result["status"] = "skipped_linked_kyc"
            return result

        # Screen UBO name
        check = await self._run_name_screening(
            db=db,
            tenant_id=tenant_id,
            name=ubo.full_name,
            entity_type="beneficial_owner",
            entity_id=ubo.id,
            check_type="ubo_name",
            date_of_birth=ubo.date_of_birth,
            nationality=ubo.nationality,
        )

        result["check"] = check
        result["hits"] = check["hit_count"]
        result["has_sanctions"] = check.get("has_sanctions", False)
        result["has_pep"] = check.get("has_pep", False)
        result["has_adverse_media"] = check.get("has_adverse_media", False)

        # Update UBO screening status
        ubo.screening_status = "hits" if result["hits"] > 0 else "clear"
        ubo.last_screened_at = datetime.utcnow()

        if result["hits"] > 0:
            flags = set(ubo.flags or [])
            if result["has_sanctions"]:
                flags.add("sanctions")
            if result["has_pep"]:
                flags.add("pep")
            if result["has_adverse_media"]:
                flags.add("adverse_media")
            ubo.flags = list(flags)

        return result

    async def _run_name_screening(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        name: str,
        entity_type: str,
        entity_id: UUID,
        check_type: str,
        date_of_birth=None,
        nationality: str | None = None,
    ) -> dict[str, Any]:
        """
        Run screening check for a name.

        Returns:
            Dict with check results
        """
        result = {
            "check_type": check_type,
            "name": name,
            "hit_count": 0,
            "has_sanctions": False,
            "has_pep": False,
            "has_adverse_media": False,
            "check_id": None,
        }

        try:
            # Use existing screening service
            screening_result = await screening_service.screen_entity(
                name=name,
                date_of_birth=date_of_birth.isoformat() if date_of_birth else None,
                nationality=nationality,
                entity_type="company" if "company" in check_type else "person",
            )

            # Create screening check record
            check = ScreeningCheck(
                tenant_id=tenant_id,
                company_id=entity_id if entity_type == "company" else None,
                check_type=check_type,
                status="completed",
                screened_name=name,
                screened_dob=date_of_birth,
                screened_nationality=nationality,
                result_count=len(screening_result.get("results", [])),
                completed_at=datetime.utcnow(),
            )
            db.add(check)
            await db.flush()

            result["check_id"] = str(check.id)

            # Process hits
            for hit_data in screening_result.get("results", []):
                # Determine hit type
                hit_type = "unknown"
                if hit_data.get("is_sanctioned"):
                    hit_type = "sanctions"
                    result["has_sanctions"] = True
                elif hit_data.get("is_pep"):
                    hit_type = "pep"
                    result["has_pep"] = True
                elif hit_data.get("topics"):
                    if "sanction" in str(hit_data["topics"]).lower():
                        hit_type = "sanctions"
                        result["has_sanctions"] = True
                    elif "pep" in str(hit_data["topics"]).lower():
                        hit_type = "pep"
                        result["has_pep"] = True
                    else:
                        hit_type = "adverse_media"
                        result["has_adverse_media"] = True

                # Create hit record
                hit = ScreeningHit(
                    check_id=check.id,
                    hit_type=hit_type,
                    list_source=hit_data.get("dataset", "opensanctions"),
                    matched_name=hit_data.get("name", "Unknown"),
                    match_score=hit_data.get("score", 0.0),
                    hit_data=hit_data,
                    resolution_status="pending",
                )
                db.add(hit)
                result["hit_count"] += 1

        except Exception as e:
            # Log error but don't fail entire screening
            result["error"] = str(e)

        return result

    def _calculate_risk_level(self, company_hits: int, ubo_hits: int) -> str:
        """
        Calculate overall risk level based on hits.

        Returns:
            Risk level: low, medium, or high
        """
        total_hits = company_hits + ubo_hits

        if company_hits > 0:
            # Company sanctions hit is always high risk
            return "high"
        elif ubo_hits >= 3:
            return "high"
        elif ubo_hits >= 1:
            return "medium"
        else:
            return "low"


# Singleton instance
kyb_screening_service = KYBScreeningService()
