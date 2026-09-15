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
}

/**
 * Confirmation before a department head approves a request (F17). Approving
 * takes no payload - this is a plain confirm, not a form - so the only state
 * to manage is the in-flight spinner while the request is out.
 */
export function PurchaseRequestApproveDialog({
  requisitionNumber,
  isApproving,
  onConfirm,
  onCancel,
}: PurchaseRequestApproveDialogProps) {
  return (
    <Dialog
      open={requisitionNumber !== null}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Approve {requisitionNumber}?</DialogTitle>
          <DialogDescription>
            This will send the request to Accounts for verification.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isApproving}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isApproving}>
            {isApproving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Approving...
              </>
            ) : (
              <>
                <CheckCircle className="mr-2 h-4 w-4" />
                Approve
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestApproveDialog;
