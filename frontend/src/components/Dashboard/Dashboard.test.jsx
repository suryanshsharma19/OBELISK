import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';

import Dashboard from './Dashboard';
import { getStatsOverview, getStatsTrend } from '../../services/api';
import { fetchAlerts } from '../../store/slices/alertsSlice';

const mockDispatch = jest.fn();
const mockState = {
  alerts: {
    list: [
      {
        id: 101,
        title: 'Critical dependency chain detected',
        threat_level: 'critical',
        created_at: '2026-01-01T00:00:00Z',
      },
    ],
    total: 1,
    unreadCount: 1,
    loading: false,
    error: null,
  },
};

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../services/api', () => ({
  getStatsOverview: jest.fn(),
  getStatsTrend: jest.fn(),
}));

jest.mock('../../store/slices/alertsSlice', () => ({
  fetchAlerts: jest.fn((params) => ({
    type: 'alerts/fetchAllRequested',
    payload: params,
  })),
}));

jest.mock('./ThreatChart', () => () => (
  <div data-testid="threat-chart">Mock Threat Chart</div>
));

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useDispatch.mockReturnValue(mockDispatch);
    useSelector.mockImplementation((selector) => selector(mockState));
  });

  it('loads overview stats and renders recent alerts', async () => {
    getStatsOverview.mockResolvedValue({
      total_packages: 1024,
      malicious_packages: 12,
      active_alerts: 5,
      scans_24h: 256,
      threat_distribution: {
        safe: 900,
        low: 80,
        medium: 30,
        high: 10,
        critical: 4,
      },
    });
    getStatsTrend.mockResolvedValue({
      trend: [{ date: '2026-01-01', scanned: 25, threats: 3 }],
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(getStatsOverview).toHaveBeenCalledTimes(1);
      expect(getStatsTrend).toHaveBeenCalledWith(7);
    });

    await screen.findByRole('heading', { name: 'Dashboard' });

    expect(fetchAlerts).toHaveBeenCalledWith({ limit: 5 });
    expect(mockDispatch).toHaveBeenCalled();
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.getByText('1.0K')).toBeInTheDocument();
    expect(screen.getByText('Malicious Detected')).toBeInTheDocument();
    expect(screen.getByText('Critical dependency chain detected')).toBeInTheDocument();
    expect(screen.getByTestId('threat-chart')).toBeInTheDocument();
  });
});
