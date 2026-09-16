import { CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PurchaseRequestApproveDialogProps {
  /** The request awaiting approval confirmation, or null when the dialog should be closed. */
  requisitionNumber: string | null;
  isApproving: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  /**
   * Stage-specific copy (F18: reused for Accounts' "Verify" action, and
   * intended for GM/Director later). All three default to the original
   * Department Head wording, so any existing caller that doesn't pass them
   * keeps behaving exactly as before.
   */
  title?: string;
  description?: string;
  confirmLabel?: string;
}

const DEFAULT_DESCRIPTION = 'This will send the request to Accounts for verification.';
const DEFAULT_CONFIRM_LABEL = 'Approve';

/** In-flight label per confirmLabel - "Approving..."/"Verifying..." aren't a simple suffix rule. */
const PENDING_LABELS: Record<string, string> = {
  Approve: 'Approving...',
  Verify: 'Verifying...',
};

/**
 * Confirmation before a reviewer approves/verifies a request at their stage
 * (F17: Department Head "Approve"; F18: Accounts "Verify"). The action
 * itself takes no payload - this is a plain confirm, not a form - so the
 * only state to manage is the in-flight spinner while the request is out.
 */
export function PurchaseRequestApproveDialog({
  requisitionNumber,
  isApproving,
  onConfirm,
  onCancel,
  title,
  description = DEFAULT_DESCRIPTION,
  confirmLabel = DEFAULT_CONFIRM_LABEL,
}: PurchaseRequestApproveDialogProps) {
  const pendingLabel = PENDING_LABELS[confirmLabel] ?? `${confirmLabel}ing...`;

  return (
    <Dialog
      open={requisitionNumber !== null}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title ?? `${DEFAULT_CONFIRM_LABEL} ${requisitionNumber}?`}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isApproving}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isApproving}>
            {isApproving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                {pendingLabel}
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                {confirmLabel}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestApproveDialog;
