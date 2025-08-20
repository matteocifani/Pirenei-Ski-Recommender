import datetime
import os
from typing import List, Tuple

import numpy as np
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

from app.data_loader import load_datasets
from app.prediction import compute_indices, get_historical_data_for_date
from app.scoring import apply_profile_adjustment, build_ranking
from app.llm import generate_overview
from app.config import DEFAULT_LLM_MODEL
from app.config import SUPPORTED_PROFILES


def format_date_for_display(d):
    """Formatta la data in italiano per la visualizzazione"""
    mesi = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
    return f"{d.day} {mesi[d.month-1]} {d.year}"


def render_kpi(label, value, suffix=None, icon="📊"):
    """Rende una card KPI moderna con design tech"""
    suffix_html = f" {suffix}" if suffix else ""
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}{suffix_html}</div>
    </div>"""


def parse_model_name(model_name: str | None) -> str:
    """Converte il nome del modello in formato user-friendly.
    
    Esempi:
    - mistralai/mistral-nemo:free -> Mistral AI (Nemo Free)
    - openai/gpt-4 -> OpenAI (GPT-4)
    - None -> AI
    """
    if not model_name or not str(model_name).strip():
        return "AI"
    
    model_str = str(model_name).strip()
    
    # Mapping dei provider
    provider_map = {
        "mistralai": "Mistral AI",
        "openai": "OpenAI", 
        "anthropic": "Anthropic",
        "google": "Google",
        "meta-llama": "Meta",
        "microsoft": "Microsoft"
    }
    
    try:
        # Parse formato: provider/model:variant
        if "/" in model_str:
            provider_part, model_part = model_str.split("/", 1)
            provider_name = provider_map.get(provider_part, provider_part.title())
            
            if ":" in model_part:
                model_base, variant = model_part.split(":", 1)
                model_display = model_base.replace("-", " ").title()
                variant_display = variant.replace("-", " ").title()
                return f"{provider_name} ({model_display} {variant_display})"
            else:
                model_display = model_part.replace("-", " ").title()
                return f"{provider_name} ({model_display})"
        else:
            return model_str.title()
    except:
        return model_str







def render_podium(top3):
    """Rende il podio moderno stile tech"""
    if len(top3) < 3:
        return ""
    
    names = top3["nome_stazione"].tolist()
    first = names[0] if len(names) > 0 else ""
    second = names[1] if len(names) > 1 else ""
    third = names[2] if len(names) > 2 else ""
    
    return f"""
    <div class='podium-container'>
      <div class='podium-step second'>
        <div class='podium-platform second'>
          <div class='podium-rank'>2</div>
          <div class='podium-medal'>🥈</div>
          <div class='podium-name'>{second}</div>
        </div>
      </div>
      <div class='podium-step first'>
        <div class='podium-platform first'>
          <div class='podium-rank'>1</div>
          <div class='podium-medal'>🥇</div>
          <div class='podium-name'>{first}</div>
        </div>
      </div>
      <div class='podium-step third'>
        <div class='podium-platform third'>
          <div class='podium-rank'>3</div>
          <div class='podium-medal'>🥉</div>
          <div class='podium-name'>{third}</div>
        </div>
      </div>
    </div>"""


def render_ai_dock(is_loading=False, model_name=None, has_api_key=True):
    """Rende il pannello flottante AI dock"""
    status = "Generazione in corso..." if is_loading else "AI pronta"
    model_display = model_name if model_name else "Default Model"
    disabled_class = "is-disabled" if not has_api_key else ""
    
    return f"""
    <div class="ai-dock">
        <div class="ai-dock-left">
            <span class="ai-status">{status}</span>
        </div>
        <div class="ai-dock-center">
            <button class="ai-icon-button" title="Voice mode (coming soon)">🗣️</button>
            <button class="ai-icon-button" title="Genera riepilogo">🧠</button>
            <button class="ai-icon-button" title="Condividi (coming soon)">🔗</button>
        </div>
        <div class="ai-dock-right">
            <select class="ai-model-select" disabled>
                <option>{model_display}</option>
            </select>
            <button class="ai-run-button {disabled_class}" title="Esegui" {'disabled' if not has_api_key else ''}>▶️</button>
        </div>
    </div>"""


st.set_page_config(layout="wide", page_title="🎿 Sci su misura v2 - Pirenei", page_icon="🎿")

# Modern Tech Startup Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* Modern Design System - Tech Startup Inspired */
:root {
    /* Spacing System */
    --space-2: 0.125rem;
    --space-4: 0.25rem;
    --space-6: 0.375rem;
    --space-8: 0.5rem;
    --space-12: 0.75rem;
    --space-16: 1rem;
    --space-20: 1.25rem;
    --space-24: 1.5rem;
    --space-32: 2rem;
    --space-40: 2.5rem;
    --space-48: 3rem;
    --space-64: 4rem;
    --space-80: 5rem;
    
    /* Border Radius */
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-2xl: 1.5rem;
    --radius-3xl: 2rem;
    --radius-full: 9999px;
    
    /* Shadows - Apple/Modern inspired */
    --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    --shadow-glow: 0 0 0 1px rgba(59, 130, 246, 0.1), 0 0 20px rgba(59, 130, 246, 0.15);
    --shadow-ai-glow: 0 0 0 1px rgba(139, 92, 246, 0.2), 0 0 30px rgba(139, 92, 246, 0.1);
    
    /* Color Palette - Tech/Startup inspired */
    --white: #ffffff;
    --gray-25: #fcfcfd;
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-400: #9ca3af;
    --gray-500: #6b7280;
    --gray-600: #4b5563;
    --gray-700: #374151;
    --gray-800: #1f2937;
    --gray-900: #111827;
    --gray-950: #030712;
    
    /* Brand Colors */
    --primary-50: #eff6ff;
    --primary-100: #dbeafe;
    --primary-500: #3b82f6;
    --primary-600: #2563eb;
    --primary-700: #1d4ed8;
    --primary-900: #1e3a8a;
    
    --purple-50: #faf5ff;
    --purple-100: #f3e8ff;
    --purple-500: #8b5cf6;
    --purple-600: #7c3aed;
    --purple-700: #6d28d9;
    
    --emerald-50: #ecfdf5;
    --emerald-100: #d1fae5;
    --emerald-500: #10b981;
    --emerald-600: #059669;
    
    --amber-50: #fffbeb;
    --amber-100: #fef3c7;
    --amber-500: #f59e0b;
    --amber-600: #d97706;
    
    --red-50: #fef2f2;
    --red-100: #fee2e2;
    --red-500: #ef4444;
    --red-600: #dc2626;
    
    /* Semantic Colors - Dark Theme */
    --bg-primary: var(--gray-950);
    --bg-secondary: var(--gray-900);
    --bg-tertiary: var(--gray-800);
    --bg-card: var(--gray-900);
    --bg-overlay: rgba(15, 23, 42, 0.9);
    --bg-glass: rgba(15, 23, 42, 0.1);
    
    --text-primary: var(--gray-50);
    --text-secondary: var(--gray-300);
    --text-tertiary: var(--gray-400);
    --text-inverse: var(--gray-900);
    
    --border-primary: var(--gray-800);
    --border-secondary: var(--gray-700);
    --border-focus: var(--emerald-500);
    
    /* Gradients - Dark Theme */
    --gradient-primary: linear-gradient(135deg, var(--emerald-500), var(--purple-600));
    --gradient-secondary: linear-gradient(135deg, var(--purple-600), var(--emerald-500));
    --gradient-success: linear-gradient(135deg, var(--emerald-500), var(--emerald-600));
    --gradient-glass: linear-gradient(135deg, rgba(15, 23, 42, 0.3), rgba(15, 23, 42, 0.1));
    
    /* Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 500ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Global Reset & Typography */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}



html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Streamlit Specific Overrides */
.main .block-container {
    padding-top: var(--space-24) !important;
    padding-bottom: 8rem !important;
    max-width: 1400px !important;
    padding-left: var(--space-32) !important;
    padding-right: var(--space-32) !important;
}

.stApp {
    background: var(--bg-primary) !important;
}

/* Remove Streamlit default margins */
.stMarkdown {
    margin-bottom: 0 !important;
}

/* HERO HEADER - Capolavoro di Web Design */
.app-header {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    position: relative;
    overflow: hidden;
    background: radial-gradient(ellipse at center, rgba(139, 92, 246, 0.03) 0%, rgba(59, 130, 246, 0.02) 50%, transparent 100%);
    padding: var(--space-64) var(--space-32);
    margin: calc(-1 * var(--space-32)) calc(-1 * var(--space-32)) var(--space-64) calc(-1 * var(--space-32));
    width: calc(100% + 2 * var(--space-32));
    border-radius: 48px;
    box-shadow: 
        0 0 60px rgba(139, 92, 246, 0.1),
        0 0 120px rgba(59, 130, 246, 0.05),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    transition: all var(--transition-slow);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}

/* Organic Background Movement - Ultra sottile */
.app-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    right: -50%;
    bottom: -50%;
    background: 
        radial-gradient(ellipse 80% 60% at 30% 40%, rgba(139, 92, 246, 0.015) 0%, transparent 60%),
        radial-gradient(ellipse 70% 80% at 70% 60%, rgba(6, 182, 212, 0.012) 0%, transparent 65%),
        radial-gradient(ellipse 90% 50% at 50% 80%, rgba(245, 158, 11, 0.008) 0%, transparent 70%),
        radial-gradient(ellipse 60% 90% at 20% 20%, rgba(239, 246, 255, 0.005) 0%, transparent 75%);
    animation: organicFlow 30s ease-in-out infinite;
    z-index: 1;
    filter: blur(3px);
    border-radius: 60px;
}

/* Organic flowing animation - no geometric shapes */
@keyframes organicFlow {
    0% { 
        transform: translate(0%, 0%) scale(1);
        opacity: 0.3;
    }
    25% { 
        transform: translate(2%, -1%) scale(1.05);
        opacity: 0.5;
    }
    50% { 
        transform: translate(-1%, 2%) scale(0.98);
        opacity: 0.4;
    }
    75% { 
        transform: translate(-2%, -1%) scale(1.02);
        opacity: 0.6;
    }
    100% { 
        transform: translate(0%, 0%) scale(1);
        opacity: 0.3;
    }
}

.app-title {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-weight: 900;
    font-size: clamp(3.5rem, 8vw, 7rem);
    text-align: center;
    margin: 0;
    letter-spacing: -0.06em;
    line-height: 0.9;
    position: relative;
    z-index: 2;
    
    /* Gradient text animato - solo colori vivaci senza bianco */
    background: linear-gradient(
        45deg,
        #06b6d4 0%,      /* Azzurro */
        #8b5cf6 25%,     /* Viola */
        #ec4899 50%,     /* Magenta */
        #f59e0b 75%,     /* Giallo/Arancione */
        #06b6d4 100%     /* Azzurro (chiude il ciclo) */
    );
    background-size: 400% 400%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShimmer 8s ease-in-out infinite;
    
    /* Glow effect */
    filter: drop-shadow(0 0 40px rgba(139, 92, 246, 0.3))
            drop-shadow(0 0 80px rgba(59, 130, 246, 0.2));
}

@keyframes gradientShimmer {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}

.app-subtitle {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: clamp(1.2rem, 3vw, 1.8rem);
    font-weight: 500;
    margin-top: var(--space-24);
    text-align: center;
    letter-spacing: 0.02em;
    line-height: 1.4;
    position: relative;
    z-index: 2;
    
    /* Gradient subtitle */
    background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 50%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    
    /* Typing animation */
    opacity: 0;
    animation: fadeInUp 1.5s ease-out 0.5s forwards;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Floating scroll indicator */
.app-header::after {
    content: '↓';
    position: absolute;
    bottom: var(--space-32);
    left: 50%;
    transform: translateX(-50%);
    font-size: 2rem;
    color: rgba(148, 163, 184, 0.6);
    animation: bounce 2s infinite;
    z-index: 2;
}

@keyframes bounce {
    0%, 20%, 50%, 80%, 100% {
        transform: translateX(-50%) translateY(0);
    }
    40% {
        transform: translateX(-50%) translateY(-10px);
    }
    60% {
        transform: translateX(-50%) translateY(-5px);
    }
}

/* Magic sparkles */
.app-title::before {
    content: '✨';
    position: absolute;
    top: -20px;
    left: -30px;
    font-size: 1.5rem;
    animation: sparkleRotate 4s ease-in-out infinite;
    z-index: 3;
}

.app-title::after {
    content: '⭐';
    position: absolute;
    bottom: -20px;
    right: -30px;
    font-size: 1.2rem;
    animation: sparkleRotate 6s ease-in-out infinite reverse;
    z-index: 3;
}

@keyframes sparkleRotate {
    0%, 100% { 
        transform: rotate(0deg) scale(1);
        opacity: 0.7;
    }
    50% { 
        transform: rotate(180deg) scale(1.2);
        opacity: 1;
    }
}

.section-header {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.875rem;
    color: var(--text-primary);
    margin: var(--space-48) 0 var(--space-24) 0;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

.section-subtitle {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1.25rem;
    color: var(--text-secondary);
    margin: var(--space-32) 0 var(--space-16) 0;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: var(--space-8);
}

/* Profile Section Styles */
.profile-main-title {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: 2.5rem;
    color: var(--text-primary);
    margin: var(--space-32) 0 var(--space-24) 0;
    letter-spacing: -0.03em;
    line-height: 1.1;
    text-align: center;
    background: linear-gradient(135deg, var(--purple-500), var(--emerald-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.profile-divider {
    border: none;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--emerald-500), transparent);
    margin: var(--space-48) 0;
    opacity: 0.6;
}

.profile-section-title {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 2rem;
    color: var(--text-primary);
    margin: var(--space-24) 0 var(--space-32) 0;
    letter-spacing: -0.02em;
    line-height: 1.2;
    text-align: center;
    background: linear-gradient(135deg, var(--emerald-400), var(--emerald-300));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Hero Container */
.hero-container {
    position: relative;
    margin: var(--space-20) 0 var(--space-32) 0;
    width: 100%;
}

/* Hero Section - Elegant Redesign */
.hero-section {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: var(--radius-3xl);
    padding: var(--space-40) var(--space-32);
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 
        0 0 0 1px rgba(148, 163, 184, 0.1),
        0 0 20px rgba(100, 116, 139, 0.15),
        0 0 40px rgba(71, 85, 105, 0.1),
        0 25px 50px -12px rgba(0, 0, 0, 0.6);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    backdrop-filter: blur(20px);
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(148, 163, 184, 0.05), transparent, rgba(203, 213, 225, 0.05), transparent);
    animation: heroRotate 12s linear infinite;
    z-index: -1;
}

.hero-section::after {
    content: '';
    position: absolute;
    inset: 1px;
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
    border-radius: calc(var(--radius-3xl) - 1px);
    z-index: -1;
}

@keyframes heroRotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.hero-section:hover {
    transform: translateY(-4px) scale(1.01);
    box-shadow: 
        0 0 0 1px rgba(148, 163, 184, 0.2),
        0 0 30px rgba(100, 116, 139, 0.2),
        0 0 60px rgba(71, 85, 105, 0.15),
        0 30px 60px -15px rgba(0, 0, 0, 0.8);
    border-color: rgba(148, 163, 184, 0.3);
}

/* Removed frosted label styles - no longer needed */

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-8);
    background: var(--emerald-950);
    color: var(--emerald-300);
    font-family: 'Inter', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    padding: var(--space-8) var(--space-16);
    border-radius: var(--radius-full);
    margin-bottom: var(--space-12);
    border: 1px solid var(--emerald-800);
    position: relative;
    z-index: 1;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-3px); }
}

.hero-title {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    font-size: clamp(2.5rem, 6vw, 4rem);
    margin: 0;
    letter-spacing: -0.02em;
    line-height: 0.9;
    background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 50%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    z-index: 2;
    filter: drop-shadow(0 0 15px rgba(148, 163, 184, 0.3));
}

@keyframes gradientShift {
    0%, 100% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
}



@keyframes sparkle {
    0%, 100% { 
        transform: scale(1) rotate(0deg);
        opacity: 0.7;
    }
    50% { 
        transform: scale(1.2) rotate(180deg);
        opacity: 1;
    }
}

.hero-subtitle {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1.3rem;
    background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 var(--space-16) 0;
    letter-spacing: 0.01em;
    line-height: 1.4;
    position: relative;
    z-index: 2;
    opacity: 0.95;
}

/* KPI Cards - Modern Design */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-24);
    margin: var(--space-32) 0;
}

.kpi-grid.grid-3 {
    grid-template-columns: repeat(3, 1fr);
}

.kpi-grid.grid-4 {
    grid-template-columns: repeat(4, 1fr);
}

.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-2xl);
    padding: var(--space-32) var(--space-24);
    text-align: center;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-200);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.kpi-card:hover::before {
    opacity: 1;
}

.kpi-icon {
    width: 48px;
    height: 48px;
    margin: 0 auto var(--space-16) auto;
    background: var(--emerald-950);
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: var(--emerald-400);
}

.kpi-label {
    font-family: 'Inter', sans-serif;
    color: var(--text-secondary) !important;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: var(--space-8);
}

.kpi-value {
    font-family: 'Inter', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary) !important;
    margin: var(--space-8) 0;
    letter-spacing: -0.02em;
    line-height: 1;
}

.kpi-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-tertiary);
    margin-top: var(--space-4);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* AI Overview Section - Modern with Glow */
.ai-overview-section {
    background: var(--bg-card);
    border: 1px solid var(--purple-200);
    border-radius: var(--radius-2xl);
    padding: var(--space-32);
    margin: var(--space-32) 0;
    position: relative;
    overflow: hidden;
    /* Glow ridotto per un effetto più sottile */
    box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.3), 0 0 30px rgba(139, 92, 246, 0.15), 0 0 60px rgba(139, 92, 246, 0.08), var(--shadow-xl);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: all var(--transition-normal);
}

.ai-overview-section:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 0 1px rgba(139, 92, 246, 0.4), 0 0 40px rgba(139, 92, 246, 0.2), 0 0 80px rgba(139, 92, 246, 0.1), var(--shadow-xl);
}



.ai-header {
    display: flex;
    align-items: flex-start;
    gap: var(--space-12);
    margin-bottom: var(--space-20);
    justify-content: flex-start;
}



.ai-header-text {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    gap: var(--space-6);
    width: 100%;
}

.ai-title {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.125rem;
    color: var(--text-primary);
    margin: 0;
}

.ai-badge {
    background: var(--purple-950);
    color: var(--purple-300);
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    padding: var(--space-4) var(--space-8);
    border-radius: var(--radius-full);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border: 1px solid var(--purple-800);
    margin: 0;
    align-self: flex-start;
    margin-left: 0;
}

.ai-overview-content {
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
    line-height: 1.7;
    font-size: 1rem;
    font-weight: 400;
    letter-spacing: -0.01em;
}

/* Modern Podium - Apple/Tech Inspired */
.podium-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: var(--space-32);
    margin: var(--space-48) 0;
    padding: var(--space-32);
}

.podium-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: all var(--transition-normal);
    position: relative;
}

.podium-step:hover {
    transform: translateY(-8px);
}

.podium-step.first { order: 2; }
.podium-step.second { order: 1; }
.podium-step.third { order: 3; }

.podium-platform {
    width: 200px;
    border-radius: var(--radius-2xl);
    padding: var(--space-32) var(--space-24);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.podium-platform.first {
    height: 180px;
    background: linear-gradient(135deg, var(--amber-500), var(--amber-600));
    box-shadow: var(--shadow-xl), 0 0 40px rgba(245, 158, 11, 0.2);
}

.podium-platform.second {
    height: 150px;
    background: linear-gradient(135deg, var(--gray-400), var(--gray-500));
    box-shadow: var(--shadow-lg), 0 0 30px rgba(148, 163, 184, 0.2);
}

.podium-platform.third {
    height: 130px;
    background: linear-gradient(135deg, #cd7f32, #b8741f);
    box-shadow: var(--shadow-md), 0 0 25px rgba(205, 127, 50, 0.2);
}

.podium-rank {
    position: absolute;
    top: var(--space-12);
    right: var(--space-12);
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: white;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
}

.podium-medal {
    font-size: 3rem;
    margin-bottom: var(--space-16);
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.podium-name {
    font-family: 'Inter', sans-serif;
    color: white;
    font-weight: 700;
    font-size: 1rem;
    text-align: center;
    line-height: 1.3;
    max-width: 180px;
    word-wrap: break-word;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Floating Controls Bar - Real Functional Version */
.floating-controls-container {
    position: fixed;
    bottom: var(--space-24);
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    display: flex;
    align-items: flex-end;
    gap: var(--space-24);
    padding: var(--space-16) var(--space-24);
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-full);
    box-shadow: var(--shadow-xl), 0 0 40px rgba(0, 0, 0, 0.3);
    transition: all var(--transition-normal);
    min-width: 400px;
}

.floating-controls-container:hover {
    transform: translateX(-50%) translateY(-4px);
    box-shadow: var(--shadow-2xl), 0 0 60px rgba(0, 0, 0, 0.15);
}

.floating-control-item {
    text-align: center;
    margin-bottom: var(--space-8);
}

.floating-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: block;
    margin-bottom: var(--space-4);
}

.floating-controls-container .stDateInput > div > div,
.floating-controls-container .stSelectbox > div > div {
    font-family: 'Inter', sans-serif !important;
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: var(--radius-lg) !important;
    padding: var(--space-8) var(--space-12) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    transition: all var(--transition-fast) !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    min-width: 120px !important;
}

.floating-controls-container .stDateInput > div > div:focus-within,
.floating-controls-container .stSelectbox > div > div:focus-within {
    outline: none !important;
    border-color: var(--emerald-500) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
}

/* Hide sidebar completely */
.css-1d391kg {
    display: none !important;
}

section[data-testid="stSidebar"] {
    display: none !important;
}

/* Onboarding System Styles */
.onboarding-container {
    margin: var(--space-48) 0;
    position: relative;
}

/* Center selectors labels */
#selectors-container .stDateInput > label,
#selectors-container .stSelectbox > label {
    text-align: center !important;
    justify-content: center !important;
    display: flex !important;
    width: 100% !important;
    font-weight: 700 !important;
    font-size: 22px !important;
    margin-bottom: var(--space-4) !important;
    line-height: 1.2 !important;
    height: 32px !important;
    align-items: center !important;
}

/* FORCED Alignment - Override Streamlit */
div[data-testid="column"]:has(.stDateInput),
div[data-testid="column"]:has(.stSelectbox) {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: flex-start !important;
    min-height: 150px !important;
}

/* Force labels to be the same height */
div[data-testid="column"] .stDateInput > label,
div[data-testid="column"] .stSelectbox > label {
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 16px !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    width: 100% !important;
    text-align: center !important;
}

/* Force widgets to be the same height */
div[data-testid="column"] .stDateInput,
div[data-testid="column"] .stSelectbox {
    width: 100% !important;
    height: 60px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Force input containers */
div[data-testid="column"] .stDateInput > div,
div[data-testid="column"] .stSelectbox > div {
    width: 100% !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Remove old conflicting rules - using new forced alignment above */

.onboarding-selectors {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--space-48);
    padding: var(--space-32);
    margin-bottom: var(--space-24);
}

.selector-wrapper {
    text-align: center;
    position: relative;
    min-width: 160px;
}

.selector-label {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: var(--space-12);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Onboarding Overlay */
.onboarding-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.8);
    z-index: 9998;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

/* Onboarding Tooltip */
.onboarding-tooltip {
    position: absolute;
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-xl);
    padding: var(--space-20) var(--space-24);
    box-shadow: var(--shadow-xl);
    z-index: 9999;
    min-width: 250px;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    animation: tooltipFadeIn 0.3s ease;
}

@keyframes tooltipFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.tooltip-text {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.5;
    margin: 0;
}

/* Onboarding Arrow */
.onboarding-arrow {
    position: absolute;
        font-size: 2rem;
    color: var(--emerald-400);
    animation: arrowPulse 2s infinite;
    z-index: 9999;
}

@keyframes arrowPulse {
    0%, 100% { 
        transform: scale(1);
        opacity: 0.7;
    }
    50% { 
        transform: scale(1.2);
        opacity: 1;
    }
}

/* Element Highlighting */
.onboarding-highlight {
    position: relative;
    z-index: 9999 !important;
    background: var(--bg-card) !important;
    border-radius: var(--radius-xl);
    box-shadow: 0 0 0 4px var(--emerald-500), 0 0 40px rgba(16, 185, 129, 0.3) !important;
    animation: highlightPulse 2s infinite;
}

@keyframes highlightPulse {
    0%, 100% { 
        box-shadow: 0 0 0 4px var(--emerald-500), 0 0 40px rgba(16, 185, 129, 0.3);
    }
    50% { 
        box-shadow: 0 0 0 6px var(--emerald-400), 0 0 60px rgba(16, 185, 129, 0.5);
    }
}

/* Snow Effect */
.snowflake {
        position: fixed;
    top: -10px;
    color: #fff;
    user-select: none;
    pointer-events: none;
    z-index: 10000;
    animation: snowfall linear infinite;
    font-size: 1rem;
}

@keyframes snowfall {
    from {
        transform: translateY(-10vh) rotate(0deg);
        opacity: 1;
    }
    to {
        transform: translateY(110vh) rotate(360deg);
        opacity: 0;
    }
}

/* Welcome Message */
.welcome-message {
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-3xl);
    padding: var(--space-64) var(--space-32);
    margin: var(--space-48) 0;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}

.welcome-message::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.05) 0%, rgba(16, 185, 129, 0.02) 40%, transparent 70%);
    border-radius: 50%;
    animation: welcomeGlow 3s ease-in-out infinite;
    z-index: 0;
}

@keyframes welcomeGlow {
    0%, 100% { 
        transform: translate(-50%, -50%) scale(1);
        opacity: 0.4;
    }
    50% { 
        transform: translate(-50%, -50%) scale(1.05);
        opacity: 0.7;
    }
}

.welcome-content {
    position: relative;
    z-index: 1;
}

.welcome-title {
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    font-size: clamp(2rem, 5vw, 3rem);
    color: var(--text-primary);
    margin: 0 0 var(--space-16) 0;
    letter-spacing: -0.02em;
}

.welcome-subtitle {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 1.25rem;
    color: var(--text-secondary);
    margin: 0 0 var(--space-24) 0;
    line-height: 1.5;
}

.welcome-guide {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    color: var(--emerald-400);
    margin: 0;
    animation: welcomeBounce 2s ease-in-out infinite;
}

@keyframes welcomeBounce {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-5px); }
}

/* No Data Message */
.no-data-message {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: var(--radius-3xl);
    padding: var(--space-40) var(--space-32);
    margin: var(--space-32) 0;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 
        0 0 0 1px rgba(148, 163, 184, 0.1),
        0 0 10px rgba(100, 116, 139, 0.08),
        0 0 20px rgba(71, 85, 105, 0.05),
        0 25px 50px -12px rgba(0, 0, 0, 0.6);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(20px);
}

.no-data-message::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(248, 113, 113, 0.05), transparent, rgba(239, 68, 68, 0.05), transparent);
    animation: heroRotate 15s linear infinite;
    z-index: -1;
}

.no-data-message::after {
    content: '';
    position: absolute;
    inset: 1px;
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 50%, #1e293b 100%);
    border-radius: calc(var(--radius-3xl) - 1px);
    z-index: -1;
}

.no-data-content {
    position: relative;
    z-index: 2;
}

.no-data-title {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.8rem;
    color: #f87171;
    margin: 0 0 var(--space-16) 0;
}

.no-data-subtitle {
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 1.2rem;
    color: #e2e8f0;
    margin: 0 0 var(--space-20) 0;
    line-height: 1.5;
    opacity: 0.9;
}

.no-data-guide {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin: 0;
    opacity: 0.9;
    animation: welcomeBounce 2s ease-in-out infinite;
}

/* CELEBRATION SNOWFALL - Animazione Spettacolare */
.celebration-snowflake {
    position: fixed;
    top: -50px;
    z-index: 10000;
    pointer-events: none;
    user-select: none;
    color: white;
    text-shadow: 
        0 0 10px rgba(255, 255, 255, 0.8),
        0 0 20px rgba(139, 92, 246, 0.6),
        0 0 30px rgba(59, 130, 246, 0.4);
    filter: drop-shadow(0 0 15px rgba(255, 255, 255, 0.5));
}

@keyframes celebrationSnowfall {
    0% {
        transform: translateY(-50px) translateX(0) rotate(0deg) scale(0);
        opacity: 0;
    }
    10% {
        opacity: 1;
        transform: translateY(10vh) translateX(0) rotate(90deg) scale(1);
    }
    100% {
        transform: translateY(110vh) translateX(30px) rotate(360deg) scale(0.8);
        opacity: 0;
    }
}

/* Responsive Onboarding */
@media (max-width: 768px) {
    .onboarding-selectors {
        flex-direction: column;
        gap: var(--space-24);
        padding: var(--space-20);
    }
    
    .selector-wrapper {
        min-width: 280px;
    }
    
    .onboarding-tooltip {
        min-width: 200px;
        padding: var(--space-16) var(--space-20);
    }
    
    .tooltip-text {
        font-size: 0.9rem;
    }
    
    .onboarding-arrow {
        font-size: 1.5rem;
    }
    
    .welcome-message {
        padding: var(--space-48) var(--space-20);
        margin: var(--space-32) 0;
    }
    
    .welcome-title {
        font-size: 2rem;
    }
    
    .welcome-subtitle {
        font-size: 1.125rem;
    }
}

.theme-light .ai-dock {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
}

.floating-controls {
    gap: 20px;
}

.control-group {
    gap: 2px;
}

.control-group label {
    font-size: 0.7rem;
}

.theme-light .control-group label {
    color: #64748b;
}

.control-value {
    font-size: 0.8rem;
}

.theme-light .control-value {
    color: #0f172a;
}

.ai-dock:hover {
    background: rgba(20,20,22,0.9);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.theme-light .ai-dock:hover {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.ai-dock a, .ai-dock span {
    color: var(--text-primary);
    text-decoration: none;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
}

.ai-dock a:hover {
    background: var(--bg-secondary);
}

.theme-dark .ai-dock {
    background: linear-gradient(135deg, rgba(0, 180, 160, 0.22), rgba(0, 110, 255, 0.10));
    border-color: rgba(255, 255, 255, 0.14);
}

.theme-light .ai-dock {
    background: linear-gradient(135deg, rgba(0, 180, 160, 0.18), rgba(0, 110, 255, 0.06));
    border-color: rgba(0, 0, 0, 0.08);
}

.ai-dock::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(139, 92, 246, 0.3));
    border-radius: var(--radius-28);
    z-index: -1;
    animation: borderBreathing 8s ease-in-out infinite;
}

.ai-dock:hover {
    opacity: 1;
    transform: translateX(-50%) translateY(-2px);
    box-shadow: var(--shadow-strong);
}

.ai-dock-left {
    display: flex;
    align-items: center;
    gap: var(--space-16);
}

.ai-dock-center {
    display: flex;
    gap: var(--space-16);
}

.ai-dock-right {
    display: flex;
    align-items: center;
    gap: var(--space-16);
}

.ai-status {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
}

.ai-icon-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    font-size: 1.2rem;
    cursor: pointer;
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.ai-icon-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
}

.ai-icon-button:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

.ai-icon-button.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ai-model-select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--radius-16);
    padding: var(--space-8) var(--space-12);
    color: var(--text-primary);
    font-size: 0.875rem;
    min-width: 120px;
}

.ai-run-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: var(--gradient-primary);
    color: white;
    font-size: 1.2rem;
    cursor: pointer;
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
}

.ai-run-button:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-medium);
}

.ai-run-button:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .modern-header {
        font-size: 2rem;
        margin: 24px 0 16px 0;
    }
    
    .hero-title {
        font-size: 2rem;
    }
    
    .hero-section {
        padding: 20px;
        margin: 20px 0;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
        gap: 16px;
    }
    
    .kpi-card {
        padding: 20px;
    }
    
    .podium-container {
        flex-direction: column;
        align-items: center;
        height: auto;
        gap: 16px;
    }
    
    .podium-step {
        order: unset !important;
    }
    
    .podium-platform {
        width: 120px;
    }
    
    .podium-platform.first { height: 120px; }
    .podium-platform.second { height: 100px; }
    .podium-platform.third { height: 80px; }
    
    .ai-dock {
        position: fixed;
        bottom: 16px;
        left: 16px;
        right: 16px;
        transform: none;
        min-width: auto;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px;
        padding: 12px 16px;
    }
    
    .ai-dock-left,
    .ai-dock-center,
    .ai-dock-right {
        gap: 12px;
    }
}

/* Utility Classes */
.text-center { text-align: center; }
.mb-16 { margin-bottom: 16px; }
.mb-24 { margin-bottom: 24px; }
.mb-32 { margin-bottom: 32px; }

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

/* Success/Info/Warning/Error Messages */
.stSuccess {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 12px;
}

.stInfo {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(139, 92, 246, 0.1));
    border: 1px solid rgba(14, 165, 233, 0.2);
    border-radius: 12px;
}

.stWarning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1));
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-radius: 12px;
}

.stError {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 12px;
}

/* Global Styles */
.main {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, system-ui, sans-serif;
}

/* Theme-specific main styles */
.theme-light .main {
    background: var(--bg-primary);
    color: var(--text-primary);
}

.theme-dark .main {
    background: var(--bg-primary);
    color: var(--text-primary);
}

/* Modern Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #8b5cf6);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* Modern Tables */
.modern-table {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.95));
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(226, 232, 240, 0.8);
}

.theme-dark .modern-table {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.8);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.modern-table th {
    background: linear-gradient(135deg, #0ea5e9, #8b5cf6);
    color: white;
    font-weight: 600;
    padding: 16px;
    text-align: left;
}

.modern-table td {
    padding: 16px;
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

.theme-dark .modern-table td {
    border-bottom: 1px solid rgba(71, 85, 105, 0.8);
}

.modern-table tr:hover {
    background: rgba(14, 165, 233, 0.05);
}

/* Modern Cards */
.modern-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.95));
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
    backdrop-filter: blur(20px);
}

.theme-dark .modern-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.8);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    border-color: #0ea5e9;
}

/* Streamlit Element Overrides */
.stSelectbox > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05)) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 8px !important;
}

.theme-dark .stSelectbox > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1)) !important;
    border: 1px solid rgba(245, 158, 11, 0.4) !important;
}

.stDateInput > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05)) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 8px !important;
}

.theme-dark .stDateInput > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1)) !important;
    border: 1px solid rgba(245, 158, 11, 0.4) !important;
}

/* Modern Sidebar */
.sidebar .sidebar-content {
    background: linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.95)) !important;
    border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
}

.theme-dark .sidebar .sidebar-content {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95)) !important;
    border-right: 1px solid rgba(71, 85, 105, 0.8) !important;
}

.sidebar .sidebar-content .block-container {
    background: transparent;
}

/* Modern Main */
.main .block-container {
    background: transparent;
    padding-top: 2rem;
    padding-bottom: 6rem;
}

.main .block-container .stMarkdown {
    background: transparent;
}

/* Modern Caption */
.stCaption {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 400;
    text-align: center;
    margin: 16px 0;
}

.theme-dark .stCaption {
    color: #94a3b8;
}

/* Floating Control Bar */
.ai-dock {
    position: fixed;
    bottom: 16px;
    left: 16px;
    right: 16px;
    transform: none;
    min-width: auto;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    padding: 12px 16px;
}

.theme-light .ai-dock {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(0, 0, 0, 0.1);
}

.floating-controls {
    gap: 20px;
}

.control-group {
    gap: 2px;
}

.control-group label {
    font-size: 0.7rem;
}

.theme-light .control-group label {
    color: #64748b;
}

.control-value {
    font-size: 0.8rem;
}

.theme-light .control-value {
    color: #0f172a;
}

.ai-dock:hover {
    background: rgba(20,20,22,0.9);
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.theme-light .ai-dock:hover {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.ai-dock a, .ai-dock span {
    color: var(--text-primary);
    text-decoration: none;
    font-weight: 600;
    padding: 8px 12px;
    border-radius: 10px;
}

.ai-dock a:hover {
    background: var(--bg-secondary);
}

.theme-dark .ai-dock {
    background: linear-gradient(135deg, rgba(0, 180, 160, 0.22), rgba(0, 110, 255, 0.10));
    border-color: rgba(255, 255, 255, 0.14);
}

.theme-light .ai-dock {
    background: linear-gradient(135deg, rgba(0, 180, 160, 0.18), rgba(0, 110, 255, 0.06));
    border-color: rgba(0, 0, 0, 0.08);
}

.ai-dock::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(139, 92, 246, 0.3));
    border-radius: var(--radius-28);
    z-index: -1;
    animation: borderBreathing 8s ease-in-out infinite;
}

.ai-dock:hover {
    opacity: 1;
    transform: translateX(-50%) translateY(-2px);
    box-shadow: var(--shadow-strong);
}

.ai-dock-left {
    display: flex;
    align-items: center;
    gap: var(--space-16);
}

.ai-dock-center {
    display: flex;
    gap: var(--space-16);
}

.ai-dock-right {
    display: flex;
    align-items: center;
    gap: var(--space-16);
}

.ai-status {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
}

.ai-icon-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    font-size: 1.2rem;
    cursor: pointer;
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.ai-icon-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
}

.ai-icon-button:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

.ai-icon-button.is-disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ai-model-select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--radius-16);
    padding: var(--space-8) var(--space-12);
    color: var(--text-primary);
    font-size: 0.875rem;
    min-width: 120px;
}

.ai-run-button {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background: var(--gradient-primary);
    color: white;
    font-size: 1.2rem;
    cursor: pointer;
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
}

.ai-run-button:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-medium);
}

.ai-run-button:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .modern-header {
        font-size: 2rem;
        margin: 24px 0 16px 0;
    }
    
    .hero-title {
        font-size: 2rem;
    }
    
    .hero-section {
        padding: 20px;
        margin: 20px 0;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
        gap: 16px;
    }
    
    .kpi-card {
        padding: 20px;
    }
    
    .podium-container {
        flex-direction: column;
        align-items: center;
        height: auto;
        gap: 16px;
    }
    
    .podium-step {
        order: unset !important;
    }
    
    .podium-platform {
        width: 120px;
    }
    
    .podium-platform.first { height: 120px; }
    .podium-platform.second { height: 100px; }
    .podium-platform.third { height: 80px; }
    
    .ai-dock {
        position: fixed;
        bottom: 16px;
        left: 16px;
        right: 16px;
        transform: none;
        min-width: auto;
        flex-wrap: wrap;
        justify-content: center;
        gap: 12px;
        padding: 12px 16px;
    }
    
    .ai-dock-left,
    .ai-dock-center,
    .ai-dock-right {
        gap: 12px;
    }
}

/* Utility Classes */
.text-center { text-align: center; }
.mb-16 { margin-bottom: 16px; }
.mb-24 { margin-bottom: 24px; }
.mb-32 { margin-bottom: 32px; }

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

/* Success/Info/Warning/Error Messages */
.stSuccess {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 12px;
}

.stInfo {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.1), rgba(139, 92, 246, 0.1));
    border: 1px solid rgba(14, 165, 233, 0.2);
    border-radius: 12px;
}

.stWarning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1));
    border: 1px solid rgba(245, 158, 11, 0.2);
    border-radius: 12px;
}

.stError {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 12px;
}

/* Global Styles */
.main {
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, system-ui, sans-serif;
}

/* Theme-specific main styles */
.theme-light .main {
    background: var(--bg-primary);
    color: var(--text-primary);
}

.theme-dark .main {
    background: var(--bg-primary);
    color: var(--text-primary);
}

/* Modern Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #8b5cf6);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    padding: 12px 24px;
    font-size: 0.95rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* Modern Tables */
.modern-table {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.95));
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(226, 232, 240, 0.8);
}

.theme-dark .modern-table {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.8);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.modern-table th {
    background: linear-gradient(135deg, #0ea5e9, #8b5cf6);
    color: white;
    font-weight: 600;
    padding: 16px;
    text-align: left;
}

.modern-table td {
    padding: 16px;
    border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

.theme-dark .modern-table td {
    border-bottom: 1px solid rgba(71, 85, 105, 0.8);
}

.modern-table tr:hover {
    background: rgba(14, 165, 233, 0.05);
}

/* Modern Cards */
.modern-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.95));
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
    backdrop-filter: blur(20px);
}

.theme-dark .modern-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95));
    border: 1px solid rgba(71, 85, 105, 0.8);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    border-color: #0ea5e9;
}

/* Streamlit Element Overrides */
.stSelectbox > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05)) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 8px !important;
}

.theme-dark .stSelectbox > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1)) !important;
    border: 1px solid rgba(245, 158, 11, 0.4) !important;
}

.stDateInput > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05)) !important;
    border: 1px solid rgba(245, 158, 11, 0.3) !important;
    border-radius: 8px !important;
}

.theme-dark .stDateInput > div > div {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.1)) !important;
    border: 1px solid rgba(245, 158, 11, 0.4) !important;
}

/* Modern Sidebar */
.sidebar .sidebar-content {
    background: linear-gradient(135deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.95)) !important;
    border-right: 1px solid rgba(226, 232, 240, 0.8) !important;
}

.theme-dark .sidebar .sidebar-content {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(51, 65, 85, 0.95)) !important;
    border-right: 1px solid rgba(71, 85, 105, 0.8) !important;
}

.sidebar .sidebar-content .block-container {
    background: transparent;
}

/* Modern Main */
.main .block-container {
    background: transparent;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.main .block-container .stMarkdown {
    background: transparent;
}

/* Modern Caption */
.stCaption {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 400;
    text-align: center;
    margin: 16px 0;
}

.theme-dark .stCaption {
    color: #94a3b8;
}

/* Floating Control Bar */
.ai-dock {
    position: fixed;
    bottom: 16px;
    left: 16px;
    right: 16px;
    transform: none;
    min-width: auto;
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    padding: 12px 16px;
}

/* Modern Charts & Components */
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-2xl);
    padding: var(--space-24);
    margin: var(--space-24) 0;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-normal);
}

.chart-container:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

/* Responsive Design */
@media (max-width: 768px) {
    .app-header {
        min-height: 100vh;
        padding: var(--space-32) var(--space-16);
    }
    
    .app-title {
        font-size: clamp(2.5rem, 12vw, 4rem);
        letter-spacing: -0.04em;
    }
    
    .app-subtitle {
        font-size: clamp(1rem, 4vw, 1.4rem);
        margin-top: var(--space-16);
    }
    
    .hero-section {
        padding: var(--space-32) var(--space-20);
        margin: var(--space-24) 0;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
        gap: var(--space-16);
    }
    
    .podium-container {
        flex-direction: column;
    align-items: center;
        height: auto;
        gap: var(--space-20);
        padding: var(--space-20);
    }
    
    .podium-step {
        order: unset !important;
    }
    
    .podium-platform {
        width: 160px;
    }
    
    .podium-platform.first { height: 140px; }
    .podium-platform.second { height: 120px; }
    .podium-platform.third { height: 100px; }
    
    .floating-controls-container {
        bottom: var(--space-16);
        flex-direction: column;
        gap: var(--space-12);
        padding: var(--space-12) var(--space-16);
        min-width: 300px;
        border-radius: var(--radius-2xl);
    }
    
    .floating-control-item {
        margin-bottom: var(--space-4);
    }
    
    .floating-label {
        font-size: 0.7rem;
    }
}

/* Streamlit Component Overrides */
.stSelectbox > div > div,
.stDateInput > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-primary) !important;
    border-radius: var(--radius-lg) !important;
    font-family: 'Inter', sans-serif !important;
    transition: all var(--transition-fast) !important;
    box-shadow: var(--shadow-xs) !important;
}

.stSelectbox > div > div:focus-within,
.stDateInput > div > div:focus-within {
    border-color: var(--primary-500) !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.stButton > button {
    font-family: 'Inter', sans-serif !important;
    background: var(--gradient-primary) !important;
    border: none !important;
    border-radius: var(--radius-lg) !important;
    color: white !important;
    font-weight: 600 !important;
    padding: var(--space-12) var(--space-24) !important;
    font-size: 0.875rem !important;
    transition: all var(--transition-normal) !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-lg) !important;
}

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-sm);
}

/* Messages */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: var(--radius-lg) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}

.stSuccess {
    background: var(--emerald-50) !important;
    border: 1px solid var(--emerald-200) !important;
    color: var(--emerald-800) !important;
}

.stInfo {
    background: var(--primary-50) !important;
    border: 1px solid var(--primary-200) !important;
    color: var(--primary-800) !important;
}

.stWarning {
    background: var(--amber-50) !important;
    border: 1px solid var(--amber-200) !important;
    color: var(--amber-800) !important;
}

.stError {
    background: var(--red-50) !important;
    border: 1px solid var(--red-200) !important;
    color: var(--red-800) !important;
}

/* Modern Caption */
.stCaption {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-tertiary) !important;
    font-size: 0.875rem !important;
    font-weight: 400 !important;
    text-align: center !important;
    margin: var(--space-16) 0 !important;
}

</style>
""", unsafe_allow_html=True)


def aggregate_station_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "kmtotal" in df.columns:
        df["pct_open"] = np.where(df["kmtotal"] > 0, df.get("kmopen", 0) / df["kmtotal"], np.nan)
    else:
        df["pct_open"] = np.nan
    if "kmopen" in df.columns:
        df["is_open"] = (df["kmopen"].fillna(0) > 0).astype(float)
    else:
        df["is_open"] = 0.0
    agg_spec = {
        "kmopen": ("kmopen", "mean"),
        "kmtotal": ("kmtotal", "mean"),
        "pct_open": ("pct_open", "mean"),
        "is_open": ("is_open", "mean"),
        "danger_level_avg": ("danger_level_avg", "mean"),
        "vento": ("vento", "mean"),
        "nebbia": ("nebbia", "mean"),
        "espesor_medio": ("espesor_medio", "mean"),
    }
    if "sole" in df.columns:
        agg_spec["sole"] = ("sole", "mean")
    if "pioggia" in df.columns:
        agg_spec["pioggia"] = ("pioggia", "mean")

    agg = df.groupby("nome_stazione").agg(**agg_spec).reset_index()

    # rename to friendly column names
    agg = agg.rename(
        columns={
            "kmopen": "km_open_est",
            "kmtotal": "km_total_est",
            "is_open": "open_prob",
            "danger_level_avg": "avalanche",
            "espesor_medio": "neve_cm",
        }
    )
    return agg.fillna(0)


def build_textual_tags(row: pd.Series, livello: str, profilo: str) -> List[str]:
    tags: List[str] = []
    if row.get("pct_open", 0) >= 0.5 or row.get("km_open_est", 0) >= 20:
        tags.append("molte piste aperte")
    if row.get("avalanche", 3) <= 2.5:
        tags.append("basso rischio valanghe")
    if row.get("vento", 0) <= 0.2 and row.get("nebbia", 0) <= 0.2:
        tags.append("meteo stabile")
    if livello == "esperto" and row.get("neve_cm", 0) >= 40:
        tags.append("neve consistente")
    if livello == "base" and row.get("pct_open", 0) >= 0.4:
        tags.append("ideale per principianti")
    if profilo in ("panoramico", "familiare", "festaiolo", "lowcost"):
        tags.append(f"adatta al profilo {profilo}")
    return tags


def ensure_lat_lon(df: pd.DataFrame) -> pd.DataFrame:
    """Try to provide 'lat' and 'lon' columns by renaming common variants.

    Supported aliases: latitude/longitude, Latitude/Longitude, latitudine/longitudine.
    """
    df = df.copy()
    colmap = {c.lower(): c for c in df.columns}
    lat_aliases = ["lat", "latitude", "latitudine"]
    lon_aliases = ["lon", "long", "lng", "longitude", "longitudine"]
    # Find best matches
    lat_col = next((colmap[a] for a in lat_aliases if a in colmap), None)
    lon_col = next((colmap[a] for a in lon_aliases if a in colmap), None)
    if lat_col and "lat" not in df.columns:
        df["lat"] = df[lat_col]
    if lon_col and "lon" not in df.columns:
        df["lon"] = df[lon_col]
    # Ensure columns exist to avoid KeyError downstream
    if "lat" not in df.columns:
        df["lat"] = np.nan
    if "lon" not in df.columns:
        df["lon"] = np.nan
    return df


def build_llm_prompt(df_kpis: pd.DataFrame, best_name: str, livello: str, profilo: str, target_date: datetime.date) -> str:
    # Trova riga best
    best = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0].to_dict() if not df_kpis.empty else {}
    # Seleziona 2 alternative principali (per km aperti stimati)
    others = (
        df_kpis[df_kpis["nome_stazione"] != best_name]
        .sort_values("km_open_est", ascending=False)
        .head(2)
        .to_dict(orient="records")
        if "km_open_est" in df_kpis.columns else []
    )
    def fmt(x, pct=False):
        try:
            return f"{float(x)*100:.0f}%" if pct else f"{float(x):.0f}"
        except Exception:
            return "-"
    # facts per best
    b_km = fmt(best.get("km_open_est", 0))
    b_pct = fmt(best.get("pct_open", 0), pct=True)
    b_neb = fmt(best.get("nebbia", 0), pct=True)
    b_ven = fmt(best.get("vento", 0), pct=True)
    b_av  = f"{float(best.get('avalanche', 0)):.1f}" if best.get('avalanche') is not None else "-"
    lines = [
        f"BEST {best_name}: km aperti {b_km}, % aperte {b_pct}, nebbia {b_neb}, vento {b_ven}, valanghe {b_av}"
    ]
    for o in others:
        o_km = fmt(o.get("km_open_est", 0))
        o_pct = fmt(o.get("pct_open", 0), pct=True)
        o_neb = fmt(o.get("nebbia", 0), pct=True)
        o_ven = fmt(o.get("vento", 0), pct=True)
        o_av  = f"{float(o.get('avalanche', 0)):.1f}" if o.get('avalanche') is not None else "-"
        lines.append(
            f"ALT {o['nome_stazione']}: km {o_km}, % {o_pct}, nebbia {o_neb}, vento {o_ven}, valanghe {o_av}"
        )
    context = "\n".join(lines)
    target_date_italian = format_date_for_display(target_date)
    prompt = (
        f"Per la data {target_date_italian} l'app ha selezionato la stazione migliore: {best_name}. "
        f"Scrivi un'overview molto breve (max 2 frasi, 35–45 parole), chiara e utile, che spieghi perché {best_name} è preferibile rispetto alle altre. "
        f"Usa informazioni concrete: km/% piste, meteo (nebbia/vento/sole/pioggia), rischio valanghe e coerenza con livello '{livello}' e profilo '{profilo}'. "
        f"Non fare elenchi; evita superlativi generici. Se non emergono differenze nette, evidenzia il miglior compromesso. "
        f"Sii coerente con i dati della dashboard e spiega chiaramente perché {best_name} è consigliata.\n"
        f"Dati sintetici (usa solo come base, non ripetere letteralmente etichette BEST/ALT):\n{context}"
    )
    return prompt


def build_festaiolo_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date) -> str:
    # Estrae signal dalle recensioni per tema "festaiolo" per best + 2 alternative
    parole_festaiolo = [
        "divertente", "giovanile", "apres ski", "festa", "fete", "party", "fiesta", "juvenil", 
        "jovanil", "juventud", "jove", "great atmosphere", "young", "atmosfera", "nightlife", 
        "bar", "ristoranti", "divertimento", "entertainment", "fun", "lively", "vibrant"
    ]
    
    # Costruisci il prompt con focus sulla stazione consigliata
    target_date_italian = format_date_for_display(target_date)
    prompt_parts = [
        f"Per la data {target_date_italian} e livello '{livello}', {best_name} è la stazione consigliata dal sistema.",
        f"Scrivi un mini-riassunto (max 3 frasi) che spieghi perché {best_name} è consigliata per il profilo festaiolo."
    ]
    
    # Aggiungi contesto dalle recensioni
    try:
        by_station = (
            df_rec.groupby("nome_stazione")[["festaiolo", "ristoranti", "coda", "Stelle"]]
            .mean().reset_index().sort_values("festaiolo", ascending=False)
        )
        rows = by_station.head(3).to_dict(orient="records")
        for r in rows:
            parts.append(
                f"- {r['nome_stazione']}: festaiolo={r.get('festaiolo',0):.2f}, stelle={r.get('Stelle',0):.2f}, ristoranti={r.get('ristoranti',0):.2f}, code={r.get('coda',0):.2f}"
            )
    except Exception:
        parts = []
    
    context = "\n".join(parts) if parts else ""
    keywords = ", ".join(parole_festaiolo[:15]) + ", ..."
    
    prompt_parts.append(
        f"Spiega l'atmosfera e la vita notturna di {best_name} e menziona alternative se disponibili. "
        f"Considera recensioni per divertimento/ristoranti con parole chiave: {keywords}. "
        f"Sii pratico e specifico (atmosfera, après-ski, nightlife). Evita elenchi e sii coerente con i dati della dashboard."
    )
    
    if context:
        prompt_parts.append(f"Dati recensioni:\n{context}")
    
    return " ".join(prompt_parts)


def build_familiare_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date) -> str:
    # Panoramica family-friendly: segnali recensione e code
    parole_code = [
        "fila", "attesa", "coda", "caos", "affollato", "cua", "cola", "espera", "lleno", "ple",
        "caotic", "aglomeracion", "aglomeracio", "atasco", "pieno", "disorganizzato", "desorganizado",
        "desorganizat", "ressa", "file", "attente", "queue", "bouchon", "foule", "bondé", "plein",
        "chaotique", "désorganisé", "waiting", "wait", "crowd", "crowded", "full", "line", "chaos",
        "chaotic", "busy", "overcrowded", "unorganized", "messy"
    ]
    
    # Costruisci il prompt con focus sulla stazione consigliata
    target_date_italian = format_date_for_display(target_date)
    prompt_parts = [
        f"Per la data {target_date_italian} e livello '{livello}', {best_name} è la stazione consigliata dal sistema.",
        f"Scrivi un mini-riassunto (max 3 frasi) che spieghi perché {best_name} è consigliata per il profilo familiare."
    ]
    
    # Aggiungi contesto dalle recensioni
    try:
        by_station = (
            df_rec.groupby("nome_stazione")[["familiare", "sicurezza", "coda", "Stelle"]]
            .mean().reset_index().sort_values("familiare", ascending=False)
        )
        rows = by_station.head(3).to_dict(orient="records")
        for r in rows:
            parts.append(
                f"- {r['nome_stazione']}: family={r.get('familiare',0):.2f}, sicurezza={r.get('sicurezza',0):.2f}, code={r.get('coda',0):.2f}, stelle={r.get('Stelle',0):.2f}"
            )
    except Exception:
        parts = []
    
    context = "\n".join(parts) if parts else ""
    keywords = ", ".join(parole_code[:10]) + ", ..."
    
    prompt_parts.append(
        f"Spiega i servizi per famiglie di {best_name} e menziona alternative se disponibili. "
        f"Considera recensioni per servizi familiari con parole chiave: {keywords}. "
        f"Evita elenchi, sii conciso e coerente con i dati della dashboard."
    )
    
    if context:
        prompt_parts.append(f"Dati recensioni:\n{context}")
    
    return " ".join(prompt_parts)


def build_lowcost_prompt(df_rec: pd.DataFrame, best_name: str, livello: str, target_date: datetime.date, df_ratio: pd.DataFrame = None) -> str:
    # Panoramica low-cost: segnali recensione su prezzi e rapporto qualità-prezzo
    parole_lowcost = [
        "barato", "económico", "económica", "asequible", "precio", "precios", "oferta", "ofertas", 
        "descuento", "descuentos", "ahorro", "calidad-precio", "coste", "rebaja", "rebajas", 
        "promoción", "promociones", "barat", "econòmic", "econòmica", "assequible", "preu", "preus", 
        "oferta", "ofertes", "descompte", "descomptes", "estalvi", "qualitat-preu", "cost", 
        "rebaixa", "rebaixes", "promoció", "promocions", "car", "cara", "bon marché", "économique", 
        "abordable", "prix", "offre", "offres", "cheap", "affordable", "budget", "value", "deal", 
        "discount", "sale", "promotion", "offer", "cost-effective", "good value", "worth it"
    ]
    
    # Costruisci il prompt con focus sulla stazione consigliata
    target_date_italian = format_date_for_display(target_date)
    prompt_parts = [
        f"Per la data {target_date_italian} e livello '{livello}', {best_name} è la stazione consigliata dal sistema.",
        f"Scrivi un mini-riassunto (max 3 frasi) che spieghi perché {best_name} è consigliata per il profilo low-cost."
    ]
    
    # Aggiungi informazioni dal rapporto qualità-prezzo se disponibile
    if df_ratio is not None and not df_ratio.empty:
        best_ratio = df_ratio[df_ratio["nome_stazione"] == best_name]
        if not best_ratio.empty:
            best_euro_km = best_ratio.iloc[0].get("rapporto_euro_km", 0)
            best_km = best_ratio.iloc[0].get("kmopen", 0)
            best_price = best_ratio.iloc[0].get("Prezzo_skipass", 0)
            
            prompt_parts.append(
                f"Usa questi dati: {best_name} ha rapporto €/km={best_euro_km:.2f}, "
                f"km aperti={best_km:.1f}, prezzo skipass={best_price:.2f}€."
            )
    
    # Aggiungi contesto dalle recensioni
    try:
        available_cols = [col for col in ["lowcost", "Stelle"] if col in df_rec.columns]
        if available_cols:
            by_station = (
                df_rec.groupby("nome_stazione")[available_cols]
                .mean().reset_index().sort_values("lowcost", ascending=False)
            )
            rows = by_station.head(3).to_dict(orient="records")
            for r in rows:
                part_parts = [f"- {r['nome_stazione']}:"]
                if "lowcost" in available_cols:
                    part_parts.append(f"lowcost={r.get('lowcost',0):.2f}")
                if "Stelle" in available_cols:
                    part_parts.append(f"stelle={r.get('Stelle',0):.2f}")
                parts.append(", ".join(part_parts))
    except Exception:
        parts = []
    
    context = "\n".join(parts) if parts else ""
    keywords = ", ".join(parole_lowcost[:15]) + ", ..."
    
    prompt_parts.append(
        f"Spiega la convenienza di {best_name} e menziona alternative economiche se disponibili. "
        f"Considera recensioni per prezzi/offerte con parole chiave: {keywords}. "
        f"Evita elenchi, sii conciso e coerente con i dati della dashboard."
    )
    
    if context:
        prompt_parts.append(f"Dati recensioni:\n{context}")
    
    return " ".join(prompt_parts)


def build_local_overview(df_kpis: pd.DataFrame, best_name: str) -> str:
    try:
        row = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
    except Exception:
        return f"{best_name} è una scelta solida per questo periodo: piste aperte e condizioni stabili."
    parts = []
    if row.get("km_open_est", 0) > 0:
        parts.append("buona disponibilità di piste")
    if row.get("pct_open", 0) >= 0.5:
        parts.append("percentuale di apertura elevata")
    if row.get("nebbia", 0) <= 0.2 and row.get("vento", 0) <= 0.2:
        parts.append("meteo tendenzialmente stabile")
    if row.get("avalanche", 3) <= 2.5:
        parts.append("rischio contenuto")
    txt = ", ".join(parts[:3]) or "equilibrio tra piste e meteo"
    return f"{best_name} è la scelta più pratica: {txt}."


@st.cache_data(ttl=3600, show_spinner=False)
def _llm_overview_cached(prompt: str, max_tokens: int) -> tuple[str, dict]:
    return generate_overview(prompt, max_tokens)


def render_map_with_best(df_coords: pd.DataFrame, best_name: str, tooltip_km: bool = False):
    # Prepara DF con coordinate di tutte le stazioni
    base_coords = df_coords.copy()
    def _norm(s: str) -> str:
        try:
            return re.sub(r"\s+", " ", str(s).strip().lower())
        except Exception:
            return str(s)
    has_latlon = any(c.lower() in ("lat","latitude","latitudine") for c in base_coords.columns) and \
                 any(c.lower() in ("lon","lng","long","longitude","longitudine") for c in base_coords.columns)
    if not has_latlon:
        # prova a recuperare da df_meteo
        try:
            _, _, df_meteo_all, _ = load_datasets()
            if df_meteo_all is not None and not df_meteo_all.empty:
                meteo_all = ensure_lat_lon(df_meteo_all.copy())
                meteo_coords = meteo_all[["nome_stazione", "lat", "lon"]].drop_duplicates()
                base_coords = base_coords.merge(meteo_coords, on="nome_stazione", how="left")
        except Exception:
            pass
    base_coords = ensure_lat_lon(
        base_coords[["nome_stazione"] + [
            c for c in base_coords.columns
            if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")
        ]].drop_duplicates()
    )
    map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
    if map_data.empty:
        st.info("Coordinate non disponibili per la mappa.")
        return
    map_data["_norm_name"] = map_data["nome_stazione"].apply(_norm)
    best_norm = _norm(best_name)
    # Trova coords esatte per la consigliata direttamente dal meteo come fallback forte
    best_pt = pd.DataFrame()
    try:
        _, _, df_meteo_all, _ = load_datasets()
        if df_meteo_all is not None and not df_meteo_all.empty:
            meteo_all = ensure_lat_lon(df_meteo_all.copy())
            meteo_all["_norm_name"] = meteo_all["nome_stazione"].apply(_norm)
            match_exact = meteo_all[meteo_all["_norm_name"] == best_norm]
            if not match_exact.empty:
                best_pt = match_exact[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
            else:
                token = best_norm.split(" ")[0] if best_norm else ""
                if token:
                    match_partial = meteo_all[meteo_all["_norm_name"].str.contains(re.escape(token), na=False)]
                    if not match_partial.empty:
                        best_pt = match_partial[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
    except Exception:
        pass
    if best_pt.empty:
        # fallback su mappa aggregata
        cand = map_data[map_data["_norm_name"] == best_norm]
        if cand.empty and best_norm:
            token = best_norm.split(" ")[0]
            cand = map_data[map_data["_norm_name"].str.contains(re.escape(token), na=False)]
        if not cand.empty:
            best_pt = cand[["nome_stazione","lat","lon"]].drop_duplicates().head(1).copy()
    # layer base e layer corona
    center_lat = map_data["lat"].mean()
    center_lon = map_data["lon"].mean()
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)
    layer_all = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[lon, lat]',
        get_radius=8000,
        get_fill_color='[255, 0, 0, 160]',
        pickable=True,
        auto_highlight=True,
    )
    layers = [layer_all]
    if not best_pt.empty:
        # Pallino verde per l'impianto consigliato
        best_layer = pdk.Layer(
            "ScatterplotLayer",
            data=best_pt,
            get_position='[lon, lat]',
            get_radius=12000,
            get_fill_color='[0, 200, 0, 220]',
            pickable=False,
        )
        layers.append(best_layer)
    deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{nome_stazione}"})
    st.pydeck_chart(deck, use_container_width=True)


def main():
    st.markdown("""
<div class="app-header">
    <h1 class="app-title">🏔️ Pirenei Ski Recommender</h1>
    <p class="app-subtitle">La tua guida per scegliere la stazione sciistica perfetta</p>
</div>
""", unsafe_allow_html=True)

    # Set theme to dark by default
    theme = "dark"
    
    # Apply theme class to body
    st.markdown(f'<div class="theme-{theme}">', unsafe_allow_html=True)

    with st.spinner("Caricamento dati..."):
        df_infonieve, df_valanghe, df_meteo, df_recensioni = load_datasets()

    if df_infonieve is None:
        st.error("Impossibile caricare i dati. Verifica i CSV.")
        return

    # Floating dock state (replaces sidebar filters)
    min_date = df_infonieve["date"].min().date()
    default_date = datetime.date(2025, 12, 17)
    if "dock_date" not in st.session_state:
        st.session_state.dock_date = default_date
    if "dock_level" not in st.session_state:
        st.session_state.dock_level = "esperto"
    if "dock_profile" not in st.session_state:
        st.session_state.dock_profile = "nessuno"

    # Onboarding System
    if "onboarding_completed" not in st.session_state:
        st.session_state.onboarding_completed = False
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "selected_level" not in st.session_state:
        st.session_state.selected_level = None
    if "selected_profile" not in st.session_state:
        st.session_state.selected_profile = None

    # Show welcome message FIRST if onboarding not completed
    if not st.session_state.onboarding_completed:
        st.markdown("""
        <div class="welcome-message">
            <div class="welcome-content">
                <h2 class="welcome-title">Benvenuto su Pirenei Ski Recommender! 🎿</h2>
                <p class="welcome-subtitle">Analizziamo condizioni meteo storiche, apertura piste e qualità della neve per suggerirti la stazione sciistica più adatta al tuo livello e profilo.</p>
                <p class="welcome-guide">👇 Inizia selezionando le tue preferenze qui sotto</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Onboarding Selectors with proper overlay
    st.markdown('<div id="selectors-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div id="date-column" class="selector-column">', unsafe_allow_html=True)
        new_date = st.date_input(
            "📅 DATA",
            value=st.session_state.selected_date,
            min_value=min_date,
            max_value=datetime.date(2030, 12, 31),
            key="onboard_date",
            disabled=(st.session_state.onboarding_step != 1 and not st.session_state.onboarding_completed)
        )
        if new_date and new_date != st.session_state.selected_date:
            st.session_state.selected_date = new_date
            st.session_state.dock_date = new_date
            if st.session_state.onboarding_step == 1:
                st.session_state.onboarding_step = 2
                st.rerun()
            elif st.session_state.onboarding_completed:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div id="level-column" class="selector-column">', unsafe_allow_html=True)
        level_opts = ["base", "medio", "esperto"]
        new_level = st.selectbox(
            "🎯 LIVELLO",
            level_opts,
            index=level_opts.index(st.session_state.selected_level) if st.session_state.selected_level in level_opts else None,
            key="onboard_level",
            disabled=(st.session_state.onboarding_step != 2 and not st.session_state.onboarding_completed)
        )
        if new_level and new_level != st.session_state.selected_level:
            st.session_state.selected_level = new_level
            st.session_state.dock_level = new_level
            if st.session_state.onboarding_step == 2:
                st.session_state.onboarding_step = 3
                st.rerun()
            elif st.session_state.onboarding_completed:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div id="profile-column" class="selector-column">', unsafe_allow_html=True)
        profile_opts = [p for p in SUPPORTED_PROFILES if p != "nessuno"]
        all_profile_opts = ["Salta questo step"] + profile_opts
        current_index = None
        if st.session_state.selected_profile == "nessuno":
            current_index = 0
        elif st.session_state.selected_profile in profile_opts:
            current_index = profile_opts.index(st.session_state.selected_profile) + 1
            
        new_profile = st.selectbox(
            "👥 PROFILO",
            all_profile_opts,
            index=current_index,
            key="onboard_profile",
            disabled=(st.session_state.onboarding_step != 3 and not st.session_state.onboarding_completed)
        )
        if new_profile and (
            (new_profile == "Salta questo step" and st.session_state.selected_profile != "nessuno") or
            (new_profile != "Salta questo step" and st.session_state.selected_profile != new_profile)
        ):
            if new_profile == "Salta questo step":
                st.session_state.selected_profile = "nessuno"
                st.session_state.dock_profile = "nessuno"
            else:
                st.session_state.selected_profile = new_profile
                st.session_state.dock_profile = new_profile
            
            if not st.session_state.onboarding_completed:
                st.session_state.onboarding_completed = True
                st.rerun()
            elif st.session_state.onboarding_completed:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Onboarding tooltip - SOTTO I SELETTORI nel flusso normale
    if not st.session_state.onboarding_completed:
        step = st.session_state.onboarding_step
        
        # Tooltip messages
        messages = {
            1: "Quando vorresti conquistare le piste? ⛷️",
            2: "Sei un principiante o un pro della neve? 🏔️🎿", 
            3: "Che tipo di sciatore sei? (puoi anche saltare!) 🤙❄️"
        }
        
        # Position tooltip based on step with flex
        tooltip_justify = {
            1: "flex-start",    # Align left for first column
            2: "center",        # Align center for second column  
            3: "flex-end"       # Align right for third column
        }
        
        current_message = messages.get(step, f"Step {step}")
        current_justify = tooltip_justify.get(step, "center")
        
        # Show tooltip in normal document flow - allineato con i selettori  
        st.markdown(f"""
        <div id="tooltip-container" style="
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            width: 100%;
            margin: 0 0 8px 0;
            padding: 0 20px;
        ">
            <div style="grid-column: {step}; justify-self: center;">
                <div class="onboarding-tooltip-flow tooltip-step-{step}" style="
                background: #1f2937;
                border: 2px solid #10b981;
                border-radius: 16px;
                padding: 12px 18px;
                color: #f8fafc;
                font-family: Inter, sans-serif;
                font-size: 15px;
                font-weight: 600;
                box-shadow: 
                    0 0 0 1px rgba(16, 185, 129, 0.3),
                    0 0 8px rgba(16, 185, 129, 0.18),
                    0 0 16px rgba(16, 185, 129, 0.15),
                    0 0 24px rgba(16, 185, 129, 0.12),
                    0 0 32px rgba(16, 185, 129, 0.08),
                    0 0 40px rgba(16, 185, 129, 0.05),
                    0 25px 50px -12px rgba(0, 0, 0, 0.8);
                filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.25));
                max-width: 280px;
                text-align: center;
                animation: tooltipSlideDown 0.3s ease-out;
                position: relative;
                backdrop-filter: blur(10px);
            ">
                    {current_message}
                </div>
            </div>
        </div>
        
        <!-- Freccia separata con CSS -->
        <style>
        .tooltip-step-{step}::before {{
            content: '';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 12px solid transparent;
            border-right: 12px solid transparent;
            border-bottom: 12px solid #10b981;
            filter: drop-shadow(0 -2px 4px rgba(16, 185, 129, 0.3));
        }}
        
        .tooltip-step-{step}::after {{
            content: '';
            position: absolute;
            top: -9px;
            left: 50%;
            transform: translateX(-50%);
            width: 0;
            height: 0;
            border-left: 10px solid transparent;
            border-right: 10px solid transparent;
            border-bottom: 10px solid #1f2937;
        }}
        </style>
        
        <style>
        @keyframes tooltipSlideDown {{
            from {{ 
                opacity: 0; 
                transform: translateY(-20px); 
            }}
            to {{ 
                opacity: 1; 
                transform: translateY(0); 
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # Show snowfall when onboarding completes
    if st.session_state.onboarding_completed and "snowfall_shown" not in st.session_state:
        st.session_state.snowfall_shown = True
        st.markdown("""
        <script>
        // Snowfall celebration
        function createSnowflake() {
            const snowflake = document.createElement('div');
            snowflake.className = 'snowflake';
            snowflake.innerHTML = '❄️';
            snowflake.style.left = Math.random() * 100 + 'vw';
            snowflake.style.animationDuration = Math.random() * 3 + 2 + 's';
            snowflake.style.opacity = Math.random();
            snowflake.style.fontSize = Math.random() * 10 + 10 + 'px';
            document.body.appendChild(snowflake);
            
            setTimeout(() => {
                snowflake.remove();
            }, 5000);
        }
        
        // Create snowflakes
        for (let i = 0; i < 50; i++) {
            setTimeout(() => createSnowflake(), i * 100);
        }
        
        // CELEBRATION FIOCCHI DI NEVE SPETTACOLARE! 
        function createCelebrationSnowfall() {
            const container = document.body;
            const snowflakeCount = 150; // Molti più fiocchi!
            
            for (let i = 0; i < snowflakeCount; i++) {
                setTimeout(() => {
                    const snowflake = document.createElement('div');
                    snowflake.classList.add('celebration-snowflake');
                    
                    // Varietà di simboli invernali
                    const symbols = ['❄️', '⭐', '✨', '🌟', '💫', '❅', '🔥'];
                    snowflake.innerHTML = symbols[Math.floor(Math.random() * symbols.length)];
                    
                    // Posizione e stile randomici
                    snowflake.style.left = Math.random() * 100 + 'vw';
                    snowflake.style.fontSize = (Math.random() * 1.5 + 0.8) + 'rem';
                    snowflake.style.opacity = Math.random() * 0.8 + 0.6;
                    
                    // Velocità e rotazione casuali
                    const duration = Math.random() * 3 + 4; // 4-7 secondi
                    const rotation = Math.random() * 360;
                    
                    snowflake.style.animation = `
                        celebrationSnowfall ${duration}s linear forwards,
                        sparkleRotate ${duration * 0.7}s ease-in-out infinite
                    `;
                    
                    snowflake.style.transform = `rotate(${rotation}deg)`;
                    
                    container.appendChild(snowflake);
                    
                    // Rimozione automatica
                    setTimeout(() => {
                        if (snowflake && snowflake.parentNode) {
                            snowflake.remove();
                        }
                    }, duration * 1000 + 500);
                }, i * 30); // Rilascio graduale
            }
        }
        
        // Avvia celebrazione
        createCelebrationSnowfall();
        
        // Auto scroll to results con ritardo per godersi l'animazione
        setTimeout(() => {
            const resultsSection = document.querySelector('.hero-section');
            if (resultsSection) {
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
        }, 2000);
        </script>
        """, unsafe_allow_html=True)

    # Use selected values or defaults
    data_sel = st.session_state.selected_date or st.session_state.dock_date
    livello = st.session_state.selected_level or st.session_state.dock_level
    profilo = st.session_state.selected_profile or st.session_state.dock_profile
    profilo_norm = str(profilo).strip().lower()



    # STOP HERE se l'onboarding non è completato
    if not st.session_state.onboarding_completed:
        st.stop()

    # Add restart button after onboarding completion (styled)
    st.markdown("""
    <style>
    /* Restart Button Styling - Coerente con design system */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 50%, #1e293b 100%) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: var(--radius-2xl) !important;
        padding: var(--space-12) var(--space-32) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 0 0 1px rgba(148, 163, 184, 0.1),
            0 0 15px rgba(100, 116, 139, 0.1),
            0 0 30px rgba(71, 85, 105, 0.05),
            0 8px 25px -8px rgba(0, 0, 0, 0.4) !important;
        height: auto !important;
        min-height: auto !important;
        backdrop-filter: blur(10px) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(145deg, #334155 0%, #1e293b 50%, #334155 100%) !important;
        color: var(--text-primary) !important;
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 
            0 0 0 1px rgba(148, 163, 184, 0.2),
            0 0 25px rgba(100, 116, 139, 0.15),
            0 0 50px rgba(71, 85, 105, 0.1),
            0 15px 35px -10px rgba(0, 0, 0, 0.6) !important;
        border-color: rgba(148, 163, 184, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Più spazio per avvicinarlo ai selettori e allontanarlo dall'hero
    st.markdown('<div style="margin: 2px 0;"></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Ricomincia", key="restart_onboarding", use_container_width=True, type="secondary"):
            # Reset onboarding state
            st.session_state.onboarding_completed = False
            st.session_state.onboarding_step = 1
            st.session_state.selected_date = None
            st.session_state.selected_level = None
            st.session_state.selected_profile = None
            if "snowfall_shown" in st.session_state:
                del st.session_state.snowfall_shown
            st.rerun()

    # Plotly theme synchronization
    plotly_template = "plotly_white" if theme == "light" else "plotly_dark"

    # Considera sempre tutte le stazioni
    df_filtered_infonieve = df_infonieve.copy()
    df_filtered_val = df_valanghe.copy()
    df_filtered_meteo = df_meteo.copy()
    df_filtered_rec = df_recensioni.copy()

    df_with_indices = compute_indices(
        df_filtered_infonieve, df_filtered_val, df_filtered_meteo, df_filtered_rec, data_sel
    )

    if df_with_indices.empty:
        if st.session_state.onboarding_completed:
            st.markdown("""
            <div class="no-data-message">
                <div class="no-data-content">
                    <h3 class="no-data-title">😔 Nessuna stazione aperta</h3>
                    <p class="no-data-subtitle">Le piste sono chiuse in questa data. Prova a scegliere un altro giorno per divertirti sulla neve!</p>
                    <p class="no-data-guide">⬆️ Modifica la data qui sopra</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        # Tabella media apertura/chiusura per impianto (sugli anni disponibili) con logica 5 chiusi/prima e 5 aperti/dopo
        try:
            base = df_infonieve.dropna(subset=["date"]).copy()
            base["date"] = pd.to_datetime(base["date"], errors="coerce")
            base = base.dropna(subset=["date"])  # robustezza
            base["year"] = base["date"].dt.year

            # Costruisci colonna stato (1 aperto, 0 chiuso)
            if "idestado" in base.columns:
                base["stato"] = base["idestado"].fillna(0).astype(int).clip(0, 1)
            elif "kmopen" in base.columns:
                base["stato"] = (base["kmopen"].fillna(0) > 0).astype(int)
            else:
                base["stato"] = 0  # se non sappiamo, consideriamo chiuso

            rows = []
            for (staz, yr), g in base.groupby(["nome_stazione", "year"], as_index=False):
                gd = g.sort_values("date").reset_index(drop=True)
                s = gd["stato"].astype(int).tolist()
                dates = gd["date"].tolist()
                n = len(gd)
                open_date = None
                close_date = None
                for i in range(n):
                    # finestre
                    prev5 = s[i-5:i] if i-5 >= 0 else []
                    next5 = s[i+1:i+6] if i+6 <= n else []
                    if len(prev5) == 5 and len(next5) == 5:
                        # apertura: 5 chiusi prima (tutti 0) e 5 aperti dopo (tutti 1)
                        if sum(prev5) == 0 and sum(next5) == 5 and open_date is None:
                            open_date = dates[i]
                        # chiusura: 5 aperti prima e 5 chiusi dopo
                        if sum(prev5) == 5 and sum(next5) == 0 and close_date is None:
                            close_date = dates[i]
                    if open_date is not None and close_date is not None:
                        break
                if open_date is not None or close_date is not None:
                    rows.append({
                        "nome_stazione": staz,
                        "year": yr,
                        "apertura": open_date,
                        "chiusura": close_date,
                    })

            if rows:
                per_year = pd.DataFrame(rows)
                # calcola DOY medi ignorando NaT
                if "apertura" in per_year:
                    per_year["apertura_doy"] = pd.to_datetime(per_year["apertura"]).dt.dayofyear
                if "chiusura" in per_year:
                    per_year["chiusura_doy"] = pd.to_datetime(per_year["chiusura"]).dt.dayofyear
                avg = per_year.groupby("nome_stazione", as_index=False).agg(
                    apertura_doy=("apertura_doy", "mean"), chiusura_doy=("chiusura_doy", "mean")
                )

                def doy_to_label(doy: float) -> str:
                    try:
                        ts = pd.Timestamp(2000, 1, 1) + pd.to_timedelta(int(round(doy)) - 1, unit="D")
                        return ts.strftime("%d %b")
                    except Exception:
                        return "-"

                avg["Apertura media"] = avg["apertura_doy"].apply(doy_to_label)
                avg["Chiusura media"] = avg["chiusura_doy"].apply(doy_to_label)
                avg = avg.sort_values("apertura_doy", ascending=True)
                table = avg[["nome_stazione", "Apertura media", "Chiusura media"]].rename(
                    columns={"nome_stazione": "Impianto"}
                )
                # Messaggio guida solo quando nessun filtro è selezionato
                if livello == "nessuno" and profilo == "nessuno":
                    st.markdown("Consulta la tabella seguente per sapere quando le piste da sci si vestono di bianco")
                st.dataframe(table, use_container_width=True, hide_index=True)
        except Exception:
            pass
        return

    df_scored = apply_profile_adjustment(df_with_indices, livello, profilo)
    ranking = build_ranking(df_scored, "indice_finale")

    # Aggregated KPIs (mean over the window) for all stations
    df_kpis = aggregate_station_kpis(df_with_indices)

    # Best station name
    best_name = ranking.iloc[0]["nome_stazione"] if not ranking.empty else df_kpis.sort_values("km_open_est", ascending=False).iloc[0]["nome_stazione"]

    # Mostra risultati solo dopo il completamento dell'onboarding
    if st.session_state.onboarding_completed and data_sel and livello and livello != "nessuno":
        # Hero Section - Stazione consigliata
        st.markdown("""
        <div class="hero-container">
            <div class="hero-section">
                <p class="hero-subtitle">La migliore scelta per il tuo livello e profilo</p>
                <h1 class="hero-title">{}</h1>
            </div>
        </div>
        """.format(best_name), unsafe_allow_html=True)
        
        # Spazio extra per staccare dal bottone "Ricomincia"
        st.markdown('<div style="margin: 48px 0;"></div>', unsafe_allow_html=True)
        
        # KPI Grid
        st.markdown('<h2 class="section-header">📈 Indicatori chiave</h2>', unsafe_allow_html=True)
        
        k_row = (
            df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
            if not df_kpis.empty
            else None
        )
        
        if k_row is not None:
            # KPI Grid con layout centrato
            st.markdown(
                f"""
                <div class="kpi-grid grid-3">
                    {render_kpi("Km piste aperte stimati", f"{float(k_row.get('km_open_est', k_row.get('kmopen', 0) or 0)):.0f}", "km", "🎿")}
                    {render_kpi("% piste aperte (stima)", f"{float(k_row.get('pct_open', 0) or 0) * 100:.0f}", "%", "📈")}
                    {render_kpi("Probabilità impianto aperto", f"{float(k_row.get('open_prob', k_row.get('is_open', 0) or 0)) * 100:.0f}", "%", "✅")}
                </div>
                """,
                unsafe_allow_html=True
            )
    # end header cards

    # Map with highlight (solo per livelli diversi da "nessuno"; per "nessuno" la mostriamo più sotto)
    if livello != "nessuno" and not df_kpis.empty:
        base_coords = ensure_lat_lon(df_filtered_infonieve[["nome_stazione"] + [c for c in df_filtered_infonieve.columns if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")]].drop_duplicates())
        map_data = df_kpis.merge(base_coords, on="nome_stazione", how="left").dropna(subset=["lat", "lon"])
        if not map_data.empty:
            # Coordinate centrate sui Pirenei (Francia-Spagna)
            center_lat = 42.5  # Latitudine media dei Pirenei
            center_lon = 1.0   # Longitudine media dei Pirenei
            view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=6, pitch=0)

            def color_for_avalanche(x: float) -> List[int]:
                if x <= 2:
                    return [80, 220, 160, 180]
                if x <= 3:
                    return [240, 200, 80, 200]
                return [240, 100, 100, 220]

            map_data["color"] = map_data["avalanche"].fillna(3).apply(color_for_avalanche)
            map_data["radius"] = np.clip((map_data["km_open_est"].fillna(0) + 5) * 500, 3000, 15000)
            map_data["highlight"] = np.where(map_data["nome_stazione"] == best_name, 1, 0)
            best_pt = map_data[map_data["highlight"] == 1].copy()
            if not best_pt.empty:
                best_pt["star"] = "★"

            layer_all = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position='[lon, lat]',
                get_radius="radius",
                get_fill_color="color",
                pickable=True,
                auto_highlight=True,
            )
            # Ring per la consigliata (solo bordo, senza riempimento)
            ring_layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data[map_data["highlight"] == 1],
                get_position='[lon, lat]',
                get_radius="radius",
                stroked=True,
                filled=False,
                get_line_color='[0, 200, 255, 255]',
                line_width_min_pixels=2,
                pickable=False,
            )
            # Prova corona, fallback pallino verde
            crown_layer = None
            try:
                if not best_pt.empty:
                    best_pt["crown"] = "👑"
                    crown_layer = pdk.Layer(
                "TextLayer",
                data=best_pt,
                get_position='[lon, lat]',
                        get_text='crown',
                        get_size=32,
                get_color='[255,255,255,255]',
                get_angle=0,
                pickable=False,
            )
            except:
                # Fallback pallino verde + ring
                if not best_pt.empty:
                    green_layer = pdk.Layer(
                        "ScatterplotLayer",
                        data=best_pt,
                        get_position='[lon, lat]',
                        get_radius=15000,
                        get_fill_color='[0, 200, 0, 220]',
                        pickable=False,
                    )
                    crown_layer = green_layer
            
            layers_list = [layer_all, ring_layer]
            if crown_layer:
                layers_list.append(crown_layer)
            deck = pdk.Deck(layers=layers_list, initial_view_state=view_state, tooltip={"text": "{nome_stazione}\nKm aperti: {km_open_est}"})
            st.pydeck_chart(deck, use_container_width=True)

    # Space for separation (avoid redundant horizontal rule under caption)
    st.write("")
    # AI overview: disattivata quando livello == "nessuno"
    if livello != "nessuno":
        try:
            prompt = build_llm_prompt(df_kpis, best_name, livello, profilo, data_sel)
            output, usage = generate_overview(prompt, max_tokens=160)
            
            # Pulizia diretta e aggressiva del contenuto HTML
            import re
            clean_output = re.sub(r'<[^>]*>', '', str(output)).strip()
            clean_output = re.sub(r'\s+', ' ', clean_output)
            
            # AI Overview completo con box HTML e contenuto integrato
            st.markdown(f"""
            <div class="ai-overview-section">
                <div class="ai-header">
                    <div class="ai-header-text">
                        <div class="ai-title">AI Overview ✨</div>
                        <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                    </div>
                </div>
                <div class="ai-overview-content">{clean_output}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Errore nell'AI Overview: {e}")

    # Level-specific visualizations (no raw index shown)
    if livello == "base":
        # Divider e titolo principale sezione livello
        st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
        st.markdown('<h2 class="profile-main-title">🎿 Sezione Livello: Principiante</h2>', unsafe_allow_html=True)
        

        # Mappa con consigliata evidenziata
        st.markdown('<h4 class="section-subtitle">🗺️ Mappa delle stazioni (consigliata evidenziata)</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)

        # Podio Top 3 (estetico, senza esporre il valore indice)
        if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
            top3 = (df_with_indices.groupby("nome_stazione")["indice_base"].mean()
                    .sort_values(ascending=False).head(3).reset_index())
            if len(top3) > 0:
                st.markdown('<h4 class="section-subtitle">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                st.markdown(
                    render_podium(top3),
                    unsafe_allow_html=True
                )

        # Probabilità meteo (±3 giorni su anni precedenti per date future)
        from datetime import date as _date
        def create_speedometer(value_pct: float, title: str, color: str, reference_pct: float | None = None) -> go.Figure:
            indicator = go.Indicator(
                mode="gauge+number",
                value=max(0, min(100, value_pct)),
                title={"text": title, "font": {"size": 18, "color": "#f8fafc", "family": "Inter"}},
                number={
                    "suffix": "%", 
                    "font": {"size": 36, "color": "#f8fafc", "family": "Inter", "weight": 700}
                },
                gauge={
                    "axis": {
                        "range": [0, 100],
                        "tickwidth": 1,
                        "tickcolor": "#374151",
                        "tickfont": {"color": "#9ca3af", "size": 12, "family": "Inter"}
                    },
                    "bar": {"color": color, "thickness": 0.8},
                    "bgcolor": "#1f2937",
                    "borderwidth": 2,
                    "bordercolor": "#374151",
                    "steps": [
                        {"range": [0, 25], "color": "#0f172a"},
                        {"range": [25, 50], "color": "#1f2937"},
                        {"range": [50, 75], "color": "#374151"},
                        {"range": [75, 100], "color": "#4b5563"},
                    ],
                    "threshold": {
                        "line": {"color": color, "width": 4},
                        "thickness": 0.75,
                        "value": value_pct
                    }
                },
            )
            fig = go.Figure(indicator)
            
            # Delta migliorato per dark mode - posizionato sotto al numero principale
            if reference_pct is not None:
                delta_val = max(0, min(100, value_pct)) - max(0, min(100, reference_pct))
                fig.add_annotation(
                    x=0.5, y=0.35, xref="paper", yref="paper",
                    text=f"Δ {delta_val:+.1f}%", showarrow=False,
                    font=dict(size=14, color="#10b981" if delta_val < 0 else "#f59e0b", family="Inter", weight=600),
                    bgcolor="rgba(15, 23, 42, 0.9)",
                    bordercolor="#374151",
                    borderwidth=1,
                    borderpad=6
                )
            
            fig.update_layout(
                height=280, 
                margin=dict(l=20, r=20, t=40, b=40),
                template=plotly_template,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#f8fafc")
            )
            return fig

        # Dati meteo correnti/previsti (±3 giorni) sempre da storico per coerenza
        meteo_data = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=3)
        if not meteo_data.empty:
            st.markdown('<h4 class="section-subtitle">🌤️ Probabilità condizioni meteo (storico ±3 giorni)</h4>', unsafe_allow_html=True)
            # baseline ±15 giorni sugli anni precedenti
            baseline = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=15)
            col1, col2 = st.columns(2)
            with col1:
                prob_nebbia = float(meteo_data.get("nebbia", 0).mean() * 100)
                baseline_nebbia = float((baseline.get("nebbia", 0).mean() * 100) if not baseline.empty else 0)
                fig_n = create_speedometer(prob_nebbia, "Prob. Nebbia", "#6b7280", reference_pct=baseline_nebbia)
                st.plotly_chart(fig_n, use_container_width=True)
            with col2:
                prob_pioggia = float(meteo_data.get("pioggia", 0).mean() * 100)
                baseline_pioggia = float((baseline.get("pioggia", 0).mean() * 100) if not baseline.empty else 0)
                fig_p = create_speedometer(prob_pioggia, "Prob. Pioggia", "#06b6d4", reference_pct=baseline_pioggia)
                st.plotly_chart(fig_p, use_container_width=True)
            st.markdown(
                '<div style="text-align: center; margin-top: 20px; margin-bottom: 30px;">'
                '<p style="font-size: 14px; color: #94a3b8; font-family: Inter, sans-serif; font-style: italic; margin: 0;">'
                'Nota: probabilità calcolate sui dati storici per periodi simili; il delta confronta con la media degli anni precedenti nella finestra ±15 giorni.'
                '</p></div>',
                unsafe_allow_html=True
            )
        else:
            st.warning("Dati meteo non disponibili per questa data")

        # Barre impilate piste verdi/blu ordinate per indice_base
        if not df_with_indices.empty and "indice_base" in df_with_indices.columns:
            st.markdown('<h4 class="section-subtitle">🎿 Distribuzione piste verdi e blu</h4>', unsafe_allow_html=True)
            # Raggruppa per stazione per evitare duplicazioni (un valore per stazione)
            piste_base = (
                df_with_indices[["nome_stazione", "Piste_verdi", "Piste_blu", "indice_base"]]
                .groupby("nome_stazione")
                .agg({
                    "Piste_verdi": "first",  # Prende il primo valore (sono uguali per stazione)
                    "Piste_blu": "first",
                    "indice_base": "mean"    # Media dell'indice se varia per data
                })
                .reset_index()
                .sort_values("indice_base", ascending=False)
            )
            fig_piste_base = px.bar(
                piste_base,
                x="nome_stazione",
                y=["Piste_verdi", "Piste_blu"],
                title="Piste verdi e blu per stazione (ordinate per indice base)",
                color_discrete_map={"Piste_verdi": "#10b981", "Piste_blu": "#06b6d4"},
                barmode="group"
            )
            fig_piste_base.update_layout(
                xaxis_tickangle=-45,
                template=plotly_template,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#f8fafc"),
                title=dict(font=dict(size=16, family="Inter", color="#f8fafc")),
                xaxis=dict(
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                yaxis=dict(
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                legend=dict(
                    font=dict(color="#f8fafc", family="Inter")
                )
            )
            st.plotly_chart(fig_piste_base, use_container_width=True)

        # Sezione Festaiolo (profilo) – solo se selezionato
        if profilo_norm == "festaiolo":
            # Divider e titolo sezione profilo
            st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
            st.markdown('<h2 class="profile-main-title">🎉 Sezione Profilo: Festaiolo</h2>', unsafe_allow_html=True)
            
            # AI Overview per profilo festaiolo (PRIMA dei grafici)
            try:
                prompt_festaiolo = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_festaiolo, max_tokens=140)
                
                # Pulizia diretta e aggressiva del contenuto HTML
                clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
                clean_out = re.sub(r'\s+', ' ', clean_out)
                
                st.markdown(f"""
                <div class="ai-overview-section">
                    <div class="ai-header">
                        <div class="ai-header-text">
                            <div class="ai-title">AI Overview ✨</div>
                            <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                        </div>
                    </div>
                    <div class="ai-overview-content">{clean_out}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore nell'AI Overview Festaiolo: {e}")
            
            # Titolo per i grafici specifici del profilo
            st.markdown('<h4 class="section-subtitle">📊 Analisi specifica per festaioli</h4>', unsafe_allow_html=True)
            # Grafico 1: km di sci notturno (asse X), impianti su Y
            try:
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Km di sci notturno per impianto",
                        labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"},
                        text="Scii_notte"
                    )
                    fig_night.update_traces(texttemplate='%{text:.0f} km', textposition='outside')
                    fig_night.update_layout(
                        xaxis_tickangle=-45,
                        template=plotly_template
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass



        if profilo_norm == "familiare":
            # Divider e titolo sezione profilo
            st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
            st.markdown('<h2 class="profile-main-title">👨‍👩‍👧‍👦 Sezione Profilo: Familiare</h2>', unsafe_allow_html=True)
            
            # AI Overview per profilo familiare (PRIMA dei grafici)
            try:
                prompt_family = build_familiare_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_family, max_tokens=140)
                
                # Pulizia diretta e aggressiva del contenuto HTML
                clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
                clean_out = re.sub(r'\s+', ' ', clean_out)
                
                st.markdown(f"""
                <div class="ai-overview-section">
                    <div class="ai-header">
                        <div class="ai-header-text">
                            <div class="ai-title">AI Overview ✨</div>
                            <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                        </div>
                    </div>
                    <div class="ai-overview-content">{clean_out}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore nell'AI Overview Famiglia: {e}")
            
            # Titolo per i grafici specifici del profilo
            st.markdown('<h4 class="section-subtitle">📊 Analisi specifica per famiglie</h4>', unsafe_allow_html=True)
            
            # 1) Numero aree bambini per impianto
            try:
                if "Area_bambini" in df_with_indices.columns:
                    df_kids = (
                        df_with_indices[["nome_stazione", "Area_bambini"]]
                        .drop_duplicates().fillna(0)
                        .sort_values("Area_bambini", ascending=False)
                    )
                    fig_kids = px.bar(
                        df_kids,
                        x="nome_stazione", y="Area_bambini",
                        title="Numero aree bambini per impianto",
                        labels={"nome_stazione": "Impianto", "Area_bambini": "Aree bambini"}
                    )
                    fig_kids.update_layout(
                        xaxis_tickangle=-45,
                        template=plotly_template
                    )
                    st.plotly_chart(fig_kids, use_container_width=True)
                else:
                    st.info("Dato non disponibile: 'Area_bambini'")
            except Exception:
                pass

            # 2) Prezzi medi per impianto (skipass, scuola, noleggio)
            try:
                price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
                if price_cols:
                    df_price = (
                        df_with_indices[["nome_stazione"] + price_cols]
                        .drop_duplicates().fillna(0)
                    )
                    melted_p = df_price.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                    # Rimuovi underscore dalle label
                    melted_p["Voce"] = melted_p["Voce"].replace({
                        "Prezzo_skipass": "Prezzo skipass",
                        "Prezzo_scuola": "Prezzo scuola", 
                        "Prezzo_noleggio": "Prezzo noleggio"
                    })
                    fig_prices = px.bar(
                        melted_p,
                        x="nome_stazione", y="Prezzo", color="Voce",
                        barmode="group",
                        title="Prezzi medi per impianto (skipass, scuola, noleggio)",
                        labels={"nome_stazione": "Impianto", "Prezzo": "€"}
                    )
                    fig_prices.update_layout(
                        template=plotly_template,
                        xaxis_tickangle=-45
                    )
                    st.plotly_chart(fig_prices, use_container_width=True)
                else:
                    st.info("Dati prezzo non disponibili (skipass/scuola/noleggio)")
            except Exception:
                pass

    elif livello == "medio":
        # Divider e titolo principale sezione livello
        st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
        st.markdown('<h2 class="profile-main-title">🎿 Sezione Livello: Intermedio</h2>', unsafe_allow_html=True)
        

        # Mappa con consigliata evidenziata
        st.markdown('<h4 class="section-subtitle">🗺️ Mappa delle stazioni (consigliata evidenziata)</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)

        # Podio Top 3 per indice_medio
        if "indice_medio" in df_with_indices.columns and not df_with_indices.empty:
            top3m = (
                df_with_indices.groupby("nome_stazione")["indice_medio"].mean()
                .sort_values(ascending=False).head(3).reset_index()
            )
            if not top3m.empty:
                names = top3m["nome_stazione"].tolist()
                first = names[0] if len(names) > 0 else ""
                second = names[1] if len(names) > 1 else ""
                third = names[2] if len(names) > 2 else ""
                st.markdown('<h4 class="section-subtitle">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class='podium-container'>
                      <div class='podium-step second'>
                        <div class='podium-platform second'>
                          <div class='podium-medal'>🥈</div>
                          <div class='name'>{second}</div>
                        </div>
                      </div>
                      <div class='podium-step first'>
                        <div class='podium-platform first'>
                          <div class='podium-medal'>🥇</div>
                          <div class='name'>{first}</div>
                        </div>
                      </div>
                      <div class='podium-step third'>
                        <div class='podium-platform third'>
                          <div class='podium-medal'>🥉</div>
                          <div class='name'>{third}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Meteo compatto (5 mini-donut) per la stazione consigliata
        try:
            meteo_win = get_historical_data_for_date(df_filtered_meteo, data_sel, days_range=3)
            if not meteo_win.empty:
                m_best = meteo_win[meteo_win.get("nome_stazione", "").astype(str) == best_name]
                if m_best.empty:
                    m_best = meteo_win
                pioggia = float(m_best.get("pioggia", 0).mean() * 100)
                nebbia = float(m_best.get("nebbia", 0).mean() * 100)
                sole    = float(m_best.get("sole", 0).mean() * 100)
                vento   = float(m_best.get("vento", 0).mean() * 100)
                neve_pct = 0.0
                snow_win = get_historical_data_for_date(df_filtered_infonieve, data_sel, days_range=3)
                if not snow_win.empty:
                    s_best = snow_win[snow_win.get("nome_stazione", "").astype(str) == best_name]
                    if s_best.empty:
                        s_best = snow_win
                    cm = s_best.get("espesor_medio", 0).fillna(0)
                    if not cm.empty:
                        cmin, cmax = cm.min(), cm.max()
                        neve_pct = float(((cm.mean() - cmin) / (cmax - cmin) * 100) if cmax > cmin else 0)

                def donut(value, label, color):
                    val = max(0.0, min(100.0, value))
                    rem = 100 - val
                    fig = go.Figure(
                        data=[go.Pie(values=[val, rem], hole=0.72, sort=False, direction='clockwise', marker_colors=[color, 'rgba(255,255,255,0.08)'], textinfo='none')]
                    )
                    fig.add_annotation(text=f"{val:.0f}%", x=0.5, y=0.5, showarrow=False, font=dict(size=22, color='#e6efff'))
                    fig.update_layout(
                        title=dict(text=label, font=dict(size=16), y=0.9),
                        showlegend=False, margin=dict(l=0, r=0, t=50, b=10), height=220
                    )
                    return fig

                st.markdown('<h4 class="section-subtitle">🌤️ Meteo (storico ±3 giorni)</h4>', unsafe_allow_html=True)
                r1c1, r1c2, r1c3 = st.columns(3)
                with r1c1:
                    st.plotly_chart(donut(pioggia, "Pioggia", "#60A5FA"), use_container_width=True)
                with r1c2:
                    st.plotly_chart(donut(sole, "Sole", "#F59E0B"), use_container_width=True)
                with r1c3:
                    st.plotly_chart(donut(nebbia, "Nebbia", "#94a3b8"), use_container_width=True)
                st.write("")
                r2c1, r2c2, r2c3 = st.columns([1,1,1])
                with r2c1:
                    st.plotly_chart(donut(vento, "Vento", "#00C8FF"), use_container_width=True)
                with r2c2:
                    st.plotly_chart(donut(neve_pct, "Neve", "#6EE7B7"), use_container_width=True)
                with r2c3:
                    st.write("")
        except Exception:
            pass

        # Mappa delle stazioni (con evidenza della consigliata)
        try:
            if not df_with_indices.empty:
                base_coords = ensure_lat_lon(
                    df_filtered_infonieve[["nome_stazione"] + [
                        c for c in df_filtered_infonieve.columns
                        if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")
                    ]].drop_duplicates()
                )
                map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
                if not map_data.empty:
                    map_data["highlight"] = (map_data["nome_stazione"] == best_name).astype(int)
                    center_lat = map_data["lat"].mean()
                    center_lon = map_data["lon"].mean()
                    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=7, pitch=0)

                    layer_all = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_data,
                        get_position='[lon, lat]',
                        get_radius=8000,
                        get_fill_color='[255, 0, 0, 140]'
                    )
                    layer_best = pdk.Layer(
                        "ScatterplotLayer",
                        data=map_data[map_data["highlight"] == 1],
                        get_position='[lon, lat]',
                        get_radius=12000,
                        get_fill_color='[0, 200, 255, 200]'
                    )
                    deck = pdk.Deck(
                        layers=[layer_all, layer_best],
                        initial_view_state=view_state,
                        tooltip={"text": "{nome_stazione}"}
                    )
                    st.pydeck_chart(deck, use_container_width=True)
        except Exception:
            pass

        # Barre: piste blu/rosse ordinate per indice_medio
        if not df_with_indices.empty and "indice_medio" in df_with_indices.columns:
            st.markdown('<h4 class="section-subtitle">🎿 Piste blu e rosse per stazione</h4>', unsafe_allow_html=True)
            # Raggruppa per stazione per evitare duplicazioni (un valore per stazione)
            piste = (
                df_with_indices[["nome_stazione", "Piste_blu", "Piste_rosse", "indice_medio"]]
                .groupby("nome_stazione")
                .agg({
                    "Piste_blu": "first",    # Prende il primo valore (sono uguali per stazione)
                    "Piste_rosse": "first",
                    "indice_medio": "mean"   # Media dell'indice se varia per data
                })
                .reset_index()
                .sort_values("indice_medio", ascending=False)
            )
            melted = piste.melt("nome_stazione", value_vars=["Piste_blu", "Piste_rosse"], var_name="Tipo", value_name="Numero")
            fig = px.bar(
                melted,
                x="nome_stazione", y="Numero", color="Tipo", barmode="group",
                color_discrete_map={"Piste_blu": "#06b6d4", "Piste_rosse": "#ef4444"},
            )
            fig.update_layout(
                xaxis_tickangle=-45,
                template=plotly_template,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#f8fafc"),
                xaxis=dict(
                    title="Stazione",
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                yaxis=dict(
                    title="Numero piste",
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                legend=dict(
                    font=dict(color="#f8fafc", family="Inter")
                )
            )
            st.plotly_chart(fig, use_container_width=True)

        # Sezione Festaiolo (profilo)
        if profilo_norm == "festaiolo":
            st.markdown('<h4 class="section-subtitle">🎉 Profilo: Festaiolo</h4>', unsafe_allow_html=True)
            try:
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Km di sci notturno per impianto",
                        labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"}
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass
            try:
                cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                if not df_acts.empty:
                    melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Attività", value_name="Valore")
                    fig_acts = px.bar(
                        melted, x="nome_stazione", y="Valore", color="Attività",
                        barmode="group", title="Snowpark e Superpipe"
                    )
                    fig_acts.update_layout(
                        xaxis_tickangle=-45,
                        template=plotly_template
                    )
                    st.plotly_chart(fig_acts, use_container_width=True)
            except Exception:
                pass
            try:
                prompt_f = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                st.markdown('<h4 class="section-subtitle">🤖 AI Overview – Festa</h4>', unsafe_allow_html=True)
                out, usage = generate_overview(prompt_f, max_tokens=140)
                
                # Pulizia diretta e aggressiva del contenuto HTML
                clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
                clean_out = re.sub(r'\s+', ' ', clean_out)
                
                st.markdown(f"""
                <div class="ai-overview-section">
                    <div class="ai-header">
                        <div class="ai-header-text">
                            <div class="ai-title">AI Overview ✨</div>
                            <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                </div>
                    </div>
                    <div class="ai-overview-content">{clean_out}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore nell'AI Overview Festaiolo: {e}")

    elif livello == "esperto":
        # Divider e titolo principale sezione livello
        st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
        st.markdown('<h2 class="profile-main-title">⛷️ Sezione Livello: Esperto</h2>', unsafe_allow_html=True)
        

        
        # Mappa centrata sui Pirenei
        st.markdown('<h4 class="section-subtitle">🗺️ Mappa delle stazioni</h4>', unsafe_allow_html=True)
        render_map_with_best(df_with_indices, best_name)

        # Podio Top 3 per indice_esperto
        if not df_with_indices.empty and "indice_esperto" in df_with_indices.columns:
            top3e = (
                df_with_indices.groupby("nome_stazione")["indice_esperto"].mean()
                .sort_values(ascending=False).head(3).reset_index()
            )
            if not top3e.empty:
                names = top3e["nome_stazione"].tolist()
                first = names[0] if len(names) > 0 else ""
                second = names[1] if len(names) > 1 else ""
                third = names[2] if len(names) > 2 else ""
                st.markdown('<h4 class="section-subtitle">🏆 Classifica Top 3</h4>', unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class='podium-container'>
                      <div class='podium-step second'>
                        <div class='podium-platform second'>
                          <div class='podium-medal'>🥈</div>
                          <div class='name'>{second}</div>
                        </div>
                      </div>
                      <div class='podium-step first'>
                        <div class='podium-platform first'>
                          <div class='podium-medal'>🥇</div>
                          <div class='name'>{first}</div>
                        </div>
                      </div>
                      <div class='podium-step third'>
                        <div class='podium-platform third'>
                          <div class='podium-medal'>🥉</div>
                          <div class='name'>{third}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Speedometer rischio valanghe (1-5) per la stazione consigliata (con delta vs baseline ±15g)
        try:
            brow = df_kpis[df_kpis["nome_stazione"] == best_name].iloc[0]
            risk = float(brow.get("avalanche", 3.0))
            # baseline: media danger_level_avg nella finestra ±15 giorni su anni precedenti
            base_val = get_historical_data_for_date(df_filtered_val, data_sel, days_range=15)
            bstation = base_val[base_val.get("nome_stazione", "").astype(str) == best_name]
            baseline = float(bstation.get("danger_level_avg", 0).mean()) if not bstation.empty else 0.0
            # Due livelli: subheader esterno e delta in basso, numero centrato
            d = risk - baseline
            st.markdown('<h4 class="section-subtitle">⚠️ Rischio valanghe (1-5)</h4>', unsafe_allow_html=True)
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Indicator(
                mode="gauge+number",
                value=risk,
                number={"font": {"size": 48, "color": "#f8fafc"}},
                gauge={
                    "axis": {"range": [1, 5]},
                    "bar": {"color": "#ef4444"},
                    "steps": [
                        {"range": [1, 2], "color": "#16a34a"},
                        {"range": [2, 3], "color": "#f59e0b"},
                        {"range": [3, 5], "color": "#7f1d1d"},
                    ],
                },
                domain={"x": [0, 1], "y": [0.2, 1]}
            ))
            # Delta come annotation molto in basso
            fig_risk.add_annotation(x=0.5, y=0.05, xref="paper", yref="paper",
                                    text=f"Δ {d:+.2f} vs media ±15g", showarrow=False,
                                    font=dict(size=12, color="#16a34a" if d < 0 else "#ef4444"))
            fig_risk.update_layout(
                height=260, 
                margin=dict(l=10, r=10, t=24, b=24),
                template=plotly_template
            )
            st.plotly_chart(fig_risk, use_container_width=True)
            
            # Disclaimer rischio valanghe
            st.markdown("""
            L'indice di valanghe, conosciuto come Scala Europea del Pericolo di Valanghe, è uno strumento a 5 livelli utilizzato per valutare e comunicare il rischio di valanghe (0=basso, 5=molto alto).
            """)
        except Exception:
            pass

        # KPI tecnici (stazione consigliata)
        try:
            top_best = df_with_indices[df_with_indices["nome_stazione"] == best_name]
            if not top_best.empty:
                st.markdown('<h3 class="section-subtitle">🎯 KPI tecnici</h3>', unsafe_allow_html=True)
                vals = top_best[["Snowpark", "Area_gare", "Slalom", "Superpipe"]].fillna(0).mean()
                
                # KPI Grid per KPI tecnici con layout uniformi - 4 colonne su una riga
                st.markdown(
                    f"""
                    <div class="kpi-grid grid-4">
                        {render_kpi("Snowpark", f"{vals.get('Snowpark',0):.0f}", "", "🛹")}
                        {render_kpi("Area gare", f"{vals.get('Area_gare',0):.0f}", "", "🏁")}
                        {render_kpi("Slalom", f"{vals.get('Slalom',0):.0f}", "", "⛷️")}
                        {render_kpi("Superpipe", f"{vals.get('Superpipe',0):.0f}", "", "🏂")}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        except Exception:
            pass

        # Quota max: grafico a barre (Top 10) con scala 2000-3000 m
        try:
            quota = (
                df_with_indices.groupby("nome_stazione")["Quota_max"].mean().dropna().sort_values(ascending=False).head(10).reset_index()
            )
            if not quota.empty:
                fig_quota = px.bar(
                    quota, 
                    x="nome_stazione", 
                    y="Quota_max", 
                    title="Quota max per stazione", 
                    labels={"nome_stazione": "Stazione", "Quota_max": "Quota max (m)"},
                    text="Quota_max"
                )
                fig_quota.update_traces(texttemplate='%{text:.0f} m', textposition='outside')
                fig_quota.update_layout(
                    xaxis_tickangle=-45, 
                    yaxis=dict(range=[2000, 2800]),
                    template=plotly_template
                )
                st.plotly_chart(fig_quota, use_container_width=True)
        except Exception:
            pass

        # Km totali: solo totali per le prime 8 stazioni
        top_total = df_kpis.sort_values("km_total_est", ascending=False).head(8)
        fig_bar_total = px.bar(
            top_total, 
            x="nome_stazione", 
            y="km_total_est", 
            title="Km piste totali", 
            labels={"nome_stazione": "Stazione", "km_total_est": "Km totali"},
            text="km_total_est"
        )
        fig_bar_total.update_traces(texttemplate='%{text:.0f} km', textposition='outside')
        fig_bar_total.update_layout(
            xaxis_tickangle=-45,
            template=plotly_template
        )
        st.plotly_chart(fig_bar_total, use_container_width=True)

        if profilo_norm == "festaiolo":
            st.markdown('<h4 class="section-subtitle">🎉 Profilo: Festaiolo</h4>', unsafe_allow_html=True)
            try:
                df_night = df_with_indices[["nome_stazione", "Scii_notte"]].drop_duplicates().fillna(0)
                if not df_night.empty:
                    fig_night = px.bar(
                        df_night.sort_values("Scii_notte", ascending=False),
                        x="nome_stazione", y="Scii_notte",
                        title="Km di sci notturno per impianto",
                        labels={"Scii_notte": "Km sci notturno", "nome_stazione": "Impianto"}
                    )
                    st.plotly_chart(fig_night, use_container_width=True)
            except Exception:
                pass
            try:
                cols = [c for c in ["Snowpark", "Superpipe"] if c in df_with_indices.columns]
                df_acts = df_with_indices[["nome_stazione"] + cols].drop_duplicates().fillna(0)
                if not df_acts.empty:
                    melted = df_acts.melt("nome_stazione", value_vars=cols, var_name="Attività", value_name="Valore")
                    fig_acts = px.bar(
                        melted, x="nome_stazione", y="Valore", color="Attività",
                        barmode="group", title="Snowpark e Superpipe"
                    )
                    fig_acts.update_layout(
                        xaxis_tickangle=-45,
                        template=plotly_template
                    )
                    st.plotly_chart(fig_acts, use_container_width=True)
            except Exception:
                pass
            
            # AI Overview – Festa
            st.markdown('<h4 class="section-subtitle">🤖 AI Overview – Festa</h4>', unsafe_allow_html=True)
            try:
                prompt_festaiolo = build_festaiolo_prompt(df_filtered_rec, best_name, livello, data_sel)
                out, usage = generate_overview(prompt_festaiolo, max_tokens=140)
                
                # Pulizia diretta e aggressiva del contenuto HTML
                clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
                clean_out = re.sub(r'\s+', ' ', clean_out)
                
                st.markdown(f"""
                <div class="ai-overview-section">
                    <div class="ai-header">
                        <div class="ai-header-text">
                            <div class="ai-title">AI Overview ✨</div>
                            <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                        </div>
                    </div>
                    <div class="ai-overview-content">{clean_out}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore nell'AI Overview Festaiolo: {e}")




    else:  # nessuno (panoramica base)
        # Divider e titolo principale sezione livello
        st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)
        st.markdown('<h2 class="profile-main-title">🏔️ Sezione Livello: Panoramica Generale</h2>', unsafe_allow_html=True)
        
        # Titolo sezione livello
        st.subheader("Panoramica generale")
        # Grafico a barre: numero piste per tipologia per impianto (stacked)
        piste_cols = ["Piste_verdi", "Piste_blu", "Piste_rosse", "Piste_nere"]
        if set(piste_cols).issubset(df_with_indices.columns):
            piste_counts = (
                df_with_indices[["nome_stazione"] + piste_cols]
                .drop_duplicates()
                .fillna(0)
            )
            # Ordine per impianti con più piste aperte (se disponibile kmopen), altrimenti per somma piste
            if "kmopen" in df_with_indices.columns:
                km_order = (
                    df_with_indices.groupby("nome_stazione")["kmopen"].mean().sort_values(ascending=False).index.tolist()
                )
                order = km_order
            else:
                piste_counts["tot_piste"] = (
                    piste_counts["Piste_verdi"]
                    + piste_counts["Piste_blu"]
                    + piste_counts["Piste_rosse"]
                    + piste_counts["Piste_nere"]
                )
                order = piste_counts.sort_values("tot_piste", ascending=False)["nome_stazione"].tolist()
            rename_map = {
                "Piste_verdi": "Piste verdi",
                "Piste_blu": "Piste blu",
                "Piste_rosse": "Piste rosse",
                "Piste_nere": "Piste nere",
            }
            melted = piste_counts.rename(columns=rename_map).melt(
                "nome_stazione",
                value_vars=list(rename_map.values()),
                var_name="Tipo",
                value_name="Numero",
            )
            color_map = {
                "Piste verdi": "#10b981",
                "Piste blu": "#06b6d4",
                "Piste rosse": "#ef4444",
                "Piste nere": "#374151",
            }
            fig_stack = px.bar(
                melted,
                x="nome_stazione",
                y="Numero",
                color="Tipo",
                barmode="stack",
                title="Numero piste per impianto e tipologia",
                color_discrete_map=color_map,
                category_orders={"nome_stazione": order},
            )
            fig_stack.update_layout(
                xaxis_tickangle=-45,
                template=plotly_template,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#f8fafc"),
                xaxis=dict(
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                yaxis=dict(
                    gridcolor="#374151",
                    tickfont=dict(color="#d1d5db", family="Inter")
                ),
                legend=dict(
                    font=dict(color="#f8fafc", family="Inter")
                )
            )
            st.plotly_chart(fig_stack, use_container_width=True)

        # Mappa degli impianti (centrata sulla zona) - versione semplice senza highlight in "nessuno"
        st.subheader("Mappa delle stazioni sciistiche")
        if not df_with_indices.empty:
            map_data = df_with_indices[["nome_stazione", "lat", "lon"]].drop_duplicates().dropna()
            if map_data.empty:
                # fallback su merge se lat/lon non presenti direttamente
                base_coords = ensure_lat_lon(
                    df_filtered_infonieve[["nome_stazione"] + [c for c in df_filtered_infonieve.columns if c.lower() in ("lat","latitude","latitudine","lon","lng","long","longitude","longitudine")]].drop_duplicates()
                )
                map_data = base_coords.dropna(subset=["lat", "lon"]).copy()
            if not map_data.empty:
                # Coordinate centrate sui Pirenei
                center_lat = 42.5
                center_lon = 1.0
                view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=6, pitch=0)
                layer_all = pdk.Layer(
                    "ScatterplotLayer",
                    data=map_data,
                    get_position='[lon, lat]',
                    get_radius=8000,
                    get_fill_color='[255, 0, 0, 140]',
                    pickable=True,
                    auto_highlight=True,
                )
                deck = pdk.Deck(layers=[layer_all], initial_view_state=view_state, tooltip={"text": "{nome_stazione}"})
                st.pydeck_chart(deck, use_container_width=True)

        # Messaggio guida per profili senza livello
        if profilo_norm != "nessuno":
            if profilo_norm == "festaiolo":
                st.info("Seleziona un livello (Base/Medio/Esperto) per vedere la dashboard 'Festaiolo'.")
        else:
            st.info("Seleziona un profilo per avere informazioni più approfondite")

        # Trend spessore medio per tutti gli impianti, con focus selezionabile
        st.subheader("Trend spessore neve (tutti gli impianti)")
        try:
            anno = (pd.to_datetime(data_sel).year) - 1
            start = pd.Timestamp(anno, 11, 1)
            end = pd.Timestamp(anno + 1, 5, 1)
            history = df_filtered_infonieve[(df_filtered_infonieve["date"] >= start) & (df_filtered_infonieve["date"] < end)].dropna(subset=["espesor_medio"]).copy()
            if not history.empty:
                stations = sorted(history["nome_stazione"].unique().tolist())
                focus = st.selectbox("Evidenzia impianto", options=["(Nessuno)"] + stations, index=0)
                solo = st.checkbox("Mostra solo impianto selezionato", value=False)
                palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set3 + px.colors.qualitative.T10
                color_cycle = {name: palette[i % len(palette)] for i, name in enumerate(stations)}
                fig_lines = go.Figure()
                for name, grp in history.groupby("nome_stazione"):
                    if solo and focus != "(Nessuno)" and name != focus:
                        continue
                    if focus != "(Nessuno)" and name != focus:
                        color = "rgba(160,160,160,0.25)"
                        width = 1
                        opacity = 1.0
                    else:
                        color = color_cycle[name]
                        width = 2.4 if focus == name else 1.8
                        opacity = 0.98
                    fig_lines.add_trace(
                        go.Scatter(
                            x=grp["date"],
                            y=grp["espesor_medio"],
                            mode="lines",
                            name=name,
                            line=dict(color=color, width=width),
                            opacity=opacity,
                        )
                    )
                fig_lines.update_layout(xaxis_title="Data", yaxis_title="Spessore medio (cm)")
                st.plotly_chart(fig_lines, use_container_width=True)
        except Exception:
            pass

    # --- Sezione finale: classifiche semplici per livello e profilo ---
    
    # Sezione Profilo Low-Cost (solo se selezionato, dopo tutti i livelli)
    if profilo_norm == "lowcost":
        # Divider e titolo principale sezione profilo
        st.markdown('<hr class="profile-divider">', unsafe_allow_html=True)

        
        # Titolo sezione profilo
        st.markdown('<h2 class="profile-main-title">💰 Sezione Profilo: Low-Cost</h2>', unsafe_allow_html=True)
        
        # AI Overview per profilo low-cost (PRIMA dei grafici)
        try:
            prompt_lowcost = build_lowcost_prompt(df_filtered_rec, best_name, livello, data_sel)
            out, usage = generate_overview(prompt_lowcost, max_tokens=140)
            
            # Pulizia diretta e aggressiva del contenuto HTML
            clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
            clean_out = re.sub(r'\s+', ' ', clean_out)
            
            st.markdown(f"""
            <div class="ai-overview-section">
                <div class="ai-header">
                    <div class="ai-header-text">
                        <div class="ai-title">AI Overview ✨</div>
                        <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
                    </div>
                </div>
                <div class="ai-overview-content">{clean_out}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Errore nell'AI Overview Low-Cost: {e}")
        
        # Titolo per i grafici specifici del profilo
        st.markdown('<h4 class="section-subtitle">📊 Analisi specifica per low-cost</h4>', unsafe_allow_html=True)
        
        # 1) Grafico a barre: costi di ski pass, scuola sci e noleggio
        try:
            price_cols = [c for c in ["Prezzo_skipass", "Prezzo_scuola", "Prezzo_noleggio"] if c in df_with_indices.columns]
            
            if price_cols:
                df_price_lowcost = (
                    df_with_indices[["nome_stazione"] + price_cols]
                    .drop_duplicates().fillna(0)
                )
                # Ordina per prezzo medio totale
                df_price_lowcost["prezzo_medio"] = df_price_lowcost[price_cols].mean(axis=1)
                df_price_lowcost = df_price_lowcost.sort_values("prezzo_medio", ascending=True)
                
                melted_prices = df_price_lowcost.melt("nome_stazione", value_vars=price_cols, var_name="Voce", value_name="Prezzo")
                fig_prices_lowcost = px.bar(
                    melted_prices,
                    x="nome_stazione", y="Prezzo", color="Voce",
                    barmode="group",
                    title="💰 Costi per impianto (skipass, scuola, noleggio) - Ordine crescente per prezzo medio",
                    labels={"nome_stazione": "Impianto", "Prezzo": "€", "Voce": "Tipo costo"},
                    color_discrete_map={"Prezzo_skipass": "#FF6B6B", "Prezzo_scuola": "#4ECDC4", "Prezzo_noleggio": "#45B7D1"}
                )
                fig_prices_lowcost.update_layout(
                    xaxis_tickangle=-45,
                    template=plotly_template
                )
                st.plotly_chart(fig_prices_lowcost, use_container_width=True)
            else:
                st.info("Dati prezzo non disponibili per l'analisi low-cost")
        except Exception as e:
            st.warning(f"Errore nella visualizzazione prezzi: {e}")
        
        # 2) Tabella rapporto kmopen/costo skipass
        try:
            if not df_with_indices.empty and "kmopen" in df_with_indices.columns and "Prezzo_skipass" in df_with_indices.columns:
                # Raggruppa per stazione e calcola le medie per avere una riga per stazione
                df_ratio = (
                    df_with_indices.groupby("nome_stazione")
                    .agg({
                        "kmopen": "mean",
                        "Prezzo_skipass": "mean"
                    })
                    .reset_index()
                    .dropna()
                )
                
                if not df_ratio.empty:
                    # Imputa kmopen per Saint-Lary usando regressione kmopen vs kmtotal
                    try:
                        from sklearn.linear_model import LinearRegression
                        
                        # Prepara dati per il training (escludi Saint-Lary e considera solo idestado=1)
                        df_train = df_with_indices[
                            (df_with_indices["nome_stazione"] != "Saint-Lary") & 
                            (df_with_indices["idestado"] == 1) &
                            (df_with_indices["kmopen"] > 0) &
                            (df_with_indices["kmtotal"] > 0)
                        ].copy()
                        
                        if len(df_train) >= 3:  # Serve almeno 3 punti per la regressione
                            # Crea features per la regressione: kmtotal vs kmopen
                            X_train = df_train[["kmtotal"]].values
                            y_train = df_train["kmopen"].values
                            
                            # Addestra il modello di regressione lineare
                            model = LinearRegression()
                            model.fit(X_train, y_train)
                            
                            # Predici kmopen per Saint-Lary usando il suo kmtotal
                            saint_lary_data = df_with_indices[
                                (df_with_indices["nome_stazione"] == "Saint-Lary") & 
                                (df_with_indices["idestado"] == 1)
                            ]
                            
                            if not saint_lary_data.empty and "kmtotal" in saint_lary_data.columns:
                                saint_lary_kmtotal = saint_lary_data["kmtotal"].mean()
                                
                                if saint_lary_kmtotal > 0:
                                    # Predici kmopen per Saint-Lary
                                    predicted_kmopen = model.predict([[saint_lary_kmtotal]])[0]
                                    
                                    # Aggiorna il valore di kmopen per Saint-Lary nella tabella
                                    df_ratio.loc[df_ratio["nome_stazione"] == "Saint-Lary", "kmopen"] = max(0, predicted_kmopen)
                                else:
                                    st.warning("⚠️ Saint-Lary non ha kmtotal > 0 per l'imputazione")
                            else:
                                st.warning("⚠️ Dati Saint-Lary non trovati per l'imputazione")
                        else:
                            st.warning("⚠️ Dati insufficienti per l'imputazione (servono almeno 3 stazioni con kmopen > 0 e kmtotal > 0)")
                    except Exception as e:
                        st.warning(f"⚠️ Errore nell'imputazione: {e}")
                    
                    # Calcola il rapporto euro/km (costo per chilometro di pista)
                    df_ratio["rapporto_euro_km"] = np.where(
                        df_ratio["kmopen"] > 0,
                        df_ratio["Prezzo_skipass"] / df_ratio["kmopen"],
                        0
                    )
                    
                    # Ordina per rapporto migliore (meno euro per km = migliore rapporto)
                    df_ratio = df_ratio.sort_values("rapporto_euro_km", ascending=True)
                    
                    # Prepara tabella finale
                    df_table = df_ratio[["nome_stazione", "Prezzo_skipass", "kmopen", "rapporto_euro_km"]].copy()
                    
                    # Rinomina colonne per la visualizzazione
                    rename_map = {
                        "nome_stazione": "🏔️ Impianto",
                        "Prezzo_skipass": "💶 Skipass (€)",
                        "kmopen": "🛷 Km Aperti",
                        "rapporto_euro_km": "💸 €/Km"
                    }
                    df_table = df_table.rename(columns=rename_map)
                    
                    # Formatta i valori
                    if "💶 Skipass (€)" in df_table.columns:
                        df_table["💶 Skipass (€)"] = df_table["💶 Skipass (€)"].round(2)
                    if "🛷 Km Aperti" in df_table.columns:
                        df_table["🛷 Km Aperti"] = df_table["🛷 Km Aperti"].round(1)
                    if "💸 €/Km" in df_table.columns:
                        df_table["💸 €/Km"] = df_table["💸 €/Km"].round(2)
                    
                    st.subheader("📊 Rapporto Qualità-Prezzo: Euro per Chilometro")
                    st.markdown("""
                    **Indice calcolato:**
                    - **€/Km**: meno euro per chilometro di pista = migliore rapporto qualità-prezzo
                    """)
                    
                    # Mostra tutte le stazioni (dovrebbero essere 7)
                    st.dataframe(df_table, use_container_width=True, hide_index=True)
                else:
                    st.info("Dati insufficienti per calcolare il rapporto kmopen/costo skipass")
            else:
                st.info("Colonne 'kmopen' o 'Prezzo_skipass' non disponibili per l'analisi")
        except Exception as e:
            st.warning(f"Errore nel calcolo del rapporto: {e}")
            st.write(f"Errore completo: {str(e)}")
        
        # 3) AI Overview – Low-Cost (TEMPORANEAMENTE DISABILITATO)
        try:
            st.markdown('<h4 class="section-subtitle">🤖 AI Overview – Low-Cost</h4>', unsafe_allow_html=True)
            try:
                prompt_lowcost = build_lowcost_prompt(df_filtered_rec, best_name, livello, data_sel, df_ratio)
                out, usage = generate_overview(prompt_lowcost, max_tokens=140)
                
                # Pulizia diretta e aggressiva del contenuto HTML
                clean_out = re.sub(r'<[^>]*>', '', str(out)).strip()
                clean_out = re.sub(r'\s+', ' ', clean_out)
                
                st.markdown(f"""
            <div class="ai-overview-section">
                    <div class="ai-header">
                        <div class="ai-header-text">
                            <div class="ai-title">AI Overview ✨</div>
                            <div class="ai-badge">Powered by {parse_model_name(DEFAULT_LLM_MODEL)}</div>
            </div>
                    </div>
                    <div class="ai-overview-content">{clean_out}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Errore nell'AI Overview Low-Cost: {e}")
        except Exception as e:
            st.warning(f"Errore nell'AI Overview: {e}")
    
    # --- Sezione finale: classifiche semplici per livello e profilo ---
    try:
        if df_with_indices is not None and not df_with_indices.empty:
            st.markdown("---")
            # Classifica per livello
            st.subheader("Classifica e indici – Livello")
            level_to_col = {"base": "indice_base", "medio": "indice_medio", "esperto": "indice_esperto"}
            level_col = level_to_col.get(livello)
            if level_col and level_col in df_with_indices.columns:
                df_level_rank = (
                    df_with_indices.groupby("nome_stazione")[level_col]
                    .mean()
                    .reset_index()
                    .sort_values(level_col, ascending=False)
                )
                fig_lvl = px.bar(
                    df_level_rank,
                    x="nome_stazione",
                    y=level_col,
                    title=f"Ranking (livello: {livello})",
                    labels={"nome_stazione": "Impianto", level_col: "Indice livello"},
                )
                fig_lvl.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_lvl, use_container_width=True)
            else:
                st.info("Seleziona un livello per vedere la classifica per livello.")

            # Classifica per profilo
            st.subheader("Classifica e indici – Profilo")
            profile_to_col = {
                "panoramico": "indice_panoramico",
                "familiare": "indice_famigliare",
                "festaiolo": "indice_festaiolo",
                "lowcost": "indice_lowcost",
            }
            prof_col = profile_to_col.get(profilo_norm)
            if prof_col and prof_col in df_with_indices.columns:
                df_prof_rank = (
                    df_with_indices.groupby("nome_stazione")[prof_col]
                    .mean()
                    .reset_index()
                    .sort_values(prof_col, ascending=False)
                )
                fig_prof = px.bar(
                    df_prof_rank,
                    x="nome_stazione",
                    y=prof_col,
                    title=f"Ranking (profilo: {profilo_norm})",
                    labels={"nome_stazione": "Impianto", prof_col: "Indice profilo"},
                )
                fig_prof.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prof, use_container_width=True)
            else:
                st.info("Seleziona un profilo per vedere la classifica per profilo.")
    except Exception:
        pass

    st.caption("v2 – Stazione consigliata, overview AI e viste dedicate per livello")
    
    # Chiudi theme wrapper
    st.markdown('</div>', unsafe_allow_html=True)






if __name__ == "__main__":
    main()