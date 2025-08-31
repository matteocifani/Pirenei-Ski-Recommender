# 🚀 Deployment su Streamlit Cloud

## Prerequisiti
1. Account su [Streamlit Cloud](https://streamlit.io/cloud)
2. Repository GitHub pubblico o privato
3. File `requirements.txt` con tutte le dipendenze Python

## Passi per il Deployment

### 1. Preparazione Repository
- ✅ `streamlit_app_v2.py` - App principale
- ✅ `requirements.txt` - Dipendenze Python
- ✅ `.streamlit/config.toml` - Configurazione Streamlit
- ✅ `packages.txt` - Dipendenze di sistema (se necessarie)

### 2. Push su GitHub
```bash
git add .
git commit -m "Preparazione per deployment Streamlit Cloud"
git push origin main
```

### 3. Deployment su Streamlit Cloud
1. Vai su [share.streamlit.io](https://share.streamlit.io)
2. Fai login con il tuo account GitHub
3. Clicca "New app"
4. Seleziona il repository: `matteocifani/Pirenei-Ski-Recommender`
5. Imposta il file path: `streamlit_app_v2.py`
6. Clicca "Deploy!"

### 4. Configurazione Variabili d'Ambiente
Se hai API keys o configurazioni sensibili, aggiungile in:
- Streamlit Cloud → App → Settings → Secrets

### 5. Monitoraggio
- **Logs**: Streamlit Cloud → App → Logs
- **Analytics**: Streamlit Cloud → App → Analytics
- **Settings**: Streamlit Cloud → App → Settings

## Struttura File per Streamlit
```
Pirenei-Ski-Recommender/
├── streamlit_app_v2.py      # App principale
├── requirements.txt          # Dipendenze Python
├── .streamlit/
│   └── config.toml         # Configurazione Streamlit
├── packages.txt             # Dipendenze di sistema
├── *.csv                    # File dati
└── app/                     # Moduli Python
```

## Troubleshooting Comune

### Errori di Dipendenze
- Verifica che `requirements.txt` contenga tutte le librerie necessarie
- Controlla i log per errori specifici

### Problemi di Memoria
- Streamlit Cloud ha limiti di memoria per app gratuite
- Considera l'upgrade per app più complesse

### File CSV Grandi
- I file CSV sono inclusi nel repository
- Streamlit Cloud ha limiti di dimensione file
- Considera l'uso di database esterni per dataset molto grandi

## Supporto
- [Documentazione Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- [Forum Streamlit](https://discuss.streamlit.io/)
- [GitHub Issues](https://github.com/streamlit/streamlit/issues)
