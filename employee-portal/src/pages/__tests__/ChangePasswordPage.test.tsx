import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

// REM-07: an account holding a temporary password is kept on the
// change-password page until it replaces the password.
const mockAuth = {
  isAuthenticated: true,
  isLoading: false,
  employee: { must_change_password: true } as { must_change_password?: boolean } | null,
  changePassword: vi.fn(),
  logout: vi.fn(),
};
vi.mock('@/contexts/AuthContext', () => ({ useAuth: () => mockAuth }));
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const { ProtectedRoute, CHANGE_PASSWORD_PATH } = await import('@/components/ProtectedRoute');
const { ChangePasswordPage } = await import('../ChangePasswordPage');

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          path="/portal"
          element={
            <ProtectedRoute>
              <p>Dashboard</p>
            </ProtectedRoute>
          }
        />
        <Route
          path={CHANGE_PASSWORD_PATH}
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );
}

async function fill(current: string, next: string, confirm = next) {
  await userEvent.type(screen.getByLabelText('Temporary password'), current);
  await userEvent.type(screen.getByLabelText('New password'), next);
  await userEvent.type(screen.getByLabelText('Confirm new password'), confirm);
  await userEvent.click(screen.getByRole('button', { name: 'Change password' }));
}

describe('ChangePasswordPage', () => {
  beforeEach(() => {
    mockAuth.employee = { must_change_password: true };
    mockAuth.changePassword.mockReset();
  });

  it('redirects a temporary-password account away from other pages', () => {
    renderAt('/portal');
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.getByText('Change your password')).toBeInTheDocument();
  });

  it('lets a normal account through', () => {
    mockAuth.employee = { must_change_password: false };
    renderAt('/portal');
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('submits the change and continues to the portal', async () => {
    mockAuth.changePassword.mockImplementation(async () => {
      mockAuth.employee = { must_change_password: false };
    });
    renderAt(CHANGE_PASSWORD_PATH);

    await fill('Temp-123!abc', 'My-New-Passw0rd!');

    expect(mockAuth.changePassword).toHaveBeenCalledWith({
      current_password: 'Temp-123!abc',
      new_password: 'My-New-Passw0rd!',
    });
    expect(await screen.findByText('Dashboard')).toBeInTheDocument();
  });

  it('shows validation errors from the server and stays on the page', async () => {
    mockAuth.changePassword.mockRejectedValue({
      response: { data: { detail: 'x', errors: ['This password is too common.'] } },
    });
    renderAt(CHANGE_PASSWORD_PATH);

    await fill('Temp-123!abc', 'password123');

    expect(await screen.findByRole('alert')).toHaveTextContent('This password is too common.');
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
  });

  it('refuses mismatched confirmation without calling the server', async () => {
    renderAt(CHANGE_PASSWORD_PATH);
    await fill('Temp-123!abc', 'My-New-Passw0rd!', 'Something-Else1!');
    expect(await screen.findByRole('alert')).toHaveTextContent('The new passwords do not match.');
    expect(mockAuth.changePassword).not.toHaveBeenCalled();
  });
});
