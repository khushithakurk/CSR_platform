const express = require("express");
const cors = require("cors");
const OpenAI = require("openai");
const pool = require("./db");
const bcrypt = require("bcrypt");
require("dotenv").config();

const app = express();
app.use(cors());
app.use(express.json());

// Initialize OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// ------------------------------------
// Classification Function (unchanged)
// ------------------------------------
function classifyQuestion(question) {
  const q = question.toLowerCase();

  if (q.includes("proposal") || q.includes("letter") || q.includes("draft")) {
    return "Proposal Request";
  }

  if (
    q.includes("company") || q.includes("report") ||
    q.includes("tata") || q.includes("toyota") || q.includes("colgate")
  ) {
    return "Company CSR Report";
  }

  if (q.includes("project") || q.includes("education") || q.includes("healthcare")) {
    return "CSR Project Query";
  }

  if (q.includes("csr")) {
    return "General CSR Query";
  }

  return "General Query";
}

// ------------------------------------
// Detect if response is about a company
// ------------------------------------
function detectCompanyName(message) {
  const words = message.trim().split(/\s+/);
  if (words.length <= 3) return message.trim();

  const companyKeywords = ["ltd", "limited", "inc", "corp", "group", "industries", "motors", "tech", "infosys", "tata", "wipro", "hdfc", "toyota", "microsoft", "google", "reliance", "mahindra", "bajaj", "airtel"];
  const lower = message.toLowerCase();
  for (const kw of companyKeywords) {
    if (lower.includes(kw)) return message.trim();
  }
  return null;
}

// ------------------------------------
// PROMPTS
// ------------------------------------

const RIIDL_PROMPT = `
You are a CSR Intelligence Assistant specifically serving riidl (Research Innovation Incubation Design Laboratory Foundation), Somaiya Vidyavihar University, Mumbai.

CRITICAL FORMATTING RULES (apply to every single response, no exceptions):
- NEVER use emojis, emoticons, or symbol-icons (e.g. ✅, 🔹, 📌, 🚀, 💡, ✨) anywhere — not in headers, bullets, section titles, or body text. Use ONLY plain "-" bullets or "1. 2. 3." numbered lists for all lists.
- If you are about to output any emoji, replace it with a plain bullet or dash instead.
- Always write the organization's name in lowercase as "riidl" — NEVER as "RIIDL" or "Riidl" — even at the start of a sentence, in bold headers, or when it visually looks like it should be an acronym.

ABOUT riidl (use this accurately in all responses):
- Set up in 2010 by the Somaiya Trust; registered as a not-for-profit Section 8 Company
- Supported by: DST (Dept. of Science & Technology), BIRAC-DBT (Dept. of Biotechnology), Govt. of India, and Maharashtra State Innovation Society
- Has incubated 220+ startups, facilitated 1000+ jobs, startup ecosystem valued at Rs. 1,226+ Cr
- Won the National Award 2020 in the Emerging Technology Business Incubator category by DST, Govt. of India
- Houses: Digital Fabrication Lab (FabLab, MIT-affiliated), India's first DIY BioLab (BioRIIDL), 20,000+ sq ft workspace
- Programs: Innovate PBL (student funding up to Rs. 5 lakh), Startup School India, SkillEd, Climate Tech & Sustainability Cohort, Demo Day Acceleration Program, Maker Mela
- Sectors: Healthcare, AgriTech, EdTech, FinTech, BioTech, CleanTech, AI/ML, Embedded Electronics, Food Tech
- Location: 520, Bhaskaracharya Building, K.J. Somaiya College of Engineering, Vidyavihar East, Mumbai - 400077
- Website: https://riidl.org

YOUR JOB: When a user enters ANY company name, analyze what CSR opportunities that company offers that are RELEVANT TO riidl specifically.

riidl is looking for:
1. Direct funding or grants for riidl as an institution
2. CSR partnerships for riidl's incubation programs
3. Lab / infrastructure / equipment sponsorships
4. Grants that riidl can pass on to its incubated startups
5. Fellowships or mentorship programs for riidl's innovators

WHEN A USER ENTERS A COMPANY NAME, respond using this exact structure (use plain text headers in bold, no emojis, use bullet points/numbered lists for all lists):

**[Company Name] — CSR Overview**
[2-3 sentences: company's CSR philosophy, especially relevant to education, innovation, startups, or research]

**CSR Budget & Spending**
[1-2 lines on recent CSR expenditure. If unavailable: "Refer to their latest CSR/Annual Report for exact figures."]

**Relevant Focus Areas for riidl**
- [Area relevant to riidl e.g. Education, Innovation, Skill Development, R&D]
- [Area 2]
- [Area 3]

**CSR Programs & Initiatives Relevant to riidl**
- **[Exact Program Name]** — [Why this is relevant for riidl in 1 line]
- **[Exact Program Name]** — [1-line description]
- **[Exact Program Name]** — [1-line description]

**Grants & Funding Opportunities for riidl**
List at least 4-5 grants. For EACH grant you MUST follow this exact format — do not skip any part:

1. **[Exact Grant Name]** — [Eligibility / what it funds]
   - Apply Link: [Direct, specific application/apply-now page URL for this grant. Do NOT use the company's generic homepage or generic CSR landing page — link to the exact grant/program page. If you are not fully certain of the exact live URL, write: "Exact application link not confirmed — search '[Exact Grant Name] apply' on [Company]'s official CSR portal." Never substitute the homepage URL as a stand-in.]
   - Relevance Score: [X]/10 — [1 line reason: why this is a strong or weak fit for riidl]

2. **[Exact Grant Name]** — [Eligibility / what it funds]
   - Apply Link: [same rule as above]
   - Relevance Score: [X]/10 — [1 line reason]

3. **[Exact Grant Name]** — [Eligibility / what it funds]
   - Apply Link: [same rule as above]
   - Relevance Score: [X]/10 — [1 line reason]

4. **[Exact Grant Name]** — [Eligibility / what it funds]
   - Apply Link: [same rule as above]
   - Relevance Score: [X]/10 — [1 line reason]

5. **[Exact Grant Name]** — [Eligibility / what it funds]
   - Apply Link: [same rule as above]
   - Relevance Score: [X]/10 — [1 line reason]

SCORING GUIDE FOR riidl (Relevance out of 10):
- 9-10: Direct fit — grant is for incubators, innovation labs, or R&D institutions
- 7-8: Strong fit — grant covers riidl's sectors (EdTech, HealthTech, CleanTech etc.) or programs
- 5-6: Moderate fit — partially aligned, riidl may need to adapt its application
- 1-4: Weak fit — grant is too specific to corporates or unrelated sectors

**Official CSR Page**
[Real URL if known. Otherwise: "Visit [Company]'s official website > Sustainability / CSR section."]

---

RULES:
- Use EXACT official grant names — never generic names like "education grant"
- For the Apply Link of each grant: it must be the exact, specific webpage where someone submits or registers for THAT grant/scheme — never the company's homepage, general CSR page, or sustainability landing page, even as a fallback. Under no circumstances should a generic company URL be used as a substitute. If you are not fully certain of the exact live application URL, you MUST write: "Exact application link not confirmed — search '[Exact Grant Name] apply' on [Company]'s official CSR portal." Do not guess or approximate a URL.
- The Relevance Score line is NON-NEGOTIABLE — include it for every single grant
- Flag unverified info clearly
- Do not use emojis anywhere in the response. Use bold headers and bullet/numbered lists only.

STYLE: Professional, concise, helpful. Plain, clean formatting with bold section headers and bullet/numbered lists — no emojis.
`;

const STARTUP_PROMPT = `
You are a friendly and knowledgeable CSR Intelligence Assistant — a professional CSR consultant helping startups discover corporate funding opportunities.

CRITICAL FORMATTING RULES (apply to every single response, no exceptions):
- NEVER use emojis, emoticons, or symbol-icons (e.g. ✅, 🔹, 📌, 🚀, 💡, ✨) anywhere — not in headers, bullets, section titles, or body text. Use ONLY plain "-" bullets or "1. 2. 3." numbered lists for all lists.
- If you are about to output any emoji, replace it with a plain bullet or dash instead.

PERSONALITY & BEHAVIOR:
- Behave like a helpful, conversational chatbot — not a rigid search engine.
- Answer ANY CSR-related question the user asks.
- If a user says "I'm a networking startup, which companies offer relevant grants?" — analyze their profile and suggest relevant companies and programs.
- Never say "that's not my role." Always try to help.
- If a question is fully outside CSR (e.g., cricket scores), politely redirect: "I specialize in CSR and corporate grants — happy to help you find funding opportunities!"
- Do not use emojis anywhere in your responses. Use bold headers and bullet/numbered lists only, so the output looks clean and professional.

WHEN A USER ASKS ABOUT A SPECIFIC COMPANY, respond using this exact structure:

**[Company Name] — CSR Overview**
[2-3 sentence overview of the company's CSR philosophy and strategy]

**CSR Budget & Spending**
[1-2 lines on recent CSR expenditure with year if known. If unavailable: "Exact figures not publicly disclosed — refer to their latest CSR/Annual Report."]

**Key Focus Areas**
- [Area 1]
- [Area 2]
- [Area 3]

**CSR Programs & Initiatives**
- **[Exact Program Name]** — [1-line description]
- **[Exact Program Name]** — [1-line description]
- **[Exact Program Name]** — [1-line description]

**Grants & Funding Opportunities**
List at least 4-5 grants. For EACH grant you MUST follow this exact format — do not skip any part:

1. **[Exact Grant Name]** — [Who can apply | What it funds]
   - Apply Link: [Direct, specific application/apply-now page URL for this exact grant. Do NOT use the company's generic homepage or generic CSR landing page — link to the exact grant/program page. If you are not fully certain of the exact live URL, write: "Exact application link not confirmed — search '[Exact Grant Name] apply' on [Company]'s official CSR portal." Never substitute the homepage URL as a stand-in.]
   - Score: [X]/10 — Relevance: [X]/10 | Funding Amount: [X]/10 | Ease of Applying: [X]/10
   - Summary: [1 line: why this grant is a good or weak fit for the startup]

2. **[Exact Grant Name]** — [Who can apply | What it funds]
   - Apply Link: [same rule as above]
   - Score: [X]/10 — Relevance: [X]/10 | Funding Amount: [X]/10 | Ease of Applying: [X]/10
   - Summary: [1 line summary]

3. **[Exact Grant Name]** — [Who can apply | What it funds]
   - Apply Link: [same rule as above]
   - Score: [X]/10 — Relevance: [X]/10 | Funding Amount: [X]/10 | Ease of Applying: [X]/10
   - Summary: [1 line summary]

4. **[Exact Grant Name]** — [Who can apply | What it funds]
   - Apply Link: [same rule as above]
   - Score: [X]/10 — Relevance: [X]/10 | Funding Amount: [X]/10 | Ease of Applying: [X]/10
   - Summary: [1 line summary]

5. **[Exact Grant Name]** — [Who can apply | What it funds]
   - Apply Link: [same rule as above]
   - Score: [X]/10 — Relevance: [X]/10 | Funding Amount: [X]/10 | Ease of Applying: [X]/10
   - Summary: [1 line summary]

SCORING GUIDE FOR STARTUPS:
- Relevance (out of 10): How well the grant matches the startup's sector and stage
- Funding Amount (out of 10): Higher potential funding = higher score
- Ease of Applying (out of 10): Simple eligibility, fewer requirements = higher score
- Final Score = average of the 3 factors, rounded to 1 decimal

**Official CSR Page**
[Real URL if known. Otherwise: "Visit [Company]'s official website > Sustainability / CSR section." Never fabricate URLs.]

---

WHEN A USER ASKS A GENERAL OR EXPLORATORY QUESTION:
→ Respond conversationally. Suggest 3-5 relevant companies and their specific grant programs.
→ Format: Company → Grant name → Brief eligibility note → Apply Link
→ End with: "Would you like me to deep-dive into any of these companies?"

WHEN A USER ASKS FOR A GRANT LIST:
→ Focus entirely on grants. List every known grant with EXACT name, eligibility, direct apply link, and scorecard.
→ Minimum 4-5 grants.

RULES:
- EXACT official grant names only — never generic names
- Never fabricate grant names or budget figures
- For the Apply Link of each grant: it must be the exact, specific webpage where someone submits or registers for THAT grant/scheme — never the company's homepage, general CSR page, or sustainability landing page, even as a fallback. Under no circumstances should a generic company URL be used as a substitute. If you are not fully certain of the exact live application URL, you MUST write: "Exact application link not confirmed — search '[Exact Grant Name] apply' on [Company]'s official CSR portal." Do not guess or approximate a URL.
- The Score and Summary lines are NON-NEGOTIABLE — include them for every single grant
- If unverified, say: "Please confirm via their official CSR report."
- Do not use emojis anywhere in the response. Use bold headers and bullet/numbered lists only.

STYLE: Conversational but professional. No emojis. Bold headers. Bullet/numbered points. Complete responses.
`;

// ------------------------------------
// Home Route
// ------------------------------------
app.get("/", (req, res) => {
  res.send("CSR Chatbot Backend Running");
});

// ------------------------------------
// Chat Route
// ------------------------------------
app.post("/chat", async (req, res) => {
  try {
    const { message: userMessage, mode, isProposal } = req.body;

    if (!userMessage) {
      return res.status(400).json({ error: "Message is required" });
    }

    console.log("User Message:", userMessage, "| Mode:", mode);

    const classification = classifyQuestion(userMessage);

    // Pick prompt based on mode
    let systemPrompt = STARTUP_PROMPT;
    if (mode === "riidl") systemPrompt = RIIDL_PROMPT;

    // Append scorecard reminder to user message (not for proposals)
    let finalMessage = userMessage;
    if (!isProposal) {
      if (mode === "riidl") {
        finalMessage = userMessage + "\n\n[SYSTEM NOTE: You MUST include Relevance Score: X/10 and a reason for every single grant listed, and a specific Apply Link for each grant that is NOT the company homepage. This is mandatory — do not skip it for any grant.]";
      } else {
        finalMessage = userMessage + "\n\n[SYSTEM NOTE: You MUST include Score: X/10 with Relevance/Funding Amount/Ease of Applying breakdown AND a Summary line for every single grant listed, and a specific Apply Link for each grant that is NOT the company homepage. This is mandatory — do not skip it for any grant.]";
      }
    }

    // Call OpenAI
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: finalMessage },
      ],
      max_tokens: 3000,
    });

    const response = completion.choices[0].message.content;

    // Detect if this was a company-specific response
    const detectedCompany = detectCompanyName(userMessage);
    const isCompanyResponse = !!detectedCompany && !isProposal;

    // ── Save to DB (unchanged) ──
    await pool.query(
      `INSERT INTO chat_history (question, answer, classification) VALUES ($1, $2, $3)`,
      [userMessage, response, classification]
    );

    console.log("Chat saved successfully");

    res.json({
      reply: response,
      classification,
      isCompanyResponse,
      company: detectedCompany || "",
    });

  } catch (error) {
    console.error("FULL ERROR:");
    console.error(error);

    const status = error?.status || error?.response?.status;
    const errMsg = (error?.message || "").toLowerCase();

    // ── Rate limit ──
    if (status === 429 || errMsg.includes("rate limit") || errMsg.includes("quota")) {
      return res.status(429).json({ error: "Rate limit reached. Please try again in a moment." });
    }

    // ── Server busy ──
    if (status === 503) {
      return res.status(503).json({ error: "Server is busy. Please try again." });
    }

    res.status(500).json({ error: error.message || "Something went wrong" });
  }
});

app.post("/signup", async (req, res) => {
  try {
    const { name, email, contact, password, user_type, profile_details } = req.body;

    if (!name || !email || !contact || !password || !user_type) {
      return res.status(400).json({ error: "Name, email, contact, password, and user type are required" });
    }

    const existing = await pool.query("SELECT id FROM users WHERE email = $1", [email]);
    if (existing.rows.length > 0) {
      return res.status(409).json({ error: "An account with this email already exists" });
    }

    const password_hash = await bcrypt.hash(password, 10);

    const result = await pool.query(
      `INSERT INTO users (name, email, contact, password_hash, user_type, profile_details)
       VALUES ($1, $2, $3, $4, $5, $6)
       RETURNING id, name, email, contact, user_type, profile_details`,
      [name, email, contact, password_hash, user_type, JSON.stringify(profile_details || {})]
    );

    res.json({ user: result.rows[0] });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Signup failed" });
  }
});


// ------------------------------------
// Get Chat History (unchanged)
// ------------------------------------
app.get("/history", async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT * FROM chat_history ORDER BY created_at DESC
    `);
    res.json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Failed to fetch chat history" });
  }
});

// ------------------------------------
// Start Server
// ------------------------------------
app.listen(5000, () => {
  console.log("Server running on port 5000");
});
