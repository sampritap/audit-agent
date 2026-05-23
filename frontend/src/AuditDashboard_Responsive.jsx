import { useState, useRef, useCallback } from "react";

// ─── ICONS ───────────────────────────────────────────────────────────────────
const IconUpload = () => (
  <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
  </svg>
);
const IconFile = () => (
  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
  </svg>
);
const IconAlert = () => (
  <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
  </svg>
);
const IconShield = () => (
  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
  </svg>
);
const IconChevron = ({ open }) => (
  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
    style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
  </svg>
);
const IconX = () => (
  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
  </svg>
);

// ─── CONSTANTS ────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:8000";

const FINDING_META = {
  PRICE_MISMATCH:       { label: "Price Mismatch",        color: "#f59e0b", bg: "#fffbeb", border: "#fde68a" },
  VOLUME_OVERAGE:       { label: "Volume Overage",         color: "#f97316", bg: "#fff7ed", border: "#fed7aa" },
  PROHIBITED_CHARGE:    { label: "Prohibited Charge",      color: "#ef4444", bg: "#fef2f2", border: "#fecaca" },
  UNAPPROVED_AMENDMENT: { label: "Unapproved Amendment",   color: "#8b5cf6", bg: "#f5f3ff", border: "#ddd6fe" },
  DISPUTED_QUANTITY:    { label: "Disputed Quantity",      color: "#ec4899", bg: "#fdf2f8", border: "#fbcfe8" },
};

const RISK_CONFIG = {
  HIGH:   { color: "#ef4444", bg: "#fef2f2", ring: "#fca5a5", label: "HIGH RISK",   glow: "0 0 24px rgba(239,68,68,0.25)" },
  MEDIUM: { color: "#f59e0b", bg: "#fffbeb", ring: "#fde68a", label: "MEDIUM RISK", glow: "0 0 24px rgba(245,158,11,0.25)" },
  LOW:    { color: "#22c55e", bg: "#f0fdf4", ring: "#86efac", label: "LOW RISK",    glow: "0 0 24px rgba(34,197,94,0.25)"  },
};

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const MOCK_RESULT = {
  risk_score: 78,
  risk_level: "HIGH",
  estimated_overbill_inr: 75850,
  total_findings: 5,
  reasoning: "This invoice contains multiple critical anomalies including an unapproved rate revision citing a non-existent amendment (AMD-2024-01) and a prohibited platform levy charge totalling INR 30,500. Immediate dispute is recommended before payment.",
  findings: [
    { type: "PRICE_MISMATCH", service: "Cloud Compute – Premium Tier", contracted_rate: 7.20, billed_rate: 8.95, overage_pct: 24.31, estimated_overbill_inr: 14350, contract_clause: "Section 2.1 – Unit Pricing" },
    { type: "VOLUME_OVERAGE", service: "Object Storage", contracted_cap: 10000, billed_qty: 11400, overage_qty: 1400, correct_overage_rate: 3.20, contract_clause: "Section 2.2 – Volume Commitments" },
    { type: "PROHIBITED_CHARGE", service: "Platform Infrastructure Levy", amount_inr: 18500, reason: "Matches prohibited charge: 'platform maintenance or upgrade fees'", contract_clause: "Section 6 – Prohibited Charges" },
    { type: "UNAPPROVED_AMENDMENT", amendment_refs: ["AMD-2024-01"], reason: "Invoice cites amendment with no signed counterpart in contract", contract_clause: "Section 9 – Amendments and Modifications" },
    { type: "PRICE_MISMATCH", service: "Pricing Adjustment (AMD-2024-01)", contracted_rate: 0, billed_rate: 12000, overage_pct: 100, estimated_overbill_inr: 12000, contract_clause: "Section 9 – Amendments and Modifications" },
  ],
  contract_data: { vendor_name: "CloudTech Solutions Pvt. Ltd.", contract_ref: "MSA-2024-CT-00892", billing_cycle: "monthly", payment_terms_days: 30 },
  invoice_data:  { invoice_number: "INV-CT-2024-0387", billing_period: "March 1–31, 2024", total: 530591, subtotal: 454740 },
};

const fmt = (n) => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(n);

// ─── COMPONENTS ───────────────────────────────────────────────────────────────

function DropZone({ label, hint, file, onFile, onClear }) {
  const inputRef = useRef();
  const [dragging, setDragging] = useState(false);

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type === "application/pdf") onFile(f);
  }, [onFile]);

  return (
    <div style={{ flex: 1, minWidth: "280px" }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "#64748b", marginBottom: 8 }}>{label}</div>
      {file ? (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", background: "#f0fdf4", border: "1.5px solid #86efac", borderRadius: 10 }}>
          <div style={{ color: "#22c55e" }}><IconFile /></div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#166534", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{file.name}</div>
            <div style={{ fontSize: 11, color: "#4ade80" }}>{(file.size / 1024).toFixed(1)} KB</div>
          </div>
          <button onClick={onClear} style={{ background: "none", border: "none", cursor: "pointer", color: "#86efac", padding: 2, display: "flex", alignItems: "center" }}><IconX /></button>
        </div>
      ) : (
        <div
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          style={{
            padding: "24px 16px", border: `2px dashed ${dragging ? "#6366f1" : "#e2e8f0"}`,
            borderRadius: 10, textAlign: "center", cursor: "pointer",
            background: dragging ? "#eef2ff" : "#fafafa",
            transition: "all 0.15s",
          }}>
          <div style={{ color: dragging ? "#6366f1" : "#94a3b8", marginBottom: 6, display: "flex", justifyContent: "center" }}><IconUpload /></div>
          <div style={{ fontSize: 12, fontWeight: 600, color: dragging ? "#6366f1" : "#64748b" }}>Drop PDF or click</div>
          <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 3 }}>{hint}</div>
          <input ref={inputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={(e) => onFile(e.target.files[0])} />
        </div>
      )}
    </div>
  );
}

function ScoreRing({ score, level }) {
  const cfg = RISK_CONFIG[level] || RISK_CONFIG.LOW;
  const r = 52, circ = 2 * Math.PI * r;
  const dash = circ * (score / 100);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <div style={{ position: "relative", width: 128, height: 128 }}>
        <svg width="128" height="128" style={{ transform: "rotate(-90deg)" }}>
          <circle cx="64" cy="64" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10"/>
          <circle cx="64" cy="64" r={r} fill="none" stroke={cfg.color} strokeWidth="10"
            strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
            style={{ transition: "stroke-dasharray 1s cubic-bezier(.4,0,.2,1)", filter: `drop-shadow(0 0 6px ${cfg.color}88)` }}/>
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontSize: 30, fontWeight: 800, color: cfg.color, lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", letterSpacing: "0.05em" }}>/ 100</div>
        </div>
      </div>
      <div style={{ padding: "4px 14px", borderRadius: 20, background: cfg.bg, border: `1.5px solid ${cfg.ring}`, fontSize: 11, fontWeight: 800, color: cfg.color, letterSpacing: "0.08em" }}>
        {cfg.label}
      </div>
    </div>
  );
}

function FindingCard({ finding, index }) {
  const [open, setOpen] = useState(index === 0);
  const meta = FINDING_META[finding.type] || { label: finding.type, color: "#64748b", bg: "#f8fafc", border: "#e2e8f0" };

  return (
    <div style={{ border: `1.5px solid ${open ? meta.border : "#e2e8f0"}`, borderRadius: 10, overflow: "hidden", transition: "border-color 0.2s", background: open ? meta.bg : "white" }}>
      <button onClick={() => setOpen(!open)} style={{
        width: "100%", display: "flex", alignItems: "center", gap: 10, padding: "12px 14px",
        background: "none", border: "none", cursor: "pointer", textAlign: "left"
      }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: meta.color, flexShrink: 0 }}/>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: meta.color, letterSpacing: "0.05em", textTransform: "uppercase" }}>{meta.label}</div>
          <div style={{ fontSize: 12, color: "#334155", marginTop: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {finding.service || finding.amendment_refs?.join(", ") || "—"}
          </div>
        </div>
        {finding.estimated_overbill_inr > 0 && (
          <div style={{ fontSize: 12, fontWeight: 700, color: "#ef4444", flexShrink: 0 }}>₹{fmt(finding.estimated_overbill_inr)}</div>
        )}
        <div style={{ color: "#94a3b8", flexShrink: 0 }}><IconChevron open={open} /></div>
      </button>

      {open && (
        <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${meta.border}` }}>
          <div style={{ height: 10 }}/>
          <div style={{ display: "grid", gap: 6, fontSize: 12 }}>
            {finding.contracted_rate !== undefined && (
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Contracted Rate</span>
                <span style={{ fontWeight: 700 }}>₹{finding.contracted_rate}/unit</span>
              </div>
            )}
            {finding.billed_rate !== undefined && finding.billed_rate > 0 && (
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Billed Rate</span>
                <span style={{ fontWeight: 700, color: "#b91c1c" }}>₹{finding.billed_rate}/unit</span>
              </div>
            )}
            {finding.reason && (
              <div style={{ marginTop: 4, padding: "6px 10px", background: "white", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 11, color: "#64748b" }}>
                {finding.reason}
              </div>
            )}
            <div style={{ marginTop: 4, padding: "6px 10px", background: "white", borderRadius: 6, border: "1px solid #e2e8f0", fontSize: 11, color: "#64748b" }}>
              <span style={{ fontWeight: 700 }}>Clause: </span>{finding.contract_clause}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, sub, accent }) {
  return (
    <div style={{ padding: "14px 16px", background: "#f8fafc", borderRadius: 10, border: "1.5px solid #e2e8f0", flex: 1, minWidth: "140px" }}>
      <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 800, color: accent || "#1e293b", lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function AuditDashboard() {
  const [contract, setContract] = useState(null);
  const [invoice, setInvoice]   = useState(null);
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState("");
  const [useMock, setUseMock]   = useState(false);
  const [progress, setProgress] = useState("");

  const canRun = contract && invoice;

  const runAudit = async () => {
    setLoading(true); setError(""); setResult(null);

    if (useMock) {
      setProgress("Extracting contract terms...");
      await new Promise(r => setTimeout(r, 900));
      setProgress("Extracting invoice data...");
      await new Promise(r => setTimeout(r, 900));
      setProgress("Running drift analysis...");
      await new Promise(r => setTimeout(r, 800));
      setResult(MOCK_RESULT);
      setLoading(false); setProgress(""); return;
    }

    try {
      setProgress("Uploading documents...");
      const form = new FormData();
      form.append("contract", contract);
      form.append("invoice", invoice);
      form.append("vendor_name", "CloudTech");
      form.append("contract_ref", "MSA-2024-CT-00892");
      form.append("billing_period", "2024-03");

      const res = await fetch(`${API_BASE}/audit`, { method: "POST", body: form });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      const auditData = data.audit || data;
      
      auditData.risk_score = auditData.risk_score || 0;
      auditData.risk_level = auditData.risk_level || "LOW";
      auditData.findings = auditData.findings || [];
      auditData.estimated_overbill_inr = auditData.estimated_overbill_inr || 0;
      auditData.total_findings = auditData.total_findings || auditData.findings.length;

      setResult(auditData);
    } catch (e) {
      setError(`Could not reach backend. Enable demo mode to preview UI.`);
    }
    setLoading(false); setProgress("");
  };

  const risk = result ? RISK_CONFIG[result.risk_level] || RISK_CONFIG.LOW : null;

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "'DM Sans', 'Segoe UI', sans-serif", width: "100%" }}>
      <style>{`
        @keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { margin: 0; padding: 0; width: 100%; overflow-x: hidden; }
        #root { width: 100%; }
        button:hover { opacity: 0.88; }
      `}</style>

      {/* TOPBAR */}
      <div style={{ background: "white", borderBottom: "1.5px solid #e2e8f0", padding: "0 16px", height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100, width: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg,#6366f1,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", color: "white" }}>
            <IconShield />
          </div>
          <div style={{ fontSize: 14, fontWeight: 800, color: "#1e293b" }}>AuditAgent</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: "#64748b", display: window.innerWidth > 640 ? "block" : "none" }}>Demo</span>
          <button onClick={() => setUseMock(!useMock)} style={{
            width: 36, height: 20, borderRadius: 10, border: "none", cursor: "pointer",
            background: useMock ? "#6366f1" : "#e2e8f0", position: "relative", transition: "background 0.2s"
          }}>
            <div style={{ width: 16, height: 16, borderRadius: "50%", background: "white", position: "absolute", top: 2, left: useMock ? 18 : 2, transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }}/>
          </button>
        </div>
      </div>

      <div style={{ maxWidth: "100%", width: "100%", margin: "0 auto", padding: "20px 16px", display: "flex", flexDirection: "column", gap: 20 }}>

        {/* UPLOAD CARD */}
        <div style={{ background: "white", borderRadius: 14, border: "1.5px solid #e2e8f0", padding: "16px", animation: "fadeUp 0.4s ease" }}>
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 15, fontWeight: 800, color: "#1e293b" }}>Upload Documents</div>
            <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 2 }}>Upload contract and invoice PDFs</div>
          </div>

          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 16 }}>
            <DropZone label="Contract" hint="MSA PDF" file={contract} onFile={setContract} onClear={() => setContract(null)} />
            <DropZone label="Invoice" hint="Invoice PDF" file={invoice} onFile={setInvoice} onClear={() => setInvoice(null)} />
          </div>

          {error && (
            <div style={{ padding: "10px 14px", background: "#fef2f2", border: "1.5px solid #fecaca", borderRadius: 10, fontSize: 12, color: "#b91c1c", display: "flex", alignItems: "flex-start", gap: 8, marginBottom: 14 }}>
              <IconAlert /> {error}
            </div>
          )}

          <button
            onClick={runAudit}
            disabled={!canRun || loading}
            style={{
              width: "100%", padding: "13px 20px", borderRadius: 10, border: "none", cursor: canRun && !loading ? "pointer" : "not-allowed",
              background: canRun && !loading ? "linear-gradient(135deg,#6366f1,#8b5cf6)" : "#e2e8f0",
              color: canRun && !loading ? "white" : "#94a3b8",
              fontSize: 14, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", gap: 10
            }}>
            {loading ? (
              <>
                <div style={{ width: 16, height: 16, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%", animation: "spin 0.7s linear infinite" }}/>
                {progress || "Running..."}
              </>
            ) : (
              <><IconShield /> Run Audit</>
            )}
          </button>
        </div>

        {/* RESULTS */}
        {result && (
          <div style={{ animation: "fadeUp 0.5s ease", display: "flex", flexDirection: "column", gap: 16 }}>
            
            {/* SUMMARY */}
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "center" }}>
              <div style={{ background: "white", borderRadius: 14, border: `1.5px solid ${risk.ring}`, padding: "20px", display: "flex", justifyContent: "center", boxShadow: risk.glow }}>
                <ScoreRing score={result.risk_score} level={result.risk_level} />
              </div>

              <div style={{ flex: 1, minWidth: "280px", display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <Stat label="Overbill" value={`₹${fmt(result.estimated_overbill_inr)}`} sub="Disputed" accent="#ef4444" />
                  <Stat label="Findings" value={result.total_findings} sub="Anomalies" accent="#f59e0b" />
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <Stat label="Vendor" value={result.contract_data?.vendor_name?.split(" ")[0] || "—"} sub={result.contract_data?.contract_ref} />
                  <Stat label="Invoice" value={result.invoice_data?.invoice_number?.split("-").pop() || "—"} sub={result.invoice_data?.billing_period} />
                </div>
              </div>
            </div>

            {/* FINDINGS */}
            <div style={{ background: "white", borderRadius: 14, border: "1.5px solid #e2e8f0", padding: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#1e293b", marginBottom: 12 }}>Findings ({result.findings?.length || 0})</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {result.findings?.map((f, i) => <FindingCard key={i} finding={f} index={i} />)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
