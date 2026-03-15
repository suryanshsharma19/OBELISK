/**
 * Redux slice for UI state — theme, sidebar, toasts, etc.
 */

import { createSlice } from '@reduxjs/toolkit';
import { STORAGE_KEYS } from '../../utils/constants';

const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) || 'dark';

const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    theme: savedTheme,
    sidebarOpen: true,
    toasts: [],           // { id, message, type, duration }
    globalLoading: false,
  },
  reducers: {
    toggleTheme(state) {
      state.theme = state.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem(STORAGE_KEYS.THEME, state.theme);
    },
    setTheme(state, action) {
      state.theme = action.payload;
      localStorage.setItem(STORAGE_KEYS.THEME, state.theme);
    },
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
    addToast(state, action) {
      state.toasts.push({
        id: Date.now(),
        duration: 5000,
        type: 'info',
        ...action.payload,
      });
    },
    removeToast(state, action) {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload);
    },
    setGlobalLoading(state, action) {
      state.globalLoading = action.payload;
    },
  },
});

export const {
  toggleTheme,
  setTheme,
  toggleSidebar,
  addToast,
  removeToast,
  setGlobalLoading,
} = uiSlice.actions;
export default uiSlice.reducer;
