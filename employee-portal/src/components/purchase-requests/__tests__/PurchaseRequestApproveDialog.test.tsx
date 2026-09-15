import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestApproveDialog } from '../PurchaseRequestApproveDialog';

describe('PurchaseRequestApproveDialog', () => {
  it('is closed when requisitionNumber is null', () => {
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber={null}
        isApproving={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('names the request and explains what approving will do', () => {
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber="PR-0042"
        isApproving={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText('Approve PR-0042?')).toBeInTheDocument();
    expect(
      screen.getByText('This will send the request to Accounts for verification.')
    ).toBeInTheDocument();
  });

  it('calls onCancel and leaves the queue untouched when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber="PR-0042"
        isApproving={false}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('calls onConfirm when Approve is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber="PR-0042"
        isApproving={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('disables both buttons and shows an approving state while isApproving is true', () => {
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber="PR-0042"
        isApproving={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /approving/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();
  });

  it('calls onCancel when dismissed without clicking a button (Escape)', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <PurchaseRequestApproveDialog
        requisitionNumber="PR-0042"
        isApproving={false}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await user.keyboard('{Escape}');

    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
