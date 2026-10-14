import { useState } from 'react';
import { Printer, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';

type FormKind = 'leave' | 'advance' | 'claim';
const formNames: Record<FormKind, string> = {
  leave: 'Application for Leave (HR 02)',
  advance: 'DSA Advance Form',
  claim: 'Travel Expense Claim Form',
};

function Line({
  label,
  value,
  onChange,
  placeholder,
  readOnly = false,
  wide = false,
}: {
  label: string;
  value?: string;
  onChange?: (val: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  wide?: boolean;
}) {
  return (
    <label className={wide ? 'official-line official-line-wide' : 'official-line'}>
      <span>{label}</span>
      <input
        aria-label={label}
        value={value ?? ''}
        placeholder={placeholder}
        onChange={(e) => onChange?.(e.target.value)}
        readOnly={readOnly}
      />
    </label>
  );
}

function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="official-header">
      <div className="official-crest" aria-hidden="true">
        ZCHPC
      </div>
      <div className="official-heading">
        <strong>ZCHPC</strong>
        <div>ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <img src="/logo.png" alt="ZCHPC" />
    </header>
  );
}

function LeaveForm() {
  const { employee } = useAuth();
  const fullName =
    employee?.full_name || `${employee?.first_name || ''} ${employee?.surname || ''}`.trim();
  const today = new Date().toISOString().slice(0, 10);

  const [address, setAddress] = useState('');
  const [telephone, setTelephone] = useState(employee?.phone || '');
  const [email, setEmail] = useState(employee?.email || '');
  const [signature, setSignature] = useState(fullName);
  const [date, setDate] = useState(today);

  const leaveTypes = ['VACATION', 'SICK', 'MATERNITY', 'STUDY', 'SPECIAL/COMPASSIONATE', 'ANNUAL'];
  const [leaveDays, setLeaveDays] = useState<Record<string, { period: string; days: string }>>({
    ANNUAL: { period: '', days: '' },
  });

  return (
    <form className="official-paper leave-form" onSubmit={(event) => event.preventDefault()}>
      <Header title="APPLICATION FOR LEAVE (HR 02)" subtitle="Confidential" />
      <div className="official-dash" />

      {/* Auto-filled Identity Table (From active Employee Profile) */}
      <table className="official-table leave-identity">
        <tbody>
          <tr>
            <th>EMPLOYMENT CODE NUMBER</th>
            <td>
              <input value={employee?.employee_id || 'EC-0001'} readOnly />
            </td>
          </tr>
          <tr>
            <th>FULL NAMES</th>
            <td>
              <input value={fullName || 'Staff Member'} readOnly />
            </td>
          </tr>
          <tr>
            <th>DESIGNATION</th>
            <td>
              <input value={employee?.position_title || 'Officer'} readOnly />
            </td>
          </tr>
          <tr>
            <th>DEPARTMENT</th>
            <td>
              <input value={employee?.department_name || 'Technical'} readOnly />
            </td>
          </tr>
        </tbody>
      </table>

      <h2>LEAVE DETAILS</h2>
      <table className="official-table leave-types">
        <thead>
          <tr>
            <th>TYPE OF LEAVE</th>
            <th>PERIOD</th>
            <th>NUMBER OF DAYS APPLIED</th>
          </tr>
        </thead>
        <tbody>
          {leaveTypes.map((label) => (
            <tr key={label}>
              <td>{label}</td>
              <td>
                <input
                  aria-label={`${label} period`}
                  placeholder="e.g. 20 Oct - 25 Oct 2026"
                  value={leaveDays[label]?.period || ''}
                  onChange={(e) =>
                    setLeaveDays((c) => ({
                      ...c,
                      [label]: { ...c[label], period: e.target.value, days: c[label]?.days || '' },
                    }))
                  }
                />
              </td>
              <td>
                <input
                  aria-label={`${label} number of days`}
                  type="number"
                  min="1"
                  placeholder="e.g. 5"
                  value={leaveDays[label]?.days || ''}
                  onChange={(e) =>
                    setLeaveDays((c) => ({
                      ...c,
                      [label]: { ...c[label], days: e.target.value, period: c[label]?.period || '' },
                    }))
                  }
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="official-bold">Contact details while on leave:</p>
      <Line label="Address" wide value={address} onChange={setAddress} />
      <div className="official-two-lines">
        <Line label="Telephone" value={telephone} onChange={setTelephone} />
        <Line label="Email" value={email} onChange={setEmail} />
      </div>
      <div className="official-two-lines">
        <Line label="Signature of Applicant" value={signature} onChange={setSignature} />
        <Line label="Date" value={date} onChange={setDate} />
      </div>

      <table className="official-table leave-approval">
        <thead>
          <tr>
            <th>
              Recommended/
              <br />
              not recommended
            </th>
            <th>
              Recommended/
              <br />
              not recommended
            </th>
            <th>Approved/Not Approved</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              DEPARTMENT HEAD
              <span>
                ....................
                <br />
                signature
              </span>
            </td>
            <td>
              HR DEPARTMENT
              <span>
                Number of Days accumulated
                <br />
                .................... signature
              </span>
            </td>
            <td>
              DIRECTOR/GENERAL MANAGER
              <span>
                .................... &nbsp;&nbsp;&nbsp;&nbsp; ....................
                <br />
                Signature &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Date
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </form>
  );
}

function PersonDetails() {
  const { employee } = useAuth();
  const fullName =
    employee?.full_name || `${employee?.first_name || ''} ${employee?.surname || ''}`.trim();

  return (
    <section className="official-person-grid">
      <table className="official-table">
        <tbody>
          <tr>
            <th>Full Name:</th>
            <td>
              <input value={fullName || ''} readOnly />
            </td>
          </tr>
          <tr>
            <th>Department:</th>
            <td>
              <input value={employee?.department_name || ''} readOnly />
            </td>
          </tr>
          <tr>
            <th>Telephone:</th>
            <td>
              <input value={employee?.phone || employee?.email || ''} readOnly />
            </td>
          </tr>
          <tr>
            <th>Station:</th>
            <td>
              <input defaultValue="Harare Head Office" />
            </td>
          </tr>
          <tr>
            <th>Address:</th>
            <td>
              <input defaultValue="ZCHPC Complex, UZ Campus, Harare" />
            </td>
          </tr>
        </tbody>
      </table>

      <table className="official-table">
        <tbody>
          <tr>
            <th>ID No:</th>
            <td>
              <input placeholder="National ID" />
            </td>
          </tr>
          <tr>
            <th>EC:</th>
            <td>
              <input value={employee?.employee_id || ''} readOnly />
            </td>
          </tr>
          <tr>
            <th>Position:</th>
            <td>
              <input value={employee?.position_title || ''} readOnly />
            </td>
          </tr>
          <tr className="budget-row">
            <th>Budget Code:</th>
            <td>
              <span>S &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; C</span>
              <input aria-label="Budget code" placeholder="TRV-2026-01" />
              <input aria-label="Budget code second line" />
              <input aria-label="Budget code third line" />
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

function FinanceUse() {
  return (
    <table className="official-table finance-use">
      <caption>FINANCE USE ONLY</caption>
      <tbody>
        {['Certified (A)', 'Reviewed (A)', 'Approved (GM)', 'Authorised (Director)'].map((label) => (
          <tr key={label}>
            <th>{label}</th>
            <td>
              <input aria-label={label} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function AdvanceForm() {
  const { employee } = useAuth();
  const fullName =
    employee?.full_name || `${employee?.first_name || ''} ${employee?.surname || ''}`.trim();
  const today = new Date().toISOString().slice(0, 10);

  const [periodFrom, setPeriodFrom] = useState('');
  const [periodTo, setPeriodTo] = useState('');
  const [bank, setBank] = useState('');
  const [branch, setBranch] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [programme, setProgramme] = useState('HPC Technical Operations');
  const [activity, setActivity] = useState('Site Support');

  // Allowance items state with auto-calculation
  const [accommodationNights, setAccommodationNights] = useState('');
  const [accommodationRate, setAccommodationRate] = useState('');
  const [breakfastDays, setBreakfastDays] = useState('');
  const [breakfastRate, setBreakfastRate] = useState('');
  const [lunchDays, setLunchDays] = useState('');
  const [lunchRate, setLunchRate] = useState('');
  const [dinnerDays, setDinnerDays] = useState('');
  const [dinnerRate, setDinnerRate] = useState('');
  const [incidentalsDays, setIncidentalsDays] = useState('');
  const [incidentalsRate, setIncidentalsRate] = useState('');

  const calc = (q: string, r: string) => {
    const qty = Number.parseFloat(q) || 0;
    const rate = Number.parseFloat(r) || 0;
    return qty > 0 && rate > 0 ? (qty * rate).toFixed(2) : '';
  };

  const total = [
    Number.parseFloat(calc(accommodationNights, accommodationRate)) || 0,
    Number.parseFloat(calc(breakfastDays, breakfastRate)) || 0,
    Number.parseFloat(calc(lunchDays, lunchRate)) || 0,
    Number.parseFloat(calc(dinnerDays, dinnerRate)) || 0,
    Number.parseFloat(calc(incidentalsDays, incidentalsRate)) || 0,
  ].reduce((a, b) => a + b, 0);

  return (
    <form className="official-paper finance-form" onSubmit={(event) => event.preventDefault()}>
      <Header
        title="DAILY SUBSISTENCE ALLOWANCE (DSA) ADVANCE FORM"
        subtitle="Complete and submit this form in hard copy to Accounts: REQUEST MUST BE MADE AT LEAST 2 DAYS BEFORE TRIP"
      />
      <PersonDetails />

      <div className="period-line">
        Period to be covered by Advance:{' '}
        <input
          aria-label="Advance period from"
          type="date"
          value={periodFrom}
          onChange={(e) => setPeriodFrom(e.target.value)}
        />{' '}
        to{' '}
        <input
          aria-label="Advance period to"
          type="date"
          value={periodTo}
          onChange={(e) => setPeriodTo(e.target.value)}
        />{' '}
        <span>S &nbsp;&nbsp;&nbsp; C</span>
      </div>

      <section className="finance-columns">
        <div>
          <h2>BANKING DETAILS: ACCOUNT #:</h2>
          <Line label="ACCOUNT NUMBER" value={accountNumber} onChange={setAccountNumber} />
          <Line label="BANK" value={bank} onChange={setBank} />
          <Line label="BRANCH" value={branch} onChange={setBranch} />
          <Line label="Programme" value={programme} onChange={setProgramme} />
          <Line label="Activity" value={activity} onChange={setActivity} />

          <h2>DECLARATION</h2>
          <p>
            I declare that the advance will be used only for the costs approved in the Budget and refund
            all un-used funds within 14 days from date of return
          </p>
          <Line label="Signed" value={fullName} readOnly />
          <Line label="Dated" value={today} readOnly />

          <h2>AUTHORISATION</h2>
          <p>I have authorised the above Officer to undertake the trip as per TA attached.</p>
          <Line label="Name" placeholder="Authorising Manager" />
          <Line label="Signature" placeholder="Approved electronically" />
        </div>

        <table className="official-table allowance-table">
          <tbody>
            <tr>
              <th>
                Accommodation: Nights{' '}
                <input
                  style={{ width: 35, display: 'inline-block' }}
                  type="number"
                  placeholder="0"
                  value={accommodationNights}
                  onChange={(e) => setAccommodationNights(e.target.value)}
                />{' '}
                x Rate ${' '}
                <input
                  style={{ width: 45, display: 'inline-block' }}
                  type="number"
                  placeholder="0.00"
                  value={accommodationRate}
                  onChange={(e) => setAccommodationRate(e.target.value)}
                />
              </th>
              <td>${calc(accommodationNights, accommodationRate) || '0.00'}</td>
              <td />
            </tr>
            <tr>
              <th>
                Breakfast: Days{' '}
                <input
                  style={{ width: 35, display: 'inline-block' }}
                  type="number"
                  placeholder="0"
                  value={breakfastDays}
                  onChange={(e) => setBreakfastDays(e.target.value)}
                />{' '}
                x Rate ${' '}
                <input
                  style={{ width: 45, display: 'inline-block' }}
                  type="number"
                  placeholder="0.00"
                  value={breakfastRate}
                  onChange={(e) => setBreakfastRate(e.target.value)}
                />
              </th>
              <td>${calc(breakfastDays, breakfastRate) || '0.00'}</td>
              <td />
            </tr>
            <tr>
              <th>
                Lunch: Days{' '}
                <input
                  style={{ width: 35, display: 'inline-block' }}
                  type="number"
                  placeholder="0"
                  value={lunchDays}
                  onChange={(e) => setLunchDays(e.target.value)}
                />{' '}
                x Rate ${' '}
                <input
                  style={{ width: 45, display: 'inline-block' }}
                  type="number"
                  placeholder="0.00"
                  value={lunchRate}
                  onChange={(e) => setLunchRate(e.target.value)}
                />
              </th>
              <td>${calc(lunchDays, lunchRate) || '0.00'}</td>
              <td />
            </tr>
            <tr>
              <th>
                Dinner: Days{' '}
                <input
                  style={{ width: 35, display: 'inline-block' }}
                  type="number"
                  placeholder="0"
                  value={dinnerDays}
                  onChange={(e) => setDinnerDays(e.target.value)}
                />{' '}
                x Rate ${' '}
                <input
                  style={{ width: 45, display: 'inline-block' }}
                  type="number"
                  placeholder="0.00"
                  value={dinnerRate}
                  onChange={(e) => setDinnerRate(e.target.value)}
                />
              </th>
              <td>${calc(dinnerDays, dinnerRate) || '0.00'}</td>
              <td />
            </tr>
            <tr>
              <th>
                Incidentals: Days{' '}
                <input
                  style={{ width: 35, display: 'inline-block' }}
                  type="number"
                  placeholder="0"
                  value={incidentalsDays}
                  onChange={(e) => setIncidentalsDays(e.target.value)}
                />{' '}
                x Rate ${' '}
                <input
                  style={{ width: 45, display: 'inline-block' }}
                  type="number"
                  placeholder="0.00"
                  value={incidentalsRate}
                  onChange={(e) => setIncidentalsRate(e.target.value)}
                />
              </th>
              <td>${calc(incidentalsDays, incidentalsRate) || '0.00'}</td>
              <td />
            </tr>
            <tr style={{ background: '#f5f5f5', fontWeight: 'bold' }}>
              <th>Total Advanced</th>
              <td>${total > 0 ? total.toFixed(2) : '0.00'}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </section>

      <FinanceUse />
    </form>
  );
}

function ClaimForm() {
  const { employee } = useAuth();
  const fullName =
    employee?.full_name || `${employee?.first_name || ''} ${employee?.surname || ''}`.trim();
  const today = new Date().toISOString().slice(0, 10);

  const [periodFrom, setPeriodFrom] = useState('');
  const [periodTo, setPeriodTo] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [bank, setBank] = useState('');
  const [branch, setBranch] = useState('');
  const [code, setCode] = useState('');
  const [category, setCategory] = useState('Travel & Subsistence');
  const [activity, setActivity] = useState('Official Duty');

  const [telephoneCost, setTelephoneCost] = useState('');
  const [tollFeesCost, setTollFeesCost] = useState('');
  const [incidentalCost, setIncidentalCost] = useState('');
  const [subsistenceCost, setSubsistenceCost] = useState('');
  const [advanceDeduction, setAdvanceDeduction] = useState('');

  const num = (v: string) => Number.parseFloat(v) || 0;
  const totalClaimed =
    num(telephoneCost) + num(tollFeesCost) + num(incidentalCost) + num(subsistenceCost);
  const netRefund = totalClaimed - num(advanceDeduction);

  return (
    <form className="official-paper finance-form" onSubmit={(event) => event.preventDefault()}>
      <Header
        title="TRAVELLING & SUBSISTENCE EXPENSE CLAIM FORM"
        subtitle="Complete and submit this form in hard copy to FINANCE. CLAIMS MUST BE MADE WITHIN 14 DAYS OF INCURRING THE EXPENSE."
      />
      <PersonDetails />

      <div className="period-line">
        Summary of claim for the period:{' '}
        <input
          aria-label="Claim period from"
          type="date"
          value={periodFrom}
          onChange={(e) => setPeriodFrom(e.target.value)}
        />{' '}
        To{' '}
        <input
          aria-label="Claim period to"
          type="date"
          value={periodTo}
          onChange={(e) => setPeriodTo(e.target.value)}
        />{' '}
        (details overleaf) <span>S &nbsp;&nbsp;&nbsp; C</span>
      </div>

      <section className="finance-columns">
        <div>
          <h2>BANKING DETAILS: &nbsp; A/C NAME: {fullName}</h2>
          <Line label="ACCOUNT NUMBER" value={accountNumber} onChange={setAccountNumber} />
          <Line label="BANK" value={bank} onChange={setBank} />
          <Line label="BRANCH" value={branch} onChange={setBranch} />
          <Line label="CODE" value={code} onChange={setCode} />
          <Line label="Category" value={category} onChange={setCategory} />
          <Line label="Activity" value={activity} onChange={setActivity} />

          <h2>DECLARATION</h2>
          <p>
            I declare that the total expenses being claimed were incurred by me solely in the course of
            ZCHPC business. I agree to Finance rejecting my expense claim if the following attachments
            are missing: (1) Travel Authorisation (TA). (2) Field Report duly signed by me.
          </p>
          <Line label="Signed" value={fullName} readOnly />
          <Line label="Dated" value={today} readOnly />

          <h2>AUTHORISATION</h2>
          <p>This claim is correct and in order for payment.</p>
          <Line label="Name" placeholder="Authorising Manager" />
          <Line label="Signature" placeholder="Approved electronically" />
        </div>

        <table className="official-table allowance-table">
          <tbody>
            <tr>
              <th>Telephone log attached</th>
              <td>
                <input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={telephoneCost}
                  onChange={(e) => setTelephoneCost(e.target.value)}
                />
              </td>
              <td />
            </tr>
            <tr>
              <th>Toll-fees (receipts attached)</th>
              <td>
                <input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={tollFeesCost}
                  onChange={(e) => setTollFeesCost(e.target.value)}
                />
              </td>
              <td />
            </tr>
            <tr>
              <th>Other Incidental (receipts attached)</th>
              <td>
                <input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={incidentalCost}
                  onChange={(e) => setIncidentalCost(e.target.value)}
                />
              </td>
              <td />
            </tr>
            <tr>
              <th>Subsistence (attach field report &amp; TA)</th>
              <td>
                <input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={subsistenceCost}
                  onChange={(e) => setSubsistenceCost(e.target.value)}
                />
              </td>
              <td />
            </tr>
            <tr style={{ background: '#f5f5f5', fontWeight: 'bold' }}>
              <th>TOTAL EXPENSES CLAIMED</th>
              <td>${totalClaimed > 0 ? totalClaimed.toFixed(2) : '0.00'}</td>
              <td />
            </tr>
            <tr>
              <th>Less Advanced Dated:</th>
              <td>
                <input
                  type="number"
                  step="0.01"
                  placeholder="$0.00"
                  value={advanceDeduction}
                  onChange={(e) => setAdvanceDeduction(e.target.value)}
                />
              </td>
              <td />
            </tr>
            <tr style={{ background: '#e8f5e9', fontWeight: 'bold', color: '#1b5e20' }}>
              <th>RE-IMBURSEMENT / (REFUND)</th>
              <td>${netRefund !== 0 ? netRefund.toFixed(2) : '0.00'}</td>
              <td />
            </tr>
          </tbody>
        </table>
      </section>

      <FinanceUse />
    </form>
  );
}

export function TravelAuthorisationPage() {
  const [activeForm, setActiveForm] = useState<FormKind>('leave');

  return (
    <div className="official-forms-page">
      <div className="official-toolbar">
        <div>
          <p className="eyebrow flex items-center gap-1.5">
            <Sparkles className="h-3 w-3" />
            ZCHPC OFFICIAL DOCUMENTS
          </p>
          <h2>Official Forms &amp; Authorisations</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Employee credentials and calculations are automated. Fill, verify, and click Print to export
            the official A4 document.
          </p>
        </div>
        <Button type="button" variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Print Form
        </Button>
      </div>

      <div className="form-tabs" role="tablist">
        {(Object.keys(formNames) as FormKind[]).map((kind) => (
          <button
            key={kind}
            type="button"
            role="tab"
            aria-selected={activeForm === kind}
            className={activeForm === kind ? 'active' : ''}
            onClick={() => setActiveForm(kind)}
          >
            {formNames[kind]}
          </button>
        ))}
      </div>

      {activeForm === 'leave' && <LeaveForm />}
      {activeForm === 'advance' && <AdvanceForm />}
      {activeForm === 'claim' && <ClaimForm />}
    </div>
  );
}

export default TravelAuthorisationPage;
