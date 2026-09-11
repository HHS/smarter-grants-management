import logging

from sqlalchemy import select

from src.adapters import db
from src.db.models.assistance_listing_models import AssistanceListing
from tests.db.models import factories

logger = logging.getLogger(__name__)

# These assistance listings are based on real data, but are
# not the complete list. Just a decent sized set for local development.
ASSISTANCE_LISTINGS = [
    {
        "assistance_listing_number": "10.241",
        "program_title": "Institute of Rural Partnerships (GP 778)",
    },
    {
        "assistance_listing_number": "10.250",
        "program_title": "Agricultural and Rural Economic Research, Cooperative Agreements and Collaborations",
    },
    {"assistance_listing_number": "10.274", "program_title": "Regional Rural Development Centers"},
    {"assistance_listing_number": "10.351", "program_title": "Rural Business Development Grant"},
    {"assistance_listing_number": "10.411", "program_title": "Rural Housing Site Loans"},
    {"assistance_listing_number": "10.415", "program_title": "Rural Rental Housing Loans"},
    {
        "assistance_listing_number": "10.420",
        "program_title": "Rural Self-Help Housing Technical Assistance",
    },
    {"assistance_listing_number": "10.427", "program_title": "Rural Rental Assistance Payments"},
    {"assistance_listing_number": "10.433", "program_title": "Rural Housing Preservation Grants"},
    {
        "assistance_listing_number": "10.446",
        "program_title": "Rural Community Development Initiative",
    },
    {
        "assistance_listing_number": "10.447",
        "program_title": "Rural Multi-Family Housing Revitalization Demonstration Program (MPR)",
    },
    {
        "assistance_listing_number": "10.448",
        "program_title": "Rural Development Multi-Family Housing Rural Housing Voucher Program",
    },
    {
        "assistance_listing_number": "10.516",
        "program_title": "Rural Health and Safety Education Competitive Grants Program",
    },
    {"assistance_listing_number": "10.751", "program_title": "Rural Energy Savings Program (RESP)"},
    {"assistance_listing_number": "10.752", "program_title": "Rural eConnectivity Pilot Program"},
    {"assistance_listing_number": "10.755", "program_title": "Rural Innovation Stronger Economy"},
    {"assistance_listing_number": "10.758", "program_title": "Affordable Rural Cooperative"},
    {
        "assistance_listing_number": "10.760",
        "program_title": "Water and Waste Disposal Systems for Rural Communities",
    },
    {
        "assistance_listing_number": "10.771",
        "program_title": "Rural Cooperative Development Grants",
    },
    {
        "assistance_listing_number": "10.782",
        "program_title": "Appropriate Technology Transfer for Rural Areas",
    },
    {
        "assistance_listing_number": "10.850",
        "program_title": "Rural Electrification Loans and Loan Guarantees",
    },
    {"assistance_listing_number": "10.851", "program_title": "Rural Telecommunications Loans"},
    {
        "assistance_listing_number": "10.854",
        "program_title": "Rural Economic Development Loans and Grants",
    },
    {"assistance_listing_number": "10.860", "program_title": "Rural Business Investment Program"},
    {
        "assistance_listing_number": "10.862",
        "program_title": "Rural Decentralized Water Systems Grant Program",
    },
    {"assistance_listing_number": "10.868", "program_title": "Rural Energy for America Program"},
    {
        "assistance_listing_number": "10.870",
        "program_title": "Rural Microentrepreneur Assistance Program",
    },
    {"assistance_listing_number": "10.886", "program_title": "Rural Broadband Access Loans"},
    {
        "assistance_listing_number": "10.890",
        "program_title": "Rural Development Cooperative Agreement Program",
    },
    {
        "assistance_listing_number": "10.996",
        "program_title": "Rural Development Policy Public Service and Leadership Development Program",
    },
    {
        "assistance_listing_number": "11.63A",
        "program_title": "Applied Biological and Chemical Sciences",
    },
    {
        "assistance_listing_number": "12.360",
        "program_title": "Research on Chemical and Biological Defense",
    },
    {
        "assistance_listing_number": "14.250",
        "program_title": "Rural Housing and Economic Development",
    },
    {
        "assistance_listing_number": "14.265",
        "program_title": "Rural Capacity Building for Community Development and Affordable Housing Grants",
    },
    {
        "assistance_listing_number": "15.076",
        "program_title": "Musselshell-Judith Rural Water System",
    },
    {
        "assistance_listing_number": "15.234",
        "program_title": "Secure Rural Schools and Community Self-Determination",
    },
    {
        "assistance_listing_number": "15.516",
        "program_title": "Fort Peck Reservation Rural Water System ",
    },
    {"assistance_listing_number": "15.520", "program_title": "Lewis and Clark Rural Water System "},
    {"assistance_listing_number": "15.605", "program_title": "Sport Fish Restoration "},
    {
        "assistance_listing_number": "15.608",
        "program_title": "Fish and Aquatic Conservation - Aquatic Invasive Species",
    },
    {
        "assistance_listing_number": "15.611",
        "program_title": "Wildlife Restoration and Basic Hunter Education and Safety",
    },
    {
        "assistance_listing_number": "15.614",
        "program_title": "Coastal Wetlands Planning, Protection and Restoration ",
    },
    {
        "assistance_listing_number": "15.615",
        "program_title": "Cooperative Endangered Species Conservation Fund",
    },
    {"assistance_listing_number": "15.616", "program_title": "Clean Vessel Act "},
    {
        "assistance_listing_number": "15.619",
        "program_title": "Rhinoceros and Tiger Conservation Fund",
    },
    {"assistance_listing_number": "15.620", "program_title": "African Elephant Conservation Fund"},
    {"assistance_listing_number": "15.621", "program_title": "Asian Elephant Conservation Fund"},
    {"assistance_listing_number": "15.622", "program_title": "Sportfishing and Boating Safety Act"},
    {
        "assistance_listing_number": "15.623",
        "program_title": "North American Wetlands Conservation Fund",
    },
    {
        "assistance_listing_number": "15.626",
        "program_title": "Enhanced Hunter Education and Safety ",
    },
    {"assistance_listing_number": "15.628", "program_title": "Multistate Conservation Grant "},
    {
        "assistance_listing_number": "15.629",
        "program_title": "Gorilla, Chimpanzee and Bonobo Conservation Fund",
    },
    {"assistance_listing_number": "15.630", "program_title": "Coastal"},
    {"assistance_listing_number": "15.631", "program_title": "Partners for Fish and Wildlife"},
    {
        "assistance_listing_number": "15.553",
        "program_title": "Eastern New Mexico Rural Water System ",
    },
    {
        "assistance_listing_number": "15.558",
        "program_title": "White Mountain Apache Tribe Rural Water System ",
    },
    {
        "assistance_listing_number": "19.334",
        "program_title": "Office of the Biological Policy Staff",
    },
    {
        "assistance_listing_number": "20.509",
        "program_title": "Formula Grants for Rural Areas and Tribal Transit Program",
    },
    {
        "assistance_listing_number": "20.532",
        "program_title": "Passenger Ferry Grant Program, Electric or Low-Emitting Ferry Pilot Program, and Ferry Service for Rural Communities Program",
    },
    {"assistance_listing_number": "20.539", "program_title": "Ferry Service for Rural Communities"},
    {
        "assistance_listing_number": "20.938",
        "program_title": "Rural Surface Transportation Grant Program",
    },
    {
        "assistance_listing_number": "20.943",
        "program_title": "Rural and Tribal Assistance Pilot Program",
    },
    {
        "assistance_listing_number": "20.944",
        "program_title": "Autonomous Vehicle Research in Rural Communities Program",
    },
    {"assistance_listing_number": "47.074", "program_title": "Biological Sciences"},
    {"assistance_listing_number": "84.358", "program_title": "Rural Education"},
    {"assistance_listing_number": "93.396", "program_title": "Cancer Biology Research"},
    {"assistance_listing_number": "93.155", "program_title": "Rural Health Research Centers"},
    {
        "assistance_listing_number": "93.223",
        "program_title": "Development and Coordination of Rural Health Services",
    },
    {
        "assistance_listing_number": "93.241",
        "program_title": "State Rural Hospital Flexibility Program",
    },
    {
        "assistance_listing_number": "93.301",
        "program_title": "Small Rural Hospital Improvement Grant Program",
    },
    {
        "assistance_listing_number": "93.319",
        "program_title": "Outreach Programs to Reduce the Prevalence of Obesity in High Risk Rural Areas",
    },
    {
        "assistance_listing_number": "93.619",
        "program_title": "Rural Health Limited Geographic  Areas: Delta, Appalachian Region, and Northern Border Region",
    },
    {
        "assistance_listing_number": "93.690",
        "program_title": "Rural Communities Opioid Response Programs",
    },
    {
        "assistance_listing_number": "93.692",
        "program_title": "Rural Health Delivery Information Systems",
    },
    {"assistance_listing_number": "93.746", "program_title": "Rural Residency Development Program"},
    {"assistance_listing_number": "93.798", "program_title": "Rural Health Transformation Program"},
    {"assistance_listing_number": "93.811", "program_title": "Rural Hospital Information Systems"},
    {"assistance_listing_number": "93.912", "program_title": "Rural Healthcare Services Programs"},
    {
        "assistance_listing_number": "93.913",
        "program_title": "Grants to States for Operation of State Offices of Rural Health",
    },
    {
        "assistance_listing_number": "93.8CC",
        "program_title": "National Institutes of Health (NIH), Chemical Preparedness Research and Medical Countermeasure Development",
    },
    {
        "assistance_listing_number": "97.040",
        "program_title": "Chemical Stockpile Emergency Preparedness Program",
    },
]


def create_assistance_listings(db_session: db.Session) -> None:
    existing_assistance_listings = db_session.execute(select(AssistanceListing)).scalars().all()
    existing_alns = set([al.assistance_listing_number for al in existing_assistance_listings])

    for assistance_listing in ASSISTANCE_LISTINGS:
        if assistance_listing["assistance_listing_number"] in existing_alns:
            continue

        logger.info(
            f"Creating assistance listing {assistance_listing['assistance_listing_number']} - {assistance_listing['program_title']}"
        )
        factories.AssistanceListingFactory.create(**assistance_listing)
