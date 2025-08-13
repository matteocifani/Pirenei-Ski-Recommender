"""
Modern UI Design System Examples
================================

This file demonstrates how to use the new modern design system
inspired by Prospinity, Airbnb, Apple, Google, and OpenAI.

Features:
- CSS Variables for light/dark mode support
- Modern gradients and subtle glow effects
- Responsive design with CSS Grid
- Hover animations and transitions
- Professional typography and spacing
"""

import streamlit as st

# Modern UI Configuration
st.set_page_config(
    page_title="🎨 Modern UI Examples",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Design System CSS
st.markdown("""
<style>
/* Modern Design System - Inspired by Prospinity, Airbnb, Apple, Google, OpenAI */
:root {
    /* Color Palette */
    --primary-50: #eff6ff;
    --primary-100: #dbeafe;
    --primary-200: #bfdbfe;
    --primary-300: #93c5fd;
    --primary-400: #60a5fa;
    --primary-500: #3b82f6;
    --primary-600: #2563eb;
    --primary-700: #1d4ed8;
    --primary-800: #1e40af;
    --primary-900: #1e3a8a;
    
    --secondary-50: #f8fafc;
    --secondary-100: #f1f5f9;
    --secondary-200: #e2e8f0;
    --secondary-300: #cbd5e1;
    --secondary-400: #94a3b8;
    --secondary-500: #64748b;
    --secondary-600: #475569;
    --secondary-700: #334155;
    --secondary-800: #1e293b;
    --secondary-900: #0f172a;
    
    --success-50: #f0fdf4;
    --success-100: #dcfce7;
    --success-200: #bbf7d0;
    --success-300: #86efac;
    --success-400: #4ade80;
    --success-500: #22c55e;
    --success-600: #16a34a;
    --success-700: #15803d;
    --success-800: #166534;
    --success-900: #14532d;
    
    --warning-50: #fffbeb;
    --warning-100: #fef3c7;
    --warning-200: #fde68a;
    --warning-300: #fcd34d;
    --warning-400: #fbbf24;
    --warning-500: #f59e0b;
    --warning-600: #d97706;
    --warning-700: #b45309;
    --warning-800: #92400e;
    --warning-900: #78350f;
    
    --danger-50: #fef2f2;
    --danger-100: #fee2e2;
    --danger-200: #fecaca;
    --danger-300: #fca5a5;
    --danger-400: #f87171;
    --danger-500: #ef4444;
    --danger-600: #dc2626;
    --danger-700: #b91c1c;
    --danger-800: #991b1b;
    --danger-900: #7f1d1d;
    
    /* Semantic Colors */
    --text-primary: var(--secondary-900);
    --text-secondary: var(--secondary-600);
    --text-muted: var(--secondary-500);
    --text-inverse: var(--secondary-50);
    
    --bg-primary: var(--secondary-50);
    --bg-secondary: var(--secondary-100);
    --bg-card: #ffffff;
    --bg-overlay: rgba(255, 255, 255, 0.95);
    
    --border-light: var(--secondary-200);
    --border-medium: var(--secondary-300);
    --border-strong: var(--secondary-400);
    
    /* Shadows & Effects */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    
    /* Glow Effects */
    --glow-primary: 0 0 20px rgba(59, 130, 246, 0.15);
    --glow-success: 0 0 20px rgba(34, 197, 94, 0.15);
    --glow-warning: 0 0 20px rgba(245, 158, 11, 0.15);
    --glow-danger: 0 0 20px rgba(239, 68, 68, 0.15);
    
    /* Spacing */
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
    --space-3xl: 4rem;
    
    /* Border Radius */
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-2xl: 1.5rem;
    
    /* Typography */
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-mono: "SF Mono", Monaco, Inconsolata, "Roboto Mono", monospace;
    
    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 250ms ease;
    --transition-slow: 350ms ease;
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    :root {
        --text-primary: var(--secondary-50);
        --text-secondary: var(--secondary-300);
        --text-muted: var(--secondary-400);
        --text-inverse: var(--secondary-900);
        
        --bg-primary: var(--secondary-900);
        --bg-secondary: var(--secondary-800);
        --bg-card: var(--secondary-800);
        --bg-overlay: rgba(30, 41, 59, 0.95);
        
        --border-light: var(--secondary-700);
        --border-medium: var(--secondary-600);
        --border-strong: var(--secondary-500);
    }
}

/* Global Styles */
.main {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    font-family: var(--font-sans);
    color: var(--text-primary);
    line-height: 1.6;
}

/* Modern Cards */
.modern-card {
    background: var(--bg-overlay);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-xl);
    padding: var(--space-xl);
    margin: var(--space-lg) 0;
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(20px);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}

.modern-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--primary-400), var(--secondary-400));
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    border-color: var(--border-medium);
}

.modern-card:hover::before {
    opacity: 1;
}

/* Card Variants */
.modern-card.primary {
    border-color: var(--primary-200);
    box-shadow: var(--shadow-md), var(--glow-primary);
}

.modern-card.success {
    border-color: var(--success-200);
    box-shadow: var(--shadow-md), var(--glow-success);
}

.modern-card.warning {
    border-color: var(--warning-200);
    box-shadow: var(--shadow-md), var(--glow-warning);
}

.modern-card.danger {
    border-color: var(--danger-200);
    box-shadow: var(--shadow-md), var(--glow-danger);
}

/* Modern Headers */
.modern-header {
    color: var(--text-primary);
    font-weight: 800;
    font-size: 3rem;
    text-align: center;
    margin: var(--space-3xl) 0 var(--space-2xl) 0;
    letter-spacing: -0.025em;
    line-height: 1.1;
}

.modern-subheader {
    color: var(--text-primary);
    font-weight: 700;
    font-size: 1.75rem;
    margin: var(--space-xl) 0 var(--space-lg) 0;
    letter-spacing: -0.025em;
}

.modern-section-title {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 1.5rem;
    margin: var(--space-lg) 0 var(--space-md) 0;
    display: flex;
    align-items: center;
    gap: var(--space-sm);
}

/* Hero Section */
.hero-section {
    background: var(--bg-card);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-2xl);
    padding: var(--space-2xl);
    margin: var(--space-xl) 0;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.03) 0%, transparent 70%);
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: var(--space-md);
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-secondary);
    margin-bottom: var(--space-lg);
    position: relative;
    z-index: 1;
}

/* Modern Metrics */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-lg);
    margin: var(--space-lg) 0;
}

.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    text-align: center;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(147, 51, 234, 0.05));
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-300);
}

.metric-card:hover::before {
    opacity: 1;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--text-primary);
    margin: var(--space-sm) 0;
    position: relative;
    z-index: 1;
}

.metric-label {
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    position: relative;
    z-index: 1;
}

/* Modern Podium */
.podium-container {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    gap: var(--space-lg);
    margin: var(--space-2xl) 0;
    height: 180px;
}

.podium-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    transition: all var(--transition-normal);
    position: relative;
}

.podium-step:hover {
    transform: translateY(-4px);
}

.podium-step.first {
    order: 2;
}

.podium-step.second {
    order: 1;
}

.podium-step.third {
    order: 3;
}

.podium-platform {
    width: 140px;
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}

.podium-platform::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
    opacity: 0;
    transition: opacity var(--transition-normal);
}

.podium-platform:hover::before {
    opacity: 1;
}

.podium-platform.first {
    height: 140px;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    box-shadow: var(--shadow-xl), var(--glow-warning);
}

.podium-platform.second {
    height: 110px;
    background: linear-gradient(135deg, #94a3b8, #64748b);
    box-shadow: var(--shadow-lg);
}

.podium-platform.third {
    height: 80px;
    background: linear-gradient(135deg, #d97706, #b45309);
    box-shadow: var(--shadow-md);
}

.podium-medal {
    font-size: 2rem;
    margin-bottom: var(--space-sm);
    position: relative;
    z-index: 1;
}

.podium-name {
    color: white;
    font-weight: 600;
    font-size: 0.85rem;
    text-align: center;
    position: relative;
    z-index: 1;
    line-height: 1.2;
    max-width: 120px;
    word-wrap: break-word;
}

/* Modern Buttons */
.modern-button {
    background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
    border: none;
    border-radius: var(--radius-lg);
    padding: var(--space-md) var(--space-xl);
    color: var(--text-inverse);
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-normal);
    box-shadow: var(--shadow-md);
    position: relative;
    overflow: hidden;
}

.modern-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left var(--transition-slow);
}

.modern-button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
}

.modern-button:hover::before {
    left: 100%;
}

/* Modern Tables */
.modern-table {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-light);
}

.modern-table th {
    background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
    color: var(--text-inverse);
    font-weight: 600;
    padding: var(--space-md);
    text-align: left;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.modern-table td {
    padding: var(--space-md);
    border-bottom: 1px solid var(--border-light);
    color: var(--text-primary);
}

.modern-table tr:hover {
    background: var(--bg-secondary);
}

/* Modern Sidebar */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-right: 1px solid var(--border-light);
}

/* Responsive Design */
@media (max-width: 768px) {
    .podium-container {
        flex-direction: column;
        align-items: center;
    }
    
    .podium-step {
        order: unset !important;
    }
    
    .modern-header {
        font-size: 2rem;
    }
    
    .hero-title {
        font-size: 2rem;
    }
    
    .metric-grid {
        grid-template-columns: 1fr;
    }
}

/* Custom Streamlit Elements */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-500), var(--primary-600));
    border: none;
    border-radius: var(--radius-lg);
    color: var(--text-inverse);
    font-weight: 600;
    padding: var(--space-md) var(--space-xl);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-normal);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    background: linear-gradient(135deg, var(--primary-600), var(--primary-700));
}

/* Plotly Chart Styling */
.js-plotly-plot .plotly .main-svg {
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
}

/* Success Messages */
.stSuccess {
    background: linear-gradient(135deg, var(--success-50), var(--success-100));
    border: 1px solid var(--success-200);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md), var(--glow-success);
}

/* Info Messages */
.stInfo {
    background: linear-gradient(135deg, var(--primary-50), var(--primary-100));
    border: 1px solid var(--primary-200);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md), var(--glow-primary);
}

/* Warning Messages */
.stWarning {
    background: linear-gradient(135deg, var(--warning-50), var(--warning-100));
    border: 1px solid var(--warning-200);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md), var(--glow-warning);
}

/* Error Messages */
.stError {
    background: linear-gradient(135deg, var(--danger-50), var(--danger-100));
    border: 1px solid var(--danger-200);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md), var(--glow-danger);
}

/* AI Overview Styling */
.ai-overview {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin: var(--space-md) 0;
    position: relative;
    overflow: hidden;
}

.ai-overview::before {
    content: '✨';
    position: absolute;
    top: var(--space-sm);
    right: var(--space-sm);
    font-size: 1.5rem;
    opacity: 0.3;
}

.ai-content {
    color: var(--text-primary);
    line-height: 1.7;
    font-size: 1rem;
    position: relative;
    z-index: 1;
}

/* Map Container */
.map-container {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    margin: var(--space-md) 0;
    box-shadow: var(--shadow-md);
}

/* Separator */
.modern-separator {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-medium), transparent);
    margin: var(--space-2xl) 0;
    border: none;
}

/* Loading States */
.loading-shimmer {
    background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-primary) 50%, var(--bg-secondary) 75%);
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* Floating Elements */
.floating {
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

/* Gradient Text */
.gradient-text {
    background: linear-gradient(135deg, var(--primary-500), var(--success-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Status Indicators */
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: var(--space-sm);
}

.status-indicator.online {
    background: var(--success-500);
    box-shadow: 0 0 8px var(--success-500);
}

.status-indicator.offline {
    background: var(--danger-500);
    box-shadow: 0 0 8px var(--danger-500);
}

/* Tooltip */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltiptext {
    visibility: hidden;
    width: 200px;
    background: var(--bg-card);
    color: var(--text-primary);
    text-align: center;
    border-radius: var(--radius-md);
    padding: var(--space-sm);
    position: absolute;
    z-index: 1;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
    opacity: 0;
    transition: opacity var(--transition-normal);
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--border-light);
}

.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Demonstrate the new modern design system components."""
    
    # Hero Section
    st.markdown('<h1 class="modern-header">🎨 Modern UI Design System</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: var(--text-secondary); margin-bottom: 2rem;">Inspired by Prospinity, Airbnb, Apple, Google, and OpenAI</p>', unsafe_allow_html=True)
    
    # Hero Card
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">Welcome to the Future</div>
        <div class="hero-subtitle">Experience modern, responsive design with subtle animations and professional aesthetics</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Modern Cards Examples
    st.markdown('<h2 class="modern-subheader">📱 Modern Cards</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="modern-card primary">
            <h3>Primary Card</h3>
            <p>This is a primary card with blue accent and glow effect.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="modern-card success">
            <h3>Success Card</h3>
            <p>This is a success card with green accent and glow effect.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="modern-card warning">
            <h3>Warning Card</h3>
            <p>This is a warning card with orange accent and glow effect.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="modern-card danger">
            <h3>Danger Card</h3>
            <p>This is a danger card with red accent and glow effect.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics Grid
    st.markdown('<h2 class="modern-subheader">📊 Metrics Grid</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Total Users</div>
            <div class="metric-value">12,847</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Revenue</div>
            <div class="metric-value">$89,432</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Growth</div>
            <div class="metric-value">+23.4%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Conversion</div>
            <div class="metric-value">4.2%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Podium Example
    st.markdown('<h2 class="modern-subheader">🏆 Modern Podium</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="podium-container">
        <div class="podium-step second">
            <div class="podium-platform second">
                <div class="podium-medal">🥈</div>
                <div class="podium-name">Second Place</div>
            </div>
        </div>
        <div class="podium-step first">
            <div class="podium-platform first">
                <div class="podium-medal">🥇</div>
                <div class="podium-name">First Place</div>
            </div>
        </div>
        <div class="podium-step third">
            <div class="podium-platform third">
                <div class="podium-medal">🥉</div>
                <div class="podium-name">Third Place</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Overview Example
    st.markdown('<h2 class="modern-subheader">🤖 AI Overview Styling</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="ai-overview">
        <div class="ai-content">
            <h4>AI-Generated Summary</h4>
            <p>This is an example of how AI overview content would be styled with the new design system. 
            The content is contained within a modern card with subtle AI branding elements.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Modern Table Example
    st.markdown('<h2 class="modern-subheader">📋 Modern Tables</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="modern-table">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Position</th>
                    <th>Department</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John Doe</td>
                    <td>Senior Developer</td>
                    <td>Engineering</td>
                    <td><span class="status-indicator online"></span>Active</td>
                </tr>
                <tr>
                    <td>Jane Smith</td>
                    <td>Product Manager</td>
                    <td>Product</td>
                    <td><span class="status-indicator online"></span>Active</td>
                </tr>
                <tr>
                    <td>Bob Johnson</td>
                    <td>Designer</td>
                    <td>Design</td>
                    <td><span class="status-indicator offline"></span>Offline</td>
                </tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Separator
    st.markdown('<hr class="modern-separator">', unsafe_allow_html=True)
    
    # Features List
    st.markdown('<h2 class="modern-subheader">✨ Key Features</h2>', unsafe_allow_html=True)
    
    features = [
        "🎨 **Modern Design**: Inspired by top tech companies",
        "🌓 **Dark/Light Mode**: Automatic theme detection",
        "📱 **Responsive**: Mobile-first design approach",
        "✨ **Subtle Animations**: Hover effects and transitions",
        "🎯 **CSS Variables**: Easy customization and theming",
        "🚀 **Performance**: Optimized CSS with minimal overhead",
        "🎭 **Component Variants**: Multiple card and button styles",
        "🔧 **Developer Friendly**: Clean, maintainable code"
    ]
    
    for feature in features:
        st.markdown(f"- {feature}")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding: 2rem; color: var(--text-secondary);">
        <p>Built with ❤️ using Streamlit and modern CSS</p>
        <p>Design inspired by Prospinity, Airbnb, Apple, Google, and OpenAI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
