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
    {"label": "NGO (coming soon)", "value": "ngo", "disabled": True},
    {"label": "Incubator (coming soon)", "value": "incubator", "disabled": True},
    {"label": "Innovation Cell (coming soon)", "value": "innovation", "disabled": True},
    {"label": "Others (coming soon)", "value": "others", "disabled": True},
]

INDUSTRY_OPTIONS = [
    "Healthcare", "EdTech", "FinTech", "AgriTech", "CleanTech", "BioTech",
    "AI/ML", "Manufacturing", "E-commerce/Retail", "Logistics",
    "Media & Entertainment", "Other",
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

    # ── Top bar: title + theme toggle + Login/Sign Up/Chatbot buttons ──
    html.Div([
        html.Div([
            html.H3("CSR India — Live Dashboard", id="page-title", style={"margin": "0"}),
            html.P("FY 2023-24 CSR & Philanthropy Overview", id="page-subtitle", style={"margin": "0"}),
        ]),
        html.Div([
            dbc.Button("🌙 Dark / ☀️ Light", id="theme-toggle-btn", color="secondary", outline=True, className="me-2"),
            dbc.Button("Login", id="login-btn", color="light", outline=True, className="me-2"),
            dbc.Button("Sign Up", id="signup-btn", color="light", outline=True, className="me-2"),
            dbc.Button("Chatbot", id="open-chatbot-btn", color="success"),
        ], style={"display": "flex", "alignItems": "center"}),
    ], id="topbar", style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "18px 28px",
    }),

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

    # ── Sign Up popup modal ──
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Sign Up"), close_button=True),
            dbc.ModalBody([
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
                    html.Hr(),
                    html.H6("Startup Details"),
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
                ], id="startup-fields", style={"display": "none"}),

                # ── Corporate-specific fields ──
                html.Div([
                    html.Hr(),
                    html.H6("Corporate Details"),
                    dbc.Label("Name of Corporate"),
                    dbc.Input(id="su-corp-name", type="text", className="mb-3"),

                    dbc.Label("Industry"),
                    dcc.Dropdown(id="su-corp-industry",
                                 options=[{"label": i, "value": i} for i in INDUSTRY_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Domain"),
                    dbc.Input(id="su-corp-domain", type="text", className="mb-3"),

                    dbc.Label("CSR Funding Theme Area"),
                    dcc.Dropdown(id="su-corp-theme",
                                 options=[{"label": t, "value": t} for t in CSR_THEME_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("Funding To Whom"),
                    dcc.Dropdown(id="su-corp-funding-to",
                                 options=[{"label": f, "value": f} for f in FUNDING_TO_WHOM_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("CSR Funding Sector"),
                    dcc.Dropdown(id="su-corp-sector",
                                 options=[{"label": s, "value": s} for s in CSR_FUNDING_SECTOR_OPTIONS],
                                 style={"color": "black", "marginBottom": "18px"}),

                    dbc.Label("CSR Funding Range (₹)"),
                    dbc.Row([
                        dbc.Col(dbc.Input(id="su-corp-range-min", type="number", placeholder="Min (Lakh)")),
                        dbc.Col(dbc.Input(id="su-corp-range-max", type="number", placeholder="Max (Crore)")),
                    ], className="mb-1"),
                    dbc.FormFeedback("Min should not be greater than Max.", id="su-corp-range-feedback", type="invalid"),
                    html.Div(style={"marginBottom": "12px"}),
                ], id="corporate-fields", style={"display": "none"}),

                dcc.Loading(
                    type="circle", color=EMERALD,
                    children=[
                        dbc.Button("Submit", id="signup-submit-btn", color="success", className="mt-2 w-100"),
                        html.Div(id="signup-submit-status"),
                    ],
                ),
            ]),
        ],
        id="signup-modal",
        size="lg",
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
    Output("startup-fields", "style"),
    Output("corporate-fields", "style"),
    Input("su-user-type", "value"),
)
def show_relevant_fields(user_type):
    hidden = {"display": "none"}
    shown = {"display": "block"}
    if user_type == "startup":
        return shown, hidden
    if user_type == "corporate":
        return hidden, shown
    return hidden, hidden


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
    Output("su-startup-year", "invalid"),
    Input("su-startup-year", "value"),
)
def validate_startup_year(year):
    import re
    return bool(year) and not re.match(r"^(19[9]\d|20[0-2]\d)$", year)


@app.callback(
    Output("su-corp-range-min", "invalid"),
    Output("su-corp-range-max", "invalid"),
    Input("su-corp-range-min", "value"),
    Input("su-corp-range-max", "value"),
)
def validate_corp_range(c_min, c_max):
    invalid = c_min is not None and c_max is not None and c_min > c_max
    return invalid, invalid


@app.callback(
    Output("signup-submit-status", "children"),
    Input("signup-submit-btn", "n_clicks"),
    State("su-name", "value"),
    State("su-email", "value"),
    State("su-contact", "value"),
    State("su-password", "value"),
    State("su-user-type", "value"),
    State("su-startup-name", "value"),
    State("su-startup-industry", "value"),
    State("su-startup-domain", "value"),
    State("su-startup-desc", "value"),
    State("su-startup-dpiit", "value"),
    State("su-startup-year", "value"),
    State("su-startup-stage", "value"),
    State("su-corp-name", "value"),
    State("su-corp-industry", "value"),
    State("su-corp-domain", "value"),
    State("su-corp-theme", "value"),
    State("su-corp-funding-to", "value"),
    State("su-corp-sector", "value"),
    State("su-corp-range-min", "value"),
    State("su-corp-range-max", "value"),
    prevent_initial_call=True,
)
def submit_signup(n_clicks, name, email, contact, password, user_type,
                   s_name, s_industry, s_domain, s_desc, s_dpiit, s_year, s_stage,
                   c_name, c_industry, c_domain, c_theme, c_funding_to, c_sector, c_min, c_max):

    import re

    if not name or not email or not contact or not password or not user_type:
        return dbc.Alert("Please fill in Name, Email, Contact, Password, and select who you are.", color="danger")

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return dbc.Alert("Please enter a valid email address.", color="danger")

    if not re.match(r"^\d{10}$", contact):
        return dbc.Alert("Please enter a valid 10-digit contact number.", color="danger")

    if len(password) < 6:
        return dbc.Alert("Password should be at least 6 characters.", color="danger")

    if user_type not in ("startup", "corporate"):
        return dbc.Alert("Sign up for this category is coming soon.", color="warning")

    if user_type == "startup":
        if s_year and not re.match(r"^(19[9]\d|20[0-2]\d)$", s_year):
            return dbc.Alert("Please enter a valid year of incorporation (1990–2026).", color="danger")
        profile_details = {
            "startup_name": s_name, "industry": s_industry, "domain": s_domain,
            "description": s_desc, "dpiit_registered": s_dpiit,
            "year_of_incorporation": s_year, "stage": s_stage,
        }
    else:
        if c_min is not None and c_max is not None and c_min > c_max:
            return dbc.Alert("Minimum funding range cannot be greater than maximum.", color="danger")
        profile_details = {
            "corporate_name": c_name, "industry": c_industry, "domain": c_domain,
            "csr_funding_theme": c_theme, "funding_to_whom": c_funding_to,
            "csr_funding_sector": c_sector,
            "csr_funding_range_min_lakh": c_min, "csr_funding_range_max_crore": c_max,
        }

    try:
        resp = requests.post(f"{API_URL}/signup", json={
            "name": name, "email": email, "contact": contact, "password": password,
            "user_type": user_type, "profile_details": profile_details,
        }, timeout=8)

        if resp.status_code == 200:
            return dbc.Alert("Signed up successfully! You can close this window.", color="success")
        else:
            err = resp.json().get("error", "Signup failed. Please try again.")
            return dbc.Alert(err, color="danger")
    except requests.exceptions.RequestException:
        return dbc.Alert("Could not reach the server. Make sure server.js is running.", color="danger")


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
    card_style = {"backgroundColor": p["card_bg"], "border": "none", "borderRadius": "12px"}

    return (
        page_style, topbar_style, title_style, subtitle_style,
        card_style, card_style, card_style, card_style,
        card_style, card_style, card_style, card_style, card_style, card_style, card_style,
        make_heatmap(theme), make_trend(theme), make_sector_bars(theme),
        make_psu_donut(theme), make_treemap(theme), make_top_co(theme),
    )


# ── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050)