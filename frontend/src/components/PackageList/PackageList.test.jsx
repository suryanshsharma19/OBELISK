import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import PackageList from './PackageList';
import { fetchPackages } from '../../store/slices/packagesSlice';

const mockDispatch = jest.fn();
const mockState = {
  packages: {
    list: [
      {
        id: 1,
        name: 'alpha',
        version: '1.0.0',
        registry: 'npm',
        threat_level: 'low',
        risk_score: 10,
        analyzed_at: '2026-01-01T00:00:00Z',
      },
    ],
    total: 45,
    loading: false,
    error: null,
  },
};

jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../store/slices/packagesSlice', () => ({
  fetchPackages: jest.fn((params) => ({
    type: 'packages/fetchRequested',
    payload: params,
  })),
}));

describe('PackageList filters and pagination', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useDispatch.mockReturnValue(mockDispatch);
    useSelector.mockImplementation((selector) => selector(mockState));
  });

  it('requests pages and resets pagination when filters change', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <PackageList />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(fetchPackages).toHaveBeenCalledWith({
        skip: 0,
        limit: 20,
        sort: 'analyzed_at_desc',
      });
    });

    await user.click(screen.getByRole('button', { name: '2' }));

    await waitFor(() => {
      expect(fetchPackages).toHaveBeenLastCalledWith({
        skip: 20,
        limit: 20,
        sort: 'analyzed_at_desc',
      });
    });

    const selects = screen.getAllByRole('combobox');
    await user.selectOptions(selects[0], 'high');

    await waitFor(() => {
      expect(fetchPackages).toHaveBeenLastCalledWith({
        skip: 0,
        limit: 20,
        threat_level: 'high',
        sort: 'analyzed_at_desc',
      });
    });

    expect(mockDispatch).toHaveBeenCalled();
  });
});
