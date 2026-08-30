"""Mechanical, PPE, Safety, and Quality Indian Standards dataset generator."""
from __future__ import annotations

from backend.models.standard_model import (
    CertificationScheme,
    IndianStandard,
    MandatoryQCO,
    StandardStatus,
)


def get_mech_safety_standards() -> list[IndianStandard]:
    """Return curated mechanical and safety/PPE standards."""
    return [
        IndianStandard(
            is_code="IS 15683",
            title="Portable Fire Extinguishers - Performance and Construction - Specification",
            division="MED",
            status=StandardStatus.ACTIVE,
            year=2018,
            reaffirmation_year=2023,
            amendments=["Amendment 1 (2020)", "Amendment 2 (2022)"],
            scope="Specifies construction, minimum fire rating (Class A, B, C, D, F), burst pressure, and safety discharge of portable fire extinguishers.",
            key_parameters=["Working Pressure & Proof Test Pressure", "Minimum Effective Discharge Time", "Operating Temperature Range (-30C to +60C)", "Fire Rating Classification (e.g. 4A, 34B)"],
            test_methods=["IS 15683 Annexure A to G (Fire Test Protocols)", "IS 4308 (Specification for Dry Chemical Powder for Fire Fighting)"],
            normative_references=["IS 4308", "IS 4862", "IS 11108", "IS 2190"],
            safety_standards=["IS 2190 (Selection, Installation and Maintenance of Portable First-Aid Fire Extinguishers - Code of Practice)"],
            installation_standards=["IS 2190 (Code of Practice for Fire Extinguisher Installation)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 4589(E) Fire Safety Products QCO", issuing_ministry="DPIIT, Ministry of Commerce and Industry", effective_date="2023-01-01", clause_requirement="Mandatory ISI Mark certification under BIS Scheme I."),
            category_keywords=["fire extinguisher", "co2 extinguisher", "abc dry powder extinguisher", "portable fire fighting", "fire safety equipment", "foam extinguisher"],
            gem_categories=["Fire Fighting Equipment", "Portable Fire Extinguishers", "Emergency and Safety Supplies"]
        ),
        IndianStandard(
            is_code="IS 9473",
            title="Respiratory Protective Devices - Filtering Half Masks to Protect Against Particles - Specification",
            division="TXD",
            status=StandardStatus.ACTIVE,
            year=2002,
            reaffirmation_year=2022,
            amendments=["Amendment 1 (2020)"],
            scope="Specifies minimum requirements for particle filtering half masks (FFP1, FFP2 / N95 equivalent, FFP3) used as respiratory protective devices.",
            key_parameters=["Bacterial Filtration Efficiency (BFE) >= 95%", "Particle Filtration Efficiency (PFE) >= 95% at 95 L/min", "Breathing Resistance (Inhalation <= 2.4 mbar, Exhalation <= 3.0 mbar)", "Total Inward Leakage <= 8%"],
            test_methods=["IS 9473 Clause 8 (Sodium Chloride & Paraffin Oil Aerosol Test)", "IS 9473 Clause 9 (Breathing Resistance Test)"],
            normative_references=["IS 9473", "IS 14489"],
            safety_standards=["IS 9623 (Code of Practice for Selection, Use and Maintenance of Respiratory Protective Devices)"],
            installation_standards=["IS 9623"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 544(E) Personal Protective Equipment (Masks) QCO", issuing_ministry="Ministry of Textiles / DPIIT", effective_date="2021-03-15", clause_requirement="Mandatory BIS ISI Mark certification on every packaging box and mask."),
            category_keywords=["n95 mask", "particulate respirator", "filtering half mask", "ffp2 mask", "surgical mask", "ppe mask", "respiratory protection"],
            gem_categories=["Personal Protective Equipment", "Medical Masks and Respirators", "Safety Gear"]
        ),
        IndianStandard(
            is_code="IS 2925",
            title="Specification for Industrial Safety Helmets",
            division="MED",
            status=StandardStatus.ACTIVE,
            year=1984,
            reaffirmation_year=2021,
            amendments=["Amendment 1 (1990)", "Amendment 2 (2000)", "Amendment 3 (2018)"],
            scope="Specifies physical, shock absorption, penetration resistance, flammability, and electrical resistance for industrial safety helmets.",
            key_parameters=["Shock Absorption (Transmitted Force <= 5.0 kN)", "Penetration Resistance (No contact with headform)", "Flammability Test", "Electrical Resistance (Withstand 2.2 kV)"],
            test_methods=["IS 2925 Appendix A to G (Mechanical & Electrical Test Methods)"],
            normative_references=["IS 2925", "IS 14489"],
            safety_standards=["IS 14489 (Occupational Safety Audit)"],
            installation_standards=["IS 13415 (Code of Practice for Selection and Care of Industrial Safety Helmets)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 3120(E) Safety Helmets QCO", issuing_ministry="DPIIT", effective_date="2021-12-01", clause_requirement="Mandatory ISI Mark certification. Helmets without valid CML license rejected."),
            category_keywords=["safety helmet", "industrial helmet", "hard hat", "construction helmet", "head protection", "safety hardhat"],
            gem_categories=["Personal Protective Equipment", "Head Protection", "Industrial Safety Equipment"]
        )
    ]
