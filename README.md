# 🎿 Sci su misura - Dashboard Interattiva Pirenei

Dashboard interattiva per l'analisi delle stazioni sciistiche dei Pirenei con selezione dinamica di data, livello sciistico e profilo utente.

## 🚀 Funzionalità

### 📊 Dashboard Generale (nessun livello selezionato)
- **Grafico a barre (stacked)**: Piste per tipologia (verde, blu, rossa, nera) con colori coerenti e ordinamento per impianti con più piste aperte
- **Mappa interattiva**: Stazioni centrata sui Pirenei
- **Trend spessore neve**: Colori diversi per impianto, selettore per evidenziare/filtrare un impianto
- **Date apertura/chiusura**: Tabella con medie per stazione, calcolate su tutti gli anni usando regola 5/5 su `idestado` (o `kmopen`)

### 🟢 Livello Base
- **Classifica**: Stazioni ordinate per indice base
- **Speedometer meteo**: Condizioni prevalenti
- **Barre impilate**: Piste verdi e blu per impianto

### 🟡 Livello Medio
- **Classifica**: Stazioni ordinate per indice medio
- **Trend spessore**: Stazione #1 anno precedente
- **Mappa interattiva**: evidenziazione consigliata

### 🔴 Livello Esperto
- **Classifica**: Stazioni ordinate per indice esperto
- **Radar**: Strutture tecniche stazione #1
- **Bar chart**: Chilometri totali
- **Mappa interattiva**: evidenziazione consigliata

## 🔮 Previsioni per Date Future

L'applicazione supporta la selezione di date future utilizzando dati storici:
- Considera i **15 giorni prima e dopo** la data selezionata
- Calcola le **medie** sui dati degli anni precedenti
- Fornisce stime previsionali basate su trend storici

## 📁 File Richiesti

Assicurati di avere nella stessa cartella dell'applicazione:
- `Infonieve_updated.csv`
- `Valanghe_filtered_updated.csv`
- `df_meteo_updated.csv`
- `recensioni_updated.csv`

## 🛠️ Installazione

1. **Clona o scarica i file** in una cartella
2. **Installa le dipendenze**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Esecuzione (Versione 2)

Avvia la versione v2 (snella, con effetti grafici moderni e overview AI):

```bash
streamlit run streamlit_app_v2.py
```

Per usare l'overview AI configura la chiave OpenRouter in ambiente prima di lanciare:

```bash
export OPENROUTER_API_KEY="<la_tua_chiave>"
```

## 🎯 Utilizzo

1. **Seleziona una data** nella sidebar (anche futura per previsioni)
2. **Scegli il livello sciistico**: nessuno, base, medio, esperto
3. **Esplora le visualizzazioni** che cambiano dinamicamente
4. **Interagisci con i grafici** (hover, zoom, pan)

## 📊 Calcolo Indici

### Indici Livello (semplificato)
- **Base**: verdi, blu, quota_min, meteo (−vento/−nebbia), spessore medio, stelle
- **Medio**: blu, rosse, meteo (−vento/−nebbia), spessore medio, stelle
- **Esperto**: nere, strutture tecniche (slalom/snowpark/…), quota_max, (−pioggia), (−valanghe), km totali

### Indici Profilo (usati per ranking e viste dedicate se selezionati)
- **Familiare**: verdi/blu, area_bambini, (−noleggio/−scuola), sicurezza, ristoranti, familiare, (−pioggia/−nebbia/−code)
- **Festaiolo**: snowpark, sci notturno, ristoranti, stelle, festaiolo, (−pioggia) + vista dedicata con grafici e AI overview
- **Panoramico**: panoramico, (−pioggia/−vento/−nebbia), sole, (−quota_max)
- **Lowcost**: lowcost, (−skipass/−scuola/−noleggio), km aperti

## 🎨 Tecnologie Utilizzate

- **Streamlit**: Interfaccia web
- **Pandas**: Manipolazione dati
- **Plotly**: Grafici interattivi
- **PyDeck**: Mappe interattive
- **Scikit-learn**: Normalizzazione dati

## 📝 Note

- Tutti i grafici sono **interattivi** e responsive
- Mappa **centrata sui Pirenei** con zoom ottimizzato
- Giorni chiusi: tabella con aperture/chiusure medie per stazione (regola 5/5)

## 🎿 Buon divertimento!

La dashboard è progettata per fornire insights personalizzati per sciatori di tutti i livelli, aiutando nella scelta della destinazione ideale per le vacanze sulla neve. 