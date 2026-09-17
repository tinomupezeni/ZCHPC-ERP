import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestRejectDialog } from '../PurchaseRequestRejectDialog';

describe('PurchaseRequestRejectDialog', () => {
  it('is closed when requisitionNumber is null', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber={null}
        reason=""
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('names the request being rejected', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason=""
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText('Reject PR-0042')).toBeInTheDocument();
    expect(
      screen.getByText('Please provide a reason for rejecting this request.')
    ).toBeInTheDocument();
  });

  it('keeps Confirm disabled while the reason is blank', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason=""
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeDisabled();
  });

  it('keeps Confirm disabled for a whitespace-only reason', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason="   "
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeDisabled();
  });

  it('enables Confirm once a non-blank reason is entered', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason="Budget code no longer active"
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /^reject$/i })).toBeEnabled();
  });

  it('calls onReasonChange as the reviewer types', async () => {
    const user = userEvent.setup();
    const onReasonChange = vi.fn();
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason=""
        onReasonChange={onReasonChange}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    await user.type(screen.getByLabelText(/reason/i), 'x');

    expect(onReasonChange).toHaveBeenCalledWith('x');
  });

  it('calls onConfirm when Reject is clicked with a valid reason', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason="Budget code no longer active"
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /^reject$/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason=""
        onReasonChange={vi.fn()}
        isRejecting={false}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel$/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('disables the reason field and both buttons while isRejecting is true', () => {
    render(
      <PurchaseRequestRejectDialog
        requisitionNumber="PR-0042"
        reason="Budget code no longer active"
        onReasonChange={vi.fn()}
        isRejecting={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByLabelText(/reason/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /rejecting/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /^cancel$/i })).toBeDisabled();
  });
});
