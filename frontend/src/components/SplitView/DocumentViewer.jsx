// Copyright (C) 2026 Idea To Fact LLC
// SPDX-License-Identifier: AGPL-3.0-only

import React, { useState, useEffect, useRef } from "react";
import * as pdfjsLib from "pdfjs-dist";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker.min.js?url";
import { api } from "../../services/api";
import PDFHighlightCanvas from "./PDFHighlightCanvas";

// Configure local offline worker
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default function DocumentViewer({
  vaultId,
  activeDocument,
  activeCitation,
}) {
  const [numPages, setNumPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [zoomScale, setZoomScale] = useState(1.0);
  const [pdfDoc, setPdfDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [viewport, setViewport] = useState(null);
  const [fileType, setFileType] = useState("pdf");

  // Multi-page HTML / DOCX representation
  const [pagesArray, setPagesArray] = useState([]);
  const [paginationSource, setPaginationSource] = useState("VIRTUAL_LAYOUT");

  // Deterministic render completion signal (replaces flaky setTimeout)
  const [renderedPageKey, setRenderedPageKey] = useState("");
  const [pendingCitation, setPendingCitation] = useState(null);

  const canvasRef = useRef(null);
  const renderTaskRef = useRef(null);
  const htmlContainerRef = useRef(null);

  // 1. Citation Click Listener: Synchronize target page & set pendingCitation
  useEffect(() => {
    if (!activeCitation) return;

    const targetPage = activeCitation.page_number || 1;
    setPendingCitation(activeCitation);

    if (targetPage !== currentPage) {
      setCurrentPage(targetPage);
    }
  }, [activeCitation]);

  // 2. Load document whenever activeDocument changes
  useEffect(() => {
    if (!activeDocument || !vaultId) {
      setPdfDoc(null);
      setPagesArray([]);
      setNumPages(1);
      setCurrentPage(1);
      return;
    }

    let isCancelled = false;

    const loadDoc = async () => {
      setLoading(true);
      setCurrentPage(1);
      setRenderedPageKey("");
      const ext = activeDocument.filename.split(".").pop().toLowerCase();
      setFileType(ext);

      try {
        if (ext === "pdf") {
          setPagesArray([]);
          const url = api.getDocumentFileUrl(vaultId, activeDocument.id);
          const response = await fetch(url);
          const blob = await response.blob();
          const arrayBuffer = await blob.arrayBuffer();

          if (isCancelled) return;
          const loadedPdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
          if (isCancelled) return;

          setPdfDoc(loadedPdf);
          setNumPages(loadedPdf.numPages);
          setPaginationSource("PDF_NATIVE");
        } else {
          // DOCX, TXT, MD, CSV - Load paginated HTML from backend
          setPdfDoc(null);
          const htmlRes = await api.getDocumentHtml(vaultId, activeDocument.id);
          if (isCancelled) return;

          const pages = htmlRes.pages && htmlRes.pages.length > 0
            ? htmlRes.pages
            : [htmlRes.html || "<p>Document content unavailable.</p>"];

          setPagesArray(pages);
          setNumPages(pages.length);
          setPaginationSource(htmlRes.pagination_source || "VIRTUAL_LAYOUT");
        }
      } catch (err) {
        console.error("Error loading document:", err);
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    loadDoc();

    return () => {
      isCancelled = true;
    };
  }, [vaultId, activeDocument]);

  // 3. Signal render completion when PDF page renders on canvas
  useEffect(() => {
    if (!pdfDoc || !canvasRef.current || fileType !== "pdf") return;

    let isMounted = true;

    const renderPdfPage = async () => {
      try {
        if (renderTaskRef.current) {
          renderTaskRef.current.cancel();
        }

        const page = await pdfDoc.getPage(currentPage);
        if (!isMounted) return;

        const vp = page.getViewport({ scale: zoomScale });
        setViewport(vp);

        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");

        canvas.height = vp.height;
        canvas.width = vp.width;

        const renderContext = {
          canvasContext: ctx,
          viewport: vp,
        };

        const task = page.render(renderContext);
        renderTaskRef.current = task;
        await task.promise;

        if (isMounted) {
          // Emit render completion signal for PDF
          setRenderedPageKey(`${activeDocument?.id}_p${currentPage}`);
        }
      } catch (err) {
        if (err.name !== "RenderingCancelledException") {
          console.error("PDF page render error:", err);
        }
      }
    };

    renderPdfPage();

    return () => {
      isMounted = false;
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
      }
    };
  }, [pdfDoc, currentPage, zoomScale, fileType, activeDocument]);

  // 4. Signal render completion when HTML page sheet mounts
  useEffect(() => {
    if (fileType === "pdf" || loading || !pagesArray.length) return;

    // The DOM has mounted the current page HTML
    const key = `${activeDocument?.id}_p${currentPage}`;
    setRenderedPageKey(key);
  }, [fileType, loading, pagesArray, currentPage, activeDocument]);

  // 5. Deterministic Citation Navigation Effect (Triggered on render completion signal)
  useEffect(() => {
    if (!pendingCitation) return;
    if (fileType === "pdf") return; // PDFHighlightCanvas handles PDF bounding boxes
    if (!htmlContainerRef.current) return;

    const targetKey = `${activeDocument?.id}_p${currentPage}`;
    if (renderedPageKey !== targetKey) return; // Wait until current page has finished rendering

    const container = htmlContainerRef.current;
    const targetText = (
      pendingCitation.verbatim_excerpt ||
      pendingCitation.verbatim_text ||
      pendingCitation.evidence_text ||
      pendingCitation.snippet ||
      pendingCitation.surrounding_context ||
      pendingCitation.quote ||
      pendingCitation.action_required ||
      pendingCitation.text ||
      ""
    ).trim();

    const section = pendingCitation.section ? String(pendingCitation.section).trim() : null;

    // Clean previous highlights
    container.querySelectorAll(".citation-highlight-pulse").forEach((el) => {
      el.classList.remove("citation-highlight-pulse");
    });

    const candidates = Array.from(
      container.querySelectorAll("p, h1, h2, h3, h4, li, tr, td, blockquote")
    );
    if (candidates.length === 0) return;

    let bestCandidate = null;

    const cleanTarget = targetText
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    // Step A: Normalized substring match on leading snippet (35 chars) for exact paragraph targeting
    if (cleanTarget.length >= 10) {
      const leadSnippet = cleanTarget.substring(0, 35);
      bestCandidate = candidates.find((el) => {
        const elClean = el.textContent
          .toLowerCase()
          .replace(/[^a-z0-9\s]/g, " ")
          .replace(/\s+/g, " ");
        return elClean.includes(leadSnippet);
      });
    }

    // Step B: Check for exact section number match
    if (!bestCandidate && section) {
      const secLower = section.toLowerCase().replace(/^(?:section|sec\.?|§)\s*/i, "").trim();
      bestCandidate = candidates.find((el) => {
        const text = el.textContent.toLowerCase().trim();
        return (
          text.startsWith(secLower + ".") ||
          text.startsWith(secLower + " ") ||
          text.includes("section " + secLower) ||
          text.includes("sec. " + secLower)
        );
      });
    }

    // Step C: Word-overlap scoring match
    if (!bestCandidate && cleanTarget.length > 0) {
      const words = cleanTarget.split(" ").filter((w) => w.length >= 4);
      if (words.length > 0) {
        let maxScore = 0;
        for (const el of candidates) {
          const elLower = el.textContent.toLowerCase();
          let score = 0;
          for (const w of words) {
            if (elLower.includes(w)) score++;
          }
          if (score > maxScore && score >= 2) {
            maxScore = score;
            bestCandidate = el;
          }
        }
      }
    }

    // Smooth scroll and pulse highlight
    if (bestCandidate) {
      bestCandidate.scrollIntoView({ behavior: "smooth", block: "center" });
      void bestCandidate.offsetWidth; // Force CSS reflow
      bestCandidate.classList.add("citation-highlight-pulse");
    }

    // Successfully navigated
    setPendingCitation(null);
  }, [renderedPageKey, pendingCitation, currentPage, fileType, activeDocument]);

  if (!activeDocument) {
    return (
      <div className="center-pane" style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center", color: "var(--text-muted)", maxWidth: "340px" }}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" style={{ margin: "0 auto 1rem" }}>
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <p style={{ fontSize: "0.95rem", fontWeight: 500, color: "var(--text-secondary)" }}>No Document Selected</p>
          <p style={{ fontSize: "0.8rem", marginTop: "0.4rem" }}>
            Select an indexed file from the left sidebar or upload a new contract to begin reviewing.
          </p>
        </div>
      </div>
    );
  }

  const currentPageHtml = pagesArray[currentPage - 1] || "";

  return (
    <main className="center-pane">
      {/* Viewer Toolbar */}
      <div className="viewer-toolbar">
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
          <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px" }}>
            {activeDocument.filename.endsWith('.pdf') ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(239, 68, 68, 0.15)" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M14 2v6h6" stroke="#EF4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : activeDocument.filename.endsWith('.docx') || activeDocument.filename.endsWith('.doc') ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(59, 130, 246, 0.15)" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M14 2v6h6" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M7.5 12.5l1.5 5 1.5-4 1.5 4 1.5-5" stroke="#60A5FA" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" fill="rgba(6, 182, 212, 0.15)" stroke="#06B6D4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M14 2v6h6" stroke="#06B6D4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
            {activeDocument.filename}
          </span>
          <span
            className="badge"
            style={{
              background: "rgba(255, 255, 255, 0.08)",
              color: "#94A3B8",
              fontSize: "0.68rem",
              textTransform: "uppercase",
            }}
          >
            {fileType}
          </span>

          {/* Pagination Source Indicator Badge */}
          {fileType !== "pdf" && (
            <span
              className={`pagination-source-badge ${
                paginationSource === "SECTION_BREAK"
                  ? "section-break"
                  : paginationSource === "VIRTUAL_LAYOUT"
                  ? "virtual"
                  : ""
              }`}
              title={`Pagination Strategy: ${paginationSource}`}
            >
              {paginationSource === "WORD_PAGE_BREAK" && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                  </svg>
                  Word Breaks
                </span>
              )}
              {paginationSource === "SECTION_BREAK" && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                    <line x1="3" y1="12" x2="21" y2="12" strokeDasharray="3 3"></line>
                  </svg>
                  Section Breaks
                </span>
              )}
              {paginationSource === "VIRTUAL_LAYOUT" && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 6h16M4 12h16M4 18h16"></path>
                  </svg>
                  Virtual Sheet
                </span>
              )}
            </span>
          )}

          {activeCitation && (
            <span
              className="badge"
              style={{
                background: "rgba(16, 185, 129, 0.15)",
                color: "#10B981",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                fontSize: "0.7rem",
              }}
            >
              Grounded: {activeCitation.clause_title || `Page ${activeCitation.page_number || 1}`}
            </span>
          )}
        </div>

        {/* Unified Page & Zoom Navigation */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {/* Page Controls (Active for both PDF and Multi-Page DOCX/HTML) */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
            <button
              className="btn-icon"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              title="Previous Page"
            >
              ‹
            </button>
            <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)", minWidth: "75px", textAlign: "center" }}>
              Page {currentPage} of {numPages}
            </span>
            <button
              className="btn-icon"
              disabled={currentPage >= numPages}
              onClick={() => setCurrentPage((p) => Math.min(p + 1, numPages))}
              title="Next Page"
            >
              ›
            </button>
          </div>

          {/* Zoom Controls */}
          <div style={{ display: "flex", alignItems: "center", gap: "0.2rem" }}>
            <button
              className="btn-icon"
              onClick={() => setZoomScale((s) => Math.max(s - 0.15, 0.6))}
              title="Zoom Out"
            >
              -
            </button>
            <span style={{ fontSize: "0.74rem", minWidth: "36px", textAlign: "center", color: "var(--text-muted)" }}>
              {Math.round(zoomScale * 100)}%
            </span>
            <button
              className="btn-icon"
              onClick={() => setZoomScale((s) => Math.min(s + 0.15, 2.0))}
              title="Zoom In"
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Canvas / Document View Container */}
      <div className="viewer-canvas-container">
        {loading ? (
          <div style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "2rem", display: "flex", alignItems: "center", gap: "8px" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "spin 1s linear infinite" }}>
              <circle cx="12" cy="12" r="10" strokeDasharray="32" strokeDashoffset="12"></circle>
            </svg>
            Rendering {fileType.toUpperCase()} document (Page {currentPage} of {numPages})...
          </div>
        ) : fileType === "pdf" && pdfDoc ? (
          <div className="pdf-page-wrapper">
            <canvas ref={canvasRef} />
            <PDFHighlightCanvas
              activeCitation={activeCitation}
              pageNumber={currentPage}
              viewport={viewport}
            />
          </div>
        ) : pagesArray.length > 0 ? (
          <div
            className="docx-page-sheet-container"
            style={{
              transform: `scale(${zoomScale})`,
              transformOrigin: "top center",
              transition: "transform 0.1s ease",
            }}
          >
            <div
              ref={htmlContainerRef}
              className="docx-page-sheet"
              data-page={currentPage}
              dangerouslySetInnerHTML={{ __html: currentPageHtml }}
            />
            <div className="docx-page-footer">
              <span>{activeDocument.filename}</span>
              <span>Page {currentPage} of {numPages}</span>
            </div>
          </div>
        ) : (
          <div
            style={{
              background: "var(--bg-surface)",
              padding: "2rem",
              borderRadius: "var(--radius-md)",
              maxWidth: "850px",
              width: "100%",
              whiteSpace: "pre-wrap",
              fontFamily: "var(--font-mono)",
              fontSize: "0.84rem",
              lineHeight: 1.6,
              color: "var(--text-primary)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            No renderable content found for this document.
          </div>
        )}
      </div>
    </main>
  );
}
