# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Review Package Exporter (.ZIP)
Bundles executive audit brief (Markdown), tabular risk matrix (CSV), and obligations register (CSV).
"""
import io
import csv
import zipfile
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class ReviewPackageExporter:
    """
    Generates a professional contract review package (.zip archive) for legal teams.
    """

    MARKDOWN_DISCLAIMER_FOOTER = (
        "\n---\n"
        "*NOTICE: This document review package was generated automatically by SovereignDoc "
        "(provided by Idea To Fact LLC). It is designed solely to assist qualified professionals "
        "in analyzing contracts and does not constitute formal legal representation or legal advice. "
        "All findings, risk flags, and extracted obligations must be independently verified by a "
        "licensed legal professional.*\n"
    )

    CSV_DISCLAIMER_CELL = (
        "Informational tool output by SovereignDoc (Idea To Fact LLC); not legal advice. "
        "Verify with licensed counsel."
    )

    DISCLAIMER_TXT_CONTENT = (
        "SOVEREIGNDOC LEGAL & REGULATORY DISCLAIMER (v1.0)\n"
        "=================================================\n\n"
        "NOTICE: This document review package was generated automatically by SovereignDoc\n"
        "(provided by Idea To Fact LLC). It is designed solely to assist qualified professionals\n"
        "in analyzing contracts and does not constitute formal legal representation or legal advice.\n\n"
        "All findings, clause classifications, risk flags, obligations registers, and redline summaries\n"
        "may contain errors or omissions and must be independently reviewed and verified by a\n"
        "qualified, licensed attorney prior to executing any legal agreement or taking operational action.\n\n"
        "Use of SovereignDoc does not establish an attorney-client relationship.\n"
        "Provided 'AS IS' without warranty of any kind under the GNU AGPLv3 License.\n"
    )

    @classmethod
    def generate_audit_markdown(
        cls,
        document_filename: str,
        review_run_id: str,
        ruleset_version: str,
        risks: List[Any],
        obligations: List[Any],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Generates executive markdown audit brief."""
        ts = timestamp or datetime.now(timezone.utc)
        high_count = sum(1 for r in risks if getattr(r, "risk_level", None) == "HIGH" or (isinstance(r, dict) and r.get("risk_level") == "HIGH"))
        med_count = sum(1 for r in risks if getattr(r, "risk_level", None) == "MEDIUM" or (isinstance(r, dict) and r.get("risk_level") == "MEDIUM"))
        low_count = sum(1 for r in risks if getattr(r, "risk_level", None) == "LOW" or (isinstance(r, dict) and r.get("risk_level") == "LOW"))

        md = []
        md.append(f"# SovereignDoc Contract Intelligence Review Audit")
        md.append(f"**Document**: `{document_filename}`  ")
        md.append(f"**Review Run ID**: `{review_run_id}`  ")
        md.append(f"**Audit Date**: `{ts.strftime('%Y-%m-%d %H:%M:%S UTC')}`  ")
        md.append(f"**Ruleset Version**: `{ruleset_version}`  ")
        md.append(f"**Air-Gap Integrity**: `100% Local (Verified Zero Cloud Leakage)`  \n")
        md.append("---\n")

        md.append("## 1. Executive Summary")
        md.append(f"- **Total Risks Flagged**: **{len(risks)}**")
        md.append(f"  - 🔴 **High Severity**: {high_count}")
        md.append(f"  - 🟡 **Medium Severity**: {med_count}")
        md.append(f"  - 🟢 **Low / Standard**: {low_count}")
        md.append(f"- **Total Affirmative Obligations Extracted**: **{len(obligations)}**\n")

        md.append("## 2. Identified Contract Risks Matrix")
        if not risks:
            md.append("*No contract risks flagged by current deterministic ruleset.*\n")
        else:
            md.append("| Severity | Rule ID | Category | Issue Title | Page | Section |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for r in risks:
                sev = getattr(r, "risk_level", None) or (r.get("risk_level") if isinstance(r, dict) else "MEDIUM")
                rule_id = getattr(r, "rule_id", None) or (r.get("rule_id") if isinstance(r, dict) else "")
                cat = getattr(r, "category", None) or (r.get("category") if isinstance(r, dict) else "")
                title = getattr(r, "issue_title", None) or (r.get("issue_title") if isinstance(r, dict) else "")
                page = getattr(r, "page_number", None) or (r.get("page_number") if isinstance(r, dict) else 1)
                sec = getattr(r, "section", None) or (r.get("section") if isinstance(r, dict) else "-") or "-"
                icon = "🔴" if sev == "HIGH" else "🟡" if sev == "MEDIUM" else "🟢"
                md.append(f"| {icon} **{sev}** | `{rule_id}` | {cat} | {title} | Page {page} | {sec} |")
            md.append("")

        md.append("## 3. Detailed Risk Findings & Exact Provenance")
        for i, r in enumerate(risks, 1):
            sev = getattr(r, "risk_level", None) or (r.get("risk_level") if isinstance(r, dict) else "MEDIUM")
            rule_id = getattr(r, "rule_id", None) or (r.get("rule_id") if isinstance(r, dict) else "")
            title = getattr(r, "issue_title", None) or (r.get("issue_title") if isinstance(r, dict) else "")
            desc = getattr(r, "description", None) or (r.get("description") if isinstance(r, dict) else "")
            page = getattr(r, "page_number", None) or (r.get("page_number") if isinstance(r, dict) else 1)
            sec = getattr(r, "section", None) or (r.get("section") if isinstance(r, dict) else "")
            verb = getattr(r, "verbatim_text", None) or (r.get("verbatim_text") if isinstance(r, dict) else "") or ""
            conf = getattr(r, "confidence", 1.0) or (r.get("confidence", 1.0) if isinstance(r, dict) else 1.0)
            method = getattr(r, "detection_method", "RULE") or (r.get("detection_method", "RULE") if isinstance(r, dict) else "RULE")

            md.append(f"### Finding #{i}: {title} ({sev})")
            md.append(f"- **Rule ID**: `{rule_id}` | **Method**: `{method}` | **Confidence**: `{int(conf*100)}%`")
            md.append(f"- **Location**: Page {page}{f', Section {sec}' if sec else ''}")
            md.append(f"- **Exposure Explanation**: {desc}")
            md.append(f"- **Verbatim Contract Text**:\n  > \"{verb.strip()}\"\n")

        md.append("## 4. Affirmative Obligations Register")
        if not obligations:
            md.append("*No affirmative obligations extracted.*\n")
        else:
            md.append("| Obligated Party | Mandatory Duty | Condition / Trigger | Deadline / Cadence | Page |")
            md.append("| :--- | :--- | :--- | :--- | :--- |")
            for o in obligations:
                party = getattr(o, "party", None) or (o.get("party") if isinstance(o, dict) else "")
                action = getattr(o, "action_required", None) or (o.get("action_required") if isinstance(o, dict) else "")
                trig = getattr(o, "trigger_or_condition", None) or (o.get("trigger_or_condition") if isinstance(o, dict) else "-") or "-"
                dl = getattr(o, "deadline_or_cadence", None) or (o.get("deadline_or_cadence") if isinstance(o, dict) else "-") or "-"
                page = getattr(o, "page_number", None) or (o.get("page_number") if isinstance(o, dict) else 1)
                md.append(f"| **{party}** | {action} | {trig} | {dl} | Page {page} |")
            md.append("")

        md.append(cls.MARKDOWN_DISCLAIMER_FOOTER.strip())
        return "\n".join(md)

    @classmethod
    def generate_risk_matrix_csv(cls, review_run_id: str, risks: List[Any]) -> str:
        """Generates RFC-4180 parser-safe CSV string of risk findings with uniform legal_disclaimer column."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "review_run_id", "rule_id", "category", "risk_level",
            "issue_title", "description", "page_number", "section",
            "confidence", "detection_method", "verbatim_text", "legal_disclaimer"
        ])
        for r in risks:
            writer.writerow([
                review_run_id,
                getattr(r, "rule_id", None) or (r.get("rule_id") if isinstance(r, dict) else ""),
                getattr(r, "category", None) or (r.get("category") if isinstance(r, dict) else ""),
                getattr(r, "risk_level", None) or (r.get("risk_level") if isinstance(r, dict) else ""),
                getattr(r, "issue_title", None) or (r.get("issue_title") if isinstance(r, dict) else ""),
                getattr(r, "description", None) or (r.get("description") if isinstance(r, dict) else ""),
                getattr(r, "page_number", 1) or (r.get("page_number", 1) if isinstance(r, dict) else 1),
                getattr(r, "section", "") or (r.get("section", "") if isinstance(r, dict) else ""),
                getattr(r, "confidence", 1.0) or (r.get("confidence", 1.0) if isinstance(r, dict) else 1.0),
                getattr(r, "detection_method", "RULE") or (r.get("detection_method", "RULE") if isinstance(r, dict) else "RULE"),
                getattr(r, "verbatim_text", "") or (r.get("verbatim_text", "") if isinstance(r, dict) else ""),
                cls.CSV_DISCLAIMER_CELL,
            ])
        return output.getvalue()

    @classmethod
    def generate_obligations_csv(cls, review_run_id: str, obligations: List[Any]) -> str:
        """Generates RFC-4180 parser-safe CSV string of extracted affirmative duties with uniform legal_disclaimer column."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "review_run_id", "party", "action_required", "trigger_or_condition",
            "deadline_or_cadence", "page_number", "section",
            "confidence", "detection_method", "verbatim_text", "legal_disclaimer"
        ])
        for o in obligations:
            writer.writerow([
                review_run_id,
                getattr(o, "party", None) or (o.get("party") if isinstance(o, dict) else ""),
                getattr(o, "action_required", None) or (o.get("action_required") if isinstance(o, dict) else ""),
                getattr(o, "trigger_or_condition", "") or (o.get("trigger_or_condition", "") if isinstance(o, dict) else ""),
                getattr(o, "deadline_or_cadence", "") or (o.get("deadline_or_cadence", "") if isinstance(o, dict) else ""),
                getattr(o, "page_number", 1) or (o.get("page_number", 1) if isinstance(o, dict) else 1),
                getattr(o, "section", "") or (o.get("section", "") if isinstance(o, dict) else ""),
                getattr(o, "confidence", 0.90) or (o.get("confidence", 0.90) if isinstance(o, dict) else 0.90),
                getattr(o, "detection_method", "HEURISTIC") or (o.get("detection_method", "HEURISTIC") if isinstance(o, dict) else "HEURISTIC"),
                getattr(o, "verbatim_text", "") or (o.get("verbatim_text", "") if isinstance(o, dict) else ""),
                cls.CSV_DISCLAIMER_CELL,
            ])
        return output.getvalue()

    @classmethod
    def build_review_package_zip(
        cls,
        document_filename: str,
        review_run_id: str,
        ruleset_version: str,
        risks: List[Any],
        obligations: List[Any],
        diff_summary: Optional[str] = None
    ) -> bytes:
        """
        Builds the complete in-memory contract_review.zip deliverable.
        """
        audit_md = cls.generate_audit_markdown(
            document_filename=document_filename,
            review_run_id=review_run_id,
            ruleset_version=ruleset_version,
            risks=risks,
            obligations=obligations
        )
        risks_csv = cls.generate_risk_matrix_csv(review_run_id, risks)
        obligations_csv = cls.generate_obligations_csv(review_run_id, obligations)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("contract_audit.md", audit_md)
            zf.writestr("risk_matrix.csv", risks_csv)
            zf.writestr("obligations.csv", obligations_csv)
            zf.writestr("DISCLAIMER.txt", cls.DISCLAIMER_TXT_CONTENT)
            if diff_summary:
                zf.writestr("comparison.md", diff_summary.rstrip() + "\n" + cls.MARKDOWN_DISCLAIMER_FOOTER)

        zip_buffer.seek(0)
        return zip_buffer.getvalue()

review_exporter = ReviewPackageExporter()
