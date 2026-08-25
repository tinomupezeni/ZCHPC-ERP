import { useEffect, useState } from 'react';
import { Loader2, Printer } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { storesRequisitionService } from '@/services/stores-requisition.service';
import type { StoresItem, StoresRequisition } from '@/types/stores-requisition.types';

const emptyItem = (): StoresItem => ({ description: '', quantity_required: '', budget_code: '', required_by: '' });
const statuses: Record<string, string> = {
  PENDING_DEPARTMENT: 'Head of Dept.', PENDING_PROCUREMENT: 'Stores Officer',
  PENDING_ACCOUNTS: 'Finance', APPROVED: 'Approved', REJECTED: 'Rejected',
};

export function StoresRequisitionsPage() {
  const [items, setItems] = useState<StoresItem[]>([emptyItem(), emptyItem(), emptyItem(), emptyItem()]);
  const [requests, setRequests] = useState<StoresRequisition[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const loadRequests = async () => { try { setRequests(await storesRequisitionService.getRequests()); } catch { toast.error('Unable to load stores requisitions'); } };
  useEffect(() => { loadRequests(); }, []);
  const updateItem = (index: number, field: keyof StoresItem, value: string) => setItems((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const filled = items.filter((item) => item.description.trim());
    if (!filled.length || filled.some((item) => !item.quantity_required || !item.budget_code || !item.required_by)) { toast.error('Complete every field for each requested item'); return; }
    setIsSubmitting(true);
    try { await storesRequisitionService.createRequest({ items: filled }); toast.success('Stores requisition sent to Head of Department'); setItems([emptyItem(), emptyItem(), emptyItem(), emptyItem()]); await loadRequests(); }
    catch (error) { const message = (error as { response?: { data?: { error?: string } } }).response?.data?.error; toast.error(message || 'Unable to submit stores requisition'); }
    finally { setIsSubmitting(false); }
  };
  return <div className="stores-page">
    <div className="stores-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="stores-paper" onSubmit={submit}>
      <header className="stores-header"><h1>Stores Requisition Form</h1><img src="/logo.png" alt="ZCHPC" /><label>Requisition No: <input disabled placeholder="________________" /></label></header>
      <h2>Section A: Request Details</h2>
      <table className="stores-table"><thead><tr><th>Item Description</th><th>Quantity<br />Required</th><th>Budget Code</th><th>Required By<br />(Date):</th></tr></thead><tbody>{items.map((item, index) => <tr key={index}><td><input aria-label={`Item ${index + 1} description`} value={item.description} onChange={(event) => updateItem(index, 'description', event.target.value)} /></td><td><input aria-label={`Item ${index + 1} quantity`} value={item.quantity_required} onChange={(event) => updateItem(index, 'quantity_required', event.target.value)} /></td><td><input aria-label={`Item ${index + 1} budget code`} value={item.budget_code} onChange={(event) => updateItem(index, 'budget_code', event.target.value)} /></td><td><input aria-label={`Item ${index + 1} required date`} type="date" value={item.required_by} onChange={(event) => updateItem(index, 'required_by', event.target.value)} /></td></tr>)}</tbody></table>
      <h2>Section B: Approvals &amp; Signatures</h2><div className="approval-head"><span>Role</span><span>Name &amp; Signature</span><span>Date</span></div>{['Requester', 'Head of Dept.', 'Stores Officer', 'Finance'].map((role) => <div className="approval-line" key={role}><span>{role}</span><input aria-label={`${role} name and signature`} /><input aria-label={`${role} date`} type="date" /></div>)}
      <h2>Section C: Stores Action</h2><table className="stores-table action-table"><thead><tr><th>Item Issued</th><th>Quantity Issued</th><th>Balance in Stock:</th><th>Remarks:</th></tr></thead><tbody>{[1, 2, 3, 4].map((row) => <tr key={row}>{[1, 2, 3, 4].map((cell) => <td key={cell}><input aria-label={`Stores action row ${row} field ${cell}`} /></td>)}</tr>)}</tbody></table>
      <h2>Section D: Finance Confirmation</h2><table className="stores-table finance-table"><thead><tr><th>Budget Code Charged</th><th>Imputer</th><th>Date</th><th>Authorisation</th></tr></thead><tbody><tr><td><input /></td><td><input /></td><td><input type="date" /></td><td><input /></td></tr></tbody></table>
      <div className="stores-submit"><Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Submit Requisition</Button></div>
    </form>
    <section className="stores-history"><h2>Submitted Requisitions</h2>{requests.length ? requests.map((request) => <p key={request.id}><strong>{request.requisition_number}</strong> | {statuses[request.status] || request.status}</p>) : <p>No stores requisitions submitted yet.</p>}</section>
  </div>;
}
export default StoresRequisitionsPage;
