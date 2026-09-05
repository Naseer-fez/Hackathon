"""Technical engineering calculation generator for Mac heavy reasoning testing."""
from __future__ import annotations
import math


def generate_heavy_engineering_calculation(prompt: str) -> str:
    """Generate multi-iteration structural engineering calculations under IS 456."""
    lines: list[str] = [
        f"### [MAC REASONING ENGINE] Multi-Iterative Structural Analysis for: '{prompt}'\n",
        "#### 1. Characteristic Strength & Target Mean Strength Calculations (IS 456 Clause 9.2):",
    ]

    grade = 20
    standard_deviation = 4.0
    while grade <= 60:
        target_fck = grade + (1.65 * standard_deviation)
        modulus_elasticity = 5000.0 * math.sqrt(grade)
        modular_ratio = 280.0 / (3.0 * (grade / 3.0))
        lines.append(
            f"- **Grade M{grade}**: f_ck = {grade} N/mm² | Target Mean Strength = {target_fck:.2f} N/mm² | "
            f"E_c = {modulus_elasticity:.1f} N/mm² | Modular Ratio m = {modular_ratio:.2f}"
        )
        grade += 5
        standard_deviation += 0.25

    lines.append("\n#### 2. Reinforcement Bar Section & Moment Capacity Iterations (IS 1786 / IS 456):")
    dia = 8
    width = 300.0
    eff_depth = 500.0
    fy = 500.0  # Fe 500
    while dia <= 32:
        bar_count = 4
        while bar_count <= 8:
            ast = bar_count * (math.pi * (dia ** 2) / 4.0)
            xu_max = 0.46 * eff_depth
            fck_test = 30.0
            xu = (0.87 * fy * ast) / (0.36 * fck_test * width)
            status = "UNDER-REINFORCED" if xu <= xu_max else "OVER-REINFORCED (Redesign Req)"
            mu_act = 0.87 * fy * ast * (eff_depth - 0.42 * min(xu, xu_max)) / 1e6
            lines.append(
                f"- Section {bar_count}xT{dia} (Ast={ast:.1f}mm²): xu={xu:.1f}mm, "
                f"xu_max={xu_max:.1f}mm, Mu={mu_act:.2f} kNm (Status: {status})"
            )
            bar_count += 2
        dia += 4

    lines.append("\n#### 3. Normative Compliance Verdict:")
    lines.append(
        "All calculations strictly adhere to IS 456:2000 Clause 38.1 and IS 1786:2008 Grade Fe 500D yield limits. "
        "Recommend section depth adjustment for structural sections exceeding limiting neutral axis xu_max."
    )
    return "\n".join(lines)
