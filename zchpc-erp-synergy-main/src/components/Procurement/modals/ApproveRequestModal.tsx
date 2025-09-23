import { approvePurchaseRequest, rejectPurchaseRequest } from "../api/procurementApi";
import { Button } from "@/components/ui/button";

interface Props {
  requestId: number;
  onClose: () => void;
  onActionComplete: () => void;
}

const ApproveRequestModal = ({ requestId, onClose, onActionComplete }: Props) => {

  const handleApprove = async () => {
    await approvePurchaseRequest(requestId, 1); // level 1 approval
    onActionComplete();
    onClose();
  };

  const handleReject = async () => {
    await rejectPurchaseRequest(requestId);
    onActionComplete();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
      <div className="bg-white p-6 rounded-lg w-96">
        <h2 className="text-lg font-bold mb-4">Manage Request #{requestId}</h2>
        <p>Do you want to approve or reject this purchase request?</p>
        <div className="mt-4 flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleReject} className="bg-red-500 text-white">Reject</Button>
          <Button onClick={handleApprove} className="bg-green-500 text-white">Approve</Button>
        </div>
      </div>
    </div>
  );
};

export default ApproveRequestModal;
