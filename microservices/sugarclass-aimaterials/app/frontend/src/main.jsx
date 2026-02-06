import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './orchestrator-theme.css'
import './index.css'
import App from './App.jsx'

async function bootstrap() {
  // If MathJax readiness promise is available, wait for it before mounting the app.
  try {
    if (window.__MATHJAX_READY && typeof window.__MATHJAX_READY.then === 'function') {
      await Promise.race([
        window.__MATHJAX_READY,
        new Promise((_, reject) => setTimeout(() => reject(new Error('MathJax ready timeout')), 8000))
      ]);
    }
  } catch (e) {
    console.warn('MathJax did not become ready before app mount:', e);
  }

  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

bootstrap();