import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import AnalyzeForm from './AnalyzeForm';
import packagesReducer from '../../store/slices/packagesSlice';
import alertsReducer from '../../store/slices/alertsSlice';
import uiReducer from '../../store/slices/uiSlice';
import * as api from '../../services/api';

jest.mock('../../services/api', () => ({
  analyzePackage: jest.fn(),
}));

function createTestStore() {
  return configureStore({
    reducer: {
      packages: packagesReducer,
      alerts: alertsReducer,
      ui: uiReducer,
    },
  });
}

describe('AnalyzeForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows validation error when package name is missing', async () => {
    const user = userEvent.setup();
    const store = createTestStore();

    render(
      <Provider store={store}>
        <AnalyzeForm />
      </Provider>,
    );

    await user.click(screen.getByRole('button', { name: /analyze/i }));

    expect(screen.getByText(/package name is required/i)).toBeInTheDocument();
    expect(api.analyzePackage).not.toHaveBeenCalled();
  });

  it('shows validation error when version is missing', async () => {
    const user = userEvent.setup();
    const store = createTestStore();

    render(
      <Provider store={store}>
        <AnalyzeForm />
      </Provider>,
    );

    await user.type(screen.getByPlaceholderText(/e\.g\. express, lodash/i), 'express');
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    expect(screen.getByText(/version is required/i)).toBeInTheDocument();
    expect(api.analyzePackage).not.toHaveBeenCalled();
  });

  it('submits valid payload and shows completion toast', async () => {
    const user = userEvent.setup();
    const store = createTestStore();

    api.analyzePackage.mockResolvedValue({
      package: {
        id: 1,
        name: 'express',
        version: '4.18.2',
        registry: 'npm',
      },
      analysis: {
        risk_score: 5,
        threat_level: 'safe',
        is_malicious: false,
      },
      detection_details: {},
    });

    render(
      <Provider store={store}>
        <AnalyzeForm />
      </Provider>,
    );

    await user.type(screen.getByPlaceholderText(/e\.g\. express, lodash/i), 'express');
    await user.type(screen.getByPlaceholderText(/4\.18\.0/i), '4.18.2');
    await user.click(screen.getByRole('button', { name: /analyze/i }));

    await waitFor(() => {
      expect(api.analyzePackage).toHaveBeenCalledWith({
        name: 'express',
        version: '4.18.2',
        registry: 'npm',
        code: '',
      });
    });

    expect(store.getState().packages.analysisResult).not.toBeNull();
    expect(store.getState().ui.toasts.length).toBeGreaterThan(0);
  });
});
