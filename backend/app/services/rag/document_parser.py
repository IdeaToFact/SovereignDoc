# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

import csv
import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from app.services.rag.pdf import get_pdf_parser
import docx
from docx.oxml import OxmlElement


class DocumentParser:
    """Parses multi-format documents (PDF, DOCX, TXT, MD, CSV) into structured text blocks

    with layout metadata, clause hierarchy, and canvas coordinates.
    """

    PAGE_BREAK_DELIMITER = "[[SOVEREIGN_PAGE_BREAK]]"

    ARTICLE_REGEX = re.compile(
        r"^\s*((?:ARTICLE|EXHIBIT|SCHEDULE|ATTACHMENT|APPENDIX|ANNEX)\s+[A-Z0-9IVXLCDM]+)(?:[\s:.\-—]+([^\n]{1,80}))?",
        re.IGNORECASE | re.MULTILINE
    )

    # Matches clause headers anchored at the start of a line/paragraph:
    # 1. Explicit keyword: "Section 10", "Sec. 14.2(b):", "§ 9.1 - Title"
    # 2. Numbered clause with delimiter: "10. Transition Services.", "9. Notice of Immunity...", "10(a). Title"
    # 3. Dotted decimal clause: "10.1 Transition Services", "10.1.2 Sub-clause"
    SECTION_REGEX = re.compile(
        r"^\s*(?:"
        r"(?i:Section|Sec\.|§)\s*(\d+(?:\.\d+)*)(?:\s*(\([a-zA-Z0-9]+\)))?(?:\s*[:.\-—]\s*([^\n]*)|\s+([\"'“(]?[A-Z][^\n]*)|\s*$)"
        r"|"
        r"(\d{1,3}(?:\.\d{1,3})*)(?:\s*(\([a-zA-Z0-9]+\)))?(?:(?:\.\s+|\s*:\s+|\)\s+)|(?<=\))\s+)([\"'“(]?[A-Z][^\n]*)"
        r"|"
        r"(\d{1,3}(?:\.\d{1,3})+)(?:\s*(\([a-zA-Z0-9]+\)))?\s+([\"'“(]?[A-Z][^\n]*)"
        r")",
        re.MULTILINE
    )

    SUBSECTION_START_REGEX = re.compile(
        r"^\s*(\([a-zA-Z0-9]{1,4}\))\s+([\"'“(]?[A-Z][^\n]*)"
    )

    @classmethod
    def _extract_short_title(cls, rest: str, max_len: int = 65) -> Optional[str]:
        """Extract a short clause heading before the first sentence period or colon if present."""
        if not rest:
            return None
        first_line = rest.splitlines()[0].strip()
        # Split on first period or colon followed by space or end-of-line
        parts = re.split(r"[.:](?:\s+|$)", first_line, maxsplit=1)
        candidate = parts[0].strip()
        if 2 <= len(candidate) <= max_len:
            return candidate
        return None

    @classmethod
    def _parse_clause_header(
        cls,
        text: str,
        current_article: Optional[str],
        current_section: Optional[str],
        current_subsection: Optional[str],
        current_heading: str,
        current_page: int,
        heading_page: int,
        is_docx_heading: bool = False,
        bold_prefix: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], str, int, str]:
        """Unified clause & section header detector across document formats.

        Returns:
            (current_article, current_section, current_subsection, current_heading, heading_page, block_section_title)
        """
        matched_header = False
        block_title = None

        # 1. Check Article / Exhibit / Schedule header at line start
        art_m = cls.ARTICLE_REGEX.search(text)
        if art_m:
            current_article = art_m.group(1).upper().strip()
            art_rest = (art_m.group(2) or "").strip()
            current_heading = f"{current_article}: {art_rest}" if art_rest else current_article
            current_heading = current_heading[:75].strip()
            current_section = None
            current_subsection = None
            heading_page = current_page
            matched_header = True
            block_title = current_heading

        # 2. Check Section / Numbered Clause header at line start
        sec_m = cls.SECTION_REGEX.search(text)
        if sec_m:
            if sec_m.group(1) is not None:
                # Branch 1: Explicit "Section / Sec. / §" keyword
                sec_num = sec_m.group(1).strip()
                sub_num = sec_m.group(2).strip() if sec_m.group(2) else None
                rest = (sec_m.group(3) or sec_m.group(4) or "").strip()
                has_keyword = True
            elif sec_m.group(5) is not None:
                # Branch 2: "10. Transition Services." or "9. Notice of Immunity..."
                sec_num = sec_m.group(5).strip()
                sub_num = sec_m.group(6).strip() if sec_m.group(6) else None
                rest = (sec_m.group(7) or "").strip()
                has_keyword = False
            else:
                # Branch 3: "10.1 Transition Services"
                sec_num = sec_m.group(8).strip()
                sub_num = sec_m.group(9).strip() if sec_m.group(9) else None
                rest = (sec_m.group(10) or "").strip()
                has_keyword = False

            current_section = sec_num
            current_subsection = sub_num
            heading_page = current_page
            matched_header = True

            short_title = cls._extract_short_title(rest)
            prefix = f"Section {sec_num}{sub_num or ''}" if has_keyword else f"{sec_num}{sub_num or ''}."
            if short_title:
                sep = ": " if has_keyword else " "
                current_heading = f"{prefix}{sep}{short_title}"
                block_title = current_heading
            else:
                current_heading = f"Section {sec_num}{sub_num or ''}"
                first_line = text.splitlines()[0].strip()
                block_title = first_line[:65].strip() if first_line else current_heading

        # 3. Check parenthesized sub-clause at paragraph start: "(a) ...", "(c) Carve-Outs."
        if not matched_header:
            sub_m = cls.SUBSECTION_START_REGEX.match(text)
            if sub_m:
                sub_num = sub_m.group(1).strip()
                rest = (sub_m.group(2) or "").strip()
                current_subsection = sub_num
                short_title = cls._extract_short_title(rest, max_len=55)
                if short_title:
                    if current_section:
                        block_title = f"Section {current_section}{sub_num}: {short_title}"
                    else:
                        block_title = f"{sub_num} {short_title}"
                else:
                    first_line = text.splitlines()[0].strip()
                    block_title = first_line[:60].strip()
                matched_header = True

        # 4. Check Word Heading style or bold leading clause title in DOCX
        if not matched_header and (is_docx_heading or bold_prefix):
            candidate = (bold_prefix or text.splitlines()[0]).strip().rstrip(".:")
            if 3 <= len(candidate) <= 70:
                current_heading = candidate
                heading_page = current_page
                block_title = current_heading
                matched_header = True

        # 5. Determine block_title for regular continuation paragraphs
        if not block_title:
            if current_page != heading_page:
                # Avoid stamping a previous page's clause title as if that header lived on this page
                first_line = text.splitlines()[0].strip()
                block_title = first_line[:60].strip() if first_line else current_heading
            else:
                block_title = current_heading

        return (
            current_article,
            current_section,
            current_subsection,
            current_heading,
            heading_page,
            block_title
        )

    @classmethod
    def parse_file(cls, file_path: Path) -> List[Dict[str, Any]]:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            return cls._parse_pdf(file_path)
        elif ext == ".docx":
            return cls._parse_docx(file_path)
        elif ext in [".txt", ".md"]:
            return cls._parse_text(file_path)
        elif ext == ".csv":
            return cls._parse_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @classmethod
    def _parse_pdf(cls, file_path: Path) -> List[Dict[str, Any]]:
        blocks = []
        pdf_parser = get_pdf_parser()
        extracted_blocks = pdf_parser.extract_page_blocks(file_path)

        current_article = None
        current_section = None
        current_subsection = None
        current_heading = "General"
        heading_page = 1

        for b in extracted_blocks:
            raw_text = b["text"].strip()
            if not raw_text:
                continue

            page_idx = b["page_number"]
            bbox = b["bbox"]

            (
                current_article,
                current_section,
                current_subsection,
                current_heading,
                heading_page,
                block_title
            ) = cls._parse_clause_header(
                text=raw_text,
                current_article=current_article,
                current_section=current_section,
                current_subsection=current_subsection,
                current_heading=current_heading,
                current_page=page_idx,
                heading_page=heading_page
            )

            section_title = block_title if block_title and block_title != "General" else (
                f"Page {page_idx}" + (f" - {current_article}" if current_article else "")
            )

            blocks.append({
                "page_number": page_idx,
                "article": current_article,
                "section": current_section,
                "subsection": current_subsection,
                "bbox": bbox,
                "section_title": section_title,
                "text": raw_text
            })

        return blocks

    @classmethod
    def _inspect_element_breaks(cls, child: Any, pag_source: str) -> Tuple[bool, bool]:
        """Return (break_before, break_after) for a DOCX body child element.

        - break_before: page break appears before any text in `child` (or in an empty element).
        - break_after: page break appears after text has already started in `child`
          (e.g. a paragraph starting at the bottom of Page N that wraps onto Page N+1,
          or a trailing page/section break at the end of the paragraph).
        """
        if pag_source == "WORD_PAGE_BREAK":
            nodes = child.xpath('.//w:t | .//w:lastRenderedPageBreak | .//w:br[@w:type="page"]')
            chars_before = 0
            break_before = False
            break_after = False
            for node in nodes:
                n_tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
                if n_tag == "t":
                    if node.text:
                        chars_before += len(node.text.strip())
                else:
                    if chars_before <= 15:
                        break_before = True
                    else:
                        break_after = True
            return break_before, break_after
        elif pag_source == "SECTION_BREAK":
            has_sect = bool(child.xpath('.//w:sectPr'))
            if not has_sect:
                return False, False
            has_text = any(t.text and t.text.strip() for t in child.xpath('.//w:t'))
            return (not has_text), has_text
        return False, False

    @classmethod
    def paginate_docx(cls, file_path: Path, include_html: bool = False) -> Dict[str, Any]:
        """Unified DOCX pagination engine shared by both RAG ingestion and the HTML Document Viewer.

        Guarantees that SQLite chunk page_number values and viewer HTML page sheets
        originate from the exact same page-sliced blocks (zero pagination drift).
        """
        doc = docx.Document(str(file_path))
        body = doc._element.body
        blocks: List[Dict[str, Any]] = []

        # Determine pagination source: Word page breaks > Section breaks > Virtual layout
        has_word_page_breaks = bool(body.xpath('.//w:lastRenderedPageBreak | .//w:br[@w:type="page"]'))
        sect_prs = body.xpath('.//w:sectPr')
        has_section_breaks = len(sect_prs) > 1

        if has_word_page_breaks:
            pag_source = "WORD_PAGE_BREAK"
        elif has_section_breaks:
            pag_source = "SECTION_BREAK"
        else:
            pag_source = "VIRTUAL_LAYOUT"

        current_page = 1
        has_content_on_page = False
        current_heading = "General"
        heading_page = 1
        current_article = None
        current_section = None
        current_subsection = None
        inserted_delimiters: List[Tuple[int, Any]] = []

        def _make_delimiter_p() -> Any:
            p_elem = OxmlElement("w:p")
            r_elem = OxmlElement("w:r")
            t_elem = OxmlElement("w:t")
            t_elem.text = cls.PAGE_BREAK_DELIMITER
            r_elem.append(t_elem)
            p_elem.append(r_elem)
            return p_elem

        for child in list(body):
            break_before, break_after = cls._inspect_element_breaks(child, pag_source)

            # 1. Break before element text starts (only if previous page had substantive content)
            if break_before and has_content_on_page:
                current_page += 1
                has_content_on_page = False
                if include_html:
                    p_elem = _make_delimiter_p()
                    child.addprevious(p_elem)
                    inserted_delimiters.append((current_page, p_elem))

            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "p":
                text_elements = child.xpath('.//w:t')
                text = "".join(t.text for t in text_elements if t.text).strip()
                if text:
                    has_content_on_page = True

                    # Check for Word Heading style or leading bold clause title
                    p_styles = child.xpath('.//w:pPr/w:pStyle/@w:val')
                    is_docx_heading = any(
                        s.lower().startswith(("heading", "title")) for s in p_styles
                    ) if p_styles else False

                    bold_prefix = None
                    runs = child.xpath('./w:r')
                    if runs:
                        bold_parts = []
                        for r in runs:
                            is_bold = bool(r.xpath('./w:rPr/w:b[not(@w:val="0") and not(@w:val="false")]'))
                            r_text = "".join(t.text for t in r.xpath('./w:t') if t.text)
                            if is_bold and r_text:
                                bold_parts.append(r_text)
                            elif r_text.strip():
                                break
                        joined_bold = "".join(bold_parts).strip()
                        if joined_bold and joined_bold.endswith((".", ":")) and 3 <= len(joined_bold) <= 70:
                            bold_prefix = joined_bold

                    (
                        current_article,
                        current_section,
                        current_subsection,
                        current_heading,
                        heading_page,
                        block_title
                    ) = cls._parse_clause_header(
                        text=text,
                        current_article=current_article,
                        current_section=current_section,
                        current_subsection=current_subsection,
                        current_heading=current_heading,
                        current_page=current_page,
                        heading_page=heading_page,
                        is_docx_heading=is_docx_heading,
                        bold_prefix=bold_prefix
                    )

                    blocks.append({
                        "page_number": current_page,
                        "article": current_article,
                        "section": current_section,
                        "subsection": current_subsection,
                        "bbox": None,
                        "section_title": block_title,
                        "text": text
                    })

            elif tag == "tbl":
                rows_text = []
                for row in child.xpath('.//w:tr'):
                    cells = []
                    for cell in row.xpath('.//w:tc'):
                        c_text = "".join(t.text for t in cell.xpath('.//w:t') if t.text).strip()
                        cells.append(c_text)
                    if any(cells):
                        rows_text.append(" | ".join(cells))
                if rows_text:
                    has_content_on_page = True
                    blocks.append({
                        "page_number": current_page,
                        "article": current_article,
                        "section": current_section,
                        "subsection": current_subsection,
                        "bbox": None,
                        "section_title": current_heading or "Table",
                        "text": "\n".join(rows_text)
                    })

            # 2. Break mid-paragraph or at end of element (after element starts on current_page)
            if break_after and has_content_on_page:
                current_page += 1
                has_content_on_page = False
                if include_html:
                    p_elem = _make_delimiter_p()
                    child.addnext(p_elem)
                    inserted_delimiters.append((current_page, p_elem))

        if not blocks:
            blocks = [{
                "page_number": 1,
                "article": None,
                "section": None,
                "subsection": None,
                "bbox": None,
                "section_title": file_path.name,
                "text": ""
            }]

        max_block_page = max(b.get("page_number", 1) for b in blocks)

        # Remove any trailing delimiter inserted after the final content block
        if include_html and inserted_delimiters:
            for delim_page, delim_elem in inserted_delimiters:
                if delim_page > max_block_page:
                    parent = delim_elem.getparent()
                    if parent is not None:
                        parent.remove(delim_elem)

        result_payload: Dict[str, Any] = {
            "blocks": blocks,
            "page_count": max_block_page,
            "pagination_source": pag_source,
            "file_type": "docx",
            "filename": file_path.name
        }

        if include_html:
            try:
                import mammoth
                bio = io.BytesIO()
                doc.save(bio)
                bio.seek(0)
                conv = mammoth.convert_to_html(bio)
                raw_html = conv.value
                pages = raw_html.split(f"<p>{cls.PAGE_BREAK_DELIMITER}</p>")
                if not pages or (len(pages) == 1 and not pages[0].strip()):
                    pages = [raw_html]
                result_payload["html"] = raw_html.replace(
                    f"<p>{cls.PAGE_BREAK_DELIMITER}</p>",
                    "<hr class='docx-page-break'/>"
                )
                result_payload["pages"] = pages
                result_payload["page_count"] = len(pages)
            except Exception:
                paras = []
                for b in blocks:
                    if b["text"].strip():
                        paras.append(f"<p>{b['text']}</p>")
                full_html = "".join(paras)
                result_payload["html"] = full_html
                result_payload["pages"] = [full_html]
                result_payload["page_count"] = 1
                result_payload["pagination_source"] = "VIRTUAL_LAYOUT"

        return result_payload

    @classmethod
    def _parse_docx(cls, file_path: Path) -> List[Dict[str, Any]]:
        return cls.paginate_docx(file_path, include_html=False)["blocks"]

    @classmethod
    def _parse_text(cls, file_path: Path) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()

        lines = content.splitlines()
        blocks = []
        current_title = file_path.name
        current_lines = []

        for line in lines:
            if line.startswith("#"):
                if current_lines:
                    blocks.append({
                        "page_number": 1,
                        "article": None,
                        "section": None,
                        "subsection": None,
                        "bbox": None,
                        "section_title": current_title,
                        "text": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                current_title = line.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            blocks.append({
                "page_number": 1,
                "article": None,
                "section": None,
                "subsection": None,
                "bbox": None,
                "section_title": current_title,
                "text": "\n".join(current_lines).strip()
            })
        return blocks if blocks else [{"page_number": 1, "article": None, "section": None, "subsection": None, "bbox": None, "section_title": file_path.name, "text": content}]

    @classmethod
    def _parse_csv(cls, file_path: Path) -> List[Dict[str, Any]]:
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return []
            for row in reader:
                if any(cell.strip() for cell in row):
                    rows.append(row)

        total_rows = len(rows)

        if total_rows < 500:
            formatted_rows = []
            for idx, row in enumerate(rows, start=1):
                row_str = ", ".join([f"{h}: {v}" for h, v in zip(headers, row) if v.strip()])
                formatted_rows.append(f"Row {idx}: {row_str}")
            return [{
                "page_number": 1,
                "article": None,
                "section": "Data Table",
                "subsection": None,
                "bbox": None,
                "section_title": f"{file_path.name} (Rows 1-{total_rows})",
                "text": "\n".join(formatted_rows)
            }]

        summary_lines = [
            f"Dataset Summary for {file_path.name}:",
            f"Total Rows: {total_rows}, Total Columns: {len(headers)}",
            f"Columns: {', '.join(headers)}",
            "\nSample Representative Data (First 15 Rows):"
        ]
        for idx in range(min(15, total_rows)):
            row = rows[idx]
            row_str = ", ".join([f"{h}: {v}" for h, v in zip(headers, row) if v.strip()])
            summary_lines.append(f"Row {idx+1}: {row_str}")

        return [{
            "page_number": 1,
            "article": None,
            "section": "Schema Summary",
            "subsection": None,
            "bbox": None,
            "section_title": f"{file_path.name} (Schema & Sample)",
            "text": "\n".join(summary_lines)
        }]


document_parser = DocumentParser()
