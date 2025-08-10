from __future__ import annotations

import pandas as pd


def apply_profile_adjustment(
    df_with_indices: pd.DataFrame, livello: str, profilo: str
) -> pd.DataFrame:
    """Adjust the chosen level index using an optional profile preference.

    Parameters
    ----------
    df_with_indices : pd.DataFrame
        Must include columns: nome_stazione and indice_<livello>
    livello : str
        one of {"base", "medio", "esperto"}
    profilo : str
        one of {"nessuno", "panoramico", "familiare", "festaiolo", "lowcost"}
    """

    if df_with_indices is None or df_with_indices.empty:
        return df_with_indices

    # Map columns for level and profile indices
    level_to_index_col = {
        "base": "indice_base",
        "medio": "indice_medio",
        "esperto": "indice_esperto",
    }

    profile_to_index_col = {
        "panoramico": "indice_panoramico",
        "familiare": "indice_famigliare",
        "festaiolo": "indice_festaiolo",
        "lowcost": "indice_lowcost",
    }

    df = df_with_indices.copy()

    level_col = level_to_index_col.get(livello)
    profile_col = profile_to_index_col.get(profilo)

    level_available = bool(level_col and level_col in df.columns)
    profile_available = bool(profile_col and profile_col in df.columns)

    # Case 1: solo livello selezionato => 100% livello
    if livello != "nessuno" and profilo == "nessuno" and level_available:
        df["indice_finale"] = df[level_col].fillna(0)
        return df

    # Case 2: solo profilo selezionato => 100% profilo
    if livello == "nessuno" and profilo != "nessuno" and profile_available:
        df["indice_finale"] = df[profile_col].fillna(0)
        return df

    # Case 3: entrambi selezionati => 50% livello, 50% profilo
    if livello != "nessuno" and profilo != "nessuno" and level_available and profile_available:
        df["indice_finale"] = 0.5 * df[level_col].fillna(0) + 0.5 * df[profile_col].fillna(0)
        return df

    # Fallbacks:
    # - Se abbiamo solo il livello disponibile, usiamo quello
    if level_available:
        df["indice_finale"] = df[level_col].fillna(0)
        return df

    # - Se abbiamo solo il profilo disponibile, usiamo quello
    if profile_available:
        df["indice_finale"] = df[profile_col].fillna(0)
        return df

    # - Nessuno disponibile: crea una colonna neutra (zeri) per evitare errori a valle
    df["indice_finale"] = 0
    return df


def build_ranking(df: pd.DataFrame, score_column: str = "indice_finale") -> pd.DataFrame:
    if df is None or df.empty or score_column not in df.columns:
        return pd.DataFrame()
    grouped = df.groupby("nome_stazione")[score_column].mean().reset_index()
    return grouped.sort_values(score_column, ascending=False)


