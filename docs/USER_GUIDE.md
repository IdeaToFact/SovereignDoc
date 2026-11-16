# SovereignDoc Local Legal Intelligence Workstation — Complete End-User Guide

Welcome to **SovereignDoc (`v1.1.0-community`)** by **Idea To Fact LLC**! This guide is written for attorneys, paralegals, procurement officers, and contract analysts. It provides practical, step-by-step instructions for analyzing commercial contracts, investigating legal risks, tracking obligations, and exploring relationship graphs—**100% locally on your workstation with zero cloud exposure at runtime** (initial installation requires standard internet access to pull containers and models unless deploying pre-packaged offline bundles).

---

## 1. Installation & First-Run Setup

### 1.1 Quick Start with Docker Desktop (Recommended)

1. **Install & Start Docker Desktop**:
   - **Windows**: Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/). Ensure WSL 2 backend is selected during installation (run `wsl --install` in PowerShell if WSL 2 is not yet installed). Launch Docker Desktop from the Start menu and verify the whale icon in the taskbar indicates the engine is running.
   - **macOS**: Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) (select Apple Silicon or Intel installer). Launch Docker Desktop from Applications.
   - **Linux**: Install Docker Engine and the Docker Compose v2 plugin (e.g. `sudo apt-get install docker-ce docker-compose-plugin`). Ensure the service is running (`sudo systemctl start docker`) and your user is in the `docker` group (`sudo usermod -aG docker $USER`).
   - **Verify Docker CLI**: Run `docker compose version` in your terminal to confirm Docker Compose v2 is available.

2. **Install Ollama on Your Host OS**:
   - Download and install Ollama from [ollama.com](https://ollama.com).
   - Configure Ollama host networking so Docker containers can communicate with it:
     - **Windows (Docker Desktop)**: Test with Ollama bound to `127.0.0.1` first. If your container engine requires binding to all interfaces, set in PowerShell:
       ```powershell
       [System.Environment]::SetEnvironmentVariable('OLLAMA_HOST', '0.0.0.0:11434', [System.EnvironmentVariableTarget]::User)
       ```
       Restart Ollama from the Windows taskbar tray. *(Security Notice: When binding to `0.0.0.0`, configure Windows Defender Firewall to block inbound connections on port 11434 from Public/Private network adapters, permitting only Docker/WSL virtual adapters).*
     - **macOS (Docker Desktop)**: Test with Ollama bound to `127.0.0.1` first. If needed, run `launchctl setenv OLLAMA_HOST "0.0.0.0:11434"` and restart Ollama (enforcing macOS Application Firewall rules if on public networks).
     - **Linux (`systemd`)**: Bind securely to the Docker bridge gateway (`OLLAMA_HOST=172.17.0.1:11434`) so external network interfaces are never exposed. *(Ensure systemd ordering has `After=docker.service` so the `docker0` bridge exists when Ollama starts, or bind to `127.0.0.1` and use `ufw` / `iptables` rules).*
   - Pull your preferred legal model:
     ```bash
     ollama pull qwen2.5:14b   # Recommended for enterprise legal review
     ollama pull llama3.2:3b   # Lightweight, fast review
     ```

3. **Launch SovereignDoc**:
   - In the repository folder, launch the Docker stack:
     ```bash
     docker compose up -d
     ```
   - Open your browser to: [http://127.0.0.1:5173](http://127.0.0.1:5173).

---

### 1.2 First-Run Legal Disclaimer Acceptance

On your first launch, SovereignDoc presents the **Legal & UPL Disclaimer Modal**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ⚖️ Legal & Regulatory Disclaimer — First-Run Acceptance               │
│                                                                        │
│ SovereignDoc is an automated legal document analysis workstation.      │
│ It does not provide legal advice, does not establish an attorney-client │
│ relationship, and is not a substitute for human legal counsel.         │
│                                                                        │
│ [x] I understand that SovereignDoc is an automated tool and not a     │
│     substitute for professional legal counsel.                         │
│                                                                        │
│                        [ Accept & Proceed ]                            │
└────────────────────────────────────────────────────────────────────────┘
```

1. Review the disclaimer text.
2. Check the mandatory acknowledgement box.
3. Click **[ Accept & Proceed ]**. Your acceptance is stored permanently in your local SQLite database (`accepted_disclaimer_version = "1.1"`). You will not be prompted again unless disclaimer terms are updated.

---

## 2. Ingesting Contracts & Running Automated Audits

### 2.1 Creating a Document Vault

A **Vault** organizes related contracts, matters, notes, and knowledge graphs in an isolated local workspace:

1. Click **+ New Vault** in the left sidebar.
2. Enter a name (e.g. `Acme Vendor Diligence` or `Master Services Agreements 2026`).
3. Optionally add a matter description or client matter number.
4. Click **Create Vault**.

---

### 2.2 Ingesting Legal Agreements (PDF & DOCX)

1. Drag and drop contracts into the upload zone, or click **Browse Files**.
2. SovereignDoc supports **PDF** and **Microsoft Word (DOCX)**.
3. During ingestion, SovereignDoc automatically:
   - Performs structure-aware chunking without breaking legal paragraphs.
   - Clusters PDF lines into cohesive paragraph blocks using a 2-stage line assembly algorithm, ensuring complete legal provisions are extracted intact.
   - Computes synchronized page numbers (3,000 characters per synthetic DOCX page).
   - Generates local FastEmbed ONNX vector embeddings.
   - Builds an SQLite FTS5 full-text keyword search index.

> [!TIP]
> **Full Clause & Paragraph Highlighting**: When you click any citation or risk item, the split viewer highlights the entire clause/paragraph on the PDF canvas or DOCX sheet viewer. If you previously ingested a document on an earlier build and notice narrow word-level highlights, simply delete and re-upload the document to re-index it into full paragraph blocks.

---

### 2.3 Running an Automated Contract Intelligence Review

1. Select your document from the vault list.
2. Click the **Reviewer** tab in the top navigation bar.
3. Click the green **Run Contract Review** button.
4. SovereignDoc evaluates the contract against the deterministic legal rule pack:
   - **Clause Classification**: Identifies and segments the 7 core legal categories (`Indemnification`, `Limitation of Liability`, `Termination`, `Confidentiality`, `Intellectual Property`, `Payment Terms`, and `Governing Law`), with books-and-records and audit covenants systematically evaluated under `Confidentiality`.
   - **Risk Scoring**: Flags high-exposure clauses (uncapped indemnities, missing liability limits, foreign dispute venues, invasive audit covenants, and tight turnaround deadlines).
   - **Obligations Extractor**: Extracts affirmative duties, responsible parties (`Vendor`, `Customer`, `Mutual`), and deadline timeframes.

---

### 2.4 Reviewing Risk Findings & Affirmative Duties

The Reviewer panel displays two structured audit views:

```text
┌──────────────────────────────────────┬──────────────────────────────────────┐
│  ⚠️ Risk Matrix (13 Issues)          │  📋 Affirmative Obligations (24)     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 🔴 HIGH: Missing Liability Cap       │ 🏢 VENDOR: Produce Software Records  │
│    No aggregate liability ceiling.   │    ⏱️ Deadline: 15 business days     │
│    Page 8 • Section 8.2              │    Page 4 • Section 4.1              │
│                                      │                                      │
│ 🟠 MEDIUM: Broad Audit Inspection    │ 👤 CUSTOMER: Written Notice of Audit │
│    Unfettered access to facilities.  │    ⏱️ Deadline: 30 calendar days     │
│    Page 4 • Section 4.1              │    Page 4 • Section 4.1              │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

- **Filter by Severity**: Click `HIGH`, `MEDIUM`, or `LOW` to focus on mission-critical exposure.
- **Interactive Citation Jump**: Click any finding or citation chip to instantly jump to the exact page and highlight the complete paragraph block on the PDF canvas or DOCX sheet viewer.

---

## 3. Navigating the Second Brain Knowledge Graph

Click the **Second Brain** tab in the top header to open the interactive 2D Legal Knowledge Graph.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ [🎯 Current State] [📚 Review Timeline]  🔍 Search Graph...   Clause: [All] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│               (DOC) Master Agreement                                        │
│                 │                                                           │
│                 ├──► (CLS) Confidentiality (incl. Audit & Records)          │
│                 │      ├──► (RISK) Unconditional Audit Fee Shifting         │
│                 │      └──► (DUTY) Deliver Audit Records within 15 Days     │
│                 │                                                           │
│                 └──► (CLS) Limitation of Liability                          │
│                        └──► (RISK) Missing Aggregate Liability Cap          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Reducing Clutter: `[ 🎯 Current State ]` vs `[ 📚 Review Timeline ]`
- **Default Mode (`[ 🎯 Current State ]`)**: Automatically isolates the active legal state from your latest review run. If you ran Reviews #1, #2, and #3, this mode hides historical duplicates, reducing canvas complexity by up to 80% (e.g. from 90 nodes down to ~25).
- **Timeline Mode (`[ 📚 Review Timeline ]`)**: Displays every historical review run and audit progression for comparing contract revisions over time.

---

### 3.2 Laser-Focused Micro-Graphs: Clause Category Isolation
Use the **Clause:** selector in the secondary toolbar to isolate a single clause:
- Select **Confidentiality (incl. Audit & Records)**: The entire graph collapses to a pristine **3 to 5 node cluster** (Document $\rightarrow$ Confidentiality Category $\rightarrow$ Books & Records Audit Risks $\rightarrow$ Record Delivery Duties). *(Inspection and books-and-records covenants are classified and filtered under the Confidentiality family).*
- Select **Termination** or **Limitation of Liability** to audit those specific clauses without noise from unrelated agreement terms.
- Click **✕** next to the dropdown to restore all visible categories.

---

### 3.3 Zero-Click Hover Tooltips
Move your mouse over any circle in the graph:
- A floating glass card instantly displays the entity badge, title, severity/party, explicit deadlines, and the first 100 characters of the contract excerpt.
- Zero clicks required.

---

### 3.4 Deep Dive: The Slide-Out Inspector Drawer
Click on any node in the graph. A 420px **Inspector Drawer** smoothly slides out from the right margin:

1. **Structured Breakdown**:
   - For **Obligations**: Shows Obligated Party (`[VENDOR]`, `[CUSTOMER]`, `[MUTUAL]`), Action Required, Trigger Condition, Explicit Deadlines (`⏱️ 15 business days`), and Clause Category.
   - For **Risks**: Shows Severity Badge (`HIGH`, `MEDIUM`, `LOW`), Rule Identifier, Issue Summary, and Legal Explanation.
2. **Verbatim Contract Quote**: Full syntax-highlighted clause excerpt with a one-click **[📋 Copy Citation]** button.
3. **Connected Entities**: Clickable breadcrumb chips for connected Documents, Review Runs, and Clauses.
4. **Action Buttons**:
   - **[📄 Open in Contract Viewer]**: Jumps directly to the document page.
   - **[📝 Pin Citation to Active Note]**: Appends the formatted quote and citation directly into your active Second Brain matter note!

---

## 4. Conversational Grounded Reviewer & Legal Safety

Click the **Reviewer** (or **Chat**) tab to analyze your agreements using natural language:

### 4.1 Free-Form Questions vs. Prompt Recipes
SovereignDoc provides two flexible ways to analyze contracts:
1. **Free-Form Manual Inquiries**: Type any custom, open-ended question directly into the chat prompt box (e.g. *"What is the governing law in this agreement?"*, *"Who is the notice contact for AIP?"*, or *"What does Section 6.4 say about trademark compliance?"*). The hybrid retrieval engine embeds and keyword-matches your specific query, returning grounded citations for exact clauses, names, dates, or dollar thresholds.
2. **Standardized Prompt Recipes**: Click any of the one-click preset buttons above the prompt bar to trigger pre-built legal audit frameworks:
   - **📋 Obligations & Deadlines**: Focuses on affirmative duties, required notices, deadlines, and operational covenants.
   - **⚠️ Liability & Indemnity**: Focuses on indemnification covenants, liability caps, carve-outs, warranties, and clawbacks.
   - **🔍 Termination Triggers**: Focuses on cause/convenience termination, cure periods, notice requirements, and post-termination survival.
   - **💡 Executive Briefing**: Generates a high-level executive briefing with concise bullet points and direct clause citations.

### 4.2 Document-Scoped Pre-Filtering in Multi-Contract Vaults
When you have multiple contracts in the same vault, SovereignDoc automatically scopes retrieval to the **active document** currently displayed in your document viewer:
- Pre-filtering is applied at both the ChromaDB vector level and BM25 candidate index level.
- This prevents large contracts in your vault from outranking or starving smaller agreements of top-k retrieval slots.
- Both manual queries and preset recipes are guaranteed to extract evidence blocks directly from the document you are examining.

### 4.3 Verifying Grounded Citations & Visual Highlights
Every response generated by the local LLM is strictly grounded in the retrieved excerpts:
- SovereignDoc displays **▶ Sources (X) — Y% Grounded Confidence** in an interactive accordion.
- Click any **📄 Source X** tag in the chat response to automatically jump the document viewer to that exact page and highlight the relevant paragraph bounding box on the PDF canvas.
- Hover over any source to inspect a floating preview of the verbatim text.
- Click **[ 📌 Save to Note ]** to immediately capture a grounded finding into your working Matter Notes.

### 4.3 Understanding the Dual-Layer UPL Notice
If a query asks for subjective legal opinions or legal advice (e.g. *"Should I sign this?"* or *"Can they sue me?"*), SovereignDoc's deterministic **UPL Guard** appends:

> *⚖️ **Notice**: SovereignDoc provides automated document analysis and informational insights only and does not provide legal advice. Consult a qualified, licensed attorney regarding legal decisions.*

---

## 5. Matter Notes & Exporting Deliverables

### 5.1 Personal Second Brain Notes
1. In the **Second Brain** view, use the left Markdown editor to document matter findings.
2. **Bi-Directional WikiLinks**: Type `[[` to link to other notes (`[[Indemnification Strategy]]`) or contract pages (`[[Doc:Master_Agreement.pdf#Page 4]]`).
3. **One-Click Pinning**: Click **[ 📌 Save to Note ]** from any Risk or Obligation to capture formatted citations into your working note.

---

### 5.2 Exporting Review Packages (.ZIP)

When your review is complete, export audit deliverables for clients or executives:

1. In the **Reviewer** tab, click **Export Findings** $\rightarrow$ **Download Review Package (.ZIP)**.
2. The downloaded `.zip` archive contains:
   - `contract_audit.md`: Full executive audit report in Markdown format.
   - `risk_matrix.csv`: Structured risk register compatible with Excel and Pandas.
   - `obligations.csv`: Affirmative duties and SLA calendar table.
   - `DISCLAIMER.txt`: Complete legal and regulatory disclaimer.

---

## 6. Best Practices for Legal Professionals

1. **Always Verify Citations**: Use the built-in jump buttons to review the actual contract text before making advisory recommendations.
2. **Run Comparative Audits**: Re-run contract review after receiving vendor redlines to verify whether proposed changes resolved identified risks.
3. **Use Clause Isolation During Negotiations**: When negotiating a specific section with opposing counsel, isolate that clause in the Second Brain graph to keep all relevant duties, triggers, and risks in single-screen focus.

