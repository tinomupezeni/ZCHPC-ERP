import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestDeleteDialog } from '../PurchaseRequestDeleteDialog';

describe('PurchaseRequestDeleteDialog', () => {
  it('is closed when requisitionNumber is null', () => {
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber={null}
        isDeleting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('names the request being deleted and warns it cannot be undone', () => {
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber="PR-0042"
        isDeleting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByText('Delete draft?')).toBeInTheDocument();
    expect(screen.getByText('PR-0042')).toBeInTheDocument();
    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
  });

  it('calls onConfirm when Delete Draft is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber="PR-0042"
        isDeleting={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /delete draft/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber="PR-0042"
        isDeleting={false}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when dismissed without clicking a button (e.g. Escape or overlay)', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber="PR-0042"
        isDeleting={false}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await user.keyboard('{Escape}');

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('disables both buttons and shows a deleting state while isDeleting is true', () => {
    render(
      <PurchaseRequestDeleteDialog
        requisitionNumber="PR-0042"
        isDeleting={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.getByRole('button', { name: /deleting/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
  });
});
