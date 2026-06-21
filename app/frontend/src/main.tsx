import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';
import { NodeProvider } from './contexts/node-context';
import { ThemeProvider } from './providers/theme-provider';
import { I18nProvider } from './i18n/I18nProvider';

import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <NodeProvider>
        <I18nProvider>
          <App />
        </I18nProvider>
      </NodeProvider>
    </ThemeProvider>
  </React.StrictMode>
);
