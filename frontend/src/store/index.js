/**
 * Redux store configuration.
 *
 * Combines all feature slices and applies middleware.
 * Exported as the single store instance used by <Provider>.
 */

import { configureStore } from '@reduxjs/toolkit';
import packagesReducer from './slices/packagesSlice';
import alertsReducer from './slices/alertsSlice';
import uiReducer from './slices/uiSlice';
import logger from './middleware/logger';

const store = configureStore({
  reducer: {
    packages: packagesReducer,
    alerts: alertsReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(
      process.env.NODE_ENV === 'development' ? [logger] : [],
    ),
  devTools: process.env.NODE_ENV !== 'production',
});

export default store;
