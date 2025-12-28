/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // OpenAI ChatGPT Apps SDK Design Tokens
        'ai-bg': {
          primary: 'var(--ai-color-bg-primary)',
          secondary: 'var(--ai-color-bg-secondary)',
          tertiary: 'var(--ai-color-bg-tertiary)',
        },
        'ai-text': {
          primary: 'var(--ai-color-text-primary)',
          secondary: 'var(--ai-color-text-secondary)',
          tertiary: 'var(--ai-color-text-tertiary)',
        },
        'ai-brand': {
          primary: 'var(--ai-color-brand-primary)',
          'primary-hover': 'var(--ai-color-brand-primary-hover)',
          success: 'var(--ai-color-brand-success)',
          warning: 'var(--ai-color-brand-warning)',
          error: 'var(--ai-color-brand-error)',
        },
        'ai-border': {
          light: 'var(--ai-color-border-light)',
          default: 'var(--ai-color-border-default)',
          heavy: 'var(--ai-color-border-heavy)',
        },
      },
      spacing: {
        'ai-0': 'var(--ai-spacing-0)',
        'ai-1': 'var(--ai-spacing-1)',
        'ai-2': 'var(--ai-spacing-2)',
        'ai-4': 'var(--ai-spacing-4)',
        'ai-6': 'var(--ai-spacing-6)',
        'ai-8': 'var(--ai-spacing-8)',
        'ai-10': 'var(--ai-spacing-10)',
        'ai-12': 'var(--ai-spacing-12)',
        'ai-16': 'var(--ai-spacing-16)',
        'ai-20': 'var(--ai-spacing-20)',
        'ai-24': 'var(--ai-spacing-24)',
        'ai-32': 'var(--ai-spacing-32)',
      },
      borderRadius: {
        'ai-none': 'var(--ai-radius-none)',
        'ai-sm': 'var(--ai-radius-sm)',
        'ai-md': 'var(--ai-radius-md)',
        'ai-base': 'var(--ai-radius-base)',
        'ai-lg': 'var(--ai-radius-lg)',
        'ai-xl': 'var(--ai-radius-xl)',
        'ai-full': 'var(--ai-radius-full)',
      },
      boxShadow: {
        'ai-0': 'var(--ai-elevation-0-shadow)',
        'ai-1': 'var(--ai-elevation-1-shadow)',
        'ai-2': 'var(--ai-elevation-2-shadow)',
        'ai-3': 'var(--ai-elevation-3-shadow)',
        'ai-4': 'var(--ai-elevation-4-shadow)',
        'ai-5': 'var(--ai-elevation-5-shadow)',
      },
      fontFamily: {
        'ai': 'var(--ai-font-family)',
      },
      fontSize: {
        'ai-h1': ['var(--ai-font-size-h1)', { lineHeight: 'var(--ai-line-height-h1)', fontWeight: 'var(--ai-font-weight-h1)', letterSpacing: 'var(--ai-letter-spacing-h1)' }],
        'ai-h2': ['var(--ai-font-size-h2)', { lineHeight: 'var(--ai-line-height-h2)', fontWeight: 'var(--ai-font-weight-h2)', letterSpacing: 'var(--ai-letter-spacing-h2)' }],
        'ai-h3': ['var(--ai-font-size-h3)', { lineHeight: 'var(--ai-line-height-h3)', fontWeight: 'var(--ai-font-weight-h3)', letterSpacing: 'var(--ai-letter-spacing-h3)' }],
        'ai-body': ['var(--ai-font-size-body)', { lineHeight: 'var(--ai-line-height-body)', fontWeight: 'var(--ai-font-weight-body)', letterSpacing: 'var(--ai-letter-spacing-body)' }],
        'ai-body-emph': ['var(--ai-font-size-body-emph)', { lineHeight: 'var(--ai-line-height-body-emph)', fontWeight: 'var(--ai-font-weight-body-emph)', letterSpacing: 'var(--ai-letter-spacing-body-emph)' }],
        'ai-body-small': ['var(--ai-font-size-body-small)', { lineHeight: 'var(--ai-line-height-body-small)', fontWeight: 'var(--ai-font-weight-body-small)', letterSpacing: 'var(--ai-letter-spacing-body-small)' }],
        'ai-body-small-emph': ['var(--ai-font-size-body-small-emph)', { lineHeight: 'var(--ai-line-height-body-small-emph)', fontWeight: 'var(--ai-font-weight-body-small-emph)', letterSpacing: 'var(--ai-letter-spacing-body-small-emph)' }],
        'ai-caption': ['var(--ai-font-size-caption)', { lineHeight: 'var(--ai-line-height-caption)', fontWeight: 'var(--ai-font-weight-caption)', letterSpacing: 'var(--ai-letter-spacing-caption)' }],
        'ai-button': ['var(--ai-font-size-button)', { lineHeight: 'var(--ai-line-height-button)', fontWeight: 'var(--ai-font-weight-button)', letterSpacing: 'var(--ai-letter-spacing-button)' }],
        'ai-badge': ['var(--ai-font-size-badge)', { lineHeight: 'var(--ai-line-height-badge)', fontWeight: 'var(--ai-font-weight-badge)', letterSpacing: 'var(--ai-letter-spacing-badge)' }],
      },
    },
  },
  plugins: [],
}
