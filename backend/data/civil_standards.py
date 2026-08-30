"""Civil engineering Indian Standards dataset generator."""
from __future__ import annotations

from backend.models.standard_model import (
    CertificationScheme,
    IndianStandard,
    MandatoryQCO,
    StandardStatus,
)


def get_civil_standards() -> list[IndianStandard]:
    """Return curated civil engineering standards."""
    return [
        IndianStandard(
            is_code="IS 456",
            title="Plain and Reinforced Concrete - Code of Practice",
            division="CED",
            status=StandardStatus.ACTIVE,
            year=2000,
            reaffirmation_year=2021,
            amendments=["Amendment 1 (2001)", "Amendment 2 (2005)", "Amendment 3 (2007)", "Amendment 4 (2013)", "Amendment 5 (2019)"],
            scope="General structural use of plain and reinforced concrete in buildings and civil structures.",
            key_parameters=["Compressive Strength", "Water-Cement Ratio", "Cover to Reinforcement", "Durability Requirements"],
            test_methods=["IS 516 (Methods of Tests for Strength of Concrete)", "IS 1199 (Sampling and Analysis of Concrete)"],
            normative_references=["IS 383", "IS 1786", "IS 8112", "IS 12269", "IS 2386"],
            safety_standards=["IS 14489 (Code of Practice on Occupational Safety and Health Audit)"],
            installation_standards=["IS 456 (Execution and Quality Assurance Clause 10)"],
            mandatory_qco=MandatoryQCO(is_mandatory=False, scheme=CertificationScheme.NONE, clause_requirement="Standard practice compliance required for government tenders."),
            category_keywords=["concrete", "rcc", "civil construction", "structural design", "portland cement concrete", "foundation"],
            gem_categories=["Construction Materials", "Civil Engineering Services", "Structural Concrete Works"]
        ),
        IndianStandard(
            is_code="IS 1786",
            title="High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
            division="CED",
            status=StandardStatus.ACTIVE,
            year=2008,
            reaffirmation_year=2023,
            amendments=["Amendment 1 (2012)", "Amendment 2 (2017)", "Amendment 3 (2020)"],
            scope="Specifies requirements for deformed steel bars (TMT rebars Fe 415, Fe 500, Fe 550, Fe 600, Fe 500D) for reinforcement.",
            key_parameters=["0.2% Proof Stress", "Tensile Strength (TS/YS Ratio)", "Elongation %", "Bend and Rebend Test", "Carbon Equivalent (CE)"],
            test_methods=["IS 1608 (Part 1) (Tensile Testing of Metallic Materials)", "IS 1599 (Metallic Materials - Bend Test)", "IS 228 (Chemical Analysis of Steels)"],
            normative_references=["IS 228", "IS 1599", "IS 1608", "IS 8910"],
            safety_standards=["IS 14489 (Safety Audit Code)"],
            installation_standards=["IS 2502 (Code of Practice for Bending and Fixing of Bars for Concrete Reinforcement)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 1225(E) Steel and Steel Products QCO", issuing_ministry="Ministry of Steel", effective_date="2020-04-01", clause_requirement="Mandatory ISI Mark under Scheme I. Bidders must produce valid CML license copy."),
            category_keywords=["tmt bar", "steel rebar", "reinforcement steel", "fe 500d", "fe 550", "deformed steel", "saria", "reinforcing bar"],
            gem_categories=["Steel Reinforcement", "TMT Rebars", "Civil Construction Steel"]
        ),
        IndianStandard(
            is_code="IS 12269",
            title="Ordinary Portland Cement, 53 Grade - Specification",
            division="CED",
            status=StandardStatus.ACTIVE,
            year=2013,
            reaffirmation_year=2020,
            amendments=["Amendment 1 (2016)", "Amendment 2 (2019)"],
            scope="Specifies chemical and physical requirements for 53 grade Ordinary Portland Cement.",
            key_parameters=["28-Day Compressive Strength >= 53 MPa", "Initial Setting Time >= 30 min", "Fineness (Specific Surface) >= 225 m2/kg", "Soundness (Le-Chatelier) <= 10 mm"],
            test_methods=["IS 4031 (Methods of Physical Tests for Hydraulic Cement)", "IS 4032 (Method of Chemical Analysis of Hydraulic Cement)"],
            normative_references=["IS 4031", "IS 4032", "IS 650"],
            safety_standards=["IS 14489"],
            installation_standards=["IS 456"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 2480(E) Cement Quality Control Order", issuing_ministry="DPIIT, Ministry of Commerce and Industry", effective_date="2003-02-17", clause_requirement="Mandatory BIS ISI certification. Manufacturer must hold valid BIS license."),
            category_keywords=["opc 53", "53 grade cement", "cement", "ordinary portland cement", "high strength cement"],
            gem_categories=["Cement", "Hydraulic Cement", "Building Construction Materials"]
        ),
        IndianStandard(
            is_code="IS 4984",
            title="High Density Polyethylene (HDPE) Pipes for Water Supply - Specification",
            division="CED",
            status=StandardStatus.ACTIVE,
            year=2016,
            reaffirmation_year=2021,
            amendments=["Amendment 1 (2018)", "Amendment 2 (2021)"],
            scope="Specifies requirements for HDPE pipes (PE 63, PE 80, PE 100) for underground water supply networks.",
            key_parameters=["Melt Flow Rate (MFR)", "Hydrostatic Strength at 80 deg C", "Oxidation Induction Time (OIT)", "Carbon Black Content & Dispersion"],
            test_methods=["IS 12235 (Methods of Test for Unplasticized PVC / Polyethylene Pipes)", "IS 2530 (Methods of Test for Polyethylene)"],
            normative_references=["IS 2530", "IS 7328", "IS 12235"],
            safety_standards=["IS 10500 (Drinking Water Quality Specification)"],
            installation_standards=["IS 7634 (Part 2) (Code of Practice for Laying and Jointing of Polyethylene Pipes)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 384(E) HDPE/PVC Pipes QCO", issuing_ministry="DPIIT, Ministry of Commerce and Industry", effective_date="2023-09-01", clause_requirement="Pipes must bear ISI mark with manufacturer CML number."),
            category_keywords=["hdpe pipe", "pe 100 pipe", "water supply pipe", "polyethylene pipe", "potable water piping"],
            gem_categories=["Pipes and Fittings", "Water Distribution Infrastructure", "Plumbing Supplies"]
        ),
        IndianStandard(
            is_code="IS 1786:1985",
            title="High Strength Deformed Steel Bars (Outdated / Superseded)",
            division="CED",
            status=StandardStatus.SUPERSEDED,
            superseded_by="IS 1786:2008 (Reaffirmed 2023)",
            year=1985,
            reaffirmation_year=None,
            amendments=[],
            scope="Superseded older edition of TMT steel bar specification.",
            key_parameters=["Obsolete Yield Stress Classes"],
            test_methods=["IS 1608"],
            normative_references=["IS 228"],
            safety_standards=[],
            installation_standards=[],
            mandatory_qco=MandatoryQCO(is_mandatory=False, scheme=CertificationScheme.NONE, clause_requirement="OUTDATED: Do not use in new tenders."),
            category_keywords=["is 1786 1985", "old tmt standard"],
            gem_categories=[]
        )
    ]
