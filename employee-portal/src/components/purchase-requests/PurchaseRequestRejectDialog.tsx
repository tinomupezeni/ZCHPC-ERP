import { Loader2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PurchaseRequestRejectDialogProps {
  /** The request awaiting rejection confirmation, or null when the dialog should be closed. */
  requisitionNumber: string | null;
  reason: string;
  onReasonChange: (value: string) => void;
  isRejecting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * Rejection dialog (F17). Unlike approve, this always needs a non-blank
 * reason - the backend requires one too (allow_blank=False on
 * RejectPurchaseRequestInputSerializer) - so Confirm stays disabled until
 * the reviewer has actually typed something, not just whitespace.
 */
export function PurchaseRequestRejectDialog({
  requisitionNumber,
  reason,
  onReasonChange,
  isRejecting,
  onConfirm,
  onCancel,
}: PurchaseRequestRejectDialogProps) {
  const isReasonBlank = reason.trim().length === 0;

  return (
    <Dialog
      open={requisitionNumber !== null}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reject {requisitionNumber}</DialogTitle>
          <DialogDescription>
            Please provide a reason for rejecting this request.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="reject-reason">Reason</Label>
          <Textarea
            id="reject-reason"
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
            disabled={isRejecting}
            placeholder="Explain what needs to change..."
            rows={4}
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isRejecting}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={onConfirm}
            disabled={isRejecting || isReasonBlank}
          >
            {isRejecting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Rejecting...
              </>
            ) : (
              <>
                <XCircle className="mr-2 h-4 w-4" />
                Reject
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestRejectDialog;
