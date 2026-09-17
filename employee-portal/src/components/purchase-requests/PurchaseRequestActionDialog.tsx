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

interface PurchaseRequestActionDialogProps {
  /** The request awaiting confirmation, or null when the dialog should be closed. */
  requisitionNumber: string | null;
  isSubmitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  /**
   * Stage-specific copy (F17 Department Head "Approve", F18 Accounts
   * "Verify", F21 GM "Recommend"). All three default to the original
   * Department Head wording, so any existing caller that doesn't pass them
   * keeps behaving exactly as before.
   */
  title?: string;
  description?: string;
  confirmLabel?: string;
}

const DEFAULT_DESCRIPTION = 'This will send the request to Accounts for verification.';
const DEFAULT_CONFIRM_LABEL = 'Approve';

/**
 * In-flight label per confirmLabel. Most verbs just take "ing..." ("Verify"
 * -> "Verifying...", "Recommend" -> "Recommending..."); "Approve" is the one
 * irregular case (dropping the trailing "e"), so it's the only one that
 * needs an explicit override rather than the generic suffix rule below.
 */
const PENDING_LABELS: Record<string, string> = {
  Approve: 'Approving...',
};

/**
 * Confirmation before a reviewer takes their stage's terminal action on a
 * request (F17: Department Head "Approve"; F18: Accounts "Verify"; F21: GM
 * "Recommend"). A genuinely generic action-confirmation dialog - not named
 * or defaulted around any one verb beyond its historical Department Head
 * default - reused rather than duplicated per stage. The action itself
 * takes no payload - this is a plain confirm, not a form - so the only
 * state to manage is the in-flight spinner while the request is out.
 */
export function PurchaseRequestActionDialog({
  requisitionNumber,
  isSubmitting,
  onConfirm,
  onCancel,
  title,
  description = DEFAULT_DESCRIPTION,
  confirmLabel = DEFAULT_CONFIRM_LABEL,
}: PurchaseRequestActionDialogProps) {
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
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isSubmitting}>
            {isSubmitting ? (
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

export default PurchaseRequestActionDialog;
