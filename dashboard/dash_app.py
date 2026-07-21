"""
CSR India — Live CSR & Philanthropy Dashboard
Data: CSR_Report_2026-05-22.csv (FY 2023-24)
Extended with: Login/Sign Up placeholders + embedded React Chatbot popup
"""

import os
import dash
import pandas as pd
import numpy as np
import requests
from dash import Dash, dcc, html, Input, Output, State, ALL, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression

# ── CHATBOT (React app) ────────────────────────────────────────────────────
# Your React chatbot runs standalone (npm run dev). Point this at its URL.
CHATBOT_URL = os.environ.get("CSR_CHATBOT_URL", "http://localhost:5173")

# Your Node.js backend (server.js) — used for signup/login API calls
API_URL = os.environ.get("CSR_API_URL", "http://localhost:5000")

# ── DESIGN TOKENS (accent colors — shared across both themes) ─────────────
EMERALD   = "#22D87A"
EMERALD_D = "#1AB868"
AMBER     = "#FBBF24"
CRIMSON   = "#F45B5B"
BLUE      = "#4F8EF7"
INDIGO    = "#4F8EF7"
PURPLE    = "#B78CF7"
CYAN      = "#14CFC4"
WHITE     = "#FFFFFF"
FONT      = "-apple-system, BlinkMacSystemFont, Inter, Segoe UI, sans-serif"

SEC_COLORS = [BLUE, EMERALD, CYAN, AMBER, INDIGO, PURPLE, CRIMSON,
              "#10B981", "#F59E0B", "#EC4899", "#64748B", "#1E293B"]

THEME_CHART = {
    "dark": dict(
        grid="rgba(99,140,255,0.1)", tick="#7E92B8", legend="#DDE6FA",
        hover_bg="#111E35", hover_text="#DDE6FA", line="#111E35", ink="#DDE6FA",
        map_scale=[[0.0, "#0A1830"], [0.1, "#0D2E22"], [0.3, "#146B4A"],
                   [0.6, "#22D87A"], [0.8, "#5FE8A8"], [1.0, "#A8F4CE"]],
    ),
    "light": dict(
        grid="rgba(0,0,0,0.07)", tick="#4A5E80", legend="#0D1628",
        hover_bg="#0D1628", hover_text="#FFFFFF", line="#FFFFFF", ink="#0D1628",
        map_scale=[[0.0, "#E7F5EC"], [0.2, "#A9E6C6"], [0.45, "#5FCB9C"],
                   [0.7, "#16A34A"], [1.0, "#0B5A2C"]],
    ),
}


def tc(theme):
    return THEME_CHART.get(theme, THEME_CHART["dark"])


THEME_PAGE = {
    "dark": dict(page_bg="#08101F", card_bg="#111E35", text="#DDE6FA",
                 subtext="#7E92B8", heading="#DDE6FA", border="1px solid rgba(99,140,255,0.1)",
                 card_border="1px solid rgba(99,140,255,0.1)"),
    "light": dict(page_bg="#F0F4FC", card_bg="#FFFFFF", text="#0D1628",
                  subtext="#4A5E80", heading="#0D1628", border="1px solid rgba(0,0,0,0.07)",
                  card_border="1px solid rgba(0,0,0,0.07)"),
}


def tp(theme):
    return THEME_PAGE.get(theme, THEME_PAGE["dark"])


# ── SIGNUP FORM OPTIONS ─────────────────────────────────────────────────────
USER_TYPES = [
    {"label": "Startup", "value": "startup"},
    {"label": "Corporate", "value": "corporate"},
    {"label": "NGO", "value": "ngo"},
    {"label": "Incubator", "value": "incubator"},
    {"label": "Innovation Cell / Innovator", "value": "innovation"},
    {"label": "Others", "value": "others"},
]

INDUSTRY_OPTIONS = [
    "Healthcare", "EdTech", "FinTech", "AgriTech", "CleanTech", "BioTech",
    "AI/ML", "Manufacturing", "E-commerce/Retail", "Logistics",
    "Media & Entertainment", "Real Estate & Construction", "Automotive",
    "Telecom", "Energy & Power", "Aerospace & Defence", "Textiles & Apparel",
    "Food & Beverage", "Travel & Hospitality", "Other",
]

STARTUP_STAGE_OPTIONS = [
    "No Revenue (Idea Stage)", "Pre-Revenue (MVP Built)", "Early Revenue",
    "Growth Stage", "Scaling", "Profitable/Mature",
]

CSR_THEME_OPTIONS = [
    "Education", "Healthcare", "Environment & Sustainability", "Rural Development",
    "Women Empowerment & Gender Equality", "Skill Development & Livelihood",
    "Sports", "Heritage & Culture", "Technology & Innovation",
    "Poverty Alleviation", "Disaster Relief",
]

FUNDING_TO_WHOM_OPTIONS = [
    "Startups", "NGOs", "Incubators", "Educational Institutions",
    "Individuals", "Government Bodies", "Others",
]

# Uses the same sector labels already present in your CSV data (set below, after data loads)
CSR_FUNDING_SECTOR_OPTIONS = []

# CSR Focus Areas — used as a checklist (12 options + Other)
CSR_FOCUS_AREA_OPTIONS = [
    "Education", "Healthcare & Nutrition", "Environment & Sustainability",
    "Rural Development", "Women Empowerment & Gender Equality",
    "Skill Development & Livelihood", "Sports", "Heritage & Culture",
    "Technology & Innovation", "Poverty Alleviation", "Disaster Relief",
    "Water, Sanitation & Hygiene (WASH)", "Other",
]

CSR_DONATION_PRIORITY_OPTIONS = [
    "NGOs", "R&D", "Incubators", "Infrastructure", "Others",
]

INCUBATOR_TYPE_OPTIONS = ["Government", "Private", "Academic", "NGO-backed"]

NGO_TYPE_OPTIONS = [
    "Trust", "Society", "Section 8 Company", "Foundation", "Other",
]

GEOGRAPHIC_REACH_OPTIONS = ["North", "West", "South", "East", "Central", "Pan India"]

REQUIRED_DOCS_OPTIONS = [
    "CSR Form", "80G Certificate", "12A Certificate", "MOM (Memorandum of Meeting)",
    "AOA (Articles of Association)", "Incorporation Certificate", "FCRA Registration",
    "PAN Registration No.",
]


# ── LOAD DATA ───────────────────────────────────────────────────────────────
# TODO tomorrow: swap this line for her/your confirmed Excel file, e.g.
#   df = pd.read_excel("CSR_Report.xlsx", sheet_name=0)
DATA_PATH = os.environ.get("CSR_DATA_PATH", "CSR_Report_CLEANED.csv")

print("Loading CSR data …")
df = pd.read_csv(DATA_PATH, skiprows=1)
# Source file's real headers (row 2): Company Name, Financial Year, PSU/Non-PSU,
# CSR State, CSR Development Sector, CSR Sub Development, Project Amount Spent
# Renaming by position to the short names the rest of the code uses below:
df.columns = ["Company", "FY", "PSU_Type", "State", "Sector", "SubSector", "Amount"]
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df = df[df["Amount"] > 0].copy()
print(f"Loaded {len(df):,} records | Total: ₹{df['Amount'].sum():,.1f} Cr")

TOTAL      = df["Amount"].sum()
PSU_SPEND  = df[df["PSU_Type"] == "PSU"]["Amount"].sum()
PRIV_SPEND = df[df["PSU_Type"] == "Non-PSU"]["Amount"].sum()
CO_COUNT   = df["Company"].nunique()

SECTOR_SHORT = {
    "Education, Differently Abled, Livelihood": "Education & Livelihood",
    "Health, Eradicating Hunger, Poverty And Malnutrition, Safe Drinking Water , Sanitation": "Health & Nutrition",
    "Environment, Animal Welfare, Conservation Of Resources": "Environment",
    "Gender Equality , Women Empowerment , Old Age Homes , Reducing Inequalities": "Gender & Equality",
    "Rural Development": "Rural Development",
    "NEC/Not mentioned": "Other / NEC",
    "Prime Minister's National Relief Fund": "PM Relief Fund",
    "Encouraging Sports": "Sports",
    "Heritage Art And Culture": "Heritage & Culture",
    "Any Other Fund": "Other Funds",
    "Other Sectors ( Technology Incubator And Benefits To Armed Forces And Admin Overheads )": "Technology / Defence",
    "Swachh Bharat Kosh": "Swachh Bharat",
    "Slum area development": "Slum Development",
    "Clean Ganga Fund": "Clean Ganga",
}

STATE_FIX = {
    "Andaman And Nicobar": "Andaman and Nicobar", "Orissa": "Odisha",
    "Pondicherry": "Puducherry", "Jammu & Kashmir": "Jammu and Kashmir",
    "PAN India": None, "PAN India (Other Centralized Funds)": None,
    "Dadra And Nagar Haveli": "Dadra and Nagar Haveli and Daman and Diu",
}

sec_spend = df.groupby("Sector")["Amount"].sum().sort_values(ascending=False).reset_index()
sec_spend["Label"] = sec_spend["Sector"].map(SECTOR_SHORT).fillna(sec_spend["Sector"].str[:30])
CSR_FUNDING_SECTOR_OPTIONS.extend(sec_spend["Label"].tolist())

sub_spend = df.groupby("SubSector")["Amount"].sum().sort_values(ascending=False).head(12).reset_index()
co_top    = df.groupby("Company")["Amount"].sum().sort_values(ascending=False).head(20).reset_index()

state_df = df.groupby("State")["Amount"].sum().reset_index().rename(columns={"Amount": "Spend"})
state_df["Name"] = state_df["State"].replace(STATE_FIX)
state_df = state_df[state_df["Name"].notna()]

TOP_COS = df.groupby("Company")["Amount"].sum().sort_values(ascending=False).head(60).index.tolist()

# ML trend simulation
np.random.seed(42)
FY_LABELS  = ["FY17", "FY18", "FY19", "FY20", "FY21", "FY22", "FY23", "FY24"]
FY_YEARS   = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
P_FACTORS  = [0.55, 0.62, 0.70, 0.75, 0.80, 0.87, 0.93, 1.00]
A_FACTORS  = [0.50, 0.57, 0.64, 0.66, 0.73, 0.80, 0.88, 0.96]
PRESCRIBED = [TOTAL * f for f in P_FACTORS]
ACTUAL     = [TOTAL * f for f in A_FACTORS]

X     = np.array(FY_YEARS).reshape(-1, 1)
poly  = PolynomialFeatures(degree=2)
Xp    = poly.fit_transform(X)
model = LinearRegression().fit(Xp, PRESCRIBED)

FC_YEARS  = [2025, 2026, 2027, 2028, 2029, 2030]
FC_LABELS = ["FY25", "FY26", "FY27", "FY28", "FY29", "FY30"]
FC_VALS   = model.predict(poly.transform(np.array(FC_YEARS).reshape(-1, 1)))
FC_UPPER  = FC_VALS * 1.08
FC_LOWER  = FC_VALS * 0.92


# ── CHART BUILDERS (all theme-aware) ────────────────────────────────────────

def base_layout(theme="dark", h=320, margin=None, **extra):
    c = tc(theme)
    m = margin or dict(l=10, r=10, t=30, b=10)
    lo = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=c["legend"], size=11),
        margin=m, height=h,
        xaxis=dict(gridcolor=c["grid"], zerolinecolor=c["grid"],
                   tickfont=dict(color=c["tick"], size=10), linecolor=c["grid"]),
        yaxis=dict(gridcolor=c["grid"], zerolinecolor=c["grid"],
                   tickfont=dict(color=c["tick"], size=10), linecolor=c["grid"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["legend"], size=9)),
        hoverlabel=dict(bgcolor=c["hover_bg"], font=dict(color=c["hover_text"], size=10)),
    )
    lo.update(extra)
    return lo


def make_heatmap(theme="dark"):
    c = tc(theme)
    fig = go.Figure(go.Choropleth(
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey="properties.ST_NM",
        locations=state_df["Name"],
        z=state_df["Spend"],
        colorscale=c["map_scale"],
        marker_line_color=c["line"], marker_line_width=0.8,
        colorbar=dict(thickness=10, len=0.7, x=1.01,
                      title=dict(text="₹ Cr", font=dict(color=c["legend"], size=9)),
                      tickfont=dict(color=c["tick"], size=9), bgcolor="rgba(0,0,0,0)"),
        hovertemplate="<b>%{location}</b><br>CSR Spend: ₹%{z:,.1f} Cr<extra></extra>",
        name="",
    ))
    fig.update_geos(visible=False, fitbounds="locations",
                    bgcolor="rgba(0,0,0,0)", showframe=False, showcountries=False)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=c["legend"], size=11),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=0, b=0), height=320,
        hoverlabel=dict(bgcolor=c["hover_bg"], font=dict(color=c["hover_text"], size=10)),
    )
    return fig


def make_trend(theme="dark"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=FC_LABELS + FC_LABELS[::-1],
        y=list(FC_UPPER) + list(FC_LOWER[::-1]),
        fill="toself", fillcolor="rgba(5,150,105,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip", name="CAGR Band ±8%", showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=FC_LABELS, y=FC_VALS, mode="lines+markers",
        line=dict(color=EMERALD, width=2, dash="dot"),
        marker=dict(size=5, color=EMERALD),
        name="ML Forecast (Poly Reg.)",
        hovertemplate="<b>%{x}</b><br>Forecast: ₹%{y:,.0f} Cr<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=FY_LABELS, y=PRESCRIBED, mode="lines+markers",
        line=dict(color=EMERALD, width=2.5),
        marker=dict(size=6, color=EMERALD),
        name="Prescribed Commitment",
        hovertemplate="<b>%{x}</b><br>Prescribed: ₹%{y:,.0f} Cr<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=FY_LABELS, y=ACTUAL, mode="lines+markers",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=6, color=BLUE),
        name="Actual Outflow",
        hovertemplate="<b>%{x}</b><br>Actual: ₹%{y:,.0f} Cr<extra></extra>",
    ))
    c = tc(theme)
    fig.add_vline(x="FY24", line_dash="dash", line_color=c["grid"], line_width=1)
    fig.add_annotation(x="FY25", y=max(FC_VALS) * 1.06,
                       text="ML Forecast →", font=dict(color=EMERALD, size=9), showarrow=False)

    lo = base_layout(theme, h=310, margin=dict(l=10, r=10, t=10, b=40))
    lo["yaxis"].update(title="₹ Crore", tickformat=",.0f")
    lo["legend"] = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["legend"], size=9),
                        orientation="h", y=-0.18, x=0)
    lo["hovermode"] = "x unified"
    fig.update_layout(**lo)
    return fig


def make_sector_bars(theme="dark"):
    c = tc(theme)
    ds = sec_spend.head(10)
    colors = SEC_COLORS[:len(ds)]
    fig = go.Figure(go.Bar(
        y=ds["Label"], x=ds["Amount"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"₹{v:,.0f} Cr" for v in ds["Amount"]],
        textposition="outside",
        textfont=dict(color=c["legend"], size=9),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.1f} Cr<extra></extra>",
    ))
    lo = base_layout(theme, h=320, margin=dict(l=10, r=90, t=10, b=10))
    lo["xaxis"].update(title="₹ Crore", tickformat=",.0f")
    lo["yaxis"].update(title=None, autorange="reversed", tickfont=dict(color=c["legend"], size=9))
    lo["bargap"] = 0.28
    fig.update_layout(**lo)
    return fig


def make_psu_donut(theme="dark"):
    c = tc(theme)
    fig = go.Figure(go.Pie(
        labels=["Non-PSU (Private)", "PSU (Public)"],
        values=[PRIV_SPEND, PSU_SPEND],
        hole=0.62,
        marker=dict(colors=[EMERALD, BLUE], line=dict(color=c["line"], width=2)),
        textinfo="label+percent",
        textfont=dict(size=10, color=WHITE),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} Cr  (%{percent})<extra></extra>",
        pull=[0.03, 0],
    ))
    fig.add_annotation(text=f"₹{TOTAL/1000:.1f}K Cr",
                       x=0.5, y=0.56, showarrow=False,
                       font=dict(size=14, color=c["ink"], family=FONT))
    fig.add_annotation(text="Total FY24",
                       x=0.5, y=0.44, showarrow=False,
                       font=dict(size=9, color=c["legend"], family=FONT))
    lo = base_layout(theme, h=310, margin=dict(l=10, r=80, t=10, b=10))
    lo["showlegend"] = True
    lo["legend"] = dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["legend"], size=9),
                        orientation="v", x=1.05, y=0.5)
    fig.update_layout(**lo)
    return fig


def make_treemap(theme="dark"):
    c = tc(theme)
    ds = sub_spend.copy()
    fig = go.Figure(go.Treemap(
        labels=ds["SubSector"].str[:28].tolist(),
        parents=[""] * len(ds),
        values=ds["Amount"].tolist(),
        marker=dict(colors=SEC_COLORS[:len(ds)],
                    line=dict(width=1.5, color=c["line"])),
        texttemplate="<b>%{label}</b><br>₹%{value:,.0f} Cr",
        textfont=dict(size=10, color=WHITE),
        hovertemplate="<b>%{label}</b><br>₹%{value:,.1f} Cr<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=c["legend"], size=11),
        margin=dict(l=0, r=0, t=0, b=0), height=310,
        hoverlabel=dict(bgcolor=c["hover_bg"], font=dict(color=c["hover_text"], size=10)),
    )
    return fig


def make_co_chart(company="HDFC BANK LIMITED", theme="dark"):
    c = tc(theme)
    co_df = df[df["Company"] == company]
    if co_df.empty:
        co_df = df[df["Company"].str.contains(company[:10], case=False, na=False)]
    subs = co_df.groupby("SubSector")["Amount"].sum().sort_values(ascending=False).head(8)

    fig = go.Figure()
    for i, (sub, amt) in enumerate(subs.items()):
        fig.add_trace(go.Bar(
            name=sub[:28], x=[sub[:22]], y=[amt],
            marker_color=SEC_COLORS[i % len(SEC_COLORS)],
            hovertemplate=f"<b>{sub}</b><br>₹{amt:,.2f} Cr<extra></extra>",
        ))

    total_co = co_df["Amount"].sum()
    states = co_df["State"].nunique()
    lo = base_layout(theme, h=260, margin=dict(l=10, r=10, t=36, b=10))
    lo["barmode"] = "group"
    lo["xaxis"].update(title=None, tickangle=-18, tickfont=dict(size=9, color=c["tick"]))
    lo["yaxis"].update(title="₹ Crore")
    lo["showlegend"] = False
    lo["title"] = dict(text=f"{company[:38]}  ·  ₹{total_co:,.1f} Cr  ·  {states} States",
                       font=dict(color=c["legend"], size=10), x=0, xanchor="left")
    fig.update_layout(**lo)
    return fig, total_co, states


def make_top_co(theme="dark", n=15):
    """Horizontal bar chart of the top N companies by total CSR spend."""
    c = tc(theme)
    ds = co_top.head(n)
    colors = [EMERALD if i < 3 else BLUE for i in range(len(ds))]
    fig = go.Figure(go.Bar(
        y=ds["Company"].str[:32], x=ds["Amount"], orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"₹{v:,.0f} Cr" for v in ds["Amount"]],
        textposition="outside",
        textfont=dict(color=c["legend"], size=9),
        hovertemplate="<b>%{y}</b><br>₹%{x:,.1f} Cr<extra></extra>",
    ))
    lo = base_layout(theme, h=420, margin=dict(l=10, r=90, t=10, b=10))
    lo["xaxis"].update(title="₹ Crore", tickformat=",.0f")
    lo["yaxis"].update(title=None, autorange="reversed", tickfont=dict(color=c["legend"], size=9))
    lo["bargap"] = 0.22
    fig.update_layout(**lo)
    return fig


# ── APP SETUP ────────────────────────────────────────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.title = "CSR India — Live Dashboard"
server = app.server


def kpi_card(label, value, color=EMERALD, theme="dark", card_id=None):
    p = tp(theme)
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, style={
                "fontSize": "10.5px", "fontWeight": "600", "color": p["subtext"],
                "textTransform": "uppercase", "letterSpacing": "0.7px", "marginBottom": "8px",
            }),
            html.Div(value, style={"fontSize": "26px", "fontWeight": "800", "letterSpacing": "-0.6px", "color": color}),
        ]),
        id=card_id,
        style={"backgroundColor": p["card_bg"], "border": p["card_border"], "borderRadius": "12px",
               "padding": "4px 2px"},
    )


def chart_card(title, graph, theme="dark", card_id=None):
    p = tp(theme)
    return dbc.Card(
        dbc.CardBody([
            html.Div(title, style={
                "fontSize": "12.5px", "fontWeight": "700", "color": p["text"], "marginBottom": "2px",
            }),
            graph,
        ]),
        id=card_id,
        style={"backgroundColor": p["card_bg"], "border": p["card_border"], "borderRadius": "12px"},
    )


# ── LAYOUT ───────────────────────────────────────────────────────────────────
app.layout = html.Div([

    dcc.Store(id="theme-store", data="dark"),

    # ── Top bar: logo + title + theme toggle + auth area ──
    html.Div([
        html.Div([
            html.Div(
                "◈",
                style={
                    "width": "34px", "height": "34px", "borderRadius": "9px",
                    "background": f"linear-gradient(135deg, {BLUE} 0%, {CYAN} 100%)",
                    "display": "flex", "alignItems": "center", "justifyContent": "center",
                    "fontSize": "17px", "color": "#fff", "flexShrink": "0",
                },
            ),
            html.Div([
                html.H3("CSR India — Live Dashboard", id="page-title", style={"margin": "0"}),
                html.P("FY 2023-24 CSR & Philanthropy Overview", id="page-subtitle", style={"margin": "0"}),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
        html.Div([
            html.Div([
                html.Div(style={
                    "width": "6px", "height": "6px", "borderRadius": "50%",
                    "backgroundColor": EMERALD, "marginRight": "6px",
                }),
                "MCA Live",
            ], style={
                "display": "flex", "alignItems": "center", "fontSize": "10.5px", "fontWeight": "700",
                "color": EMERALD, "backgroundColor": "rgba(34,216,122,0.12)",
                "border": "1px solid rgba(34,216,122,0.3)", "borderRadius": "999px",
                "padding": "4px 12px", "marginRight": "12px", "letterSpacing": "0.2px",
            }),
            dbc.Button("☀️  Light Mode", id="theme-toggle-btn", color="secondary", outline=True,
                       className="me-2", style={"borderRadius": "999px", "fontWeight": "500"}),
            html.Div([
                html.Div([
                    dbc.Button("Login", id="login-btn", color="light", outline=True, className="me-2"),
                    dbc.Button("Sign Up", id="signup-btn", color="success"),
                ], id="auth-logged-out", style={"display": "flex", "alignItems": "center"}),
                html.Div([
                    html.Span(id="auth-user-name", style={"marginRight": "14px", "fontWeight": "600"}),
                    dbc.Button("Logout", id="logout-btn", color="light", outline=True, size="sm"),
                ], id="auth-logged-in", style={"display": "none", "alignItems": "center"}),
            ]),
        ], style={"display": "flex", "alignItems": "center"}),
    ], id="topbar", style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "18px 28px",
    }),

    # ── Floating chatbot bubble (bottom-right) ──
    html.Div(
        "💬",
        id="open-chatbot-btn",
        n_clicks=0,
        style={
            "position": "fixed", "bottom": "28px", "right": "28px",
            "width": "62px", "height": "62px", "borderRadius": "50%",
            "background": f"linear-gradient(135deg, {EMERALD} 0%, {EMERALD_D} 100%)",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "fontSize": "28px", "cursor": "pointer", "zIndex": "2000",
            "boxShadow": "0 6px 20px rgba(5,150,105,0.45)",
            "border": "none", "userSelect": "none",
        },
        title="Chat with our CSR Assistant",
    ),

    # ── KPI row ──
    dbc.Row([
        dbc.Col(kpi_card("Total CSR Spend (FY24)", f"₹{TOTAL:,.0f} Cr", card_id="kpi-total"), md=3),
        dbc.Col(kpi_card("PSU Spend", f"₹{PSU_SPEND:,.0f} Cr", BLUE, card_id="kpi-psu"), md=3),
        dbc.Col(kpi_card("Private Spend", f"₹{PRIV_SPEND:,.0f} Cr", EMERALD, card_id="kpi-priv"), md=3),
        dbc.Col(kpi_card("Companies Reporting", f"{CO_COUNT:,}", AMBER, card_id="kpi-co"), md=3),
    ], style={"padding": "20px 28px 0 28px"}),

    # ── Charts grid ──
    dbc.Row([
        dbc.Col(chart_card("CSR Spend by State",
            dcc.Graph(id="heatmap-graph", figure=make_heatmap("dark"), config={"displayModeBar": False}),
            card_id="card-heatmap"), md=6),

        dbc.Col(chart_card("Spend Trend & ML Forecast",
            dcc.Graph(id="trend-graph", figure=make_trend("dark"), config={"displayModeBar": False}),
            card_id="card-trend"), md=6),
    ], style={"padding": "20px 28px 0 28px"}),

    dbc.Row([
        dbc.Col(chart_card("Top Sectors",
            dcc.Graph(id="sector-graph", figure=make_sector_bars("dark"), config={"displayModeBar": False}),
            card_id="card-sector"), md=4),

        dbc.Col(chart_card("PSU vs Private",
            dcc.Graph(id="donut-graph", figure=make_psu_donut("dark"), config={"displayModeBar": False}),
            card_id="card-donut"), md=4),

        dbc.Col(chart_card("Sub-Sector Breakdown",
            dcc.Graph(id="treemap-graph", figure=make_treemap("dark"), config={"displayModeBar": False}),
            card_id="card-treemap"), md=4),
    ], style={"padding": "20px 28px 0 28px"}),

    dbc.Row([
        dbc.Col(chart_card("Top 15 Companies by CSR Spend",
            dcc.Graph(id="topco-graph", figure=make_top_co("dark"), config={"displayModeBar": False}),
            card_id="card-topco"), md=6),

        dbc.Col(chart_card("Company Deep-Dive",
            html.Div([
                dcc.Dropdown(
                    id="company-dropdown",
                    options=[{"label": c[:45], "value": c} for c in TOP_COS],
                    value=TOP_COS[0] if TOP_COS else None,
                    style={"marginBottom": "10px", "color": "black"},
                ),
                dcc.Graph(id="company-graph", config={"displayModeBar": False}),
            ]),
            card_id="card-companydive"), md=6),
    ], style={"padding": "20px 28px 28px 28px"}),

    # ── Login modal (React iframe) ──
    dbc.Modal(
        [
            dbc.ModalHeader(close_button=True, style={"border": "none", "padding": "12px 16px"}),
            dbc.ModalBody(
                html.Iframe(
                    src=f"{CHATBOT_URL}?screen=login",
                    style={"width": "100%", "height": "100%", "border": "none"},
                ),
                style={"padding": "0", "height": "100%"},
            ),
        ],
        id="login-modal",
        fullscreen=True,
        is_open=False,
    ),

    # ── Sign Up modal (React iframe) ──
    dbc.Modal(
        [
            dbc.ModalHeader(close_button=True, style={"border": "none", "padding": "12px 16px"}),
            dbc.ModalBody(
                html.Iframe(
                    src=f"{CHATBOT_URL}?screen=signup",
                    style={"width": "100%", "height": "100%", "border": "none"},
                ),
                style={"padding": "0", "height": "100%"},
            ),
        ],
        id="signup-modal",
        fullscreen=True,
        is_open=False,
    ),

        # ── Chatbot popup modal (embeds your React app) ──
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("CSR Chatbot"), close_button=True),
            dbc.ModalBody(
                html.Iframe(
                    src=CHATBOT_URL,
                    style={"width": "100%", "height": "100%", "border": "none"},
                ),
                style={"padding": "0", "height": "100%"},
            ),
        ],
        id="chatbot-modal",
        fullscreen=True,
        is_open=False,
    ),

], id="page-root", style={"minHeight": "100vh", "fontFamily": FONT})


# ── CALLBACKS ────────────────────────────────────────────────────────────────

@app.callback(
    Output("signup-modal", "is_open"),
    Input("signup-btn", "n_clicks"),
    State("signup-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_signup_modal(n_clicks, is_open):
    return not is_open


@app.callback(
    Output("login-modal", "is_open"),
    Input("login-btn", "n_clicks"),
    State("login-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_login_modal(n_clicks, is_open):
    return not is_open


@app.callback(
    Output("chatbot-modal", "is_open"),
    Input("open-chatbot-btn", "n_clicks"),
    State("chatbot-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_chatbot(n_clicks, is_open):
    return not is_open


@app.callback(
    Output("theme-store", "data"),
    Input("theme-toggle-btn", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def flip_theme(n_clicks, current_theme):
    return "light" if current_theme == "dark" else "dark"


@app.callback(
    Output("company-graph", "figure"),
    Input("company-dropdown", "value"),
    Input("theme-store", "data"),
)
def update_company_chart(company, theme):
    if not company:
        return go.Figure()
    fig, _, _ = make_co_chart(company, theme)
    return fig


@app.callback(
    Output("page-root", "style"),
    Output("topbar", "style"),
    Output("page-title", "style"),
    Output("page-subtitle", "style"),
    Output("auth-user-name", "style"),
    Output("theme-toggle-btn", "children"),
    Output("kpi-total", "style"),
    Output("kpi-psu", "style"),
    Output("kpi-priv", "style"),
    Output("kpi-co", "style"),
    Output("card-heatmap", "style"),
    Output("card-trend", "style"),
    Output("card-sector", "style"),
    Output("card-donut", "style"),
    Output("card-treemap", "style"),
    Output("card-topco", "style"),
    Output("card-companydive", "style"),
    Output("heatmap-graph", "figure"),
    Output("trend-graph", "figure"),
    Output("sector-graph", "figure"),
    Output("donut-graph", "figure"),
    Output("treemap-graph", "figure"),
    Output("topco-graph", "figure"),
    Input("theme-store", "data"),
)
def apply_theme(theme):
    p = tp(theme)
    page_style = {"minHeight": "100vh", "fontFamily": FONT, "backgroundColor": p["page_bg"]}
    topbar_style = {
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "18px 28px", "backgroundColor": p["page_bg"], "borderBottom": p["border"],
    }
    title_style = {"margin": "0", "color": p["text"]}
    subtitle_style = {"margin": "0", "color": p["subtext"]}
    auth_name_style = {"marginRight": "14px", "fontWeight": "600", "color": p["text"]}
    card_style = {"backgroundColor": p["card_bg"], "border": p["card_border"], "borderRadius": "12px"}
    toggle_label = "☀️  Light Mode" if theme == "dark" else "🌙  Dark Mode"

    return (
        page_style, topbar_style, title_style, subtitle_style, auth_name_style, toggle_label,
        card_style, card_style, card_style, card_style,
        card_style, card_style, card_style, card_style, card_style, card_style, card_style,
        make_heatmap(theme), make_trend(theme), make_sector_bars(theme),
        make_psu_donut(theme), make_treemap(theme), make_top_co(theme),
    )


# ── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)