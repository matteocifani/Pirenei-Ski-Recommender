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

from app.data_loader import load_datasets
from app.prediction import compute_indices, get_historical_data_for_date
from app.scoring import apply_profile_adjustment, build_ranking
from app.llm import generate_overview
from app.config import SUPPORTED_PROFILES


st.set_page_config(layout="wide", page_title="🎿 Sci su misura v2 - Pirenei", page_icon="🎿")

# Minimal modern styling
st.markdown(
    """
    <style>
      .main {
        background: radial-gradient(1200px 600px at 10% 10%, rgba(0, 140, 255, 0.08), transparent 60%),
                    radial-gradient(1000px 500px at 90% 20%, rgba(0, 255, 200, 0.06), transparent 60%),
                    linear-gradient(180deg, #0b1020, #0f1426 40%, #0b1020);
        color: #e6efff;
      }
      .glass-wrap { display: flex; gap: 16px; }
      .glass-card {
        width: 100%;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 14px 16px;
        position: relative;
        overflow: hidden;
      }
      .glass-card:before {
        content: "";
        position: absolute; inset: -2px;
        background: radial-gradient(600px 200px at 20% -20%, rgba(0,255,200,0.12), transparent 60%),
                    radial-gradient(500px 200px at 120% 120%, rgba(0,170,255,0.12), transparent 60%);
        filter: blur(20px);
        z-index: 0;
      }
      .glass-card .content { position: relative; z-index: 1; }
      .kpi-card { min-height: 120px; display: flex; }
      .hero {
        background: linear-gradient(135deg, rgba(0, 170, 255, 0.22), rgba(0, 255, 170, 0.12));
        border: 1px solid rgba(255, 255, 255, 0.16);
        box-shadow: 0 10px 40px rgba(0, 200, 255, 0.15), 0 10px 40px rgba(0, 255, 160, 0.12);
        border-radius: 18px;
        padding: 18px 20px;
      }
      .kpi {font-size: 24px; font-weight: 700;}
      .subtle {color:#a9b8d0; font-size:13px}
      .good {color:#6ef7c8}
      .warn {color:#ffd27e}
      .bad {color:#ff7e7e}
      /* podium styles */
      .podium {display:flex; align-items:flex-end; gap:12px; margin: 8px 0 18px}
      .podium .col {flex:1; text-align:center}
      .podium .step {background: rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12); border-radius:10px; padding:10px 8px}
      .podium .s1 {height: 180px}
      .podium .s2 {height: 120px}
      .podium .s3 {height: 120px}
      .podium .name {font-weight:700}
      .podium .medal {font-size: 22px; opacity:0.9}
    </style>
    """,
    unsafe_allow_html=True,
)


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
        f"Scrivi un’overview molto breve (max 2 frasi, 35–45 parole), chiara e utile, che spieghi perché {best_name} è preferibile rispetto alle altre. "
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
        st.info("Coordinate non disponibili per la mappa.")
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
    st.title("🏔️ Pirenei Ski Recommender v2")

    with st.spinner("Caricamento dati..."):
        df_infonieve, df_valanghe, df_meteo, df_recensioni = load_datasets()

    if df_infonieve is None:
        st.error("Impossibile caricare i dati. Verifica i CSV.")
        return

    st.sidebar.header("Filtri")
    min_date = df_infonieve["date"].min().date()
    default_date = datetime.date(2025, 12, 17)
    data_sel = st.sidebar.date_input("Data", value=default_date, min_value=min_date, max_value=datetime.date(2030, 12, 31))
    livello = st.sidebar.selectbox("Livello", ["nessuno", "base", "medio", "esperto"], index=3)
    profilo = st.sidebar.selectbox("Profilo (opzionale)", SUPPORTED_PROFILES, index=0)
    profilo_norm = str(profilo).strip().lower()

    # Considera sempre tutte le stazioni
    df_filtered_infonieve = df_infonieve.copy()
    df_filtered_val = df_valanghe.copy()
    df_filtered_meteo = df_meteo.copy()
    df_filtered_rec = df_recensioni.copy()

    df_with_indices = compute_indices(
        df_filtered_infonieve, df_filtered_val, df_filtered_meteo, df_filtered_rec, data_sel
    )

    if df_with_indices.empty:
        st.warning("La stazione non è aperta in questa data. Prova a scegliere un altro giorno per divertirti sulla neve!")
        # Tabella media apertura/chiusura per impianto (sugli anni disponibili) con logica 5 chiusi/prima e 5 aperti/dopo
        try:
            base = df_infonieve.dropna(subset=["date"]).copy()
            base["date"] = pd.to_datetime(base["date"], errors="coerce")
            base = base.dropna(subset=["date"])  # robustezza
            base["year"] = base["date"].dt.year

            # Costruisci colonna stato (1 aperto, 0 chiuso)
            if "idestado" in base.columns:
                base["stato"] = base["idestado"].fillna(0).astype(int).clip(0, 1)
            elif "kmopen" in base.columns:
                base["stato"] = (base["kmopen"].fillna(0) > 0).astype(int)
            else:
                base["stato"] = 0  # se non sappiamo, consideriamo chiuso

            rows = []
            for (staz, yr), g in base.groupby(["nome_stazione", "year"], as_index=False):
                gd = g.sort_values("date").reset_index(drop=True)
                s = gd["stato"].astype(int).tolist()
                dates = gd["date"].tolist()
                n = len(gd)
                open_date = None
                close_date = None
                for i in range(n):
                    # finestre
                    prev5 = s[i-5:i] if i-5 >= 0 else []
                    next5 = s[i+1:i+6] if i+6 <= n else []
                    if len(prev5) == 5 and len(next5) == 5:
                        # apertura: 5 chiusi prima (tutti 0) e 5 aperti dopo (tutti 1)
                        if sum(prev5) == 0 and sum(next5) == 5 and open_date is None:
                            open_date = dates[i]
                        # chiusura: 5 aperti prima e 5 chiusi dopo
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
                # calcola DOY medi ignorando NaT
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
                    columns={"nome_stazione": "Impianto"}
                )
                st.dataframe(table, use_container_width=True, hide_index=True)
        except Exception:
            pass
        return

    df_scored = apply_profile_adjustment(df_with_indices, livello, profilo)
    ranking = build_ranking(df_scored, "indice_finale")

    # Aggregated KPIs (mean over the window) for all stations
    df_kpis = aggregate_station_kpis(df_with_indices)

    # Best station name
    best_name = ranking.iloc[0]["nome_stazione"] if not ranking.empty else df_kpis.sort_values("km_open_est", ascending=False).iloc[0]["nome_stazione"]

    # Mostra raccomandazione solo se almeno un filtro è selezionato
    if not (livello == "nessuno" and profilo == "nessuno"):
        st.subheader(f"✅ Stazione consigliata: {best_name}")
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
                        <div class='glass-card kpi-card'><div class='content'>
                      <div class='subtle'>Km piste aperte stimati</div>
                      <div class='kpi'>{k_row.km_open_est:.0f} km</div>
                    </div></div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                pct = k_row.pct_open * 100 if k_row.pct_open == k_row.pct_open else 0
                st.markdown(
                    f"""
                        <div class='glass-card kpi-card'><div class='content'>
                      <div class='subtle'>% piste aperte (stima)</div>
                      <div class='kpi'>{pct:.0f}%</div>
                    </div></div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"""
                        <div class='glass-card kpi-card'><div class='content'>
                      <div class='subtle'>Probabilità impianto aperto</div>
                      <div class='kpi'>{k_row.open_prob*100:.0f}%</div>
                    </div></div>
                    """,
                    unsafe_allow_html=True,
                )
    # end header cards

    # Map with highlight (solo per livelli diversi da "nessuno"; per "nessuno" la mostriamo più sotto)
    if livello != "nessuno" and not df_kpis.empty:
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
            # Ring per la consigliata (solo bordo, senza riempimento)
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
            deck = pdk.Deck(layers=[layer_all, ring_layer, star_layer], initial_view_state=view_state, tooltip={"text": "{nome_stazione}\nKm aperti: {km_open_est}"})
            st.pydeck_chart(deck, use_container_width=True)

    # Space for separation (avoid redundant horizontal rule under caption)
    st.write("")
    # AI overview: disattivata quando livello == "nessuno"
    if livello != "nessuno":
        st.subheader("✨ AI overview")
        api_key_present = bool(os.getenv("OPENROUTER_API_KEY"))
        try:
            if not api_key_present:
                st.info("Configura OPENROUTER_API_KEY per abilitare l'overview AI.")
            else:
                prompt = build_llm_prompt(df_kpis, best_name, livello, profilo, data_sel)
                with st.spinner("Generazione riepilogo AI..."):
                    output, usage = generate_overview(prompt, max_tokens=160)
                model_used = usage.get("model") if isinstance(usage, dict) else None
                if isinstance(usage, dict) and usage.get("error"):
                    st.error(f"Errore modello: {usage['error']}")
                    if model_used:
                        st.caption(f"Modello: {model_used}")
                elif output:
                    st.write(output)
                    if model_used:
                        st.caption(f"Modello: {model_used}")
                else:
                    st.error("Nessuna risposta dal modello.")
        except Exception as e:
            st.error(f"LLM non disponibile: {e}")

    st.markdown("---")
    # Level-specific visualizations (no raw index shown)
    if livello == "base":
        st.subheader("Per principianti: dove trovi più piste facili e condizioni stabili")
        # Mappa con consigliata evidenziata
        st.subheader("Mappa delle stazioni (consigliata evidenziata)")
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

        # Dati meteo correnti/previsti (±3 giorni) sempre da storico per coerenza
        meteo_data = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=3)
        if not meteo_data.empty:
            st.subheader("Probabilità condizioni meteo (storico ±3 giorni)")
            # baseline ±15 giorni sugli anni precedenti
            baseline = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=15)
            col1, col2 = st.columns(2)
            with col1:
                prob_nebbia = float(meteo_data.get("nebbia", 0).mean() * 100)
                baseline_nebbia = float((baseline.get("nebbia", 0).mean() * 100) if not baseline.empty else 0)
                fig_n = create_speedometer(prob_nebbia, "Prob. Nebbia", "#94a3b8", reference_pct=baseline_nebbia)
                st.plotly_chart(fig_n, use_container_width=True)
            with col2:
                prob_pioggia = float(meteo_data.get("pioggia", 0).mean() * 100)
                baseline_pioggia = float((baseline.get("pioggia", 0).mean() * 100) if not baseline.empty else 0)
                fig_p = create_speedometer(prob_pioggia, "Prob. Pioggia", "#60a5fa", reference_pct=baseline_pioggia)
                st.plotly_chart(fig_p, use_container_width=True)
            st.caption("Nota: probabilità calcolate sui dati storici per periodi simili; il delta confronta con la media degli anni precedenti nella finestra ±15 giorni.")
        else:
            st.warning("Dati meteo non disponibili per questa data")

        # Barre impilate piste verdi/blu ordinate per indice_base
        if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
            st.subheader("Distribuzione piste verdi e blu")
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
        if profilo_norm == "festaiolo":
            st.subheader("Profilo: Festaiolo")
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

        if profilo_norm == "familiare":
            st.subheader("Profilo: Familiare")
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

            # 3) AI Overview – Famiglia
            try:
                st.subheader("AI Overview – Famiglia")
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "Nessun contenuto disponibile ora.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Modello: {usage['model']}")
            except Exception:
                pass
            # RIMOSSI: Snowpark/Superpipe e AI Overview – Festa (solo per profilo festaiolo)

    elif livello == "medio":
        st.subheader("Per intermedi: equilibrio tra piste e sicurezza")
        # Mappa con consigliata evidenziata
        st.subheader("Mappa delle stazioni (consigliata evidenziata)")
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

        # Meteo compatto (5 mini-donut) per la stazione consigliata
        try:
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

                st.subheader("Meteo (storico ±3 giorni)")
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

        # Mappa delle stazioni (con evidenza della consigliata)
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

        # Barre: piste blu/rosse ordinate per indice_medio
        if not df_with_indices.empty and "indice_medio" in df_with_indices.columns:
            st.subheader("Piste blu e rosse per stazione (ordinate per indice medio)")
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
        if profilo_norm == "festaiolo":
            st.subheader("Profilo: Festaiolo")
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
            try:
                prompt_f = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                st.subheader("AI Overview – Festa")
                out, usage = generate_overview(prompt_f, max_tokens=140)
                st.write(out or "Nessun contenuto disponibile ora.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Modello: {usage['model']}")
            except Exception:
                pass

        # Sezione Familiare (profilo)
        if profilo_norm == "familiare":
            st.subheader("Profilo: Familiare")
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

            # 3) AI Overview – Famiglia
            try:
                st.subheader("AI Overview – Famiglia")
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "Nessun contenuto disponibile ora.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Modello: {usage['model']}")
            except Exception:
                pass

    elif livello == "esperto":
        st.subheader("Per esperti: caratteristiche tecniche e chilometri")
        # Mappa con consigliata evidenziata
        st.subheader("Mappa delle stazioni (consigliata evidenziata)")
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

        # Speedometer rischio valanghe (1-5) per la stazione consigliata (con delta vs baseline ±15g)
        try:
            brow = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
            risk = float(brow.get("avalanche", 3.0))
            # baseline: media danger_level_avg nella finestra ±15 giorni su anni precedenti
            base_val = get_historical_data_for_date(df_filtered_val, data_sel, days_range=15)
            bstation = base_val[base_val.get("nome_stazione", "").astype(str) == best_name]
            baseline = float(bstation.get("danger_level_avg", 0).mean()) if not bstation.empty else 0.0
            # Due livelli: subheader esterno e delta in basso, numero centrato
            d = risk - baseline
            st.subheader("Rischio valanghe (1-5)")
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
                st.subheader("KPI tecnici")
                vals = top_best[["Snowpark", "Area_gare", "Slalom", "Superpipe"]].fillna(0).mean()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"""<div class='glass-card kpi-card'><div class='content'><div class='subtle'><b>Snowpark</b></div><div class='kpi'>{vals.get('Snowpark',0):.0f}</div></div></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class='glass-card kpi-card'><div class='content'><div class='subtle'><b>Area gare</b></div><div class='kpi'>{vals.get('Area_gare',0):.0f}</div></div></div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class='glass-card kpi-card'><div class='content'><div class='subtle'><b>Slalom</b></div><div class='kpi'>{vals.get('Slalom',0):.0f}</div></div></div>""", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"""<div class='glass-card kpi-card'><div class='content'><div class='subtle'><b>Superpipe</b></div><div class='kpi'>{vals.get('Superpipe',0):.0f}</div></div></div>""", unsafe_allow_html=True)
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

        if profilo_norm == "festaiolo":
            st.subheader("Profilo: Festaiolo")
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
            try:
                prompt_f = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                st.subheader("AI Overview – Festa")
                out, usage = generate_overview(prompt_f, max_tokens=140)
                st.write(out or "Nessun contenuto disponibile ora.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Modello: {usage['model']}")
            except Exception:
                pass

        # Sezione Familiare (profilo)
        if profilo_norm == "familiare":
            st.subheader("Profilo: Familiare")
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

            # 3) AI Overview – Famiglia
            try:
                st.subheader("AI Overview – Famiglia")
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                st.write(out or "Nessun contenuto disponibile ora.")
                if isinstance(usage, dict) and usage.get("model"):
                    st.caption(f"Modello: {usage['model']}")
            except Exception:
                pass

    else:  # nessuno (panoramica base)
        st.subheader("Panoramica generale")
        # Grafico a barre: numero piste per tipologia per impianto (stacked)
        piste_cols = ["Piste_verdi", "Piste_blu", "Piste_rosse", "Piste_nere"]
        if set(piste_cols).issubset(df_with_indices.columns):
            piste_counts = (
                df_with_indices[["nome_stazione"] + piste_cols]
                .drop_duplicates()
                .fillna(0)
            )
            # Ordine per impianti con più piste aperte (se disponibile kmopen), altrimenti per somma piste
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
                "Piste_verdi": "Piste verdi",
                "Piste_blu": "Piste blu",
                "Piste_rosse": "Piste rosse",
                "Piste_nere": "Piste nere",
            }
            melted = piste_counts.rename(columns=rename_map).melt(
                "nome_stazione",
                value_vars=list(rename_map.values()),
                var_name="Tipo",
                value_name="Numero",
            )
            color_map = {
                "Piste verdi": "#22c55e",
                "Piste blu": "#60a5fa",
                "Piste rosse": "#ef4444",
                "Piste nere": "#111827",
            }
            fig_stack = px.bar(
                melted,
                x="nome_stazione",
                y="Numero",
                color="Tipo",
                barmode="stack",
                title="Numero piste per impianto e tipologia",
                color_discrete_map=color_map,
                category_orders={"nome_stazione": order},
            )
            fig_stack.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_stack, use_container_width=True)

        # Mappa degli impianti (centrata sulla zona) - versione semplice senza highlight in "nessuno"
        st.subheader("Mappa delle stazioni sciistiche")
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

        # Messaggio guida per profili senza livello
        if profilo_norm != "nessuno":
            if profilo_norm == "festaiolo":
                st.info("Seleziona un livello (Base/Medio/Esperto) per vedere la dashboard 'Festaiolo'.")
        else:
            st.info("Seleziona un profilo per avere informazioni più approfondite")

        # Trend spessore medio per tutti gli impianti, con focus selezionabile
        st.subheader("Trend spessore neve (tutti gli impianti)")
        try:
            anno = (pd.to_datetime(data_sel).year) - 1
            start = pd.Timestamp(anno, 11, 1)
            end = pd.Timestamp(anno + 1, 5, 1)
            history = df_filtered_infonieve[(df_filtered_infonieve["date"] >= start) & (df_filtered_infonieve["date"] < end)].dropna(subset=["espesor_medio"]).copy()
            if not history.empty:
                stations = sorted(history["nome_stazione"].unique().tolist())
                focus = st.selectbox("Evidenzia impianto", options=["(Nessuno)"] + stations, index=0)
                solo = st.checkbox("Mostra solo impianto selezionato", value=False)
                palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set3 + px.colors.qualitative.T10
                color_cycle = {name: palette[i % len(palette)] for i, name in enumerate(stations)}
                fig_lines = go.Figure()
                for name, grp in history.groupby("nome_stazione"):
                    if solo and focus != "(Nessuno)" and name != focus:
                        continue
                    if focus != "(Nessuno)" and name != focus:
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
                fig_lines.update_layout(xaxis_title="Data", yaxis_title="Spessore medio (cm)")
                st.plotly_chart(fig_lines, use_container_width=True)
        except Exception:
            pass

    # --- Sezione finale: classifiche semplici per livello e profilo ---
    
    # Sezione Profilo Low-Cost (solo se selezionato, dopo tutti i livelli)
    if profilo_norm == "lowcost":
        st.markdown("---")
        st.subheader("💰 Profilo: Low-Cost")
        
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
                    # Imputa kmopen per Saint-Lary usando regressione kmopen vs kmtotal
                    try:
                        from sklearn.linear_model import LinearRegression
                        
                        # Prepara dati per il training (escludi Saint-Lary e considera solo idestado=1)
                        df_train = df_with_indices[
                            (df_with_indices["nome_stazione"] != "Saint-Lary") & 
                            (df_with_indices["idestado"] == 1) &
                            (df_with_indices["kmopen"] > 0) &
                            (df_with_indices["kmtotal"] > 0)
                        ].copy()
                        
                        if len(df_train) >= 3:  # Serve almeno 3 punti per la regressione
                            # Crea features per la regressione: kmtotal vs kmopen
                            X_train = df_train[["kmtotal"]].values
                            y_train = df_train["kmopen"].values
                            
                            # Addestra il modello di regressione lineare
                            model = LinearRegression()
                            model.fit(X_train, y_train)
                            
                            # Predici kmopen per Saint-Lary usando il suo kmtotal
                            saint_lary_data = df_with_indices[
                                (df_with_indices["nome_stazione"] == "Saint-Lary") & 
                                (df_with_indices["idestado"] == 1)
                            ]
                            
                            if not saint_lary_data.empty and "kmtotal" in saint_lary_data.columns:
                                saint_lary_kmtotal = saint_lary_data["kmtotal"].mean()
                                
                                if saint_lary_kmtotal > 0:
                                    # Predici kmopen per Saint-Lary
                                    predicted_kmopen = model.predict([[saint_lary_kmtotal]])[0]
                                    
                                    # Aggiorna il valore di kmopen per Saint-Lary nella tabella
                                    df_ratio.loc[df_ratio["nome_stazione"] == "Saint-Lary", "kmopen"] = max(0, predicted_kmopen)
                                else:
                                    st.warning("⚠️ Saint-Lary non ha kmtotal > 0 per l'imputazione")
                            else:
                                st.warning("⚠️ Dati Saint-Lary non trovati per l'imputazione")
                        else:
                            st.warning("⚠️ Dati insufficienti per l'imputazione (servono almeno 3 stazioni con kmopen > 0 e kmtotal > 0)")
                    except Exception as e:
                        st.warning(f"⚠️ Errore nell'imputazione: {e}")
                    
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
                    
                    st.subheader("📊 Rapporto Qualità-Prezzo: Euro per Chilometro")
                    st.markdown("""
                    **Indice calcolato:**
                    - **€/Km**: meno euro per chilometro di pista = migliore rapporto qualità-prezzo
                    """)
                    
                    # Mostra tutte le stazioni (dovrebbero essere 7)
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                else:
                    st.info("Dati insufficienti per calcolare il rapporto kmopen/costo skipass")
            else:
                st.info("Colonne 'kmopen' o 'Prezzo_skipass' non disponibili per l'analisi")
        except Exception as e:
            st.warning(f"Errore nel calcolo del rapporto: {e}")
            st.write(f"Errore completo: {str(e)}")
        
        # 3) AI Overview – Low-Cost
        try:
            st.subheader("🤖 AI Overview – Low-Cost")
            prompt_lowcost = build_lowcost_prompt(df_filtered_rec, best_name, livello, data_sel)
            out, usage = generate_overview(prompt_lowcost, max_tokens=140)
            st.write(out or "Nessun contenuto disponibile ora.")
            if isinstance(usage, dict) and usage.get("model"):
                st.caption(f"Modello: {usage['model']}")
        except Exception as e:
            st.warning(f"Errore nell'AI Overview: {e}")
    
    # --- Sezione finale: classifiche semplici per livello e profilo ---
    try:
        if df_with_indices is not None and not df_with_indices.empty:
            st.markdown("---")
            # Classifica per livello
            st.subheader("Classifica e indici – Livello")
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
                    title=f"Ranking (livello: {livello})",
                    labels={"nome_stazione": "Impianto", level_col: "Indice livello"},
                )
                fig_lvl.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_lvl, use_container_width=True)
            else:
                st.info("Seleziona un livello per vedere la classifica per livello.")

            # Classifica per profilo
            st.subheader("Classifica e indici – Profilo")
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
                    title=f"Ranking (profilo: {profilo_norm})",
                    labels={"nome_stazione": "Impianto", prof_col: "Indice profilo"},
                )
                fig_prof.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prof, use_container_width=True)
            else:
                st.info("Seleziona un profilo per vedere la classifica per profilo.")
    except Exception:
        pass

    st.caption("v2 – Stazione consigliata, overview AI e viste dedicate per livello")


if __name__ == "__main__":
    main()