import { CheckCircle2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface PurchaseRequestProcessDialogProps {
  /** The request awaiting processing confirmation, or null when the dialog should be closed. */
  requisitionNumber: string | null;
  purchaseOrderNumber: string;
  onPurchaseOrderNumberChange: (value: string) => void;
  isProcessing: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * F23: Procurement's processing confirmation dialog.
 *
 * Unlike Approve (no input) and Reject (a reason), this stage requires the
 * Procurement Officer to manually enter a Purchase Order number - never
 * auto-generated, and distinct from the request's own requisition_number
 * (PR-xxxxx). The backend requires a non-blank value (F23's
 * ProcessPurchaseRequestInputSerializer/process_by_procurement), so Confirm
 * stays disabled until something has actually been typed, mirroring
 * PurchaseRequestRejectDialog's own reason guard.
 */
export function PurchaseRequestProcessDialog({
  requisitionNumber,
  purchaseOrderNumber,
  onPurchaseOrderNumberChange,
  isProcessing,
  onConfirm,
  onCancel,
}: PurchaseRequestProcessDialogProps) {
  const isPoNumberBlank = purchaseOrderNumber.trim().length === 0;

  return (
    <Dialog
      open={requisitionNumber !== null}
      onOpenChange={(open) => {
        if (!open) onCancel();
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Process {requisitionNumber}</DialogTitle>
          <DialogDescription>
            Enter the Purchase Order number for this request. Processing moves the
            request to its final state and cannot be undone.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="purchase-order-number">Purchase Order Number</Label>
          <Input
            id="purchase-order-number"
            value={purchaseOrderNumber}
            onChange={(e) => onPurchaseOrderNumberChange(e.target.value)}
            disabled={isProcessing}
            placeholder="e.g. PO-2026-00042"
            autoComplete="off"
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onCancel} disabled={isProcessing}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={onConfirm}
            disabled={isProcessing || isPoNumberBlank}
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Process
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PurchaseRequestProcessDialog;
