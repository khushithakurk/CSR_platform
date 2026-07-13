import "./App.css";
import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

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

function App() {
  // ── Mode: null = welcome, "riidl" or "startup" ──
  const [mode, setMode] = useState(null);

  // ── Track last company the bot responded about (for proposal) ──
  const [lastCompany, setLastCompany] = useState("");

  // ── Proposal flow state ──
  // null | "asked" | "collecting" | "drafting" | "done"
  const [proposalState, setProposalState] = useState(null);
  const [startupInfo, setStartupInfo] = useState({});
  const [collectingField, setCollectingField] = useState(null);

  const STARTUP_FIELDS = [
    { key: "name",    question: "What is your **startup's name**?" },
    { key: "sector",  question: "What **sector or industry** does your startup operate in? (e.g. HealthTech, EdTech, AgriTech)" },
    { key: "stage",   question: "What is your **current stage**? (e.g. Idea, MVP, Early Revenue, Scaling)" },
    { key: "need",    question: "What do you need the **CSR funding for**? (e.g. R&D, infrastructure, pilot program)" },
    { key: "contact", question: "What is your **contact email or founder's name** to include in the letter?" },
  ];

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Set initial message when mode is selected ──
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

  // ── Add a bot message helper ──
  const addBotMessage = (text) => {
    setMessages((prev) => [...prev, { text, sender: "bot" }]);
  };

  // ── Main send handler ──
  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setMessages((prev) => [...prev, { text: userMessage, sender: "user" }]);
    setInput("");

    // ── Proposal flow: collecting startup info ──
    if (proposalState === "collecting" && collectingField !== null) {
      const field = STARTUP_FIELDS[collectingField];
      const updatedInfo = { ...startupInfo, [field.key]: userMessage };
      setStartupInfo(updatedInfo);

      const nextIndex = collectingField + 1;
      if (nextIndex < STARTUP_FIELDS.length) {
        setCollectingField(nextIndex);
        addBotMessage(STARTUP_FIELDS[nextIndex].question);
      } else {
        // All info collected — draft proposal
        setCollectingField(null);
        setProposalState("drafting");
        await draftProposal(updatedInfo, lastCompany);
      }
      return;
    }

    // ── Proposal flow: user replied yes/no to "draft proposal?" ──
    if (proposalState === "asked") {
      const lower = userMessage.toLowerCase();
      if (lower.includes("yes") || lower.includes("sure") || lower.includes("ok") || lower.includes("yeah") || lower.includes("please")) {
        if (mode === "riidl") {
          setProposalState("drafting");
          await draftProposal(null, lastCompany);
        } else {
          setProposalState("collecting");
          setCollectingField(0);
          addBotMessage("Great! I just need a few quick details about your startup to personalise the letter.\n\n" + STARTUP_FIELDS[0].question);
        }
      } else {
        setProposalState(null);
        addBotMessage("No problem! Feel free to ask about another company or CSR opportunity. 😊");
      }
      return;
    }

    // ── Proposal flow: user replied to "any changes?" ──
    if (proposalState === "done") {
      const lower = userMessage.toLowerCase();
      if (lower.includes("no") || lower.includes("looks good") || lower.includes("perfect") || lower.includes("fine") || lower.includes("thank")) {
        setProposalState(null);
        addBotMessage("Glad I could help! 🎉 Feel free to ask about another company or CSR opportunity.");
      } else {
        // User wants changes — send to Gemini with revision instruction
        setLoading(true);
        await callGemini(`The user wants the following changes to the proposal letter: "${userMessage}". Please revise the proposal accordingly and return the updated letter only.`, true);
        setLoading(false);
        addBotMessage("Would you like any further changes to the proposal? 😊");
      }
      return;
    }

    // ── Normal chat flow ──
    setLoading(true);
    await callGemini(userMessage, false);
    setLoading(false);
  };

  // ── Call backend (Gemini) ──
  const callGemini = async (userMessage, isRevision) => {
    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, mode, isRevision }),
      });

      // ── 503 handler ──
      if (response.status === 503) {
        addBotMessage("⚠️ The  server is currently busy. Please try again in a few minutes.");
        return;
      }

      if (!response.ok) {
        addBotMessage("⚠️ Something went wrong. Please try again.");
        return;
      }

      const data = await response.json();
      const reply = data.reply;

      // ── Detect company name from reply (backend sends it back) ──
      if (data.company) setLastCompany(data.company);

      setMessages((prev) => [...prev, { text: reply, sender: "bot" }]);

      // ── After a company response, ask about proposal ──
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

  // ── Draft proposal letter ──
  const draftProposal = async (info, company) => {
    const entity = mode === "riidl" ? RIIDL_INFO : info;
    const entityName = mode === "riidl" ? RIIDL_INFO.name : info?.name || "Our Startup";
    const about = mode === "riidl"
      ? RIIDL_INFO.about
      : `a ${info?.stage || "early-stage"} startup in the ${info?.sector || "technology"} sector seeking CSR support for ${info?.need || "our initiatives"}`;
    const contact = mode === "riidl" ? RIIDL_INFO.contact : info?.contact || "";

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
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: proposalPrompt, mode, isRevision: false, isProposal: true }),
      });

      if (response.status === 503) {
        addBotMessage("⚠️ The  server is currently busy. Please try again in a few minutes.");
        setLoading(false);
        return;
      }

      const data = await response.json();
      addBotMessage("📄 **Here is your proposal letter:**\n\n---\n\n" + data.reply);
      setProposalState("done");
      setTimeout(() => {
        addBotMessage("Would you like any **changes** to this proposal? (e.g. *make it shorter*, *change the tone*, *add more about our work*)");
      }, 600);

    } catch (error) {
      addBotMessage("⚠️ Unable to draft the proposal right now. Please try again.");
      console.error(error);
    }
    setLoading(false);
  };

  // ── Markdown renderer config ──
  const mdComponents = {
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>
    ),
    ul: ({ children }) => <ul className="md-list">{children}</ul>,
    li: ({ children }) => <li className="md-item">{children}</li>,
    p: ({ children }) => <p className="md-p">{children}</p>,
    strong: ({ children }) => <strong className="md-bold">{children}</strong>,
    h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
    h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
    hr: () => <hr className="md-hr" />,
  };

  // ════════════════════════════════════════
  // WELCOME SCREEN
  // ════════════════════════════════════════
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

  // ════════════════════════════════════════
  // CHAT SCREEN
  // ════════════════════════════════════════
  return (
    <div className="page">
      <div className="container">

        {/* Header */}
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

        {/* Chat box */}
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message-row ${msg.sender}`}>
              {msg.sender === "bot" && (
                <div className="avatar">{mode === "riidl" ? "🏛️" : "🚀"}</div>
              )}
              <div className={`bubble ${msg.sender}`}>
                {msg.sender === "bot" ? (
                  <ReactMarkdown components={mdComponents}>{msg.text}</ReactMarkdown>
                ) : (
                  msg.text
                )}
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

        {/* Input */}
        <div className="input-area">
          <input
            type="text"
            placeholder={
              proposalState === "collecting"
                ? "Type your answer..."
                : proposalState === "asked"
                ? "Type Yes or No..."
                : proposalState === "done"
                ? "Suggest changes or say No..."
                : mode === "riidl"
                ? "Enter a company name (e.g. Tata, Infosys, HDFC)..."
                : "Ask about grants, CSR programs, company funding..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }}
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? "..." : "Send"}
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;
