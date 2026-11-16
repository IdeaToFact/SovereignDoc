# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""
Permissive PDF Parser Adapter using pypdfium2 (PDFium / Chrome engine).
Licensed under Apache-2.0 / BSD-3-Clause, suitable for both Community and Commercial Pro/Enterprise editions.

Converts standard PDF bottom-left coordinates into web top-left coordinates [x0, y0, x1, y1]
and clusters text lines into paragraph blocks matching the SovereignDoc canvas highlight engine.
"""
from pathlib import Path
from typing import Any, Dict, List
import pypdfium2 as pdfium

from .base import BasePDFParser


class PDFiumParser(BasePDFParser):
    """Clean-room, permissive PDF parser implementation powered by pypdfium2."""

    def __init__(self, line_merge_factor: float = 1.4, min_gap_pt: float = 10.0):
        self.line_merge_factor = line_merge_factor
        self.min_gap_pt = min_gap_pt

    def extract_page_blocks(self, file_path: Path) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        doc = pdfium.PdfDocument(str(file_path))

        for page_idx, page in enumerate(doc, start=1):
            page_blocks = self._extract_blocks_from_page(page, page_idx)
            blocks.extend(page_blocks)

        doc.close()
        return blocks

    def _extract_blocks_from_page(self, page: pdfium.PdfPage, page_number: int) -> List[Dict[str, Any]]:
        textpage = page.get_textpage()
        page_height = page.get_height()
        n_rects = textpage.count_rects()
        if n_rects == 0:
            return []

        raw_rects = []
        for i in range(n_rects):
            r = textpage.get_rect(i)  # (left, bottom, right, top) in PDF coordinates
            txt = textpage.get_text_bounded(*r).strip()
            if not txt:
                continue

            # Invert coordinates: PDF (0,0) is bottom-left -> Web (0,0) is top-left
            x0 = round(r[0], 2)
            y0 = round(page_height - r[3], 2)
            x1 = round(r[2], 2)
            y1 = round(page_height - r[1], 2)
            box = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
            raw_rects.append({"bbox": box, "text": txt})

        if not raw_rects:
            return []

        # Sort raw rects roughly top-to-bottom, left-to-right
        raw_rects.sort(key=lambda r: (r["bbox"][1], r["bbox"][0]))

        # Stage 1: Group horizontal text fragments belonging to the same line
        lines: List[Dict[str, Any]] = []
        for r in raw_rects:
            r_mid = (r["bbox"][1] + r["bbox"][3]) / 2.0
            r_h = r["bbox"][3] - r["bbox"][1]
            assigned = False
            for line in lines:
                l_mid = (line["bbox"][1] + line["bbox"][3]) / 2.0
                l_h = line["bbox"][3] - line["bbox"][1]
                # Merge into existing line if vertical midpoints align within tolerance
                if abs(r_mid - l_mid) <= max(3.0, min(r_h, l_h) * 0.45):
                    line["rects"].append(r)
                    line["bbox"][0] = min(line["bbox"][0], r["bbox"][0])
                    line["bbox"][1] = min(line["bbox"][1], r["bbox"][1])
                    line["bbox"][2] = max(line["bbox"][2], r["bbox"][2])
                    line["bbox"][3] = max(line["bbox"][3], r["bbox"][3])
                    assigned = True
                    break
            if not assigned:
                lines.append({"bbox": list(r["bbox"]), "rects": [r]})

        # Sort fragments within each line left-to-right and assemble line text
        for line in lines:
            line["rects"].sort(key=lambda r: r["bbox"][0])
            line["text"] = " ".join(r["text"] for r in line["rects"])

        # Sort lines strictly top-to-bottom
        lines.sort(key=lambda l: l["bbox"][1])

        # Stage 2: Merge consecutive lines into cohesive visual paragraph blocks
        page_blocks: List[Dict[str, Any]] = []
        curr_lines = [lines[0]]

        for next_line in lines[1:]:
            prev_line = curr_lines[-1]
            prev_box = prev_line["bbox"]
            next_box = next_line["bbox"]

            line_height = prev_box[3] - prev_box[1]
            v_gap = next_box[1] - prev_box[3]

            # Paragraph lines have small vertical gaps (inter-line pitch <= 0.75 * line_height or <= 5.5pt)
            # Separate paragraphs have an explicit gap (typically >= 8pt)
            max_line_gap = max(5.5, line_height * 0.75)
            if v_gap <= max_line_gap:
                curr_lines.append(next_line)
            else:
                page_blocks.append(self._finalize_block(curr_lines, page_number))
                curr_lines = [next_line]

        if curr_lines:
            page_blocks.append(self._finalize_block(curr_lines, page_number))

        return page_blocks

    @staticmethod
    def _finalize_block(lines: List[Dict[str, Any]], page_number: int) -> Dict[str, Any]:
        text = "\n".join(l["text"] for l in lines)
        bbox = [
            round(min(l["bbox"][0] for l in lines), 2),
            round(min(l["bbox"][1] for l in lines), 2),
            round(max(l["bbox"][2] for l in lines), 2),
            round(max(l["bbox"][3] for l in lines), 2),
        ]
        return {
            "page_number": page_number,
            "bbox": bbox,
            "text": text
        }

