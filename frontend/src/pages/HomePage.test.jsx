import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen } from '@testing-library/react';

import HomePage from './HomePage';

describe('HomePage', () => {
  it('renders the hero title and primary CTA', () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/protect your supply chain/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /analyze a package/i })).toBeInTheDocument();
  });
});
