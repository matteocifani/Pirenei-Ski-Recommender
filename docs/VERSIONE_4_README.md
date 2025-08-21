# 🚀 Versione 4 - Pirenei Ski Recommender

## 📋 Panoramica Aggiornamento

La **Versione 4** introduce un sistema di onboarding completo, un'interfaccia utente completamente ridisegnata e l'integrazione avanzata con modelli AI per fornire raccomandazioni personalizzate e intelligenti.

## ✨ Nuove Funzionalità Principali

### 🎯 **Sistema di Onboarding Intelligente**

#### **Flusso Step-by-Step**
1. **Selezione Data** 📅
   - Calendario intuitivo con validazione
   - Supporto per date future con previsioni
   - Tooltip contestuali per guidare l'utente

2. **Definizione Livello** 🎿
   - Base: Principianti e famiglie
   - Medio: Sciatori intermedi
   - Esperto: Sciatori avanzati e professionisti

3. **Profilo Utente** 👥
   - Panoramico: Focus su vista e paesaggi
   - Familiare: Servizi per famiglie e bambini
   - Festaiolo: Vita notturna e divertimento
   - Lowcost: Budget-friendly e convenienza

#### **Caratteristiche Onboarding**
- **Validazione Dinamica**: Controlli in tempo reale
- **Tooltip Interattivi**: Suggerimenti contestuali per ogni fase
- **Celebrazione Completamento**: Feedback visivo per l'utente
- **Pulsante Ricomincia**: Possibilità di riavviare il processo

### 🧠 **AI Overview Integrato**

#### **Sistema Multi-Provider**
- **Mistral AI**: Mistral Nemo (modello principale)
- **Qwen**: Qwen2.5-32B Instruct (fallback)
- **Meta**: Llama 3.1-8B Instruct (fallback)
- **OpenAI**: GPT-OSS-20B (fallback)
- **Microsoft**: Phi-3.5 Mini (fallback)
- **Google**: Gemma-2-9B IT (fallback)

#### **Prompt Specializzati**
- **Prompt Generico**: Overview generale per ogni stazione
- **Prompt Festaiolo**: Focus su vita notturna e divertimento
- **Prompt Familiare**: Enfasi su servizi per famiglie
- **Prompt Lowcost**: Analisi costi e convenienza

#### **Ottimizzazioni Performance**
- **Cache Intelligente**: 1 ora per chiamate AI
- **Lazy Loading**: Import dinamici per ridurre startup time
- **Prompt Caching**: Evita ripetizioni costose

### 🎨 **Interfaccia Utente Completamente Ridisegnata**

#### **Design System Moderno**
- **Stile Tech Startup**: Ispirato a Prospinity, Airbnb, Apple
- **Gradient e Glassmorphism**: Effetti visivi moderni
- **Animazioni Fluide**: Transizioni CSS ottimizzate
- **Tema Dark/Light**: Supporto automatico per preferenze sistema

#### **Componenti UI Avanzati**
- **Hero Header**: Titolo principale con animazioni
- **KPI Cards**: Metriche chiave con design moderno
- **Podium System**: Classifica top 3 con stile olimpico
- **AI Dock**: Pannello flottante per controlli AI
- **Floating Controls**: Barra di controllo moderna e responsive

#### **Responsive Design**
- **Mobile-First**: Ottimizzato per dispositivi mobili
- **CSS Grid**: Layout flessibili e adattivi
- **Breakpoints Intelligenti**: Adattamento automatico per tutti i dispositivi

## 🔧 Miglioramenti Tecnici

### **Performance e Ottimizzazioni**
- **Caching Strategico**: 
  - Dati: 30 minuti
  - LLM: 1 ora
  - Template: Permanente
- **Lazy Loading**: Import condizionali per librerie pesanti
- **Componenti Condizionali**: UI mostrata solo quando necessaria

### **Gestione Dati**
- **Preprocessing Ottimizzato**: Operazioni vectorizzate per dataset grandi
- **Merge Intelligente**: Gestione automatica di coordinate e metadati
- **Fallback Robusto**: Gestione graziosa di dati mancanti

### **Integrazione AI**
- **OpenRouter API**: Accesso unificato a modelli multipli
- **Prompt Engineering**: Contesti specializzati per ogni profilo
- **Error Handling**: Gestione robusta di fallimenti AI

## 📊 Dashboard e Visualizzazioni

### **Visualizzazioni Base**
- **Grafici a Barre**: Distribuzione piste per tipologia e stazione
- **Mappe Interattive**: Centrate sui Pirenei con PyDeck
- **Trend Temporali**: Spessore neve e condizioni meteo
- **Tabelle Dinamiche**: Date apertura/chiusura medie

### **Visualizzazioni per Livello**
- **Base**: Focus su piste verdi/blu e sicurezza
- **Medio**: Enfasi su piste blu/rosse e meteo
- **Esperto**: Piste nere, strutture tecniche e performance

### **Visualizzazioni per Profilo**
- **Panoramico**: Condizioni meteo e vista
- **Familiare**: Servizi e sicurezza
- **Festaiolo**: Vita notturna e divertimento
- **Lowcost**: Costi e convenienza

## 🧮 **Calcolo Indici Dettagliato**

### **Indici Livello (con pesi specifici)**

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

### **Indici Profilo (con pesi specifici)**

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

## 🚀 Guida all'Installazione

### **Requisiti di Sistema**
- Python 3.8+
- 4GB RAM minimo
- Connessione internet per modelli AI

### **Installazione Dipendenze**
```bash
pip install -r requirements.txt
```

### **Configurazione AI**
```bash
export OPENROUTER_API_KEY="<la_tua_chiave>"
```

### **Avvio Applicazione**
```bash
streamlit run streamlit_app_v2.py
```

## 📱 Utilizzo e Navigazione

### **Primo Avvio**
1. **Completa l'Onboarding**: Segui la guida step-by-step
2. **Seleziona Preferenze**: Data, livello e profilo
3. **Esplora i Risultati**: Dashboard personalizzata per le tue scelte

### **Navigazione Principale**
- **Onboarding**: Guida iniziale per nuovi utenti
- **Dashboard**: Visualizzazioni principali e metriche
- **AI Overview**: Riepiloghi personalizzati generati da AI
- **Controlli**: Modifica preferenze e ricomincia

### **Funzionalità Avanzate**
- **Ricomincia Onboarding**: Pulsante dedicato per riavviare
- **Cache Management**: Ottimizzazioni automatiche per performance
- **Responsive Design**: Adattamento automatico per tutti i dispositivi

## 🎯 Roadmap e Sviluppi Futuri

### **Versione 4.1** (Prossima)
- [ ] Supporto per più lingue (IT, EN, ES, FR)
- [ ] Integrazione con API meteo in tempo reale
- [ ] Sistema di notifiche per condizioni ideali

### **Versione 4.2** (Media)
- [ ] App mobile nativa (iOS/Android)
- [ ] Integrazione con dispositivi IoT per neve
- [ ] Sistema di social sharing e recensioni

### **Versione 5.0** (Lunga)
- [ ] Machine Learning avanzato per previsioni
- [ ] Integrazione con sistemi di prenotazione
- [ ] Realtà aumentata per mappe resort

## 🐛 Risoluzione Problemi

### **Problemi Comuni**
1. **AI non funziona**: Verifica la chiave API OpenRouter
2. **App lenta**: Controlla la connessione internet e la RAM disponibile
3. **Grafici non si caricano**: Aggiorna le dipendenze con `pip install -r requirements.txt`

### **Supporto Tecnico**
- **Documentazione**: Consulta i file README nella cartella docs/
- **Issues**: Segnala problemi su GitHub
- **Performance**: Usa il sistema di caching integrato

## 📚 Risorse e Riferimenti

### **Documentazione**
- `README.md`: Guida principale
- `docs/MODERN_UI_README.md`: Sistema di design
- `docs/ski_dashboard_ai_prompt.md`: Specifiche AI

### **Tecnologie**
- **Streamlit**: Framework web principale
- **Plotly**: Grafici interattivi
- **PyDeck**: Mappe 3D
- **OpenRouter**: API AI con Mistral AI e modelli gratuiti

### **Design Inspiration**
- **Prospinity**: Clean startup design
- **Airbnb**: User experience
- **Apple**: Minimalismo e eleganza
- **Google**: Material Design
- **OpenAI**: Futuristico e accessibile

---

**Versione 4** - Pirenei Ski Recommender  
*Built with ❤️ using modern AI and beautiful design*
