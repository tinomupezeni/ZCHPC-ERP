import { useEffect, useState } from 'react';
import { Loader2, Printer } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { comparativeScheduleService } from '@/services/comparative-schedule.service';
import type { ComparativeItem, ComparativeSchedule } from '@/types/comparative-schedule.types';

const emptyItem = (): ComparativeItem => ({ description: '', quantity: '', quotation_one_unit: '', quotation_one_total: '', quotation_two_unit: '', quotation_two_total: '' });
const checks = ['Requirement', 'Tax Clearance', 'PRA Registration'];
const statuses: Record<string, string> = { PENDING_DIRECTOR: 'Director', PENDING_PROCUREMENT: 'Procurement', PENDING_ACCOUNTS: 'Accounts', APPROVED: 'Approved', REJECTED: 'Rejected' };

export function ComparativeSchedulesPage() {
  const [items, setItems] = useState<ComparativeItem[]>([emptyItem(), emptyItem(), emptyItem(), emptyItem()]);
  const [compliance, setCompliance] = useState<Record<string, string>>({});
  const [recommendation, setRecommendation] = useState('');
  const [schedules, setSchedules] = useState<ComparativeSchedule[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const load = async () => { try { setSchedules(await comparativeScheduleService.getSchedules()); } catch { toast.error('Unable to load comparative schedules'); } };
  useEffect(() => { load(); }, []);
  const update = (index: number, field: keyof ComparativeItem, value: string) => setItems((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
  const submit = async (event: React.FormEvent) => { event.preventDefault(); const filled = items.filter((item) => item.description.trim()); if (!filled.length) { toast.error('Enter at least one item'); return; } setIsSubmitting(true); try { await comparativeScheduleService.createSchedule({ compliance, items: filled, recommendation }); toast.success('Comparative schedule submitted to Director'); setItems([emptyItem(), emptyItem(), emptyItem(), emptyItem()]); setCompliance({}); setRecommendation(''); await load(); } catch { toast.error('Unable to submit comparative schedule'); } finally { setIsSubmitting(false); } };
  return <div className="stores-page">
    <div className="stores-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="stores-paper comparative-paper" onSubmit={submit}>
      <header className="stores-header"><h1>COMPARATIVE SCHEDULE FOR THE PURCHASE OF</h1><img src="/logo.png" alt="ZCHPC" /></header>
      <table className="stores-table compliance-table"><thead><tr><th>Compliance Checklist</th><th>Compliant</th><th>Compliant</th></tr></thead><tbody>{checks.map((check) => <tr key={check}><td>{check}</td><td><input aria-label={`${check} supplier one`} value={compliance[`${check}_one`] || ''} onChange={(event) => setCompliance((current) => ({ ...current, [`${check}_one`]: event.target.value }))} placeholder="Compliant" /></td><td><input aria-label={`${check} supplier two`} value={compliance[`${check}_two`] || ''} onChange={(event) => setCompliance((current) => ({ ...current, [`${check}_two`]: event.target.value }))} placeholder="Compliant" /></td></tr>)}</tbody></table>
      <h2>Price Comparison</h2><table className="stores-table comparison-table"><thead><tr><th>Description</th><th>Qty.</th><th>Unit Price<br />USD</th><th>Total Price<br />USD</th><th>Unit Price<br />USD</th><th>Total Price<br />USD</th></tr></thead><tbody>{items.map((item, index) => <tr key={index}>{(['description', 'quantity', 'quotation_one_unit', 'quotation_one_total', 'quotation_two_unit', 'quotation_two_total'] as const).map((field) => <td key={field}><input aria-label={`Item ${index + 1} ${field}`} value={item[field]} onChange={(event) => update(index, field, event.target.value)} /></td>)}</tr>)}<tr><th colSpan={5}>GRAND TOTAL</th><td><input aria-label="Grand total" /></td></tr></tbody></table>
      <section className="recommendation"><h2>Recommendations:</h2><textarea value={recommendation} onChange={(event) => setRecommendation(event.target.value)} rows={4} /></section>
      <div className="comparison-signatures"><div>Compiled by: Procurement Officer: <span /></div><div>Signature <span /> Date <span /></div><div>Approved by: <span /></div><div>Signature <span /> Date <span /></div><strong>ZCHPC DIRECTOR</strong></div>
      <div className="stores-submit"><Button type="submit" disabled={isSubmitting}>{isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Submit Schedule</Button></div>
    </form>
    <section className="stores-history"><h2>Submitted Schedules</h2>{schedules.length ? schedules.map((schedule) => <p key={schedule.id}><strong>{schedule.schedule_number}</strong> | {statuses[schedule.status] || schedule.status}</p>) : <p>No comparative schedules submitted yet.</p>}</section>
  </div>;
}
export default ComparativeSchedulesPage;
