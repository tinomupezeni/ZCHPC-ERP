import { Loader2, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PurchaseRequestDeleteDialogProps {
  /** The draft pending deletion, or null when the dialog should be closed. */
  requisitionNumber: string | null;
  isDeleting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Confirmation before permanently deleting a DRAFT purchase request (Slice
 * 4) - there is no undo, so this is the one point where the employee is
 * asked to be sure before the backend call fires.
 */
export function PurchaseRequestDeleteDialog({
  requisitionNumber,
  isDeleting,
  onConfirm,
  onCancel,
}: PurchaseRequestDeleteDialogProps) {
  return (
    <Dialog
      open={requisitionNumber !== null}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete draft?</DialogTitle>
          <DialogDescription>
            {requisitionNumber && (
              <>
                This will permanently delete <strong>{requisitionNumber}</strong>. This
                cannot be undone.
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isDeleting}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Draft
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestDeleteDialog;
