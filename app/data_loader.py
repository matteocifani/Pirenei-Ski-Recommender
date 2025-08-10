import os
import pandas as pd
import streamlit as st


@st.cache_data
def load_datasets():
    """Load CSV datasets and perform minimal preprocessing.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]
        (df_infonieve, df_valanghe, df_meteo, df_recensioni)
    """
    try:
        if os.path.exists("Infonieve_updated.csv") and os.path.getsize("Infonieve_updated.csv") > 0:
            df_infonieve = pd.read_csv("Infonieve_updated.csv", parse_dates=["date"])
            if not df_infonieve.empty:
                df_infonieve = df_infonieve.rename(columns={"name": "nome_stazione"})
            else:
                raise ValueError("File Infonieve vuoto")
        else:
            raise FileNotFoundError("File Infonieve non trovato")

        if os.path.exists("Valanghe_filtered_updated.csv") and os.path.getsize("Valanghe_filtered_updated.csv") > 0:
            df_valanghe = pd.read_csv("Valanghe_filtered_updated.csv", parse_dates=["date"])
            if not df_valanghe.empty:
                df_valanghe = df_valanghe.rename(columns={"Name": "nome_stazione"})
            else:
                raise ValueError("File Valanghe vuoto")
        else:
            raise FileNotFoundError("File Valanghe non trovato")

        if os.path.exists("df_meteo_updated.csv") and os.path.getsize("df_meteo_updated.csv") > 0:
            df_meteo = pd.read_csv("df_meteo_updated.csv", parse_dates=["time"])
            if not df_meteo.empty:
                df_meteo = df_meteo.rename(columns={"località": "nome_stazione", "time": "date"})
            else:
                raise ValueError("File Meteo vuoto")
        else:
            raise FileNotFoundError("File Meteo non trovato")

        if os.path.exists("recensioni_updated.csv") and os.path.getsize("recensioni_updated.csv") > 0:
            df_recensioni = pd.read_csv("recensioni_updated.csv")
            if not df_recensioni.empty:
                df_recensioni = df_recensioni.rename(
                    columns={
                        "Stazione": "nome_stazione",
                        "Data": "date",
                        "parole_ristorazione": "ristoranti",
                        "parole_code": "coda",
                        "parole_sicurezza": "sicurezza",
                        "parole_famiglia": "familiare",
                        "parole_festa": "festaiolo",
                        "parole_panoramico": "panoramico",
                        "parole_lowcost": "lowcost",
                    }
                )
                df_recensioni["date"] = pd.to_datetime(df_recensioni["date"], errors="coerce")
            else:
                raise ValueError("File Recensioni vuoto")
        else:
            raise FileNotFoundError("File Recensioni non trovato")

        # Derived columns
        if "espesormin" in df_infonieve.columns and "espesormax" in df_infonieve.columns:
            df_infonieve["espesor_medio"] = (
                df_infonieve["espesormin"] + df_infonieve["espesormax"]
            ) / 2
        else:
            df_infonieve["espesor_medio"] = 0

        return df_infonieve, df_valanghe, df_meteo, df_recensioni

    except Exception as exc:  # show a friendly warning in the UI
        st.warning(f"Impossibile caricare i file CSV: {exc}")
        return None, None, None, None


