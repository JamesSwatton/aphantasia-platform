# Design System Implementation Plan

## Overview

Building a minimal custom CSS system for the participant-facing side of the platform. This will replace inline styles with a lightweight, maintainable design system.

**Goals:**
- Replace inline CSS with a clean, consistent system
- Keep bundle size tiny (~10-15KB)
- No external dependencies
- Easy to maintain and extend
- Professional, academic aesthetic

**Tech Stack:**
- Pure CSS with CSS custom properties (variables)
- No build step required (optional for future)
- Works with planned HTMX/Alpine.js integration

---

## Phase 1: Audit & Foundation

### Step 1.1: Audit Existing Styles
- [ ] Extract all inline styles from current templates
- [ ] Document color palette being used
- [ ] Document spacing patterns (padding, margins)
- [ ] Document font sizes and weights
- [ ] List all component types (buttons, cards, badges, forms, etc.)

**Files to audit:**
- `templates/base.html`
- `templates/dashboard/participant_dashboard.html`
- `templates/surveys/survey_detail.html`
- `templates/surveys/survey_list.html`
- `templates/tasks/*.html`
- `templates/home.html`
- `templates/account/*.html`

### Step 1.2: Create CSS File Structure

**Initial structure (simple):**
```
static/
├── css/
│   └── main.css          # Single CSS file
└── js/                   # Future: Alpine.js, HTMX
```

**Alternative (if CSS grows beyond 800 lines):**
```
static/
└── css/
    ├── main.css         # Imports everything
    ├── variables.css    # CSS custom properties
    ├── utilities.css    # Utility classes
    └── components.css   # Component classes
```

### Step 1.3: Define CSS Variables (Design Tokens)

Create foundation with CSS custom properties:

```css
:root {
  /* Colors - extracted from current palette */
  --color-primary: #3498db;      /* Blue - main actions */
  --color-success: #27ae60;      /* Green - success states */
  --color-warning: #f39c12;      /* Orange - warnings */
  --color-danger: #e74c3c;       /* Red - errors */
  --color-info: #9b59b6;         /* Purple - info/tasks */

  /* Grays */
  --color-gray-50: #f9f9f9;      /* Lightest background */
  --color-gray-100: #f5f5f5;     /* Light background */
  --color-gray-200: #ddd;        /* Borders */
  --color-gray-600: #666;        /* Secondary text */
  --color-gray-800: #2c3e50;     /* Primary text/headers */

  /* Spacing scale (based on 16px = 1rem) */
  --space-xs: 0.25rem;    /* 4px */
  --space-sm: 0.5rem;     /* 8px */
  --space-md: 1rem;       /* 16px */
  --space-lg: 1.5rem;     /* 24px */
  --space-xl: 2rem;       /* 32px */
  --space-2xl: 3rem;      /* 48px */

  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-size-sm: 0.875rem;   /* 14px */
  --font-size-base: 1rem;      /* 16px */
  --font-size-lg: 1.1rem;      /* 17.6px */
  --font-size-xl: 1.5rem;      /* 24px */
  --font-size-2xl: 2rem;       /* 32px */
  --line-height-tight: 1.25;
  --line-height-normal: 1.6;
  --line-height-relaxed: 1.8;

  /* Borders & Shadows */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.1);
  --shadow-md: 0 2px 4px rgba(0,0,0,0.1);
  --shadow-lg: 0 4px 8px rgba(0,0,0,0.1);

  /* Layout */
  --container-width: 800px;
  --container-width-wide: 1200px;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
}
```

---

## Phase 2: Build Utility Classes

### Step 2.1: Spacing Utilities

```css
/* Margin utilities */
.m-0 { margin: 0; }
.m-xs { margin: var(--space-xs); }
.m-sm { margin: var(--space-sm); }
.m-md { margin: var(--space-md); }
.m-lg { margin: var(--space-lg); }
.m-xl { margin: var(--space-xl); }

/* Margin - specific sides */
.mt-0 { margin-top: 0; }
.mt-sm { margin-top: var(--space-sm); }
.mt-md { margin-top: var(--space-md); }
.mt-lg { margin-top: var(--space-lg); }
.mt-xl { margin-top: var(--space-xl); }

.mb-0 { margin-bottom: 0; }
.mb-sm { margin-bottom: var(--space-sm); }
.mb-md { margin-bottom: var(--space-md); }
.mb-lg { margin-bottom: var(--space-lg); }
.mb-xl { margin-bottom: var(--space-xl); }
.mb-2xl { margin-bottom: var(--space-2xl); }

.ml-sm { margin-left: var(--space-sm); }
.ml-md { margin-left: var(--space-md); }

.mr-sm { margin-right: var(--space-sm); }
.mr-md { margin-right: var(--space-md); }

/* Padding utilities */
.p-0 { padding: 0; }
.p-sm { padding: var(--space-sm); }
.p-md { padding: var(--space-md); }
.p-lg { padding: var(--space-lg); }
.p-xl { padding: var(--space-xl); }
.p-2xl { padding: var(--space-2xl); }

/* Padding - axis */
.px-sm { padding-left: var(--space-sm); padding-right: var(--space-sm); }
.px-md { padding-left: var(--space-md); padding-right: var(--space-md); }
.px-lg { padding-left: var(--space-lg); padding-right: var(--space-lg); }
.px-xl { padding-left: var(--space-xl); padding-right: var(--space-xl); }

.py-sm { padding-top: var(--space-sm); padding-bottom: var(--space-sm); }
.py-md { padding-top: var(--space-md); padding-bottom: var(--space-md); }
.py-lg { padding-top: var(--space-lg); padding-bottom: var(--space-lg); }
.py-xl { padding-top: var(--space-xl); padding-bottom: var(--space-xl); }

/* Padding - specific sides */
.pt-md { padding-top: var(--space-md); }
.pb-sm { padding-bottom: var(--space-sm); }
.pb-md { padding-bottom: var(--space-md); }
.pb-lg { padding-bottom: var(--space-lg); }
```

### Step 2.2: Layout Utilities

```css
/* Display */
.block { display: block; }
.inline-block { display: inline-block; }
.flex { display: flex; }
.inline-flex { display: inline-flex; }

/* Flexbox */
.flex-row { flex-direction: row; }
.flex-col { flex-direction: column; }
.flex-wrap { flex-wrap: wrap; }

.items-start { align-items: flex-start; }
.items-center { align-items: center; }
.items-end { align-items: flex-end; }

.justify-start { justify-content: flex-start; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }

.gap-xs { gap: var(--space-xs); }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }

/* Flex sizing */
.flex-1 { flex: 1; }
.flex-auto { flex: 1 1 auto; }
.flex-none { flex: none; }

/* Width */
.w-full { width: 100%; }
.w-auto { width: auto; }

/* Container */
.container {
  max-width: var(--container-width);
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-md);
  padding-right: var(--space-md);
}

.container-wide {
  max-width: var(--container-width-wide);
  margin-left: auto;
  margin-right: auto;
  padding-left: var(--space-md);
  padding-right: var(--space-md);
}
```

### Step 2.3: Text Utilities

```css
/* Font sizes */
.text-sm { font-size: var(--font-size-sm); }
.text-base { font-size: var(--font-size-base); }
.text-lg { font-size: var(--font-size-lg); }
.text-xl { font-size: var(--font-size-xl); }
.text-2xl { font-size: var(--font-size-2xl); }

/* Text alignment */
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }

/* Font weight */
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-bold { font-weight: 600; }

/* Text colors */
.text-primary { color: var(--color-primary); }
.text-success { color: var(--color-success); }
.text-gray-600 { color: var(--color-gray-600); }
.text-gray-800 { color: var(--color-gray-800); }
.text-white { color: white; }

/* Text decoration */
.no-underline { text-decoration: none; }
.underline { text-decoration: underline; }

/* White space */
.whitespace-nowrap { white-space: nowrap; }
```

### Step 2.4: Background & Border Utilities

```css
/* Background colors */
.bg-white { background-color: white; }
.bg-gray-50 { background-color: var(--color-gray-50); }
.bg-gray-100 { background-color: var(--color-gray-100); }
.bg-primary { background-color: var(--color-primary); }

/* Border radius */
.rounded { border-radius: var(--radius-sm); }
.rounded-md { border-radius: var(--radius-md); }
.rounded-lg { border-radius: var(--radius-lg); }

/* Borders */
.border { border: 1px solid var(--color-gray-200); }
.border-t { border-top: 1px solid var(--color-gray-200); }
.border-b { border-bottom: 1px solid var(--color-gray-200); }

/* Border width */
.border-2 { border-width: 2px; }

/* Border colors */
.border-primary { border-color: var(--color-primary); }
.border-gray-200 { border-color: var(--color-gray-200); }

/* Shadows */
.shadow-sm { box-shadow: var(--shadow-sm); }
.shadow-md { box-shadow: var(--shadow-md); }
.shadow-lg { box-shadow: var(--shadow-lg); }
```

---

## Phase 3: Component Classes

### Step 3.1: Buttons

```css
.btn {
  display: inline-block;
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-sm);
  text-decoration: none;
  font-weight: 500;
  font-size: var(--font-size-base);
  text-align: center;
  cursor: pointer;
  border: none;
  transition: opacity var(--transition-base);
  line-height: var(--line-height-tight);
}

.btn:hover {
  opacity: 0.9;
}

.btn:focus {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Button variants */
.btn-primary {
  background-color: var(--color-primary);
  color: white;
}

.btn-success {
  background-color: var(--color-success);
  color: white;
}

.btn-info {
  background-color: var(--color-info);
  color: white;
}

.btn-secondary {
  background-color: var(--color-gray-600);
  color: white;
}

.btn-danger {
  background-color: var(--color-danger);
  color: white;
}

/* Button sizes */
.btn-sm {
  padding: var(--space-xs) var(--space-md);
  font-size: var(--font-size-sm);
}

.btn-lg {
  padding: var(--space-md) var(--space-xl);
  font-size: var(--font-size-lg);
}

/* Button modifiers */
.btn-block {
  display: block;
  width: 100%;
}
```

### Step 3.2: Cards

```css
.card {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
}

.card-compact {
  padding: var(--space-lg);
}

.card-header {
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-md);
  border-bottom: 2px solid var(--color-gray-200);
}

.card-title {
  margin: 0;
  margin-bottom: var(--space-sm);
  color: var(--color-gray-800);
  font-size: var(--font-size-xl);
}

.card-body {
  /* Intentionally minimal - use utilities for spacing */
}

.card-footer {
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-gray-200);
}
```

### Step 3.3: Badges

```css
.badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  line-height: 1;
}

/* Badge variants */
.badge-primary {
  background-color: #e3f2fd;
  color: #1565c0;
}

.badge-success {
  background-color: #d4edda;
  color: #155724;
}

.badge-info {
  background-color: #d1ecf1;
  color: #0c5460;
}

.badge-warning {
  background-color: #fff3cd;
  color: #856404;
}

.badge-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.badge-purple {
  background-color: #f3e5f5;
  color: #6a1b9a;
}

.badge-orange {
  background-color: #ffe0b2;
  color: #e65100;
}
```

### Step 3.4: Forms

```css
.form-group {
  margin-bottom: var(--space-lg);
}

.form-label {
  display: block;
  margin-bottom: var(--space-sm);
  font-weight: 500;
  color: var(--color-gray-800);
  font-size: var(--font-size-base);
}

.form-input,
.form-textarea,
.form-select {
  display: block;
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-gray-800);
  background-color: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-sm);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.form-input:disabled,
.form-textarea:disabled,
.form-select:disabled {
  background-color: var(--color-gray-100);
  cursor: not-allowed;
  opacity: 0.6;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-help {
  display: block;
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
}

.form-error {
  display: block;
  margin-top: var(--space-xs);
  font-size: var(--font-size-sm);
  color: var(--color-danger);
}

/* Checkbox and radio */
.form-check {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.form-check-input {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.form-check-label {
  cursor: pointer;
  margin: 0;
  font-weight: normal;
}
```

### Step 3.5: Messages/Alerts

```css
.message,
.alert {
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
}

.message-success,
.alert-success {
  background-color: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

.message-error,
.alert-error,
.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
  border-color: #f5c6cb;
}

.message-warning,
.alert-warning {
  background-color: #fff3cd;
  color: #856404;
  border-color: #ffeaa7;
}

.message-info,
.alert-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border-color: #bee5eb;
}
```

### Step 3.6: Header/Navigation

```css
.site-header {
  background-color: var(--color-gray-800);
  color: white;
  padding: var(--space-md) 0;
  margin-bottom: var(--space-xl);
}

.site-header .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.site-title {
  font-size: var(--font-size-xl);
  margin: 0;
  font-weight: 600;
}

.site-nav {
  display: flex;
  gap: var(--space-md);
  align-items: center;
}

.site-nav a {
  color: white;
  text-decoration: none;
  transition: opacity var(--transition-base);
}

.site-nav a:hover {
  opacity: 0.8;
}
```

---

## Phase 4: Refactor Templates

### Priority Order

1. **base.html** - Foundation for everything
2. **dashboard/participant_dashboard.html** - Most visible to participants
3. **surveys/survey_detail.html** - Survey taking interface
4. **surveys/survey_list.html** - Researcher interface
5. **tasks/task_*.html** - Task interfaces
6. **home.html** - Landing page
7. **account/*.html** - Auth pages

### Example Refactor

**Before (inline styles):**
```html
<div style="border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; background-color: #fafafa;">
  <div style="display: flex; justify-content: space-between; align-items: start; gap: 1rem;">
    <div style="flex: 1;">
      <h3 style="margin-bottom: 0.5rem; color: #2c3e50;">{{ survey.title }}</h3>
      <p style="color: #666; margin-bottom: 1rem;">{{ survey.description }}</p>
      <span style="background-color: #e3f2fd; color: #1565c0; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem;">
        {{ survey.domain.name }}
      </span>
    </div>
    <div>
      <a href="..." style="display: inline-block; background-color: #3498db; color: white; padding: 0.75rem 1.5rem; border-radius: 4px; text-decoration: none; white-space: nowrap;">
        Start Survey
      </a>
    </div>
  </div>
</div>
```

**After (CSS classes):**
```html
<div class="card card-compact bg-gray-50">
  <div class="flex justify-between items-start gap-md">
    <div class="flex-1">
      <h3 class="mb-sm text-gray-800">{{ survey.title }}</h3>
      <p class="text-gray-600 mb-md">{{ survey.description }}</p>
      <span class="badge badge-primary">{{ survey.domain.name }}</span>
    </div>
    <div>
      <a href="..." class="btn btn-primary whitespace-nowrap">Start Survey</a>
    </div>
  </div>
</div>
```

### Templates to Refactor (Checklist)

- [ ] `templates/base.html`
- [ ] `templates/home.html`
- [ ] `templates/dashboard/participant_dashboard.html`
- [ ] `templates/surveys/survey_list.html`
- [ ] `templates/surveys/survey_detail.html`
- [ ] `templates/tasks/task_list.html`
- [ ] `templates/tasks/task_run.html`
- [ ] `templates/tasks/task_complete.html`
- [ ] `templates/account/login.html`
- [ ] `templates/account/signup.html`

---

## Phase 5: Enhancements & Polish

### Step 5.1: Responsive Design

Add media queries for mobile/tablet:

```css
/* Mobile - up to 640px */
@media (max-width: 640px) {
  .container {
    padding-left: var(--space-sm);
    padding-right: var(--space-sm);
  }

  .site-header .container {
    flex-direction: column;
    gap: var(--space-sm);
    text-align: center;
  }

  .card {
    padding: var(--space-md);
  }

  /* Stack buttons on mobile */
  .btn-group-mobile-stack {
    flex-direction: column;
  }

  .btn-group-mobile-stack .btn {
    width: 100%;
  }
}

/* Tablet - 641px to 1024px */
@media (min-width: 641px) and (max-width: 1024px) {
  .container {
    max-width: 100%;
  }
}
```

### Step 5.2: Accessibility Enhancements

```css
/* Focus visible for keyboard navigation */
*:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Skip to content link (hidden until focused) */
.skip-to-content {
  position: absolute;
  top: -100px;
  left: 0;
  background: var(--color-primary);
  color: white;
  padding: var(--space-sm) var(--space-md);
  text-decoration: none;
  z-index: 100;
}

.skip-to-content:focus {
  top: 0;
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .btn {
    border: 2px solid currentColor;
  }
}
```

### Step 5.3: Print Styles

```css
@media print {
  .site-header,
  .btn,
  .no-print {
    display: none !important;
  }

  .card {
    box-shadow: none;
    border: 1px solid #000;
    page-break-inside: avoid;
  }

  a {
    text-decoration: underline;
  }

  a[href^="http"]:after {
    content: " (" attr(href) ")";
  }
}
```

### Step 5.4: Create Documentation

Create `DESIGN_SYSTEM.md` documenting:
- Color palette with use cases
- Spacing scale
- Typography scale
- All available utility classes
- All component classes
- Usage examples
- Responsive breakpoints
- Accessibility considerations

---

## File Size Estimates

- **CSS Variables**: ~1-2KB
- **Utility Classes**: ~4-6KB
- **Component Classes**: ~4-6KB
- **Responsive/A11y**: ~1-2KB
- **Total**: ~10-15KB (unminified)
- **Gzipped**: ~3-5KB

Compare to frameworks:
- Bootstrap 5: ~200KB (unminified)
- Tailwind (full): ~3MB (before purge)
- Our system: ~15KB ✅

---

## Testing Checklist

### Browser Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### Responsive Testing
- [ ] Mobile (320px - 640px)
- [ ] Tablet (641px - 1024px)
- [ ] Desktop (1025px+)

### Accessibility Testing
- [ ] Keyboard navigation works
- [ ] Screen reader testing (NVDA/VoiceOver)
- [ ] Color contrast ratios pass WCAG AA
- [ ] Focus indicators visible
- [ ] Forms have proper labels

### Functionality Testing
- [ ] Survey taking works
- [ ] Task completion works
- [ ] Dashboard displays correctly
- [ ] Login/signup flows work
- [ ] Messages/alerts display properly

---

## Migration Strategy

### Approach 1: Big Bang (Faster)
1. Create complete `main.css`
2. Update `base.html` to include it
3. Refactor all templates in one session
4. Test everything
5. Deploy

**Pros:** Done quickly, no half-migrated state
**Cons:** Higher risk, harder to test incrementally

### Approach 2: Incremental (Safer)
1. Create complete `main.css`
2. Update `base.html` to include it (CSS won't break existing inline styles)
3. Refactor templates one at a time
4. Test each template as you go
5. Deploy when all templates refactored

**Pros:** Lower risk, easier to test, can deploy partially
**Cons:** Takes longer, temporary inconsistency

**Recommendation:** Use Approach 2 (Incremental)

---

## Next Steps

### Session 1:
1. Run audit of existing inline styles
2. Create `static/css/main.css` with all CSS variables
3. Add utility classes to `main.css`
4. Update `base.html` to link to new CSS file
5. Test that existing templates still work (CSS shouldn't break anything)

### Session 2:
1. Add all component classes to `main.css`
2. Refactor `base.html` structure
3. Refactor `participant_dashboard.html`
4. Test dashboard extensively

### Session 3:
1. Refactor survey templates
2. Refactor task templates
3. Test survey and task flows

### Session 4:
1. Refactor account templates
2. Add responsive design media queries
3. Add accessibility enhancements
4. Create `DESIGN_SYSTEM.md`

### Session 5:
1. Browser testing
2. Accessibility testing
3. Bug fixes and polish
4. Deploy!

---

## Resources

### CSS Custom Properties
- [MDN: Using CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)

### Accessibility
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [A11y Project](https://www.a11yproject.com/)

### Inspiration
- GitHub (minimal, clean design)
- Linear.app (modern, professional)
- Notion (clean forms and cards)

---

## Notes

- Keep classes semantic and readable
- Avoid over-abstracting - it's okay to repeat code sometimes
- Document unusual decisions in CSS comments
- Consider adding a build step later (PostCSS for autoprefixer, minification)
- Can add CSS nesting in the future if needed
- Keep mobile-first mindset when designing responsive patterns

---

## Success Metrics

- ✅ Zero inline styles in templates
- ✅ CSS file under 20KB
- ✅ All pages responsive on mobile
- ✅ WCAG AA contrast ratios
- ✅ Consistent spacing/colors across all pages
- ✅ Fast page loads (< 1s on 3G)
- ✅ Easy for future developers to understand and extend
