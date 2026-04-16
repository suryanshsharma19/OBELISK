import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import AlertCard from './AlertCard';
import { markAlertRead, resolveAlert } from '../../store/slices/alertsSlice';

const mockDispatch = jest.fn();

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: () => mockDispatch,
}));

jest.mock('../../store/slices/alertsSlice', () => ({
  markAlertRead: jest.fn((id) => ({ type: 'alerts/markRead', payload: id })),
  resolveAlert: jest.fn((id) => ({ type: 'alerts/resolve', payload: id })),
}));

describe('AlertCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('dispatches mark-read and resolve actions', async () => {
    const user = userEvent.setup();

    render(
      <AlertCard
        alert={{
          id: 42,
          title: 'Suspicious postinstall script',
          description: 'package executes shell commands during install',
          threat_level: 'high',
          is_read: false,
          is_resolved: false,
          created_at: '2026-01-01T00:00:00Z',
        }}
      />,
    );

    await user.click(screen.getByRole('button', { name: /mark read/i }));
    await user.click(screen.getByRole('button', { name: /resolve/i }));

    expect(markAlertRead).toHaveBeenCalledWith(42);
    expect(resolveAlert).toHaveBeenCalledWith(42);
    expect(mockDispatch).toHaveBeenCalledTimes(2);
  });

  it('shows resolved state and hides action buttons', () => {
    render(
      <AlertCard
        alert={{
          id: 43,
          title: 'Resolved threat',
          description: '',
          threat_level: 'low',
          is_read: true,
          is_resolved: true,
          created_at: '2026-01-01T00:00:00Z',
        }}
      />,
    );

    expect(screen.getByText('Resolved')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /mark read/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /resolve/i })).not.toBeInTheDocument();
  });
});
