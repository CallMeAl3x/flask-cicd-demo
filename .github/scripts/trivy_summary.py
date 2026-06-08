#!/usr/bin/env python3
"""Render a Trivy JSON report as a Markdown summary.

Usage:
    trivy_summary.py <report.json> [--gate]

Without ``--gate`` it prints a Markdown summary (used by the report job, piped
into ``$GITHUB_STEP_SUMMARY``) and always exits 0.

With ``--gate`` it prints the same summary and exits 1 if any vulnerability is
found, so the Trivy job fails the pipeline.
"""
import json
import os
import sys

SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def load_vulnerabilities(path):
    with open(path) as fh:
        data = json.load(fh)
    return [
        vuln
        for result in (data.get("Results") or [])
        for vuln in (result.get("Vulnerabilities") or [])
    ]


def render(vulns):
    lines = ["## 🐳 Trivy — scan de l'image Docker (dépendances pip + OS)", ""]
    if not vulns:
        lines.append("✅ Aucune vulnérabilité CRITICAL/HIGH (corrigeable) détectée.")
        return lines

    crit = sum(1 for v in vulns if v.get("Severity") == "CRITICAL")
    high = sum(1 for v in vulns if v.get("Severity") == "HIGH")
    lines.append(
        f"**{len(vulns)} vulnérabilité(s)** — 🔴 {crit} CRITICAL · 🟠 {high} HIGH"
    )
    lines.append("")
    lines.append("| Package | Version | Sévérité | CVE | Corrigé dans | Détail |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for v in sorted(vulns, key=lambda x: SEVERITY_RANK.get(x.get("Severity"), 9)):
        title = (v.get("Title") or "").replace("|", "\\|")[:70]
        fixed = v.get("FixedVersion") or "—"
        lines.append(
            f"| `{v.get('PkgName', '')}` | {v.get('InstalledVersion', '')} "
            f"| **{v.get('Severity', '')}** | {v.get('VulnerabilityID', '')} "
            f"| {fixed} | {title} |"
        )
    return lines


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    gate = "--gate" in argv
    path = args[0] if args else "trivy-report.json"

    if not os.path.exists(path):
        print("ℹ️ Pas de rapport Trivy trouvé — étape ignorée.")
        return 0

    vulns = load_vulnerabilities(path)
    print("\n".join(render(vulns)))
    print()

    if gate and vulns:
        print(f"::error::Trivy a trouvé {len(vulns)} vulnérabilité(s) CRITICAL/HIGH.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
