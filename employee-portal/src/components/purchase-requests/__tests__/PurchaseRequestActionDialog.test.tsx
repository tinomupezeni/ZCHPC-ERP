import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestActionDialog } from '../PurchaseRequestActionDialog';

describe('PurchaseRequestActionDialog', () => {
  it('is closed when requisitionNumber is null', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber={null}
        isSubmitting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('names the request and explains what approving will do (Department Head default copy)', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
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
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
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
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />
    );

    await user.click(screen.getByRole('button', { name: /^approve$/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('disables both buttons and shows an approving state while isSubmitting is true', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={true}
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
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    await user.keyboard('{Escape}');

    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});

/**
 * F18: the dialog is reused for Accounts' "Verify" action via title/
 * description/confirmLabel props. These tests use custom copy exclusively -
 * every test above this point passes no such props, proving the Department
 * Head defaults are unchanged (F18 dialog-regression requirement).
 */
describe('PurchaseRequestActionDialog - stage-specific copy (F18 Accounts)', () => {
  it('renders custom title, description and confirm label when provided (Accounts "Verify" copy)', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        title="Verify PR-0042?"
        description="This will send the request to the General Manager for review."
        confirmLabel="Verify"
      />
    );

    expect(screen.getByText('Verify PR-0042?')).toBeInTheDocument();
    expect(
      screen.getByText('This will send the request to the General Manager for review.')
    ).toBeInTheDocument();
    expect(screen.queryByText(/approve/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^verify$/i })).toBeInTheDocument();
  });

  it('calls onConfirm when the custom confirm button is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
        title="Verify PR-0042?"
        description="This will send the request to the General Manager for review."
        confirmLabel="Verify"
      />
    );

    await user.click(screen.getByRole('button', { name: /^verify$/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('shows a "Verifying..." in-flight label (not "Approving...") for the Verify confirm label', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        title="Verify PR-0042?"
        description="This will send the request to the General Manager for review."
        confirmLabel="Verify"
      />
    );

    expect(screen.getByRole('button', { name: /verifying/i })).toBeDisabled();
    expect(screen.queryByText(/approving/i)).not.toBeInTheDocument();
  });
});

/**
 * F21: the same dialog reused a third time for GM's "Recommend" action -
 * proving the refactor to a genuinely generic action dialog actually
 * supports a verb neither Department Head nor Accounts used.
 */
describe('PurchaseRequestActionDialog - stage-specific copy (F21 GM)', () => {
  it('renders custom title, description and confirm label for GM "Recommend" copy', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        title="Recommend PR-0042?"
        description="This will send the request to the Director for review."
        confirmLabel="Recommend"
      />
    );

    expect(screen.getByText('Recommend PR-0042?')).toBeInTheDocument();
    expect(
      screen.getByText('This will send the request to the Director for review.')
    ).toBeInTheDocument();
    expect(screen.queryByText(/approve/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/verify/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^recommend$/i })).toBeInTheDocument();
  });

  it('calls onConfirm when the "Recommend" confirm button is clicked', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={false}
        onConfirm={onConfirm}
        onCancel={vi.fn()}
        title="Recommend PR-0042?"
        description="This will send the request to the Director for review."
        confirmLabel="Recommend"
      />
    );

    await user.click(screen.getByRole('button', { name: /^recommend$/i }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('shows a "Recommending..." in-flight label (not "Approving...") for the Recommend confirm label', () => {
    render(
      <PurchaseRequestActionDialog
        requisitionNumber="PR-0042"
        isSubmitting={true}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        title="Recommend PR-0042?"
        description="This will send the request to the Director for review."
        confirmLabel="Recommend"
      />
    );

    expect(screen.getByRole('button', { name: /recommending/i })).toBeDisabled();
    expect(screen.queryByText(/approving/i)).not.toBeInTheDocument();
  });
});
