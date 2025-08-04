"""
Outreach service for managing email campaigns and communications
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.outreach import OutreachCampaign, OutreachAttempt
from app.models.lead import Lead
from app.models.company import Company
from app.models.lead_enrichment import LeadEnrichment


class OutreachService:
    """Service class for outreach operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_campaign(
        self,
        user_id: int,
        name: str,
        subject_template: str,
        message_template: str,
        auto_send: bool = False
    ) -> OutreachCampaign:
        """Create a new outreach campaign"""
        campaign = OutreachCampaign(
            user_id=user_id,
            name=name,
            subject_template=subject_template,
            message_template=message_template,
            auto_send=auto_send
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
    
    def get_user_campaigns(self, user_id: int) -> List[OutreachCampaign]:
        """Get all campaigns for a user"""
        return self.db.query(OutreachCampaign).filter(
            OutreachCampaign.user_id == user_id
        ).all()
    
    def personalize_message(
        self,
        template: str,
        lead: Lead,
        company: Optional[Company] = None,
        enrichment_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Personalize message template with lead and company data"""
        message = template
        
        # Company personalization
        if company:
            message = message.replace("{company_name}", company.name or "")
            message = message.replace("{company_industry}", company.industry or "Unknown")
            message = message.replace("{company_location}", company.location or "")
            
            if company.funding_amount:
                funding_str = f"${company.funding_amount:,.0f}"
            else:
                funding_str = "undisclosed"
            message = message.replace("{company_funding}", funding_str)
        
        # Lead personalization
        message = message.replace("{contact_email}", lead.main_contact_email or "")
        message = message.replace("{lead_score}", str(lead.score))
        
        # Enrichment data personalization
        if enrichment_data:
            contact_info = enrichment_data.get("contact_info", {})
            message = message.replace("{contact_name}", self._extract_name_from_email(lead.main_contact_email))
            message = message.replace("{job_title}", contact_info.get("job_title", ""))
            message = message.replace("{linkedin_url}", contact_info.get("linkedin", ""))
            
            # Add insights
            insights = enrichment_data.get("company_insights", {})
            tech_stack = insights.get("tech_stack", [])
            if tech_stack:
                message = message.replace("{tech_stack}", ", ".join(tech_stack[:3]))
            else:
                message = message.replace("{tech_stack}", "modern technologies")
        
        # Default fallbacks
        message = message.replace("{contact_name}", self._extract_name_from_email(lead.main_contact_email))
        message = message.replace("{job_title}", "")
        message = message.replace("{linkedin_url}", "")
        message = message.replace("{tech_stack}", "")
        
        return message
    
    def _extract_name_from_email(self, email: Optional[str]) -> str:
        """Extract a name from email address"""
        if not email:
            return "there"
        
        # Extract name part before @
        name_part = email.split("@")[0]
        
        # Handle common formats like first.last, first_last, firstlast
        if "." in name_part:
            parts = name_part.split(".")
            first_name = parts[0].capitalize()
            return first_name
        elif "_" in name_part:
            parts = name_part.split("_")
            first_name = parts[0].capitalize()
            return first_name
        else:
            return name_part.capitalize()
    
    def send_outreach(
        self,
        lead_id: int,
        user_id: int,
        subject: str,
        message: str,
        campaign_id: Optional[int] = None,
        delivery_method: str = "email"
    ) -> OutreachAttempt:
        """Send outreach to a lead (mock implementation for MVP)"""
        # Get lead and validate
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        if not lead.main_contact_email:
            raise ValueError(f"Lead {lead_id} has no contact email")
        
        # Create outreach attempt record
        attempt = OutreachAttempt(
            campaign_id=campaign_id,
            lead_id=lead_id,
            user_id=user_id,
            recipient_email=lead.main_contact_email,
            subject=subject,
            message=message,
            delivery_method=delivery_method
        )
        
        # Mock email sending
        try:
            # In a real implementation, you would:
            # - Use an email service (SendGrid, Mailgun, etc.)
            # - Track email delivery and opens
            # - Handle bounces and unsubscribes
            
            # For MVP, we just log the outreach
            print(f"📧 OUTREACH SENT:")
            print(f"   To: {lead.main_contact_email}")
            print(f"   From: User {user_id}")
            print(f"   Subject: {subject}")
            print(f"   Lead ID: {lead_id}")
            print(f"   Campaign: {campaign_id}")
            print("   Message Preview:", message[:100] + "..." if len(message) > 100 else message)
            
            attempt.status = "sent"
            attempt.sent_at = datetime.utcnow()
            
            # Update campaign statistics if part of campaign
            if campaign_id:
                campaign = self.db.query(OutreachCampaign).filter(
                    OutreachCampaign.id == campaign_id
                ).first()
                if campaign:
                    campaign.total_sent += 1
            
        except Exception as e:
            attempt.status = "failed"
            attempt.error_message = str(e)
        
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        
        return attempt
    
    def send_bulk_outreach(
        self,
        lead_ids: List[int],
        user_id: int,
        campaign_id: Optional[int] = None,
        subject_template: Optional[str] = None,
        message_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send outreach to multiple leads"""
        results = {
            "sent": 0,
            "failed": 0,
            "errors": [],
            "attempts": []
        }
        
        # Get campaign templates if campaign_id provided
        if campaign_id:
            campaign = self.db.query(OutreachCampaign).filter(
                OutreachCampaign.id == campaign_id,
                OutreachCampaign.user_id == user_id
            ).first()
            
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            subject_template = campaign.subject_template
            message_template = campaign.message_template
        
        if not subject_template or not message_template:
            raise ValueError("Subject and message templates are required")
        
        for lead_id in lead_ids:
            try:
                # Get lead and company data
                lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
                if not lead:
                    results["failed"] += 1
                    results["errors"].append(f"Lead {lead_id} not found")
                    continue
                
                if not lead.main_contact_email:
                    results["failed"] += 1
                    results["errors"].append(f"Lead {lead_id} has no contact email")
                    continue
                
                company = self.db.query(Company).filter(Company.id == lead.company_id).first()
                
                # Get enrichment data
                enrichment = self.db.query(LeadEnrichment).filter(
                    LeadEnrichment.lead_id == lead_id
                ).first()
                enrichment_data = enrichment.enriched_data if enrichment else None
                
                # Personalize templates
                subject = self.personalize_message(subject_template, lead, company, enrichment_data)
                message = self.personalize_message(message_template, lead, company, enrichment_data)
                
                # Send outreach
                attempt = self.send_outreach(
                    lead_id=lead_id,
                    user_id=user_id,
                    subject=subject,
                    message=message,
                    campaign_id=campaign_id
                )
                
                results["attempts"].append(attempt.id)
                
                if attempt.status == "sent":
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"Lead {lead_id}: {attempt.error_message}")
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Lead {lead_id}: {str(e)}")
        
        return results
    
    def get_outreach_attempts(
        self,
        user_id: int,
        lead_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        limit: int = 100
    ) -> List[OutreachAttempt]:
        """Get outreach attempts for a user"""
        query = self.db.query(OutreachAttempt).filter(
            OutreachAttempt.user_id == user_id
        )
        
        if lead_id:
            query = query.filter(OutreachAttempt.lead_id == lead_id)
        
        if campaign_id:
            query = query.filter(OutreachAttempt.campaign_id == campaign_id)
        
        return query.order_by(OutreachAttempt.created_at.desc()).limit(limit).all()
    
    def get_default_templates(self) -> Dict[str, Dict[str, str]]:
        """Get default email templates for different scenarios"""
        return {
            "introduction": {
                "subject": "Quick question about {company_name}'s {company_industry} initiatives",
                "message": """Hi {contact_name},

I noticed {company_name} is doing interesting work in the {company_industry} space. Your recent growth (I see you've raised {company_funding}) suggests you're scaling rapidly.

I work with companies using {tech_stack} to solve similar challenges. Would you be open to a brief conversation about how we could potentially help {company_name} accelerate growth?

Best regards,
[Your Name]

P.S. I saw your profile on LinkedIn - {linkedin_url} - impressive background!"""
            },
            "follow_up": {
                "subject": "Following up: {company_name} growth opportunities",
                "message": """Hi {contact_name},

I wanted to follow up on my previous message about {company_name}. 

Given your {job_title} role and {company_name}'s position in {company_location}, I thought you might be interested in how other companies in {company_industry} are tackling similar challenges.

Would a 15-minute call work for you this week?

Best,
[Your Name]"""
            },
            "value_proposition": {
                "subject": "How {company_name} could save 20+ hours/week",
                "message": """Hi {contact_name},

Companies like {company_name} in {company_industry} typically spend significant time on manual processes.

Our platform helps businesses like yours:
• Automate lead research (save 15+ hours/week)
• Increase lead quality by 40%
• Improve conversion rates with AI scoring

With {company_name}'s current growth trajectory, this could be a perfect fit.

Quick 15-minute demo this week?

Best,
[Your Name]"""
            }
        }
    
    def mark_opened(self, attempt_id: int, user_id: int) -> bool:
        """Mark an outreach attempt as opened"""
        attempt = self.db.query(OutreachAttempt).filter(
            OutreachAttempt.id == attempt_id,
            OutreachAttempt.user_id == user_id
        ).first()
        
        if not attempt:
            return False
        
        if not attempt.opened_at:
            attempt.opened_at = datetime.utcnow()
            attempt.status = "opened"
            
            # Update campaign statistics
            if attempt.campaign_id:
                campaign = self.db.query(OutreachCampaign).filter(
                    OutreachCampaign.id == attempt.campaign_id
                ).first()
                if campaign:
                    campaign.total_opened += 1
            
            self.db.commit()
        
        return True
    
    def mark_replied(self, attempt_id: int, user_id: int, reply_content: str) -> bool:
        """Mark an outreach attempt as replied"""
        attempt = self.db.query(OutreachAttempt).filter(
            OutreachAttempt.id == attempt_id,
            OutreachAttempt.user_id == user_id
        ).first()
        
        if not attempt:
            return False
        
        if not attempt.replied_at:
            attempt.replied_at = datetime.utcnow()
            attempt.status = "replied"
            attempt.reply_content = reply_content
            
            # Update campaign statistics
            if attempt.campaign_id:
                campaign = self.db.query(OutreachCampaign).filter(
                    OutreachCampaign.id == attempt.campaign_id
                ).first()
                if campaign:
                    campaign.total_replied += 1
            
            self.db.commit()
        
        return True