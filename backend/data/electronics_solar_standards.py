"""Electronics, IT, and Solar Photovoltaic Indian Standards dataset generator."""
from __future__ import annotations

from backend.models.standard_model import (
    CertificationScheme,
    IndianStandard,
    MandatoryQCO,
    StandardStatus,
)


def get_electronics_solar_standards() -> list[IndianStandard]:
    """Return curated IT, electronics, and solar PV standards."""
    return [
        IndianStandard(
            is_code="IS 14286",
            title="Crystalline Silicon Terrestrial Photovoltaic (PV) Modules - Design Qualification and Type Approval",
            division="LITD",
            status=StandardStatus.ACTIVE,
            year=2010,
            reaffirmation_year=2021,
            amendments=["Amendment 1 (2018)", "Amendment 2 (2021)"],
            scope="Design qualification and type approval of terrestrial PV modules for long-term outdoor operation.",
            key_parameters=["Maximum Power (Pmax) Determination", "Temperature Coefficients", "Hail Impact Test", "Damp Heat (1000h at 85C/85%RH)", "PID Resistance"],
            test_methods=["IS/IEC 61215-2 (Terrestrial PV Modules - Test Procedures)", "IS/IEC 60904 (Photovoltaic Devices - Measurement of PV Current-Voltage)"],
            normative_references=["IS/IEC 61730-1", "IS/IEC 61730-2", "IS/IEC 60904"],
            safety_standards=["IS/IEC 61730-1 (PV Module Safety Qualification - Construction)", "IS/IEC 61730-2 (PV Module Safety - Testing)"],
            installation_standards=["IS/IEC 62548 (Photovoltaic (PV) Arrays - Design Requirements)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.CRS, order_number="S.O. 2920(E) Solar Photovoltaics Systems/Devices QCO", issuing_ministry="Ministry of New and Renewable Energy (MNRE)", effective_date="2018-04-16", clause_requirement="Mandatory BIS Registration (CRS Scheme II / ALMM Listing by MNRE)."),
            category_keywords=["solar panel", "pv module", "solar pv", "monocrystalline module", "polycrystalline solar", "rooftop solar", "photovoltaic"],
            gem_categories=["Solar Power Equipment", "Photovoltaic Modules", "Renewable Energy Systems"]
        ),
        IndianStandard(
            is_code="IS 16221 (Part 2)",
            title="Safety of Power Converters for Use in Photovoltaic Power Systems - Particular Requirements for Inverters",
            division="LITD",
            status=StandardStatus.ACTIVE,
            year=2015,
            reaffirmation_year=2022,
            amendments=["Amendment 1 (2019)"],
            scope="Specifies electrical and fire safety requirements for grid-connected and off-grid solar inverters.",
            key_parameters=["Inverter Efficiency >= 98%", "Total Harmonic Distortion (THD) < 3%", "Anti-Islanding Protection Trip Time <= 2s", "IP65 Enclosure Rating"],
            test_methods=["IS 16169 (Test Procedure of Islanding Prevention Measures)", "IS/IEC 60068 (Environmental Testing)"],
            normative_references=["IS 16169", "IS/IEC 60529", "IS 16221 (Part 1)"],
            safety_standards=["IS 16221 (Part 1) (General Safety Requirements for Power Converters)"],
            installation_standards=["IS 732", "IS 3043 (Code of Practice for Earthing)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.CRS, order_number="S.O. 2920(E) Solar Inverters QCO", issuing_ministry="MNRE", effective_date="2018-09-05", clause_requirement="Mandatory BIS CRS registration and MNRE guidelines compliance."),
            category_keywords=["solar inverter", "grid tie inverter", "string inverter", "solar pcu", "power converter", "on grid inverter"],
            gem_categories=["Solar Inverters", "Power Conditioning Units", "Renewable Energy Electronics"]
        ),
        IndianStandard(
            is_code="IS 13252 (Part 1)",
            title="Information Technology Equipment - Safety - Part 1: General Requirements",
            division="LITD",
            status=StandardStatus.ACTIVE,
            year=2010,
            reaffirmation_year=2020,
            amendments=["Amendment 1 (2013)", "Amendment 2 (2015)", "Amendment 3 (2017)", "Amendment 4 (2020)"],
            scope="Safety of mains-powered or battery-powered information technology equipment including laptops, desktops, servers, monitors, printers.",
            key_parameters=["Electric Shock Protection", "Dielectric Strength Voltage Withstand", "Temperature Rise Under Fault", "Flammability of Enclosure V-0/V-1"],
            test_methods=["IS 13252 (Part 1) Clause 5 (Electrical Tests)"],
            normative_references=["IS 616", "IS 16046 (Part 2)"],
            safety_standards=["IS 13252 (Part 1)"],
            installation_standards=["IS 732"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.CRS, order_number="S.O. 2357(E) Electronics and IT Goods (Requirement for Compulsory Registration) Order", issuing_ministry="Ministry of Electronics and Information Technology (MeitY)", effective_date="2013-07-03", clause_requirement="Mandatory BIS CRS Registration Number (R-XXXXXXXX) prominently marked on product and packaging."),
            category_keywords=["laptop", "desktop computer", "server", "computer monitor", "printer", "tablet pc", "it equipment", "workstation"],
            gem_categories=["Computer Hardware", "Laptops and Notebooks", "Enterprise Servers", "Office IT Equipment"]
        ),
        IndianStandard(
            is_code="IS 10322 (Part 5/Sec 3)",
            title="Luminaires - Particular Requirements - Luminaires for Road and Street Lighting",
            division="LITD",
            status=StandardStatus.ACTIVE,
            year=2012,
            reaffirmation_year=2022,
            amendments=["Amendment 1 (2016)", "Amendment 2 (2021)"],
            scope="Safety and constructional requirements for LED street light luminaires, highway lighting, and public space poles.",
            key_parameters=["Luminous Efficacy >= 120 lm/W", "CCT (3000K - 6500K)", "Ingress Protection IP66", "Surge Protection >= 10 kV", "Power Factor >= 0.95"],
            test_methods=["IS 16103 (Part 1 & 2) (LED Modules for General Lighting)", "IS 16107 (Part 2/Sec 1) (Photometric Testing)"],
            normative_references=["IS 15885 (Part 2/Sec 13)", "IS 16103", "IS 16107"],
            safety_standards=["IS 15885 (Part 2/Sec 13) (Safety of Lamp Controlgear - LED Drivers)"],
            installation_standards=["IS 1944 (Code of Practice for Lighting of Public Thoroughfares)"],
            mandatory_qco=MandatoryQCO(is_mandatory=True, scheme=CertificationScheme.CRS, order_number="S.O. 2357(E) Lighting Products CRS Order", issuing_ministry="MeitY / DPIIT", effective_date="2015-09-01", clause_requirement="Mandatory BIS CRS Registration for LED Luminaire and Driver."),
            category_keywords=["led street light", "street light luminaire", "road lighting", "outdoor led", "led floodlight", "pole light"],
            gem_categories=["Street Lighting", "LED Luminaires", "Municipal Lighting Infrastructure"]
        )
    ]
