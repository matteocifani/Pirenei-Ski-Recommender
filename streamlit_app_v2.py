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
from app.llm import generate_overview
from app.config import SUPPORTED_PROFILES

# Modern UI Styling with Glow Effects
st.set_page_config(
    page_title="🏔️ Ski Resort Recommender",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI with glow effects
st.markdown("""
<style>
/* Modern Design System with Glow Effects */
:root {
    --primary-glow: 0 0 20px rgba(59, 130, 246, 0.3);
    --secondary-glow: 0 0 30px rgba(147, 51, 234, 0.2);
    --success-glow: 0 0 20px rgba(34, 197, 94, 0.3);
    --warning-glow: 0 0 20px rgba(245, 158, 11, 0.3);
    --danger-glow: 0 0 20px rgba(239, 68, 68, 0.3);
    --card-bg: rgba(255, 255, 255, 0.95);
    --card-border: rgba(59, 130, 246, 0.1);
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --accent-blue: #3b82f6;
    --accent-purple: #8b5cf6;
    --accent-green: #10b981;
    --accent-orange: #f59e0b;
}

/* Global Styles */
.main {
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

/* Modern Cards with Glow Effects */
.glow-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 
        0 4px 6px -1px rgba(0, 0, 0, 0.1),
        0 2px 4px -1px rgba(0, 0, 0, 0.06),
        var(--primary-glow);
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.glow-card:hover {
    transform: translateY(-2px);
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05),
        var(--primary-glow);
}

/* Success Card */
.glow-card.success {
    border-color: rgba(34, 197, 94, 0.2);
    box-shadow: var(--success-glow);
}

.glow-card.success:hover {
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05),
        var(--success-glow);
}

/* Warning Card */
.glow-card.warning {
    border-color: rgba(245, 158, 11, 0.2);
    box-shadow: var(--warning-glow);
}

.glow-card.warning:hover {
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05),
        var(--warning-glow);
}

/* Info Card */
.glow-card.info {
    border-color: rgba(59, 130, 246, 0.2);
    box-shadow: var(--primary-glow);
}

.glow-card.info:hover {
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.1),
        0 4px 6px -2px rgba(0, 0, 0, 0.05),
        var(--primary-glow);
}

/* Modern Headers */
.modern-header {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
    font-size: 2.5rem;
    text-align: center;
    margin: 2rem 0;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.modern-subheader {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 600;
    font-size: 1.5rem;
    margin: 1.5rem 0 1rem 0;
}

/* Glow Buttons */
.glow-button {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: var(--primary-glow);
}

.glow-button:hover {
    transform: translateY(-2px);
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.2),
        var(--primary-glow);
}

/* Modern Metrics */
.metric-card {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: var(--primary-glow);
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 
        0 8px 20px -3px rgba(0, 0, 0, 0.15),
        var(--primary-glow);
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--accent-blue);
    margin: 8px 0;
}

.metric-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 500;
}

/* Modern Podium */
.podium {
    display: flex;
    justify-content: center;
    align-items: end;
    gap: 20px;
    margin: 2rem 0;
}

.podium .col {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.podium .step {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 10px;
    box-shadow: var(--primary-glow);
    transition: all 0.3s ease;
}

.podium .step:hover {
    transform: translateY(-5px);
    box-shadow: 
        0 15px 35px -5px rgba(0, 0, 0, 0.2),
        var(--primary-glow);
}

.podium .s1 {
    height: 120px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    box-shadow: var(--warning-glow);
}

.podium .s2 {
    height: 100px;
    background: linear-gradient(135deg, #9ca3af, #6b7280);
}

.podium .s3 {
    height: 80px;
    background: linear-gradient(135deg, #d97706, #b45309);
}

.podium .medal {
    font-size: 2rem;
    margin-bottom: 10px;
}

.podium .name {
    color: white;
    font-weight: 600;
    font-size: 1.1rem;
    text-align: center;
}

/* Modern Tables */
.modern-table {
    background: var(--card-bg);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--primary-glow);
    border: 1px solid var(--card-border);
}

.modern-table th {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    color: white;
    font-weight: 600;
    padding: 16px;
    text-align: left;
}

.modern-table td {
    padding: 16px;
    border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.modern-table tr:hover {
    background: rgba(59, 130, 246, 0.05);
}

/* Modern Sidebar */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
    border-right: 1px solid var(--card-border);
}

/* Responsive Design */
@media (max-width: 768px) {
    .podium {
        flex-direction: column;
        align-items: center;
    }
    
    .podium .step {
        width: 200px;
    }
    
    .modern-header {
        font-size: 2rem;
    }
}

/* Custom Streamlit Elements */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    box-shadow: var(--primary-glow);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 
        0 10px 25px -3px rgba(0, 0, 0, 0.2),
        var(--primary-glow);
}

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
    box-shadow: var(--primary-glow);
}

/* Success Messages */
.stSuccess {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.1));
    border: 1px solid rgba(34, 197, 94, 0.2);
    border-radius: 12px;
    box-shadow: var(--success-glow);
}

/* Info Messages */
.stInfo {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1));
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 12px;
    box-shadow: var(--primary-glow);
}

/* Warning Messages */
.stWarning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1));
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-radius: 12px;
    box-shadow: var(--warning-glow);
}

/* Error Messages */
.stError {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 12px;
    box-shadow: var(--danger-glow);
}
</style>
""", unsafe_allow_html=True)


def aggregate_station_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
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
        "danger_level_avg": ("danger_level_avg", "mean"),
        "vento": ("vento", "mean"),
        "nebbia": ("nebbia", "mean"),
        "espesor_medio": ("espesor_medio", "mean"),
    }
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
            "danger_level_avg": "avalanche",
            "espesor_medio": "neve_cm",
        }
    )
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
                        tags.append("ideal for beginners")
    if profilo in ("panoramico", "familiare", "festaiolo", "lowcost"):
                        tags.append(f"suitable for {profilo} profile")
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
    prompt = (
        f"Per la data {target_date} l'app ha selezionato la stazione migliore: {best_name}. "
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
    return (
        f"Per la data {target_date} e livello '{livello}', fai un mini-riassunto (max 2 frasi) sul tema 'festa' "
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
    return (
        f"Per la data {target_date} e livello '{livello}', scrivi un mini-riassunto (max 2 frasi) focalizzato su famiglie. "
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
    return (
        f"Per la data {target_date} e livello '{livello}', scrivi un mini-riassunto (max 2 frasi) focalizzato su rapporto qualità-prezzo. "
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


@st.cache_data(ttl=3600, show_spinner=False)
def _llm_overview_cached(prompt: str, max_tokens: int) -> tuple[str, dict]:
    return generate_overview(prompt, max_tokens)


def render_map_with_best(df_coords: pd.DataFrame, best_name: str, tooltip_km: bool = False):
    # Prepara DF con coordinate di tutte le stazioni
    base_coords = df_coords.copy()
    def _norm(s: str) -> str:
        try:
            return re.sub(r"\s+", " ", str(s).strip().lower())
        except Exception:
            return str(s)
    has_latlon = any(c.lower() in ("lat","latitude","latitudine") for c in base_coords.columns) and \
                 any(c.lower() in ("lon","lng","long","longitude","longitudine") for c in base_coords.columns)
    if not has_latlon:
        # prova a recuperare da df_meteo
        try:
            _, _, df_meteo_all, _ = load_datasets()
            if df_meteo_all is not None and not df_meteo_all.empty:
                meteo_all = ensure_lat_lon(df_meteo_all.copy())
                meteo_coords = meteo_all[["nome_stazione", "lat", "lon"]].drop_duplicates()
                base_coords = base_coords.merge(meteo_coords, on="nome_stazione", how="left")
        except Exception:
            pass
    base_coords = ensure_lat_lon(
        base_coords[["nome_stazione"] + [
            c for c in base_coords.columns
            if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")
        ]].drop_duplicates()
    )
    map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
    if map_data.empty:
        st.info("Coordinates not available for the map.")
        return
    map_data["_norm_name"] = map_data["nome_stazione"].apply(_norm)
    best_norm = _norm(best_name)
    # Trova coords esatte per la consigliata direttamente dal meteo come fallback forte
    best_pt = pd.DataFrame()
    try:
        _, _, df_meteo_all, _ = load_datasets()
        if df_meteo_all is not None and not df_meteo_all.empty:
            meteo_all = ensure_lat_lon(df_meteo_all.copy())
            meteo_all["_norm_name"] = meteo_all["nome_stazione"].apply(_norm)
            match_exact = meteo_all[meteo_all["_norm_name"] == best_norm]
            if not match_exact.empty:
                best_pt = match_exact[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
            else:
                token = best_norm.split(" ")[0] if best_norm else ""
                if token:
                    match_partial = meteo_all[meteo_all["_norm_name"].str.contains(re.escape(token), na=False)]
                    if not match_partial.empty:
                        best_pt = match_partial[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
    except Exception:
        pass
    if best_pt.empty:
        # fallback su mappa aggregata
        cand = map_data[map_data["_norm_name"] == best_norm]
        if cand.empty and best_norm:
            token = best_norm.split(" ")[0]
            cand = map_data[map_data["_norm_name"].str.contains(re.escape(token), na=False)]
        if not cand.empty:
            best_pt = cand[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
    # layer base e layer corona
    center_lat = map_data["lat"].mean()
    center_lon = map_data["lon"].mean()
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)
    layer_all = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[lon, lat]',
        get_radius=8000,
        get_fill_color='[255, 0, 0, 160]',
        pickable=True,
        auto_highlight=True,
    )
    layers = [layer_all]
    if not best_pt.empty:
        # Pallino verde per l'impianto consigliato
        best_layer = pdk.Layer(
            "ScatterplotLayer",
            data=best_pt,
            get_position='[lon, lat]',
            get_radius=12000,
            get_fill_color='[0, 200, 0, 220]',
            pickable=False,
        )
        layers.append(best_layer)
    deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{nome_stazione}"})
    st.pydeck_chart(deck, use_container_width=True)


def main():
    # Modern Hero Section
    st.markdown('<h1 class="modern-header">🏔️ Ski Resort Recommender</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 2rem;">Discover the perfect ski resort for your next adventure</p>', unsafe_allow_html=True)
    
    with st.spinner("Loading data..."):
        df_infonieve, df_valanghe, df_meteo, df_recensioni = load_datasets()

    if df_infonieve is None:
        st.error("Unable to load data. Please check the CSV files.")
        return

    # Modern Sidebar
    with st.sidebar:
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin: 0 0 1rem 0; color: var(--accent-blue);">⚙️ Configuration</h3>', unsafe_allow_html=True)
        
        min_date = df_infonieve["date"].min().date()
        default_date = datetime.date(2025, 12, 17)
        data_sel = st.date_input("📅 Date", value=default_date, min_value=min_date, max_value=datetime.date(2030, 12, 31))
        livello = st.selectbox("🎯 Skill Level", ["nessuno", "base", "medio", "esperto"], index=3)
        profilo = st.selectbox("👤 Profile (optional)", SUPPORTED_PROFILES, index=0)
        profilo_norm = str(profilo).strip().lower()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Considera sempre tutte le stazioni
    df_filtered_infonieve = df_infonieve.copy()
    df_filtered_val = df_valanghe.copy()
    df_filtered_meteo = df_meteo.copy()
    df_filtered_rec = df_recensioni.copy()

    df_with_indices = compute_indices(
        df_filtered_infonieve, df_filtered_val, df_filtered_meteo, df_filtered_rec, data_sel
    )

    if df_with_indices.empty:
        st.markdown('<div class="glow-card warning">', unsafe_allow_html=True)
        st.warning("🚫 No stations are open on this date. Try choosing another day for your snow adventure!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show average opening/closing dates for all stations
        try:
            base = df_infonieve.dropna(subset=["date"]).copy()
            base["date"] = pd.to_datetime(base["date"], errors="coerce")
            base = base.dropna(subset=["date"])
            base["year"] = base["date"].dt.year

            # Build status column (1 open, 0 closed)
            if "idestado" in base.columns:
                base["stato"] = base["idestado"].fillna(0).astype(int).clip(0, 1)
            elif "kmopen" in base.columns:
                base["stato"] = (base["kmopen"].fillna(0) > 0).astype(int)
            else:
                base["stato"] = 0

            rows = []
            for (staz, yr), g in base.groupby(["nome_stazione", "year"], as_index=False):
                gd = g.sort_values("date").reset_index(drop=True)
                s = gd["stato"].astype(int).tolist()
                dates = gd["date"].tolist()
                n = len(gd)
                open_date = None
                close_date = None
                for i in range(n):
                    prev5 = s[i-5:i] if i-5 >= 0 else []
                    next5 = s[i+1:i+6] if i+6 <= n else []
                    if len(prev5) == 5 and len(next5) == 5:
                        if sum(prev5) == 0 and sum(next5) == 5 and open_date is None:
                            open_date = dates[i]
                        if sum(prev5) == 5 and sum(next5) == 0 and close_date is None:
                            close_date = dates[i]
                    if open_date is not None and close_date is not None:
                        break
                if open_date is not None or close_date is not None:
                    rows.append({
                        "nome_stazione": staz,
                        "year": yr,
                        "apertura": open_date,
                        "chiusura": close_date,
                    })

            if rows:
                per_year = pd.DataFrame(rows)
                if "apertura" in per_year:
                    per_year["apertura_doy"] = pd.to_datetime(per_year["apertura"]).dt.dayofyear
                if "chiusura" in per_year:
                    per_year["chiusura_doy"] = pd.to_datetime(per_year["chiusura"]).dt.dayofyear
                avg = per_year.groupby("nome_stazione", as_index=False).agg(
                    apertura_doy=("apertura_doy", "mean"), chiusura_doy=("chiusura_doy", "mean")
                )

                def doy_to_label(doy: float) -> str:
                    try:
                        ts = pd.Timestamp(2000, 1, 1) + pd.to_timedelta(int(round(doy)) - 1, unit="D")
                        return ts.strftime("%d %b")
                    except Exception:
                        return "-"

                avg["Apertura media"] = avg["apertura_doy"].apply(doy_to_label)
                avg["Chiusura media"] = avg["chiusura_doy"].apply(doy_to_label)
                avg = avg.sort_values("apertura_doy", ascending=True)
                table = avg[["nome_stazione", "Apertura media", "Chiusura media"]].rename(
                    columns={"nome_stazione": "Station"}
                )
                
                st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
                st.markdown('<h3 class="modern-subheader">📅 Average Opening/Closing Dates</h3>', unsafe_allow_html=True)
                st.dataframe(table, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass
        return

    df_scored = apply_profile_adjustment(df_with_indices, livello, profilo)
    ranking = build_ranking(df_scored, "indice_finale")

    # Aggregated KPIs (mean over the window) for all stations
    df_kpis = aggregate_station_kpis(df_with_indices)

    # Best station name
    best_name = ranking.iloc[0]["nome_stazione"] if not ranking.empty else df_kpis.sort_values("km_open_est", ascending=False).iloc[0]["nome_stazione"]

    # Show recommendation only if at least one filter is selected
    if not (livello == "nessuno" and profilo == "nessuno"):
        st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
        st.markdown(f'<h2 class="modern-subheader">🏆 Recommended Station: {best_name}</h2>', unsafe_allow_html=True)
        
        k_row = (
            df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
            if not df_kpis.empty
            else None
        )
        if k_row is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">Estimated Open Slopes</div>
                        <div class="metric-value">{k_row.km_open_est:.0f} km</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                pct = k_row.pct_open * 100 if k_row.pct_open == k_row.pct_open else 0
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">Open Slopes %</div>
                        <div class="metric-value">{pct:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">Open Probability</div>
                        <div class="metric-value">{k_row.open_prob*100:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown('</div>', unsafe_allow_html=True)
    # end header cards

    # Map with highlight (only for levels different from "nessuno")
    if livello != "nessuno" and not df_kpis.empty:
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">🗺️ Interactive Resort Map</h3>', unsafe_allow_html=True)
        
        base_coords = ensure_lat_lon(df_filtered_infonieve[["nome_stazione"] + [c for c in df_filtered_infonieve.columns if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")]].drop_duplicates())
        map_data = df_kpis.merge(base_coords, on="nome_stazione", how="left").dropna(subset=["lat", "lon"])
        if not map_data.empty:
            center_lat = map_data["lat"].mean()
            center_lon = map_data["lon"].mean()
            view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)

            def color_for_avalanche(x: float) -> List[int]:
                if x <= 2:
                    return [80, 220, 160, 180]
                if x <= 3:
                    return [240, 200, 80, 200]
                return [240, 100, 100, 220]

            map_data["color"] = map_data["avalanche"].fillna(3).apply(color_for_avalanche)
            map_data["radius"] = np.clip((map_data["km_open_est"].fillna(0) + 5) * 500, 3000, 15000)
            map_data["highlight"] = np.where(map_data["nome_stazione"] == best_name, 1, 0)
            best_pt = map_data[map_data["highlight"] == 1].copy()
            if not best_pt.empty:
                best_pt["star"] = "★"

            layer_all = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position='[lon, lat]',
                get_radius="radius",
                get_fill_color="color",
                pickable=True,
                auto_highlight=True,
            )
            # Ring for recommended station (border only, no fill)
            ring_layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data[map_data["highlight"] == 1],
                get_position='[lon, lat]',
                get_radius="radius",
                stroked=True,
                filled=False,
                get_line_color='[0, 200, 255, 255]',
                line_width_min_pixels=2,
                pickable=False,
            )
            star_layer = pdk.Layer(
                "TextLayer",
                data=best_pt,
                get_position='[lon, lat]',
                get_text='star',
                get_size=28,
                get_color='[255,255,255,255]',
                get_angle=0,
                pickable=False,
            )
            deck = pdk.Deck(layers=[layer_all, ring_layer, star_layer], initial_view_state=view_state, tooltip={"text": "{nome_stazione}\nOpen slopes: {km_open_est} km"})
            st.pydeck_chart(deck, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # AI overview: disabled when level == "nessuno"
    if livello != "nessuno":
        st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">✨ AI Overview</h3>', unsafe_allow_html=True)
        
        api_key_present = True
        try:
            if not api_key_present:
                st.info("Configure OPENROUTER_API_KEY to enable AI overview.")
            else:
                prompt = build_llm_prompt(df_kpis, best_name, livello, profilo, data_sel)
                with st.spinner("Generating AI summary..."):
                    output, usage = generate_overview(prompt, max_tokens=160)
                model_used = usage.get("model") if isinstance(usage, dict) else None
                if isinstance(usage, dict) and usage.get("error"):
                    st.error(f"Model error: {usage['error']}")
                    if model_used:
                        st.caption(f"Model: {model_used}")
                elif output:
                    st.write(output)
                    if model_used:
                        st.caption(f"Model: {model_used}")
                else:
                    st.error("No response from model.")
        except Exception as e:
            st.error(f"LLM not available: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    # Level-specific visualizations
    if livello == "base":
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">🎿 For Beginners: Where to Find Easy Slopes and Stable Conditions</h3>', unsafe_allow_html=True)
        st.markdown('<h4 class="modern-subheader">🗺️ Station Map (Recommended Highlighted)</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)
        st.markdown('</div>', unsafe_allow_html=True)

        # Top 3 Podium (aesthetic, without exposing index value)
        if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
            top3 = (df_with_indices.groupby("nome_stazione")["indice_base"].mean()
                    .sort_values(ascending=False).head(3).reset_index())
            if len(top3) > 0:
                names = top3["nome_stazione"].tolist()
                first = names[0] if len(names) > 0 else ""
                second = names[1] if len(names) > 1 else ""
                third = names[2] if len(names) > 2 else ""
                st.markdown('<h4 class="modern-subheader">🏆 Top 3 Stations</h4>', unsafe_allow_html=True)
                st.markdown("""
                <div class='podium'>
                  <div class='col'>
                    <div class='step s2'>
                      <div class='medal'>🥈</div>
                      <div class='name'>%s</div>
                    </div>
                  </div>
                  <div class='col'>
                    <div class='step s1'>
                      <div class='medal'>🥇</div>
                      <div class='name'>%s</div>
                    </div>
                  </div>
                  <div class='col'>
                    <div class='step s3'>
                      <div class='medal'>🥉</div>
                      <div class='name'>%s</div>
                    </div>
                  </div>
                </div>
                """ % (second, first, third), unsafe_allow_html=True)

        # Probabilità meteo (±3 giorni su anni precedenti per date future)
        from datetime import date as _date
        def create_speedometer(value_pct: float, title: str, color: str, reference_pct: float | None = None) -> go.Figure:
            indicator = go.Indicator(
                mode="gauge+number",
                value=max(0, min(100, value_pct)),
                title={"text": title, "font": {"size": 30}},
                number={"suffix": "%", "font": {"size": 36, "color": "#e6efff"}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 33], "color": "#1f2937"},
                        {"range": [33, 66], "color": "#374151"},
                        {"range": [66, 100], "color": "#4b5563"},
                    ],
                },
            )
            fig = go.Figure(indicator)
            # delta al centro basso
            if reference_pct is not None:
                delta_val = max(0, min(100, value_pct)) - max(0, min(100, reference_pct))
                fig.add_annotation(
                    x=0.5, y=0.10, xref="paper", yref="paper",
                    text=f"{delta_val:+.2f}%", showarrow=False,
                    font=dict(size=16, color="#16a34a" if delta_val < 0 else "#ef4444")
                )
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=20))
            return fig

        # Current/forecast weather data (±3 days) always from historical for consistency
        meteo_data = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=3)
        if not meteo_data.empty:
            st.markdown('<h4 class="modern-subheader">🌤️ Weather Conditions Probability (Historical ±3 days)</h4>', unsafe_allow_html=True)
            # baseline ±15 days on previous years
            baseline = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=15)
            col1, col2 = st.columns(2)
            with col1:
                prob_nebbia = float(meteo_data.get("nebbia", 0).mean() * 100)
                baseline_nebbia = float((baseline.get("nebbia", 0).mean() * 100) if not baseline.empty else 0)
                fig_n = create_speedometer(prob_nebbia, "Fog Prob.", "#94a3b8", reference_pct=baseline_nebbia)
                st.plotly_chart(fig_n, use_container_width=True)
            with col2:
                prob_pioggia = float(meteo_data.get("pioggia", 0).mean() * 100)
                baseline_pioggia = float((baseline.get("pioggia", 0).mean() * 100) if not baseline.empty else 0)
                fig_p = create_speedometer(prob_pioggia, "Rain Prob.", "#60a5fa", reference_pct=baseline_pioggia)
                st.plotly_chart(fig_p, use_container_width=True)
            st.caption("Note: probabilities calculated on historical data for similar periods; delta compares with average of previous years in ±15 days window.")
        else:
            st.warning("Weather data not available for this date")

        # Stacked bars for green/blue slopes ordered by base index
        if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
            st.markdown('<h4 class="modern-subheader">🎿 Green and Blue Slopes Distribution</h4>', unsafe_allow_html=True)
            piste_base = df_with_indices[["nome_stazione", "Piste_verdi", "Piste_blu", "indice_base"]].drop_duplicates()
            piste_base = piste_base.sort_values("indice_base", ascending=False)
            fig_piste_base = px.bar(
                piste_base,
                x="nome_stazione",
                y=["Piste_verdi", "Piste_blu"],
                title="Green and Blue Slopes per Station (ordered by base index)",
                color_discrete_map={"Piste_verdi": "#4CAF50", "Piste_blu": "#2196F3"}
            )
            fig_piste_base.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_piste_base, use_container_width=True)

        # Festaiolo Profile Section (only if selected)
        if profilo_norm == "festaiolo":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🎉 Profile: Party Goer</h4>', unsafe_allow_html=True)
            
            # Chart 1: night skiing km (X axis), resorts on Y
            try:
                st.markdown('<h5 class="modern-subheader">🌙 Night Skiing</h5>', unsafe_allow_html=True)
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Night Skiing Kilometers by Resort",
                        labels={"Scii_notte": "Night Skiing Km", "nome_stazione": "Resort"}
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

        if profilo_norm == "familiare":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">👨‍👩‍👧‍👦 Profile: Family</h4>', unsafe_allow_html=True)
            
            # 1) Number of children areas per resort
            try:
                st.markdown('<h5 class="modern-subheader">🧒 Children Areas</h5>', unsafe_allow_html=True)
                if "Area_bambini" in df_with_indices.columns:
                    df_kids = (
                        df_with_indices[["nome_stazione", "Area_bambini"]]
                        .drop_duplicates().fillna(0)
                        .sort_values("Area_bambini", ascending=False)
                    )
                    fig_kids = px.bar(
                        df_kids,
                        x="nome_stazione", y="Area_bambini",
                        title="Number of Children Areas per Resort",
                        labels={"nome_stazione": "Resort", "Area_bambini": "Children Areas"}
                    )
                    fig_kids.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_kids, use_container_width=True)
                else:
                    st.info("Data not available: 'Area_bambini'")
            except Exception:
                pass

            # 2) Average prices per resort (skipass, school, rental)
            try:
                st.markdown('<h5 class="modern-subheader">💰 Average Prices</h5>', unsafe_allow_html=True)
                price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                if price_cols:
                    df_price = (
                        df_with_indices[["nome_stazione"] + price_cols]
                        .drop_duplicates().fillna(0)
                    )
                    melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Item", value_name="Price")
                    fig_prices = px.bar(
                        melted_p,
                        x="Price", y="nome_stazione", color="Item",
                        barmode="group",
                        title="Average Prices per Resort (Skipass, School, Rental)",
                        labels={"nome_stazione": "Resort", "Price": "€"}
                    )
                    st.plotly_chart(fig_prices, use_container_width=True)
                else:
                    st.info("Price data not available (skipass/school/rental)")
            except Exception:
                pass

            # 3) AI Overview – Family
            try:
                st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Family</h5>', unsafe_allow_html=True)
                
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "No content available now.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Model: {usage['model']}")
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)
            # RIMOSSI: Snowpark/Superpipe e AI Overview – Festa (solo per profilo festaiolo)

    elif livello == "medio":
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">🎯 For Intermediates: Balance Between Slopes and Safety</h3>', unsafe_allow_html=True)
        st.markdown('<h4 class="modern-subheader">🗺️ Station Map (Recommended Highlighted)</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)
        st.markdown('</div>', unsafe_allow_html=True)

        # Top 3 Podium for intermediate index
        if "indice_medio" in df_with_indices.columns and not df_with_indices.empty:
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🏆 Top 3 Intermediate Stations</h4>', unsafe_allow_html=True)
            top3m = (
                df_with_indices.groupby("nome_stazione")["indice_medio"].mean()
                .sort_values(ascending=False).head(3).reset_index()
            )
            if not top3m.empty:
                names = top3m["nome_stazione"].tolist()
                first = names[0] if len(names) > 0 else ""
                second = names[1] if len(names) > 1 else ""
                third = names[2] if len(names) > 2 else ""
                st.markdown(
                    f"""
                    <div class='podium'>
                      <div class='col'>
                        <div class='step s2'>
                          <div class='medal'>🥈</div>
                          <div class='name'>{second}</div>
                        </div>
                      </div>
                      <div class='col'>
                        <div class='step s1'>
                          <div class='medal'>🥇</div>
                          <div class='name'>{first}</div>
                        </div>
                      </div>
                      <div class='col'>
                        <div class='step s3'>
                          <div class='medal'>🥉</div>
                          <div class='name'>{third}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Compact weather (5 mini-donuts) for recommended station
        try:
            st.markdown('<div class="glow-card warning">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🌤️ Weather Conditions (Historical ±3 days)</h4>', unsafe_allow_html=True)
            
            meteo_win = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=3)
            if not meteo_win.empty:
                m_best = meteo_win[meteo_win.get("nome_stazione", "").astype(str) == best_name]
                if m_best.empty:
                    m_best = meteo_win
                pioggia = float(m_best.get("pioggia", 0).mean() * 100)
                nebbia = float(m_best.get("nebbia", 0).mean() * 100)
                sole    = float(m_best.get("sole", 0).mean() * 100)
                vento   = float(m_best.get("vento", 0).mean() * 100)
                neve_pct = 0.0
                snow_win = get_historical_data_for_date(df_filtered_infonieve, data_sel, days_range=3)
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

                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    st.plotly_chart(donut(pioggia, "Rain", "#60A5FA"), use_container_width=True)
                with r1c2:
                    st.plotly_chart(donut(sole, "Sun", "#F59E0B"), use_container_width=True)
                with r1c3:
                    st.plotly_chart(donut(nebbia, "Fog", "#94a3b8"), use_container_width=True)
                st.write("")
                r2c1, r2c2, r2c3 = st.columns([1,1,1])
                with r2c1:
                    st.plotly_chart(donut(vento, "Wind", "#00C8FF"), use_container_width=True)
                with r2c2:
                    st.plotly_chart(donut(neve_pct, "Snow", "#6EE7B7"), use_container_width=True)
                with r2c3:
                    st.write("")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass

        # Resort map (with recommended resort highlighted)
        try:
            if not df_with_indices.empty:
                base_coords = ensure_lat_lon(
                    df_filtered_infonieve[["nome_stazione"] + [
                        c for c in df_filtered_infonieve.columns
                        if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")
                    ]].drop_duplicates()
                )
                map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
                if not map_data.empty:
                    map_data["highlight"] = (map_data["nome_stazione"] == best_name).astype(int)
                    center_lat = map_data["lat"].mean()
                    center_lon = map_data["lon"].mean()
                    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)

                    layer_all = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_data,
                        get_position='[lon, lat]',
                        get_radius=8000,
                        get_fill_color='[255, 0, 0, 140]'
                    )
                    layer_best = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_data[map_data["highlight"] == 1],
                        get_position='[lon, lat]',
                        get_radius=12000,
                        get_fill_color='[0, 200, 255, 200]'
                    )
                    deck = pdk.Deck(
                        layers=[layer_all, layer_best],
                        initial_view_state=view_state,
                        tooltip={"text": "{nome_stazione}"}
                    )
                    st.pydeck_chart(deck, use_container_width=True)
        except Exception:
            pass

        # Blue/red slopes ordered by intermediate index
        if not df_with_indices.empty and "indice_medio" in df_with_indices.columns:
            st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
            st.markdown('<h5 class="modern-subheader">🛷 Blue and Red Slopes by Station</h5>', unsafe_allow_html=True)
            piste = df_with_indices[["nome_stazione", "Piste_blu", "Piste_rosse", "indice_medio"]].drop_duplicates()
            piste = piste.sort_values("indice_medio", ascending=False)
            melted = piste.melt("nome_stazione", value_vars=["Piste_blu", "Piste_rosse"], var_name="Type", value_name="Number")
            fig = px.bar(
                melted,
                x="nome_stazione", y="Number", color="Type", barmode="stack",
                color_discrete_map={"Piste_blu": "#60A5FA", "Piste_rosse": "#FB7185"},
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Festaiolo Profile Section
        if profilo_norm == "festaiolo":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🎉 Profile: Party Goer</h4>', unsafe_allow_html=True)
            try:
                st.markdown('<h5 class="modern-subheader">🌙 Night Skiing</h5>', unsafe_allow_html=True)
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Night Skiing Kilometers by Resort",
                        labels={"Scii_notte": "Night Skiing Km", "nome_stazione": "Resort"}
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass
            try:
                st.markdown('<h5 class="modern-subheader">🏂 Snowpark & Superpipe</h5>', unsafe_allow_html=True)
                cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                if not df_acts.empty:
                    melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Activity", value_name="Value")
                    fig_acts = px.bar(
                        melted, x="nome_stazione", y="Value", color="Activity",
                        barmode="group", title="Snowpark and Superpipe"
                    )
                    st.plotly_chart(fig_acts, use_container_width=True)
            except Exception:
                pass
            try:
                st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Party</h5>', unsafe_allow_html=True)
                prompt_f = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_f, max_tokens=140)
                st.write(out or "No content available now.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Model: {usage['model']}")
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

        # Familiare Profile Section
        if profilo_norm == "familiare":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">👨‍👩‍👧‍👦 Profile: Family</h4>', unsafe_allow_html=True)
            
            # 1) Number of children areas per resort
            try:
                st.markdown('<h5 class="modern-subheader">🧒 Children Areas</h5>', unsafe_allow_html=True)
                if "Area_bambini" in df_with_indices.columns:
                    df_kids = (
                        df_with_indices[["nome_stazione", "Area_bambini"]]
                        .drop_duplicates().fillna(0)
                        .sort_values("Area_bambini", ascending=False)
                    )
                    fig_kids = px.bar(
                        df_kids,
                        x="nome_stazione", y="Area_bambini",
                        title="Number of Children Areas per Resort",
                        labels={"nome_stazione": "Resort", "Area_bambini": "Children Areas"}
                    )
                    fig_kids.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_kids, use_container_width=True)
                else:
                    st.info("Data not available: 'Area_bambini'")
            except Exception:
                pass

            # 2) Average prices per resort (skipass, school, rental)
            try:
                st.markdown('<h5 class="modern-subheader">💰 Average Prices</h5>', unsafe_allow_html=True)
                price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                if price_cols:
                    df_price = (
                        df_with_indices[["nome_stazione"] + price_cols]
                        .drop_duplicates().fillna(0)
                    )
                    melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Item", value_name="Price")
                    fig_prices = px.bar(
                        melted_p,
                        x="Price", y="nome_stazione", color="Item",
                        barmode="group",
                        title="Average Prices per Resort (Skipass, School, Rental)",
                        labels={"nome_stazione": "Resort", "Price": "€"}
                    )
                    st.plotly_chart(fig_prices, use_container_width=True)
                else:
                    st.info("Price data not available (skipass/school/rental)")
            except Exception:
                pass

            # 3) AI Overview – Family
            try:
                st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Family</h5>', unsafe_allow_html=True)
                
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "No content available now.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Model: {usage['model']}")
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

    elif livello == "esperto":
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">🏂 For Experts: Technical Features and Kilometers</h3>', unsafe_allow_html=True)
        st.markdown('<h4 class="modern-subheader">🗺️ Station Map (Recommended Highlighted)</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)
        st.markdown('</div>', unsafe_allow_html=True)

        # Top 3 Podium for expert index
        if not df_with_indices.empty and "indice_esperto" in df_with_indices.columns:
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🏆 Top 3 Expert Stations</h4>', unsafe_allow_html=True)
            top3e = (
                df_with_indices.groupby("nome_stazione")["indice_esperto"].mean()
                .sort_values(ascending=False).head(3).reset_index()
            )
            if not top3e.empty:
                names = top3e["nome_stazione"].tolist()
                first = names[0] if len(names) > 0 else ""
                second = names[1] if len(names) > 1 else ""
                third = names[2] if len(names) > 2 else ""
                st.markdown(
                    f"""
                    <div class='podium'>
                      <div class='col'>
                        <div class='step s2'>
                          <div class='medal'>🥈</div>
                          <div class='name'>{second}</div>
                        </div>
                      </div>
                      <div class='col'>
                        <div class='step s1'>
                          <div class='medal'>🥇</div>
                          <div class='name'>{first}</div>
                        </div>
                      </div>
                      <div class='col'>
                        <div class='step s3'>
                          <div class='medal'>🥉</div>
                          <div class='name'>{third}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Avalanche risk speedometer (1-5) for recommended station (with delta vs baseline ±15d)
        try:
            st.markdown('<div class="glow-card warning">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">⚠️ Avalanche Risk (1-5)</h4>', unsafe_allow_html=True)
            
            brow = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
            risk = float(brow.get("avalanche", 3.0))
            # baseline: average danger_level_avg in ±15 days window on previous years
            base_val = get_historical_data_for_date(df_filtered_val, data_sel, days_range=15)
            bstation = base_val[base_val.get("nome_stazione", "").astype(str) == best_name]
            baseline = float(bstation.get("danger_level_avg", 0).mean()) if not bstation.empty else 0.0
            # Two levels: external subheader and delta at bottom, centered number
            d = risk - baseline
            
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Indicator(
                mode="gauge+number",
                value=risk,
                number={"font": {"size": 30, "color": "#e6efff"}},
                gauge={
                    "axis": {"range": [1, 5]},
                    "bar": {"color": "#ef4444"},
                    "steps": [
                        {"range": [1, 2], "color": "#16a34a"},
                        {"range": [2, 3], "color": "#f59e0b"},
                        {"range": [3, 5], "color": "#7f1d1d"},
                    ],
                },
                domain={"x": [0, 1], "y": [0.15, 1]}
            ))
            # Delta as annotation at very bottom
            fig_risk.add_annotation(x=0.5, y=0.05, xref="paper", yref="paper",
                                    text=f"Δ {d:+.2f} vs ±15d avg", showarrow=False,
                                    font=dict(size=12, color="#16a34a" if d < 0 else "#ef4444"))
            fig_risk.update_layout(height=230, margin=dict(l=10, r=10, t=20, b=40))
            st.plotly_chart(fig_risk, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass

        # Technical KPIs (recommended station)
        try:
            st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">⚡ Technical KPIs</h4>', unsafe_allow_html=True)
            
            top_best = df_with_indices[df_with_indices["nome_stazione"] == best_name]
            if not top_best.empty:
                vals = top_best[["Snowpark", "Area_gare", "Slalom", "Superpipe"]].fillna(0).mean()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"""<div class='metric-card'><div class='metric-value'>{vals.get('Snowpark',0):.0f}</div><div class='metric-label'>Snowpark</div></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class='metric-card'><div class='metric-value'>{vals.get('Area_gare',0):.0f}</div><div class='metric-label'>Race Area</div></div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class='metric-card'><div class='metric-value'>{vals.get('Slalom',0):.0f}</div><div class='metric-label'>Slalom</div></div>""", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"""<div class='metric-card'><div class='metric-value'>{vals.get('Superpipe',0):.0f}</div><div class='metric-label'>Superpipe</div></div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass

        # Max elevation: bar chart (Top 10) with 2000-3000m scale
        try:
            st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🏔️ Max Elevation by Station</h4>', unsafe_allow_html=True)
            
            quota = (
                df_with_indices.groupby("nome_stazione")["Quota_max"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
            )
            if not quota.empty:
                fig_quota = px.bar(quota, x="nome_stazione", y="Quota_max", title="Max Elevation by Station", labels={"nome_stazione": "Station", "Quota_max": "Max Elevation (m)"})
                fig_quota.update_layout(xaxis_tickangle=-45, yaxis=dict(range=[2000, 2800]))
                st.plotly_chart(fig_quota, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception:
            pass

        # Total kilometers: only totals for top 8 stations
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h4 class="modern-subheader">📏 Total Slopes Length</h4>', unsafe_allow_html=True)
        
        top_total = df_kpis.sort_values("km_total_est", ascending=False).head(8)
        fig_bar_total = px.bar(top_total, x="nome_stazione", y="km_total_est", title="Total Slopes Length by Station", labels={"nome_stazione": "Station", "km_total_est": "Total Kilometers"})
        fig_bar_total.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar_total, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if profilo_norm == "festaiolo":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🎉 Profile: Party Goer</h4>', unsafe_allow_html=True)
            
            try:
                st.markdown('<h5 class="modern-subheader">🌙 Night Skiing</h5>', unsafe_allow_html=True)
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Night Skiing Kilometers by Resort",
                        labels={"Scii_notte": "Night Skiing Km", "nome_stazione": "Resort"}
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass
            
            try:
                st.markdown('<h5 class="modern-subheader">🏂 Snowpark & Superpipe</h5>', unsafe_allow_html=True)
                cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                if not df_acts.empty:
                    melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Activity", value_name="Value")
                    fig_acts = px.bar(
                        melted, x="nome_stazione", y="Value", color="Activity",
                        barmode="group", title="Snowpark and Superpipe"
                    )
                    st.plotly_chart(fig_acts, use_container_width=True)
            except Exception:
                pass
            
            try:
                prompt_f = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Party</h5>', unsafe_allow_html=True)
                out, usage = generate_overview(prompt_f, max_tokens=140)
                st.write(out or "No content available now.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Model: {usage['model']}")
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

        # Family Profile Section
        if profilo_norm == "familiare":
            st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">👨‍👩‍👧‍👦 Profile: Family</h4>', unsafe_allow_html=True)
            
            # 1) Number of children areas per resort
            try:
                st.markdown('<h5 class="modern-subheader">🧒 Children Areas</h5>', unsafe_allow_html=True)
                if "Area_bambini" in df_with_indices.columns:
                    df_kids = (
                        df_with_indices[["nome_stazione", "Area_bambini"]]
                        .drop_duplicates().fillna(0)
                        .sort_values("Area_bambini", ascending=False)
                    )
                    fig_kids = px.bar(
                        df_kids,
                        x="nome_stazione", y="Area_bambini",
                        title="Number of Children Areas per Resort",
                        labels={"nome_stazione": "Resort", "Area_bambini": "Children Areas"}
                    )
                    fig_kids.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_kids, use_container_width=True)
                else:
                    st.info("Data not available: 'Area_bambini'")
            except Exception:
                pass

            # 2) Average prices per resort (skipass, school, rental)
            try:
                st.markdown('<h5 class="modern-subheader">💰 Average Prices</h5>', unsafe_allow_html=True)
                price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                if price_cols:
                    df_price = (
                        df_with_indices[["nome_stazione"] + price_cols]
                        .drop_duplicates().fillna(0)
                    )
                    melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Item", value_name="Price")
                    fig_prices = px.bar(
                        melted_p,
                        x="Price", y="nome_stazione", color="Item",
                        barmode="group",
                        title="Average Prices per Resort (Skipass, School, Rental)",
                        labels={"nome_stazione": "Resort", "Price": "€"}
                    )
                    st.plotly_chart(fig_prices, use_container_width=True)
                else:
                    st.info("Price data not available (skipass/school/rental)")
            except Exception:
                pass

            # 3) AI Overview – Family
            try:
                st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Family</h5>', unsafe_allow_html=True)
                
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "No content available now.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Model: {usage['model']}")
            except Exception:
                pass
            st.markdown('</div>', unsafe_allow_html=True)

    else:  # none (general overview)
        st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
        st.markdown('<h3 class="modern-subheader">📊 General Overview</h3>', unsafe_allow_html=True)
        
        # Bar chart: number of slopes by type per resort (stacked)
        piste_cols = ["Piste_verdi", "Piste_blu", "Piste_rosse", "Piste_nere"]
        if set(piste_cols).issubset(df_with_indices.columns):
            st.markdown('<h4 class="modern-subheader">🛷 Slopes by Type and Resort</h4>', unsafe_allow_html=True)
            piste_counts = (
                df_with_indices[["nome_stazione"] + piste_cols]
                .drop_duplicates()
                .fillna(0)
            )
            # Order by resorts with more open slopes (if kmopen available), otherwise by total slopes
            if "kmopen" in df_with_indices.columns:
                km_order = (
                    df_with_indices.groupby("nome_stazione")["kmopen"].mean().sort_values(ascending=False).index.tolist()
                )
                order = km_order
            else:
                piste_counts["tot_piste"] = (
                    piste_counts["Piste_verdi"]
                    + piste_counts["Piste_blu"]
                    + piste_counts["Piste_rosse"]
                    + piste_counts["Piste_nere"]
                )
                order = piste_counts.sort_values("tot_piste", ascending=False)["nome_stazione"].tolist()
            rename_map = {
                "Piste_verdi": "Green Slopes",
                "Piste_blu": "Blue Slopes",
                "Piste_rosse": "Red Slopes",
                "Piste_nere": "Black Slopes",
            }
            melted = piste_counts.rename(columns=rename_map).melt(
                "nome_stazione",
                value_vars=list(rename_map.values()),
                var_name="Type",
                value_name="Number",
            )
            color_map = {
                "Green Slopes": "#22c55e",
                "Blue Slopes": "#60a5fa",
                "Red Slopes": "#ef4444",
                "Black Slopes": "#111827",
            }
            fig_stack = px.bar(
                melted,
                x="nome_stazione",
                y="Number",
                color="Type",
                barmode="stack",
                title="Number of Slopes by Resort and Type",
                color_discrete_map=color_map,
                category_orders={"nome_stazione": order},
            )
            fig_stack.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_stack, use_container_width=True)

        # Resort map (centered on area) - simple version without highlight in "none"
        st.markdown('<h4 class="modern-subheader">🗺️ Ski Resort Map</h4>', unsafe_allow_html=True)
        if not df_with_indices.empty:
            map_data = df_with_indices[["nome_stazione", "lat", "lon"]].drop_duplicates().dropna()
            if map_data.empty:
                # fallback su merge se lat/lon non presenti direttamente
                base_coords = ensure_lat_lon(
                    df_filtered_infonieve[["nome_stazione"] + [c for c in df_filtered_infonieve.columns if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")]].drop_duplicates()
                )
                map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
            if not map_data.empty:
                center_lat = map_data["lat"].mean()
                center_lon = map_data["lon"].mean()
                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)
                layer_all = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_data,
                    get_position='[lon, lat]',
                    get_radius=8000,
                    get_fill_color='[255, 0, 0, 140]',
                    pickable=True,
                    auto_highlight=True,
                )
                deck = pdk.Deck(layers=[layer_all], initial_view_state=view_state, tooltip={"text": "{nome_stazione}"})
                st.pydeck_chart(deck, use_container_width=True)

        # Guide message for profiles without level
        if profilo_norm != "nessuno":
            if profilo_norm == "festaiolo":
                st.info("Select a level (Base/Medio/Esperto) to see the 'Festaiolo' dashboard.")
        else:
            st.info("Select a profile to get more detailed information")

        # Average snow depth trend for all resorts, with selectable focus
        st.markdown('<h4 class="modern-subheader">❄️ Snow Depth Trend (All Resorts)</h4>', unsafe_allow_html=True)
        try:
            anno = (pd.to_datetime(data_sel).year) - 1
            start = pd.Timestamp(anno, 11, 1)
            end = pd.Timestamp(anno + 1, 5, 1)
            history = df_filtered_infonieve[(df_filtered_infonieve["date"] >= start) & (df_filtered_infonieve["date"] < end)].dropna(subset=["espesor_medio"]).copy()
            if not history.empty:
                stations = sorted(history["nome_stazione"].unique().tolist())
                focus = st.selectbox("Highlight resort", options=["(None)"] + stations, index=0)
                solo = st.checkbox("Show only selected resort", value=False)
                palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set3 + px.colors.qualitative.T10
                color_cycle = {name: palette[i % len(palette)] for i, name in enumerate(stations)}
                fig_lines = go.Figure()
                for name, grp in history.groupby("nome_stazione"):
                    if solo and focus != "(None)" and name != focus:
                        continue
                    if focus != "(None)" and name != focus:
                        color = "rgba(160,160,160,0.25)"
                        width = 1
                        opacity = 1.0
                    else:
                        color = color_cycle[name]
                        width = 2.4 if focus == name else 1.8
                        opacity = 0.98
                    fig_lines.add_trace(
                        go.Scatter(
                            x=grp["date"],
                            y=grp["espesor_medio"],
                            mode="lines",
                            name=name,
                            line=dict(color=color, width=width),
                            opacity=opacity,
                        )
                    )
                fig_lines.update_layout(xaxis_title="Date", yaxis_title="Average Depth (cm)")
                st.plotly_chart(fig_lines, use_container_width=True)
        except Exception:
            pass
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Sezione finale: classifiche semplici per livello e profilo ---
    
    # Low-Cost Profile Section (only if selected, after all levels)
    if profilo_norm == "lowcost":
        st.markdown('<div class="glow-card success">', unsafe_allow_html=True)
        st.markdown('<h4 class="modern-subheader">💸 Profile: Low-Cost</h4>', unsafe_allow_html=True)
        
        # 1) Bar chart: ski pass, ski school and rental costs
        try:
            st.markdown('<h5 class="modern-subheader">💰 Costs by Resort</h5>', unsafe_allow_html=True)
            price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
            
            if price_cols:
                df_price_lowcost = (
                    df_with_indices[["nome_stazione"] + price_cols]
                    .drop_duplicates().fillna(0)
                )
                # Sort by total average price
                df_price_lowcost["prezzo_medio"] = df_price_lowcost[price_cols].mean(axis=1)
                df_price_lowcost = df_price_lowcost.sort_values("prezzo_medio", ascending=True)
                
                melted_prices = df_price_lowcost.melt("nome_stazione", value_vars=price_cols, var_name="Item", value_name="Price")
                fig_prices_lowcost = px.bar(
                    melted_prices,
                    x="nome_stazione", y="Price", color="Item",
                    barmode="group",
                    title="💰 Costs by Resort (Skipass, School, Rental) - Ascending by Average Price",
                    labels={"nome_stazione": "Resort", "Price": "€", "Item": "Cost Type"},
                    color_discrete_map={"Prezzo_skipass": "#FF6B6B", "Prezzo_scuola": "#4ECDC4", "Prezzo_noleggio": "#45B7D1"}
                )
                fig_prices_lowcost.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prices_lowcost, use_container_width=True)
            else:
                st.info("Price data not available for low-cost analysis")
        except Exception as e:
            st.warning(f"Error displaying prices: {e}")
        
        # 2) Quality-price ratio table
        try:
            st.markdown('<h5 class="modern-subheader">📊 Quality-Price Ratio: Euro per Kilometer</h5>', unsafe_allow_html=True)
            if not df_with_indices.empty and "kmopen" in df_with_indices.columns and "Prezzo_skipass" in df_with_indices.columns:
                # Group by station and calculate averages to have one row per station
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
                    # Impute kmopen for Saint-Lary using regression kmopen vs kmtotal
                    try:
                        from sklearn.linear_model import LinearRegression
                        
                        # Prepare training data (exclude Saint-Lary and consider only idestado=1)
                        df_train = df_with_indices[
                            (df_with_indices["nome_stazione"] != "Saint-Lary") & 
                            (df_with_indices["idestado"] == 1) &
                            (df_with_indices["kmopen"] > 0) &
                            (df_with_indices["kmtotal"] > 0)
                        ].copy()
                        
                        if len(df_train) >= 3:  # Need at least 3 points for regression
                            # Create features for regression: kmtotal vs kmopen
                            X_train = df_train[["kmtotal"]].values
                            y_train = df_train["kmopen"].values
                            
                            # Train linear regression model
                            model = LinearRegression()
                            model.fit(X_train, y_train)
                            
                            # Predict kmopen for Saint-Lary using its kmtotal
                            saint_lary_data = df_with_indices[
                                (df_with_indices["nome_stazione"] == "Saint-Lary") & 
                                (df_with_indices["idestado"] == 1)
                            ]
                            
                            if not saint_lary_data.empty and "kmtotal" in saint_lary_data.columns:
                                saint_lary_kmtotal = saint_lary_data["kmtotal"].mean()
                                
                                if saint_lary_kmtotal > 0:
                                    # Predict kmopen for Saint-Lary
                                    predicted_kmopen = model.predict([[saint_lary_kmtotal]])[0]
                                    
                                    # Update kmopen value for Saint-Lary in the table
                                    df_ratio.loc[df_ratio["nome_stazione"] == "Saint-Lary", "kmopen"] = max(0, predicted_kmopen)
                                else:
                                    st.warning("⚠️ Saint-Lary doesn't have kmtotal > 0 for imputation")
                            else:
                                st.warning("⚠️ Saint-Lary data not found for imputation")
                        else:
                            st.warning("⚠️ Insufficient data for imputation (need at least 3 stations with kmopen > 0 and kmtotal > 0)")
                    except Exception as e:
                        st.warning(f"⚠️ Error in imputation: {e}")
                    
                    # Calculate euro/km ratio (cost per kilometer of slope)
                    df_ratio["rapporto_euro_km"] = np.where(
                        df_ratio["kmopen"] > 0,
                        df_ratio["Prezzo_skipass"] / df_ratio["kmopen"],
                        0
                    )
                    
                    # Sort by best ratio (fewer euros per km = better ratio)
                    df_ratio = df_ratio.sort_values("rapporto_euro_km", ascending=True)
                    
                    # Prepare final table
                    df_table = df_ratio[["nome_stazione", "Prezzo_skipass", "kmopen", "rapporto_euro_km"]].copy()
                    
                    # Rename columns for display
                    rename_map = {
                        "nome_stazione": "🏔️ Resort",
                        "Prezzo_skipass": "💶 Skipass (€)",
                        "kmopen": "🛷 Open Km",
                        "rapporto_euro_km": "💸 €/Km"
                    }
                    df_table = df_table.rename(columns=rename_map)
                    
                    # Format values
                    if "💶 Skipass (€)" in df_table.columns:
                        df_table["💶 Skipass (€)"] = df_table["💶 Skipass (€)"].round(2)
                    if "🛷 Open Km" in df_table.columns:
                        df_table["🛷 Open Km"] = df_table["🛷 Open Km"].round(1)
                    if "💸 €/Km" in df_table.columns:
                        df_table["💸 €/Km"] = df_table["💸 €/Km"].round(2)
                    
                    st.markdown("""
                    **Calculated Index:**
                    - **€/Km**: fewer euros per kilometer of slope = better quality-price ratio
                    """)
                    
                    # Show all stations (should be 7)
                    st.markdown('<div class="modern-table">', unsafe_allow_html=True)
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("Insufficient data to calculate kmopen/cost skipass ratio")
            else:
                st.info("Columns 'kmopen' or 'Prezzo_skipass' not available for analysis")
        except Exception as e:
            st.warning(f"Error calculating ratio: {e}")
            st.write(f"Complete error: {str(e)}")
        
        # 3) AI Overview – Low-Cost
        try:
            st.markdown('<h5 class="modern-subheader">🤖 AI Overview – Low-Cost</h5>', unsafe_allow_html=True)
            prompt_lowcost = build_lowcost_prompt(df_filtered_rec, best_name, livello, data_sel)
            out, usage = generate_overview(prompt_lowcost, max_tokens=140)
            st.write(out or "No content available now.")
            if isinstance(usage, dict) and usage.get("model"):
                st.caption(f"Model: {usage['model']}")
        except Exception as e:
            st.warning(f"Error in AI Overview: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # --- Final section: simple rankings by level and profile ---
    try:
        if df_with_indices is not None and not df_with_indices.empty:
            st.markdown('<div class="glow-card info">', unsafe_allow_html=True)
            st.markdown('<h4 class="modern-subheader">🏆 Rankings & Indices</h4>', unsafe_allow_html=True)
            
            # Ranking by level
            st.markdown('<h5 class="modern-subheader">📊 Level Ranking</h5>', unsafe_allow_html=True)
            level_to_col = {"base": "indice_base", "medio": "indice_medio", "esperto": "indice_esperto"}
            level_col = level_to_col.get(livello)
            if level_col and level_col in df_with_indices.columns:
                df_level_rank = (
                    df_with_indices.groupby("nome_stazione")[level_col]
                    .mean()
                    .reset_index()
                    .sort_values(level_col, ascending=False)
                )
                fig_lvl = px.bar(
                    df_level_rank,
                    x="nome_stazione",
                    y=level_col,
                    title=f"Ranking (Level: {livello})",
                    labels={"nome_stazione": "Resort", level_col: "Level Index"},
                )
                fig_lvl.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_lvl, use_container_width=True)
            else:
                st.info("Select a level to see the level ranking.")

            # Ranking by profile
            st.markdown('<h5 class="modern-subheader">👤 Profile Ranking</h5>', unsafe_allow_html=True)
            profile_to_col = {
                "panoramico": "indice_panoramico",
                "familiare": "indice_famigliare",
                "festaiolo": "indice_festaiolo",
                "lowcost": "indice_lowcost",
            }
            prof_col = profile_to_col.get(profilo_norm)
            if prof_col and prof_col in df_with_indices.columns:
                df_prof_rank = (
                    df_with_indices.groupby("nome_stazione")[prof_col]
                    .mean()
                    .reset_index()
                    .sort_values(prof_col, ascending=False)
                )
                fig_prof = px.bar(
                    df_prof_rank,
                    x="nome_stazione",
                    y=prof_col,
                    title=f"Ranking (Profile: {profilo_norm})",
                    labels={"nome_stazione": "Resort", prof_col: "Profile Index"},
                )
                fig_prof.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prof, use_container_width=True)
            else:
                st.info("Select a profile to see the profile ranking.")
            st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        pass

    st.caption("v2 – Recommended station, AI overview and dedicated views by level")


if __name__ == "__main__":
    main()