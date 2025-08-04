"""
Advanced lead scoring service with sophisticated algorithms
"""
import math
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.lead import Lead
from app.models.company import Company
from app.models.lead_enrichment import LeadEnrichment


class AdvancedScoringService:
    """Advanced lead scoring with machine learning-inspired algorithms"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Advanced scoring weights and criteria
        self.default_weights = {
            "industry_match": 25,
            "location_preference": 15,
            "funding_stage": 20,
            "company_size": 10,
            "data_completeness": 8,
            "engagement_signals": 12,
            "timing_indicators": 10
        }
        
        # Industry scoring matrix
        self.industry_scores = {
            "Technology": {"Technology": 100, "SaaS": 90, "Fintech": 80, "E-commerce": 70},
            "Fintech": {"Fintech": 100, "Technology": 85, "SaaS": 75, "Healthcare": 60},
            "Healthcare": {"Healthcare": 100, "Technology": 80, "SaaS": 70, "Fintech": 65},
            "SaaS": {"SaaS": 100, "Technology": 95, "E-commerce": 80, "Fintech": 75},
            "E-commerce": {"E-commerce": 100, "SaaS": 85, "Technology": 80, "Fintech": 70}
        }
        
        # Funding stage scores (higher = better fit)
        self.funding_stage_scores = {
            "pre-seed": 30,
            "seed": 60,
            "series-a": 90,
            "series-b": 100,
            "series-c": 85,
            "series-d+": 70
        }
        
        # Company size preferences
        self.company_size_scores = {
            "1-10": 40,
            "11-50": 80,
            "51-200": 100,
            "201-1000": 95,
            "1000+": 75
        }

    def calculate_advanced_score(
        self, 
        lead: Lead, 
        company: Company, 
        enrichment_data: Optional[Dict[str, Any]] = None,
        scoring_criteria: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate advanced lead score with detailed breakdown
        Returns: (score, breakdown_details)
        """
        
        # Merge default criteria with provided criteria
        criteria = {**self.default_weights}
        if scoring_criteria:
            criteria.update(scoring_criteria)
        
        score_breakdown = {}
        total_score = 0.0
        total_weight = sum(criteria.values())
        
        # 1. Industry Match Score
        industry_score = self._calculate_industry_score(company, criteria)
        score_breakdown["industry_match"] = {
            "score": industry_score,
            "weight": criteria["industry_match"],
            "weighted_score": industry_score * criteria["industry_match"] / 100
        }
        total_score += score_breakdown["industry_match"]["weighted_score"]
        
        # 2. Location Preference Score
        location_score = self._calculate_location_score(company, criteria)
        score_breakdown["location_preference"] = {
            "score": location_score,
            "weight": criteria["location_preference"],
            "weighted_score": location_score * criteria["location_preference"] / 100
        }
        total_score += score_breakdown["location_preference"]["weighted_score"]
        
        # 3. Funding Stage Score
        funding_score = self._calculate_funding_score(company, criteria)
        score_breakdown["funding_stage"] = {
            "score": funding_score,
            "weight": criteria["funding_stage"],
            "weighted_score": funding_score * criteria["funding_stage"] / 100
        }
        total_score += score_breakdown["funding_stage"]["weighted_score"]
        
        # 4. Company Size Score
        size_score = self._calculate_company_size_score(company, enrichment_data, criteria)
        score_breakdown["company_size"] = {
            "score": size_score,
            "weight": criteria["company_size"],
            "weighted_score": size_score * criteria["company_size"] / 100
        }
        total_score += score_breakdown["company_size"]["weighted_score"]
        
        # 5. Data Completeness Score
        completeness_score = self._calculate_data_completeness_score(lead, company, enrichment_data)
        score_breakdown["data_completeness"] = {
            "score": completeness_score,
            "weight": criteria["data_completeness"],
            "weighted_score": completeness_score * criteria["data_completeness"] / 100
        }
        total_score += score_breakdown["data_completeness"]["weighted_score"]
        
        # 6. Engagement Signals Score
        engagement_score = self._calculate_engagement_score(enrichment_data, criteria)
        score_breakdown["engagement_signals"] = {
            "score": engagement_score,
            "weight": criteria["engagement_signals"],
            "weighted_score": engagement_score * criteria["engagement_signals"] / 100
        }
        total_score += score_breakdown["engagement_signals"]["weighted_score"]
        
        # 7. Timing Indicators Score
        timing_score = self._calculate_timing_score(enrichment_data, criteria)
        score_breakdown["timing_indicators"] = {
            "score": timing_score,
            "weight": criteria["timing_indicators"],
            "weighted_score": timing_score * criteria["timing_indicators"] / 100
        }
        total_score += score_breakdown["timing_indicators"]["weighted_score"]
        
        # Normalize to 0-100 scale
        final_score = (total_score / total_weight) * 100
        
        # Apply bonus/penalty modifiers
        final_score = self._apply_score_modifiers(final_score, lead, company, enrichment_data)
        
        # Ensure score is within bounds
        final_score = max(0.0, min(100.0, final_score))
        
        return final_score, score_breakdown

    def _calculate_industry_score(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Calculate industry match score"""
        if not company.industry:
            return 40.0  # Neutral score for missing industry
        
        target_industries = criteria.get("target_industries", [])
        if not target_industries:
            # Default high-value industries
            target_industries = ["Technology", "SaaS", "Fintech", "Healthcare"]
        
        # Direct match
        if company.industry in target_industries:
            return 100.0
        
        # Related industry match using scoring matrix
        company_industry = company.industry
        if company_industry in self.industry_scores:
            for target in target_industries:
                if target in self.industry_scores[company_industry]:
                    return self.industry_scores[company_industry][target]
        
        # Partial text match
        for target in target_industries:
            if target.lower() in company.industry.lower() or company.industry.lower() in target.lower():
                return 70.0
        
        return 30.0  # No match

    def _calculate_location_score(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Calculate location preference score"""
        if not company.location:
            return 50.0  # Neutral score for missing location
        
        target_locations = criteria.get("target_locations", [])
        if not target_locations:
            # Default preferred locations (major tech hubs)
            target_locations = ["California", "San Francisco", "New York", "Austin", "Seattle", "Boston"]
        
        location = company.location.lower()
        
        # Direct match
        for target in target_locations:
            if target.lower() in location:
                return 100.0
        
        # State-level matches
        state_scores = {
            "ca": 90, "california": 90,
            "ny": 85, "new york": 85,
            "tx": 80, "texas": 80,
            "wa": 75, "washington": 75,
            "ma": 75, "massachusetts": 75,
            "co": 70, "colorado": 70
        }
        
        for state, score in state_scores.items():
            if state in location:
                return score
        
        return 40.0  # Other locations

    def _calculate_funding_score(self, company: Company, criteria: Dict[str, Any]) -> float:
        """Calculate funding stage/amount score"""
        if not company.funding_amount:
            return 30.0  # Low score for unknown funding
        
        min_funding = criteria.get("min_funding", 0)
        max_funding = criteria.get("max_funding", float('inf'))
        
        funding = company.funding_amount
        
        # Check if within preferred range
        if min_funding <= funding <= max_funding:
            # Determine funding stage
            stage = self._determine_funding_stage(funding)
            return self.funding_stage_scores.get(stage, 50.0)
        
        # Penalty for being outside range
        if funding < min_funding:
            # Too small - give partial credit
            return max(20.0, 60.0 * (funding / min_funding))
        else:
            # Too large - less penalty
            return max(60.0, 100.0 * (max_funding / funding))

    def _calculate_company_size_score(
        self, 
        company: Company, 
        enrichment_data: Optional[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> float:
        """Calculate company size preference score"""
        
        # Try to get size from enrichment data first
        if enrichment_data and "company_insights" in enrichment_data:
            size_range = enrichment_data["company_insights"].get("employee_count")
            if size_range and size_range in self.company_size_scores:
                return self.company_size_scores[size_range]
        
        # Estimate from funding amount
        if company.funding_amount:
            estimated_size = self._estimate_size_from_funding(company.funding_amount)
            return self.company_size_scores.get(estimated_size, 50.0)
        
        return 40.0  # Unknown size

    def _calculate_data_completeness_score(
        self, 
        lead: Lead, 
        company: Company, 
        enrichment_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate data completeness score"""
        
        total_fields = 0
        completed_fields = 0
        
        # Lead fields
        fields_to_check = [
            (lead.main_contact_email, 2),  # Email is more important
            (lead.enrichment_status == "completed", 2),
            (lead.score > 0, 1)
        ]
        
        # Company fields
        company_fields = [
            (company.name, 1),
            (company.industry, 2),
            (company.location, 2),
            (company.funding_amount, 1)
        ]
        
        fields_to_check.extend(company_fields)
        
        # Enrichment data fields
        if enrichment_data:
            enrichment_fields = [
                (enrichment_data.get("contact_info", {}).get("phone"), 1),
                (enrichment_data.get("contact_info", {}).get("linkedin"), 1),
                (enrichment_data.get("company_insights", {}).get("website"), 1),
                (enrichment_data.get("company_insights", {}).get("tech_stack"), 1),
                (enrichment_data.get("market_intelligence", {}).get("budget_range"), 2)
            ]
            fields_to_check.extend(enrichment_fields)
        
        # Calculate completeness
        for field_value, weight in fields_to_check:
            total_fields += weight
            if field_value:
                completed_fields += weight
        
        return (completed_fields / total_fields * 100) if total_fields > 0 else 0.0

    def _calculate_engagement_score(
        self, 
        enrichment_data: Optional[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> float:
        """Calculate engagement signals score"""
        
        if not enrichment_data or "market_intelligence" not in enrichment_data:
            return 30.0  # Low score for no engagement data
        
        market_intel = enrichment_data["market_intelligence"]
        score = 0.0
        
        # Engagement score from enrichment
        if "engagement_score" in market_intel:
            score += market_intel["engagement_score"]
        else:
            score += 50.0  # Default
        
        # Buying signals boost
        if "buying_signals" in enrichment_data.get("company_insights", {}):
            signals = enrichment_data["company_insights"]["buying_signals"]
            signal_boost = min(20.0, len(signals) * 5)
            score += signal_boost
        
        # Timing signals boost
        if "timing_signals" in market_intel:
            timing_signals = market_intel["timing_signals"]
            timing_boost = min(15.0, len(timing_signals) * 7.5)
            score += timing_boost
        
        return min(100.0, score)

    def _calculate_timing_score(
        self, 
        enrichment_data: Optional[Dict[str, Any]], 
        criteria: Dict[str, Any]
    ) -> float:
        """Calculate timing indicators score"""
        
        if not enrichment_data:
            return 40.0  # Neutral score for no timing data
        
        score = 40.0  # Base score
        
        # Check market intelligence
        market_intel = enrichment_data.get("market_intelligence", {})
        
        # Urgency level
        urgency = market_intel.get("urgency_level", "medium")
        urgency_scores = {"low": 30, "medium": 60, "high": 90}
        score += (urgency_scores.get(urgency, 60) - 40) * 0.4
        
        # Deal probability
        deal_prob = market_intel.get("deal_probability", "50%")
        try:
            prob_value = float(deal_prob.replace("%", ""))
            score += (prob_value - 50) * 0.5
        except:
            pass
        
        # Recent news/events
        if "recent_news" in enrichment_data.get("company_insights", {}):
            news = enrichment_data["company_insights"]["recent_news"]
            if any(keyword in news.lower() for keyword in ["funding", "launch", "expansion", "hire"]):
                score += 20.0
        
        return min(100.0, max(0.0, score))

    def _apply_score_modifiers(
        self, 
        base_score: float, 
        lead: Lead, 
        company: Company, 
        enrichment_data: Optional[Dict[str, Any]]
    ) -> float:
        """Apply bonus/penalty modifiers to the base score"""
        
        modified_score = base_score
        
        # Bonus for recent enrichment
        if lead.enrichment_status == "completed" and enrichment_data:
            metadata = enrichment_data.get("enrichment_metadata", {})
            enriched_at = metadata.get("enriched_at")
            if enriched_at:
                try:
                    enriched_date = datetime.fromisoformat(enriched_at.replace("Z", "+00:00"))
                    days_since = (datetime.now() - enriched_date.replace(tzinfo=None)).days
                    if days_since <= 7:
                        modified_score += 5.0  # Fresh data bonus
                except:
                    pass
        
        # Penalty for stale data
        if lead.enrichment_status == "pending":
            modified_score -= 3.0
        elif lead.enrichment_status == "failed":
            modified_score -= 8.0
        
        # High-value company bonus
        if company.funding_amount and company.funding_amount >= 50000000:
            modified_score += 7.0
        
        # Industry leadership bonus
        if enrichment_data and "company_insights" in enrichment_data:
            insights = enrichment_data["company_insights"]
            if insights.get("company_size") == "enterprise":
                modified_score += 5.0
        
        # Contact information quality bonus
        if lead.main_contact_email and "@" in lead.main_contact_email:
            # Check for generic emails (penalty)
            generic_emails = ["info@", "contact@", "sales@", "support@"]
            if any(generic in lead.main_contact_email.lower() for generic in generic_emails):
                modified_score -= 2.0
            else:
                modified_score += 3.0  # Personal email bonus
        
        return modified_score

    def _determine_funding_stage(self, funding_amount: float) -> str:
        """Determine funding stage from amount"""
        if funding_amount < 500000:
            return "pre-seed"
        elif funding_amount < 2000000:
            return "seed"
        elif funding_amount < 10000000:
            return "series-a"
        elif funding_amount < 30000000:
            return "series-b"
        elif funding_amount < 100000000:
            return "series-c"
        else:
            return "series-d+"

    def _estimate_size_from_funding(self, funding_amount: float) -> str:
        """Estimate company size from funding amount"""
        if funding_amount < 1000000:
            return "1-10"
        elif funding_amount < 5000000:
            return "11-50"
        elif funding_amount < 20000000:
            return "51-200"
        elif funding_amount < 50000000:
            return "201-1000"
        else:
            return "1000+"

    def score_lead_advanced(
        self, 
        lead_id: int, 
        scoring_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Score a single lead with advanced algorithm"""
        
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            raise ValueError(f"Company not found for lead {lead_id}")
        
        # Get enrichment data if available
        enrichment = self.db.query(LeadEnrichment).filter(
            LeadEnrichment.lead_id == lead_id
        ).first()
        enrichment_data = enrichment.enriched_data if enrichment else None
        
        # Calculate score with breakdown
        score, breakdown = self.calculate_advanced_score(
            lead, company, enrichment_data, scoring_criteria
        )
        
        # Update lead score
        lead.score = score
        self.db.commit()
        self.db.refresh(lead)
        
        return {
            "lead_id": lead_id,
            "score": score,
            "status": "completed",
            "score_breakdown": breakdown,
            "criteria_used": scoring_criteria or self.default_weights,
            "scoring_timestamp": datetime.now().isoformat()
        }

    def batch_score_leads_advanced(
        self, 
        lead_ids: List[int], 
        scoring_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Score multiple leads with advanced algorithm"""
        
        results = {}
        successful = 0
        failed = 0
        errors = []
        
        for lead_id in lead_ids:
            try:
                result = self.score_lead_advanced(lead_id, scoring_criteria)
                results[str(lead_id)] = result["score"]
                successful += 1
            except Exception as e:
                errors.append(f"Lead {lead_id}: {str(e)}")
                results[str(lead_id)] = -1
                failed += 1
        
        return {
            "total_requested": len(lead_ids),
            "successful": successful,
            "failed": failed,
            "scores": results,
            "errors": errors,
            "criteria_used": scoring_criteria or self.default_weights
        }