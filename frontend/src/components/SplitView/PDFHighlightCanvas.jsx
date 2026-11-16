// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useEffect, useRef } from "react";

export default function PDFHighlightCanvas({
  activeCitation,
  pageNumber,
  viewport,
}) {
  const boxRef = useRef(null);

  useEffect(() => {
    if (activeCitation && activeCitation.page_number === pageNumber && boxRef.current) {
      boxRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [activeCitation, pageNumber]);

  if (!activeCitation || activeCitation.page_number !== pageNumber || !activeCitation.bbox || !viewport) {
    return null;
  }

  const [x0, y0, x1, y1] = activeCitation.bbox;

  // PyMuPDF coordinates: [x0, y0, x1, y1] with (0,0) at top-left
  // PDF.js viewport.scale provides the exact scaling from PDF points to CSS canvas pixels
  const scale = viewport.scale || 1.0;
  const left = x0 * scale;
  const top = y0 * scale;
  const width = Math.max((x1 - x0) * scale, 20);
  const height = Math.max((y1 - y0) * scale, 14);

  return (
    <div className="bbox-highlight-layer">
      <div
        ref={boxRef}
        className="highlight-box"
        style={{
          left: `${left}px`,
          top: `${top}px`,
          width: `${width}px`,
          height: `${height}px`,
        }}
        title={`Grounded Citation: ${activeCitation.clause_title || "Clause"}`}
      />
    </div>
  );
}