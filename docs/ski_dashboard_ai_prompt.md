# 🎿 PROMPT ESAUSTIVO PER CURSOR - Dashboard Sciistica Interattiva Pirenei

## 🎯 OBIETTIVO PRINCIPALE
Crea una dashboard interattiva in Python per analizzare stazioni sciistiche dei Pirenei con selezione dinamica di:
- **Data** (anche futura con previsione basata su dati storici)
- **Livello sciistico**: base, medio, esperto
- **Profilo utente**: low-cost, festaiolo, familiare, panoramico (festaiolo ha vista dedicata)

## 📊 DATASET DISPONIBILI

### 1. Infonieve_updated.csv (786KB, 4825 righe)
**Colonne principali:**
- `nome_stazione`, `date`
- `espesormin`, `espesormax` → calcola `espesor_medio = (espesormin + espesormax) / 2`
- `Quota_min`, `Quota_max`
- Piste: `Piste_verdi`, `Piste_blu`, `Piste_rosse`, `Piste_nere`
- Attività: `Area_bambini`, `Slalom`, `Snowpark`, `Area_gare`, `Superpipe`, `Scii_notte`
- Prezzi: `Prezzo_skipass`, `Prezzo_scuola`, `Prezzo_noleggio`
- Altri: `Stelle`, `kmopen`, `kmtotal`, `tipo_neve`, `data_apertura`, `data_chiusura`

### 2. Valanghe_filtered_updated.csv (232KB, 6102 righe)
- `nome_stazione`, `date`, `danger_level_avg` (1-5)

### 3. df_meteo_updated.csv (320KB, 4825 righe)
- `nome_stazione`, `date`, `sole`, `pioggia`, `nebbia`, `vento`, `neve`
- contiene `lat`, `lon` usati per la mappa (merge su `nome_stazione`)

### 4. recensioni_updated.csv (1.2MB)
- `nome_stazione`, `date`
- Parole chiave: `ristoranti`, `coda`, `sicurezza`, `famigliare`, `festaiolo`, `panoramico`, `lowcost`

## 🔮 LOGICA PREVISIONALE PER DATE FUTURE
Se la data selezionata è nel futuro:
1. Trova tutti i dati nei **15 giorni prima e dopo** quella data negli anni precedenti
2. Calcola la **media** di tutti i valori per ogni stazione
3. Usa queste medie come "previsione" per la data futura

**Esempio:** Data selezionata = 2025-12-20
- Considera dati dal 5 dicembre al 4 gennaio di 2022, 2023, 2024
- Calcola media per ogni metrica per ogni stazione

## 🎨 VISUALIZZAZIONI RICHIESTE

### 📍 DASHBOARD BASE (nessun filtro selezionato)

#### 1. Grafico a Barre - Distribuzione Piste per Stazione
```python
# Mostra per ogni stazione: Piste_verdi, Piste_blu, Piste_rosse, Piste_nere
# Barre impilate o raggruppate, ordinate per numero totale piste
```

#### 2. Mappa Interattiva - Stazioni Pirenei
```python
# Centrata sui Pirenei (lat: ~42.5, lon: ~1.5, zoom: 7)
# Marker grandi con tooltip che mostra nome stazione
# Colori diversi per stazioni (es. rosso per stazioni principali)
```

#### 3. Trend Spessore Neve Interattivo
```python
# Grafico a linee con espesor_medio per tutte le stazioni
# Possibilità di cliccare su nome stazione per vedere solo quella
# Include selettore dropdown per stazione specifica
```

#### 4. Pie Chart - Tipo Neve Frequente
```python
# Distribuzione tipo_neve per stazione selezionata
# Dropdown per scegliere stazione
```

#### 5. Date Apertura/Chiusura Media
```python
# Visualizzazione date medie apertura/chiusura per ogni stazione
# Gantt chart o barre orizzontali con date
```

### 🟢 LIVELLO BASE

#### 1. Classifica Migliori Piste Base
```python
# Bar chart con stazioni ordinate per indice_base
# Indice base = f(Piste_verdi, Piste_blu, Quota_min, condizioni_meteo, espesor_medio, Stelle)
```

#### 2. Speedometer Meteo
```python
# Gauge chart che punta all'emoji meteo più frequente:
# 🌞 (sole), 🌧 (pioggia), 🌫 (nebbia), 💨 (vento), ❄ (neve)
# Mostra percentuale condizione più frequente
```

#### 3. Barre Impilate - Piste Verdi/Blu per Impianto
```python
# Barre ordinate dall'impianto migliore al peggiore (per indice_base)
# Ogni barra mostra divisione interna tra piste verdi e blu
```

#### 4. Pie Chart - Qualità Neve per Piste
```python
# Distribuzione tipo_neve per ciascuna pista delle top 3 stazioni
```

### 🟡 LIVELLO MEDIO

#### 1. Classifica Migliori Piste Medio
```python
# Bar chart con stazioni ordinate per indice_medio
# Indice medio = f(Piste_blu, Piste_rosse, condizioni_meteo, espesor_medio, Stelle)
```

#### 2. Speedometer Rischio Valanghe
```python
# Gauge chart con scala 1-5 per danger_level_avg
# Colori: verde (1-2), giallo (3), rosso (4-5)
```

#### 3. Trend Spessore Neve Stazione #1
```python
# Grafico a linee con espesor_medio per la prima stazione in classifica
# Dati dell'anno precedente
```

### 🔴 LIVELLO ESPERTO

#### 1. Classifica Migliori Piste Esperto
```python
# Bar chart con stazioni ordinate per indice_esperto
# Indice esperto = f(Piste_nere, attività_tecniche, espesor_medio, Quota_max, rischio_valanghe, kmtotal)
```

#### 2. Speedometer Rischio Valanghe
```python
# Stesso del livello medio
```

#### 3. Pie Chart - Tipi Piste Tecniche Stazione #1
```python
# Distribuzione per stazione #1: Superpipe, Slalom, Snowpark, Area_gare, etc.
```

#### 4. Bar Chart - Chilometri Totali per Impianto
```python
# Grafico a barre con kmtotal per ciascuna stazione
# Ordinate per chilometri (decrescente)
```

## 🧮 CALCOLO INDICI

### Indice Base
```python
# Normalizza con MinMaxScaler (0-1):
base = normalizza([Piste_verdi, Piste_blu, Quota_min, vento, nebbia, espesor_medio, Stelle])
indice_base = 0.25*base.Piste_verdi + 0.15*base.Piste_blu + 0.05*base.Quota_min + 
              0.05*(1-base.vento) + 0.05*(1-base.nebbia) + 0.20*base.espesor_medio + 0.25*base.Stelle
```

### Indice Medio
```python
medio = normalizza([Piste_blu, Piste_rosse, vento, nebbia, espesor_medio, Stelle])
indice_medio = 0.25*medio.Piste_blu + 0.25*medio.Piste_rosse + 0.05*(1-medio.vento) + 
               0.05*(1-medio.nebbia) + 0.20*medio.espesor_medio + 0.20*medio.Stelle
```

### Indice Esperto
```python
esperto = normalizza([Piste_nere, Slalom, Snowpark, Area_gare, Superpipe, Scii_notte, 
                      espesor_medio, Quota_max, pioggia, danger_level_avg, kmtotal])
indice_esperto = 0.15*esperto.Piste_nere + 0.05*esperto.Slalom + 0.10*esperto.Snowpark + 
                 0.05*esperto.Area_gare + 0.05*esperto.Superpipe + 0.05*esperto.Scii_notte + 
                 0.15*esperto.espesor_medio + 0.10*esperto.Quota_max + 
                 0.05*(1-esperto.pioggia) + 0.15*(1-esperto.danger_level_avg) + 0.10*esperto.kmtotal
```

## 🛠️ TECNOLOGIE RACCOMANDATE

### Librerie Python
```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import pydeck as pdk
from sklearn.preprocessing import MinMaxScaler
import datetime
from datetime import timedelta
```

### Struttura App
```python
# 1. Caricamento e preprocessing dati
# 2. Calcolo indici con normalizzazione
# 3. Logica previsionale per date future
# 4. Sidebar con filtri interattivi
# 5. Visualizzazioni dinamiche basate sui filtri
```

## 🎨 INTERFACCIA UTENTE

### Sidebar
```python
st.sidebar.header("🎯 Personalizza la tua ricerca")
data_sel = st.sidebar.date_input("📅 Seleziona una data", value=datetime.date.today())
livello = st.sidebar.selectbox("⛷️ Livello sciistico", ["nessuno", "base", "medio", "esperto"])
profilo = st.sidebar.selectbox("🧭 Profilo utente", ["nessuno", "panoramico", "familiare", "festaiolo", "lowcost"])
```

### Layout Principale
```python
st.set_page_config(layout="wide", page_title="🎿 Sci su misura - Pirenei")
st.title("🎿 Sci su misura - Dashboard Interattiva Pirenei")

# Layout a colonne per ottimizzare spazio
col1, col2 = st.columns([2, 1])
```

## 📋 CHECKLIST IMPLEMENTAZIONE

- [ ] Caricamento e merge di tutti i 4 dataset
- [ ] Calcolo `espesor_medio` da min/max
- [ ] Implementazione logica previsionale per date future
- [ ] Calcolo indici con MinMaxScaler
- [ ] Dashboard base con 5 visualizzazioni
- [ ] Filtri dinamici per livello sciistico
- [ ] Speedometer per meteo e valanghe
- [ ] Mappa interattiva centrata sui Pirenei
- [ ] Grafici interattivi con Plotly
- [ ] Gestione errori per dati mancanti
- [ ] Ottimizzazione performance con caching

## 🎯 OUTPUT FINALE
Una dashboard Streamlit completa che:
- Cambia dinamicamente in base ai filtri
- Supporta previsioni per date future
- Mostra visualizzazioni specifiche per ogni livello
- È intuitiva e responsive
- Centra l'analisi sui Pirenei
- Fornisce insights personalizzati per sciatori

## 💡 NOTE AGGIUNTIVE
- Il profilo **festaiolo** ha una vista dedicata (grafici sci notturno, snowpark/superpipe, AI overview a tema festa)
- Tutti i grafici devono essere interattivi (hover, zoom, pan)
- La mappa deve essere centrata sui Pirenei con zoom appropriato
- Gestire graziosamente i casi di dati mancanti
- Usare colori coerenti e palette accattivanti per lo sci