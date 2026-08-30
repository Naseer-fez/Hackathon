"""Electrotechnical Indian Standards dataset generator."""
from __future__ import annotations

from backend.models.standard_model import (
    CertificationScheme,
    IndianStandard,
    MandatoryQCO,
    StandardStatus,
)


def get_electrical_standards() -> list[IndianStandard]:
    """Return curated electrotechnical standards."""
    return [
        IndianStandard(
            is_code="IS 1180 (Part 1)",
            title="Outdoor Type Three-Phase Distribution Transformers Up to and Including 2500 kVA, 33 kV",
            division="ETD",
            status=StandardStatus.ACTIVE,
            year=2014,
            reaffirmation_year=2021,
            amendments=["Amendment 1 (2016)", "Amendment 2 (2018)", "Amendment 3 (2021)", "Amendment 4 (2023)"],
            scope="Specifies standard ratings, maximum allowable losses (Energy Efficiency Level 1/2/3), and tests for distribution transformers.",
            key_parameters=["No-load Loss & Load Loss at 50% / 100% load", "Temperature Rise Limit (Winding 55 deg C, Oil 50 deg C)", "Insulation Level (LI 170 kV, AC 70 kV for 33kV)", "Short Circuit Withstand Capability"],
            test_methods=["IS 2026 (Power Transformers - General & Temperature Rise Tests)", "IS 335 (New Insulating Oils - Specification & Breakdown Voltage)", "IS 6600 (Guide for Loading of Oil Immersed Transformers)"],
            normative_references=["IS 2026", "IS 335", "IS 10028", "IS 3639", "IS 2099"],
            safety_standards=["IS 1646 (Code of Practice for Fire Safety of Buildings - Electrical Installations)"],
            installation_standards=["IS 10028 (Part 1, 2, 3) (Code of Practice for Selection, Installation and Maintenance of Transformers)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 1130(E) Distribution Transformers QCO", issuing_ministry="Ministry of Power / DPIIT", effective_date="2014-05-07", clause_requirement="Mandatory BIS ISI Mark and BEE Star Rating Label (BEE Gazette S.O. 3338E)."),
            category_keywords=["distribution transformer", "power transformer", "oil immersed transformer", "step down transformer", "11kv transformer", "33kv transformer", "2500 kva"],
            gem_categories=["Power Distribution", "Electrical Transformers", "Substation Equipment"]
        ),
        IndianStandard(
            is_code="IS 694",
            title="PVC Insulated Cables for Working Voltages Up to and Including 1100 V - Specification",
            division="ETD",
            status=StandardStatus.ACTIVE,
            year=2010,
            reaffirmation_year=2022,
            amendments=["Amendment 1 (2014)", "Amendment 2 (2017)", "Amendment 3 (2020)"],
            scope="Single-core and multi-core PVC insulated and sheathed flexible and non-flexible copper/aluminium wires for electric power and lighting.",
            key_parameters=["Conductor Resistance at 20 deg C", "Insulation Resistance Constant", "Flame Retardant (FR / FRLS) Oxygen Index >= 29%", "High Voltage Spark Test"],
            test_methods=["IS 10810 (Methods of Test for Cables - Part 0 to 64)", "IS 8130 (Conductors for Insulated Electric Cables)", "IS 5831 (PVC Insulation and Sheath of Electric Cables)"],
            normative_references=["IS 8130", "IS 5831", "IS 10810", "IS 4905"],
            safety_standards=["IS 732 (Code of Practice for Electrical Wiring Installations)"],
            installation_standards=["IS 732 (Electrical Wiring Installation)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 4330(E) Electrical Wires and Cables QCO", issuing_ministry="DPIIT, Ministry of Commerce and Industry", effective_date="2023-06-01", clause_requirement="Mandatory ISI Mark. Uncertified cables prohibited from government tenders."),
            category_keywords=["pvc wire", "copper wire", "building wire", "frls cable", "flexible cable", "single core wire", "1100v cable", "electrical cable"],
            gem_categories=["Wires and Cables", "Electrical Wiring", "Building Electrical Infrastructure"]
        ),
        IndianStandard(
            is_code="IS 1293",
            title="Plugs and Socket-Outlets of Related Voltages Up to and Including 250 Volts and Rated Current Up to and Including 16 Amperes - Specification",
            division="ETD",
            status=StandardStatus.ACTIVE,
            year=2019,
            reaffirmation_year=2024,
            amendments=["Amendment 1 (2020)", "Amendment 2 (2022)"],
            scope="Specifies safety, dimensional, and endurance requirements for domestic and commercial 6A / 16A plugs and socket outlets.",
            key_parameters=["Contact Resistance", "Temperature Rise <= 45 K", "Shutter Interlocking Mechanism", "Insulation Resistance >= 5 MOhm", "Glow Wire Test at 750 deg C"],
            test_methods=["IS 1293 Clause 13 to Clause 28 (Endurance and Safety Tests)"],
            normative_references=["IS 302 (Part 1)", "IS 9857"],
            safety_standards=["IS 302 (Part 1) (Safety of Household Electrical Appliances)"],
            installation_standards=["IS 732 (Code of Practice for Electrical Wiring Installations)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.ISI_MARK, order_number="S.O. 4381(E) Plugs and Socket Outlets QCO", issuing_ministry="DPIIT", effective_date="2020-12-01", clause_requirement="Mandatory ISI Mark certification under BIS Scheme I."),
            category_keywords=["plug", "socket", "power plug", "switch socket", "6a socket", "16a plug", "wall outlet"],
            gem_categories=["Electrical Accessories", "Wiring Devices", "Switches and Sockets"]
        ),
        IndianStandard(
            is_code="IS 1293:2005",
            title="Plugs and Socket-Outlets (Outdated / Superseded 2005 Edition)",
            division="ETD",
            status=StandardStatus.SUPERSEDED,
            superseded_by="IS 1293:2019",
            year=2005,
            reaffirmation_year=None,
            amendments=[],
            scope="Outdated 2005 edition of Plugs and Sockets standard without revised safety shutters.",
            key_parameters=["Obsolete pin dimensions and non-shuttered requirements"],
            test_methods=["IS 1293:2005"],
            normative_references=[],
            safety_standards=[],
            installation_standards=[],
            mandatory_qco=MandatoryQCO(is_mandatory=False, scheme=CertificationScheme.NONE, clause_requirement="SUPERSEDED: Must be updated to IS 1293:2019 in all active tenders."),
            category_keywords=["is 1293 2005", "old socket standard"],
            gem_categories=[]
        )
    ]
