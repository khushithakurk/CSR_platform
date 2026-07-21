import "./App.css";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

const API = "http://localhost:5000";

// ── RIIDL info (used in proposal without asking user) ──
const RIIDL_INFO = {
  name: "riidl (Research Innovation Incubation Design Laboratory Foundation)",
  organization: "Somaiya Vidyavihar University, Mumbai",
  location: "520, Bhaskaracharya Building, K.J. Somaiya College of Engineering, Vidyavihar East, Mumbai - 400077, Maharashtra, India",
  about: "riidl is a nationally recognised, sector-agnostic startup incubator and innovation centre set up in 2010 by the Somaiya Trust. It is supported by DST, BIRAC-DBT (Government of India), and Maharashtra State Innovation Society. riidl has incubated 220+ startups, facilitated 1000+ jobs and internships, and contributed to a startup ecosystem valued at over ₹1,226 Cr. It houses a Digital Fabrication Lab (FabLab), India's first DIY BioLab (Bioriidl), and offers workspace, mentoring, IP support, government grants, and investor connections. RIIDL won the National Award 2020 in the Emerging Technology Business Incubator category by DST, Government of India.",
  programs: "Innovate PBL (student funding up to ₹5 lakh), Startup School India, SkillEd, Bioriidl Incubator, Climate Tech & Sustainability Cohort, Maker Mela, Demo Day Acceleration Program",
  sectors: "Healthcare, AgriTech, EdTech, FinTech, BioTech, CleanTech, Embedded Electronics, AI/ML, SAAS, Food Tech",
  recognitions: "National Award 2020 - Emerging Technology Business Incubator (DST, Govt. of India); Supported by DST, BIRAC, Maharashtra State Innovation Society; MIT FabLab Node; Community Partner with MIT Media Lab Community Bio-Initiative",
  contact: "riidl.org/incubation",
  website: "https://riidl.org",
};

// ── Option lists — exactly matching dash_app.py ──
const USER_TYPES = [
  { label: "Startup", value: "startup" },
  { label: "Corporate", value: "corporate" },
  { label: "NGO", value: "ngo" },
  { label: "Incubator", value: "incubator" },
  { label: "Innovation Cell / Innovator", value: "innovation" },
  { label: "Others", value: "others" },
];
const INDUSTRY_OPTIONS = [
  "Healthcare","EdTech","FinTech","AgriTech","CleanTech","BioTech",
  "AI/ML","Manufacturing","E-commerce/Retail","Logistics",
  "Media & Entertainment","Real Estate & Construction","Automotive",
  "Telecom","Energy & Power","Aerospace & Defence","Textiles & Apparel",
  "Food & Beverage","Travel & Hospitality","Other",
];
const STARTUP_STAGE_OPTIONS = [
  "No Revenue (Idea Stage)","Pre-Revenue (MVP Built)","Early Revenue",
  "Growth Stage","Scaling","Profitable/Mature",
];
const CSR_FOCUS_AREA_OPTIONS = [
  "Education","Healthcare & Nutrition","Environment & Sustainability",
  "Rural Development","Women Empowerment & Gender Equality",
  "Skill Development & Livelihood","Sports","Heritage & Culture",
  "Technology & Innovation","Poverty Alleviation","Disaster Relief",
  "Water, Sanitation & Hygiene (WASH)","Other",
];
const CSR_DONATION_PRIORITY_OPTIONS = ["NGOs","R&D","Incubators","Infrastructure","Others"];
const INCUBATOR_TYPE_OPTIONS = ["Government","Private","Academic","NGO-backed"];
const NGO_TYPE_OPTIONS = ["Trust","Society","Section 8 Company","Foundation","Other"];
const GEOGRAPHIC_REACH_OPTIONS = ["North","West","South","East","Central","Pan India"];
const REQUIRED_DOCS_OPTIONS = [
  "CSR Form","80G Certificate","12A Certificate","MOM (Memorandum of Meeting)",
  "AOA (Articles of Association)","Incorporation Certificate","FCRA Registration",
  "PAN Registration No.",
];

// ── Detect which screen to show from URL param ──
function getScreenFromURL() {
  const params = new URLSearchParams(window.location.search);
  const s = params.get("screen");
  if (s === "login" || s === "signup") return s;
  return null;
}

// ── Reusable field wrapper ──
function Field({ label, error, children }) {
  return (
    <div className="field-grp">
      {label && <label className="field-label">{label}</label>}
      {children}
      {error && <p className="field-error">{error}</p>}
    </div>
  );
}

// ── Checklist ──
function Checklist({ options, value, onChange }) {
  const toggle = (opt) => {
    const next = value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt];
    onChange(next);
  };
  return (
    <div className="checklist">
      {options.map((opt) => (
        <label key={opt} className="checklist-item">
          <input type="checkbox" checked={value.includes(opt)} onChange={() => toggle(opt)} />
          {opt}
        </label>
      ))}
    </div>
  );
}

// ── Range (min/max inputs) ──
function RangeSlider({ min, max, step, value, onChange, marks }) {
  return (
    <div style={{ padding: "0 4px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#999", marginBottom: "6px" }}>
        {marks.map((m) => <span key={m}>{m}</span>)}
      </div>
      <div style={{ display: "flex", gap: "10px" }}>
        <div style={{ flex: 1 }}>
          <label className="field-label" style={{ fontSize: "11px" }}>Min</label>
          <input className="field-input" type="number" min={min} max={value[1]} step={step}
            value={value[0]} onChange={(e) => onChange([Number(e.target.value), value[1]])} />
        </div>
        <div style={{ flex: 1 }}>
          <label className="field-label" style={{ fontSize: "11px" }}>Max</label>
          <input className="field-input" type="number" min={value[0]} max={max} step={step}
            value={value[1]} onChange={(e) => onChange([value[0], Number(e.target.value)])} />
        </div>
      </div>
      <p className="field-hint">Selected: ₹{value[0]}L – ₹{value[1]}L</p>
    </div>
  );
}

// ── Section card ──
function SectionCard({ type, title, children }) {
  const colors = {
    startup:    { bg: "rgba(26,127,90,0.05)",   border: "rgba(26,127,90,0.3)"   },
    corporate:  { bg: "rgba(37,99,235,0.05)",   border: "rgba(37,99,235,0.3)"   },
    incubator:  { bg: "rgba(147,51,234,0.05)",  border: "rgba(147,51,234,0.3)"  },
    ngo:        { bg: "rgba(217,119,6,0.05)",   border: "rgba(217,119,6,0.3)"   },
    innovation: { bg: "rgba(8,145,178,0.05)",   border: "rgba(8,145,178,0.3)"   },
    others:     { bg: "rgba(100,116,139,0.07)", border: "rgba(100,116,139,0.35)"},
  }[type] || {};
  return (
    <div className={`section-card section-${type}`}
      style={{ background: colors.bg, borderColor: colors.border, marginTop: "16px" }}>
      <p className="section-card-title">{title}</p>
      {children}
    </div>
  );
}

// ════════════════════════════════════════
// LOGIN SCREEN
// ════════════════════════════════════════
function LoginScreen() {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);

  const validate = () => {
    if (!email || !password) return "Email and password are required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email address.";
    if (password.length < 6) return "Password must be at least 6 characters.";
    return "";
  };

  const handleSubmit = async () => {
    const err = validate();
    if (err) { setError(err); return; }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) setError(data.error || "Login failed. Please try again.");
      else setSuccess(true);
    } catch {
      setError("Could not reach the server. Make sure server.js is running.");
    }
    setLoading(false);
  };

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-wrap">
          <div className="auth-header">
            <div style={{ fontSize: "48px", marginBottom: "12px" }}>✅</div>
            <h2 className="auth-title">Logged in successfully!</h2>
            <p className="auth-sub">You can close this window and return to the dashboard.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-wrap">
        <div className="auth-header">
          <h2 className="auth-title">Welcome back</h2>
          <p className="auth-sub">Log in to your CSR account</p>
        </div>

        {error && <div className="form-alert error">{error}</div>}

        <Field label="Email">
          <input className={`field-input${error ? " invalid" : ""}`} type="email"
            placeholder="you@example.com" value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }} />
        </Field>

        <Field label="Password">
          <input className="field-input" type="password"
            placeholder="Your password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSubmit(); }} />
        </Field>

        <button className="auth-submit-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? "Logging in…" : "Login"}
        </button>

        <p className="auth-switch">
          Don't have an account?{" "}
          <a className="auth-switch-link" href="?screen=signup">Sign Up</a>
        </p>
      </div>
    </div>
  );
}

// ════════════════════════════════════════
// SIGNUP SCREEN — all fields from dash_app.py
// ════════════════════════════════════════
function SignupScreen() {
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [contact, setContact]   = useState("");
  const [password, setPassword] = useState("");
  const [userType, setUserType] = useState("");

  // Startup
  const [sName, setSName]           = useState("");
  const [sIndustry, setSIndustry]   = useState("");
  const [sDomain, setSDomain]       = useState("");
  const [sDesc, setSDesc]           = useState("");
  const [sDpiit, setSDpiit]         = useState("");
  const [sYear, setSYear]           = useState("");
  const [sStage, setSStage]         = useState("");
  const [sPitch, setSPitch]         = useState("");

  // Corporate
  const [cName, setCName]                     = useState("");
  const [cIndustry, setCIndustry]             = useState("");
  const [cDomain, setCDomain]                 = useState("");
  const [cArea, setCArea]                     = useState([]);
  const [cAreaOther, setCAreaOther]           = useState("");
  const [cPriority, setCPriority]             = useState("");
  const [cPriorityOther, setCPriorityOther]   = useState("");
  const [cSector, setCSector]                 = useState("");
  const [cRange, setCRange]                   = useState([5, 100]);

  // Incubator
  const [iName, setIName]             = useState("");
  const [iType, setIType]             = useState("");
  const [iYear, setIYear]             = useState("");
  const [iLocation, setILocation]     = useState("");
  const [iFocus, setIFocus]           = useState([]);
  const [iFocusOther, setIFocusOther] = useState("");
  const [iPartner, setIPartner]       = useState("");
  const [iRevenue, setIRevenue]       = useState([100, 300]);
  const [iDocs, setIDocs]             = useState([]);

  // NGO
  const [nName, setNName]             = useState("");
  const [nType, setNType]             = useState("");
  const [nYear, setNYear]             = useState("");
  const [nLocation, setNLocation]     = useState("");
  const [nFocus, setNFocus]           = useState([]);
  const [nFocusOther, setNFocusOther] = useState("");
  const [nPartner, setNPartner]       = useState("");
  const [nRevenue, setNRevenue]       = useState([100, 300]);
  const [nReach, setNReach]           = useState("");
  const [nDocs, setNDocs]             = useState([]);

  // Innovation
  const [innovName, setInnovName]         = useState("");
  const [innovResearch, setInnovResearch] = useState("");

  // Others
  const [oName, setOName]   = useState("");
  const [oType, setOType]   = useState("");
  const [oDesc, setODesc]   = useState("");
  const [oFocus, setOFocus] = useState("");

  const [errors, setErrors]   = useState({});
  const [alert, setAlert]     = useState(null);
  const [loading, setLoading] = useState(false);

  // ── Validation — exactly matching dash_app.py ──
  const validate = () => {
    const e = {};
    if (!name.trim())    e.name     = "Name is required.";
    if (!email.trim())   e.email    = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = "Enter a valid email address.";
    if (!contact.trim()) e.contact  = "Contact number is required.";
    else if (!/^\d{10}$/.test(contact)) e.contact = "Enter a valid 10-digit contact number.";
    if (!password)       e.password = "Password is required.";
    else if (password.length < 6) e.password = "Password should be at least 6 characters.";
    if (!userType)       e.userType = "Please select who you are.";
    if (userType === "startup" && sYear && !/^(19[9]\d|20[0-2]\d)$/.test(sYear))
      e.sYear = "Please enter a valid year of incorporation (1990–2026).";
    if (userType === "innovation") {
      if (!innovName.trim())     e.innovName     = "Innovator name is required.";
      if (!innovResearch.trim()) e.innovResearch = "Research work description is required.";
    }
    return e;
  };

  // ── Build profile_details — exactly matching dash_app.py ──
  const buildProfile = () => {
    if (userType === "startup") return {
      startup_name: sName, industry: sIndustry, domain: sDomain, description: sDesc,
      dpiit_registered: sDpiit, year_of_incorporation: sDpiit === "yes" ? sYear : null,
      stage: sStage, pitch_deck_link: sPitch,
    };
    if (userType === "corporate") {
      let areaFinal = [...cArea];
      if (areaFinal.includes("Other") && cAreaOther)
        areaFinal = areaFinal.filter((a) => a !== "Other").concat(cAreaOther);
      return {
        corporate_name: cName, industry: cIndustry, domain: cDomain,
        csr_funding_area: areaFinal,
        csr_donation_priority: cPriority === "Others" && cPriorityOther ? cPriorityOther : cPriority,
        csr_funding_sector: cSector,
        csr_funding_range_min_lakh: cRange[0], csr_funding_range_max_lakh: cRange[1],
      };
    }
    if (userType === "incubator") {
      let focusFinal = [...iFocus];
      if (focusFinal.includes("Other") && iFocusOther)
        focusFinal = focusFinal.filter((a) => a !== "Other").concat(iFocusOther);
      return {
        incubator_name: iName, type: iType, year_of_establishment: iYear, location: iLocation,
        csr_focus_area: focusFinal, associate_corporate_partner: iPartner,
        annual_revenue_min_lakh: iRevenue[0], annual_revenue_max_lakh: iRevenue[1],
        documents_available: iDocs, grant_eligible: iDocs.length === REQUIRED_DOCS_OPTIONS.length,
      };
    }
    if (userType === "ngo") {
      let focusFinal = [...nFocus];
      if (focusFinal.includes("Other") && nFocusOther)
        focusFinal = focusFinal.filter((a) => a !== "Other").concat(nFocusOther);
      return {
        ngo_name: nName, type: nType, year_of_establishment: nYear, location: nLocation,
        csr_focus_area: focusFinal, associate_corporate_partner: nPartner,
        annual_revenue_min_lakh: nRevenue[0], annual_revenue_max_lakh: nRevenue[1],
        geographical_reach: nReach, documents_available: nDocs,
        grant_eligible: nDocs.length === REQUIRED_DOCS_OPTIONS.length,
      };
    }
    if (userType === "innovation")
      return { innovator_name: innovName, research_work: innovResearch };
    if (userType === "others")
      return { organization_name: oName, organization_type: oType, description: oDesc, area_of_focus: oFocus };
    return {};
  };

  const handleSubmit = async () => {
    const e = validate();
    setErrors(e);
    if (Object.keys(e).length > 0) return;
    setAlert(null);
    setLoading(true);
    try {
      const res = await fetch(`${API}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, contact, password, user_type: userType, profile_details: buildProfile() }),
      });
      const data = await res.json();
      if (!res.ok) setAlert({ type: "error", msg: data.error || "Signup failed. Please try again." });
      else setAlert({ type: "success", msg: "🎉 Account created! You can close this and log in." });
    } catch {
      setAlert({ type: "error", msg: "Could not reach the server. Make sure server.js is running." });
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-wrap">
        <div className="auth-header">
          <h2 className="auth-title">Create your account</h2>
          <p className="auth-sub">Sign up to discover and apply for CSR grants</p>
        </div>

        {alert && <div className={`form-alert ${alert.type}`}>{alert.msg}</div>}

        {/* ── Base fields ── */}
        <Field label="Name" error={errors.name}>
          <input className={`field-input${errors.name ? " invalid" : ""}`} type="text"
            placeholder="Your full name" value={name} onChange={(e) => setName(e.target.value)} />
        </Field>

        <Field label="Email" error={errors.email}>
          <input className={`field-input${errors.email ? " invalid" : ""}`} type="email"
            placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </Field>

        <div style={{ display: "flex", gap: "14px" }}>
          <Field label="Contact Number" error={errors.contact}>
            <input className={`field-input${errors.contact ? " invalid" : ""}`} type="text"
              placeholder="10-digit phone" value={contact} maxLength={10}
              onChange={(e) => setContact(e.target.value)} />
          </Field>
          <Field label="Password" error={errors.password}>
            <input className={`field-input${errors.password ? " invalid" : ""}`} type="password"
              placeholder="Min 6 characters" value={password}
              onChange={(e) => setPassword(e.target.value)} />
          </Field>
        </div>

        <Field label="Who are you?" error={errors.userType}>
          <select className={`field-select${errors.userType ? " invalid" : ""}`}
            value={userType} onChange={(e) => setUserType(e.target.value)}>
            <option value="">Select one</option>
            {USER_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </Field>

        {/* ════ STARTUP ════ */}
        {userType === "startup" && (
          <SectionCard type="startup" title="🚀 Startup Details">
            <Field label="Name of Startup">
              <input className="field-input" type="text" value={sName} onChange={(e) => setSName(e.target.value)} />
            </Field>
            <Field label="Industry">
              <select className="field-select" value={sIndustry} onChange={(e) => setSIndustry(e.target.value)}>
                <option value="">Select one</option>
                {INDUSTRY_OPTIONS.map((i) => <option key={i}>{i}</option>)}
              </select>
            </Field>
            <Field label="Domain">
              <input className="field-input" type="text" placeholder="e.g. B2B SaaS, D2C, Marketplace"
                value={sDomain} onChange={(e) => setSDomain(e.target.value)} />
            </Field>
            <Field label="Explain what your startup does">
              <textarea className="field-textarea" value={sDesc} onChange={(e) => setSDesc(e.target.value)} />
            </Field>
            <Field label="Have you registered your startup on DPIIT?">
              <div className="radio-row">
                <label className="radio-opt"><input type="radio" name="dpiit" value="yes" checked={sDpiit==="yes"} onChange={()=>setSDpiit("yes")} /> Yes</label>
                <label className="radio-opt"><input type="radio" name="dpiit" value="no"  checked={sDpiit==="no"}  onChange={()=>setSDpiit("no")}  /> No</label>
              </div>
            </Field>
            {sDpiit === "yes" && (
              <Field label="Year of Incorporation" error={errors.sYear}>
                <input className={`field-input${errors.sYear?" invalid":""}`} type="text"
                  placeholder="e.g. 2022" value={sYear} onChange={(e) => setSYear(e.target.value)} />
              </Field>
            )}
            <Field label="Stage of Startup">
              <select className="field-select" value={sStage} onChange={(e) => setSStage(e.target.value)}>
                <option value="">Select one</option>
                {STARTUP_STAGE_OPTIONS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Pitch Deck / Startup Info (optional)">
              <input className="field-input" type="text" placeholder="Google Drive / website link (optional)"
                value={sPitch} onChange={(e) => setSPitch(e.target.value)} />
            </Field>
          </SectionCard>
        )}

        {/* ════ CORPORATE ════ */}
        {userType === "corporate" && (
          <SectionCard type="corporate" title="🏢 Corporate Details">
            <Field label="Name of Corporate">
              <input className="field-input" type="text" value={cName} onChange={(e) => setCName(e.target.value)} />
            </Field>
            <Field label="Industry">
              <select className="field-select" value={cIndustry} onChange={(e) => setCIndustry(e.target.value)}>
                <option value="">Select one</option>
                {INDUSTRY_OPTIONS.map((i) => <option key={i}>{i}</option>)}
              </select>
            </Field>
            <Field label="Domain">
              <input className="field-input" type="text" value={cDomain} onChange={(e) => setCDomain(e.target.value)} />
            </Field>
            <Field label="CSR Funding Area (select all that apply)">
              <Checklist options={CSR_FOCUS_AREA_OPTIONS} value={cArea} onChange={setCArea} />
              {cArea.includes("Other") && (
                <input className="field-input" type="text" placeholder="Please specify"
                  style={{marginTop:"8px"}} value={cAreaOther} onChange={(e) => setCAreaOther(e.target.value)} />
              )}
            </Field>
            <Field label="CSR Donation Priority">
              <select className="field-select" value={cPriority} onChange={(e) => setCPriority(e.target.value)}>
                <option value="">Select one</option>
                {CSR_DONATION_PRIORITY_OPTIONS.map((d) => <option key={d}>{d}</option>)}
              </select>
              {cPriority === "Others" && (
                <input className="field-input" type="text" placeholder="Please specify"
                  style={{marginTop:"8px"}} value={cPriorityOther} onChange={(e) => setCPriorityOther(e.target.value)} />
              )}
            </Field>
            <Field label="CSR Funding Sector">
              <input className="field-input" type="text" placeholder="e.g. Education, Healthcare"
                value={cSector} onChange={(e) => setCSector(e.target.value)} />
            </Field>
            <Field label="CSR Funding Range (in Lakhs)">
              <RangeSlider min={5} max={500} step={5} value={cRange} onChange={setCRange}
                marks={["₹5L","₹50L","₹1Cr","₹2.5Cr","₹5Cr+"]} />
            </Field>
          </SectionCard>
        )}

        {/* ════ INCUBATOR ════ */}
        {userType === "incubator" && (
          <SectionCard type="incubator" title="🧪 Incubator Details">
            <Field label="Name of Incubator">
              <input className="field-input" type="text" value={iName} onChange={(e) => setIName(e.target.value)} />
            </Field>
            <Field label="Type of Incubator">
              <select className="field-select" value={iType} onChange={(e) => setIType(e.target.value)}>
                <option value="">Select one</option>
                {INCUBATOR_TYPE_OPTIONS.map((t) => <option key={t}>{t}</option>)}
              </select>
            </Field>
            <Field label="Year of Establishment">
              <input className="field-input" type="text" placeholder="e.g. 2015"
                value={iYear} onChange={(e) => setIYear(e.target.value)} />
            </Field>
            <Field label="Location of Incubation">
              <input className="field-input" type="text" value={iLocation} onChange={(e) => setILocation(e.target.value)} />
            </Field>
            <Field label="CSR Focus Area (select all that apply)">
              <Checklist options={CSR_FOCUS_AREA_OPTIONS} value={iFocus} onChange={setIFocus} />
              {iFocus.includes("Other") && (
                <input className="field-input" type="text" placeholder="Please specify"
                  style={{marginTop:"8px"}} value={iFocusOther} onChange={(e) => setIFocusOther(e.target.value)} />
              )}
            </Field>
            <Field label="Associate Corporate Partner / Funder">
              <input className="field-input" type="text" value={iPartner} onChange={(e) => setIPartner(e.target.value)} />
            </Field>
            <Field label="Annual Revenue (in Lakhs)">
              <RangeSlider min={100} max={500} step={25} value={iRevenue} onChange={setIRevenue}
                marks={["₹1Cr","₹2Cr","₹3Cr","₹4Cr","₹5Cr+"]} />
            </Field>
            <Field label="Do you have the following documents?">
              <Checklist options={REQUIRED_DOCS_OPTIONS} value={iDocs} onChange={setIDocs} />
              {iDocs.length === REQUIRED_DOCS_OPTIONS.length
                ? <div className="form-alert success" style={{marginTop:"8px"}}>✅ You have all required documents — grant eligible!</div>
                : <div className="form-alert warning" style={{marginTop:"8px"}}>⚠️ You are missing some documents. You can still sign up and complete them later.</div>
              }
            </Field>
          </SectionCard>
        )}

        {/* ════ NGO ════ */}
        {userType === "ngo" && (
          <SectionCard type="ngo" title="🤝 NGO Details">
            <Field label="Name of NGO">
              <input className="field-input" type="text" value={nName} onChange={(e) => setNName(e.target.value)} />
            </Field>
            <Field label="Type of NGO">
              <select className="field-select" value={nType} onChange={(e) => setNType(e.target.value)}>
                <option value="">Select one</option>
                {NGO_TYPE_OPTIONS.map((t) => <option key={t}>{t}</option>)}
              </select>
            </Field>
            <Field label="Year of Establishment">
              <input className="field-input" type="text" placeholder="e.g. 2010"
                value={nYear} onChange={(e) => setNYear(e.target.value)} />
            </Field>
            <Field label="Location of NGO">
              <input className="field-input" type="text" value={nLocation} onChange={(e) => setNLocation(e.target.value)} />
            </Field>
            <Field label="CSR Focus Area (select all that apply)">
              <Checklist options={CSR_FOCUS_AREA_OPTIONS} value={nFocus} onChange={setNFocus} />
              {nFocus.includes("Other") && (
                <input className="field-input" type="text" placeholder="Please specify"
                  style={{marginTop:"8px"}} value={nFocusOther} onChange={(e) => setNFocusOther(e.target.value)} />
              )}
            </Field>
            <Field label="Associate Corporate Partner / Funder">
              <input className="field-input" type="text" value={nPartner} onChange={(e) => setNPartner(e.target.value)} />
            </Field>
            <Field label="Annual Revenue (in Lakhs)">
              <RangeSlider min={100} max={500} step={25} value={nRevenue} onChange={setNRevenue}
                marks={["₹1Cr","₹2Cr","₹3Cr","₹4Cr","₹5Cr+"]} />
            </Field>
            <Field label="Geographical Reach">
              <select className="field-select" value={nReach} onChange={(e) => setNReach(e.target.value)}>
                <option value="">Select one</option>
                {GEOGRAPHIC_REACH_OPTIONS.map((g) => <option key={g}>{g}</option>)}
              </select>
            </Field>
            <Field label="Do you have the following documents?">
              <Checklist options={REQUIRED_DOCS_OPTIONS} value={nDocs} onChange={setNDocs} />
              {nDocs.length === REQUIRED_DOCS_OPTIONS.length
                ? <div className="form-alert success" style={{marginTop:"8px"}}>✅ You have all required documents — grant eligible!</div>
                : <div className="form-alert warning" style={{marginTop:"8px"}}>⚠️ You are missing some documents. You can still sign up and complete them later.</div>
              }
            </Field>
          </SectionCard>
        )}

        {/* ════ INNOVATION ════ */}
        {userType === "innovation" && (
          <SectionCard type="innovation" title="💡 Innovator Details">
            <Field label="Name of Innovator" error={errors.innovName}>
              <input className={`field-input${errors.innovName?" invalid":""}`} type="text"
                value={innovName} onChange={(e) => setInnovName(e.target.value)} />
            </Field>
            <Field label="Explain your research work" error={errors.innovResearch}>
              <textarea className={`field-textarea${errors.innovResearch?" invalid":""}`}
                style={{minHeight:"160px"}} value={innovResearch}
                onChange={(e) => setInnovResearch(e.target.value)} />
            </Field>
          </SectionCard>
        )}

        {/* ════ OTHERS ════ */}
        {userType === "others" && (
          <SectionCard type="others" title="📋 Organization Details">
            <Field label="Organization Name">
              <input className="field-input" type="text" value={oName} onChange={(e) => setOName(e.target.value)} />
            </Field>
            <Field label="Organization Type">
              <input className="field-input" type="text"
                placeholder="e.g. Government Body, Academic Institution, Media"
                value={oType} onChange={(e) => setOType(e.target.value)} />
            </Field>
            <Field label="Brief Description">
              <textarea className="field-textarea" style={{minHeight:"100px"}}
                value={oDesc} onChange={(e) => setODesc(e.target.value)} />
            </Field>
            <Field label="Area of Interest / Focus">
              <input className="field-input" type="text" value={oFocus} onChange={(e) => setOFocus(e.target.value)} />
            </Field>
          </SectionCard>
        )}

        <button className="auth-submit-btn" onClick={handleSubmit} disabled={loading}>
          {loading ? "Creating account…" : "Submit"}
        </button>

        <p className="auth-switch">
          Already have an account?{" "}
          <a className="auth-switch-link" href="?screen=login">Login</a>
        </p>
      </div>
    </div>
  );
}

// ════════════════════════════════════════
// MAIN APP — chatbot only, no auth buttons inside
// ════════════════════════════════════════
function App() {
  // ── Check URL param to render login/signup screens when iframed from dashboard ──
  const urlScreen = getScreenFromURL();
  if (urlScreen === "login")  return <LoginScreen />;
  if (urlScreen === "signup") return <SignupScreen />;

  // ── Chatbot state ──
  const [mode, setMode]                       = useState(null);
  const [lastCompany, setLastCompany]         = useState("");
  const [proposalState, setProposalState]     = useState(null);
  const [startupInfo, setStartupInfo]         = useState({});
  const [collectingField, setCollectingField] = useState(null);

  const STARTUP_FIELDS = [
    { key: "name",    question: "What is your **startup's name**?" },
    { key: "sector",  question: "What **sector or industry** does your startup operate in? (e.g. HealthTech, EdTech, AgriTech)" },
    { key: "stage",   question: "What is your **current stage**? (e.g. Idea, MVP, Early Revenue, Scaling)" },
    { key: "need",    question: "What do you need the **CSR funding for**? (e.g. R&D, infrastructure, pilot program)" },
    { key: "contact", question: "What is your **contact email or founder's name** to include in the letter?" },
  ];

  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const bottomRef               = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (mode === "riidl") {
      setMessages([{
        text: "Hello! I'm your **riidl CSR Intelligence Assistant** 🌱\n\nI help riidl discover CSR funding, partnerships, lab sponsorships, and grants from corporates.\n\nJust enter a **company name** (e.g. *Tata, Infosys, HDFC*) and I'll find what's relevant for riidl!",
        sender: "bot",
      }]);
    } else if (mode === "startup") {
      setMessages([{
        text: "Hello! I'm your **Startup CSR Funding Assistant** 🚀\n\nI help startups discover CSR grants and funding opportunities from corporates.\n\nAsk me anything — enter a **company name**, your **sector**, or a question like *'which companies fund HealthTech startups?'*",
        sender: "bot",
      }]);
    }
    setProposalState(null);
    setStartupInfo({});
    setCollectingField(null);
    setLastCompany("");
  }, [mode]);

  const addBotMessage = (text) => setMessages((prev) => [...prev, { text, sender: "bot" }]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");

    if (proposalState === "collecting" && collectingField !== null) {
      const field = STARTUP_FIELDS[collectingField];
      const updatedInfo = { ...startupInfo, [field.key]: userMessage };
      setStartupInfo(updatedInfo);
      const nextIndex = collectingField + 1;
      if (nextIndex < STARTUP_FIELDS.length) {
        setCollectingField(nextIndex);
        addBotMessage(STARTUP_FIELDS[nextIndex].question);
      } else {
        setCollectingField(null);
        setProposalState("drafting");
        await draftProposal(updatedInfo, lastCompany);
      }
      return;
    }

    if (proposalState === "asked") {
      const lower = userMessage.toLowerCase();
      if (lower.includes("yes") || lower.includes("sure") || lower.includes("ok") || lower.includes("yeah") || lower.includes("please")) {
        if (mode === "riidl") { setProposalState("drafting"); await draftProposal(null, lastCompany); }
        else { setProposalState("collecting"); setCollectingField(0); addBotMessage("Great! I just need a few quick details about your startup to personalise the letter.\n\n" + STARTUP_FIELDS[0].question); }
      } else {
        setProposalState(null);
        addBotMessage("No problem! Feel free to ask about another company or CSR opportunity. 😊");
      }
      return;
    }

    if (proposalState === "done") {
      const lower = userMessage.toLowerCase();
      if (lower.includes("no") || lower.includes("looks good") || lower.includes("perfect") || lower.includes("fine") || lower.includes("thank")) {
        setProposalState(null);
        addBotMessage("Glad I could help! 🎉 Feel free to ask about another company or CSR opportunity.");
      } else {
        setLoading(true);
        await callGemini(`The user wants the following changes to the proposal letter: "${userMessage}". Please revise the proposal accordingly and return the updated letter only.`, true);
        setLoading(false);
        addBotMessage("Would you like any further changes to the proposal? 😊");
      }
      return;
    }

    setLoading(true);
    await callGemini(userMessage, false);
    setLoading(false);
  };

  const callGemini = async (userMessage, isRevision) => {
    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, mode, isRevision }),
      });
      if (response.status === 503) { addBotMessage("⚠️ The  server is currently busy. Please try again in a few minutes."); return; }
      if (!response.ok) { addBotMessage("⚠️ Something went wrong. Please try again."); return; }
      const data = await response.json();
      if (data.company) setLastCompany(data.company);
      setMessages((prev) => [...prev, { text: data.reply, sender: "bot" }]);
      if (!isRevision && data.isCompanyResponse) {
        setTimeout(() => {
          addBotMessage("💼 Would you like me to **draft a proposal letter** to this company on behalf of " + (mode === "riidl" ? "RIIDL" : "your startup") + "? (Yes / No)");
          setProposalState("asked");
        }, 600);
      }
    } catch (error) {
      addBotMessage("⚠️ Unable to connect to the server. Please check your connection and try again.");
      console.error(error);
    }
  };

  const draftProposal = async (info, company) => {
    const entityName = mode === "riidl" ? RIIDL_INFO.name : info?.name || "Our Startup";
    const proposalPrompt = `
Draft a formal, professional CSR proposal/outreach letter from ${entityName} to the CSR team of ${company}.

About the sender:
${mode === "riidl"
  ? `Organization: ${RIIDL_INFO.name}\nAffiliated with: ${RIIDL_INFO.organization}\nLocation: ${RIIDL_INFO.location}\nAbout: ${RIIDL_INFO.about}\nWebsite: ${RIIDL_INFO.website}\nContact: ${RIIDL_INFO.contact}`
  : `Startup Name: ${info?.name}\nSector: ${info?.sector}\nStage: ${info?.stage}\nFunding Need: ${info?.need}\nContact: ${info?.contact}`
}

The letter should:
1. Have a proper subject line
2. Open with a warm professional greeting
3. Introduce the organization/startup clearly in 2-3 lines
4. Explain why they are reaching out to this specific company's CSR program
5. Mention alignment with the company's CSR focus areas
6. State clearly what kind of support or grant they are seeking
7. Close with a call to action and contact details
8. Be formal, concise, and compelling — not more than 350 words
9. Format it as a proper letter with Date, Subject, Dear [CSR Head], body paragraphs, and sign-off

Return ONLY the letter. No extra commentary.
`;
    setLoading(true);
    try {
      const response = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: proposalPrompt, mode, isRevision: false, isProposal: true }),
      });
      if (response.status === 503) { addBotMessage("⚠️ The  server is currently busy. Please try again in a few minutes."); setLoading(false); return; }
      const data = await response.json();
      addBotMessage("📄 **Here is your proposal letter:**\n\n---\n\n" + data.reply);
      setProposalState("done");
      setTimeout(() => addBotMessage("Would you like any **changes** to this proposal? (e.g. *make it shorter*, *change the tone*, *add more about our work*)"), 600);
    } catch (error) {
      addBotMessage("⚠️ Unable to draft the proposal right now. Please try again.");
      console.error(error);
    }
    setLoading(false);
  };

  const mdComponents = {
    a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
    ul: ({ children }) => <ul className="md-list">{children}</ul>,
    li: ({ children }) => <li className="md-item">{children}</li>,
    p: ({ children }) => <p className="md-p">{children}</p>,
    strong: ({ children }) => <strong className="md-bold">{children}</strong>,
    h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
    h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
    hr: () => <hr className="md-hr" />,
  };

  // ── Welcome screen ──
  if (!mode) {
    return (
      <div className="page">
        <div className="welcome-screen">
          <div className="welcome-logo">🌱</div>
          <h1 className="welcome-title">CSR Intelligence Assistant</h1>
          <p className="welcome-sub">Powered by riidl · Somaiya Vidyavihar</p>
          <p className="welcome-desc">
            Welcome! I help discover CSR grants, funding opportunities, and corporate partnerships.
            <br />Please select who you are to get started:
          </p>
          <div className="mode-cards">
            <div className="mode-card" onClick={() => setMode("riidl")}>
              <div className="mode-icon">🏛️</div>
              <div className="mode-label">I am riidl</div>
              <div className="mode-desc">Find CSR funding, partnerships & lab sponsorships for riidl</div>
            </div>
            <div className="mode-card" onClick={() => setMode("startup")}>
              <div className="mode-icon">🚀</div>
              <div className="mode-label">I am a Startup</div>
              <div className="mode-desc">Discover grants & CSR funding opportunities for your startup</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Chat screen ──
  return (
    <div className="page">
      <div className="container">
        <div className="header">
          <div className="header-icon">{mode === "riidl" ? "🏛️" : "🚀"}</div>
          <div style={{ flex: 1 }}>
            <h1>{mode === "riidl" ? "riidl CSR Assistant" : "Startup CSR Assistant"}</h1>
            <p className="header-sub">
              {mode === "riidl"
                ? "Finding CSR opportunities for RIIDL · Somaiya Vidyavihar"
                : "Grants · Funding · CSR Research for Startups"}
            </p>
          </div>
          <button className="switch-btn" onClick={() => setMode(null)}>⬅ Switch Mode</button>
        </div>

        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.sender}`}>
              {msg.sender === "bot" && <div className="avatar">{mode === "riidl" ? "🏛️" : "🚀"}</div>}
              <div className={`bubble ${msg.sender}`}>
                {msg.sender === "bot"
                  ? <ReactMarkdown components={mdComponents}>{msg.text}</ReactMarkdown>
                  : msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-row bot">
              <div className="avatar">{mode === "riidl" ? "🏛️" : "🚀"}</div>
              <div className="bubble bot loading-bubble">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <input type="text"
            placeholder={
              proposalState === "collecting" ? "Type your answer..."
              : proposalState === "asked"    ? "Type Yes or No..."
              : proposalState === "done"     ? "Suggest changes or say No..."
              : mode === "riidl"             ? "Enter a company name (e.g. Tata, Infosys, HDFC)..."
              :                               "Ask about grants, CSR programs, company funding..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>{loading ? "..." : "Send"}</button>
        </div>
      </div>
    </div>
  );
}

export default App;