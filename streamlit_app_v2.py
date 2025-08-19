import datetime
import os
from typing import List, Tuple

import numpy as np
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
from sklearn.linear_model import LinearRegression

from app.data_loader import load_datasets
from app.prediction import compute_indices, get_historical_data_for_date
from app.scoring import apply_profile_adjustment, build_ranking
# LLM temporaneamente disabilitato
# from app.llm import generate_overview
from app.config import SUPPORTED_PROFILES

# Modern UI Configuration
st.set_page_config(
    page_title="🏔️ Ski Resort Recommender",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Design System CSS
st.markdown("""
<style>
/* Modern Design System - Light/Dark Mode Compatible */
html { scroll-behavior: smooth; }
:root {
    /* Color Palette */
    --primary: #007AFF;
    --primary-light: #5AC8FA;
    --primary-dark: #0051D5;
    --secondary: #5856D6;
    --accent: #FF2D92;
    --success: #34C759;
    --warning: #FF9500;
    --error: #FF3B30;
    
    /* Neutral Colors */
    --bg-primary: #FFFFFF;
    --bg-secondary: #F2F2F7;
    --bg-tertiary: #E5E5EA;
    --text-primary: #000000;
    --text-secondary: #8E8E93;
    --text-tertiary: #C7C7CC;
    
    /* Borders & Shadows */
    --border-light: #E5E5EA;
    --border-medium: #C7C7CC;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
    
    /* Gradients */
    --gradient-primary: linear-gradient(135deg, var(--primary), var(--primary-light));
    --gradient-secondary: linear-gradient(135deg, var(--secondary), var(--accent));
    --gradient-success: linear-gradient(135deg, var(--success), #30D158);
    --gradient-warning: linear-gradient(135deg, var(--warning), #FF6B35);
    
    /* Glow Effects */
    --glow-primary: 0 0 20px rgba(0, 122, 255, 0.3);
    --glow-secondary: 0 0 20px rgba(88, 86, 214, 0.3);
    --glow-success: 0 0 20px rgba(52, 199, 89, 0.3);
    --glow-warning: 0 0 20px rgba(255, 149, 0, 0.3);
}

/* Dark Mode Overrides */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #000000;
        --bg-secondary: #1C1C1E;
        --bg-tertiary: #2C2C2E;
        --text-primary: #FFFFFF;
        --text-secondary: #8E8E93;
        --text-tertiary: #48484A;
        --border-light: #38383A;
        --border-medium: #48484A;
    }
}

/* Global Styles */
.main {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* Modern Cards */
.modern-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(20px);
}

.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary);
}

/* Hero Section */
.hero-section {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 20px;
    padding: 32px;
    margin: 28px 0 22px 0;
    text-align: center;
    color: var(--text-primary);
    box-shadow: var(--shadow-md);
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    font-size: 1.25rem;
    font-weight: 500;
    opacity: 0.9;
    margin: 0;
}

/* KPI Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin: 24px 0;
}

.kpi-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 140px;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--border-light);
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary);
}
.kpi-card:hover::before {
    opacity: 1;
}

.kpi-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 12px 0 6px 0;
    letter-spacing: -0.02em;
}

.kpi-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Modern Headers */
.modern-header {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: 2rem 0 1rem 0;
    letter-spacing: -0.02em;
}

.modern-subheader {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 1.5rem 0 1rem 0;
    letter-spacing: -0.01em;
}

.modern-section-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 1rem 0 0.5rem 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* AI Overview Section (Apple Intelligence-inspired) */
.ai-overview-section {
    background: var(--bg-primary);
    border: 2px solid transparent;
    border-radius: 20px;
    padding: 24px 28px;
    margin: 20px 0 28px 0;
    position: relative;
}

/* Extended frosted glass effect for more elements */
.frosted-glass {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.modern-card.frosted {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Enhanced floating AI dock with frosted glass */
.ai-dock {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 50px;
    padding: 12px 24px;
    display: flex;
    gap: 20px;
    align-items: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    transition: all 0.3s ease;
}

.ai-dock:hover {
    background: rgba(255, 255, 255, 0.15);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.ai-dock a {
    color: var(--text-primary);
    text-decoration: none;
    padding: 8px 16px;
    border-radius: 25px;
    transition: all 0.3s ease;
    background: rgba(255, 255, 255, 0.1);
}

.ai-dock a:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
}

/* Animated edge glow border - inspired by reference image */
.ai-overview-section::after {
    content: '';
    position: absolute;
    inset: -2px;
    z-index: -1;
    border-radius: 22px;
    background: conic-gradient(
        from 0deg,
        #3b82f6,
        #7c3aed,
        #ec4899,
        #ef4444,
        #f59e0b,
        #facc15,
        #3b82f6
    );
    filter: blur(3px);
    opacity: 0.7;
    animation: aiGlow 8s linear infinite;
}

/* Enhanced edge glow with breathing effect */
.ai-overview-section::before {
    content: '';
    position: absolute;
    inset: -1px;
    z-index: -1;
    border-radius: 21px;
    background: linear-gradient(90deg, 
        #3b82f6, #7c3aed, #ec4899, #ef4444, #f59e0b, #facc15, #3b82f6
    );
    background-size: 200% 100%;
    animation: edgeGlow 4s ease-in-out infinite;
    opacity: 0.9;
}

/* Additional breathing glow effect */
.ai-overview-section::after {
    animation: breathingGlow 3s ease-in-out infinite;
}

@keyframes breathingGlow {
    0%, 100% { 
        opacity: 0.6;
        filter: blur(3px) brightness(1);
    }
    50% { 
        opacity: 0.9;
        filter: blur(2px) brightness(1.2);
    }
}

@keyframes aiGlow {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes edgeGlow {
    0% { 
        background-position: 0% 50%;
        opacity: 0.7;
        filter: blur(2px);
    }
    25% {
        opacity: 1;
        filter: blur(1px);
    }
    50% { 
        background-position: 100% 50%;
        opacity: 0.9;
        filter: blur(3px);
    }
    75% {
        opacity: 1;
        filter: blur(1px);
    }
    100% { 
        background-position: 0% 50%;
        opacity: 0.7;
        filter: blur(2px);
    }
}

/* Scanning light effect along the border */
.ai-overview-section::before {
    animation: edgeGlow 4s ease-in-out infinite, scanningLight 2s ease-in-out infinite;
}

@keyframes scanningLight {
    0% { 
        background: linear-gradient(90deg, 
            #3b82f6 0%, #7c3aed 20%, #ec4899 40%, #ef4444 60%, #f59e0b 80%, #facc15 100%
        );
        background-size: 200% 100%;
        background-position: 0% 50%;
    }
    50% { 
        background: linear-gradient(90deg, 
            #facc15 0%, #3b82f6 20%, #7c3aed 40%, #ec4899 60%, #ef4444 80%, #f59e0b 100%
        );
        background-size: 200% 100%;
        background-position: 100% 50%;
    }
    100% { 
        background: linear-gradient(90deg, 
            #3b82f6 0%, #7c3aed 20%, #ec4899 40%, #ef4444 60%, #f59e0b 80%, #facc15 100%
        );
        background-size: 200% 100%;
        background-position: 0% 50%;
    }
}

.ai-overview-content {
    color: var(--text-primary);
    line-height: 1.65;
    font-size: 1rem;
}

/* AI Overview Border Animation - ONLY BORDER */
.ai-overview-section {
    position: relative;
    /* No animation on content */
}

.ai-overview-section::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: conic-gradient(
        #3b82f6 0deg,
        #7c3aed 60deg,
        #ec4899 120deg,
        #ef4444 180deg,
        #f59e0b 240deg,
        #facc15 300deg,
        #3b82f6 360deg
    );
    border-radius: 16px;
    z-index: -1;
    animation: borderRotate 4s linear infinite;
}

.ai-overview-section::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-card);
    border-radius: 14px;
    z-index: 0;
}

.ai-overview-content {
    position: relative;
    z-index: 1;
}

@keyframes borderRotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Floating AI Dock */
.ai-dock {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(20,20,22,0.6);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 10px 14px;
    display: flex;
    gap: 10px;
    align-items: center;
    z-index: 9999;
}

@media (prefers-color-scheme: light) {
  .ai-dock { background: rgba(255,255,255,0.75); }
}

.ai-dock a, .ai-dock span {
    color: var(--text-primary);
    text-decoration: none;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
}

.ai-dock a:hover {
    background: var(--bg-secondary);
}

/* Modern Buttons */
.stButton > button {
    background: var(--gradient-primary);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    box-shadow: var(--shadow-sm);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg), var(--glow-primary);
}

/* Modern Tables */
.modern-table {
    background: var(--bg-primary);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border-light);
}

.modern-table th {
    background: var(--gradient-primary);
    color: white;
    font-weight: 600;
    padding: 16px;
    text-align: left;
}

.modern-table td {
    padding: 16px;
    border-bottom: 1px solid var(--border-light);
}

.modern-table tr:hover {
    background: rgba(0, 122, 255, 0.05);
}

/* Podium */
.podium-container {
    display: flex;
    justify-content: center;
    align-items: end;
    gap: 24px;
    margin: 32px 0;
}

.podium-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}

.podium-1 {
    background: var(--gradient-warning);
    height: 120px;
    width: 120px;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    box-shadow: var(--glow-warning);
}

.podium-2 {
    background: var(--gradient-secondary);
    height: 100px;
    width: 110px;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    box-shadow: var(--glow-secondary);
}

.podium-3 {
    background: var(--gradient-success);
    height: 80px;
    width: 110px;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    box-shadow: var(--glow-success);
}

.podium-medal {
    font-size: 1.5rem;
    margin-bottom: 8px;
}

.podium-name {
    font-weight: 700;
    font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
    }
    
    .podium-container {
        flex-direction: column;
        align-items: center;
    }
}

/* Streamlit Element Overrides */
.stSelectbox > div > div {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 8px;
}

.stDateInput > div > div {
    background: var(--bg-primary);
    border: 1px solid var(--border-light);
    border-radius: 8px;
}

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
}



/* Success/Info/Warning/Error Messages */
.stSuccess {
    background: rgba(52, 199, 89, 0.1);
    border: 1px solid rgba(52, 199, 89, 0.2);
    border-radius: 12px;
    color: var(--success);
}

.stInfo {
    background: rgba(0, 122, 255, 0.1);
    border: 1px solid rgba(0, 122, 255, 0.2);
    border-radius: 12px;
    color: var(--primary);
}

.stWarning {
    background: rgba(255, 149, 0, 0.1);
    border: 1px solid rgba(255, 149, 0, 0.2);
    border-radius: 12px;
    color: var(--warning);
}

.stError {
    background: rgba(255, 59, 48, 0.1);
    border: 1px solid rgba(255, 59, 48, 0.2);
    border-radius: 12px;
    color: var(--error);
}
</style>
""", unsafe_allow_html=True)


def aggregate_station_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Ensure required columns exist with fallbacks
    if "kmtotal" not in df.columns:
        df["kmtotal"] = 0
    if "kmopen" not in df.columns:
        df["kmopen"] = 0
        
    if "kmtotal" in df.columns:
        df["pct_open"] = np.where(df["kmtotal"] > 0, df.get("kmopen", 0) / df["kmtotal"], np.nan)
    else:
        df["pct_open"] = np.nan
    if "kmopen" in df.columns:
        df["is_open"] = (df["kmopen"].fillna(0) > 0).astype(float)
    else:
        df["is_open"] = 0.0
        
    agg_spec = {
        "kmopen": ("kmopen", "mean"),
        "kmtotal": ("kmtotal", "mean"),
        "pct_open": ("pct_open", "mean"),
        "is_open": ("is_open", "mean"),
    }
    
    # Add optional columns only if they exist
    if "danger_level_avg" in df.columns:
        agg_spec["danger_level_avg"] = ("danger_level_avg", "mean")
    if "vento" in df.columns:
        agg_spec["vento"] = ("vento", "mean")
    if "nebbia" in df.columns:
        agg_spec["nebbia"] = ("nebbia", "mean")
    if "espesor_medio" in df.columns:
        agg_spec["espesor_medio"] = ("espesor_medio", "mean")
    if "sole" in df.columns:
        agg_spec["sole"] = ("sole", "mean")
    if "pioggia" in df.columns:
        agg_spec["pioggia"] = ("pioggia", "mean")

    agg = df.groupby("nome_stazione").agg(**agg_spec).reset_index()

    # rename to friendly column names
    agg = agg.rename(
        columns={
            "kmopen": "km_open_est",
            "kmtotal": "km_total_est",
            "is_open": "open_prob",
        }
    )
    
    # Add missing columns with default values
    if "avalanche" not in agg.columns:
        agg["avalanche"] = 0
    if "neve_cm" not in agg.columns:
        agg["neve_cm"] = 0
        
    return agg.fillna(0)


def build_textual_tags(row: pd.Series, livello: str, profilo: str) -> List[str]:
    tags: List[str] = []
    if row.get("pct_open", 0) >= 0.5 or row.get("km_open_est", 0) >= 20:
        tags.append("molte piste aperte")
    if row.get("avalanche", 3) <= 2.5:
        tags.append("basso rischio valanghe")
    if row.get("vento", 0) <= 0.2 and row.get("nebbia", 0) <= 0.2:
        tags.append("meteo stabile")
    if livello == "esperto" and row.get("neve_cm", 0) >= 40:
        tags.append("neve consistente")
    if livello == "base" and row.get("pct_open", 0) >= 0.4:
        tags.append("ideale per principianti")
    if profilo in ("panoramico", "familiare", "festaiolo", "lowcost"):
        tags.append(f"adatta al profilo {profilo}")
    return tags


def ensure_lat_lon(df: pd.DataFrame) -> pd.DataFrame:
    """Try to provide 'lat' and 'lon' columns by renaming common variants.

    Supported aliases: latitude/longitude, Latitude/Longitude, latitudine/longitudine.
    """
    df = df.copy()
    colmap = {c.lower(): c for c in df.columns}
    lat_aliases = ["lat", "latitude", "latitudine"]
    lon_aliases = ["lon", "long", "lng", "longitude", "longitudine"]
    # Find best matches
    lat_col = next((colmap[a] for a in lat_aliases if a in colmap), None)
    lon_col = next((colmap[a] for a in lon_aliases if a in colmap), None)
    if lat_col and "lat" not in df.columns:
        df["lat"] = df[lat_col]
    if lon_col and "lon" not in df.columns:
        df["lon"] = df[lon_col]
    # Ensure columns exist to avoid KeyError downstream
    if "lat" not in df.columns:
        df["lat"] = np.nan
    if "lon" not in df.columns:
        df["lon"] = np.nan
    return df


def create_speedometer(value: float, reference: float, title: str, unit: str = ""):
    """Create a modern speedometer chart with Plotly."""
    # Normalize values to 0-100 range
    value_pct = min(100, max(0, value * 100))
    reference_pct = min(100, max(0, reference * 100))
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value_pct,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        delta={'reference': reference_pct, 'increasing': {'color': "#FF3B30"}, 'decreasing': {'color': "#34C759"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#007AFF"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#FF3B30'},
                {'range': [25, 50], 'color': '#FF9500'},
                {'range': [50, 75], 'color': '#FFCC02'},
                {'range': [75, 100], 'color': '#34C759'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    # Update layout for modern look
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=40, b=60),
        font={'color': "#000000"},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def format_date_for_display(date_obj: datetime.date) -> str:
    """Formatta una data nel formato 'XX mese 20XX'"""
    month_names = {
        1: "gennaio", 2: "febbraio", 3: "marzo", 4: "aprile", 5: "maggio", 6: "giugno",
        7: "luglio", 8: "agosto", 9: "settembre", 10: "ottobre", 11: "novembre", 12: "dicembre"
    }
    return f"{date_obj.day} {month_names[date_obj.month]} {date_obj.year}"

def build_llm_prompt(df_kpis: pd.DataFrame, best_name: str, livello: str, profilo: str, target_date: datetime.date) -> str:
    # Trova riga best
    best = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0].to_dict() if not df_kpis.empty else {}
    
    # Seleziona 2 alternative principali (per km aperti stimati)
    others = (
        df_kpis[df_kpis["nome_stazione"] != best_name]
        .sort_values("km_open_est", ascending=False)
        .head(2)
        .to_dict(orient="records")
        if "km_open_est" in df_kpis.columns else []
    )
    
    def fmt(x, pct=False):
        try:
            return f"{float(x)*100:.0f}%" if pct else f"{float(x):.0f}"
        except Exception:
            return "-"
    
    # facts per best
    b_km = fmt(best.get("km_open_est", 0))
    b_pct = fmt(best.get("pct_open", 0), pct=True)
    b_neb = fmt(best.get("nebbia", 0), pct=True)
    b_ven = fmt(best.get("vento", 0), pct=True)
    b_av  = f"{float(best.get('avalanche', 0)):.1f}" if best.get('avalanche') is not None else "-"
    
    lines = [
        f"BEST {best_name}: km aperti {b_km}, % aperte {b_pct}, nebbia {b_neb}, vento {b_ven}, valanghe {b_av}"
    ]
    
    for o in others:
        o_km = fmt(o.get("km_open_est", 0))
        o_pct = fmt(o.get("pct_open", 0), pct=True)
        o_neb = fmt(o.get("nebbia", 0), pct=True)
        o_ven = fmt(o.get("vento", 0), pct=True)
        o_av  = f"{float(o.get('avalanche', 0)):.1f}" if o.get('avalanche') is not None else "-"
        lines.append(
            f"ALT {o['nome_stazione']}: km {o_km}, % {o_pct}, nebbia {o_neb}, vento {o_ven}, valanghe {o_av}"
        )
    
    context = "\n".join(lines)
    
    # Formatta la data nel formato richiesto
    formatted_date = format_date_for_display(target_date)
    
    prompt = (
        f"Per la data {formatted_date} l'app ha selezionato la stazione migliore: {best_name}. "
        f"Scrivi un'overview molto breve (max 2 frasi, 35–45 parole), chiara e utile, che spieghi perché {best_name} è preferibile rispetto alle altre. "
        f"Usa informazioni concrete: km/% piste, meteo (nebbia/vento/sole/pioggia), rischio valanghe e coerenza con livello '{livello}' e profilo '{profilo}'. "
        f"Non fare elenchi; evita superlativi generici. Se non emergono differenze nette, evidenzia il miglior compromesso.\n"
        f"Dati sintetici (usa solo come base, non ripetere letteralmente etichette BEST/ALT):\n{context}"
    )
    return prompt

def build_festaiolo_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date) -> str:
    # Estrae signal dalle recensioni per tema "festaiolo" per best + 2 alternative
    parts = []
    try:
        by_station = (
            df_rec.groupby("nome_stazione")[["festaiolo", "ristoranti", "coda", "Stelle"]]
            .mean().reset_index().sort_values("festaiolo", ascending=False)
        )
        rows = by_station.head(3).to_dict(orient="records")
        for r in rows:
            parts.append(
                f"- {r['nome_stazione']}: festaiolo={r.get('festaiolo',0):.2f}, stelle={r.get('Stelle',0):.2f}, ristoranti={r.get('ristoranti',0):.2f}, code={r.get('coda',0):.2f}"
            )
    except Exception:
        pass
    
    context = "\n".join(parts)
    
    # Formatta la data nel formato richiesto
    formatted_date = format_date_for_display(target_date)
    
    return (
        f"Per la data {formatted_date} e livello '{livello}', fai un mini-riassunto (max 2 frasi) sul tema 'festa' "
        f"basandoti sui segnali di recensione (indicatori: festaiolo, stelle, ristoranti, code, divertente, giovanile, apres ski, festa, fete, party, fiesta, juvenil, jovanil, juventud, jove, great atmosphere, young) per {best_name} e alternative. "
        f"Sii pratico e specifico (atmosfera, après-ski, nightlife). Evita elenchi.\nDati sintetici:\n{context}"
    )

def build_familiare_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date) -> str:
    # Panoramica family-friendly: segnali recensione e code
    parole_code = [
        "fila", "attesa", "coda", "caos", "affollato", "cua", "cola", "espera", "lleno", "ple",
        "caotic", "aglomeracion", "aglomeracio", "atasco", "pieno", "disorganizzato", "desorganizado",
        "desorganizat", "ressa", "file", "attente", "queue", "bouchon", "foule", "bondé", "plein",
        "chaotique", "désorganisé", "waiting", "wait", "crowd", "crowded", "full", "line", "chaos",
        "chaotic", "busy", "overcrowded", "unorganized", "messy"
    ]
    
    parts = []
    try:
        by_station = (
            df_rec.groupby("nome_stazione")[["familiare", "sicurezza", "coda", "Stelle"]]
            .mean().reset_index().sort_values("familiare", ascending=False)
        )
        rows = by_station.head(3).to_dict(orient="records")
        for r in rows:
            parts.append(
                f"- {r['nome_stazione']}: family={r.get('familiare',0):.2f}, sicurezza={r.get('sicurezza',0):.2f}, code={r.get('coda',0):.2f}, stelle={r.get('Stelle',0):.2f}"
            )
    except Exception:
        pass
    
    context = "\n".join(parts)
    keywords = ", ".join(parole_code[:10]) + ", ..."
    
    # Formatta la data nel formato richiesto
    formatted_date = format_date_for_display(target_date)
    
    return (
        f"Per la data {formatted_date} e livello '{livello}', scrivi un mini-riassunto (max 2 frasi) focalizzato su famiglie. "
        f"Dai priorità a: servizi per bambini, sicurezza percepita, organizzazione (code/affollamento), rapporto qualità/prezzo. "
        f"Considera indicatori da recensioni per {best_name} e alternative (familiare, sicurezza, coda, stelle). "
        f"Se utile, intercetta menzioni a code/affollamento con parole chiave tipo: {keywords}. Evita elenchi.\n"
        f"Dati sintetici:\n{context}"
    )

def build_lowcost_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date) -> str:
    # Panoramica low-cost: segnali recensione su prezzi e rapporto qualità-prezzo
    parole_lowcost = [
        "barato", "económico", "económica", "asequible", "precio", "precios", "oferta", "ofertas", 
        "descuento", "descuentos", "ahorro", "calidad-precio", "coste", "rebaja", "rebajas", 
        "promoción", "promociones", "barat", "econòmic", "econòmica", "assequible", "preu", "preus", 
        "oferta", "ofertes", "descompte", "descomptes", "estalvi", "qualitat-preu", "cost", 
        "rebaixa", "rebaixes", "promoció", "promocions", "car", "cara", "bon marché", "économique", 
        "abordable", "prix", "offre", "offres", "cheap", "affordable", "budget", "value", "deal", 
        "discount", "sale", "promotion", "offer", "cost-effective", "good value", "worth it"
    ]
    
    parts = []
    try:
        # Usa solo le colonne disponibili
        available_cols = [col for col in ["lowcost", "Stelle"] if col in df_rec.columns]
        if available_cols:
            by_station = (
                df_rec.groupby("nome_stazione")[available_cols]
                .mean().reset_index().sort_values("lowcost", ascending=False)
            )
            rows = by_station.head(3).to_dict(orient="records")
            for r in rows:
                part_parts = [f"- {r['nome_stazione']}:"]
                if "lowcost" in available_cols:
                    part_parts.append(f"lowcost={r.get('lowcost',0):.2f}")
                if "Stelle" in available_cols:
                    part_parts.append(f"stelle={r.get('Stelle',0):.2f}")
                parts.append(", ".join(part_parts))
    except Exception:
        pass
    
    context = "\n".join(parts)
    keywords = ", ".join(parole_lowcost[:15]) + ", ..."
    
    # Formatta la data nel formato richiesto
    formatted_date = format_date_for_display(target_date)
    
    return (
        f"Per la data {formatted_date} e livello '{livello}', scrivi un mini-riassunto (max 2 frasi) focalizzato su rapporto qualità-prezzo. "
        f"Dai priorità a: convenienza economica, offerte disponibili, valore percepito, alternative economiche. "
        f"Considera indicatori da recensioni per {best_name} e alternative (lowcost, stelle). "
        f"Se utile, intercetta menzioni a prezzi/offerte con parole chiave tipo: {keywords}. Evita elenchi.\n"
        f"Dati sintetici:\n{context}"
    )


def build_local_overview(df_kpis: pd.DataFrame, best_name: str) -> str:
    try:
        row = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
    except Exception:
        return f"{best_name} è una scelta solida per questo periodo: piste aperte e condizioni stabili."
    parts = []
    if row.get("km_open_est", 0) > 0:
        parts.append("buona disponibilità di piste")
    if row.get("pct_open", 0) >= 0.5:
        parts.append("percentuale di apertura elevata")
    if row.get("nebbia", 0) <= 0.2 and row.get("vento", 0) <= 0.2:
        parts.append("meteo tendenzialmente stabile")
    if row.get("avalanche", 3) <= 2.5:
        parts.append("rischio contenuto")
    txt = ", ".join(parts[:3]) or "equilibrio tra piste e meteo"
    return f"{best_name} è la scelta più pratica: {txt}."


# LLM Overview temporaneamente disabilitato
# @st.cache_data(ttl=3600, show_spinner=False)
# def _llm_overview_cached(prompt: str, max_tokens: int) -> tuple[str, dict]:
#     return generate_overview(prompt, max_tokens)

@st.cache_data(ttl=3600, show_spinner=False)
def _llm_overview_cached(prompt: str, max_tokens: int) -> tuple[str, dict]:
    # Testo temporaneo al posto dell'LLM
    return "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum", {}


def render_map_with_best(df_coords: pd.DataFrame, best_name: str, tooltip_km: bool = False):
    """Render a modern map with the best station highlighted."""
    if df_coords.empty or "lat" not in df_coords.columns or "lon" not in df_coords.columns:
        return None
    
    # Prepare map data
    map_data = df_coords.copy()
    map_data["highlight"] = (map_data["nome_stazione"] == best_name).astype(int)
    map_data["radius"] = np.where(map_data["highlight"] == 1, 15000, 8000)
    
    # Create layers
    layer_all = pdk.Layer(
        "ScatterplotLayer",
        data=map_data[map_data["highlight"] == 0],
        get_position='[lon, lat]',
        get_radius='radius',
        get_fill_color='[100, 100, 100, 180]',
        pickable=True,
    )
    
    layers = [layer_all]
    
    # Highlight best station
    best_pt = map_data[map_data["highlight"] == 1]
    if not best_pt.empty:
        # Pallino verde più grande per l'impianto consigliato
        best_layer = pdk.Layer(
            "ScatterplotLayer",
            data=best_pt,
            get_position='[lon, lat]',
            get_radius=15000,
            get_fill_color='[0, 200, 0, 220]',  # Verde
            pickable=False,
        )
        
        # Corona sopra il pallino verde
        crown_layer = pdk.Layer(
            "TextLayer",
            data=best_pt,
            get_position='[lon, lat]',
            get_text='👑',
            get_size=35,
            get_color='[255, 215, 0, 255]',
            get_angle=0,
            pickable=False,
        )
        
        layers.extend([best_layer, crown_layer])
    
    # View state
    view_state = pdk.ViewState(
        longitude=map_data["lon"].mean(),
        latitude=map_data["lat"].mean(),
        zoom=8,
        pitch=0,
    )
    
    # Create deck
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip={"text": "{nome_stazione}\nKm aperti: {km_open_est}" if tooltip_km else "{nome_stazione}"}
    )
    
    return deck


def main():
    st.markdown('<h1 class="modern-header">🏔️ Ski Resort Recommender</h1>', unsafe_allow_html=True)
    st.markdown('<p class="modern-section-title">Trova la stazione sciistica perfetta per il tuo weekend</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<h3 class="modern-subheader">⚙️ Configurazione</h3>', unsafe_allow_html=True)
        
        # Date selector
        data_sel = st.date_input(
            "📅 Data target",
            value=datetime.date.today(),
            min_value=datetime.date(2024, 1, 1),
            max_value=datetime.date(2025, 12, 31)
        )
        
        # Level selector
        livello = st.selectbox(
            "🎯 Livello di difficoltà",
            options=["nessuno", "base", "medio", "esperto"],
            index=0
        )
        
        # Profile selector
        profilo = st.selectbox(
            "👥 Profilo utente",
            options=SUPPORTED_PROFILES,
            index=0
        )
        
        st.markdown("**💡 Suggerimento:** Seleziona un livello e un profilo per ricevere raccomandazioni personalizzate basate su AI.")
    
    # Floating Filter Dock (always visible)
    st.markdown(
        """
        <div class="ai-dock">
            <span>⚙️ Filtri</span>
            <a href="#" onclick="document.querySelector('[data-testid=\'stDateInput\']')?.scrollIntoView({behavior: 'smooth'}); return false;">📅 Data</a>
            <a href="#" onclick="document.querySelector('[data-testid=\'stSelectbox\']')?.scrollIntoView({behavior: 'smooth'}); return false;">🎯 Livello</a>
            <a href="#" onclick="document.querySelectorAll('[data-testid=\'stSelectbox\']')[1]?.scrollIntoView({behavior: 'smooth'}); return false;">👥 Profilo</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Load data
    try:
        # Order from data_loader: (infonieve, valanghe, meteo, recensioni)
        df_infonieve, df_valanghe, df_meteo, df_recensioni = load_datasets()
    except Exception as e:
        st.error(f"Errore nel caricamento dei dati: {e}")
        return
    
    # Compute indices
    try:
        df_kpis = compute_indices(df_infonieve, df_valanghe, df_meteo, df_recensioni, data_sel)
    except Exception as e:
        st.error(f"Errore nel calcolo degli indici: {e}")
        return
    
    # Check if date is before ski season opening
    is_before_opening = False
    try:
        # Load opening dates to check if current date is before season
        df_opening = pd.read_csv("df_meteo_updated.csv")
        if "apertura_doy" in df_opening.columns:
            # Convert day of year to date for current year
            current_year = data_sel.year
            df_opening["apertura_date"] = pd.to_datetime(f"{current_year}-01-01") + pd.to_timedelta(df_opening["apertura_doy"] - 1, unit="D")
            
            # Check if selected date is before earliest opening
            earliest_opening = df_opening["apertura_date"].min()
            is_before_opening = data_sel < earliest_opening
    except Exception:
        pass
    
    # Apply profile adjustment to create indice_finale
    df_kpis = apply_profile_adjustment(df_kpis, livello, profilo)
    
    # Build ranking using the indice_finale column
    df_ranking = build_ranking(df_kpis, "indice_finale")
    
    if df_ranking.empty:
        st.warning("Nessuna stazione disponibile per i criteri selezionati.")
        return
    
    # Get best station
    best_name = df_ranking.iloc[0]["nome_stazione"]
    best_row = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
    
    # Show general information when no filters are selected
    if livello == "nessuno" and profilo == "nessuno":
        st.markdown('<h2 class="modern-subheader">📊 Panoramica generale</h2>', unsafe_allow_html=True)
        
        # Show basic stats for all stations
        if not df_kpis.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_stations = len(df_kpis)
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Stazioni totali</div>
                        <div class="kpi-value">{total_stations}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                avg_quota = df_kpis["Quota_max"].mean() if "Quota_max" in df_kpis.columns else 0
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Quota media</div>
                        <div class="kpi-value">{avg_quota:.0f}m</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                avg_km = df_kpis["kmtotal"].mean() if "kmtotal" in df_kpis.columns else 0
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Km totali medi</div>
                        <div class="kpi-value">{avg_km:.0f} km</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col4:
                open_stations = df_kpis["kmopen"].sum() if "kmopen" in df_kpis.columns else 0
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Km aperti totali</div>
                        <div class="kpi-value">{open_stations:.0f} km</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Show opening dates info if date is before season
    if is_before_opening:
        st.markdown('<h2 class="modern-subheader">📅 Informazioni per la stagione sciistica</h2>', unsafe_allow_html=True)
        st.markdown("Consulta la tabella seguente per sapere quando le piste da sci si vestono di bianco")
        
        try:
            # Load opening dates data
            df_opening = pd.read_csv("df_meteo_updated.csv")
            
            if "apertura_doy" in df_opening.columns:
                # Convert day of year to date
                df_opening["apertura_doy"] = pd.to_numeric(df_opening["apertura_doy"], errors="coerce")
                df_opening = df_opening.dropna(subset=["apertura_doy"])
                
                # Convert to dates
                df_opening["Apertura media"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(df_opening["apertura_doy"] - 1, unit="D")
                df_opening["Apertura media"] = df_opening["Apertura media"].dt.strftime("%d/%m")
                
                # Chiusura (assume 30 giorni dopo apertura)
                df_opening["Chiusura media"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(df_opening["apertura_doy"] + 29, unit="D")
                df_opening["Chiusura media"] = df_opening["Chiusura media"].dt.strftime("%d/%m")
                
                # Sort and display
                avg = df_opening.groupby("nome_stazione")["apertura_doy"].mean().reset_index()
                avg = avg.sort_values("apertura_doy", ascending=True)
                
                table = avg[["nome_stazione", "Apertura media", "Chiusura media"]].rename(
                    columns={"nome_stazione": "Impianto"}
                )
                
                # Use modern table styling
                st.markdown(
                    f"""
                    <div class="modern-table">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr>
                                    <th>Impianto</th>
                                    <th>Apertura media</th>
                                    <th>Chiusura media</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'<tr><td>{row["Impianto"]}</td><td>{row["Apertura media"]}</td><td>{row["Chiusura media"]}</td></tr>' for _, row in table.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        except Exception as e:
            st.warning(f"Impossibile caricare le date di apertura: {e}")
    
    # Hero Section - Stazione consigliata
    if not (livello == "nessuno" and profilo == "nessuno"):
        st.markdown(
            f"""
            <div class="hero-section">
                <p class="hero-subtitle">Stazione consigliata per il tuo livello</p>
                <h1 class="hero-title">{best_name}</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # KPI Grid
    if not (livello == "nessuno" and profilo == "nessuno"):
        st.markdown('<h2 class="modern-subheader">📊 Indicatori chiave</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            km_open_val = float(best_row.get("km_open_est", best_row.get("kmopen", 0) or 0))
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Km piste aperte stimati</div>
                    <div class="kpi-value">{km_open_val:.0f} km</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            pct_open_val = best_row.get("pct_open", np.nan)
            pct = float(pct_open_val) * 100 if pd.notna(pct_open_val) else 0
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">% piste aperte (stima)</div>
                    <div class="kpi-value">{pct:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            open_prob_val = float(best_row.get("open_prob", best_row.get("is_open", 0) or 0)) * 100
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">Probabilità impianto aperto</div>
                    <div class="kpi-value">{open_prob_val:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # AI Overview
    if livello != "nessuno":
        st.markdown('<h2 class="modern-subheader">✨ AI Overview</h2>', unsafe_allow_html=True)
        
        # AI Overview (TEMPORANEAMENTE DISABILITATO)
        # try:
        #     prompt = build_llm_prompt(df_kpis, best_name, livello, profilo, data_sel)
        #     with st.spinner("Generazione riepilogo AI..."):
        #         output, usage = generate_overview(prompt, max_tokens=160)
        #     
        #     if output:
        #         st.markdown(
        #             f"""
        #             <div class="ai-overview-section">
        #             <div class="ai-overview-content">{output}</div>
        #             </div>
        #             """,
        #             unsafe_allow_html=True
        #             )
        #             
        #             if isinstance(usage, dict) and usage.get("model"):
        #             st.caption(f"Modello: {usage['model']}")
        #     else:
        #         st.error("Nessuna risposta dal modello.")
        # except Exception as e:
        #     st.error(f"LLM non disponibile: {e}")
        
        # Testo temporaneo al posto dell'LLM
        output = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum"
        usage = {}
        
        st.markdown(
            f"""
            <div class="ai-overview-section">
                <div class="ai-overview-content">{output}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Level-specific information
        if livello == "base":
            st.markdown('<h3 class="modern-section-title">🎿 Per principianti: dove trovi più piste facili e condizioni stabili</h3>', unsafe_allow_html=True)
            
            # Mappa con consigliata evidenziata
            st.markdown('<h4 class="modern-section-title">🗺️ Mappa delle stazioni (consigliata evidenziata)</h4>', unsafe_allow_html=True)
            render_map_with_best(df_with_indices, best_name)

            # Podio Top 3 (estetico, senza esporre il valore indice)
            if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
                top3 = (df_with_indices.groupby("nome_stazione")["indice_base"].mean()
                        .sort_values(ascending=False).head(3).reset_index())
                if len(top3) > 0:
                    names = top3["nome_stazione"].tolist()
                    first = names[0] if len(names) > 0 else ""
                    second = names[1] if len(names) > 1 else ""
                    third = names[2] if len(names) > 2 else ""
                    st.markdown('<h4 class="modern-section-title">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                    st.markdown("""
                    <div class='podium-container'>
                      <div class='podium-step second'>
                        <div class='podium-platform second'>
                          <div class='podium-medal'>🥈</div>
                          <div class='podium-name'>%s</div>
                        </div>
                      </div>
                      <div class='podium-step first'>
                        <div class='podium-platform first'>
                          <div class='podium-medal'>🥇</div>
                          <div class='podium-name'>%s</div>
                        </div>
                      </div>
                      <div class='podium-step third'>
                        <div class='podium-platform third'>
                          <div class='podium-medal'>🥉</div>
                          <div class='podium-name'>%s</div>
                        </div>
                      </div>
                    </div>
                    """ % (second, first, third), unsafe_allow_html=True)
            
            # Probabilità meteo (±3 giorni su anni precedenti per date future)
            meteo_data = get_historical_data_for_date(df_meteo, data_sel, days_range=3)
            if not meteo_data.empty:
                st.markdown('<h4 class="modern-section-title">🌤️ Probabilità condizioni meteo (storico ±3 giorni)</h4>', unsafe_allow_html=True)
                # baseline ±15 giorni sugli anni precedenti
                baseline = get_historical_data_for_date(df_meteo, data_sel, days_range=15)
                col1, col2 = st.columns(2)
                with col1:
                    prob_nebbia = float(meteo_data.get("nebbia", 0).mean() * 100)
                    baseline_nebbia = float((baseline.get("nebbia", 0).mean() * 100) if not baseline.empty else 0)
                    fig_n = create_speedometer(prob_nebbia, baseline_nebbia, "Prob. Nebbia", "%")
                    st.plotly_chart(fig_n, use_container_width=True)
                with col2:
                    prob_pioggia = float(meteo_data.get("pioggia", 0).mean() * 100)
                    baseline_pioggia = float((baseline.get("pioggia", 0).mean() * 100) if not baseline.empty else 0)
                    fig_p = create_speedometer(prob_pioggia, baseline_pioggia, "Prob. Pioggia", "%")
                    st.plotly_chart(fig_p, use_container_width=True)
                st.caption("Nota: probabilità calcolate sui dati storici per periodi simili; il delta confronta con la media degli anni precedenti nella finestra ±15 giorni.")
            else:
                st.warning("Dati meteo non disponibili per questa data")

            # Barre impilate piste verdi/blu ordinate per indice_base
            if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
                st.markdown('<h4 class="modern-section-title">🎿 Distribuzione piste verdi e blu</h4>', unsafe_allow_html=True)
                piste_base = df_with_indices[["nome_stazione", "Piste_verdi", "Piste_blu", "indice_base"]].drop_duplicates()
                piste_base = piste_base.sort_values("indice_base", ascending=False)
                fig_piste_base = px.bar(
                    piste_base,
                    x="nome_stazione",
                    y=["Piste_verdi", "Piste_blu"],
                    title="Piste verdi e blu per stazione (ordinate per indice base)",
                    color_discrete_map={"Piste_verdi": "#4CAF50", "Piste_blu": "#2196F3"}
                )
                fig_piste_base.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_piste_base, use_container_width=True)
            
            # Sezione Festaiolo (profilo) – solo se selezionato
            if profilo == "festaiolo":
                st.markdown('<h4 class="modern-section-title">🎉 Profilo: Festaiolo</h4>', unsafe_allow_html=True)
                # Grafico 1: km di sci notturno (asse X), impianti su Y
                try:
                    df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                    if not df_night.empty:
                        fig_night = px.bar(
                            df_night.sort_values("Scii_notte", ascending=False),
                            x="nome_stazione", y="Scii_notte",
                            title="Km di sci notturno per impianto",
                            labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"}
                        )
                        st.plotly_chart(fig_night, use_container_width=True)
                except Exception:
                    pass

            if profilo == "familiare":
                st.markdown('<h4 class="modern-section-title">👨‍👩‍👧‍👦 Profilo: Familiare</h4>', unsafe_allow_html=True)
                # 1) Numero aree bambini per impianto
                try:
                    if "Area_bambini" in df_with_indices.columns:
                        df_kids = (
                            df_with_indices[["nome_stazione", "Area_bambini"]]
                            .drop_duplicates().fillna(0)
                            .sort_values("Area_bambini", ascending=False)
                        )
                        fig_kids = px.bar(
                            df_kids,
                            x="nome_stazione", y="Area_bambini",
                            title="Numero aree bambini per impianto",
                            labels={"nome_stazione": "Impianto", "Area_bambini": "Aree bambini"}
                        )
                        fig_kids.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_kids, use_container_width=True)
                    else:
                        st.info("Dato non disponibile: 'Area_bambini'")
                except Exception:
                    pass

                # 2) Prezzi medi per impianto (skipass, scuola, noleggio)
                try:
                    price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                    if price_cols:
                        df_price = (
                            df_with_indices[["nome_stazione"] + price_cols]
                            .drop_duplicates().fillna(0)
                        )
                        melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                        fig_prices = px.bar(
                            melted_p,
                            x="Prezzo", y="nome_stazione", color="Voce",
                            barmode="group",
                            title="Prezzi medi per impianto (skipass, scuola, noleggio)",
                            labels={"nome_stazione": "Impianto", "Prezzo": "€"}
                        )
                        st.plotly_chart(fig_prices, use_container_width=True)
                    else:
                        st.info("Dati prezzo non disponibili (skipass/scuola/noleggio)")
                except Exception:
                    pass
                
                # 3) AI Overview – Famiglia (TEMPORANEAMENTE DISABILITATO)
                st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Famiglia</h4>', unsafe_allow_html=True)
                st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")
            
        elif livello == "medio":
            st.markdown('<h3 class="modern-section-title">🎿 Per intermedi: equilibrio tra piste e sicurezza</h3>', unsafe_allow_html=True)
            
            # Mappa con consigliata evidenziata
            st.markdown('<h4 class="modern-section-title">🗺️ Mappa delle stazioni (consigliata evidenziata)</h4>', unsafe_allow_html=True)
            render_map_with_best(df_with_indices, best_name)

            # Podio Top 3 per indice_medio
            if "indice_medio" in df_with_indices.columns and not df_with_indices.empty:
                top3m = (
                    df_with_indices.groupby("nome_stazione")["indice_medio"].mean()
                    .sort_values(ascending=False).head(3).reset_index()
                )
                if not top3m.empty:
                    names = top3m["nome_stazione"].tolist()
                    first = names[0] if len(names) > 0 else ""
                    second = names[1] if len(names) > 1 else ""
                    third = names[2] if len(names) > 2 else ""
                    st.markdown('<h4 class="modern-section-title">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class='podium-container'>
                          <div class='podium-step second'>
                            <div class='podium-platform second'>
                              <div class='podium-medal'>🥈</div>
                              <div class='podium-name'>{second}</div>
                            </div>
                          </div>
                          <div class='podium-step first'>
                            <div class='podium-platform first'>
                              <div class='podium-medal'>🥇</div>
                              <div class='podium-name'>{first}</div>
                            </div>
                          </div>
                          <div class='podium-step third'>
                            <div class='podium-platform third'>
                              <div class='podium-medal'>🥉</div>
                              <div class='podium-name'>{third}</div>
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Meteo compatto (5 mini-donut) per la stazione consigliata
            try:
                meteo_win = get_historical_data_for_date(df_meteo, data_sel, days_range=3)
                if not meteo_win.empty:
                    m_best = meteo_win[meteo_win.get("nome_stazione", "").astype(str) == best_name]
                    if m_best.empty:
                        m_best = meteo_win
                    pioggia = float(m_best.get("pioggia", 0).mean() * 100)
                    nebbia = float(m_best.get("nebbia", 0).mean() * 100)
                    sole    = float(m_best.get("sole", 0).mean() * 100)
                    vento   = float(m_best.get("vento", 0).mean() * 100)
                    neve_pct = 0.0
                    snow_win = get_historical_data_for_date(df_infonieve, data_sel, days_range=3)
                    if not snow_win.empty:
                        s_best = snow_win[snow_win.get("nome_stazione", "").astype(str) == best_name]
                        if s_best.empty:
                            s_best = snow_win
                        cm = s_best.get("espesor_medio", 0).fillna(0)
                        if not cm.empty:
                            cmin, cmax = cm.min(), cm.max()
                            neve_pct = float(((cm.mean() - cmin) / (cmax - cmin) * 100) if cmax > cmin else 0)

                    def donut(value, label, color):
                        val = max(0.0, min(100.0, value))
                        rem = 100 - val
                        fig = go.Figure(
                            data=[go.Pie(values=[val, rem], hole=0.72, sort=False, direction='clockwise', marker_colors=[color, 'rgba(255,255,255,0.08)'], textinfo='none')]
                        )
                        fig.add_annotation(text=f"{val:.0f}%", x=0.5, y=0.5, showarrow=False, font=dict(size=22, color='#e6efff'))
                        fig.update_layout(
                            title=dict(text=label, font=dict(size=16), y=0.9),
                            showlegend=False, margin=dict(l=0, r=0, t=50, b=10), height=220
                        )
                        return fig

                    st.markdown('<h4 class="modern-section-title">🌤️ Meteo (storico ±3 giorni)</h4>', unsafe_allow_html=True)
                    r1c1, r1c2, r1c3 = st.columns(3)
                    with r1c1:
                        st.plotly_chart(donut(pioggia, "Pioggia", "#60A5FA"), use_container_width=True)
                    with r1c2:
                        st.plotly_chart(donut(sole, "Sole", "#F59E0B"), use_container_width=True)
                    with r1c3:
                        st.plotly_chart(donut(nebbia, "Nebbia", "#94a3b8"), use_container_width=True)
                    st.write("")
                    r2c1, r2c2, r2c3 = st.columns([1,1,1])
                    with r2c1:
                        st.plotly_chart(donut(vento, "Vento", "#00C8FF"), use_container_width=True)
                    with r2c2:
                        st.plotly_chart(donut(neve_pct, "Neve", "#6EE7B7"), use_container_width=True)
                    with r2c3:
                        st.write("")
            except Exception:
                pass

            # Barre: piste blu/rosse ordinate per indice_medio
            if not df_with_indices.empty and "indice_medio" in df_with_indices.columns:
                st.markdown('<h4 class="modern-section-title">🎿 Piste blu e rosse per stazione (ordinate per indice medio)</h4>', unsafe_allow_html=True)
                piste = df_with_indices[["nome_stazione", "Piste_blu", "Piste_rosse", "indice_medio"]].drop_duplicates()
                piste = piste.sort_values("indice_medio", ascending=False)
                melted = piste.melt("nome_stazione", value_vars=["Piste_blu", "Piste_rosse"], var_name="Tipo", value_name="Numero")
                fig = px.bar(
                    melted,
                    x="nome_stazione", y="Numero", color="Tipo", barmode="stack",
                    color_discrete_map={"Piste_blu": "#60A5FA", "Piste_rosse": "#FB7185"},
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            
            # Sezione Festaiolo (profilo)
            if profilo == "festaiolo":
                st.markdown('<h4 class="modern-section-title">🎉 Profilo: Festaiolo</h4>', unsafe_allow_html=True)
                try:
                    df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                    if not df_night.empty:
                        fig_night = px.bar(
                            df_night.sort_values("Scii_notte", ascending=False),
                            x="nome_stazione", y="Scii_notte",
                            title="Km di sci notturno per impianto",
                            labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"}
                        )
                        st.plotly_chart(fig_night, use_container_width=True)
                except Exception:
                    pass
                try:
                    cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                    df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                    if not df_acts.empty:
                        melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Attività", value_name="Valore")
                        fig_acts = px.bar(
                            melted, x="nome_stazione", y="Valore", color="Attività",
                            barmode="group", title="Snowpark e Superpipe"
                        )
                        st.plotly_chart(fig_acts, use_container_width=True)
                except Exception:
                    pass
                # AI Overview – Festa (TEMPORANEAMENTE DISABILITATO)
                st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Festa</h4>', unsafe_allow_html=True)
                st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")

            # Sezione Familiare (profilo)
            if profilo == "familiare":
                st.markdown('<h4 class="modern-section-title">👨‍👩‍👧‍👦 Profilo: Familiare</h4>', unsafe_allow_html=True)
                # 1) Numero aree bambini per impianto
                try:
                    if "Area_bambini" in df_with_indices.columns:
                        df_kids = (
                            df_with_indices[["nome_stazione", "Area_bambini"]]
                            .drop_duplicates().fillna(0)
                            .sort_values("Area_bambini", ascending=False)
                        )
                        fig_kids = px.bar(
                            df_kids,
                            x="nome_stazione", y="Area_bambini",
                            title="Numero aree bambini per impianto",
                            labels={"nome_stazione": "Impianto", "Area_bambini": "Aree bambini"}
                        )
                        fig_kids.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_kids, use_container_width=True)
                    else:
                        st.info("Dato non disponibile: 'Area_bambini'")
                except Exception:
                    pass

                # 2) Prezzi medi per impianto (skipass, scuola, noleggio)
                try:
                    price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                    if price_cols:
                        df_price = (
                            df_with_indices[["nome_stazione"] + price_cols]
                            .drop_duplicates().fillna(0)
                        )
                        melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                        fig_prices = px.bar(
                            melted_p,
                            x="Prezzo", y="nome_stazione", color="Voce",
                            barmode="group",
                            title="Prezzi medi per impianto (skipass, scuola, noleggio)",
                            labels={"nome_stazione": "Impianto", "Prezzo": "€"}
                        )
                        st.plotly_chart(fig_prices, use_container_width=True)
                    else:
                        st.info("Dati prezzo non disponibili (skipass/scuola/noleggio)")
                except Exception:
                    pass

                # 3) AI Overview – Famiglia (TEMPORANEAMENTE DISABILITATO)
                st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Famiglia</h4>', unsafe_allow_html=True)
                st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")
            
        elif livello == "esperto":
            st.markdown('<h3 class="modern-section-title">🎿 Per esperti: caratteristiche tecniche e chilometri</h3>', unsafe_allow_html=True)
            
            # Mappa con consigliata evidenziata
            st.markdown('<h4 class="modern-section-title">🗺️ Mappa delle stazioni (consigliata evidenziata)</h4>', unsafe_allow_html=True)
            render_map_with_best(df_with_indices, best_name)

            # Podio Top 3 per indice_esperto
            if not df_with_indices.empty and "indice_esperto" in df_with_indices.columns:
                top3e = (
                    df_with_indices.groupby("nome_stazione")["indice_esperto"].mean()
                    .sort_values(ascending=False).head(3).reset_index()
                )
                if not top3e.empty:
                    names = top3e["nome_stazione"].tolist()
                    first = names[0] if len(names) > 0 else ""
                    second = names[1] if len(names) > 1 else ""
                    third = names[2] if len(names) > 2 else ""
                    st.markdown('<h4 class="modern-section-title">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                    st.markdown(
                        f"""
                        <div class='podium-container'>
                          <div class='podium-step second'>
                            <div class='podium-platform second'>
                              <div class='podium-medal'>🥈</div>
                              <div class='podium-name'>{second}</div>
                            </div>
                          </div>
                          <div class='podium-step first'>
                            <div class='podium-platform first'>
                              <div class='podium-medal'>🥇</div>
                              <div class='podium-name'>{first}</div>
                            </div>
                          </div>
                          <div class='podium-step third'>
                            <div class='podium-platform third'>
                              <div class='podium-medal'>🥉</div>
                              <div class='podium-name'>{third}</div>
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Speedometer rischio valanghe (1-5) per la stazione consigliata (con delta vs baseline ±15g)
            try:
                brow = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
                risk = float(brow.get("avalanche", 3.0))
                # baseline: media danger_level_avg nella finestra ±15 giorni su anni precedenti
                base_val = get_historical_data_for_date(df_valanghe, data_sel, days_range=15)
                bstation = base_val[base_val.get("nome_stazione", "").astype(str) == best_name]
                baseline = float(bstation.get("danger_level_avg", 0).mean()) if not bstation.empty else 0.0
                # Due livelli: subheader esterno e delta in basso, numero centrato
                d = risk - baseline
                st.markdown('<h4 class="modern-section-title">⚠️ Rischio valanghe (1-5)</h4>', unsafe_allow_html=True)
                fig_risk = create_speedometer(risk, baseline, "Rischio valanghe", "")
                # Delta come annotation molto in basso
                fig_risk.add_annotation(x=0.5, y=0.05, xref="paper", yref="paper",
                                        text=f"Δ {d:+.2f} vs media ±15g", showarrow=False,
                                        font=dict(size=12, color="#16a34a" if d < 0 else "#ef4444"))
                fig_risk.update_layout(height=230, margin=dict(l=10, r=10, t=20, b=40))
                st.plotly_chart(fig_risk, use_container_width=True)
            except Exception:
                pass

            # KPI tecnici (stazione consigliata)
            try:
                top_best = df_with_indices[df_with_indices["nome_stazione"] == best_name]
                if not top_best.empty:
                    st.markdown('<h4 class="modern-section-title">🎯 KPI tecnici</h4>', unsafe_allow_html=True)
                    vals = top_best[["Snowpark", "Area_gare", "Slalom", "Superpipe"]].fillna(0).mean()
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Snowpark</div><div class="kpi-value">{vals.get('Snowpark',0):.0f}</div></div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Area gare</div><div class="kpi-value">{vals.get('Area_gare',0):.0f}</div></div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Slalom</div><div class="kpi-value">{vals.get('Slalom',0):.0f}</div></div>""", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Superpipe</div><div class="kpi-value">{vals.get('Superpipe',0):.0f}</div></div>""", unsafe_allow_html=True)
            except Exception:
                pass

            # Quota max: grafico a barre (Top 10) con scala 2000-3000 m
            try:
                quota = (
                    df_with_indices.groupby("nome_stazione")["Quota_max"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
                )
                if not quota.empty:
                    fig_quota = px.bar(quota, x="nome_stazione", y="Quota_max", title="Quota max per stazione", labels={"nome_stazione": "Stazione", "Quota_max": "Quota max (m)"})
                    fig_quota.update_layout(xaxis_tickangle=-45, yaxis=dict(range=[2000, 2800]))
                    st.plotly_chart(fig_quota, use_container_width=True)
            except Exception:
                pass

            # Km totali: solo totali per le prime 8 stazioni
            top_total = df_kpis.sort_values("km_total_est", ascending=False).head(8)
            fig_bar_total = px.bar(top_total, x="nome_stazione", y="km_total_est", title="Km piste totali", labels={"nome_stazione": "Stazione", "km_total_est": "Km totali"})
            fig_bar_total.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar_total, use_container_width=True)

            # Sezione Festaiolo (profilo)
            if profilo == "festaiolo":
                st.markdown('<h4 class="modern-section-title">🎉 Profilo: Festaiolo</h4>', unsafe_allow_html=True)
                try:
                    df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                    if not df_night.empty:
                        fig_night = px.bar(
                            df_night.sort_values("Scii_notte", ascending=False),
                            x="nome_stazione", y="Scii_notte",
                            title="Km di sci notturno per impianto",
                            labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"}
                        )
                        st.plotly_chart(fig_night, use_container_width=True)
                except Exception:
                    pass
                try:
                    cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                    df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                    if not df_acts.empty:
                        melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Attività", value_name="Valore")
                        fig_acts = px.bar(
                            melted, x="nome_stazione", y="Valore", color="Attività",
                            barmode="group", title="Snowpark e Superpipe"
                        )
                        st.plotly_chart(fig_acts, use_container_width=True)
                except Exception:
                    pass
                # AI Overview – Festa (TEMPORANEAMENTE DISABILITATO)
                st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Festa</h4>', unsafe_allow_html=True)
                st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")

            # Sezione Familiare (profilo)
            if profilo == "familiare":
                st.markdown('<h4 class="modern-section-title">👨‍👩‍👧‍👦 Profilo: Familiare</h4>', unsafe_allow_html=True)
                # 1) Numero aree bambini per impianto
                try:
                    if "Area_bambini" in df_with_indices.columns:
                        df_kids = (
                            df_with_indices[["nome_stazione", "Area_bambini"]]
                            .drop_duplicates().fillna(0)
                            .sort_values("Area_bambini", ascending=False)
                        )
                        fig_kids = px.bar(
                            df_kids,
                            x="nome_stazione", y="Area_bambini",
                            title="Numero aree bambini per impianto",
                            labels={"nome_stazione": "Impianto", "Area_bambini": "Aree bambini"}
                        )
                        fig_kids.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_kids, use_container_width=True)
                    else:
                        st.info("Dato non disponibile: 'Area_bambini'")
                except Exception:
                    pass

                # 2) Prezzi medi per impianto (skipass, scuola, noleggio)
                try:
                    price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                    if price_cols:
                        df_price = (
                            df_with_indices[["nome_stazione"] + price_cols]
                            .drop_duplicates().fillna(0)
                        )
                        melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                        fig_prices = px.bar(
                            melted_p,
                            x="Prezzo", y="nome_stazione", color="Voce",
                            barmode="group",
                            title="Prezzi medi per impianto (skipass, scuola, noleggio)",
                            labels={"nome_stazione": "Impianto", "Prezzo": "€"}
                        )
                        st.plotly_chart(fig_prices, use_container_width=True)
                    else:
                        st.info("Dati prezzo non disponibili (skipass/scuola/noleggio)")
                except Exception:
                    pass

                # 3) AI Overview – Famiglia (TEMPORANEAMENTE DISABILITATO)
                st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Famiglia</h4>', unsafe_allow_html=True)
                st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")

    # Sezione Profilo Low-Cost (solo se selezionato, dopo tutti i livelli)
    if profilo == "lowcost":
        st.markdown("---")
        st.markdown('<h3 class="modern-section-title">💰 Profilo: Low-Cost</h3>', unsafe_allow_html=True)
        
        # 1) Grafico a barre: costi di ski pass, scuola sci e noleggio
        try:
            price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
            
            if price_cols:
                df_price_lowcost = (
                    df_with_indices[["nome_stazione"] + price_cols]
                    .drop_duplicates().fillna(0)
                )
                # Ordina per prezzo medio totale
                df_price_lowcost["prezzo_medio"] = df_price_lowcost[price_cols].mean(axis=1)
                df_price_lowcost = df_price_lowcost.sort_values("prezzo_medio", ascending=True)
                
                melted_prices = df_price_lowcost.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                fig_prices_lowcost = px.bar(
                    melted_prices,
                    x="nome_stazione", y="Prezzo", color="Voce",
                    barmode="group",
                    title="💰 Costi per impianto (skipass, scuola, noleggio) - Ordine crescente per prezzo medio",
                    labels={"nome_stazione": "Impianto", "Prezzo": "€", "Voce": "Tipo costo"},
                    color_discrete_map={"Prezzo_skipass": "#FF6B6B", "Prezzo_scuola": "#4ECDC4", "Prezzo_noleggio": "#45B7D1"}
                )
                fig_prices_lowcost.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prices_lowcost, use_container_width=True)
            else:
                st.info("Dati prezzo non disponibili per l'analisi low-cost")
        except Exception as e:
            st.warning(f"Errore nella visualizzazione prezzi: {e}")
        
        # 2) Tabella rapporto kmopen/costo skipass
        try:
            if not df_with_indices.empty and "kmopen" in df_with_indices.columns and "Prezzo_skipass" in df_with_indices.columns:
                # Raggruppa per stazione e calcola le medie per avere una riga per stazione
                df_ratio = (
                    df_with_indices.groupby("nome_stazione")
                    .agg({
                        "kmopen": "mean",
                        "Prezzo_skipass": "mean"
                    })
                    .reset_index()
                    .dropna()
                )
                
                if not df_ratio.empty:
                    # Calcola il rapporto euro/km (costo per chilometro di pista)
                    df_ratio["rapporto_euro_km"] = np.where(
                        df_ratio["kmopen"] > 0,
                        df_ratio["Prezzo_skipass"] / df_ratio["kmopen"],
                        0
                    )
                    
                    # Ordina per rapporto migliore (meno euro per km = migliore rapporto)
                    df_ratio = df_ratio.sort_values("rapporto_euro_km", ascending=True)
                    
                    # Prepara tabella finale
                    df_table = df_ratio[["nome_stazione", "Prezzo_skipass", "kmopen", "rapporto_euro_km"]].copy()
                    
                    # Rinomina colonne per la visualizzazione
                    rename_map = {
                        "nome_stazione": "🏔️ Impianto",
                        "Prezzo_skipass": "💶 Skipass (€)",
                        "kmopen": "🛷 Km Aperti",
                        "rapporto_euro_km": "💸 €/Km"
                    }
                    df_table = df_table.rename(columns=rename_map)
                    
                    # Formatta i valori
                    if "💶 Skipass (€)" in df_table.columns:
                        df_table["💶 Skipass (€)"] = df_table["💶 Skipass (€)"].round(2)
                    if "🛷 Km Aperti" in df_table.columns:
                        df_table["🛷 Km Aperti"] = df_table["🛷 Km Aperti"].round(1)
                    if "💸 €/Km" in df_table.columns:
                        df_table["💸 €/Km"] = df_table["💸 €/Km"].round(2)
                    
                    st.markdown('<h4 class="modern-section-title">📊 Rapporto Qualità-Prezzo: Euro per Chilometro</h4>', unsafe_allow_html=True)
                    st.markdown("""
                    **Indice calcolato:**
                    - **€/Km**: meno euro per chilometro di pista = migliore rapporto qualità-prezzo
                    """)
                    
                    # Mostra tutte le stazioni
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                else:
                    st.info("Dati insufficienti per calcolare il rapporto kmopen/costo skipass")
            else:
                st.info("Colonne 'kmopen' o 'Prezzo_skipass' non disponibili per l'analisi")
        except Exception as e:
            st.warning(f"Errore nel calcolo del rapporto: {e}")
        
        # 3) AI Overview – Low-Cost (TEMPORANEAMENTE DISABILITATO)
        st.markdown('<h4 class="modern-section-title">🤖 AI Overview – Low-Cost</h4>', unsafe_allow_html=True)
        st.info("AI Overview temporaneamente disabilitato. Funzionalità in fase di ripristino.")

    # Opening dates table
    if livello == "nessuno" and profilo == "nessuno":
        st.markdown('<h2 class="modern-subheader">📅 Date di apertura medie</h2>', unsafe_allow_html=True)
        
        try:
            # Load opening dates data
            df_opening = pd.read_csv("df_meteo_updated.csv")
            
            if "apertura_doy" in df_opening.columns:
                # Convert day of year to date
                df_opening["apertura_doy"] = pd.to_numeric(df_opening["apertura_doy"], errors="coerce")
                df_opening = df_opening.dropna(subset=["apertura_doy"])
                
                # Convert to dates
                df_opening["Apertura media"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(df_opening["apertura_doy"] - 1, unit="D")
                df_opening["Apertura media"] = df_opening["Apertura media"].dt.strftime("%d/%m")
                
                # Chiusura (assume 30 giorni dopo apertura)
                df_opening["Chiusura media"] = pd.to_datetime("2024-01-01") + pd.to_timedelta(df_opening["apertura_doy"] + 29, unit="D")
                df_opening["Chiusura media"] = df_opening["Chiusura media"].dt.strftime("%d/%m")
                
                # Sort and display
                avg = df_opening.groupby("nome_stazione")["apertura_doy"].mean().reset_index()
                avg = avg.sort_values("apertura_doy", ascending=True)
                
                table = avg[["nome_stazione", "Apertura media", "Chiusura media"]].rename(
                    columns={"nome_stazione": "Impianto"}
                )
                
                st.info("Consulta la tabella seguente per sapere quando le piste da sci si vestono di bianco")
                
                # Use modern table styling
                st.markdown(
                    f"""
                    <div class="modern-table">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr>
                                    <th>Impianto</th>
                                    <th>Apertura media</th>
                                    <th>Chiusura media</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'<tr><td>{row["Impianto"]}</td><td>{row["Apertura media"]}</td><td>{row["Chiusura media"]}</td></tr>' for _, row in table.iterrows()])}
                            </tbody>
                        </table>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        except Exception as e:
            st.warning(f"Impossibile caricare le date di apertura: {e}")

    # Main content sections
    if livello != "nessuno":
        # Approfondimenti
        st.markdown('<h2 class="modern-subheader">📊 Approfondimenti</h2>', unsafe_allow_html=True)
        
        # Top stations by km open
        if "km_open_est" in df_kpis.columns:
            top_km = df_kpis.nlargest(8, "km_open_est")
            if not top_km.empty:
                fig_km = px.bar(
                    top_km, 
                    x="nome_stazione", 
                    y="km_open_est", 
                    title="Km piste aperte per stazione",
                    labels={"nome_stazione": "Stazione", "km_open_est": "Km aperti"}
                )
                fig_km.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_km, use_container_width=True)
        
        # Quota max per stazione
        quota = df_kpis[["nome_stazione", "Quota_max"]].dropna()
        if not quota.empty:
            fig_quota = px.bar(
                quota, 
                x="nome_stazione", 
                y="Quota_max", 
                title="Quota max per stazione", 
                labels={"nome_stazione": "Stazione", "Quota_max": "Quota max (m)"}
            )
            fig_quota.update_layout(xaxis_tickangle=-45, yaxis=dict(range=[2000, 2800]))
            # Aggiungi i valori sulle barre
            fig_quota.update_traces(texttemplate='%{y:.0f}m', textposition='outside')
            st.plotly_chart(fig_quota, use_container_width=True)
        
        # Km totali
        if "km_total_est" in df_kpis.columns:
            top_total = df_kpis.sort_values("km_total_est", ascending=False).head(8)
            fig_bar_total = px.bar(
                top_total, 
                x="nome_stazione", 
                y="km_total_est", 
                title="Km piste totali", 
                labels={"nome_stazione": "Stazione", "km_total_est": "Km totali"}
            )
            fig_bar_total.update_layout(xaxis_tickangle=-45)
            # Aggiungi i valori sulle barre
            fig_bar_total.update_traces(texttemplate='%{y:.0f} km', textposition='outside')
            st.plotly_chart(fig_bar_total, use_container_width=True)
        
        # Prezzi medi per impianto
        try:
            price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_kpis.columns]
            if price_cols:
                df_price = (
                    df_kpis[["nome_stazione"] + price_cols]
                    .drop_duplicates().fillna(0)
                )
                # Mappa nomi colonne per rimuovere underscore
                name_mapping = {
                    "Prezzo_skipass": "Skipass",
                    "Prezzo_scuola": "Scuola",
                    "Prezzo_noleggio": "Noleggio"
                }
                df_price_renamed = df_price.rename(columns=name_mapping)
                melted_p = df_price_renamed.melt("nome_stazione", value_vars=list(name_mapping.values()), var_name="Voce", value_name="Prezzo")
                fig_prices = px.bar(
                    melted_p,
                    x="Prezzo", 
                    y="nome_stazione", 
                    color="Voce",
                    barmode="group",
                    title="Prezzi medi per impianto (skipass, scuola, noleggio)",
                    labels={"Prezzo": "€", "nome_stazione": "Impianto"},
                    orientation='h'
                )
                st.plotly_chart(fig_prices, use_container_width=True)
        except Exception:
            pass
        

        
        # KPI tecnici
        if "Snowpark" in df_kpis.columns:
            st.markdown('<h3 class="modern-section-title">KPI tecnici</h3>', unsafe_allow_html=True)
            
            top_best = df_kpis.nlargest(5, "km_open_est") if "km_open_est" in df_kpis.columns else df_kpis.head(5)
            tech_cols = [col for col in ["Snowpark", "Area_gare", "Slalom", "Superpipe"] if col in top_best.columns]
            if tech_cols:
                vals = top_best[tech_cols].fillna(0).mean()
            else:
                vals = pd.Series([0, 0, 0, 0], index=["Snowpark", "Area_gare", "Slalom", "Superpipe"])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Snowpark</div>
                        <div class="kpi-value">{vals.get('Snowpark',0):.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Area gare</div>
                        <div class="kpi-value">{vals.get('Area_gare',0):.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col3:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Slalom</div>
                        <div class="kpi-value">{vals.get('Slalom',0):.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col4:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">Superpipe</div>
                        <div class="kpi-value">{vals.get('Superpipe',0):.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Mappa
        st.markdown('<h3 class="modern-section-title">🗺️ Mappa</h3>', unsafe_allow_html=True)
        
        # Prepare map data
        map_cols = ["nome_stazione", "lat", "lon"]
        if "km_open_est" in df_kpis.columns:
            map_cols.append("km_open_est")
        map_data = df_kpis[map_cols].dropna()
        if not map_data.empty:
            map_data["highlight"] = (map_data["nome_stazione"] == best_name).astype(int)
            map_data["radius"] = np.where(map_data["highlight"] == 1, 15000, 8000)
            
            # Create layers
            layer_all = pdk.Layer(
                "ScatterplotLayer",
                data=map_data[map_data["highlight"] == 0],
                get_position='[lon, lat]',
                get_radius='radius',
                get_fill_color='[100, 100, 100, 180]',
                pickable=True,
            )
            
            # Highlight best station
            best_pt = map_data[map_data["highlight"] == 1]
            if not best_pt.empty:
                # Pallino verde più grande per l'impianto consigliato
                best_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=best_pt,
                    get_position='[lon, lat]',
                    get_radius=15000,
                    get_fill_color='[0, 200, 0, 220]',  # Verde
                    pickable=False,
                )
                
                # Corona sopra il pallino verde
                crown_layer = pdk.Layer(
                    "TextLayer",
                    data=best_pt,
                    get_position='[lon, lat]',
                    get_text='👑',
                    get_size=35,
                    get_color='[255, 215, 0, 255]',
                    get_angle=0,
                    pickable=False,
                )
                
                layers = [layer_all, best_layer, crown_layer]
            else:
                layers = [layer_all]
            
            # View state
            view_state = pdk.ViewState(
                longitude=map_data["lon"].mean(),
                latitude=map_data["lat"].mean(),
                zoom=8,
                pitch=0,
            )
            
            # Create deck
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip={"text": "{nome_stazione}\nKm aperti: {km_open_est}" if "km_open_est" in map_data.columns else "{nome_stazione}"}
            )
            
            st.pydeck_chart(deck, use_container_width=True)
    
    # Expert level specific content
    if livello == "esperto":
        st.markdown('<h2 class="modern-subheader">🏆 Classifica Top 3</h2>', unsafe_allow_html=True)
        
        # Get top 3 by expert index
        df_with_indices = df_ranking.copy()
        if "indice_esperto" in df_with_indices.columns:
            top_3 = df_with_indices.nlargest(3, "indice_esperto")
            
            if not top_3.empty:
                st.markdown(
                    """
                    <div class="podium-container">
                    """,
                    unsafe_allow_html=True
                )
                
                # First place
                st.markdown(
                    f"""
                    <div class="podium-step">
                        <div class="podium-1">
                            <div class="podium-medal">🥇</div>
                            <div class="podium-name">{top_3.iloc[0]['nome_stazione']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Second place
                if len(top_3) > 1:
                    st.markdown(
                        f"""
                        <div class="podium-step">
                            <div class="podium-2">
                                <div class="podium-medal">🥈</div>
                                <div class="podium-name">{top_3.iloc[1]['nome_stazione']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Third place
                if len(top_3) > 2:
                    st.markdown(
                        f"""
                        <div class="podium-step">
                            <div class="podium-3">
                                <div class="podium-medal">🥉</div>
                                <div class="podium-name">{top_3.iloc[2]['nome_stazione']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Base/Medium level specific content
    elif livello in ["base", "medio"]:
        st.markdown('<h2 class="modern-subheader">🏆 Classifica Top 3</h2>', unsafe_allow_html=True)
        
        # Get top 3 by base index
        df_with_indices = df_ranking.copy()
        if "indice_base" in df_with_indices.columns:
            top_3 = df_with_indices.nlargest(3, "indice_base")
            
            if not top_3.empty:
                st.markdown(
                    """
                    <div class="podium-container">
                    """,
                    unsafe_allow_html=True
                )
                
                # First place
                st.markdown(
                    f"""
                    <div class="podium-step">
                        <div class="podium-1">
                            <div class="podium-medal">🥇</div>
                            <div class="podium-name">{top_3.iloc[0]['nome_stazione']}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Second place
                if len(top_3) > 1:
                    st.markdown(
                        f"""
                        <div class="podium-step">
                            <div class="podium-2">
                                <div class="podium-medal">🥈</div>
                                <div class="podium-name">{top_3.iloc[1]['nome_stazione']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Third place
                if len(top_3) > 2:
                    st.markdown(
                        f"""
                        <div class="podium-step">
                            <div class="podium-3">
                                <div class="podium-medal">🥉</div>
                                <div class="podium-name">{top_3.iloc[2]['nome_stazione']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Weather probability charts
    if livello != "nessuno":
        st.markdown('<h3 class="modern-section-title">🌤️ Probabilità condizioni meteo (storico ±3 giorni)</h3>', unsafe_allow_html=True)
        
        # Get historical data
        try:
            historical_data = get_historical_data_for_date(df_meteo, data_sel)
            
            if not historical_data.empty:
                # Create speedometer charts
                col1, col2 = st.columns(2)
                
                with col1:
                    # Sunshine probability
                    sun_prob = historical_data["sole"].mean()
                    fig_sun = create_speedometer(
                        sun_prob, 
                        historical_data["sole"].mean(), 
                        "Probabilità sole", 
                        "%"
                    )
                    st.plotly_chart(fig_sun, use_container_width=True)
                
                with col2:
                    # Rain probability
                    rain_prob = historical_data["pioggia"].mean()
                    fig_rain = create_speedometer(
                        rain_prob, 
                        historical_data["pioggia"].mean(), 
                        "Probabilità pioggia", 
                        "%"
                    )
                    st.plotly_chart(fig_rain, use_container_width=True)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    # Fog probability
                    fog_prob = historical_data["nebbia"].mean()
                    fig_fog = create_speedometer(
                        fog_prob, 
                        historical_data["nebbia"].mean(), 
                        "Probabilità nebbia", 
                        "%"
                    )
                    st.plotly_chart(fig_fog, use_container_width=True)
                
                with col4:
                    # Wind probability
                    wind_prob = historical_data["vento"].mean()
                    fig_wind = create_speedometer(
                        wind_prob, 
                        historical_data["vento"].mean(), 
                        "Probabilità vento", 
                        "%"
                    )
                    st.plotly_chart(fig_wind, use_container_width=True)
        
        except Exception as e:
            st.warning(f"Impossibile caricare i dati meteo storici: {e}")
    
    # Avalanche risk
    if livello != "nessuno":
        st.markdown('<h3 class="modern-section-title">⚠️ Rischio valanghe</h3>', unsafe_allow_html=True)
        
        try:
            # Get historical avalanche data
            historical_avalanche = get_historical_data_for_date(df_valanghe, data_sel)
            
            if not historical_avalanche.empty:
                risk = historical_avalanche["danger_level_avg"].mean()
                baseline = df_valanghe["danger_level_avg"].mean()
                
                # Create speedometer for avalanche risk
                fig_risk = create_speedometer(
                    risk, 
                    baseline, 
                    "Rischio valanghe (1-5)", 
                    ""
                )
                
                fig_risk.update_layout(height=230, margin=dict(l=10, r=10, t=20, b=40))
                st.plotly_chart(fig_risk, use_container_width=True)
                
                st.markdown("L’indice di valanghe, conosciuto come Scala Europea del Pericolo di Valanghe, è uno strumento a 5 livelli utilizzato per valutare e comunicare il rischio di valanghe (0=basso, 5=molto alto)")
        
        except Exception as e:
            st.warning(f"Impossibile caricare i dati valanghe: {e}")
    
    # Profile-specific AI Overview
    if profilo != "nessuno":
        st.markdown('<h3 class="modern-section-title">🤖 AI Overview - Profilo specifico</h3>', unsafe_allow_html=True)
        
        # AI Overview per profili specifici (TEMPORANEAMENTE DISABILITATO)
        # try:
        #     if profilo == "festaiolo":
        #         prompt_profile = build_festaiolo_prompt(df_recensioni, best_name, livello, data_sel)
        #         output_profile, usage_profile = generate_overview(prompt_profile, max_tokens=140)
        #         
        #         if output_profile:
        #             st.markdown(
        #             f"""
        #             <div class="ai-overview-section">
        #             <div class="ai-overview-content">{output_profile}</div>
        #             </div>
        #             """,
        #             unsafe_allow_html=True
        #             )
        #             
        #             if isinstance(usage_profile, dict) and usage_profile.get("model"):
        #             st.caption(f"Modello: {usage_profile['model']}")
        #     
        #     elif profilo == "familiare":
        #         # Show specific data for recommended station
        #         if "Area_bambini" in df_kpis.columns:
        #             best_station_data = df_kpis[df_kpis["nome_stazione"] == best_name]
        #             if not best_station_data.empty:
        #             area_bambini = best_station_data["Area_bambini"].iloc[0]
        #             if pd.notna(area_bambini) and area_bambini > 0:
        #             st.info(f"🎯 **{best_name}** ha **{int(area_bambini)} aree bambini** aperte per i tuoi piccoli!")
        #         
        #         prompt_profile = build_familiare_prompt(df_recensioni, best_name, livello, data_sel)
        #         output_profile, usage_profile = generate_overview(prompt_profile, max_tokens=140)
        #         
        #         if output_profile:
        #             st.markdown(
        #             f"""
        #             <div class="ai-overview-content">{output_profile}</div>
        #             </div>
        #             """,
        #             unsafe_allow_html=True
        #             )
        #             
        #             if isinstance(usage_profile, dict) and usage_profile.get("model"):
        #             st.caption(f"Modello: {usage_profile['model']}")
        #     
        #     elif profilo == "lowcost":
        #         prompt_profile = build_lowcost_prompt(df_recensioni, best_name, livello, data_sel)
        #         output_profile, usage_profile = generate_overview(prompt_profile, max_tokens=140)
        #         
        #         if output_profile:
        #             st.markdown(
        #             f"""
        #             <div class="ai-overview-section">
        #             <div class="ai-overview-content">{output_profile}</div>
        #             </div>
        #             """,
        #             unsafe_allow_html=True
        #             )
        #             
        #         if isinstance(usage_profile, dict) and usage_profile.get("model"):
        #             st.caption(f"Modello: {usage_profile['model']}")
        # 
        # except Exception as e:
        #     st.warning(f"Impossibile generare l'AI Overview per il profilo: {e}")
        
        # Testo temporaneo al posto dell'LLM per profili specifici
        if profilo == "familiare":
            # Show specific data for recommended station
            if "Area_bambini" in df_kpis.columns:
                best_station_data = df_kpis[df_kpis["nome_stazione"] == best_name]
                if not best_station_data.empty:
                    area_bambini = best_station_data["Area_bambini"].iloc[0]
                    if pd.notna(area_bambini) and area_bambini > 0:
                        st.info(f"🎯 **{best_name}** ha **{int(area_bambini)} aree bambini** aperte per i tuoi piccoli!")
        

        
        # Profile-specific information
        if profilo == "festaiolo":
            st.markdown('<h4 class="modern-section-title">🎉 Profilo Festaiolo</h4>', unsafe_allow_html=True)
            st.info("**Focus**: Snowpark, sci notturno, ristoranti e vita notturna. Perfetto per chi vuole divertirsi oltre allo sci!")
            
        elif profilo == "familiare":
            st.markdown('<h4 class="modern-section-title">👨‍👩‍👧‍👦 Profilo Familiare</h4>', unsafe_allow_html=True)
            st.info("**Focus**: Aree bambini, piste sicure, ristoranti family-friendly e servizi per famiglie.")
            
        elif profilo == "lowcost":
            st.markdown('<h4 class="modern-section-title">💰 Profilo Low-Cost</h4>', unsafe_allow_html=True)
            st.info("**Focus**: Prezzi contenuti, skipass economici, opzioni di alloggio convenienti.")
            
        elif profilo == "panoramico":
            st.markdown('<h4 class="modern-section-title">🏔️ Profilo Panoramico</h4>', unsafe_allow_html=True)
            st.info("**Focus**: Viste mozzafiato, piste panoramiche, fotografie e relax.")
        
        # Testo Lorem ipsum per tutti i profili
        output_profile = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum"
        
        st.markdown(
            f"""
            <div class="ai-overview-section">
                <div class="ai-overview-content">{output_profile}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    


if __name__ == "__main__":
    main()