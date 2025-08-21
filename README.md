# 🎿 Sci su misura - Dashboard Interattiva Pirenei

Dashboard interattiva per l'analisi delle stazioni sciistiche dei Pirenei con selezione dinamica di data, livello sciistico e profilo utente. **Versione 2** con interfaccia moderna e sistema AI integrato.

## 🚀 Funzionalità Principali

### 🎯 **Sistema di Onboarding Intelligente**
- **Guida Step-by-Step**: Selezione progressiva di data, livello e profilo
- **Tooltip Interattivi**: Suggerimenti contestuali per ogni fase
- **Validazione Dinamica**: Controlli in tempo reale delle selezioni
- **Celebrazione Completamento**: Feedback visivo per l'utente

### 🧠 **AI Overview Integrato**
- **Generazione Automatica**: Riepiloghi personalizzati per ogni stazione
- **Modelli Multi-Provider**: Supporto per OpenAI, Mistral AI, Anthropic
- **Prompt Specializzati**: Contesti specifici per ogni profilo utente
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

**Provider Supportati:**
- OpenAI (GPT-4, GPT-3.5)
- Mistral AI (Mistral, Nemo)
- Anthropic (Claude)
- Google (Gemini)
- Meta (Llama)

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

- **Streamlit**: Interfaccia web moderna
- **Pandas**: Manipolazione dati ottimizzata
- **Plotly**: Grafici interattivi avanzati
- **PyDeck**: Mappe interattive 3D
- **Scikit-learn**: Normalizzazione dati e ML
- **OpenRouter**: Integrazione AI multi-provider
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