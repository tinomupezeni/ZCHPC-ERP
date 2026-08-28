import { useState } from 'react';
import { Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';

type ClaimFields = Record<string, string>;

const initialFields: ClaimFields = {
  fullName: '', department: '', telephone: '', station: '', address: '', idNumber: '', ec: '', position: '',
  periodFrom: '', periodTo: '', accountNumber: '', bank: '', branch: '', code: '', category: '', activity: '',
  signed: '', dated: '', authorisedName: '', certified: '', reviewed: '', approved: '', authorised: '', advance: '', refund: '',
};

const claimRows = ['Telephone log attached', 'Toll-fees (receipts attached)', 'Other Incidental (receipts attached)', 'Subsistence (attach field report & TA)'];

export function TravelAuthorisationPage() {
  const [fields, setFields] = useState(initialFields);
  const updateField = (name: string, value: string) => setFields((current) => ({ ...current, [name]: value }));
  const input = (name: string, type = 'text') => <input aria-label={name} type={type} value={fields[name] ?? ''} onChange={(event) => updateField(name, event.target.value)} />;

  return <div className="ta-page">
    <div className="ta-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="claim-paper" onSubmit={(event) => event.preventDefault()}>
      <header className="claim-header"><div className="claim-crest">ZCHPC</div><div><div className="claim-brand">ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</div><h1>TRAVELLING &amp; SUBSISTENCE EXPENSE CLAIM FORM</h1><p>Complete and submit this form in hard copy to FINANCE. CLAIMS MUST BE MADE WITHIN 14 DAYS OF<br />INCURRING THE EXPENSE.</p></div><img src="/logo.png" alt="ZCHPC" /></header>
      <section className="claim-grid"><table><tbody><tr><th>Full Name:</th><td>{input('fullName')}</td></tr><tr><th>Department:</th><td>{input('department')}</td></tr><tr><th>Telephone:</th><td>{input('telephone')}</td></tr><tr><th>Station:</th><td>{input('station')}</td></tr><tr><th>Address:</th><td><textarea aria-label="address" value={fields.address} onChange={(event) => updateField('address', event.target.value)} /></td></tr></tbody></table><table><tbody><tr><th>ID No:</th><td>{input('idNumber')}</td></tr><tr><th>EC:</th><td>{input('ec')}</td></tr><tr><th>Position:</th><td>{input('position')}</td></tr><tr className="budget-code"><th>Budget code to be charged</th><td><span className="amount-head">S &nbsp;&nbsp;&nbsp;&nbsp; C</span>{Array.from({ length: 4 }, (_, index) => <input key={index} aria-label={`budget code ${index + 1}`} />)}</td></tr></tbody></table></section>
      <div className="claim-period">Summary of claim for the period: {input('periodFrom')} To {input('periodTo')} (details overleaf)</div>
      <section className="claim-middle"><div><table className="banking"><tbody><tr><th colSpan={2}>BANKING DETAILS: &nbsp; A/C NAME:</th></tr><tr><th>ACCOUNT NUMBER:</th><td>{input('accountNumber')}</td></tr><tr><th>BANK</th><td>{input('bank')} &nbsp; BRANCH: {input('branch')} &nbsp; CODE {input('code')}</td></tr></tbody></table><div className="claim-line">Category: {input('category')}</div><div className="claim-line">Activity: {input('activity')}</div><h2>DECLARATION</h2><p className="declaration">I declare that the total expenses being claimed were incurred by me solely in the course of ZCHPC business. I agree to Finance rejecting my expense claim if the following attachments are missing: (1) Travel Authorisation (TA). (2) Field Report duly signed by me.</p><div className="claim-line">Signed: {input('signed')}</div><div className="claim-line">Dated: {input('dated')}</div><h2 className="authorisation">AUTHORISATION</h2><p>This claim is correct and in order for payment.</p><div className="claim-line">Name: {input('authorisedName')}</div></div><table className="claim-expenses"><tbody>{claimRows.map((label) => <tr key={label}><th>{label}</th><td>{input(label)}</td><td>{input(`${label} cents`)}</td></tr>)}<tr className="total"><th>TOTAL EXPENSES CLAIMED</th><td>S</td><td>C</td></tr><tr><th>Less Advanced Dated:</th><td>{input('advance')}</td><td /></tr><tr><th>RE-IMBURSEMENT/(REFUND)</th><td>{input('refund')}</td><td /></tr></tbody></table></section>
      <table className="finance-only"><caption>FINANCE USE ONLY</caption><tbody><tr><th>Certified (A)</th><td>{input('certified')}</td></tr><tr><th>Reviewed (A)</th><td>{input('reviewed')}</td></tr><tr><th>Approved (GM)</th><td>{input('approved')}</td></tr><tr><th>Authorised<br />(Director)</th><td>{input('authorised')}</td></tr></tbody></table>
    </form>
  </div>;
}

export default TravelAuthorisationPage;
