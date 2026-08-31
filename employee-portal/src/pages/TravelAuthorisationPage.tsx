import { useState } from 'react';
import { Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';

type FormKind = 'leave' | 'advance' | 'claim';
const formNames: Record<FormKind, string> = { leave: 'Application for Leave', advance: 'DSA Advance', claim: 'Travel Expense Claim' };

function Line({ label, wide = false }: { label: string; wide?: boolean }) {
  return <label className={wide ? 'official-line official-line-wide' : 'official-line'}><span>{label}</span><input aria-label={label} /></label>;
}

function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return <header className="official-header"><div className="official-crest" aria-hidden="true">ZCHPC</div><div className="official-heading"><strong>ZCHPC</strong><div>ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div><img src="/logo.png" alt="ZCHPC" /></header>;
}

function LeaveForm() {
  const leaveTypes = ['VACATION', 'SICK', 'MATERNITY', 'STUDY', 'SPECIAL/COMPASSIONATE', 'ANNUAL'];
  return <form className="official-paper leave-form" onSubmit={(event) => event.preventDefault()}><Header title="APPLICATION FOR LEAVE (HR 02)" subtitle="Confidential" /><div className="official-dash" /><table className="official-table leave-identity"><tbody>{['EMPLOYMENT CODE NUMBER', 'FULL NAMES', 'DESIGNATION', 'DEPARTMENT'].map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td></tr>)}</tbody></table><h2>LEAVE DETAILS</h2><table className="official-table leave-types"><thead><tr><th>TYPE OF LEAVE</th><th>PERIOD</th><th>NUMBER OF DAYS APPLIED</th></tr></thead><tbody>{leaveTypes.map((label) => <tr key={label}><td>{label}</td><td><input aria-label={`${label} period`} /></td><td><input aria-label={`${label} number of days`} /></td></tr>)}</tbody></table><p className="official-bold">Contact details while on leave:</p><Line label="Address" wide /><div className="official-two-lines"><Line label="Telephone" /><Line label="Email" /></div><div className="official-two-lines"><Line label="Signature of Applicant" /><Line label="Date" /></div><table className="official-table leave-approval"><thead><tr><th>Recommended/<br />not recommended</th><th>Recommended/<br />not recommended</th><th>Approved/Not Approved</th></tr></thead><tbody><tr><td>DEPARTMENT HEAD<span>....................<br />signature</span></td><td>HR DEPARTMENT<span>Number of Days accumulated<br />.................... signature</span></td><td>DIRECTOR/GENERAL MANAGER<span>.................... &nbsp;&nbsp;&nbsp;&nbsp; ....................<br />Signature &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date</span></td></tr></tbody></table></form>;
}

function PersonDetails() {
  return <section className="official-person-grid"><table className="official-table"><tbody>{['Full Name:', 'Department:', 'Telephone:', 'Station:', 'Address:'].map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td></tr>)}</tbody></table><table className="official-table"><tbody>{['ID No:', 'EC:', 'Position:'].map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td></tr>)}<tr className="budget-row"><th>Budget Code:</th><td><span>S &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; C</span><input aria-label="Budget code" /><input aria-label="Budget code second line" /><input aria-label="Budget code third line" /></td></tr></tbody></table></section>;
}

function FinanceUse() {
  return <table className="official-table finance-use"><caption>FINANCE USE ONLY</caption><tbody>{['Certified (A)', 'Reviewed (A)', 'Approved (GM)', 'Authorised (Director)'].map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td></tr>)}</tbody></table>;
}

function AdvanceForm() {
  const rows = ['Accommodation: Nights ____ Rate $____', 'Breakfast: Days ____ x Rate $____', 'Lunch: Days ____ x Rate $____', 'Dinner: Days ____ x Rate $____', 'Incidentals: Days ____ x Rate $____', 'Total Advanced'];
  return <form className="official-paper finance-form" onSubmit={(event) => event.preventDefault()}><Header title="DAILY SUBSISTENCE ALLOWANCE (DSA) ADVANCE FORM" subtitle="Complete and submit this form in hard copy to Accounts: REQUEST MUST BE MADE AT LEAST 2 DAYS BEFORE TRIP" /><PersonDetails /><div className="period-line">Period to be covered by Advance: <input aria-label="Advance period from" /> to <input aria-label="Advance period to" /> <span>S &nbsp;&nbsp;&nbsp; C</span></div><section className="finance-columns"><div><h2>BANKING DETAILS: ACCOUNT #:</h2><Line label="BANK" /><Line label="BRANCH" /><Line label="Programme" /><Line label="Activity" /><h2>DECLARATION</h2><p>I declare that the advance will be used only for the costs approved in the Budget and refund all un-used funds within 14 days from date of return</p><Line label="Signed" /><Line label="Dated" /><h2>AUTHORISATION</h2><p>I have authorised the above Officer to undertake the trip as per TA attached.</p><Line label="Name" /><Line label="Signature" /></div><table className="official-table allowance-table"><tbody>{rows.map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td><td /></tr>)}</tbody></table></section><FinanceUse /></form>;
}

function ClaimForm() {
  const rows = ['Telephone log attached', 'Toll-fees (receipts attached)', 'Other Incidental (receipts attached)', 'Subsistence (attach field report & TA)'];
  return <form className="official-paper finance-form" onSubmit={(event) => event.preventDefault()}><Header title="TRAVELLING & SUBSISTENCE EXPENSE CLAIM FORM" subtitle="Complete and submit this form in hard copy to FINANCE. CLAIMS MUST BE MADE WITHIN 14 DAYS OF INCURRING THE EXPENSE." /><PersonDetails /><div className="period-line">Summary of claim for the period: <input aria-label="Claim period from" /> To <input aria-label="Claim period to" /> (details overleaf) <span>S &nbsp;&nbsp;&nbsp; C</span></div><section className="finance-columns"><div><h2>BANKING DETAILS: &nbsp; A/C NAME:</h2><Line label="ACCOUNT NUMBER:" /><Line label="BANK" /><Line label="BRANCH:" /><Line label="CODE" /><Line label="Category:" /><Line label="Activity:" /><h2>DECLARATION</h2><p>I declare that the total expenses being claimed were incurred by me solely in the course of ZCHPC business. I agree to Finance rejecting my expense claim if the following attachments are missing: (1) Travel Authorisation (TA). (2) Field Report duly signed by me.</p><Line label="Signed" /><Line label="Dated" /><h2>AUTHORISATION</h2><p>This claim is correct and in order for payment.</p><Line label="Name" /><Line label="Signature" /></div><table className="official-table allowance-table"><tbody>{rows.map((label) => <tr key={label}><th>{label}</th><td><input aria-label={label} /></td><td /></tr>)}<tr><th>TOTAL EXPENSES CLAIMED</th><td /><td /></tr><tr><th>Less Advanced Dated:</th><td /><td /></tr><tr><th>RE-IMBURSEMENT/(REFUND)</th><td /><td /></tr></tbody></table></section><FinanceUse /></form>;
}

export function TravelAuthorisationPage() {
  const [activeForm, setActiveForm] = useState<FormKind>('leave');
  return <div className="official-forms-page"><div className="official-toolbar"><div><p className="eyebrow">ZCHPC DOCUMENTS</p><h2>Official forms</h2><p>Complete a form on screen, then print the original layout for signing and routing.</p></div><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div><div className="form-tabs" role="tablist">{(Object.keys(formNames) as FormKind[]).map((kind) => <button key={kind} type="button" role="tab" aria-selected={activeForm === kind} className={activeForm === kind ? 'active' : ''} onClick={() => setActiveForm(kind)}>{formNames[kind]}</button>)}</div>{activeForm === 'leave' && <LeaveForm />}{activeForm === 'advance' && <AdvanceForm />}{activeForm === 'claim' && <ClaimForm />}</div>;
}

export default TravelAuthorisationPage;
