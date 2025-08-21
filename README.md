# 🏔️ Pirenei Ski Recommender

Dashboard interattiva per l'analisi delle stazioni sciistiche dei Pirenei con selezione dinamica di data, livello sciistico e profilo utente. **Versione 2** con interfaccia moderna e sistema AI integrato.

## 🚀 Funzionalità Principali

### 🎯 **Sistema di Onboarding Intelligente**
- **Guida Step-by-Step**: Selezione progressiva di data, livello e profilo
- **Tooltip Interattivi**: Suggerimenti contestuali per ogni fase
- **Validazione Dinamica**: Controlli in tempo reale delle selezioni
- **Celebrazione Completamento**: Feedback visivo per l'utente

### 🧠 **AI Overview Integrato**
- **Generazione Automatica**: Riepiloghi personalizzati per ogni stazione
- **Modello Principale**: Mistral AI (Mistral Nemo) via OpenRouter
- **Fallback Intelligenti**: Retry automatico su modelli gratuiti alternativi
- **Cache Intelligente**: Ottimizzazione performance per chiamate AI

### 🎨 **Interfaccia Utente Moderna**
- **Design System Coerente**: Stile tech startup con animazioni fluide
- **Tema Dark/Light**: Supporto automatico per preferenze sistema
- **Responsive Design**: Ottimizzato per mobile e desktop
- **Componenti Reutilizzabili**: KPI cards, podium, hero sections

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

### 🔑 Configurazione AI

Per usare l'overview AI configura la chiave OpenRouter in ambiente prima di lanciare:

```bash
export OPENROUTER_API_KEY="<la_tua_chiave>"
```

**Modello Principale:**
- **Mistral AI**: Mistral Nemo (gratuito via OpenRouter)

**Modelli di Fallback (automatici):**
- **Qwen**: Qwen2.5-32B Instruct
- **Meta**: Llama 3.1-8B Instruct  
- **OpenAI**: GPT-OSS-20B
- **Microsoft**: Phi-3.5 Mini
- **Google**: Gemma-2-9B IT

## 🎯 Utilizzo

### **Onboarding Iniziale**
1. **Seleziona una data** (anche futura per previsioni)
2. **Scegli il livello sciistico**: base, medio, esperto
3. **Definisci il profilo**: panoramico, familiare, festaiolo, lowcost
4. **Completa l'onboarding** per accedere ai risultati

### **Dashboard Interattiva**
- **Esplora le visualizzazioni** che cambiano dinamicamente
- **Interagisci con i grafici** (hover, zoom, pan)
- **Usa l'AI Overview** per riassunti personalizzati
- **Ricomincia l'onboarding** con il pulsante dedicato

## 📊 Calcolo Indici

### Indici Livello (con pesi specifici)

#### **🟢 Indice Base**
```python
# Normalizzazione con MinMaxScaler (0-1) per ogni metrica
base = normalizza([Piste_verdi, Piste_blu, Quota_min, vento, nebbia, espesor_medio, Stelle])

indice_base = 0.25 * base.Piste_verdi      # 25% - Piste verdi (principianti)
                + 0.15 * base.Piste_blu     # 15% - Piste blu (intermedi)
                + 0.05 * base.Quota_min     # 5%  - Quota minima (accessibilità)
                + 0.05 * (1 - base.vento)   # 5%  - Assenza vento (stabilità)
                + 0.05 * (1 - base.nebbia)  # 5%  - Assenza nebbia (visibilità)
                + 0.20 * base.espesor_medio # 20% - Spessore neve (qualità)
                + 0.25 * base.Stelle        # 25% - Rating generale (qualità servizi)
```

#### **🟡 Indice Medio**
```python
medio = normalizza([Piste_blu, Piste_rosse, vento, nebbia, espesor_medio, Stelle])

indice_medio = 0.25 * medio.Piste_blu      # 25% - Piste blu (intermediate)
                + 0.25 * medio.Piste_rosse  # 25% - Piste rosse (avanzate)
                + 0.05 * (1 - medio.vento)  # 5%  - Assenza vento (stabilità)
                + 0.05 * (1 - medio.nebbia) # 5%  - Assenza nebbia (visibilità)
                + 0.20 * medio.espesor_medio # 20% - Spessore neve (qualità)
                + 0.20 * medio.Stelle       # 20% - Rating generale (qualità servizi)
```

#### **🔴 Indice Esperto**
```python
esperto = normalizza([Piste_nere, Slalom, Snowpark, Area_gare, Superpipe, Scii_notte, 
                      espesor_medio, Quota_max, pioggia, danger_level_avg, kmtotal])

indice_esperto = 0.15 * esperto.Piste_nere      # 15% - Piste nere (difficoltà)
                  + 0.05 * esperto.Slalom        # 5%  - Piste slalom (tecnica)
                  + 0.10 * esperto.Snowpark      # 10% - Snowpark (freestyle)
                  + 0.05 * esperto.Area_gare     # 5%  - Area gare (competizione)
                  + 0.05 * esperto.Superpipe     # 5%  - Superpipe (estremo)
                  + 0.05 * esperto.Scii_notte    # 5%  - Sci notturno (esperienza)
                  + 0.15 * esperto.espesor_medio # 15% - Spessore neve (qualità)
                  + 0.10 * esperto.Quota_max     # 10% - Quota massima (dislivello)
                  + 0.05 * (1 - esperto.pioggia) # 5%  - Assenza pioggia (condizioni)
                  + 0.15 * (1 - esperto.danger_level_avg) # 15% - Sicurezza valanghe
                  + 0.10 * esperto.kmtotal       # 10% - Chilometri totali (estensione)
```

### Indici Profilo (con pesi specifici)

#### **🏔️ Profilo Panoramico**
```python
panoramico = normalizza([panoramico, pioggia, vento, nebbia, sole, quota_max])

indice_panoramico = 0.30 * panoramico.panoramico    # 30% - Rating panoramico
                     + 0.15 * (1 - panoramico.pioggia) # 15% - Assenza pioggia
                     + 0.15 * (1 - panoramico.vento)   # 15% - Assenza vento
                     + 0.15 * (1 - panoramico.nebbia)  # 15% - Assenza nebbia
                     + 0.15 * panoramico.sole          # 15% - Presenza sole
                     + 0.10 * (1 - panoramico.quota_max) # 10% - Quota moderata
```

#### **👨‍👩‍👧‍👦 Profilo Familiare**
```python
familiare = normalizza([Piste_verdi, Piste_blu, area_bambini, noleggio, scuola, 
                        sicurezza, ristoranti, familiare, pioggia, nebbia, coda])

indice_familiare = 0.20 * familiare.Piste_verdi     # 20% - Piste verdi (sicurezza)
                    + 0.15 * familiare.Piste_blu      # 15% - Piste blu (intermediate)
                    + 0.15 * familiare.area_bambini   # 15% - Area bambini
                    + 0.10 * (1 - familiare.noleggio) # 10% - Assenza noleggio (semplicità)
                    + 0.10 * (1 - familiare.scuola)   # 10% - Assenza scuola (indipendenza)
                    + 0.10 * familiare.sicurezza      # 10% - Rating sicurezza
                    + 0.10 * familiare.ristoranti     # 10% - Presenza ristoranti
                    + 0.05 * familiare.familiare      # 5%  - Rating familiare
                    + 0.03 * (1 - familiare.pioggia)  # 3%  - Assenza pioggia
                    + 0.01 * (1 - familiare.nebbia)   # 1%  - Assenza nebbia
                    + 0.01 * (1 - familiare.coda)     # 1%  - Assenza code
```

#### **🎉 Profilo Festaiolo**
```python
festaiolo = normalizza([snowpark, Scii_notte, ristoranti, Stelle, festaiolo, pioggia])

indice_festaiolo = 0.25 * festaiolo.snowpark         # 25% - Snowpark (divertimento)
                    + 0.20 * festaiolo.Scii_notte      # 20% - Sci notturno (vita notturna)
                    + 0.20 * festaiolo.ristoranti      # 20% - Presenza ristoranti
                    + 0.20 * festaiolo.Stelle          # 20% - Rating generale (qualità)
                    + 0.10 * festaiolo.festaiolo       # 10% - Rating festaiolo
                    + 0.05 * (1 - festaiolo.pioggia)   # 5%  - Assenza pioggia
```

#### **💰 Profilo Lowcost**
```python
lowcost = normalizza([lowcost, skipass, scuola, noleggio, kmopen])

indice_lowcost = 0.35 * lowcost.lowcost              # 35% - Rating convenienza
                  + 0.25 * (1 - lowcost.skipass)       # 25% - Prezzo skipass contenuto
                  + 0.20 * (1 - lowcost.scuola)        # 20% - Assenza scuola (risparmio)
                  + 0.15 * (1 - lowcost.noleggio)      # 15% - Assenza noleggio (risparmio)
                  + 0.05 * lowcost.kmopen              # 5%  - Chilometri aperti (valore)
```

### 🔍 **Note sui Pesi**

- **Pesi maggiori (20-35%)**: Caratteristiche principali del profilo
- **Pesi medi (10-15%)**: Caratteristiche secondarie importanti
- **Pesi minori (1-5%)**: Caratteristiche di supporto o bonus
- **Normalizzazione**: Tutti i valori vengono normalizzati tra 0 e 1 prima del calcolo
- **Inversione**: Per metriche negative (vento, nebbia, pioggia) si usa `(1 - valore)` per convertire in positivo

## 🎨 Tecnologie Utilizzate

- **Streamlit**: Interfaccia web moderna
- **Pandas**: Manipolazione dati ottimizzata
- **Plotly**: Grafici interattivi avanzati
- **PyDeck**: Mappe interattive 3D
- **Scikit-learn**: Normalizzazione dati e ML
- **OpenRouter**: Integrazione AI con Mistral AI e modelli gratuiti
- **CSS Moderno**: Design system con variabili CSS e animazioni

## 🚀 Performance e Ottimizzazioni

### **Caching Intelligente**
- **Cache dati**: 30 minuti per dataset principali
- **Cache LLM**: 1 ora per chiamate AI
- **Cache template**: Permanente per componenti HTML/CSS

### **Lazy Loading**
- **Import dinamici**: Plotly e PyDeck caricati solo quando necessari
- **Componenti condizionali**: UI mostrata solo quando richiesta
- **Ottimizzazione grafici**: Template Plotly unificati e ottimizzati

## 📝 Note

- Tutti i grafici sono **interattivi** e responsive
- Mappa **centrata sui Pirenei** con zoom ottimizzato
- Giorni chiusi: tabella con aperture/chiusure medie per stazione (regola 5/5)
- **Sistema di onboarding** per utenti principianti
- **AI Overview** per spiegazioni personalizzate
- **Design moderno** ispirato alle migliori startup tech

## 🎿 Buon divertimento!

La dashboard è progettata per fornire insights personalizzati per sciatori di tutti i livelli, aiutando nella scelta della destinazione ideale per le vacanze sulla neve. Con l'interfaccia moderna e l'intelligenza artificiale integrata, ogni utente può trovare la stazione perfetta per le proprie esigenze. 