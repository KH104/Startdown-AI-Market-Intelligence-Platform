"""
Enhanced lead enrichment service with realistic data generation
"""
import random
import re
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.lead import Lead
from app.models.company import Company
from app.models.lead_enrichment import LeadEnrichment


class EnhancedEnrichmentService:
    """Enhanced enrichment service with realistic mock data generation"""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Enhanced data pools for realistic generation
        self.industry_data = {
            "Technology": {
                "roles": ["CTO", "VP Engineering", "Head of Product", "Lead Developer", "Solutions Architect"],
                "tech_stacks": [
                    ["Python", "Django", "PostgreSQL", "Redis", "Docker"],
                    ["JavaScript", "Node.js", "React", "MongoDB", "AWS"],
                    ["Java", "Spring Boot", "MySQL", "Kubernetes", "GCP"],
                    ["Go", "GraphQL", "Cassandra", "Kafka", "Azure"],
                    ["Ruby", "Rails", "PostgreSQL", "Sidekiq", "Heroku"]
                ],
                "pain_points": ["scaling infrastructure", "talent acquisition", "technical debt", "security compliance"],
                "buying_signals": ["rapid growth", "new funding", "team expansion", "system modernization"]
            },
            "Fintech": {
                "roles": ["Chief Risk Officer", "VP Financial Operations", "Compliance Director", "Product Manager"],
                "tech_stacks": [
                    ["Python", "Flask", "PostgreSQL", "Celery", "AWS"],
                    ["Java", "Spring", "Oracle", "Kafka", "Docker"],
                    ["Node.js", "Express", "MongoDB", "Redis", "Azure"]
                ],
                "pain_points": ["regulatory compliance", "fraud prevention", "customer onboarding", "payment processing"],
                "buying_signals": ["new regulations", "security incidents", "customer growth", "international expansion"]
            },
            "Healthcare": {
                "roles": ["Chief Medical Officer", "VP Clinical Operations", "Health IT Director", "Compliance Officer"],
                "tech_stacks": [
                    ["Python", "Django", "PostgreSQL", "FHIR", "AWS"],
                    ["Java", "Spring", "MySQL", "HL7", "Azure"],
                    ["C#", ".NET", "SQL Server", "Azure", "Docker"]
                ],
                "pain_points": ["HIPAA compliance", "patient data security", "interoperability", "cost reduction"],
                "buying_signals": ["regulatory changes", "merger activity", "patient volume growth", "digital transformation"]
            },
            "E-commerce": {
                "roles": ["VP E-commerce", "Digital Marketing Director", "Operations Manager", "Customer Success Manager"],
                "tech_stacks": [
                    ["PHP", "Laravel", "MySQL", "Redis", "AWS"],
                    ["JavaScript", "React", "Node.js", "MongoDB", "Shopify"],
                    ["Python", "Django", "PostgreSQL", "Elasticsearch", "GCP"]
                ],
                "pain_points": ["customer acquisition", "inventory management", "shipping optimization", "conversion rates"],
                "buying_signals": ["seasonal peaks", "new product launches", "market expansion", "customer complaints"]
            },
            "SaaS": {
                "roles": ["VP Product", "Customer Success Director", "Head of Growth", "Engineering Manager"],
                "tech_stacks": [
                    ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                    ["JavaScript", "React", "Node.js", "MongoDB", "AWS"],
                    ["Ruby", "Rails", "PostgreSQL", "Sidekiq", "Heroku"]
                ],
                "pain_points": ["customer churn", "product-market fit", "scalability", "feature development"],
                "buying_signals": ["user growth", "feature requests", "competitive pressure", "funding rounds"]
            }
        }
        
        self.contact_names = {
            "executive": [
                ("John", "Patterson"), ("Sarah", "Chen"), ("Michael", "Rodriguez"), ("Emily", "Thompson"),
                ("David", "Anderson"), ("Lisa", "Williams"), ("Robert", "Garcia"), ("Jessica", "Martinez"),
                ("William", "Taylor"), ("Ashley", "Brown"), ("James", "Davis"), ("Amanda", "Wilson"),
                ("Christopher", "Moore"), ("Nicole", "Jackson"), ("Daniel", "Martin"), ("Rachel", "Lee")
            ],
            "technical": [
                ("Alex", "Kumar"), ("Jordan", "Smith"), ("Casey", "Johnson"), ("Morgan", "Liu"),
                ("Taylor", "Patel"), ("Ryan", "Zhang"), ("Jamie", "Gonzalez"), ("Quinn", "Wang"),
                ("Avery", "Singh"), ("Blake", "Kim"), ("Cameron", "Nguyen"), ("Drew", "Shah")
            ]
        }
        
        self.news_templates = [
            "{company} announced a successful Series {series} funding round of ${funding}M",
            "{company} launched their new {product} targeting {market} customers",
            "{company} expanded operations to {location} with plans to hire {count} employees",
            "{company} partnered with {partner} to enhance their {capability} offerings",
            "{company} reported {metric}% growth in {timeframe} amid strong market demand",
            "{company} unveiled innovative {technology} solution at {event} conference"
        ]

    def generate_realistic_contact_info(self, company: Company, role_type: str = "executive") -> Dict[str, Any]:
        """Generate realistic contact information based on company and role"""
        
        # Select appropriate name based on role type
        if role_type == "executive":
            first_name, last_name = random.choice(self.contact_names["executive"])
        else:
            first_name, last_name = random.choice(self.contact_names["technical"])
        
        # Generate company domain
        domain_name = self._generate_company_domain(company.name)
        
        # Generate email variations
        email_patterns = [
            f"{first_name.lower()}.{last_name.lower()}@{domain_name}",
            f"{first_name.lower()}{last_name.lower()}@{domain_name}",
            f"{first_name[0].lower()}{last_name.lower()}@{domain_name}",
            f"{first_name.lower()}@{domain_name}"
        ]
        
        email = random.choice(email_patterns)
        
        # Generate phone number (realistic US format)
        area_codes = ["415", "650", "408", "925", "510", "707", "831", "559", "209", "530"]  # CA area codes
        if company.location and "NY" in company.location:
            area_codes = ["212", "646", "718", "347", "929", "917"]
        elif company.location and "TX" in company.location:
            area_codes = ["214", "469", "972", "945", "903", "430"]
        
        area_code = random.choice(area_codes)
        phone = f"+1-{area_code}-{random.randint(200,999)}-{random.randint(1000,9999)}"
        
        # Generate LinkedIn URL
        linkedin_handle = f"{first_name.lower()}-{last_name.lower()}-{random.randint(1000,9999)}"
        linkedin_url = f"https://www.linkedin.com/in/{linkedin_handle}"
        
        return {
            "name": f"{first_name} {last_name}",
            "email": email,
            "phone": phone,
            "linkedin": linkedin_url,
            "first_name": first_name,
            "last_name": last_name
        }

    def generate_company_insights(self, company: Company) -> Dict[str, Any]:
        """Generate realistic company insights based on industry and size"""
        
        industry = company.industry if company.industry else "Technology"
        industry_info = self.industry_data.get(industry, self.industry_data["Technology"])
        
        # Estimate company size based on funding
        if company.funding_amount:
            if company.funding_amount < 1000000:
                size_range = "1-10"
                size_category = "startup"
            elif company.funding_amount < 5000000:
                size_range = "11-50"
                size_category = "small"
            elif company.funding_amount < 20000000:
                size_range = "51-200"
                size_category = "medium"
            elif company.funding_amount < 50000000:
                size_range = "201-1000"
                size_category = "large"
            else:
                size_range = "1000+"
                size_category = "enterprise"
        else:
            size_range = "11-50"
            size_category = "small"
        
        # Generate website and domain
        domain = self._generate_company_domain(company.name)
        website = f"https://www.{domain}"
        
        # Select appropriate tech stack and pain points
        tech_stack = random.choice(industry_info["tech_stacks"])
        pain_points = random.sample(industry_info["pain_points"], min(3, len(industry_info["pain_points"])))
        buying_signals = random.sample(industry_info["buying_signals"], min(2, len(industry_info["buying_signals"])))
        
        # Generate competitors (realistic for industry)
        competitors = self._generate_competitors(industry, company.name)
        
        # Generate recent news
        news = self._generate_company_news(company)
        
        return {
            "website": website,
            "domain": domain,
            "employee_count": size_range,
            "company_size": size_category,
            "tech_stack": tech_stack,
            "pain_points": pain_points,
            "buying_signals": buying_signals,
            "competitors": competitors,
            "recent_news": news,
            "industry_category": industry,
            "funding_stage": self._determine_funding_stage(company.funding_amount)
        }

    def generate_market_intelligence(self, company: Company) -> Dict[str, Any]:
        """Generate market intelligence and sales insights"""
        
        # Determine market size and growth
        market_sizes = ["small", "medium", "large", "massive"]
        market_size = random.choice(market_sizes)
        
        growth_rates = [5, 8, 12, 15, 18, 22, 25, 30, 35, 40]
        market_growth = random.choice(growth_rates)
        
        # Generate buying cycle information
        buying_cycles = {
            "Technology": "3-6 months",
            "Fintech": "6-12 months", 
            "Healthcare": "9-18 months",
            "E-commerce": "1-3 months",
            "SaaS": "2-4 months",
            "Manufacturing": "6-12 months",
            "Education": "12-24 months"
        }
        
        industry = company.industry if company.industry else "Technology"
        buying_cycle = buying_cycles.get(industry, "3-6 months")
        
        # Generate decision makers
        decision_makers = self._generate_decision_makers(industry)
        
        # Generate budget information
        budget_range = self._estimate_budget_range(company.funding_amount)
        
        # Generate engagement score
        engagement_score = random.randint(60, 95)
        
        # Generate timing signals
        timing_signals = self._generate_timing_signals(company)
        
        return {
            "market_size": market_size,
            "market_growth_rate": f"{market_growth}%",
            "buying_cycle": buying_cycle,
            "decision_makers": decision_makers,
            "budget_range": budget_range,
            "engagement_score": engagement_score,
            "timing_signals": timing_signals,
            "competitive_landscape": "moderate",
            "urgency_level": random.choice(["low", "medium", "high"]),
            "deal_probability": f"{random.randint(15, 75)}%"
        }

    def enrich_lead_with_retry(self, lead_id: int, retry_count: int = 3) -> Dict[str, Any]:
        """Enrich lead with retry mechanism for failed enrichments"""
        
        for attempt in range(retry_count):
            try:
                return self.enrich_lead_advanced(lead_id)
            except Exception as e:
                if attempt == retry_count - 1:
                    # Mark as failed after all retries
                    lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
                    if lead:
                        lead.enrichment_status = "failed"
                        self.db.commit()
                    raise e
                else:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
        
    def enrich_lead_advanced(self, lead_id: int) -> Dict[str, Any]:
        """Advanced lead enrichment with comprehensive data generation"""
        
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        company = self.db.query(Company).filter(Company.id == lead.company_id).first()
        if not company:
            raise ValueError(f"Company not found for lead {lead_id}")
        
        # Mark as in progress
        lead.enrichment_status = "in_progress"
        self.db.commit()
        
        # Generate comprehensive enrichment data
        contact_info = self.generate_realistic_contact_info(company)
        company_insights = self.generate_company_insights(company)
        market_intelligence = self.generate_market_intelligence(company)
        
        # Determine role based on company size and industry
        industry = company.industry if company.industry else "Technology"
        industry_info = self.industry_data.get(industry, self.industry_data["Technology"])
        job_title = random.choice(industry_info["roles"])
        
        # Combine all enrichment data
        enriched_data = {
            "contact_info": {
                "name": contact_info["name"],
                "email": contact_info["email"],
                "phone": contact_info["phone"],
                "linkedin": contact_info["linkedin"],
                "job_title": job_title,
                "verified": random.choice([True, False])
            },
            "company_insights": company_insights,
            "market_intelligence": market_intelligence,
            "enrichment_metadata": {
                "enriched_at": datetime.now().isoformat(),
                "data_sources": ["company_website", "social_media", "public_records", "industry_reports"],
                "confidence_score": random.randint(75, 95),
                "last_updated": datetime.now().isoformat()
            }
        }
        
        # Update lead contact email if not set
        if not lead.main_contact_email:
            lead.main_contact_email = contact_info["email"]
        
        # Create or update enrichment record
        existing_enrichment = self.db.query(LeadEnrichment).filter(
            LeadEnrichment.lead_id == lead.id
        ).first()
        
        if existing_enrichment:
            existing_enrichment.enriched_data = enriched_data
            existing_enrichment.last_checked = datetime.now()
        else:
            enrichment = LeadEnrichment(
                lead_id=lead.id,
                enriched_data=enriched_data,
                last_checked=datetime.now()
            )
            self.db.add(enrichment)
        
        # Mark as completed
        lead.enrichment_status = "completed"
        self.db.commit()
        self.db.refresh(lead)
        
        return {
            "lead_id": lead_id,
            "status": "completed",
            "enriched_data": enriched_data,
            "lead": {
                "id": lead.id,
                "main_contact_email": lead.main_contact_email,
                "enrichment_status": lead.enrichment_status,
                "score": lead.score
            }
        }

    def _generate_company_domain(self, company_name: str) -> str:
        """Generate realistic company domain from name"""
        # Clean company name
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', company_name.lower())
        clean_name = clean_name.replace(' ', '')
        
        # Truncate if too long
        if len(clean_name) > 15:
            clean_name = clean_name[:15]
        
        # Add domain extension
        extensions = [".com", ".io", ".net", ".co"]
        extension = random.choice(extensions)
        
        return f"{clean_name}{extension}"

    def _generate_competitors(self, industry: str, company_name: str) -> List[str]:
        """Generate realistic competitors based on industry"""
        competitor_pools = {
            "Technology": ["Microsoft", "Google", "Amazon", "Salesforce", "Oracle", "IBM"],
            "Fintech": ["Square", "PayPal", "Stripe", "Plaid", "Robinhood", "Coinbase"],
            "Healthcare": ["Epic", "Cerner", "Allscripts", "athenahealth", "Veracyte"],
            "E-commerce": ["Shopify", "WooCommerce", "Magento", "BigCommerce", "Amazon"],
            "SaaS": ["HubSpot", "Zendesk", "Slack", "Zoom", "Asana", "Monday.com"]
        }
        
        pool = competitor_pools.get(industry, competitor_pools["Technology"])
        # Don't include the company itself
        pool = [comp for comp in pool if comp.lower() not in company_name.lower()]
        
        return random.sample(pool, min(3, len(pool)))

    def _generate_company_news(self, company: Company) -> str:
        """Generate realistic recent news about the company"""
        template = random.choice(self.news_templates)
        
        # Fill in template variables
        series_letters = ["A", "B", "C", "D"]
        funding_amounts = [1, 2, 5, 10, 15, 25, 50, 100]
        products = ["platform", "solution", "app", "service", "tool"]
        markets = ["enterprise", "SMB", "consumer", "healthcare", "fintech"]
        locations = ["Austin", "Denver", "Seattle", "Boston", "Chicago"]
        partners = ["Microsoft", "Google", "AWS", "Salesforce", "Oracle"]
        capabilities = ["AI", "analytics", "security", "integration", "automation"]
        technologies = ["AI-powered", "blockchain-based", "cloud-native", "mobile-first"]
        events = ["TechCrunch", "CES", "Dreamforce", "re:Invent", "Build"]
        
        news = template.format(
            company=company.name,
            series=random.choice(series_letters),
            funding=random.choice(funding_amounts),
            product=random.choice(products),
            market=random.choice(markets),
            location=random.choice(locations),
            count=random.randint(10, 100),
            partner=random.choice(partners),
            capability=random.choice(capabilities),
            metric=random.randint(50, 200),
            timeframe="Q3 2024",
            technology=random.choice(technologies),
            event=random.choice(events)
        )
        
        return news

    def _determine_funding_stage(self, funding_amount: Optional[float]) -> str:
        """Determine funding stage based on amount"""
        if not funding_amount:
            return "pre-seed"
        
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

    def _generate_decision_makers(self, industry: str) -> List[str]:
        """Generate typical decision makers for industry"""
        decision_maker_map = {
            "Technology": ["CTO", "VP Engineering", "Head of Product"],
            "Fintech": ["CFO", "Chief Risk Officer", "VP Operations"],
            "Healthcare": ["CMO", "Chief Medical Officer", "VP Clinical"],
            "E-commerce": ["VP E-commerce", "CMO", "Operations Director"],
            "SaaS": ["VP Product", "Head of Growth", "Customer Success Director"]
        }
        
        return decision_maker_map.get(industry, ["CEO", "CTO", "VP Operations"])

    def _estimate_budget_range(self, funding_amount: Optional[float]) -> str:
        """Estimate budget range based on company funding"""
        if not funding_amount:
            return "$10K-$50K"
        
        if funding_amount < 1000000:
            return "$5K-$25K"
        elif funding_amount < 5000000:
            return "$25K-$100K"
        elif funding_amount < 20000000:
            return "$100K-$500K"
        elif funding_amount < 50000000:
            return "$500K-$2M"
        else:
            return "$2M+"

    def _generate_timing_signals(self, company: Company) -> List[str]:
        """Generate timing signals for sales engagement"""
        signals = [
            "Recent funding announcement",
            "New executive hire",
            "Product launch planned",
            "Market expansion",
            "Competitive pressure",
            "Technology upgrade cycle",
            "Seasonal demand increase",
            "Regulatory compliance deadline"
        ]
        
        return random.sample(signals, random.randint(1, 3))