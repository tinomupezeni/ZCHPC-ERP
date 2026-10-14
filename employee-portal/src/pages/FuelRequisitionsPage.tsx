import { useEffect, useState } from 'react';
import { FileCheck, Fuel, Loader2, Plus, Printer, Send } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/layout/PageHeader';
import { RequesterInfoCard } from '@/components/RequesterInfoCard';
import { RequisitionApprovalInbox } from '@/components/RequisitionApprovalInbox';
import { RequisitionStatusBadge } from '@/components/RequisitionStatusBadge';
import { useAuth } from '@/contexts/AuthContext';
import { fuelRequisitionService } from '@/services/fuel-requisition.service';
import { numberToWords } from '@/lib/numberToWords';
import type { FuelRequisition } from '@/types/fuel-requisition.types';

const statuses: Record<string, string> = {
  PENDING_DEPARTMENT: 'Awaiting Department Approval',
  PENDING_RECIPIENT: 'Awaiting Recipient / Driver Confirmation',
  PENDING_FINANCE: 'Awaiting Finance / General Manager',
  PENDING_DIRECTOR: 'Awaiting Director Approval',
  PENDING_ADMIN: 'Awaiting Administration Issuance',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
};

// Realistic sample of a fully approved fuel requisition for instant browser preview
const sampleApprovedFuelRequest: FuelRequisition = {
  id: 104,
  requester_name: 'Tendai Moyo',
  requester_email: 'tmoyo@zchpc.ac.zw',
  requester_employee_id: 'EC-0042',
  department: 'Technical & Infrastructure',
  programme: 'National HPC Outreach & Training',
  recipient_driver: 'Tendai Moyo',
  requester_signature: 'Tendai Moyo (Electronic)',
  vehicle_registration: 'AEF-4521',
  request_date: new Date().toISOString().slice(0, 10),
  diesel_quantity: '60.00',
  diesel_quantity_words: 'Sixty litres',
  petrol_quantity: '0.00',
  petrol_quantity_words: '',
  purpose: 'Official travel to Bulawayo Datacenter for scheduled supercomputer node maintenance and network setup.',
  destination: 'Bulawayo Site',
  destination_dates: '16 Oct 2026 - 19 Oct 2026',
  status: 'APPROVED',
  rejection_reason: '',
  rejected_by: null,
  rejected_at: null,
  rejected_at_stage: '',
  department_approved_by: 'Dr. S. Moyo (Head of Department)',
  department_approved_at: new Date(Date.now() - 3600 * 4 * 1000).toISOString(),
  recipient_approved_by: 'Tendai Moyo (Driver)',
  recipient_approved_at: new Date(Date.now() - 3600 * 3 * 1000).toISOString(),
  finance_recommendation: 'Approved within Q4 travel fuel allocation',
  finance_approved_by: 'P. Gumbo (Finance & Admin Manager)',
  finance_approved_at: new Date(Date.now() - 3600 * 2 * 1000).toISOString(),
  director_approved_by: 'Dr. N. Sithole (ZCHPC Director)',
  director_approved_at: new Date(Date.now() - 3600 * 1 * 1000).toISOString(),
  admin_approved_by: 'K. Mapfumo (Admin Officer)',
  admin_approved_at: new Date().toISOString(),
  issuance_quantity: '60.00 Litres Diesel',
  serial_numbers: 'COUPON-99412 to COUPON-99415',
  issued_by_name: 'K. Mapfumo (Stores Officer)',
  received_by_name: 'Tendai Moyo (Driver)',
  created_at: new Date(Date.now() - 3600 * 5 * 1000).toISOString(),
};

export function FuelRequisitionsPage() {
  const { employee } = useAuth();
  const [activeTab, setActiveTab] = useState('new');
  const [requests, setRequests] = useState<FuelRequisition[]>([]);
  const [inbox, setInbox] = useState<FuelRequisition[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [expandedRequestId, setExpandedRequestId] = useState<number | null>(null);
  const [printingRequestId, setPrintingRequestId] = useState<number | null>(null);
  const [showSample, setShowSample] = useState(true);

  // Form state
  const employeeName =
    employee?.full_name || `${employee?.first_name || ''} ${employee?.surname || ''}`.trim();
  const [isSelfDriver, setIsSelfDriver] = useState(true);
  const [recipientDriver, setRecipientDriver] = useState('');
  const [vehicleRegistration, setVehicleRegistration] = useState('');
  const [programme, setProgramme] = useState('');
  const [dieselQuantity, setDieselQuantity] = useState('');
  const [dieselQuantityWords, setDieselQuantityWords] = useState('');
  const [petrolQuantity, setPetrolQuantity] = useState('');
  const [petrolQuantityWords, setPetrolQuantityWords] = useState('');
  const [purpose, setPurpose] = useState('');
  const [destination, setDestination] = useState('');
  const [destinationDates, setDestinationDates] = useState('');

  const loadRequests = async () => {
    try {
      const data = await fuelRequisitionService.getRequests();
      setRequests(data);
    } catch {
      toast.error('Unable to load fuel requisitions');
    }
  };

  const loadInbox = async () => {
    try {
      setInbox(await fuelRequisitionService.getInbox());
    } catch {
      toast.error('Unable to load fuel approval inbox');
    }
  };

  useEffect(() => {
    loadRequests();
    loadInbox();
  }, []);

  useEffect(() => {
    if (printingRequestId === null) return;
    const finishPrint = () => setPrintingRequestId(null);
    window.addEventListener('afterprint', finishPrint, { once: true });
    window.print();
    return () => window.removeEventListener('afterprint', finishPrint);
  }, [printingRequestId]);

  const handleDieselChange = (val: string) => {
    setDieselQuantity(val);
    const num = Number.parseFloat(val);
    if (!Number.isNaN(num) && num > 0) {
      setDieselQuantityWords(numberToWords(num));
    } else {
      setDieselQuantityWords('');
    }
  };

  const handlePetrolChange = (val: string) => {
    setPetrolQuantity(val);
    const num = Number.parseFloat(val);
    if (!Number.isNaN(num) && num > 0) {
      setPetrolQuantityWords(numberToWords(num));
    } else {
      setPetrolQuantityWords('');
    }
  };

  const approve = async (id: number) => {
    setBusyId(id);
    try {
      await fuelRequisitionService.approve(id);
      toast.success('Fuel request approved and routed to the next stage');
      await Promise.all([loadInbox(), loadRequests()]);
    } catch {
      toast.error('Unable to approve fuel request');
    } finally {
      setBusyId(null);
    }
  };

  const reject = async (id: number, reason: string) => {
    setBusyId(id);
    try {
      await fuelRequisitionService.reject(id, reason);
      toast.success('Fuel request rejected');
      await Promise.all([loadInbox(), loadRequests()]);
    } catch {
      toast.error('Unable to reject fuel request');
    } finally {
      setBusyId(null);
    }
  };

  const resetForm = () => {
    setIsSelfDriver(true);
    setRecipientDriver('');
    setVehicleRegistration('');
    setProgramme('');
    setDieselQuantity('');
    setDieselQuantityWords('');
    setPetrolQuantity('');
    setPetrolQuantityWords('');
    setPurpose('');
    setDestination('');
    setDestinationDates('');
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const dieselNum = Number(dieselQuantity || 0);
    const petrolNum = Number(petrolQuantity || 0);

    if (dieselNum <= 0 && petrolNum <= 0) {
      toast.error('Please enter a quantity for either Diesel or Petrol');
      return;
    }

    const driverName = isSelfDriver ? employeeName : recipientDriver.trim();
    if (!driverName) {
      toast.error('Please specify the recipient or driver name');
      return;
    }

    if (!vehicleRegistration.trim()) {
      toast.error('Please provide vehicle registration number');
      return;
    }

    if (!purpose.trim()) {
      toast.error('Please describe the purpose of the request');
      return;
    }

    if (!destination.trim()) {
      toast.error('Please enter the travel destination');
      return;
    }

    setIsSubmitting(true);
    try {
      await fuelRequisitionService.createRequest({
        programme: programme.trim(),
        recipient_driver: driverName,
        requester_signature: employeeName || 'Signed electronically',
        vehicle_registration: vehicleRegistration.trim(),
        request_date: new Date().toISOString().slice(0, 10),
        diesel_quantity: dieselNum,
        diesel_quantity_words:
          dieselQuantityWords.trim() || (dieselNum > 0 ? numberToWords(dieselNum) : ''),
        petrol_quantity: petrolNum,
        petrol_quantity_words:
          petrolQuantityWords.trim() || (petrolNum > 0 ? numberToWords(petrolNum) : ''),
        purpose: purpose.trim(),
        destination: destination.trim(),
        destination_dates: destinationDates.trim(),
      });

      toast.success('Fuel requisition submitted to your department for approval');
      resetForm();
      await loadRequests();
      setActiveTab('requests');
    } catch (error) {
      const message = (error as { response?: { data?: { error?: string } } }).response?.data?.error;
      toast.error(message || 'Unable to submit fuel requisition');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Combine real requests with sample approved preview if toggled
  const displayRequests = [...requests];
  if (showSample && !requests.some((r) => r.id === sampleApprovedFuelRequest.id)) {
    displayRequests.unshift(sampleApprovedFuelRequest);
  }

  return (
    <div className={`space-y-6 ${printingRequestId !== null ? 'fuel-page printing-history' : ''}`}>
      <PageHeader
        title="Fuel Requisitions"
        description="Raise and track departmental vehicle fuel requisitions"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-3">
          <TabsTrigger value="new">New Requisition</TabsTrigger>
          <TabsTrigger value="requests">
            My Requests ({displayRequests.length})
          </TabsTrigger>
          {inbox.length > 0 && (
            <TabsTrigger value="inbox" className="relative">
              Approval Inbox
              <span className="ml-2 rounded-full bg-primary/20 px-2 py-0.5 text-xs font-semibold text-primary">
                {inbox.length}
              </span>
            </TabsTrigger>
          )}
        </TabsList>

        {/* Tab 1: New Requisition Form */}
        <TabsContent value="new" className="mt-6">
          <form onSubmit={submit} className="space-y-6 max-w-4xl">
            {/* Requester Information (Automated, matching Purchase Request) */}
            <RequesterInfoCard employee={employee} />

            {/* Vehicle & Driver Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Fuel className="h-4 w-4 text-primary" />
                  Vehicle &amp; Driver Details
                </CardTitle>
                <CardDescription>
                  Specify the vehicle and designated driver for this fuel allocation.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="vehicle_reg">Vehicle Registration Number *</Label>
                    <Input
                      id="vehicle_reg"
                      placeholder="e.g. AEF-1234"
                      value={vehicleRegistration}
                      onChange={(e) => setVehicleRegistration(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="programme">Programme / Project (Optional)</Label>
                    <Input
                      id="programme"
                      placeholder="e.g. HPC Infrastructure Deployment"
                      value={programme}
                      onChange={(e) => setProgramme(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-3 pt-2 border-t border-border/60">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="self_driver"
                      checked={isSelfDriver}
                      onChange={(e) => setIsSelfDriver(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                    />
                    <Label htmlFor="self_driver" className="cursor-pointer text-sm font-medium">
                      I am the driver / recipient ({employeeName || 'Logged-in user'})
                    </Label>
                  </div>

                  {!isSelfDriver && (
                    <div className="space-y-2 pt-1">
                      <Label htmlFor="recipient_driver">Designated Driver / Recipient Name *</Label>
                      <Input
                        id="recipient_driver"
                        placeholder="Enter full name of driver"
                        value={recipientDriver}
                        onChange={(e) => setRecipientDriver(e.target.value)}
                        required={!isSelfDriver}
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Fuel Quantity Requested */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Fuel Quantities</CardTitle>
                <CardDescription>
                  Enter the requested fuel quantity. At least one fuel type must be greater than zero.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Diesel Section */}
                  <div className="rounded-lg border p-4 space-y-3 bg-muted/20">
                    <span className="font-semibold text-sm text-foreground">Diesel</span>
                    <div className="space-y-2">
                      <Label htmlFor="diesel_qty">Quantity (Litres)</Label>
                      <Input
                        id="diesel_qty"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={dieselQuantity}
                        onChange={(e) => handleDieselChange(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="diesel_words">Quantity in Words</Label>
                      <Input
                        id="diesel_words"
                        placeholder="e.g. Fifty litres"
                        value={dieselQuantityWords}
                        onChange={(e) => setDieselQuantityWords(e.target.value)}
                      />
                    </div>
                  </div>

                  {/* Petrol Section */}
                  <div className="rounded-lg border p-4 space-y-3 bg-muted/20">
                    <span className="font-semibold text-sm text-foreground">Petrol</span>
                    <div className="space-y-2">
                      <Label htmlFor="petrol_qty">Quantity (Litres)</Label>
                      <Input
                        id="petrol_qty"
                        type="number"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        value={petrolQuantity}
                        onChange={(e) => handlePetrolChange(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="petrol_words">Quantity in Words</Label>
                      <Input
                        id="petrol_words"
                        placeholder="e.g. Twenty-five litres"
                        value={petrolQuantityWords}
                        onChange={(e) => setPetrolQuantityWords(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Trip & Purpose */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Trip &amp; Purpose</CardTitle>
                <CardDescription>State the purpose and itinerary of the journey.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="destination">Destination *</Label>
                    <Input
                      id="destination"
                      placeholder="e.g. Bulawayo Datacenter"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dest_dates">Travel Date(s)</Label>
                    <Input
                      id="dest_dates"
                      placeholder="e.g. 15 Oct 2026 - 18 Oct 2026"
                      value={destinationDates}
                      onChange={(e) => setDestinationDates(e.target.value)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="purpose">Purpose of Request *</Label>
                  <Textarea
                    id="purpose"
                    rows={3}
                    placeholder="Provide a detailed explanation for the travel and fuel allocation..."
                    value={purpose}
                    onChange={(e) => setPurpose(e.target.value)}
                    required
                  />
                </div>
              </CardContent>
            </Card>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={resetForm} disabled={isSubmitting}>
                Reset
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Submit Fuel Requisition
                  </>
                )}
              </Button>
            </div>
          </form>
        </TabsContent>

        {/* Tab 2: My Requests */}
        <TabsContent value="requests" className="mt-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2">
            <h2 className="text-base font-semibold text-foreground">Submitted Fuel Requests</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowSample((v) => !v);
                if (!showSample) setExpandedRequestId(sampleApprovedFuelRequest.id);
              }}
              className="text-xs"
            >
              <FileCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" />
              {showSample ? 'Hide Approved Sample' : 'Preview Fully Approved Sample'}
            </Button>
          </div>

          <section className="fuel-history">
            {displayRequests.length === 0 ? (
              <Card className="p-8 text-center text-muted-foreground">
                <p>No fuel requisitions submitted yet.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => setActiveTab('new')}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create Requisition
                </Button>
              </Card>
            ) : (
              displayRequests.map((request) => {
                const isSample = request.id === sampleApprovedFuelRequest.id;
                const expanded = expandedRequestId === request.id;
                const printTarget = printingRequestId === request.id;
                const dieselNum = Number(request.diesel_quantity || 0);
                const petrolNum = Number(request.petrol_quantity || 0);

                return (
                  <article
                    className={`fuel-history-item rounded-lg border bg-card p-5 mb-4 shadow-xs ${
                      isSample ? 'border-emerald-300 bg-emerald-50/20' : ''
                    } ${expanded ? ' is-expanded' : ''}${printTarget ? ' is-print-target' : ''}`}
                    key={request.id}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-border/60">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-base text-foreground">FR-{request.id}</span>
                          <RequisitionStatusBadge status={request.status} labels={statuses} />
                          {isSample && (
                            <Badge
                              variant="secondary"
                              className="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0 border-emerald-300"
                            >
                              Live Approved Sample
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          Vehicle:{' '}
                          <strong className="text-foreground">{request.vehicle_registration}</strong>{' '}
                          · Driver: {request.recipient_driver} · Date: {request.request_date}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant={expanded ? 'default' : 'outline'}
                          onClick={() => setExpandedRequestId(expanded ? null : request.id)}
                        >
                          {expanded ? 'Hide form' : 'View completed form'}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setPrintingRequestId(request.id)}
                        >
                          <Printer className="mr-2 h-4 w-4" />
                          Print
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs pt-3">
                      <div>
                        <span className="text-muted-foreground block font-medium">
                          Fuel Requested
                        </span>
                        <span className="text-foreground font-semibold">
                          {dieselNum > 0 && `${dieselNum}L Diesel `}
                          {petrolNum > 0 && `${petrolNum}L Petrol`}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block font-medium">Destination</span>
                        <span className="text-foreground">
                          {request.destination}{' '}
                          {request.destination_dates ? `(${request.destination_dates})` : ''}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block font-medium">Purpose</span>
                        <span className="text-foreground truncate block">{request.purpose}</span>
                      </div>
                    </div>

                    {request.status === 'REJECTED' && (
                      <div className="mt-3 rounded-md bg-rose-50 border border-rose-200 p-3 text-xs text-rose-800">
                        <strong>
                          Rejected at {statuses[request.rejected_at_stage] ?? request.rejected_at_stage}:
                        </strong>{' '}
                        {request.rejection_reason}
                        {request.rejected_by && (
                          <span className="block mt-1 text-rose-600">By {request.rejected_by}</span>
                        )}
                      </div>
                    )}

                    {/* Official Completed Record View (Rendered when expanded or printing) */}
                    {expanded && (
                      <div className="fuel-completed-record fuel-paper mt-5 pt-4 border-t">
                        <header className="fuel-header">
                          <h1>ZIMBABWE CENTRE FOR HIGH PERFORMANCE COMPUTING</h1>
                          <img src="/logo.png" alt="ZCHPC" />
                          <h2>FUEL REQUISITION FORM</h2>
                        </header>
                        <section className="paper-identity">
                          <label className="paper-field">
                            <span>Programme</span>
                            <input value={request.programme || ''} readOnly />
                          </label>
                          <label className="paper-field">
                            <span>Department</span>
                            <input value={request.department} readOnly />
                          </label>
                          <label className="paper-field">
                            <span>Recipient / Driver Name</span>
                            <input value={request.recipient_driver} readOnly />
                          </label>
                          <label className="paper-field">
                            <span>Signature</span>
                            <input value={request.requester_signature} readOnly />
                          </label>
                          <label className="paper-field">
                            <span>Date</span>
                            <input type="date" value={request.request_date} disabled />
                          </label>
                          <label className="paper-field">
                            <span>Vehicle Reg No.</span>
                            <input value={request.vehicle_registration} readOnly />
                          </label>
                        </section>
                        <table className="fuel-table">
                          <thead>
                            <tr>
                              <th>Description</th>
                              <th>
                                Quantity requested
                                <br />
                                (Figures)
                              </th>
                              <th>Quantity requested (Words)</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <th>Diesel</th>
                              <td>
                                <input value={request.diesel_quantity} readOnly />
                              </td>
                              <td>
                                <input value={request.diesel_quantity_words} readOnly />
                              </td>
                            </tr>
                            <tr>
                              <th>Petrol</th>
                              <td>
                                <input value={request.petrol_quantity} readOnly />
                              </td>
                              <td>
                                <input value={request.petrol_quantity_words} readOnly />
                              </td>
                            </tr>
                          </tbody>
                        </table>
                        <section className="paper-block">
                          <h3>Purpose of request</h3>
                          <textarea rows={4} value={request.purpose} readOnly />
                        </section>
                        <section className="paper-row">
                          <label className="paper-field">
                            <span>Destination</span>
                            <input value={request.destination} readOnly />
                          </label>
                          <label className="paper-field">
                            <span>Date(s)</span>
                            <input value={request.destination_dates} readOnly />
                          </label>
                        </section>
                        <section className="approval-block">
                          <h3>Recommended by Finance and Administration Manager</h3>
                          <div className="signature-row">
                            <span>Name: {request.finance_approved_by || ''}</span>
                            <span>
                              {request.finance_recommendation ||
                                (request.finance_approved_by
                                  ? 'Approved electronically'
                                  : 'Signature')}
                            </span>
                            <span>
                              Date:{' '}
                              {request.finance_approved_at
                                ? new Date(request.finance_approved_at).toLocaleDateString('en-GB')
                                : ''}
                            </span>
                          </div>
                          <h3>Approved by ZCHPC Director</h3>
                          <div className="signature-row">
                            <span>Name: {request.director_approved_by || ''}</span>
                            <span>
                              {request.director_approved_by
                                ? 'Approved electronically'
                                : 'Signature'}
                            </span>
                            <span>
                              Date:{' '}
                              {request.director_approved_at
                                ? new Date(request.director_approved_at).toLocaleDateString('en-GB')
                                : ''}
                            </span>
                          </div>
                        </section>
                        <section className="paper-block issuance">
                          <h3>Details of issuance:</h3>
                          <div className="dotted-line">
                            Quantity Issued (Figures and Words)
                            {request.issuance_quantity ? `: ${request.issuance_quantity}` : ''}
                          </div>
                          <div className="dotted-line">
                            Serial Number(s)
                            {request.serial_numbers ? `: ${request.serial_numbers}` : ''}
                          </div>
                          <div className="signature-row">
                            <span>
                              Issued by
                              {request.issued_by_name ? `: ${request.issued_by_name}` : ''}
                            </span>
                            <span>Signature</span>
                            <span>Date</span>
                          </div>
                          <div className="signature-row">
                            <span>
                              Received by
                              {request.received_by_name ? `: ${request.received_by_name}` : ''}
                            </span>
                            <span>Signature</span>
                            <span>Date</span>
                          </div>
                        </section>
                      </div>
                    )}
                  </article>
                );
              })
            )}
          </section>
        </TabsContent>

        {/* Tab 3: Approval Inbox */}
        {inbox.length > 0 && (
          <TabsContent value="inbox" className="mt-6">
            <RequisitionApprovalInbox
              kind="fuel"
              requests={inbox}
              busyId={busyId}
              onApprove={approve}
              onReject={reject}
            />
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}

export default FuelRequisitionsPage;
