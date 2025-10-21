# Micro-Consent Pipeline Landing Page

A modern landing page for the Micro-Consent Pipeline project, built with Vite + React + Tailwind CSS.

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Deployment

### Vercel (Recommended)
1. Connect GitHub repository to Vercel
2. Set build settings:
   - Framework Preset: `Vite`
   - Root Directory: `landing-page`
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. Add custom domain: `microconsent.dev`

### Netlify
1. Connect GitHub repository to Netlify
2. Set build settings:
   - Base directory: `landing-page`
   - Build command: `npm run build`
   - Publish directory: `dist`
3. Add custom domain: `microconsent.dev`

## Features

- Responsive design with Tailwind CSS
- Hero section with CTA buttons
- Features showcase
- API documentation preview
- Metrics dashboard placeholder
- Footer with links

## Customization

Edit the components in `src/components/` to customize content:

- `Hero.jsx` - Main headline and CTA buttons
- `Features.jsx` - Feature grid
- `Docs.jsx` - API documentation section
- `Metrics.jsx` - Metrics dashboard placeholder
- `Footer.jsx` - Footer links and information