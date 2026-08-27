import { useState } from 'react';
import { Printer } from 'lucide-react';
import { Button } from '@/components/ui/button';

type TravelRow = { date: string; destination: string };

const initialRows: TravelRow[] = Array.from({ length: 5 }, () => ({ date: '', destination: '' }));

export function TravelAuthorisationPage() {
  const [officers, setOfficers] = useState(['', '', '']);
  const [programme, setProgramme] = useState('');
  const [subProgramme, setSubProgramme] = useState('');
  const [activity, setActivity] = useState('');
  const [budgetCode, setBudgetCode] = useState('');
  const [travelRows, setTravelRows] = useState(initialRows);
  const [nights, setNights] = useState('');
  const [reasons, setReasons] = useState('');
  const [transport, setTransport] = useState('');
  const [expenditure, setExpenditure] = useState('');
  const [budgetSign, setBudgetSign] = useState('');
  const [budgetDate, setBudgetDate] = useState('');
  const [headSign, setHeadSign] = useState('');
  const [headDate, setHeadDate] = useState('');
  const [directorSign, setDirectorSign] = useState('');
  const [directorDate, setDirectorDate] = useState('');

  const updateOfficer = (index: number, value: string) => setOfficers((current) => current.map((item, itemIndex) => itemIndex === index ? value : item));
  const updateTravel = (index: number, field: keyof TravelRow, value: string) => setTravelRows((current) => current.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: value } : row));

  return <div className="ta-page">
    <div className="ta-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="ta-paper" onSubmit={(event) => event.preventDefault()}>
      <header className="ta-header"><div className="ta-crest-space" /><div className="ta-title"><h1>ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</h1><h2>TRAVEL AUTHORISATION (TA) FORM</h2></div><img src="/logo.png" alt="ZCHPC" /></header>
      <table className="ta-table ta-top-table"><tbody><tr><th>Name of Travelling Officers</th><td>{officers.map((officer, index) => <label key={index}>({index + 1})<input value={officer} onChange={(event) => updateOfficer(index, event.target.value)} /></label>)}</td></tr><tr><th>Programme</th><td><input value={programme} onChange={(event) => setProgramme(event.target.value)} /></td><th>Sub-programme</th><td><input value={subProgramme} onChange={(event) => setSubProgramme(event.target.value)} /></td></tr><tr><th>Activity as in Approved<br />Budget</th><td colSpan={3}><input value={activity} onChange={(event) => setActivity(event.target.value)} /></td></tr><tr><th>Budget Code:</th><td colSpan={3}><input value={budgetCode} onChange={(event) => setBudgetCode(event.target.value)} /></td></tr></tbody></table>
      <table className="ta-table ta-travel-table"><thead><tr><th>Dates of Travel</th><th>Destination</th></tr></thead><tbody>{travelRows.map((row, index) => <tr key={index}><td><input type="date" aria-label={`Travel date ${index + 1}`} value={row.date} onChange={(event) => updateTravel(index, 'date', event.target.value)} /></td><td><input aria-label={`Destination ${index + 1}`} value={row.destination} onChange={(event) => updateTravel(index, 'destination', event.target.value)} /></td></tr>)}<tr><th>Number of nights</th><td><input value={nights} onChange={(event) => setNights(event.target.value)} /></td></tr><tr><th>Outline reasons for visit/What will be<br />achieved/Attach TORs</th><td><textarea rows={3} value={reasons} onChange={(event) => setReasons(event.target.value)} /></td></tr><tr><th>Mode of Transport Required</th><td><input value={transport} onChange={(event) => setTransport(event.target.value)} /></td></tr><tr><th>Estimated Expenditure,<br />accommodation/expenses etc</th><td><textarea rows={4} value={expenditure} onChange={(event) => setExpenditure(event.target.value)} /></td></tr></tbody></table>
      <table className="ta-table ta-approval-table"><tbody><tr><th>Budget Confirmation</th><td>Sign:<input value={budgetSign} onChange={(event) => setBudgetSign(event.target.value)} /></td><td>Date:<input type="date" value={budgetDate} onChange={(event) => setBudgetDate(event.target.value)} /></td></tr><tr><th>Recommended by Head of Department</th><td>Sign:<input value={headSign} onChange={(event) => setHeadSign(event.target.value)} /></td><td>Date:<input type="date" value={headDate} onChange={(event) => setHeadDate(event.target.value)} /></td></tr><tr><th>Authorized by Director:</th><td>Sign:<input value={directorSign} onChange={(event) => setDirectorSign(event.target.value)} /></td><td>Date:<input type="date" value={directorDate} onChange={(event) => setDirectorDate(event.target.value)} /></td></tr></tbody></table>
    </form>
  </div>;
}

export default TravelAuthorisationPage;
