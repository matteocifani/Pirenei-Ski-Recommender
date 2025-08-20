from __future__ import annotations

import datetime
from datetime import timedelta
from typing import Optional

import pandas as pd
import streamlit as st
from sklearn.preprocessing import MinMaxScaler

from .config import DAYS_RANGE


def ensure_date_column(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame({"date": pd.Series([], dtype="datetime64[ns]")})
    df = df.copy()
    if "date" not in df.columns:
        if "Data" in df.columns:
            df["date"] = pd.to_datetime(df["Data"], errors="coerce")
        else:
            df["date"] = pd.NaT
    else:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


@st.cache_data(ttl=7200, show_spinner=False)  # Cache per 2 ore
def get_historical_data_for_date(
    df: pd.DataFrame, target_date: datetime.date, days_range: int = DAYS_RANGE
) -> pd.DataFrame:
    if (
        df is None
        or df.empty
        or "date" not in df.columns
        or not pd.api.types.is_datetime64_any_dtype(df["date"])
    ):
        return pd.DataFrame({"date": pd.Series([], dtype="datetime64[ns]")})
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date)

    target_month = int(target_date.month)
    target_day = int(target_date.day)

    available_years = df["date"].dt.year.dropna().unique()

    historical_parts = []
    for year in available_years:
        year = int(year)
        if year < target_date.year:
            start_date = pd.Timestamp(year, target_month, target_day) - timedelta(days=int(days_range))
            end_date = pd.Timestamp(year, target_month, target_day) + timedelta(days=int(days_range))
            year_data = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
            historical_parts.append(year_data)

    if historical_parts:
        return pd.concat(historical_parts, ignore_index=True)
    return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)  # Cache per 1 ora
def compute_indices(
    df_infonieve: pd.DataFrame,
    df_valanghe: pd.DataFrame,
    df_meteo: pd.DataFrame,
    df_recensioni: pd.DataFrame,
    target_date: datetime.date,
) -> pd.DataFrame:
    if target_date > datetime.date.today():
        df_infonieve_filtered = get_historical_data_for_date(df_infonieve, target_date)
        df_valanghe_filtered = get_historical_data_for_date(df_valanghe, target_date)
        df_meteo_filtered = get_historical_data_for_date(df_meteo, target_date)
        df_recensioni_filtered = get_historical_data_for_date(df_recensioni, target_date)
    else:
        df_infonieve_filtered = df_infonieve[df_infonieve["date"] == pd.to_datetime(target_date)]
        df_valanghe_filtered = df_valanghe[df_valanghe["date"] == pd.to_datetime(target_date)]
        df_meteo_filtered = df_meteo[df_meteo["date"] == pd.to_datetime(target_date)]
        df_recensioni_filtered = df_recensioni[df_recensioni["date"] == pd.to_datetime(target_date)]

    df_merged = df_infonieve_filtered.copy()
    if not df_merged.empty:
        df_merged = df_merged.merge(df_meteo_filtered, how="left", on=["nome_stazione", "date"])
        df_merged = df_merged.merge(
            df_valanghe_filtered[["nome_stazione", "date", "danger_level_avg"]],
            how="left",
            on=["nome_stazione", "date"],
        )
        df_merged = df_merged.merge(df_recensioni_filtered, how="left", on=["nome_stazione", "date"])

    if df_merged.empty:
        return pd.DataFrame()

    scaler = MinMaxScaler()

    def normalize(df_subset: pd.DataFrame) -> pd.DataFrame:
        if df_subset.empty:
            return pd.DataFrame()
        filled = df_subset.fillna(0)
        normalized = pd.DataFrame(
            scaler.fit_transform(filled), columns=df_subset.columns, index=df_subset.index
        )
        return normalized

    try:
        # Indice livello: base
        base_cols = [
            "Piste_verdi",
            "Piste_blu",
            "Quota_min",
            "vento",
            "nebbia",
            "espesor_medio",
            "Stelle",
        ]
        base_df = pd.DataFrame({
            "Piste_verdi": df_merged["Piste_verdi"] if "Piste_verdi" in df_merged.columns else 0,
            "Piste_blu": df_merged["Piste_blu"] if "Piste_blu" in df_merged.columns else 0,
            "Quota_min": df_merged["Quota_min"] if "Quota_min" in df_merged.columns else 0,
            "vento": df_merged["vento"] if "vento" in df_merged.columns else 0,
            "nebbia": df_merged["nebbia"] if "nebbia" in df_merged.columns else 0,
            "espesor_medio": df_merged["espesor_medio"] if "espesor_medio" in df_merged.columns else 0,
            "Stelle": df_merged["Stelle"] if "Stelle" in df_merged.columns else 0,
        }).fillna(0)
        if not base_df.empty:
            base_norm = pd.DataFrame(MinMaxScaler().fit_transform(base_df), columns=base_df.columns)
            df_merged["indice_base"] = (
                0.25 * base_norm["Piste_verdi"]
                + 0.15 * base_norm["Piste_blu"]
                + 0.05 * base_norm["Quota_min"]
                + 0.05 * (1 - base_norm["vento"])
                + 0.05 * (1 - base_norm["nebbia"])
                + 0.20 * base_norm["espesor_medio"]
                + 0.25 * base_norm["Stelle"]
            )

        # Indice livello: medio
        medio_df = pd.DataFrame({
            "Piste_blu": df_merged["Piste_blu"] if "Piste_blu" in df_merged.columns else 0,
            "Piste_rosse": df_merged["Piste_rosse"] if "Piste_rosse" in df_merged.columns else 0,
            "vento": df_merged["vento"] if "vento" in df_merged.columns else 0,
            "nebbia": df_merged["nebbia"] if "nebbia" in df_merged.columns else 0,
            "espesor_medio": df_merged["espesor_medio"] if "espesor_medio" in df_merged.columns else 0,
            "Stelle": df_merged["Stelle"] if "Stelle" in df_merged.columns else 0,
        }).fillna(0)
        if not medio_df.empty:
            medio_norm = pd.DataFrame(MinMaxScaler().fit_transform(medio_df), columns=medio_df.columns)
            df_merged["indice_medio"] = (
                0.25 * medio_norm["Piste_blu"]
                + 0.25 * medio_norm["Piste_rosse"]
                + 0.05 * (1 - medio_norm["vento"])
                + 0.05 * (1 - medio_norm["nebbia"])
                + 0.20 * medio_norm["espesor_medio"]
                + 0.20 * medio_norm["Stelle"]
            )

        # Indice livello: esperto
        esperto_df = pd.DataFrame({
            "Piste_nere": df_merged["Piste_nere"] if "Piste_nere" in df_merged.columns else 0,
            "Slalom": df_merged["Slalom"] if "Slalom" in df_merged.columns else 0,
            "Snowpark": df_merged["Snowpark"] if "Snowpark" in df_merged.columns else 0,
            "Area_gare": df_merged["Area_gare"] if "Area_gare" in df_merged.columns else 0,
            "Superpipe": df_merged["Superpipe"] if "Superpipe" in df_merged.columns else 0,
            "Scii_notte": df_merged["Scii_notte"] if "Scii_notte" in df_merged.columns else 0,
            "espesor_medio": df_merged["espesor_medio"] if "espesor_medio" in df_merged.columns else 0,
            "Quota_max": df_merged["Quota_max"] if "Quota_max" in df_merged.columns else 0,
            "pioggia": df_merged["pioggia"] if "pioggia" in df_merged.columns else 0,
            "danger_level_avg": df_merged["danger_level_avg"] if "danger_level_avg" in df_merged.columns else 0,
            "kmtotal": df_merged["kmtotal"] if "kmtotal" in df_merged.columns else 0,
        }).fillna(0)
        if not esperto_df.empty:
            esperto_norm = pd.DataFrame(MinMaxScaler().fit_transform(esperto_df), columns=esperto_df.columns)
            df_merged["indice_esperto"] = (
                0.15 * esperto_norm["Piste_nere"]
                + 0.05 * esperto_norm["Slalom"]
                + 0.10 * esperto_norm["Snowpark"]
                + 0.05 * esperto_norm["Area_gare"]
                + 0.05 * esperto_norm["Superpipe"]
                + 0.05 * esperto_norm["Scii_notte"]
                + 0.15 * esperto_norm["espesor_medio"]
                + 0.10 * esperto_norm["Quota_max"]
                + 0.05 * (1 - esperto_norm["pioggia"]) 
                + 0.15 * (1 - esperto_norm["danger_level_avg"]) 
                + 0.10 * esperto_norm["kmtotal"]
            )

        # Indici profilo: famigliare
        famigliare_df = pd.DataFrame({
            "Piste_verdi": df_merged.get("Piste_verdi", 0),
            "Piste_blu": df_merged.get("Piste_blu", 0),
            "Area_bambini": df_merged.get("Area_bambini", 0),
            "Prezzo_noleggio": df_merged.get("Prezzo_noleggio", 0),
            "Prezzo_scuola": df_merged.get("Prezzo_scuola", 0),
            "sicurezza": df_merged.get("sicurezza", 0),
            "ristoranti": df_merged.get("ristoranti", 0),
            "familiare": df_merged.get("familiare", 0),
            "pioggia": df_merged.get("pioggia", 0),
            "nebbia": df_merged.get("nebbia", 0),
            "coda": df_merged.get("coda", 0),
        }).fillna(0)
        if not famigliare_df.empty:
            fam_norm = pd.DataFrame(MinMaxScaler().fit_transform(famigliare_df), columns=famigliare_df.columns)
            df_merged["indice_famigliare"] = (
                0.10 * fam_norm["Piste_verdi"]
                + 0.15 * fam_norm["Piste_blu"]
                + 0.15 * fam_norm["Area_bambini"]
                + 0.05 * (1 - fam_norm["Prezzo_noleggio"]) 
                + 0.05 * (1 - fam_norm["Prezzo_scuola"]) 
                + 0.10 * fam_norm["sicurezza"]
                + 0.10 * fam_norm["ristoranti"]
                + 0.15 * fam_norm["familiare"]
                + 0.05 * (1 - fam_norm["pioggia"]) 
                + 0.05 * (1 - fam_norm["nebbia"]) 
                + 0.05 * (1 - fam_norm["coda"]) 
            )

        # Indice profilo: festaiolo
        festaiolo_df = pd.DataFrame({
            "Snowpark": df_merged.get("Snowpark", 0),
            "Scii_notte": df_merged.get("Scii_notte", 0),
            "ristoranti": df_merged.get("ristoranti", 0),
            "Stelle": df_merged.get("Stelle", 0),
            "festaiolo": df_merged.get("festaiolo", 0),
            "pioggia": df_merged.get("pioggia", 0),
        }).fillna(0)
        if not festaiolo_df.empty:
            fes_norm = pd.DataFrame(MinMaxScaler().fit_transform(festaiolo_df), columns=festaiolo_df.columns)
            df_merged["indice_festaiolo"] = (
                0.20 * fes_norm["Snowpark"]
                + 0.15 * fes_norm["Scii_notte"]
                + 0.20 * fes_norm["ristoranti"]
                + 0.10 * fes_norm["Stelle"]
                + 0.30 * fes_norm["festaiolo"]
                + 0.05 * (1 - fes_norm["pioggia"]) 
            )

        # Indice profilo: panoramico
        panoramico_df = pd.DataFrame({
            "panoramico": df_merged.get("panoramico", 0),
            "pioggia": df_merged.get("pioggia", 0),
            "vento": df_merged.get("vento", 0),
            "sole": df_merged.get("sole", 0),
            "nebbia": df_merged.get("nebbia", 0),
            "Quota_max": df_merged.get("Quota_max", 0),
        }).fillna(0)
        if not panoramico_df.empty:
            pan_norm = pd.DataFrame(MinMaxScaler().fit_transform(panoramico_df), columns=panoramico_df.columns)
            df_merged["indice_panoramico"] = (
                0.25 * pan_norm["panoramico"]
                + 0.15 * (1 - pan_norm["pioggia"]) 
                + 0.10 * (1 - pan_norm["vento"]) 
                + 0.20 * pan_norm["sole"]
                + 0.10 * (1 - pan_norm["nebbia"]) 
                + 0.20 * (1 - pan_norm["Quota_max"]) 
            )

        # Indice profilo: lowcost
        lowcost_df = pd.DataFrame({
            "lowcost": df_merged.get("lowcost", 0),
            "Prezzo_skipass": df_merged.get("Prezzo_skipass", 0),
            "kmopen": df_merged.get("kmopen", 0),
            "Prezzo_scuola": df_merged.get("Prezzo_scuola", 0),
            "Prezzo_noleggio": df_merged.get("Prezzo_noleggio", 0),
        }).fillna(0)
        if not lowcost_df.empty:
            low_norm = pd.DataFrame(MinMaxScaler().fit_transform(lowcost_df), columns=lowcost_df.columns)
            df_merged["indice_lowcost"] = (
                0.25 * low_norm["lowcost"]
                + 0.20 * (1 - low_norm["Prezzo_skipass"]) 
                + 0.15 * low_norm["kmopen"]
                + 0.20 * (1 - low_norm["Prezzo_scuola"]) 
                + 0.20 * (1 - low_norm["Prezzo_noleggio"]) 
            )
    except Exception:
        return df_merged

    return df_merged


