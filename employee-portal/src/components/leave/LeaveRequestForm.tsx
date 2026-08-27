import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Printer } from 'lucide-react';
import { format } from 'date-fns';
import { useAuth } from '@/contexts/AuthContext';
import type { LeaveType, LeaveBalance, CreateLeaveRequestData } from '@/types/leave.types';

interface LeaveRequestFormProps {
  leaveTypes: LeaveType[];
  balances: LeaveBalance[];
  onSubmit: (data: CreateLeaveRequestData) => Promise<void>;
  isSubmitting: boolean;
}

export function LeaveRequestForm({
  leaveTypes,
  onSubmit,
  isSubmitting,
}: LeaveRequestFormProps) {
  const [leaveType, setLeaveType] = useState<string>('');
  const [period, setPeriod] = useState<string>('');
  const [daysApplied, setDaysApplied] = useState<string>('');
  const [address, setAddress] = useState('');
  const [telephone, setTelephone] = useState('');
  const [email, setEmail] = useState('');
  const [signature, setSignature] = useState('');
  const [applicationDate, setApplicationDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [employmentCode, setEmploymentCode] = useState('EMP0001');
  const [fullNames, setFullNames] = useState('');
  const [designation, setDesignation] = useState('');
  const [department, setDepartment] = useState('IT');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { employee } = useAuth();

  useEffect(() => {
    if (employee) {
      setEmploymentCode(employee.employee_id || 'EMP0001');
      setFullNames(employee.full_name || `${employee.first_name} ${employee.surname}`.trim());
      setDesignation(employee.position_title || '');
      setDepartment(employee.department_name || 'IT');
    }
  }, [employee]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!leaveType) newErrors.leaveType = 'Select a leave type';
    if (!period) newErrors.period = 'Enter the leave period';
    if (!daysApplied) newErrors.daysApplied = 'Enter the number of days';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    await onSubmit({
      leave_type_id: parseInt(leaveType),
      start_date: period.split(' to ')[0] || applicationDate,
      end_date: period.split(' to ')[1] || applicationDate,
      reason: `Employment Code Number: ${employmentCode}; Full Names: ${fullNames}; Designation: ${designation}; Department: ${department}; Address: ${address}; Telephone: ${telephone}; Email: ${email}; Signature: ${signature}`,
    });

    // Reset form on success
    setLeaveType('');
    setPeriod(''); setDaysApplied(''); setAddress(''); setTelephone(''); setEmail(''); setSignature('');
    setErrors({});
  };

  return <div className="leave-paper-wrap">
    <div className="leave-actions"><Button type="button" variant="outline" onClick={() => window.print()}><Printer className="mr-2 h-4 w-4" />Print form</Button></div>
    <form className="leave-paper" onSubmit={handleSubmit}>
      <header className="leave-header"><img src="/logo.png" alt="ZCHPC" /><h1>ZCHPC</h1><h2>ZIMBABWE CENTRE FOR HIGH PERFORMANCE<br />COMPUTING</h2><h3>APPLICATION FOR LEAVE <span>(HR 02)</span></h3><strong>Confidential</strong></header>
      <div className="leave-dash" />
      <table className="leave-identity"><tbody><tr><th>EMPLOYMENT CODE NUMBER</th><td><input value={employmentCode} onChange={(event) => setEmploymentCode(event.target.value)} /></td></tr><tr><th>FULL NAMES</th><td><input value={fullNames} onChange={(event) => setFullNames(event.target.value)} /></td></tr><tr><th>DESIGNATION</th><td><input value={designation} onChange={(event) => setDesignation(event.target.value)} /></td></tr><tr><th>DEPARTMENT</th><td><input value={department} onChange={(event) => setDepartment(event.target.value)} /></td></tr></tbody></table>
      <h4>LEAVE DETAILS</h4><table className="leave-types"><thead><tr><th>TYPE OF LEAVE</th><th>PERIOD</th><th>NUMBER OF DAYS APPLIED</th></tr></thead><tbody>{['VACATION', 'SICK', 'MATERNITY', 'STUDY', 'SPECIAL/COMPASSIONATE', 'ANNUAL'].map((name) => <tr key={name}><td><label><input type="radio" name="leaveType" checked={leaveType === String(leaveTypes.find((type) => type.name.toUpperCase() === name)?.id || '')} onChange={() => { const type = leaveTypes.find((item) => item.name.toUpperCase() === name); if (type) setLeaveType(String(type.id)); }} />{name}</label></td><td><input value={leaveType === String(leaveTypes.find((type) => type.name.toUpperCase() === name)?.id || '') ? period : ''} onChange={(event) => setPeriod(event.target.value)} /></td><td><input value={leaveType === String(leaveTypes.find((type) => type.name.toUpperCase() === name)?.id || '') ? daysApplied : ''} onChange={(event) => setDaysApplied(event.target.value)} /></td></tr>)}</tbody></table>
      <h4>Contact details while on leave:</h4><label className="leave-line">Address<input value={address} onChange={(event) => setAddress(event.target.value)} /></label><div className="leave-two-lines"><label>Telephone<input value={telephone} onChange={(event) => setTelephone(event.target.value)} /></label><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label></div><div className="leave-two-lines"><label>Signature of Applicant<input value={signature} onChange={(event) => setSignature(event.target.value)} /></label><label>Date<input type="date" value={applicationDate} onChange={(event) => setApplicationDate(event.target.value)} /></label></div>
      <table className="leave-approval"><thead><tr><th>Recommended/<br />not recommended</th><th>Recommended/<br />not recommended</th><th>Approved/Not Approved</th></tr></thead><tbody><tr><td>DEPARTMENT HEAD<br /><span>........................<br />signature</span></td><td>HR DEPARTMENT<br /><span>Number of Days accumulated<br /><br />.................... signature</span></td><td>DIRECTOR/GENERAL MANAGER<br /><span>............................ Signature ................. Date</span></td></tr></tbody></table>
      <div className="leave-submit"><Button type="submit" disabled={isSubmitting || !leaveType}>{isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Submit Leave Application</Button></div>
    </form>
  </div>;
}

export default LeaveRequestForm;
