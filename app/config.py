"""Central configuration for v2 ski recommender app."""

DAYS_RANGE = 15  # days before/after the selected date
DEFAULT_TOP_N = 5

# LLM via OpenRouter
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_LLM_MODEL = "mistralai/mistral-nemo:free"

# How much the optional user profile affects the final score (0-1)
PROFILE_ALPHA = 0.20

SUPPORTED_PROFILES = ["nessuno", "panoramico", "familiare", "festaiolo", "lowcost"]

# Column aliases expected for the new indices (documentation aid)
# Infonieve: Piste_verdi, Piste_blu, Piste_rosse, Piste_nere, Quota_min, Quota_max,
#            Slalom, Snowpark, Area_gare, Superpipe, Scii_notte, kmtotal,
#            Prezzo_skipass, Prezzo_scuola, Prezzo_noleggio, Area_bambini
# Meteo:     vento, nebbia, pioggia, sole
# Valanghe:  danger_level_avg
# Recensioni: Stelle, sicurezza, ristoranti, familiare, festaiolo, panoramico, lowcost, coda


