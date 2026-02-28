/**
 * Redux slice for alerts — list, unread count, and actions.
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as api from '../../services/api';

export const fetchAlerts = createAsyncThunk(
  'alerts/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      return await api.getAlerts(params);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

export const resolveAlert = createAsyncThunk(
  'alerts/resolve',
  async (alertId, { rejectWithValue }) => {
    try {
      await api.updateAlert(alertId, { is_resolved: true });
      return alertId;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

export const markAlertRead = createAsyncThunk(
  'alerts/markRead',
  async (alertId, { rejectWithValue }) => {
    try {
      await api.updateAlert(alertId, { is_read: true });
      return alertId;
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

const alertsSlice = createSlice({
  name: 'alerts',
  initialState: {
    list: [],
    total: 0,
    unreadCount: 0,
    loading: false,
    error: null,
  },
  reducers: {
    clearAlertError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAlerts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAlerts.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.alerts;
        state.total = action.payload.total;
        state.unreadCount = action.payload.unread_count || 0;
      })
      .addCase(fetchAlerts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(resolveAlert.fulfilled, (state, action) => {
        const idx = state.list.findIndex((a) => a.id === action.payload);
        if (idx !== -1) state.list[idx].is_resolved = true;
      })
      .addCase(markAlertRead.fulfilled, (state, action) => {
        const idx = state.list.findIndex((a) => a.id === action.payload);
        if (idx !== -1) {
          state.list[idx].is_read = true;
          state.unreadCount = Math.max(0, state.unreadCount - 1);
        }
      });
  },
});

export const { clearAlertError } = alertsSlice.actions;
export default alertsSlice.reducer;
