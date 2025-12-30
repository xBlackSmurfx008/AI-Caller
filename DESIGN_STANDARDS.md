# Design Standards — AI Caller

This document defines the UI/UX standards for the AI Caller CRM + Orchestrator app. All new features must follow these guidelines.

---

## 1. Color System

### Dark Theme (Recommended)

The app uses a dark theme with purple accents to match the "Godfather" power user aesthetic.

```css
/* Core Colors */
--bg-primary: #0f172a;        /* slate-900 - Main background */
--bg-secondary: #1e293b;      /* slate-800 - Card backgrounds */
--bg-tertiary: #334155;       /* slate-700 - Elevated surfaces */

/* Text Colors */
--text-primary: #ffffff;       /* White - Primary text */
--text-secondary: #94a3b8;     /* slate-400 - Secondary text */
--text-muted: #64748b;         /* slate-500 - Muted text */

/* Accent Colors */
--accent-primary: #8b5cf6;     /* violet-500 - Primary accent */
--accent-secondary: #6366f1;   /* indigo-500 - Secondary accent */
--accent-gradient: linear-gradient(to right, #8b5cf6, #6366f1);

/* Semantic Colors */
--success: #10b981;            /* emerald-500 */
--warning: #f59e0b;            /* amber-500 */
--error: #ef4444;              /* red-500 */
--info: #3b82f6;               /* blue-500 */

/* AI Indicator */
--ai-purple: #a855f7;          /* purple-500 - AI actions */
--ai-bg: rgba(168, 85, 247, 0.1);
```

### Usage Rules

1. **Never use white backgrounds** for cards — use `bg-slate-800/50` or `bg-slate-900/50`
2. **Always use dark borders** — `border-slate-700` not `border-gray-200`
3. **Text on dark backgrounds** must be white or slate-300/400
4. **Accent colors** for primary actions, links, and AI-related elements

---

## 2. Typography

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Type Scale

| Element | Size | Weight | Class |
|---------|------|--------|-------|
| Page Title | 30px | Bold (700) | `text-3xl font-bold` |
| Section Title | 24px | Semibold (600) | `text-2xl font-semibold` |
| Card Title | 18px | Semibold (600) | `text-lg font-semibold` |
| Body | 16px | Normal (400) | `text-base` |
| Small | 14px | Normal (400) | `text-sm` |
| Caption | 12px | Medium (500) | `text-xs font-medium` |

### Text Color Application

```tsx
// Primary text (white on dark)
className="text-white"

// Secondary text
className="text-slate-400"

// Muted/helper text
className="text-slate-500"

// Success state
className="text-emerald-400"

// Warning state
className="text-amber-400"

// Error state
className="text-red-400"

// AI-related
className="text-purple-400"
```

---

## 3. Component Patterns

### Cards

Use the Card component with dark theme overrides:

```tsx
<Card className="bg-slate-900/50 border-slate-700">
  <CardHeader>
    <CardTitle className="text-white">Title</CardTitle>
  </CardHeader>
  <CardContent>
    {/* content */}
  </CardContent>
</Card>
```

### Buttons

| Variant | Use Case | Style |
|---------|----------|-------|
| `primary` | Primary actions | Purple gradient, white text |
| `secondary` | Secondary actions | Gray background, dark text |
| `outline` | Tertiary actions | Border only, transparent bg |
| `ghost` | Subtle actions | No border, transparent bg |
| `danger` | Destructive actions | Red background |

```tsx
// Primary action
<Button variant="primary">Save</Button>

// Secondary action
<Button variant="secondary">Cancel</Button>

// Destructive
<Button variant="danger">Delete</Button>
```

### Badges & Status Indicators

```tsx
// Success/Ready
className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400"

// Warning/Partial
className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400"

// Error/Blocked
className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400"

// Info/AI
className="px-2 py-1 rounded text-xs bg-purple-500/20 text-purple-400"

// Neutral
className="px-2 py-1 rounded text-xs bg-slate-500/20 text-slate-400"
```

### Lists

```tsx
// List container
<div className="space-y-3">
  {/* List items */}
</div>

// List item (selectable)
<div className={`p-3 rounded-lg cursor-pointer transition-colors ${
  isSelected ? 'bg-purple-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-white'
}`}>
```

---

## 4. AI Output Patterns

### AI Suggestions

Always show AI suggestions with:
1. Purple accent indicator
2. Rationale/explanation
3. Risk flags if applicable
4. Clear action buttons

```tsx
<div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
  <div className="flex items-center gap-2 mb-2">
    <Sparkles className="w-4 h-4 text-purple-400" />
    <span className="text-sm font-medium text-purple-400">AI Suggestion</span>
  </div>
  <p className="text-white mb-2">{suggestion.content}</p>
  {suggestion.rationale && (
    <p className="text-sm text-slate-400 mb-3">{suggestion.rationale}</p>
  )}
  {suggestion.risk_flags?.length > 0 && (
    <div className="text-xs text-amber-400 mb-3">
      ⚠️ {suggestion.risk_flags.join(', ')}
    </div>
  )}
  <div className="flex gap-2">
    <Button size="sm" variant="primary">Accept</Button>
    <Button size="sm" variant="ghost">Dismiss</Button>
  </div>
</div>
```

### AI Explanations

When AI explains a decision:

```tsx
<div className="flex items-start gap-3 bg-slate-800/50 rounded-lg p-3">
  <Lightbulb className="w-4 h-4 text-blue-400 mt-0.5" />
  <div>
    <p className="text-sm font-medium text-white mb-1">Why this recommendation</p>
    <p className="text-sm text-slate-400">{explanation}</p>
  </div>
</div>
```

### AI Actions Pending

For actions awaiting user approval:

```tsx
<div className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
  <Clock className="w-4 h-4 text-amber-400" />
  <div className="flex-1">
    <p className="text-sm font-medium text-white">Awaiting Approval</p>
    <p className="text-xs text-slate-400">{description}</p>
  </div>
  <div className="flex gap-2">
    <Button size="sm" variant="primary">Approve</Button>
    <Button size="sm" variant="ghost">Reject</Button>
  </div>
</div>
```

---

## 5. Confirmation Patterns

### Before Destructive Actions

Always confirm before:
- Deleting data
- Sending messages
- Executing AI tasks with external effects

```tsx
// Simple confirmation
if (window.confirm(`Delete ${item.name}?`)) {
  deleteItem(item.id);
}

// Complex confirmation (use modal)
<ConfirmationModal
  title="Send Message?"
  description="This will send an SMS to John Doe at +1234567890"
  confirmLabel="Send"
  cancelLabel="Cancel"
  onConfirm={handleSend}
  onCancel={closeModal}
/>
```

### Approval Patterns

For AI-initiated actions requiring approval:

1. **Show what will happen** — Clear description of action
2. **Show who/what is affected** — Contact name, project, etc.
3. **Show risk level** — Visual indicator if sensitive
4. **Provide approve/reject** — Clear action buttons
5. **Allow editing** — Option to modify before approving

```tsx
<Card className="bg-indigo-900/30 border-indigo-700/50">
  <CardContent className="py-4">
    <h3 className="font-semibold text-white mb-2">Pending Approval</h3>
    <p className="text-sm text-slate-300 mb-4">{action.description}</p>
    
    {action.risk_level === 'high' && (
      <div className="flex items-center gap-2 text-amber-400 text-sm mb-4">
        <AlertTriangle className="w-4 h-4" />
        <span>High sensitivity action</span>
      </div>
    )}
    
    <div className="flex gap-2">
      <Button variant="primary" onClick={approve}>Approve</Button>
      <Button variant="ghost" onClick={edit}>Edit</Button>
      <Button variant="ghost" onClick={reject}>Reject</Button>
    </div>
  </CardContent>
</Card>
```

---

## 6. Risk Flag Styles

### Severity Levels

```tsx
// Critical (P0) — Red
<div className="flex items-center gap-2 text-red-400">
  <AlertCircle className="w-4 h-4" />
  <span>Critical</span>
</div>

// Warning (P1) — Amber
<div className="flex items-center gap-2 text-amber-400">
  <AlertTriangle className="w-4 h-4" />
  <span>Warning</span>
</div>

// Info (P2/P3) — Blue
<div className="flex items-center gap-2 text-blue-400">
  <Lightbulb className="w-4 h-4" />
  <span>Info</span>
</div>
```

### Trust Indicators

```tsx
// Fully autonomous (AI can do alone)
<span className="px-2 py-1 rounded text-xs bg-emerald-500/20 text-emerald-400">
  ✅ Autonomous
</span>

// Partial (AI needs some help/approval)
<span className="px-2 py-1 rounded text-xs bg-amber-500/20 text-amber-400">
  🟡 Partial
</span>

// Blocked (requires human action)
<span className="px-2 py-1 rounded text-xs bg-red-500/20 text-red-400">
  🔴 Blocked
</span>
```

---

## 7. Loading & Empty States

### Loading State

Always use the Loader2 spinner from lucide-react:

```tsx
// Centered loading
<div className="flex items-center justify-center py-12">
  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
</div>

// Inline loading
<Button disabled>
  <Loader2 className="w-4 h-4 animate-spin mr-2" />
  Loading...
</Button>
```

### Empty States

Every empty state must have:
1. Icon or illustration
2. Friendly message
3. Primary action button

```tsx
<div className="text-center py-12">
  <Sparkles className="w-12 h-12 text-slate-400 mx-auto mb-4" />
  <p className="text-slate-400 mb-4">No projects yet</p>
  <Button variant="primary">Create your first project</Button>
</div>
```

### Error States

```tsx
<Card>
  <CardContent className="py-12 text-center">
    <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
    <p className="text-red-400 font-semibold mb-2">Failed to load data</p>
    <p className="text-slate-400 text-sm mb-4">{error.message}</p>
    <Button variant="primary" onClick={retry}>Try Again</Button>
  </CardContent>
</Card>
```

---

## 8. Terminology Standards

Use consistent terminology throughout the app:

| Concept | Use | Don't Use |
|---------|-----|-----------|
| People | Contact | User, Person, Lead |
| To-do items | Task | Todo, Item, Action |
| Multi-task groups | Project | Goal, Objective |
| User approval | Approval | Confirmation, Permission |
| AI recommendation | Suggestion | Recommendation, Advice |
| Contact history | Memory | History, Data, Profile |
| Saved preferences | Trusted List | Favorites, Defaults, Preferences |
| Execution plan | PEC | Plan, Confirmation |

---

## 9. Spacing & Layout

### Container Widths

```tsx
// Full-width with responsive padding
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

// Narrower for focused content
<div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

// Even narrower for forms/settings
<div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
```

### Spacing Scale

| Size | Value | Use |
|------|-------|-----|
| 2 | 8px | Within components |
| 3 | 12px | Small gaps |
| 4 | 16px | Standard gaps |
| 6 | 24px | Section gaps |
| 8 | 32px | Large gaps |

```tsx
// Grid with gaps
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

// Stacked sections
<div className="space-y-6">

// Form fields
<div className="space-y-4">
```

---

## 10. Accessibility

### Minimum Requirements

1. **Color Contrast:** 4.5:1 for normal text, 3:1 for large text
2. **Focus States:** All interactive elements must have visible focus
3. **Touch Targets:** Minimum 44x44px for buttons on mobile
4. **Screen Readers:** Use semantic HTML, aria-labels where needed
5. **Keyboard Navigation:** All features accessible via keyboard

### Focus Styles

```css
:focus {
  outline: none;
  ring: 2px;
  ring-offset: 2px;
  ring-color: purple-500;
}
```

### Screen Reader Support

```tsx
// Hidden label for icon-only buttons
<Button aria-label="Delete contact">
  <Trash2 className="w-4 h-4" />
</Button>

// Announce loading states
<div role="status" aria-live="polite">
  {isLoading && <span className="sr-only">Loading...</span>}
</div>
```

---

## 11. Mobile Considerations

### Bottom Navigation

- Maximum 5 items visible
- Icons with short labels
- Active state clearly visible
- Safe area for iOS home indicator

### Touch Targets

- Buttons: minimum 44px height
- List items: minimum 48px height
- Action buttons in messages: larger for easy tapping

### Responsive Breakpoints

| Breakpoint | Width | Use |
|------------|-------|-----|
| `sm` | 640px | Small tablets, large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small laptops |
| `xl` | 1280px | Desktops |

---

## 12. Animation Guidelines

### Transitions

```css
/* Standard transition */
transition: all 150ms ease;

/* Slow transitions for larger changes */
transition: all 300ms ease;
```

### Loading Animations

```tsx
// Spinner
<Loader2 className="w-6 h-6 animate-spin" />

// Pulse for skeleton
<div className="animate-pulse bg-slate-700 rounded h-4 w-24" />
```

### Hover States

```tsx
// Cards
className="hover:shadow-lg transition-shadow"

// List items
className="hover:bg-slate-700 transition-colors"

// Buttons
className="hover:from-purple-700 hover:to-indigo-700"
```

---

*These standards are living documentation. Update as the design system evolves.*

