/**
 * Redux slice for package state — list, detail, and analysis.
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as api from '../../services/api';

/* ── Async thunks ────────────────────────────────────────────── */

export const fetchPackages = createAsyncThunk(
  'packages/fetchAll',
  async (params = {}, { rejectWithValue }) => {
    try {
      return await api.getPackages(params);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

export const fetchPackageDetail = createAsyncThunk(
  'packages/fetchDetail',
  async (id, { rejectWithValue }) => {
    try {
      return await api.getPackageDetail(id);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

export const analyzePackage = createAsyncThunk(
  'packages/analyze',
  async (payload, { rejectWithValue }) => {
    try {
      return await api.analyzePackage(payload);
    } catch (err) {
      return rejectWithValue(err.message);
    }
  },
);

/* ── Slice ───────────────────────────────────────────────────── */

const packagesSlice = createSlice({
  name: 'packages',
  initialState: {
    list: [],
    total: 0,
    detail: null,
    analysisResult: null,
    loading: false,
    analyzing: false,
    error: null,
  },
  reducers: {
    clearAnalysisResult(state) {
      state.analysisResult = null;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchPackages
      .addCase(fetchPackages.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPackages.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload.packages;
        state.total = action.payload.total;
      })
      .addCase(fetchPackages.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // fetchPackageDetail
      .addCase(fetchPackageDetail.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPackageDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.detail = action.payload;
      })
      .addCase(fetchPackageDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // analyzePackage
      .addCase(analyzePackage.pending, (state) => {
        state.analyzing = true;
        state.error = null;
        state.analysisResult = null;
      })
      .addCase(analyzePackage.fulfilled, (state, action) => {
        state.analyzing = false;
        state.analysisResult = action.payload;
      })
      .addCase(analyzePackage.rejected, (state, action) => {
        state.analyzing = false;
        state.error = action.payload;
      });
  },
});

export const { clearAnalysisResult, clearError } = packagesSlice.actions;
export default packagesSlice.reducer;
