import { useEffect, useState } from 'react';
import { Loader2, Printer } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { fuelRequisitionService } from '@/services/fuel-requisition.service';
import type { FuelRequisition } from '@/types/fuel-requisition.types';

export function FuelRequisitionsPage() {
  const [requests, setRequests] = useState<FuelRequisition[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({ programme: '', recipient_driver: '', requester_signature: '', vehicle_registration: '', request_date: new Date().toISOString().slice(0, 10), diesel_quantity: '', diesel_quantity_words: '', petrol_quantity: '', petrol_quantity_words: '', purpose: '', destination: '', destination_dates: '' });
  const update = (field: string, value: string) => setForm((current) => ({ ...current, [field]: value }));
  const loadRequests = async () => { try { setRequests(await fuelRequisitionService.getRequests()); } catch { toast.error('Unable to load fuel requisitions'); } };
  useEffect(() => { loadRequests(); }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.diesel_quantity && !form.petrol_quantity) { toast.error('Enter a diesel or petrol quantity'); return; }
    setIsSubmitting(true);
    try {
      await fuelRequisitionService.createRequest({ ...form, diesel_quantity: Number(form.diesel_quantity || 0), petrol_quantity: Number(form.petrol_quantity || 0) });
      toast.success('Fuel requisition sent to your department');
      setForm((current) => ({ ...current, programme: '', recipient_driver: '', requester_signature: '', vehicle_registration: '', diesel_quantity: '', diesel_quantity_words: '', petrol_quantity: '', petrol_quantity_words: '', purpose: '', destination: '', destination_dates: '' }));
      await loadRequests();
    } catch (error) {
      const message = (error as { response?: { data?: { error?: string } } }).response?.data?.error;
      toast.error(message || 'Unable to submit fuel requisition');
    } finally { setIsSubmitting(false); }
  };

  const field = (id: keyof typeof form, label: string, type = 'text') => (
    <label className="paper-field" htmlFor={id}>
      <span>{label}</span>
      <input id={id} type={type} value={form[id]} onChange={(event) => update(id, event.target.value)} required={id !== 'programme' && id !== 'requester_signature'} />
    </label>
  );

  return <div className="fuel-page">
    <div className="fuel-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="fuel-paper" onSubmit={submit}>
      <header className="fuel-header">
        <h1>ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</h1>
        <img src="/logo.png" alt="ZCHPC" />
        <h2>FUEL REQUISITION FORM</h2>
      </header>
      <section className="paper-identity">
        {field('programme', 'Programme')}
        <label className="paper-field" htmlFor="department"><span>Department</span><input id="department" value="Assigned from employee profile" disabled /></label>
        {field('recipient_driver', 'Recipient / Driver Name')}
        {field('requester_signature', 'Signature')}
        {field('request_date', 'Date', 'date')}
        {field('vehicle_registration', 'Vehicle Reg No.')}
      </section>
      <table className="fuel-table"><thead><tr><th>Description</th><th>Quantity requested<br />(Figures)</th><th>Quantity requested (Words)</th></tr></thead><tbody>
        <tr><th>Diesel</th><td><input id="diesel_quantity" type="number" min="0" step="0.01" value={form.diesel_quantity} onChange={(event) => update('diesel_quantity', event.target.value)} /></td><td><input id="diesel_quantity_words" value={form.diesel_quantity_words} onChange={(event) => update('diesel_quantity_words', event.target.value)} /></td></tr>
        <tr><th>Petrol</th><td><input id="petrol_quantity" type="number" min="0" step="0.01" value={form.petrol_quantity} onChange={(event) => update('petrol_quantity', event.target.value)} /></td><td><input id="petrol_quantity_words" value={form.petrol_quantity_words} onChange={(event) => update('petrol_quantity_words', event.target.value)} /></td></tr>
      </tbody></table>
      <section className="paper-block"><h3>Purpose of request</h3><textarea id="purpose" rows={4} value={form.purpose} onChange={(event) => update('purpose', event.target.value)} required /></section>
      <section className="paper-row">{field('destination', 'Destination')}{field('destination_dates', 'Date(s)')}</section>
      <section className="approval-block"><h3>Recommended by Finance and Administration Manager</h3><div className="signature-row"><span>Name</span><span>Signature</span><span>Date</span></div><h3>Approved by ZCHPC Director</h3><div className="signature-row"><span>Name</span><span>Signature</span><span>Date</span></div></section>
      <section className="paper-block issuance"><h3>Details of issuance:</h3><div className="dotted-line">Quantity Issued (Figures and Words)</div><div className="dotted-line">Serial Number(s)</div><div className="signature-row"><span>Issued by</span><span>Signature</span><span>Date</span></div><div className="signature-row"><span>Received by</span><span>Signature</span><span>Date</span></div></section>
      <div className="fuel-submit"><Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Submit Fuel Request</Button></div>
    </form>
    <section className="fuel-history"><h2>Submitted forms</h2>{requests.length === 0 ? <p>No fuel requests submitted yet.</p> : requests.map((request) => <p key={request.id}>FR-{request.id}: {request.status}</p>)}</section>
  </div>;
}
export default FuelRequisitionsPage;
