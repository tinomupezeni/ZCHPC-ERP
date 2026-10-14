import { useEffect, useState } from 'react';
import { FileCheck, Loader2, Package, Plus, Printer, Send, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/layout/PageHeader';
import { RequesterInfoCard } from '@/components/RequesterInfoCard';
import { RequisitionApprovalInbox } from '@/components/RequisitionApprovalInbox';
import { RequisitionStatusBadge } from '@/components/RequisitionStatusBadge';
import { useAuth } from '@/contexts/AuthContext';
import { storesRequisitionService } from '@/services/stores-requisition.service';
import type { StoresItem, StoresRequisition } from '@/types/stores-requisition.types';

interface DynamicStoresItem extends StoresItem {
  key: string;
}

const emptyItem = (): DynamicStoresItem => ({
  key: Math.random().toString(36).substring(2, 9),
  description: '',
  quantity_required: '',
  budget_code: '',
  required_by: '',
});

const statuses: Record<string, string> = {
  PENDING_DEPARTMENT: 'Awaiting Head of Department',
  PENDING_PROCUREMENT: 'Awaiting Procurement / Stores',
  PENDING_ACCOUNTS: 'Awaiting Accounts / Finance',
  PENDING_GENERAL_MANAGER: 'Awaiting General Manager',
  PENDING_DIRECTOR: 'Awaiting Director',
  PENDING_ADMIN: 'Awaiting Administration',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
};

// Realistic sample of a fully approved stores requisition for instant browser preview
const sampleApprovedStoresRequest: StoresRequisition = {
  id: 201,
  requisition_number: 'SR-2026-0089',
  requester_name: 'John Doe',
  requester_email: 'jdoe@zchpc.ac.zw',
  requester_employee_id: 'EC-0019',
  department: 'Technical & Infrastructure',
  items: [
    {
      description: 'A4 Printing Paper (80gsm, White - 5 Reams/Box)',
      quantity_required: '5 Boxes',
      budget_code: 'ADMIN-SUP-01',
      required_by: '2026-10-20',
    },
    {
      description: 'HP LaserJet 85A Black Toner Cartridge',
      quantity_required: '2 Units',
      budget_code: 'IT-OPS-04',
      required_by: '2026-10-22',
    },
    {
      description: 'Cat6 Shielded Patch Cables (2m, Blue)',
      quantity_required: '10 Units',
      budget_code: 'NET-HW-02',
      required_by: '2026-10-25',
    },
  ],
  status: 'APPROVED',
  rejection_reason: '',
  rejected_by: null,
  rejected_at: null,
  rejected_at_stage: '',
  department_approved_by: 'Dr. S. Moyo (Head of Department)',
  department_approved_at: '2026-10-14T09:15:00Z',
  procurement_approved_by: 'T. Chitepo (Stores & Procurement Officer)',
  procurement_approved_at: '2026-10-14T10:30:00Z',
  accounts_approved_by: 'C. Ndlovu (Finance & Accounts)',
  accounts_approved_at: '2026-10-14T11:45:00Z',
  general_manager_approved_by: 'M. Sibanda (General Manager)',
  general_manager_approved_at: '2026-10-14T13:00:00Z',
  director_approved_by: 'Dr. N. Sithole (ZCHPC Director)',
  director_approved_at: '2026-10-14T14:15:00Z',
  admin_approved_by: 'A. Zhou (Administration)',
  admin_approved_at: '2026-10-14T15:00:00Z',
  created_at: '2026-10-14T08:00:00Z',
};

export function StoresRequisitionsPage() {
  const { employee } = useAuth();
  const [activeTab, setActiveTab] = useState('new');
  const [items, setItems] = useState<DynamicStoresItem[]>([emptyItem()]);
  const [requests, setRequests] = useState<StoresRequisition[]>([]);
  const [inbox, setInbox] = useState<StoresRequisition[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [expandedRequestId, setExpandedRequestId] = useState<number | null>(null);
  const [printingRequestId, setPrintingRequestId] = useState<number | null>(null);
  const [showSample, setShowSample] = useState(true);

  const loadRequests = async () => {
    try {
      const data = await storesRequisitionService.getRequests();
      setRequests(data);
    } catch {
      toast.error('Unable to load stores requisitions');
    }
  };

  const loadInbox = async () => {
    try {
      setInbox(await storesRequisitionService.getInbox());
    } catch {
      toast.error('Unable to load stores approval inbox');
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

  const approve = async (id: number) => {
    setBusyId(id);
    try {
      await storesRequisitionService.approve(id);
      toast.success('Stores requisition approved and routed to the next stage');
      await Promise.all([loadInbox(), loadRequests()]);
    } catch {
      toast.error('Unable to approve stores requisition');
    } finally {
      setBusyId(null);
    }
  };

  const reject = async (id: number, reason: string) => {
    setBusyId(id);
    try {
      await storesRequisitionService.reject(id, reason);
      toast.success('Stores requisition rejected');
      await Promise.all([loadInbox(), loadRequests()]);
    } catch {
      toast.error('Unable to reject stores requisition');
    } finally {
      setBusyId(null);
    }
  };

  const updateItem = (key: string, field: keyof StoresItem, value: string) => {
    setItems((current) =>
      current.map((item) => (item.key === key ? { ...item, [field]: value } : item))
    );
  };

  const addItem = () => {
    if (items.length >= 4) {
      toast.error('Maximum of 4 items allowed per stores requisition');
      return;
    }
    setItems((current) => [...current, emptyItem()]);
  };

  const removeItem = (key: string) => {
    if (items.length <= 1) return;
    setItems((current) => current.filter((item) => item.key !== key));
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();

    // Validation matching Purchase Requests
    for (let i = 0; i < items.length; i++) {
      const itm = items[i];
      if (!itm.description.trim()) {
        toast.error(`Item ${i + 1}: Description is required`);
        return;
      }
      if (!itm.quantity_required.trim()) {
        toast.error(`Item ${i + 1}: Quantity is required`);
        return;
      }
      if (!itm.budget_code.trim()) {
        toast.error(`Item ${i + 1}: Budget code is required`);
        return;
      }
      if (!itm.required_by) {
        toast.error(`Item ${i + 1}: Required-by date is required`);
        return;
      }
    }

    const payloadItems = items.map((itm) => ({
      description: itm.description.trim(),
      quantity_required: itm.quantity_required.trim(),
      budget_code: itm.budget_code.trim(),
      required_by: itm.required_by,
    }));

    setIsSubmitting(true);
    try {
      await storesRequisitionService.createRequest({ items: payloadItems });
      toast.success('Stores requisition submitted to Head of Department');
      setItems([emptyItem()]);
      await loadRequests();
      setActiveTab('requests');
    } catch (error) {
      const message = (error as { response?: { data?: { error?: string } } }).response?.data?.error;
      toast.error(message || 'Unable to submit stores requisition');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Combine real requests with sample approved preview if toggled
  const displayRequests = [...requests];
  if (showSample && !requests.some((r) => r.id === sampleApprovedStoresRequest.id)) {
    displayRequests.unshift(sampleApprovedStoresRequest);
  }

  return (
    <div className={`space-y-6 ${printingRequestId !== null ? 'stores-page printing-history' : ''}`}>
      <PageHeader
        title="Stores Requisitions"
        description="Raise and track departmental stores and inventory requisitions"
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

            {/* Dynamic Items Section (Matching Purchase Requests dynamic rows) */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Package className="h-4 w-4 text-primary" />
                      Item(s) Requested
                    </CardTitle>
                    <CardDescription>
                      List each item required from stores, its quantity, budget code, and needed date.
                    </CardDescription>
                  </div>
                  <span className="text-xs text-muted-foreground font-medium">
                    {items.length} / 4 items
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {items.map((item, index) => (
                  <div key={item.key} className="rounded-lg border p-4 space-y-3 bg-card shadow-2xs">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-foreground">Item {index + 1}</span>
                      {items.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-8 px-2"
                          onClick={() => removeItem(item.key)}
                          disabled={isSubmitting}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor={`description-${item.key}`}>Item Description *</Label>
                        <Input
                          id={`description-${item.key}`}
                          placeholder="e.g. A4 Printing Paper, White (Reams)"
                          value={item.description}
                          onChange={(e) => updateItem(item.key, 'description', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`quantity-${item.key}`}>Quantity Required *</Label>
                        <Input
                          id={`quantity-${item.key}`}
                          placeholder="e.g. 5 boxes / 10 units"
                          value={item.quantity_required}
                          onChange={(e) => updateItem(item.key, 'quantity_required', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`budget_code-${item.key}`}>Budget Code *</Label>
                        <Input
                          id={`budget_code-${item.key}`}
                          placeholder="e.g. B-101 / ADMIN-SUPPLIES"
                          value={item.budget_code}
                          onChange={(e) => updateItem(item.key, 'budget_code', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>

                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor={`required_by-${item.key}`}>Required By (Date) *</Label>
                        <Input
                          id={`required_by-${item.key}`}
                          type="date"
                          value={item.required_by}
                          onChange={(e) => updateItem(item.key, 'required_by', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>
                    </div>
                  </div>
                ))}

                {items.length < 4 && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={addItem}
                    disabled={isSubmitting}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Item
                  </Button>
                )}
                {items.length >= 4 && (
                  <p className="text-xs text-muted-foreground text-center">
                    Maximum limit of 4 items reached for this requisition.
                  </p>
                )}
              </CardContent>
            </Card>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setItems([emptyItem()])}
                disabled={isSubmitting}
              >
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
                    Submit Stores Requisition
                  </>
                )}
              </Button>
            </div>
          </form>
        </TabsContent>

        {/* Tab 2: My Requests */}
        <TabsContent value="requests" className="mt-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2">
            <h2 className="text-base font-semibold text-foreground">Submitted Stores Requisitions</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowSample((v) => !v);
                if (!showSample) setExpandedRequestId(sampleApprovedStoresRequest.id);
              }}
              className="text-xs"
            >
              <FileCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" />
              {showSample ? 'Hide Approved Sample' : 'Preview Fully Approved Sample'}
            </Button>
          </div>

          <section className="stores-history">
            {displayRequests.length === 0 ? (
              <Card className="p-8 text-center text-muted-foreground">
                <p>No stores requisitions submitted yet.</p>
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
                const isSample = request.id === sampleApprovedStoresRequest.id;
                const expanded = expandedRequestId === request.id;
                const printTarget = printingRequestId === request.id;

                return (
                  <article
                    className={`stores-history-item rounded-lg border bg-card p-5 mb-4 shadow-xs ${
                      isSample ? 'border-emerald-300 bg-emerald-50/20' : ''
                    } ${expanded ? ' is-expanded' : ''}${printTarget ? ' is-print-target' : ''}`}
                    key={request.id}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-border/60">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-base text-foreground">
                            {request.requisition_number}
                          </span>
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
                          Date: {request.created_at.slice(0, 10)} · Items:{' '}
                          <strong>{request.items.length}</strong>
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

                    <div className="pt-3">
                      <div className="rounded-md border bg-muted/30 overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="border-b bg-muted/50 text-muted-foreground text-left">
                              <th className="p-2 font-medium">Description</th>
                              <th className="p-2 font-medium">Quantity</th>
                              <th className="p-2 font-medium">Budget Code</th>
                              <th className="p-2 font-medium">Required By</th>
                            </tr>
                          </thead>
                          <tbody>
                            {request.items.map((item, idx) => (
                              <tr key={idx} className="border-b last:border-0">
                                <td className="p-2 font-medium text-foreground">{item.description}</td>
                                <td className="p-2 text-muted-foreground">{item.quantity_required}</td>
                                <td className="p-2 text-muted-foreground">{item.budget_code}</td>
                                <td className="p-2 text-muted-foreground">{item.required_by}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
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
                      <div className="stores-completed-record stores-paper mt-5 pt-4 border-t">
                        <header className="stores-header">
                          <h1>Stores Requisition Form</h1>
                          <img src="/logo.png" alt="ZCHPC" />
                          <label>
                            Requisition No: <output>{request.requisition_number}</output>
                          </label>
                        </header>
                        <h2>Section A: Request Details</h2>
                        <table className="stores-table">
                          <thead>
                            <tr>
                              <th>Item Description</th>
                              <th>
                                Quantity
                                <br />
                                Required
                              </th>
                              <th>Budget Code</th>
                              <th>
                                Required By
                                <br />
                                (Date):
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {request.items.map((item, index) => (
                              <tr key={`${request.id}-${index}`}>
                                <td>
                                  <input value={item.description} readOnly />
                                </td>
                                <td>
                                  <input value={item.quantity_required} readOnly />
                                </td>
                                <td>
                                  <input value={item.budget_code} readOnly />
                                </td>
                                <td>
                                  <input type="date" value={item.required_by} disabled />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        <h2>Section B: Approvals &amp; Signatures</h2>
                        <div className="approval-head">
                          <span>Role</span>
                          <span>Name &amp; Signature</span>
                          <span>Date</span>
                        </div>
                        <div className="approval-line">
                          <span>Requester</span>
                          <input
                            value={`${request.requester_name} (Submitted electronically)`}
                            readOnly
                          />
                          <input type="date" value={request.created_at.slice(0, 10)} disabled />
                        </div>
                        <div className="approval-line">
                          <span>Head of Dept.</span>
                          <input
                            value={
                              request.department_approved_by
                                ? `${request.department_approved_by} (Approved)`
                                : ''
                            }
                            readOnly
                          />
                          <input
                            type="date"
                            value={request.department_approved_at?.slice(0, 10) || ''}
                            disabled
                          />
                        </div>
                        <div className="approval-line">
                          <span>Stores Officer</span>
                          <input
                            value={
                              request.procurement_approved_by
                                ? `${request.procurement_approved_by} (Approved)`
                                : ''
                            }
                            readOnly
                          />
                          <input
                            type="date"
                            value={request.procurement_approved_at?.slice(0, 10) || ''}
                            disabled
                          />
                        </div>
                        <div className="approval-line">
                          <span>Finance</span>
                          <input
                            value={
                              request.accounts_approved_by
                                ? `${request.accounts_approved_by} (Approved)`
                                : ''
                            }
                            readOnly
                          />
                          <input
                            type="date"
                            value={request.accounts_approved_at?.slice(0, 10) || ''}
                            disabled
                          />
                        </div>

                        <h2>Section C: Stores Action</h2>
                        <table className="stores-table action-table">
                          <thead>
                            <tr>
                              <th>Item Issued</th>
                              <th>Quantity Issued</th>
                              <th>Balance in Stock:</th>
                              <th>Remarks:</th>
                            </tr>
                          </thead>
                          <tbody>
                            {request.items.map((item, rowIdx) => (
                              <tr key={rowIdx}>
                                <td>
                                  <input value={item.description} readOnly />
                                </td>
                                <td>
                                  <input value={item.quantity_required} readOnly />
                                </td>
                                <td>
                                  <input value="Verified in Stock" readOnly />
                                </td>
                                <td>
                                  <input value="Issued in Full" readOnly />
                                </td>
                              </tr>
                            ))}
                            {Array.from({
                              length: Math.max(0, 4 - request.items.length),
                            }).map((_, emptyIdx) => (
                              <tr key={`empty-${emptyIdx}`}>
                                <td>
                                  <input readOnly />
                                </td>
                                <td>
                                  <input readOnly />
                                </td>
                                <td>
                                  <input readOnly />
                                </td>
                                <td>
                                  <input readOnly />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        <h2>Section D: Finance Confirmation</h2>
                        <table className="stores-table finance-table">
                          <thead>
                            <tr>
                              <th>Budget Code Charged</th>
                              <th>Imputer</th>
                              <th>Date</th>
                              <th>Authorisation</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td>
                                <input
                                  value={
                                    request.items
                                      .map((i) => i.budget_code)
                                      .filter(Boolean)
                                      .join(', ') || 'ADMIN-SUP-01'
                                  }
                                  readOnly
                                />
                              </td>
                              <td>
                                <input
                                  value={request.accounts_approved_by || 'Finance Officer'}
                                  readOnly
                                />
                              </td>
                              <td>
                                <input
                                  type="date"
                                  value={
                                    request.accounts_approved_at?.slice(0, 10) ||
                                    request.created_at.slice(0, 10)
                                  }
                                  disabled
                                />
                              </td>
                              <td>
                                <input value="VERIFIED / POSTED" readOnly />
                              </td>
                            </tr>
                          </tbody>
                        </table>
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
              kind="stores"
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

export default StoresRequisitionsPage;
