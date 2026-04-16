import React from 'react';
import { render, screen } from '@testing-library/react';

jest.mock('../../hooks/useWebSocket', () => ({
  __esModule: true,
  default: jest.fn(),
}));

import LiveFeed from './LiveFeed';
import useWebSocket from '../../hooks/useWebSocket';

describe('LiveFeed websocket updates', () => {
  it('shows connection status and appends incoming websocket messages', () => {
    const state = {
      connected: false,
      lastMessage: null,
      send: jest.fn(),
    };

    useWebSocket.mockImplementation(() => state);

    const { rerender } = render(<LiveFeed />);

    expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    expect(screen.getByText(/waiting for events/i)).toBeInTheDocument();

    state.connected = true;
    state.lastMessage = {
      timestamp: new Date().toISOString(),
      message: 'queued package suspicious-lib@1.0.0',
    };

    rerender(<LiveFeed />);

    expect(screen.getByText(/connected/i)).toBeInTheDocument();
    expect(
      screen.getByText(/queued package suspicious-lib@1\.0\.0/i),
    ).toBeInTheDocument();
  });
});
