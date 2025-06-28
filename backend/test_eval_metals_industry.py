#!/usr/bin/env python3
"""
Comprehensive Test Evaluation: Metals Industry Customer Emails
Tests Phase 2 Sales Order Intelligence with 20 diverse, realistic customer scenarios
"""

import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.reasoning_framework import SalesOrderReasoningFramework
from app.mcp.fulfillment_execution import SalesOrderSearchCoordinator
from app.models.line_item_schemas import LineItem
from app.services.local_parts_catalog import LocalPartsCatalogService
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# 20 Diverse Customer Email Test Cases
CUSTOMER_EMAILS = [
    {
        "test_id": "001",
        "category": "Emergency Production - Major Auto",
        "customer": "Ford Motor Company - Dearborn Plant",
        "subject": "URGENT: Production Line Down - Need SS316L Tubing ASAP",
        "email_body": """EMERGENCY REQUEST - PRODUCTION CRITICAL
        
Our stamping line #3 is down due to hydraulic failure. Need immediate replacement:

- Stainless Steel 316L seamless tubing
- 2.5" OD x 0.065" wall thickness 
- Length: 48" pieces (need 6 pieces minimum)
- Pressure rating: 3000 PSI minimum
- Mill cert required

Production impact: $85K per hour downtime
Need delivery by tomorrow 2PM latest

Contact: Mike Rodriguez, Production Manager
Direct: 313-555-0147
This is affecting F-150 production schedule.

Best regards,
Mike Rodriguez
Ford Motor Company - Dearborn Stamping Plant""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "automotive", 
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock", "custom_solution"]
    },
    
    {
        "test_id": "002", 
        "category": "Precision Aerospace - Small Supplier",
        "customer": "Precision Aerospace Components LLC",
        "subject": "RFQ: Ti-6Al-4V bars for Boeing subcontract",
        "email_body": """Dear Supplier,

We are a Tier 2 supplier to Boeing and require the following for aircraft landing gear components:

Material: Titanium 6Al-4V (Grade 5)
Form: Round bar stock
Diameter: 3.25" +/- 0.005"
Length: 12" lengths
Quantity: 15 pieces
Certifications Required:
- AS9100 Rev D compliant
- Material certs per AMS 4928
- Full traceability to heat lot

This is for 737 MAX landing gear assemblies. Boeing audit trail required.
Need quote by Friday, delivery in 3 weeks.

Project: BNG-LG-4472
PO will follow upon quote approval.

Thanks,
Jennifer Chen, Materials Manager
Precision Aerospace Components LLC
AS9100 Certified Facility
CAGE Code: 7H429""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "aerospace",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "003",
        "category": "Research Institution - Informal",
        "customer": "MIT Materials Science Lab",
        "subject": "need some aluminum samples for testing",
        "email_body": """hey there,

prof johnson here from MIT materials lab. we're doing some fatigue testing and need aluminum samples. not sure exactly what grades yet but thinking:

- aluminum 6061-T6 
- aluminum 7075-T6
- maybe some 2024-T3 if you have it

sizes around 1" x 6" strips, thickness doesn't matter much, maybe 0.25" ish?
need like 20-30 pieces total, mixed grades ok

this is for NSF grant research on crack propagation. budget is tight but we can pay net 30 if that works.

student pickup ok? we're in cambridge.

thanks!
prof j
MIT materials lab
room 8-139""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "research_development", 
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products", "split_shipment"]
    },

    {
        "test_id": "004",
        "category": "Medical Device - Regulatory Critical",
        "customer": "BioMed Implants Corporation",
        "subject": "URGENT: FDA submission deadline - 316LVM surgical steel",
        "email_body": """CRITICAL REQUEST - FDA SUBMISSION DEADLINE

We have an FDA 510(k) submission deadline of December 15th and require:

MATERIAL: 316LVM Stainless Steel (Vacuum Melted)
SPECIFICATIONS:
- Round bar: 0.375" diameter ± 0.001"
- Length: 6" pieces
- Quantity: 50 pieces
- Surface finish: 32 Ra max
- ASTM F138 compliant

CRITICAL REQUIREMENTS:
✓ Full biocompatibility testing certificates
✓ USP Class VI certification
✓ Material traceability to heat number
✓ ISO 13485 supplier qualification
✓ Endotoxin testing documentation

This material is for cardiac stent prototypes. FDA is expecting submission with material certs included.

DELIVERY NEEDED: By December 10th
BUDGET APPROVED: Up to $15K for expedited processing

Please confirm availability immediately.

Best regards,
Dr. Sarah Kim, VP Engineering
BioMed Implants Corporation
FDA Registered Facility #12345678
ISO 13485:2016 Certified""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "medical_device",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "005",
        "category": "Small Machine Shop - Cost Conscious", 
        "customer": "Joe's Precision Machining",
        "subject": "Quote request - steel bar stock",
        "email_body": """Hi,

Small family shop here, been in business 35 years. Need some steel for a local job:

4140 steel round bar
- 2" diameter  
- 36" lengths
- Need 8 pieces

Customer is a local farm equipment manufacturer, nothing fancy. Standard mill tolerance fine.

What's your best price? We usually buy from local suppliers but they're out of stock. Need delivery next week.

Can pay COD or check on delivery.

Thanks,
Joe Kowalski  
Joe's Precision Machining
Family owned since 1988""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products"]
    },

    {
        "test_id": "006",
        "category": "Defense Contractor - Security Sensitive",
        "customer": "Lockheed Martin Skunk Works",
        "subject": "CLASSIFIED MATERIAL REQUEST - Special Alloy",
        "email_body": """**UNCLASSIFIED//FOR OFFICIAL USE ONLY**

Material Request for Project AURORA-7 (Classification: CONFIDENTIAL)

REQUIREMENTS:
- Inconel 718 round bar stock
- Diameter: 4.00" ± 0.010"
- Length: 24" pieces
- Quantity: 12 pieces
- Solution annealed condition

COMPLIANCE REQUIREMENTS:
- ITAR registered supplier only
- Security clearance verification required
- No foreign national involvement in processing
- DCMA quality oversight
- DFARS compliant sourcing

Project Officer: Col. James Mitchell, USAF
Contract: FA8650-23-C-1234
Delivery: Palmdale Facility, Building 602

Material testing will be conducted at classified facility.
Delivery schedule is project critical.

POC: Sarah Thompson, Materials Engineering
Cleared: SECRET level
Phone: 661-555-0199 (secure line)

**UNCLASSIFIED//FOR OFFICIAL USE ONLY**""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "aerospace",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "007",
        "category": "Startup - Cash Flow Issues",
        "customer": "Tesla Competitor Motors (Stealth Mode)",
        "subject": "Aluminum space frame materials - payment terms needed",
        "email_body": """Hello,

We're a stealth-mode EV startup (can't disclose name yet, but think Tesla competitor). Building our first prototype and need aluminum for space frame:

MATERIALS NEEDED:
- Aluminum 6061-T6 extrusions
- Various profiles: 2"x2" square tube, 1.5" round tube
- Total length needed: ~500 linear feet
- Wall thickness: 0.125" typical

CHALLENGE: We're pre-revenue startup with limited cash flow but solid VC backing (Series A closing next month).

PAYMENT: Can we do Net 60 terms? Have LOI from Andreessen Horowitz for $50M Series A. Can provide investor contact for verification.

This is for our alpha prototype vehicle. If relationship works, we'll need 10,000+ parts for beta builds.

Stealth mode = can't provide company name yet, but happy to do video call.

Best,
"Mike" (not real name)
Chief Technology Officer
[Stealth Mode EV Company]
Direct: 650-555-0156""",
        "expected_complexity": "MODERATE",
        "expected_industry": "automotive",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products", "split_shipment"]
    },

    {
        "test_id": "008",
        "category": "International Customer - Language Barrier",
        "customer": "Kawasaki Heavy Industries - Japan",
        "subject": "Urgent request for steel plate material",
        "email_body": """Dear Respected Supplier,

We are Kawasaki Heavy Industries from Japan. Please excuse my English writing.

We need steel plate for motorcycle frame manufacturing:

Material specification:
- Steel plate AISI 4130 chrome-moly
- Thickness: 3mm (approximately 0.118 inch)
- Size: 1000mm x 2000mm (approximately 39" x 79")
- Quantity: 25 pieces
- Heat treatment: normalized condition

This material for new Ninja motorcycle model production line in Nebraska factory. Very important for production schedule.

Please quotation include:
- Material cost
- Shipping cost to Nebraska
- Delivery time
- Payment terms (we prefer wire transfer)

Our purchasing manager Mr. Tanaka will contact for technical discussion.

Thank you for your cooperation.

Best regards,
Hiroshi Yamamoto
Materials Procurement Department
Kawasaki Heavy Industries, Ltd.
Kobe, Japan
Email: yamamoto.h@khi.co.jp""",
        "expected_complexity": "MODERATE", 
        "expected_industry": "automotive",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products"]
    },

    {
        "test_id": "009",
        "category": "Oil & Gas - Harsh Environment",
        "customer": "Halliburton Energy Services",
        "subject": "Downhole tool materials - H2S resistant",
        "email_body": """MATERIAL REQUEST - SOUR GAS SERVICE

Project: Permian Basin Completion Tools
Operating Environment: H2S service, 15,000 PSI, 350°F

MATERIAL REQUIREMENTS:
- Duplex Stainless Steel 2205 (UNS S32205)
- Round bar stock
- Diameter: 3.5" +0.010/-0.000
- Length: 72" pieces 
- Quantity: 8 pieces
- Condition: Solution annealed + pickled

CRITICAL SPECIFICATIONS:
✓ NACE MR0175/ISO 15156 compliant for sour service
✓ Impact testing at -20°F required
✓ PMI verification (portable XRF acceptable)
✓ Hardness: 32 HRC maximum
✓ Material certs showing PRE ≥ 35

This is for downhole drilling tools in sour gas wells. Material failure = $2M well loss.

Delivery: Midland, TX by month end
Budget: Approved for premium pricing

Contact: Jim Patterson, Materials Engineer
Phone: 432-555-0188
Project: PB-2024-CT-0067

Thanks,
Jim Patterson
Halliburton Energy Services
Permian Basin Operations""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "010",
        "category": "Art Installation - Unique Application",
        "customer": "Maya Lin Studio",
        "subject": "Weathering steel for memorial sculpture",
        "email_body": """Dear Metal Suppliers,

I am working with artist Maya Lin on a memorial sculpture installation and we need weathering steel (Cor-Ten) for the project.

ARTISTIC REQUIREMENTS:
- Weathering Steel A588 Grade A
- Plate thickness: 0.75" 
- Sheets: 8' x 4' (standard size preferred)
- Quantity: 12 sheets
- Surface: Mill finish (will weather naturally)

This is for a 9/11 memorial installation in Lower Manhattan. The steel will be cut into geometric forms and allowed to develop natural patina over time.

SPECIAL CONSIDERATIONS:
- Material must be clean (no oil, markings that affect weathering)
- Delivery to NYC art fabrication facility
- Installation deadline: September 2024 (memorial anniversary)
- Budget: $25K maximum for materials

The piece will be permanent outdoor installation, so material quality is critical for longevity.

Please provide:
- Material availability 
- Cost estimate
- Recommended surface preparation
- NYC delivery options

Thank you,
David Chen, Project Manager
Maya Lin Studio
New York, NY
Phone: 212-555-0134""",
        "expected_complexity": "MODERATE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products"]
    },

    {
        "test_id": "011",
        "category": "Maintenance Emergency - Plant Shutdown",
        "customer": "U.S. Steel Gary Works",
        "subject": "PLANT EMERGENCY: Blast furnace bearing housing cracked",
        "email_body": """***EMERGENCY MAINTENANCE REQUEST***

BLAST FURNACE #4 SHUTDOWN - BEARING FAILURE

Situation: Main drive bearing housing cracked during night shift. Blast furnace shut down, losing $180K per hour.

IMMEDIATE NEED:
- Cast Steel Grade WCB bearing housing blank
- Approximate dimensions: 48" diameter x 24" thick
- OR suitable forging blank we can machine
- Weight: ~8,000 lbs estimated

ALTERNATIVES ACCEPTABLE:
- 4140 steel forging (will re-machine)
- A105 carbon steel forging
- Any machinable steel block of suitable size

DELIVERY: Need material on-site within 72 hours maximum
BUDGET: Unlimited - this is production critical
TRANSPORT: We can arrange heavy haul pickup

Our machine shop can work around the clock once material arrives.

Emergency contact: 
- Plant Manager: Bill Hughes (219-555-0123)
- Maintenance Super: Tom Kowalski (219-555-0456)
- This phone answered 24/7

Every hour counts. Blast furnace cooling costs $2M to restart.

Thanks,
Tom Kowalski, Maintenance Superintendent  
U.S. Steel Gary Works
Emergency Response Team""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "general_manufacturing",
        "expected_emergency": True,
        "expected_strategies": ["expedited_restock", "custom_solution", "alternative_products"]
    },

    {
        "test_id": "012",
        "category": "Prototype Development - Tech Startup",
        "customer": "Quantum Computing Labs Inc",
        "subject": "Ultra-pure copper for quantum computer prototype",
        "email_body": """Hello,

We're developing quantum computing hardware and need ultra-pure copper for our cryogenic systems.

SPECIFICATIONS:
- Copper C10100 (99.99% pure minimum)
- Form: Round rod
- Diameter: 0.5" ± 0.001"
- Length: 12" pieces
- Quantity: 6 pieces
- Surface: Bright annealed finish

APPLICATION: Superconducting quantum processor operating at 10 milliKelvin (-273.14°C). Any impurities cause quantum decoherence.

TESTING REQUIRED:
- Residual resistivity ratio (RRR) > 300
- Oxygen content < 5 ppm
- Total impurities < 10 ppm
- Surface roughness < 0.5 μm Ra

This is for our Series B investor demo next month. Google Ventures is evaluating our technology.

BUDGET: $50K approved for prototype materials
TIMELINE: 2 weeks delivery preferred

We're located in Palo Alto. Can arrange pickup.

Best regards,
Dr. Alex Chen, CTO
Quantum Computing Labs Inc
Stanford Research Park
alex.chen@qcl.com""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "research_development",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "custom_solution"]
    },

    {
        "test_id": "013",
        "category": "Small Contractor - Home Builder",
        "customer": "Rodriguez Construction LLC",
        "subject": "Steel beams for custom home",
        "email_body": """Hi there,

Small residential contractor here. Building a custom home with exposed steel beams and need some material.

What I need:
- Steel I-beams (wide flange)
- Size: W8 x 31 (8 inch deep)
- Lengths: (4) 20-foot beams, (2) 16-foot beams  
- Finish: Painted black (or can we get raw and paint ourselves?)

This is for a high-end custom home in Marin County. Architect wants exposed structural steel look in living room.

Questions:
- What's the price difference painted vs raw?
- Can you deliver to job site? (residential area)
- Payment terms? (we're small contractor, net 30 helpful)
- Building inspector will need mill certs - included?

Job needs to close escrow by end of month so timing is important.

Thanks,
Carlos Rodriguez
Rodriguez Construction LLC
Licensed Contractor #789456
Marin County, CA
carlos.r.construction@gmail.com""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products"]
    },

    {
        "test_id": "014",
        "category": "Marine Application - Corrosion Critical",
        "customer": "Boston Whaler Marine Engineering",
        "subject": "Marine grade aluminum for boat hull repairs",
        "email_body": """Marine Engineering Department
Boston Whaler Manufacturing

Subject: Urgent aluminum stock for hull damage repairs

We have multiple boats in for warranty hull repairs and need marine grade aluminum stock:

MATERIAL: 5086 Marine Aluminum Alloy
TEMPER: H116 (corrosion resistant)
FORMS NEEDED:
- Plate: 0.25" thick x 48" x 96" sheets (need 6 sheets)
- Plate: 0.125" thick x 48" x 96" sheets (need 4 sheets)
- Bar: 2" x 0.25" flat bar x 12' lengths (need 8 pieces)

MARINE REQUIREMENTS:
✓ Mill certs showing 5086-H116 alloy compliance
✓ Salt spray testing documentation (ASTM B117)
✓ Magnesium content verification (3.5-4.5%)
✓ No welding wire needed (we stock)

URGENCY: Hurricane season damaged boats, customers waiting for repairs. Coast Guard inspection scheduled.

These are for hull patches on 25-35 foot pleasure craft. Safety critical application.

Delivery to: Edgewater, FL facility
Timeline: ASAP, customers getting restless
Budget: Standard marine pricing acceptable

Contact: Mike Sullivan, Marine Engineer
Phone: 386-555-0167
USCG Licensed Marine Inspector

Boston Whaler Marine Engineering
Edgewater, Florida""",
        "expected_complexity": "MODERATE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "015",
        "category": "Government Lab - Bureaucratic",
        "customer": "Sandia National Laboratories",
        "subject": "Request for Quote - Tungsten alloy for nuclear research",
        "email_body": """OFFICIAL REQUEST FOR QUOTATION
Sandia National Laboratories
Operated by National Technology & Engineering Solutions of Sandia, LLC

RFQ Number: SNL-2024-MAT-0892
Contract Vehicle: GSA Schedule 51V required
Security Level: Unclassified
Export Control: EAR99

MATERIAL SPECIFICATION:
- Tungsten Heavy Alloy (90% W minimum)
- Composition: W-7Ni-3Fe typical
- Form: Cylindrical rods
- Diameter: 1.00" ± 0.005"
- Length: 6.00" ± 0.125"
- Quantity: 24 pieces
- Density: 17.0 g/cm³ minimum

APPLICATION: Radiation shielding research (unclassified)
FUNDING: DOE Office of Science Grant DE-SC0024156

MANDATORY REQUIREMENTS:
□ Small Business preference (provide DUNS number)
□ Made in USA (BAA compliant)
□ Material composition certificate
□ Dimensional inspection report
□ GSA contract holder status

EVALUATION CRITERIA:
- Technical compliance (40%)
- Price (35%) 
- Delivery schedule (25%)

Submission deadline: 30 days from RFQ date
Questions due: 15 days before submission deadline
Contact: procurement-mat@sandia.gov

Contracting Officer: Janet Martinez
Phone: 505-555-0198 (official business only)

OFFICIAL USE ONLY - NOT FOR PUBLIC RELEASE""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "research_development",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "016",
        "category": "Racing Team - Performance Critical",
        "customer": "Penske Racing IndyCar Team",
        "subject": "Titanium suspension components - Indy 500 prep",
        "email_body": """RACING TEAM URGENT REQUEST

Team Penske IndyCar - Indy 500 Preparation

We crashed the #12 car during practice and need titanium for suspension rebuilds:

MATERIAL: Ti-6Al-4V Grade 5 Titanium
SPECIFICATIONS:
- Round bar: 1.25" diameter x 12" length (need 4 pieces)
- Round bar: 0.75" diameter x 6" length (need 6 pieces)  
- Sheet: 0.125" thick x 12" x 24" (need 2 sheets)

RACING REQUIREMENTS:
- Aerospace grade material only
- Mill certs required for tech inspection
- No porosity, inclusions, or defects
- Machined surface capability needed

TIMELINE: Indy 500 qualifying is next week!
- Need material by Wednesday 
- Our machine shop runs 24/7 before race

BUDGET: Performance critical, cost no object
DELIVERY: Indianapolis Motor Speedway, Gasoline Alley

This is for Will Power's championship car. Every ounce matters for speed.

Racing Contact:
- Crew Chief: Tim Cindric (317-555-0189)
- Materials: John Force (317-555-0190)
- Emergency cell: 317-555-RACE

GO FAST!
Mike Thompson, Chief Engineer
Team Penske IndyCar
Indianapolis, IN""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "automotive",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock", "custom_solution"]
    },

    {
        "test_id": "017",
        "category": "International Mining - Remote Location",
        "customer": "Barrick Gold Corporation - Nevada Operations",
        "subject": "Wear-resistant steel for mining equipment",
        "email_body": """Barrick Gold - Goldstrike Mine
Remote Nevada Operations

Equipment breakdown at 6,000 feet elevation, 200 miles from nearest city.

MATERIAL NEEDED:
- AR500 Abrasion Resistant Steel Plate
- Thickness: 1" plate
- Size: 8' x 20' sheets (need 3 sheets)
- Hardness: 500 HBW minimum
- Impact toughness: 15 ft-lbs at -40°F

APPLICATION: Ore crusher liner replacement
OPERATING CONDITIONS:
- 24/7 operation processing gold ore
- Ambient temperature: -20°F to 110°F
- Extreme abrasive environment
- 50-ton rock impacts

LOGISTICS CHALLENGE:
- Location: Middle of Nevada desert
- Nearest rail: 200 miles
- Heavy haul truck access only
- Weather window limited (winter storms)

DELIVERY REQUIREMENTS:
- Truck delivery to mine site
- Crane offload capability needed
- Escort vehicle for oversize load
- Delivery coordination with mine security

URGENCY: Crusher down = $150K per day lost production
Timeline: 2 weeks maximum
Budget: Approved for emergency pricing + logistics

Contact: Dave Anderson, Mine Engineer
Sat phone: 775-555-0156 (only reliable communication)
Radio: Channel 19 "Goldstrike Base"

Barrick Gold Corporation
Goldstrike Mine, Nevada""",
        "expected_complexity": "COMPLEX",
        "expected_industry": "general_manufacturing",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock", "custom_solution"]
    },

    {
        "test_id": "018",
        "category": "Food Processing - Sanitary Requirements",
        "customer": "Tyson Foods Processing Plant",
        "subject": "Stainless steel for food grade equipment rebuild",
        "email_body": """Tyson Foods - Columbus, NE Processing Facility

USDA inspection found corrosion in our chicken processing line. Need immediate stainless steel replacement:

FOOD GRADE REQUIREMENTS:
- 316L Stainless Steel (low carbon for weld integrity)
- Surface finish: 2B mill finish minimum
- Sanitary grade (no crevices, smooth welds)
- USDA/FDA compliant material

SPECIFICATIONS:
- Plate: 0.25" thick x 48" x 96" sheets (need 8 sheets)
- Tubing: 4" diameter x 0.065" wall, 20' lengths (need 6 pieces)
- Round bar: 1" diameter x 12' lengths (need 10 pieces)

CRITICAL REQUIREMENTS:
✓ Material certs showing 316L composition
✓ Surface roughness ≤ 32 Ra (for cleanability)
✓ No sulfur inclusions (corrosion risk)
✓ ASTM A240/A269 compliance
✓ Positive Material Identification (PMI) test results

SANITARY CONSIDERATIONS:
- Equipment processes 40,000 chickens/day
- Steam cleaning at 180°F
- Caustic sanitizers (sodium hypochlorite)
- HACCP critical control point

USDA re-inspection scheduled for next Friday. If we don't pass, plant shuts down.

Production impact: $2.8M per day if closed
Timeline: Need material by Wednesday
Delivery: Columbus, NE (loading dock #7)

Contact: Maria Gonzalez, Plant Engineer
Phone: 402-555-0134
USDA Plant #969

Tyson Foods, Inc.
Columbus Processing Facility""",
        "expected_complexity": "MODERATE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": True,
        "expected_strategies": ["exact_match", "expedited_restock"]
    },

    {
        "test_id": "019",
        "category": "Hobbyist Machinist - Personal Project",
        "customer": "Robert 'Bob' Johnson - Home Workshop",
        "subject": "Small quantity steel for model steam engine",
        "email_body": """Hello,

Retired machinist here, building a scale model steam engine in my garage workshop. Need some small pieces of steel:

MATERIALS:
- 12L14 free-machining steel (easy on old lathe)
- Round bar: 1" diameter x 6" length (need 3 pieces)
- Round bar: 0.5" diameter x 12" length (need 2 pieces)
- Flat bar: 0.25" x 2" x 12" length (need 2 pieces)

PROJECT: 1/4 scale model of 1920s steam tractor engine
PURPOSE: Hobby project, maybe local steam show display

CHALLENGES:
- Retired on fixed income (need reasonable price)
- Small quantities (most suppliers have minimums)
- No business account (personal check OK?)
- Home delivery? (no loading dock)

This is for my grandson's school project on historical engines. He's fascinated by how things were made "back in the day."

Been machining 40+ years, built engines for John Deere before retirement. Know what I'm doing, just need materials.

Can pick up if not too far from Cedar Rapids, Iowa.

Thanks for considering small order,
Bob Johnson
Retired Machinist
1247 Oak Street
Cedar Rapids, IA 52404
Home: 319-555-0167
Email: bobjohnson1943@yahoo.com

P.S. - If you have any steel "drops" or cutoffs, that would work too!""",
        "expected_complexity": "SIMPLE",
        "expected_industry": "general_manufacturing",
        "expected_emergency": False,
        "expected_strategies": ["exact_match", "alternative_products", "split_shipment"]
    },

    {
        "test_id": "020",
        "category": "Renewable Energy - Wind Power",
        "customer": "Vestas Wind Systems - Blade Manufacturing",
        "subject": "High-strength steel for wind turbine hub assembly",
        "email_body": """Vestas Wind Systems A/S
Blade Manufacturing Division - Colorado

Wind turbine hub bearing failure at Midwest wind farm. Need replacement steel forgings for emergency repair:

WIND POWER SPECIFICATIONS:
- 42CrMo4 High-Strength Steel (AISI 4140 equivalent)
- Forged ring blanks for bearing races
- Outside diameter: 2.5 meters (8.2 feet)
- Wall thickness: 300mm (12 inches)
- Quantity: 2 pieces

WIND INDUSTRY REQUIREMENTS:
✓ Fatigue life: 20+ years, 10⁹ cycles
✓ Impact toughness: 27J at -40°C (Arctic operation)
✓ Ultrasonic testing (UT) for internal defects
✓ Magnetic particle inspection (MPI)
✓ Heat treatment: Quench + temper to 285-341 HB

OPERATING CONDITIONS:
- 3.6MW wind turbine (V136 model)
- Hub height: 132 meters (435 feet)
- Variable loads: 0-100% rated power
- Temperature range: -40°C to +50°C
- 25-year design life in prairie environment

LOGISTICS:
- Oversize/overweight transport required
- Crane capacity: 200-ton minimum
- Wind farm location: Kansas prairie (remote)
- Installation window: Low wind season (summer)

FINANCIAL IMPACT:
- Turbine revenue loss: $8,000/day
- Wind farm capacity factor impact
- Green energy credit losses
- Utility penalty clauses

Timeline: 6-8 weeks for forging + machining
Budget: €500K approved for emergency repair
Delivery: Kansas wind farm site

Contact: Lars Andersen, Senior Engineer
Phone: +45 97 30 0000 (Denmark)
Local: 970-555-0198 (Colorado office)
Project: VWS-2024-HUB-0156

Vestas Wind Systems A/S
Renewable Energy Solutions""",
        "expected_complexity": "CRITICAL",
        "expected_industry": "general_manufacturing",
        "expected_emergency": True,
        "expected_strategies": ["expedited_restock", "custom_solution"]
    }
]


async def evaluate_customer_email(test_case, framework):
    """Evaluate a single customer email with Phase 2 intelligence"""
    
    print(f"\n{'='*80}")
    print(f"🧪 TEST {test_case['test_id']}: {test_case['category']}")
    print(f"📧 Customer: {test_case['customer']}")
    print(f"📋 Subject: {test_case['subject']}")
    print(f"{'='*80}")
    
    # Analyze with Phase 2 Sales Order Intelligence
    analysis = await framework.analyze_sales_order(
        test_case['email_body'], 
        test_case['customer']
    )
    
    # Generate fulfillment strategies
    strategies = await framework.generate_fulfillment_strategies(analysis)
    
    # Evaluation results
    results = {
        'test_id': test_case['test_id'],
        'category': test_case['category'],
        'customer': test_case['customer'],
        
        # Analysis results
        'complexity_detected': analysis.complexity_assessment.value,
        'industry_detected': analysis.customer_context.industry_sector,
        'customer_tier_detected': analysis.customer_context.customer_tier,
        'flexibility_score': analysis.flexibility_score,
        'emergency_detected': len(analysis.emergency_indicators) > 0,
        'emergency_indicators': analysis.emergency_indicators,
        'confidence_score': analysis.confidence_score,
        
        # Strategy results
        'strategies_generated': len(strategies),
        'top_strategy': strategies[0].strategy_type.value if strategies else 'none',
        'strategy_confidence': strategies[0].confidence_score if strategies else 0.0,
        
        # Expected vs Actual (case-insensitive comparison for complexity)
        'complexity_correct': analysis.complexity_assessment.value.upper() == test_case['expected_complexity'].upper(),
        'industry_correct': analysis.customer_context.industry_sector == test_case['expected_industry'],
        'emergency_correct': (len(analysis.emergency_indicators) > 0) == test_case['expected_emergency'],
        'strategies_appropriate': strategies[0].strategy_type.value in test_case['expected_strategies'] if strategies else False,
        
        # Reasoning quality
        'reasoning_notes_count': len(analysis.reasoning_notes),
        'reasoning_notes': analysis.reasoning_notes
    }
    
    # Print results
    print(f"🧠 ANALYSIS RESULTS:")
    print(f"   Complexity: {results['complexity_detected']} (expected: {test_case['expected_complexity']}) {'✅' if results['complexity_correct'] else '❌'}")
    print(f"   Industry: {results['industry_detected']} (expected: {test_case['expected_industry']}) {'✅' if results['industry_correct'] else '❌'}")
    print(f"   Customer Tier: {results['customer_tier_detected']}")
    print(f"   Flexibility: {results['flexibility_score']:.2f}")
    print(f"   Emergency: {results['emergency_detected']} (expected: {test_case['expected_emergency']}) {'✅' if results['emergency_correct'] else '❌'}")
    if results['emergency_indicators']:
        print(f"   Emergency Indicators: {', '.join(results['emergency_indicators'])}")
    print(f"   Confidence: {results['confidence_score']:.2f}")
    
    print(f"\n🎯 STRATEGY RESULTS:")
    print(f"   Strategies Generated: {results['strategies_generated']}")
    print(f"   Top Strategy: {results['top_strategy']} (expected: {test_case['expected_strategies']}) {'✅' if results['strategies_appropriate'] else '❌'}")
    print(f"   Strategy Confidence: {results['strategy_confidence']:.2f}")
    
    if strategies:
        print(f"   All Strategies: {[s.strategy_type.value for s in strategies]}")
    
    print(f"\n💭 REASONING QUALITY:")
    print(f"   Reasoning Notes: {results['reasoning_notes_count']} insights")
    for i, note in enumerate(results['reasoning_notes'][:3], 1):
        print(f"   {i}. {note}")
    if len(results['reasoning_notes']) > 3:
        print(f"   ... and {len(results['reasoning_notes']) - 3} more insights")
    
    return results


async def run_comprehensive_evaluation():
    """Run comprehensive evaluation of Phase 2 Sales Order Intelligence"""
    
    print("🧠 COMPREHENSIVE METALS INDUSTRY EVALUATION")
    print("Phase 2: Sales Order Intelligence Framework")
    print(f"{'='*80}")
    print(f"📧 Testing {len(CUSTOMER_EMAILS)} diverse customer email scenarios")
    print(f"🏭 Industries: Automotive, Aerospace, Medical, Research, Manufacturing, Defense")
    print(f"👥 Customer Types: Major corps, small shops, startups, government, hobbyists")
    print(f"⚡ Scenarios: Emergency, routine, complex, simple, international, niche")
    print(f"{'='*80}")
    
    # Initialize framework
    framework = SalesOrderReasoningFramework()
    
    # Track evaluation metrics
    all_results = []
    category_performance = {}
    
    # Process each test case
    for i, test_case in enumerate(CUSTOMER_EMAILS, 1):
        print(f"\n🔬 PROCESSING TEST {i}/{len(CUSTOMER_EMAILS)}")
        
        try:
            result = await evaluate_customer_email(test_case, framework)
            all_results.append(result)
            
            # Track category performance
            category = test_case['category'].split(' - ')[0]
            if category not in category_performance:
                category_performance[category] = {'total': 0, 'correct': 0}
            
            category_performance[category]['total'] += 1
            if (result['complexity_correct'] and result['industry_correct'] and 
                result['emergency_correct'] and result['strategies_appropriate']):
                category_performance[category]['correct'] += 1
                
        except Exception as e:
            print(f"❌ TEST {test_case['test_id']} FAILED: {e}")
            continue
    
    # Generate comprehensive results
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE EVALUATION RESULTS")
    print(f"{'='*80}")
    
    # Overall accuracy metrics
    total_tests = len(all_results)
    complexity_accuracy = sum(1 for r in all_results if r['complexity_correct']) / total_tests
    industry_accuracy = sum(1 for r in all_results if r['industry_correct']) / total_tests  
    emergency_accuracy = sum(1 for r in all_results if r['emergency_correct']) / total_tests
    strategy_accuracy = sum(1 for r in all_results if r['strategies_appropriate']) / total_tests
    overall_accuracy = sum(1 for r in all_results if (r['complexity_correct'] and r['industry_correct'] and r['emergency_correct'] and r['strategies_appropriate'])) / total_tests
    
    print(f"🎯 ACCURACY METRICS:")
    print(f"   Complexity Detection: {complexity_accuracy:.1%} ({sum(1 for r in all_results if r['complexity_correct'])}/{total_tests})")
    print(f"   Industry Recognition: {industry_accuracy:.1%} ({sum(1 for r in all_results if r['industry_correct'])}/{total_tests})")
    print(f"   Emergency Detection: {emergency_accuracy:.1%} ({sum(1 for r in all_results if r['emergency_correct'])}/{total_tests})")
    print(f"   Strategy Appropriateness: {strategy_accuracy:.1%} ({sum(1 for r in all_results if r['strategies_appropriate'])}/{total_tests})")
    print(f"   📈 OVERALL ACCURACY: {overall_accuracy:.1%} ({sum(1 for r in all_results if (r['complexity_correct'] and r['industry_correct'] and r['emergency_correct'] and r['strategies_appropriate']))}/{total_tests})")
    
    # Performance by category
    print(f"\n📊 PERFORMANCE BY CATEGORY:")
    for category, perf in sorted(category_performance.items()):
        accuracy = perf['correct'] / perf['total'] if perf['total'] > 0 else 0
        print(f"   {category}: {accuracy:.1%} ({perf['correct']}/{perf['total']})")
    
    # Confidence and reasoning quality
    avg_confidence = sum(r['confidence_score'] for r in all_results) / total_tests
    avg_strategies = sum(r['strategies_generated'] for r in all_results) / total_tests
    avg_reasoning_quality = sum(r['reasoning_notes_count'] for r in all_results) / total_tests
    
    print(f"\n🧠 INTELLIGENCE QUALITY:")
    print(f"   Average Confidence: {avg_confidence:.2f}")
    print(f"   Average Strategies per Order: {avg_strategies:.1f}")
    print(f"   Average Reasoning Insights: {avg_reasoning_quality:.1f}")
    
    # Edge case performance
    edge_cases = [r for r in all_results if any(term in r['category'].lower() for term in ['small', 'startup', 'hobbyist', 'international', 'art', 'unique'])]
    edge_case_accuracy = sum(1 for r in edge_cases if (r['complexity_correct'] and r['industry_correct'] and r['emergency_correct'] and r['strategies_appropriate'])) / len(edge_cases) if edge_cases else 0
    
    print(f"\n🎲 EDGE CASE PERFORMANCE:")
    print(f"   Edge Cases Tested: {len(edge_cases)}")
    print(f"   Edge Case Accuracy: {edge_case_accuracy:.1%}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"evaluation_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'evaluation_summary': {
                'total_tests': total_tests,
                'complexity_accuracy': complexity_accuracy,
                'industry_accuracy': industry_accuracy,
                'emergency_accuracy': emergency_accuracy,
                'strategy_accuracy': strategy_accuracy,
                'overall_accuracy': overall_accuracy,
                'avg_confidence': avg_confidence,
                'avg_strategies': avg_strategies,
                'avg_reasoning_quality': avg_reasoning_quality,
                'edge_case_accuracy': edge_case_accuracy
            },
            'category_performance': category_performance,
            'detailed_results': all_results
        }, f, indent=2)
    
    print(f"\n💾 DETAILED RESULTS SAVED: {results_file}")
    
    # Final assessment
    print(f"\n{'='*80}")
    print("🏆 FINAL ASSESSMENT")
    print(f"{'='*80}")
    
    if overall_accuracy >= 0.9:
        grade = "🥇 EXCELLENT"
    elif overall_accuracy >= 0.8:
        grade = "🥈 VERY GOOD"
    elif overall_accuracy >= 0.7:
        grade = "🥉 GOOD"
    elif overall_accuracy >= 0.6:
        grade = "⚠️ NEEDS IMPROVEMENT"
    else:
        grade = "❌ POOR"
    
    print(f"Phase 2 Sales Order Intelligence: {grade}")
    print(f"Overall Performance: {overall_accuracy:.1%}")
    print(f"Ready for Production: {'✅ YES' if overall_accuracy >= 0.8 else '❌ NEEDS WORK'}")
    
    if overall_accuracy >= 0.8:
        print(f"\n🎉 PHASE 2 SUCCESSFULLY HANDLES DIVERSE METALS INDUSTRY SCENARIOS!")
        print(f"   • Understands customer context across industries")
        print(f"   • Detects emergency situations appropriately") 
        print(f"   • Generates intelligent fulfillment strategies")
        print(f"   • Handles edge cases (small businesses, international, niche applications)")
    
    return overall_accuracy >= 0.8


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_evaluation())
    sys.exit(0 if success else 1)