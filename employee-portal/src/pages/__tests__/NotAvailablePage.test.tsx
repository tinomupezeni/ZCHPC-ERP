import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { NotAvailablePage } from '../NotAvailablePage';

/** The placeholder for every page this version leaves out. */
describe('Coming soon page', () => {
  const renderAt = (path: string) =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/portal" element={<p>dashboard</p>} />
          <Route path="/portal/payslips" element={<NotAvailablePage />} />
        </Routes>
      </MemoryRouter>
    );

  it('says "Coming soon" and why, never "evaluation"', () => {
    renderAt('/portal/payslips');

    expect(screen.getByRole('heading', { name: 'Coming soon' })).toBeTruthy();
    expect(
      screen.getByText("This module is being built and isn't part of this version yet.")
    ).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/evaluation|not available/i);
  });

  it('goes back to the dashboard', () => {
    renderAt('/portal/payslips');

    fireEvent.click(screen.getByRole('link', { name: /back to dashboard/i }));

    expect(screen.getByText('dashboard')).toBeTruthy();
  });
});
