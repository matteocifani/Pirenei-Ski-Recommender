# 🎨 Modern UI Design System - Versione 4

## Overview

This project has been completely redesigned with a modern, professional UI inspired by top tech companies including **Prospinity**, **Airbnb**, **Apple**, **Google**, and **OpenAI**. The new design system provides a clean, minimal aesthetic with subtle animations and professional typography.

**Versione 4** introduces a complete onboarding system, AI integration, and enhanced user experience components.

## ✨ Key Features

### 🎨 **Modern Aesthetics**
- **Gradient backgrounds** with subtle color transitions
- **Glass morphism** effects with backdrop blur
- **Subtle glow effects** that don't overwhelm the content
- **Professional typography** using system fonts
- **Consistent spacing** using CSS custom properties

### 🌓 **Dark/Light Mode Support**
- **Automatic theme detection** based on system preferences
- **CSS Variables** for easy theme switching
- **Smooth transitions** between themes
- **Accessible color contrasts** in both modes

### 📱 **Responsive Design**
- **Mobile-first approach** with responsive breakpoints
- **CSS Grid layouts** for flexible component arrangements
- **Touch-friendly interactions** for mobile devices
- **Adaptive typography** that scales appropriately

### 🚀 **Performance Optimized**
- **Minimal CSS overhead** with efficient selectors
- **Hardware-accelerated animations** using transform properties
- **Optimized transitions** with appropriate easing functions
- **Lazy loading** of non-critical styles

### 🎯 **Onboarding System** (NEW in V4)
- **Step-by-step guidance** with interactive tooltips
- **Dynamic validation** and real-time feedback
- **Celebration animations** for completion
- **Restart functionality** for user flexibility

### 🧠 **AI Integration** (NEW in V4)
- **AI Dock**: Floating control panel for AI features
- **Multi-provider support**: OpenAI, Mistral, Anthropic, Google, Meta
- **Smart caching**: Performance optimization for AI calls
- **Contextual prompts**: Specialized AI overviews for each profile

## 🎭 Component Library

### **Hero Header** (`.app-header`)
```html
<div class="app-header">
    <h1 class="app-title">🏔️ Pirenei Ski Recommender</h1>
    <p class="app-subtitle">La tua guida per scegliere la stazione sciistica perfetta</p>
</div>
```

**Features:**
- **Organic background animation** with subtle flowing effects
- **Gradient text** with shimmer animation
- **Floating sparkles** and decorative elements
- **Scroll indicator** with bounce animation

### **Onboarding Components** (`.onboarding-*`)
```html
<!-- Tooltip container -->
<div class="onboarding-tooltip-flow">
    <div class="onboarding-tooltip tooltip-step-1">
        Quando vorresti conquistare le piste? ⛷️
    </div>
</div>

<!-- Restart button -->
<button class="restart-onboarding">🔄 Ricomincia</button>
```

**Features:**
- **Step-based tooltips** with contextual positioning
- **Arrow indicators** pointing to relevant elements
- **Smooth animations** for tooltip appearance
- **Responsive positioning** for all screen sizes

### **AI Dock** (`.ai-dock`)
```html
<div class="ai-dock">
    <div class="ai-dock-left">
        <span class="ai-status">AI pronta</span>
    </div>
    <div class="ai-dock-center">
        <button class="ai-icon-button" title="Voice mode">🗣️</button>
        <button class="ai-icon-button" title="Genera riepilogo">🧠</button>
        <button class="ai-icon-button" title="Condividi">🔗</button>
    </div>
    <div class="ai-dock-right">
        <select class="ai-model-select">Model</select>
        <button class="ai-run-button">▶️</button>
    </div>
</div>
```

**Features:**
- **Floating position** with backdrop blur
- **Interactive controls** for AI features
- **Model selection** dropdown
- **Status indicators** and loading states

### **Modern Cards** (`.modern-card`)
```html
<div class="modern-card">
    <h3>Card Title</h3>
    <p>Card content goes here</p>
</div>
```

**Variants:**
- `.modern-card.primary` - Blue accent with primary glow
- `.modern-card.success` - Green accent with success glow  
- `.modern-card.warning` - Orange accent with warning glow
- `.modern-card.danger` - Red accent with danger glow

### **KPI Cards** (`.kpi-card`)
```html
<div class="kpi-card">
    <div class="kpi-icon">📊</div>
    <div class="kpi-value">25 km</div>
    <div class="kpi-label">Piste Aperte</div>
    <div class="kpi-subtitle">Aggiornato oggi</div>
</div>
```

**Features:**
- **Icon integration** with consistent sizing
- **Value prominence** with large typography
- **Subtitle support** for additional context
- **Hover effects** with smooth transitions

### **Modern Podium** (`.podium-container`)
```html
<div class="podium-container">
    <div class="podium-step second">
        <div class="podium-platform second">
            <div class="podium-rank">2</div>
            <div class="podium-medal">🥈</div>
            <div class="podium-name">Second Place</div>
        </div>
    </div>
    <!-- First and Third place steps -->
</div>
```

**Features:**
- **Olympic-style design** with medal emojis
- **Rank indicators** with circular badges
- **Hover animations** with lift effects
- **Responsive scaling** for mobile devices

### **AI Overview** (`.ai-overview-section`)
```html
<div class="ai-overview-section">
    <div class="ai-header">
        <div class="ai-badge">AI Overview</div>
        <h4 class="ai-title">Riepilogo Generato da AI</h4>
    </div>
    <div class="ai-overview-content">
        Contenuto generato dall'intelligenza artificiale...
    </div>
</div>
```

**Features:**
- **Purple accent** with subtle glow effects
- **Badge system** for categorization
- **Content hierarchy** with clear typography
- **Hover interactions** with enhanced shadows

## 🎨 Color System

### **Primary Colors**
- `--primary-50` to `--primary-900`: Blue scale for primary actions
- `--secondary-50` to `--secondary-900`: Gray scale for backgrounds and text

### **Semantic Colors**
- `--success-*`: Green scale for positive actions
- `--warning-*`: Orange scale for caution states
- `--danger-*`: Red scale for error states

### **AI-Specific Colors** (NEW in V4)
- `--purple-*`: Purple scale for AI features
- `--emerald-*`: Emerald scale for success states
- `--amber-*`: Amber scale for warning states

### **Usage Examples**
```css
/* Primary button */
background: var(--primary-500);

/* Success message */
border-color: var(--success-200);

/* AI feature */
border-color: var(--purple-200);
box-shadow: var(--shadow-ai-glow);
```

## 📏 Spacing System

### **Spacing Scale**
- `--space-xs`: 0.25rem (4px)
- `--space-sm`: 0.5rem (8px)
- `--space-md`: 1rem (16px)
- `--space-lg`: 1.5rem (24px)
- `--space-xl`: 2rem (32px)
- `--space-2xl`: 3rem (48px)
- `--space-3xl`: 4rem (64px)

### **Usage**
```css
margin: var(--space-lg);
padding: var(--space-xl);
gap: var(--space-md);
```

## 🔧 Customization

### **CSS Variables**
All design tokens are defined as CSS custom properties, making it easy to customize:

```css
:root {
    --primary-500: #3b82f6; /* Change primary color */
    --radius-lg: 1rem;      /* Change border radius */
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1); /* Custom shadows */
}
```

### **Theme Overrides**
Create custom themes by overriding the CSS variables:

```css
[data-theme="custom"] {
    --primary-500: #8b5cf6;
    --bg-primary: #f8fafc;
    --text-primary: #1e293b;
}
```

## 📱 Responsive Breakpoints

### **Mobile First Approach**
```css
/* Base styles (mobile) */
.modern-card {
    padding: var(--space-md);
}

/* Tablet and up */
@media (min-width: 768px) {
    .modern-card {
        padding: var(--space-xl);
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .modern-card {
        padding: var(--space-2xl);
    }
}
```

### **Onboarding Responsiveness** (NEW in V4)
```css
/* Mobile onboarding */
@media (max-width: 768px) {
    .onboarding-selectors {
        flex-direction: column;
        gap: var(--space-24);
    }
    
    .onboarding-tooltip {
        max-width: 280px;
        font-size: 14px;
    }
}
```

## 🎭 Animation System

### **Transitions**
- `--transition-fast`: 150ms ease
- `--transition-normal`: 250ms ease  
- `--transition-slow`: 350ms ease

### **Hover Effects**
```css
.modern-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
    border-color: var(--border-medium);
}
```

### **Onboarding Animations** (NEW in V4)
```css
@keyframes tooltipSlideDown {
    from { 
        opacity: 0; 
        transform: translateY(-20px); 
    }
    to { 
        opacity: 1; 
        transform: translateY(0); 
    }
}

@keyframes tooltipFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
```

### **AI Dock Animations** (NEW in V4)
```css
@keyframes borderBreathing {
    0%, 100% { 
        opacity: 0.3;
        transform: scale(1);
    }
    50% { 
        opacity: 0.6;
        transform: scale(1.05);
    }
}
```

## 🚀 Implementation Guide

### **1. Basic Setup**
```python
import streamlit as st

# Include the CSS
st.markdown("""
<style>
/* Copy the CSS from streamlit_app_v2.py */
</style>
""", unsafe_allow_html=True)
```

### **2. Create Onboarding System**
```python
# Onboarding state management
if "onboarding_completed" not in st.session_state:
    st.session_state.onboarding_completed = False

# Step-based selection
if not st.session_state.onboarding_completed:
    # Show onboarding flow
    st.markdown('<div class="onboarding-container">', unsafe_allow_html=True)
    # Your onboarding content
    st.markdown('</div>', unsafe_allow_html=True)
```

### **3. Create AI Dock**
```python
# AI Dock component
st.markdown("""
<div class="ai-dock">
    <div class="ai-dock-left">
        <span class="ai-status">AI pronta</span>
    </div>
    <div class="ai-dock-center">
        <button class="ai-icon-button">🧠</button>
    </div>
    <div class="ai-dock-right">
        <button class="ai-run-button">▶️</button>
    </div>
</div>
""", unsafe_allow_html=True)
```

### **4. Use Modern Components**
```python
# Hero section
st.markdown('<h1 class="modern-header">🏔️ Ski Resort Recommender</h1>', unsafe_allow_html=True)

# KPI cards
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="kpi-card">
        <div class="kpi-icon">📊</div>
        <div class="kpi-value">25 km</div>
        <div class="kpi-label">Piste Aperte</div>
    </div>
    """, unsafe_allow_html=True)
```

## 🔍 Best Practices

### **Accessibility**
- Use semantic HTML elements
- Ensure sufficient color contrast
- Provide alternative text for icons
- Test with screen readers

### **Performance**
- Minimize CSS bundle size
- Use efficient selectors
- Optimize animations for 60fps
- Lazy load non-critical styles

### **Onboarding UX** (NEW in V4)
- **Clear progression**: Show current step clearly
- **Contextual help**: Provide relevant tooltips
- **Validation feedback**: Give immediate response to user actions
- **Flexible restart**: Allow users to restart the process

### **AI Integration** (NEW in V4)
- **Graceful fallbacks**: Handle AI failures gracefully
- **Loading states**: Show progress during AI operations
- **Cache results**: Avoid unnecessary API calls
- **User control**: Let users choose when to use AI features

## 🎯 Design Principles

### **1. Minimalism**
- Remove unnecessary visual elements
- Focus on content hierarchy
- Use whitespace effectively
- Keep interfaces clean and uncluttered

### **2. Consistency**
- Maintain visual consistency across components
- Use consistent spacing and typography
- Apply consistent color schemes
- Follow established design patterns

### **3. Accessibility**
- Ensure designs work for all users
- Maintain sufficient contrast ratios
- Provide clear visual hierarchy
- Support keyboard navigation

### **4. Performance**
- Optimize for fast loading
- Minimize layout shifts
- Use efficient animations
- Prioritize user experience

### **5. User Guidance** (NEW in V4)
- **Progressive disclosure**: Show information as needed
- **Contextual help**: Provide assistance when relevant
- **Clear feedback**: Give users confidence in their actions
- **Flexible navigation**: Allow multiple paths to completion

## 🚀 Future Enhancements

### **Planned Features**
- [ ] Component library with Storybook
- [ ] Design token export for design tools
- [ ] Advanced animation presets
- [ ] Theme builder interface
- [ ] Component playground
- [ ] Onboarding analytics and optimization
- [ ] AI prompt management interface

### **Contributing**
- Follow the established design patterns
- Maintain consistency with existing components
- Test across different devices and browsers
- Document new components thoroughly
- Consider accessibility in all new features

## 📚 Resources

### **Inspiration**
- [Prospinity](https://prospinity.com/) - Clean, modern startup design
- [Airbnb](https://airbnb.com/) - Intuitive user interfaces
- [Apple](https://apple.com/) - Minimal, elegant design
- [Google](https://google.com/) - Material Design principles
- [OpenAI](https://openai.com/) - Futuristic, accessible design

### **Tools**
- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [CSS Grid](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)
- [CSS Animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations)
- [Streamlit](https://streamlit.io/) - Web app framework

---

**Versione 4** - Built with ❤️ using Streamlit, modern CSS, and AI integration

*Design inspired by the world's leading tech companies*
