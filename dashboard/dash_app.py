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
EMERALD   = "#059669"
EMERALD_D = "#047857"
AMBER     = "#D97706"
CRIMSON   = "#DC2626"
BLUE      = "#2563EB"
INDIGO    = "#4F46E5"
PURPLE    = "#9333EA"
CYAN      = "#0891B2"
WHITE     = "#FFFFFF"
FONT      = "DM Sans, system-ui, sans-serif"

SEC_COLORS = [BLUE, EMERALD, CYAN, AMBER, INDIGO, PURPLE, CRIMSON,
              "#10B981", "#F59E0B", "#EC4899", "#64748B", "#1E293B"]

THEME_CHART = {
    "dark": dict(
        grid="#334155", tick="#94A3B8", legend="#CBD5E1",
        hover_bg="#1E293B", hover_text="#FFFFFF", line="#1E293B", ink="#FFFFFF",
        map_scale=[[0.0, "#0A2540"], [0.1, "#053D2B"], [0.3, "#065F46"],
                   [0.6, "#059669"], [0.8, "#34D399"], [1.0, "#6EE7B7"]],
    ),
    "light": dict(
        grid="#E2E8F0", tick="#64748B", legend="#334155",
        hover_bg="#0F172A", hover_text="#FFFFFF", line="#FFFFFF", ink="#0F172A",
        map_scale=[[0.0, "#E7F5EC"], [0.2, "#A9E6C6"], [0.45, "#5FCB9C"],
                   [0.7, "#10B981"], [1.0, "#065F46"]],
    ),
}


def tc(theme):
    return THEME_CHART.get(theme, THEME_CHART["dark"])


THEME_PAGE = {
    "dark": dict(page_bg="#0F172A", card_bg="#1E293B", text="#FFFFFF",
                 subtext="#94A3B8", heading="#CBD5E1", border="1px solid #1E293B"),
    "light": dict(page_bg="#F1F5F9", card_bg="#FFFFFF", text="#0F172A",
                  subtext="#475569", heading="#1E293B", border="1px solid #E2E8F0"),
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
            html.Div(label, style={"fontSize": "12px", "color": p["subtext"], "marginBottom": "4px"}),
            html.Div(value, style={"fontSize": "22px", "fontWeight": "700", "color": color}),
        ]),
        id=card_id,
        style={"backgroundColor": p["card_bg"], "border": "none", "borderRadius": "12px"},
    )


def chart_card(title, graph, theme="dark", card_id=None):
    p = tp(theme)
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, style={"color": p["heading"]}),
            graph,
        ]),
        id=card_id,
        style={"backgroundColor": p["card_bg"], "border": "none", "borderRadius": "12px"},
    )


# ── LAYOUT ───────────────────────────────────────────────────────────────────
app.layout = html.Div([

    dcc.Store(id="theme-store", data="dark"),
    dcc.Store(id="logged-in-user", data=None, storage_type="memory"),

    # ── Top bar: title + theme toggle + auth area ──
    html.Div([
        html.Div([
            html.H3("CSR India — Live Dashboard", id="page-title", style={"margin": "0"}),
            html.P("FY 2023-24 CSR & Philanthropy Overview", id="page-subtitle", style={"margin": "0"}),
        ]),
        html.Div([
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

    # ── Login popup modal ──
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Login"), close_button=True),
            dbc.ModalBody(
                html.Div([
                    dbc.Label("Email"),
                    dbc.Input(id="li-email", type="email", placeholder="you@example.com", className="mb-3"),

                    dbc.Label("Password"),
                    dbc.Input(id="li-password", type="password", placeholder="Your password", className="mb-3"),

                    dcc.Loading(
                        type="circle", color=EMERALD,
                        children=[
                            dbc.Button("Login", id="login-submit-btn", color="success", className="mt-2 w-100", size="lg"),
                            html.Div(id="login-submit-status", style={"marginTop": "14px"}),
                        ],
                    ),
                ], style={"maxWidth": "420px", "margin": "0 auto", "padding": "10px 8px 40px 8px"}),
            ),
        ],
        id="login-modal",
        fullscreen=True,
        is_open=False,
    ),

    # ── Sign Up popup modal ──
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Create your account"), close_button=True),
            dbc.ModalBody(
                html.Div([
                dbc.Label("Name"),
                dbc.Input(id="su-name", type="text", placeholder="Your full name", className="mb-1"),
                dbc.FormFeedback("Name is required.", id="su-name-feedback", type="invalid"),
                html.Div(style={"marginBottom": "12px"}),

                dbc.Label("Email"),
                dbc.Input(id="su-email", type="email", placeholder="you@example.com", className="mb-1"),
                dbc.FormFeedback("Enter a valid email address.", id="su-email-feedback", type="invalid"),
                html.Div(style={"marginBottom": "12px"}),

                dbc.Label("Contact Number"),
                dbc.Input(id="su-contact", type="text", placeholder="10-digit phone number", className="mb-1"),
                dbc.FormFeedback("Enter a valid 10-digit phone number.", id="su-contact-feedback", type="invalid"),
                html.Div(style={"marginBottom": "12px"}),

                dbc.Label("Password"),
                dbc.Input(id="su-password", type="password", placeholder="Choose a password (min 6 characters)", className="mb-1"),
                dbc.FormFeedback("Password should be at least 6 characters.", id="su-password-feedback", type="invalid"),
                html.Div(style={"marginBottom": "12px"}),

                dbc.Label("Who are you?"),
                dcc.Dropdown(id="su-user-type", options=USER_TYPES, placeholder="Select one",
                             style={"color": "black", "marginBottom": "18px"}),

                # ── Startup-specific fields ──
                html.Div([
                    html.H6("🚀 Startup Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Name of Startup"),
                    dbc.Input(id="su-startup-name", type="text", className="mb-3"),

                    dbc.Label("Industry"),
                    dcc.Dropdown(id="su-startup-industry",
                                 options=[{"label": i, "value": i} for i in INDUSTRY_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Domain"),
                    dbc.Input(id="su-startup-domain", type="text",
                              placeholder="e.g. B2B SaaS, D2C, Marketplace", className="mb-3"),

                    dbc.Label("Explain what your startup does"),
                    dbc.Textarea(id="su-startup-desc", style={"height": "100px"}, className="mb-3"),

                    dbc.Label("Have you registered your startup on DPIIT?"),
                    dbc.RadioItems(
                        id="su-startup-dpiit",
                        options=[{"label": "Yes", "value": "yes"}, {"label": "No", "value": "no"}],
                        inline=True, className="mb-3",
                    ),

                    dbc.Label("Year of Incorporation"),
                    dbc.Input(id="su-startup-year", type="text", placeholder="e.g. 2022", className="mb-1"),
                    dbc.FormFeedback("Enter a valid 4-digit year (1990–2026).", id="su-startup-year-feedback", type="invalid"),
                    html.Div(style={"marginBottom": "12px"}),

                    dbc.Label("Stage of Startup"),
                    dcc.Dropdown(id="su-startup-stage",
                                 options=[{"label": s, "value": s} for s in STARTUP_STAGE_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Pitch Deck / Startup Info (optional)"),
                    dbc.Input(id="su-startup-pitch-link", type="text",
                              placeholder="Google Drive / website link (optional)", className="mb-3"),
                ], id="startup-fields", style={
                    "display": "none", "backgroundColor": "rgba(5,150,105,0.06)",
                    "border": "1px solid rgba(5,150,105,0.25)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                # ── Corporate-specific fields ──
                html.Div([
                    html.H6("🏢 Corporate Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Name of Corporate"),
                    dbc.Input(id="su-corp-name", type="text", className="mb-3"),

                    dbc.Label("Industry"),
                    dcc.Dropdown(id="su-corp-industry",
                                 options=[{"label": i, "value": i} for i in INDUSTRY_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Domain"),
                    dbc.Input(id="su-corp-domain", type="text", className="mb-3"),

                    dbc.Label("CSR Funding Area (select all that apply)"),
                    dbc.Checklist(
                        id="su-corp-funding-area",
                        options=[{"label": a, "value": a} for a in CSR_FOCUS_AREA_OPTIONS],
                        className="mb-2",
                    ),
                    dbc.Input(id="su-corp-funding-area-other", type="text",
                              placeholder="Please specify", style={"display": "none"}, className="mb-3"),

                    dbc.Label("CSR Donation Priority"),
                    dcc.Dropdown(id="su-corp-donation-priority",
                                 options=[{"label": d, "value": d} for d in CSR_DONATION_PRIORITY_OPTIONS],
                                 style={"color": "black", "marginBottom": "10px"}),
                    dbc.Input(id="su-corp-donation-priority-other", type="text",
                              placeholder="Please specify", style={"display": "none"}, className="mb-3"),

                    dbc.Label("CSR Funding Sector"),
                    dcc.Dropdown(id="su-corp-sector",
                                 options=[{"label": s, "value": s} for s in CSR_FUNDING_SECTOR_OPTIONS],
                                 style={"color": "black", "marginBottom": "22px"}),

                    dbc.Label("CSR Funding Range"),
                    dcc.RangeSlider(
                        id="su-corp-range",
                        min=5, max=500, step=5, value=[5, 100],
                        marks={5: "₹5L", 50: "₹50L", 100: "₹1Cr", 250: "₹2.5Cr", 500: "₹5Cr+"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"marginBottom": "16px"}),
                ], id="corporate-fields", style={
                    "display": "none", "backgroundColor": "rgba(37,99,235,0.06)",
                    "border": "1px solid rgba(37,99,235,0.25)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                # ── Incubator-specific fields ──
                html.Div([
                    html.H6("🧪 Incubator Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Name of Incubator"),
                    dbc.Input(id="su-incub-name", type="text", className="mb-3"),

                    dbc.Label("Type of Incubator"),
                    dcc.Dropdown(id="su-incub-type",
                                 options=[{"label": t, "value": t} for t in INCUBATOR_TYPE_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Year of Establishment"),
                    dbc.Input(id="su-incub-year", type="text", placeholder="e.g. 2015", className="mb-3"),

                    dbc.Label("Location of Incubation"),
                    dbc.Input(id="su-incub-location", type="text", className="mb-3"),

                    dbc.Label("CSR Focus Area (select all that apply)"),
                    dbc.Checklist(
                        id="su-incub-focus",
                        options=[{"label": a, "value": a} for a in CSR_FOCUS_AREA_OPTIONS],
                        className="mb-2",
                    ),
                    dbc.Input(id="su-incub-focus-other", type="text",
                              placeholder="Please specify", style={"display": "none"}, className="mb-3"),

                    dbc.Label("Associate Corporate Partner / Funder"),
                    dbc.Input(id="su-incub-partner", type="text", className="mb-3"),

                    dbc.Label("Annual Revenue"),
                    dcc.RangeSlider(
                        id="su-incub-revenue", min=100, max=500, step=25, value=[100, 300],
                        marks={100: "₹1Cr", 200: "₹2Cr", 300: "₹3Cr", 400: "₹4Cr", 500: "₹5Cr+"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"marginBottom": "16px"}),

                    dbc.Label("Do you have the following documents?"),
                    dbc.Checklist(
                        id="su-incub-docs",
                        options=[{"label": d, "value": d} for d in REQUIRED_DOCS_OPTIONS],
                        className="mb-2",
                    ),
                    html.Div(id="su-incub-doc-warning"),
                ], id="incubator-fields", style={
                    "display": "none", "backgroundColor": "rgba(147,51,234,0.06)",
                    "border": "1px solid rgba(147,51,234,0.25)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                # ── NGO-specific fields ──
                html.Div([
                    html.H6("🤝 NGO Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Name of NGO"),
                    dbc.Input(id="su-ngo-name", type="text", className="mb-3"),

                    dbc.Label("Type of NGO"),
                    dcc.Dropdown(id="su-ngo-type",
                                 options=[{"label": t, "value": t} for t in NGO_TYPE_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Year of Establishment"),
                    dbc.Input(id="su-ngo-year", type="text", placeholder="e.g. 2010", className="mb-3"),

                    dbc.Label("Location of NGO"),
                    dbc.Input(id="su-ngo-location", type="text", className="mb-3"),

                    dbc.Label("CSR Focus Area (select all that apply)"),
                    dbc.Checklist(
                        id="su-ngo-focus",
                        options=[{"label": a, "value": a} for a in CSR_FOCUS_AREA_OPTIONS],
                        className="mb-2",
                    ),
                    dbc.Input(id="su-ngo-focus-other", type="text",
                              placeholder="Please specify", style={"display": "none"}, className="mb-3"),

                    dbc.Label("Associate Corporate Partner / Funder"),
                    dbc.Input(id="su-ngo-partner", type="text", className="mb-3"),

                    dbc.Label("Annual Revenue"),
                    dcc.RangeSlider(
                        id="su-ngo-revenue", min=100, max=500, step=25, value=[100, 300],
                        marks={100: "₹1Cr", 200: "₹2Cr", 300: "₹3Cr", 400: "₹4Cr", 500: "₹5Cr+"},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                    html.Div(style={"marginBottom": "16px"}),

                    dbc.Label("Geographical Reach"),
                    dcc.Dropdown(id="su-ngo-reach",
                                 options=[{"label": g, "value": g} for g in GEOGRAPHIC_REACH_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Do you have the following documents?"),
                    dbc.Checklist(
                        id="su-ngo-docs",
                        options=[{"label": d, "value": d} for d in REQUIRED_DOCS_OPTIONS],
                        className="mb-2",
                    ),
                    html.Div(id="su-ngo-doc-warning"),
                ], id="ngo-fields", style={
                    "display": "none", "backgroundColor": "rgba(217,119,6,0.06)",
                    "border": "1px solid rgba(217,119,6,0.25)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                # ── Innovation Cell / Innovator-specific fields ──
                html.Div([
                    html.H6("💡 Innovator Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Name of Innovator"),
                    dbc.Input(id="su-innov-name", type="text", className="mb-3"),

                    dbc.Label("Explain your research work"),
                    dbc.Textarea(id="su-innov-research", style={"height": "160px"}, className="mb-3"),
                ], id="innovation-fields", style={
                    "display": "none", "backgroundColor": "rgba(8,145,178,0.06)",
                    "border": "1px solid rgba(8,145,178,0.25)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                # ── Others-specific fields ──
                html.Div([
                    html.H6("📋 Organization Details", style={"marginBottom": "16px", "marginTop": "6px"}),
                    dbc.Label("Organization Name"),
                    dbc.Input(id="su-other-org-name", type="text", className="mb-3"),

                    dbc.Label("Organization Type"),
                    dbc.Input(id="su-other-org-type", type="text",
                              placeholder="e.g. Government Body, Academic Institution, Media", className="mb-3"),

                    dbc.Label("Brief Description"),
                    dbc.Textarea(id="su-other-description", style={"height": "100px"}, className="mb-3"),

                    dbc.Label("Area of Interest / Focus"),
                    dbc.Input(id="su-other-focus", type="text", className="mb-3"),
                ], id="others-fields", style={
                    "display": "none", "backgroundColor": "rgba(100,116,139,0.08)",
                    "border": "1px solid rgba(100,116,139,0.3)", "borderRadius": "12px",
                    "padding": "18px", "marginTop": "8px",
                }),

                dcc.Loading(
                    type="circle", color=EMERALD,
                    children=[
                        dbc.Button("Submit", id="signup-submit-btn", color="success", className="mt-2 w-100", size="lg"),
                        html.Div(id="signup-submit-status", style={"marginTop": "14px"}),
                        dbc.Button("Go to Login", id="signup-go-login-btn", color="primary", size="sm",
                                   style={"display": "none"}),
                    ],
                ),
                ], style={"maxWidth": "560px", "margin": "0 auto", "padding": "10px 8px 40px 8px"}),
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
    Output("su-name", "value"),
    Output("su-email", "value"),
    Output("su-contact", "value"),
    Output("su-password", "value"),
    Output("su-user-type", "value"),
    Output("su-startup-name", "value"),
    Output("su-startup-industry", "value"),
    Output("su-startup-domain", "value"),
    Output("su-startup-desc", "value"),
    Output("su-startup-dpiit", "value"),
    Output("su-startup-year", "value"),
    Output("su-startup-stage", "value"),
    Output("su-startup-pitch-link", "value"),
    Output("su-corp-name", "value"),
    Output("su-corp-industry", "value"),
    Output("su-corp-domain", "value"),
    Output("su-corp-funding-area", "value"),
    Output("su-corp-funding-area-other", "value"),
    Output("su-corp-donation-priority", "value"),
    Output("su-corp-donation-priority-other", "value"),
    Output("su-corp-sector", "value"),
    Output("su-corp-range", "value"),
    Output("su-incub-name", "value"),
    Output("su-incub-type", "value"),
    Output("su-incub-year", "value"),
    Output("su-incub-location", "value"),
    Output("su-incub-focus", "value"),
    Output("su-incub-focus-other", "value"),
    Output("su-incub-partner", "value"),
    Output("su-incub-revenue", "value"),
    Output("su-incub-docs", "value"),
    Output("su-ngo-name", "value"),
    Output("su-ngo-type", "value"),
    Output("su-ngo-year", "value"),
    Output("su-ngo-location", "value"),
    Output("su-ngo-focus", "value"),
    Output("su-ngo-focus-other", "value"),
    Output("su-ngo-partner", "value"),
    Output("su-ngo-revenue", "value"),
    Output("su-ngo-reach", "value"),
    Output("su-ngo-docs", "value"),
    Output("su-innov-name", "value"),
    Output("su-innov-research", "value"),
    Output("su-other-org-name", "value"),
    Output("su-other-org-type", "value"),
    Output("su-other-description", "value"),
    Output("su-other-focus", "value"),
    Output("signup-submit-status", "children", allow_duplicate=True),
    Output("signup-go-login-btn", "style", allow_duplicate=True),
    Input("signup-modal", "is_open"),
    prevent_initial_call=True,
)
def reset_signup_form(is_open):
    if not is_open:
        raise dash.exceptions.PreventUpdate
    # Every field reset to blank; checklists to [], the two range sliders to their defaults
    return (
        None, None, None, None, None,                     # common
        None, None, None, None, None, None, None, None,   # startup
        None, None, None, [], None, None, None, None, [5, 100],  # corporate
        None, None, None, None, [], None, None, [100, 300], [],  # incubator
        None, None, None, None, [], None, None, [100, 300], None, [],  # ngo
        None, None,                                        # innovation
        None, None, None, None,                            # others
        "", {"display": "none"},                           # clear leftover status/button
    )


@app.callback(
    Output("login-modal", "is_open"),
    Output("signup-modal", "is_open", allow_duplicate=True),
    Input("login-btn", "n_clicks"),
    Input("signup-go-login-btn", "n_clicks"),
    State("login-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_login_modal(login_btn_clicks, go_login_clicks, is_open):
    triggered = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if triggered == "signup-go-login-btn":
        return True, False  # open login, close signup
    return not is_open, dash.no_update


@app.callback(
    Output("auth-logged-out", "style"),
    Output("auth-logged-in", "style"),
    Output("auth-user-name", "children"),
    Input("logged-in-user", "data"),
)
def render_auth_area(user):
    if user:
        display_name = user.get("name", "User")
        return {"display": "none"}, {"display": "flex", "alignItems": "center"}, f"Hi, {display_name}"
    return {"display": "flex", "alignItems": "center"}, {"display": "none"}, ""


@app.callback(
    Output("logged-in-user", "data"),
    Output("login-submit-status", "children"),
    Output("login-modal", "is_open", allow_duplicate=True),
    Output("li-email", "value"),
    Output("li-password", "value"),
    Input("login-submit-btn", "n_clicks"),
    State("li-email", "value"),
    State("li-password", "value"),
    prevent_initial_call=True,
)
def submit_login(n_clicks, email, password):
    import re

    no_op = (dash.no_update, dash.no_update, dash.no_update)

    if not email or not password:
        return (dash.no_update, dbc.Alert("Please enter both email and password.", color="danger")) + no_op

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return (dash.no_update, dbc.Alert("Please enter a valid email address.", color="danger")) + no_op

    try:
        resp = requests.post(f"{API_URL}/login", json={"email": email, "password": password}, timeout=8)
        if resp.status_code == 200:
            user = resp.json().get("user")
            return user, "", False, "", ""  # clear form + close modal on success
        else:
            err = resp.json().get("error", "Login failed. Please try again.")
            return (dash.no_update, dbc.Alert(err, color="danger")) + no_op
    except requests.exceptions.RequestException:
        return (dash.no_update, dbc.Alert("Could not reach the server. Make sure server.js is running.", color="danger")) + no_op


@app.callback(
    Output("logged-in-user", "data", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    return None


@app.callback(
    Output("li-email", "value", allow_duplicate=True),
    Output("li-password", "value", allow_duplicate=True),
    Output("login-submit-status", "children", allow_duplicate=True),
    Input("login-modal", "is_open"),
    prevent_initial_call=True,
)
def reset_login_form(is_open):
    if not is_open:
        raise dash.exceptions.PreventUpdate
    return None, None, ""


SECTION_BASE_STYLE = {
    "startup": {"backgroundColor": "rgba(5,150,105,0.06)", "border": "1px solid rgba(5,150,105,0.25)"},
    "corporate": {"backgroundColor": "rgba(37,99,235,0.06)", "border": "1px solid rgba(37,99,235,0.25)"},
    "incubator": {"backgroundColor": "rgba(147,51,234,0.06)", "border": "1px solid rgba(147,51,234,0.25)"},
    "ngo": {"backgroundColor": "rgba(217,119,6,0.06)", "border": "1px solid rgba(217,119,6,0.25)"},
    "innovation": {"backgroundColor": "rgba(8,145,178,0.06)", "border": "1px solid rgba(8,145,178,0.25)"},
    "others": {"backgroundColor": "rgba(100,116,139,0.08)", "border": "1px solid rgba(100,116,139,0.3)"},
}


@app.callback(
    Output("startup-fields", "style"),
    Output("corporate-fields", "style"),
    Output("incubator-fields", "style"),
    Output("ngo-fields", "style"),
    Output("innovation-fields", "style"),
    Output("others-fields", "style"),
    Input("su-user-type", "value"),
)
def show_relevant_fields(user_type):
    order = ["startup", "corporate", "incubator", "ngo", "innovation", "others"]
    styles = []
    for t in order:
        base = {**SECTION_BASE_STYLE[t], "borderRadius": "12px", "padding": "18px", "marginTop": "8px"}
        base["display"] = "block" if user_type == t else "none"
        styles.append(base)
    return tuple(styles)


@app.callback(
    Output("su-name", "invalid"),
    Output("su-email", "invalid"),
    Output("su-contact", "invalid"),
    Output("su-password", "invalid"),
    Input("su-name", "value"),
    Input("su-email", "value"),
    Input("su-contact", "value"),
    Input("su-password", "value"),
)
def validate_common_fields(name, email, contact, password):
    import re
    name_invalid = name is not None and name.strip() == ""
    email_invalid = bool(email) and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)
    contact_invalid = bool(contact) and not re.match(r"^\d{10}$", contact)
    password_invalid = bool(password) and len(password) < 6
    return name_invalid, email_invalid, contact_invalid, password_invalid


@app.callback(
    Output("su-startup-year", "disabled"),
    Input("su-startup-dpiit", "value"),
)
def toggle_startup_year_field(dpiit_value):
    return dpiit_value == "no"


@app.callback(
    Output("su-startup-year", "invalid"),
    Input("su-startup-year", "value"),
)
def validate_startup_year(year):
    import re
    return bool(year) and not re.match(r"^(19[9]\d|20[0-2]\d)$", year)


@app.callback(
    Output("su-corp-funding-area-other", "style"),
    Input("su-corp-funding-area", "value"),
)
def toggle_corp_funding_other(selected):
    if selected and "Other" in selected:
        return {"display": "block"}
    return {"display": "none"}


@app.callback(
    Output("su-corp-donation-priority-other", "style"),
    Input("su-corp-donation-priority", "value"),
)
def toggle_corp_donation_other(value):
    if value == "Others":
        return {"display": "block"}
    return {"display": "none"}


@app.callback(
    Output("su-incub-focus-other", "style"),
    Input("su-incub-focus", "value"),
)
def toggle_incub_focus_other(selected):
    if selected and "Other" in selected:
        return {"display": "block"}
    return {"display": "none"}


@app.callback(
    Output("su-ngo-focus-other", "style"),
    Input("su-ngo-focus", "value"),
)
def toggle_ngo_focus_other(selected):
    if selected and "Other" in selected:
        return {"display": "block"}
    return {"display": "none"}


DOC_WARNING_TEXT = (
    "⚠️ You are missing one or more required documents, so you are currently "
    "not eligible to apply for CSR grants. You can still sign up and log in — "
    "you can complete your documentation later."
)


@app.callback(
    Output("su-incub-doc-warning", "children"),
    Input("su-incub-docs", "value"),
)
def check_incub_docs(selected):
    selected = selected or []
    if len(selected) < len(REQUIRED_DOCS_OPTIONS):
        return dbc.Alert(DOC_WARNING_TEXT, color="warning", className="mt-2", style={"fontSize": "13px"})
    return ""


@app.callback(
    Output("su-ngo-doc-warning", "children"),
    Input("su-ngo-docs", "value"),
)
def check_ngo_docs(selected):
    selected = selected or []
    if len(selected) < len(REQUIRED_DOCS_OPTIONS):
        return dbc.Alert(DOC_WARNING_TEXT, color="warning", className="mt-2", style={"fontSize": "13px"})
    return ""


@app.callback(
    Output("signup-submit-status", "children"),
    Output("signup-go-login-btn", "style"),
    Input("signup-submit-btn", "n_clicks"),
    State("su-name", "value"),
    State("su-email", "value"),
    State("su-contact", "value"),
    State("su-password", "value"),
    State("su-user-type", "value"),
    # startup
    State("su-startup-name", "value"),
    State("su-startup-industry", "value"),
    State("su-startup-domain", "value"),
    State("su-startup-desc", "value"),
    State("su-startup-dpiit", "value"),
    State("su-startup-year", "value"),
    State("su-startup-stage", "value"),
    State("su-startup-pitch-link", "value"),
    # corporate
    State("su-corp-name", "value"),
    State("su-corp-industry", "value"),
    State("su-corp-domain", "value"),
    State("su-corp-funding-area", "value"),
    State("su-corp-funding-area-other", "value"),
    State("su-corp-donation-priority", "value"),
    State("su-corp-donation-priority-other", "value"),
    State("su-corp-sector", "value"),
    State("su-corp-range", "value"),
    # incubator
    State("su-incub-name", "value"),
    State("su-incub-type", "value"),
    State("su-incub-year", "value"),
    State("su-incub-location", "value"),
    State("su-incub-focus", "value"),
    State("su-incub-focus-other", "value"),
    State("su-incub-partner", "value"),
    State("su-incub-revenue", "value"),
    State("su-incub-docs", "value"),
    # ngo
    State("su-ngo-name", "value"),
    State("su-ngo-type", "value"),
    State("su-ngo-year", "value"),
    State("su-ngo-location", "value"),
    State("su-ngo-focus", "value"),
    State("su-ngo-focus-other", "value"),
    State("su-ngo-partner", "value"),
    State("su-ngo-revenue", "value"),
    State("su-ngo-reach", "value"),
    State("su-ngo-docs", "value"),
    # innovation
    State("su-innov-name", "value"),
    State("su-innov-research", "value"),
    # others
    State("su-other-org-name", "value"),
    State("su-other-org-type", "value"),
    State("su-other-description", "value"),
    State("su-other-focus", "value"),
    prevent_initial_call=True,
)
def submit_signup(n_clicks, name, email, contact, password, user_type,
                   s_name, s_industry, s_domain, s_desc, s_dpiit, s_year, s_stage, s_pitch,
                   c_name, c_industry, c_domain, c_area, c_area_other, c_priority, c_priority_other, c_sector, c_range,
                   i_name, i_type, i_year, i_location, i_focus, i_focus_other, i_partner, i_revenue, i_docs,
                   n_name, n_type, n_year, n_location, n_focus, n_focus_other, n_partner, n_revenue, n_reach, n_docs,
                   innov_name, innov_research,
                   o_name, o_type, o_desc, o_focus):

    import re

    hidden_btn = {"display": "none"}

    if not name or not email or not contact or not password or not user_type:
        return dbc.Alert("Please fill in Name, Email, Contact, Password, and select who you are.", color="danger"), hidden_btn

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return dbc.Alert("Please enter a valid email address.", color="danger"), hidden_btn

    if not re.match(r"^\d{10}$", contact):
        return dbc.Alert("Please enter a valid 10-digit contact number.", color="danger"), hidden_btn

    if len(password) < 6:
        return dbc.Alert("Password should be at least 6 characters.", color="danger"), hidden_btn

    if user_type == "startup":
        if s_year and not re.match(r"^(19[9]\d|20[0-2]\d)$", s_year):
            return dbc.Alert("Please enter a valid year of incorporation (1990–2026).", color="danger"), hidden_btn
        profile_details = {
            "startup_name": s_name, "industry": s_industry, "domain": s_domain,
            "description": s_desc, "dpiit_registered": s_dpiit,
            "year_of_incorporation": s_year if s_dpiit == "yes" else None,
            "stage": s_stage, "pitch_deck_link": s_pitch,
        }

    elif user_type == "corporate":
        c_area_final = list(c_area) if c_area else []
        if "Other" in c_area_final and c_area_other:
            c_area_final = [a for a in c_area_final if a != "Other"] + [c_area_other]
        c_priority_final = c_priority_other if c_priority == "Others" and c_priority_other else c_priority
        profile_details = {
            "corporate_name": c_name, "industry": c_industry, "domain": c_domain,
            "csr_funding_area": c_area_final, "csr_donation_priority": c_priority_final,
            "csr_funding_sector": c_sector,
            "csr_funding_range_min_lakh": c_range[0] if c_range else None,
            "csr_funding_range_max_lakh": c_range[1] if c_range else None,
        }

    elif user_type == "incubator":
        i_focus_final = list(i_focus) if i_focus else []
        if "Other" in i_focus_final and i_focus_other:
            i_focus_final = [a for a in i_focus_final if a != "Other"] + [i_focus_other]
        profile_details = {
            "incubator_name": i_name, "type": i_type, "year_of_establishment": i_year,
            "location": i_location, "csr_focus_area": i_focus_final,
            "associate_corporate_partner": i_partner,
            "annual_revenue_min_lakh": i_revenue[0] if i_revenue else None,
            "annual_revenue_max_lakh": i_revenue[1] if i_revenue else None,
            "documents_available": i_docs or [],
            "grant_eligible": len(i_docs or []) == len(REQUIRED_DOCS_OPTIONS),
        }

    elif user_type == "ngo":
        n_focus_final = list(n_focus) if n_focus else []
        if "Other" in n_focus_final and n_focus_other:
            n_focus_final = [a for a in n_focus_final if a != "Other"] + [n_focus_other]
        profile_details = {
            "ngo_name": n_name, "type": n_type, "year_of_establishment": n_year,
            "location": n_location, "csr_focus_area": n_focus_final,
            "associate_corporate_partner": n_partner,
            "annual_revenue_min_lakh": n_revenue[0] if n_revenue else None,
            "annual_revenue_max_lakh": n_revenue[1] if n_revenue else None,
            "geographical_reach": n_reach,
            "documents_available": n_docs or [],
            "grant_eligible": len(n_docs or []) == len(REQUIRED_DOCS_OPTIONS),
        }

    elif user_type == "innovation":
        if not innov_name or not innov_research:
            return dbc.Alert("Please fill in your name and research work.", color="danger"), hidden_btn
        profile_details = {"innovator_name": innov_name, "research_work": innov_research}

    elif user_type == "others":
        profile_details = {
            "organization_name": o_name, "organization_type": o_type,
            "description": o_desc, "area_of_focus": o_focus,
        }

    else:
        return dbc.Alert("Please select who you are.", color="danger"), hidden_btn

    try:
        resp = requests.post(f"{API_URL}/signup", json={
            "name": name, "email": email, "contact": contact, "password": password,
            "user_type": user_type, "profile_details": profile_details,
        }, timeout=8)

        if resp.status_code == 200:
            return dbc.Alert("🎉 Signed up successfully!", color="success"), {"display": "block", "marginTop": "4px"}
        else:
            err = resp.json().get("error", "Signup failed. Please try again.")
            return dbc.Alert(err, color="danger"), hidden_btn
    except requests.exceptions.RequestException:
        return dbc.Alert("Could not reach the server. Make sure server.js is running.", color="danger"), hidden_btn


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
    card_style = {"backgroundColor": p["card_bg"], "border": "none", "borderRadius": "12px"}
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
    
    