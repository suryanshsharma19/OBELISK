// App entry point

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';

import App from './App';
import store from './store';
import './index.css';

// Suppress harmless ResizeObserver loop errors in the Webpack Dev Server overlay
const resizeObserverLoopErrRe = /^[^(ResizeObserver loop limit exceeded)]/;
window.addEventListener('error', e => {
  if (e.message === 'ResizeObserver loop limit exceeded' || e.message === 'ResizeObserver loop completed with undelivered notifications.') {
      const resizeObserverErrDiv = document.getElementById('webpack-dev-server-client-overlay-div');
      const resizeObserverErr = document.getElementById('webpack-dev-server-client-overlay');
      if (resizeObserverErr) {
          resizeObserverErr.style.display = 'none';
      }
      if (resizeObserverErrDiv) {
          resizeObserverErrDiv.style.display = 'none';
      }
  }
});

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  </React.StrictMode>,
);
