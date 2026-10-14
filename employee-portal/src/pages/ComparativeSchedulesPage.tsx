import { useEffect, useState } from 'react';
import { FileCheck, Loader2, Plus, Printer, Scale, Send, Trash2 } from 'lucide-react';
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
import { RequisitionStatusBadge } from '@/components/RequisitionStatusBadge';
import { useAuth } from '@/contexts/AuthContext';
import { comparativeScheduleService } from '@/services/comparative-schedule.service';
import type { ComparativeItem, ComparativeSchedule } from '@/types/comparative-schedule.types';

interface DynamicComparativeItem extends ComparativeItem {
  key: string;
}

const emptyItem = (): DynamicComparativeItem => ({
  key: Math.random().toString(36).substring(2, 9),
  description: '',
  quantity: '1',
  quotation_one_unit: '',
  quotation_one_total: '',
  quotation_two_unit: '',
  quotation_two_total: '',
});

const checks = ['Requirement Specifications', 'Valid Tax Clearance', 'PRAZ Registration'];

const statuses: Record<string, string> = {
  PENDING_DIRECTOR: 'Awaiting Director Approval',
  PENDING_PROCUREMENT: 'Awaiting Procurement Review',
  PENDING_ACCOUNTS: 'Awaiting Accounts Review',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
};

// Sample approved comparative schedule for instant browser preview
const sampleApprovedSchedule: ComparativeSchedule = {
  id: 501,
  schedule_number: 'CS-2026-0034',
  compliance: {
    'Requirement Specifications_one': 'Compliant',
    'Requirement Specifications_two': 'Compliant',
    'Valid Tax Clearance_one': 'Compliant',
    'Valid Tax Clearance_two': 'Compliant',
    'PRAZ Registration_one': 'Compliant',
    'PRAZ Registration_two': 'Compliant',
  },
  items: [
    {
      description: 'Server Rack Mount Rails (2U)',
      quantity: '4',
      quotation_one_unit: '120.00',
      quotation_one_total: '480.00',
      quotation_two_unit: '145.00',
      quotation_two_total: '580.00',
    },
    {
      description: 'CAT6A 24-Port Patch Panel',
      quantity: '2',
      quotation_one_unit: '85.00',
      quotation_one_total: '170.00',
      quotation_two_unit: '95.00',
      quotation_two_total: '190.00',
    },
  ],
  recommendation:
    'Recommend award to Supplier 1 based on lowest compliant price and verified PRAZ registration.',
  status: 'APPROVED',
  rejection_reason: '',
  procurement_submitted_at: new Date(Date.now() - 3600 * 24 * 1000).toISOString(),
};

export function ComparativeSchedulesPage() {
  const { employee } = useAuth();
  const [activeTab, setActiveTab] = useState('new');
  const [items, setItems] = useState<DynamicComparativeItem[]>([emptyItem()]);
  const [supplierOneName, setSupplierOneName] = useState('Supplier 1');
  const [supplierTwoName, setSupplierTwoName] = useState('Supplier 2');
  const [compliance, setCompliance] = useState<Record<string, string>>({
    'Requirement Specifications_one': 'Compliant',
    'Requirement Specifications_two': 'Compliant',
    'Valid Tax Clearance_one': 'Compliant',
    'Valid Tax Clearance_two': 'Compliant',
    'PRAZ Registration_one': 'Compliant',
    'PRAZ Registration_two': 'Compliant',
  });
  const [recommendation, setRecommendation] = useState('');
  const [schedules, setSchedules] = useState<ComparativeSchedule[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedScheduleId, setExpandedScheduleId] = useState<number | null>(null);
  const [printingScheduleId, setPrintingScheduleId] = useState<number | null>(null);
  const [showSample, setShowSample] = useState(true);

  const load = async () => {
    try {
      setSchedules(await comparativeScheduleService.getSchedules());
    } catch {
      toast.error('Unable to load comparative schedules');
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (printingScheduleId === null) return;
    const finishPrint = () => setPrintingScheduleId(null);
    window.addEventListener('afterprint', finishPrint, { once: true });
    window.print();
    return () => window.removeEventListener('afterprint', finishPrint);
  }, [printingScheduleId]);

  const updateItem = (key: string, field: keyof ComparativeItem, value: string) => {
    setItems((current) =>
      current.map((item) => {
        if (item.key !== key) return item;
        const updated = { ...item, [field]: value };

        // Auto-calculate line totals if qty and unit price are entered
        const qty = Number.parseFloat(field === 'quantity' ? value : item.quantity) || 0;
        if (field === 'quotation_one_unit' || field === 'quantity') {
          const unit1 =
            Number.parseFloat(field === 'quotation_one_unit' ? value : item.quotation_one_unit) || 0;
          if (unit1 > 0 && qty > 0) {
            updated.quotation_one_total = (qty * unit1).toFixed(2);
          }
        }
        if (field === 'quotation_two_unit' || field === 'quantity') {
          const unit2 =
            Number.parseFloat(field === 'quotation_two_unit' ? value : item.quotation_two_unit) || 0;
          if (unit2 > 0 && qty > 0) {
            updated.quotation_two_total = (qty * unit2).toFixed(2);
          }
        }
        return updated;
      })
    );
  };

  const addItem = () => {
    if (items.length >= 6) {
      toast.error('Maximum 6 items allowed on a single comparative schedule');
      return;
    }
    setItems((curr) => [...curr, emptyItem()]);
  };

  const removeItem = (key: string) => {
    if (items.length <= 1) return;
    setItems((curr) => curr.filter((i) => i.key !== key));
  };

  const totalQuotationOne = items.reduce(
    (sum, item) => sum + (Number.parseFloat(item.quotation_one_total) || 0),
    0
  );
  const totalQuotationTwo = items.reduce(
    (sum, item) => sum + (Number.parseFloat(item.quotation_two_total) || 0),
    0
  );

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const filled = items.filter((item) => item.description.trim());
    if (!filled.length) {
      toast.error('Enter at least one item description');
      return;
    }

    if (!recommendation.trim()) {
      toast.error('Please enter procurement recommendations');
      return;
    }

    setIsSubmitting(true);
    try {
      await comparativeScheduleService.createSchedule({
        compliance,
        items: filled.map((i) => ({
          description: i.description.trim(),
          quantity: i.quantity,
          quotation_one_unit: i.quotation_one_unit,
          quotation_one_total: i.quotation_one_total,
          quotation_two_unit: i.quotation_two_unit,
          quotation_two_total: i.quotation_two_total,
        })),
        recommendation: recommendation.trim(),
      });
      toast.success('Comparative schedule submitted to Director for approval');
      setItems([emptyItem()]);
      setRecommendation('');
      await load();
      setActiveTab('schedules');
    } catch {
      toast.error('Unable to submit comparative schedule');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Combine real schedules with sample for preview
  const displaySchedules = [...schedules];
  if (showSample && !schedules.some((s) => s.id === sampleApprovedSchedule.id)) {
    displaySchedules.unshift(sampleApprovedSchedule);
  }

  return (
    <div className={`space-y-6 ${printingScheduleId !== null ? 'stores-page printing-history' : ''}`}>
      <PageHeader
        title="Comparative Schedules"
        description="Quotation analysis and supplier price comparison for official purchases"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="new">New Schedule</TabsTrigger>
          <TabsTrigger value="schedules">
            Submitted Schedules ({displaySchedules.length})
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: New Comparative Schedule Form */}
        <TabsContent value="new" className="mt-6">
          <form onSubmit={submit} className="space-y-6 max-w-5xl">
            {/* Requester Identity Card */}
            <RequesterInfoCard employee={employee} />

            {/* Supplier Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Scale className="h-4 w-4 text-primary" />
                  Supplier Names
                </CardTitle>
                <CardDescription>
                  Enter the registered company names of the competing suppliers being compared.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="supplier_one">Supplier 1 Name</Label>
                    <Input
                      id="supplier_one"
                      value={supplierOneName}
                      onChange={(e) => setSupplierOneName(e.target.value)}
                      placeholder="e.g. Apex Technologies Pvt Ltd"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="supplier_two">Supplier 2 Name</Label>
                    <Input
                      id="supplier_two"
                      value={supplierTwoName}
                      onChange={(e) => setSupplierTwoName(e.target.value)}
                      placeholder="e.g. Synergy Networks Zimbabwe"
                      required
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Compliance Checklist */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Compliance Checklist</CardTitle>
                <CardDescription>
                  Verify statutory and technical compliance for each quoting supplier.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50 text-left">
                        <th className="p-3 font-medium">Compliance Requirement</th>
                        <th className="p-3 font-medium">{supplierOneName}</th>
                        <th className="p-3 font-medium">{supplierTwoName}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {checks.map((check) => (
                        <tr key={check}>
                          <td className="p-3 font-medium text-foreground">{check}</td>
                          <td className="p-3">
                            <Input
                              value={compliance[`${check}_one`] || ''}
                              onChange={(e) =>
                                setCompliance((c) => ({ ...c, [`${check}_one`]: e.target.value }))
                              }
                              placeholder="Compliant"
                              className="h-8 max-w-[200px]"
                            />
                          </td>
                          <td className="p-3">
                            <Input
                              value={compliance[`${check}_two`] || ''}
                              onChange={(e) =>
                                setCompliance((c) => ({ ...c, [`${check}_two`]: e.target.value }))
                              }
                              placeholder="Compliant"
                              className="h-8 max-w-[200px]"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Price Comparison Line Items */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold">Price Comparison</CardTitle>
                    <CardDescription>
                      Itemized quotation comparisons. Line totals and grand totals calculate automatically.
                    </CardDescription>
                  </div>
                  <span className="text-xs text-muted-foreground font-medium">
                    {items.length} / 6 items
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
                          className="text-destructive hover:text-destructive hover:bg-destructive/10 h-7 px-2"
                          onClick={() => removeItem(item.key)}
                          disabled={isSubmitting}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2 md:col-span-2">
                        <Label htmlFor={`desc-${item.key}`}>Item Description *</Label>
                        <Input
                          id={`desc-${item.key}`}
                          placeholder="e.g. Server Rails 2U"
                          value={item.description}
                          onChange={(e) => updateItem(item.key, 'description', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor={`qty-${item.key}`}>Quantity *</Label>
                        <Input
                          id={`qty-${item.key}`}
                          type="number"
                          min="1"
                          placeholder="1"
                          value={item.quantity}
                          onChange={(e) => updateItem(item.key, 'quantity', e.target.value)}
                          required
                          disabled={isSubmitting}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-border/40">
                      {/* Supplier 1 Quote */}
                      <div className="p-3 bg-muted/30 rounded-lg space-y-2">
                        <span className="text-xs font-semibold text-foreground block">
                          {supplierOneName} Pricing (USD)
                        </span>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label className="text-xs">Unit Price ($)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              value={item.quotation_one_unit}
                              onChange={(e) => updateItem(item.key, 'quotation_one_unit', e.target.value)}
                              disabled={isSubmitting}
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Line Total ($)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              value={item.quotation_one_total}
                              onChange={(e) => updateItem(item.key, 'quotation_one_total', e.target.value)}
                              disabled={isSubmitting}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Supplier 2 Quote */}
                      <div className="p-3 bg-muted/30 rounded-lg space-y-2">
                        <span className="text-xs font-semibold text-foreground block">
                          {supplierTwoName} Pricing (USD)
                        </span>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label className="text-xs">Unit Price ($)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              value={item.quotation_two_unit}
                              onChange={(e) => updateItem(item.key, 'quotation_two_unit', e.target.value)}
                              disabled={isSubmitting}
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Line Total ($)</Label>
                            <Input
                              type="number"
                              step="0.01"
                              placeholder="0.00"
                              value={item.quotation_two_total}
                              onChange={(e) => updateItem(item.key, 'quotation_two_total', e.target.value)}
                              disabled={isSubmitting}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {items.length < 6 && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={addItem}
                    disabled={isSubmitting}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Comparison Item
                  </Button>
                )}

                {/* Grand Total Comparison */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-lg bg-muted/60 border font-medium">
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{supplierOneName} Grand Total:</span>
                    <span className="text-base font-bold text-foreground">
                      ${totalQuotationOne.toFixed(2)} USD
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm">{supplierTwoName} Grand Total:</span>
                    <span className="text-base font-bold text-foreground">
                      ${totalQuotationTwo.toFixed(2)} USD
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-semibold">Recommendations</CardTitle>
                <CardDescription>
                  Provide a justified recommendation for award to the Director.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  rows={4}
                  placeholder="State the recommended supplier, justification (e.g. lowest compliant price, delivery turnaround, warranty terms)..."
                  value={recommendation}
                  onChange={(e) => setRecommendation(e.target.value)}
                  required
                />
              </CardContent>
            </Card>

            <div className="flex items-center justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setItems([emptyItem()]);
                  setRecommendation('');
                }}
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
                    Submit Schedule for Approval
                  </>
                )}
              </Button>
            </div>
          </form>
        </TabsContent>

        {/* Tab 2: Submitted Schedules */}
        <TabsContent value="schedules" className="mt-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2 pb-2">
            <h2 className="text-base font-semibold text-foreground">Submitted Comparative Schedules</h2>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowSample((v) => !v);
                if (!showSample) setExpandedScheduleId(sampleApprovedSchedule.id);
              }}
              className="text-xs"
            >
              <FileCheck className="mr-1.5 h-3.5 w-3.5 text-emerald-600" />
              {showSample ? 'Hide Approved Sample' : 'Preview Fully Approved Sample'}
            </Button>
          </div>

          <section className="stores-history">
            {displaySchedules.length === 0 ? (
              <Card className="p-8 text-center text-muted-foreground">
                <p>No comparative schedules submitted yet.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => setActiveTab('new')}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Create Schedule
                </Button>
              </Card>
            ) : (
              displaySchedules.map((schedule) => {
                const isSample = schedule.id === sampleApprovedSchedule.id;
                const expanded = expandedScheduleId === schedule.id;
                const printTarget = printingScheduleId === schedule.id;

                return (
                  <article
                    className={`stores-history-item rounded-lg border bg-card p-5 mb-4 shadow-xs ${
                      isSample ? 'border-emerald-300 bg-emerald-50/20' : ''
                    } ${expanded ? ' is-expanded' : ''}${printTarget ? ' is-print-target' : ''}`}
                    key={schedule.id}
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-border/60">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-base text-foreground">
                            {schedule.schedule_number}
                          </span>
                          <RequisitionStatusBadge status={schedule.status} labels={statuses} />
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
                          Items: <strong>{schedule.items.length}</strong> · Created:{' '}
                          {(schedule.procurement_submitted_at || schedule.created_at || '').slice(0, 10)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant={expanded ? 'default' : 'outline'}
                          onClick={() => setExpandedScheduleId(expanded ? null : schedule.id)}
                        >
                          {expanded ? 'Hide schedule' : 'View completed schedule'}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setPrintingScheduleId(schedule.id)}
                        >
                          <Printer className="mr-2 h-4 w-4" />
                          Print
                        </Button>
                      </div>
                    </div>

                    <div className="pt-3 text-xs">
                      <span className="text-muted-foreground block font-medium">Recommendation:</span>
                      <p className="text-foreground mt-0.5">{schedule.recommendation}</p>
                    </div>

                    {/* Official Completed Comparative Schedule Layout (for Print & View) */}
                    {expanded && (
                      <div className="stores-paper comparative-paper mt-5 pt-4 border-t">
                        <header className="stores-header">
                          <h1>COMPARATIVE SCHEDULE FOR THE PURCHASE OF</h1>
                          <img src="/logo.png" alt="ZCHPC" />
                        </header>
                        <table className="stores-table compliance-table">
                          <thead>
                            <tr>
                              <th>Compliance Checklist</th>
                              <th>Supplier 1</th>
                              <th>Supplier 2</th>
                            </tr>
                          </thead>
                          <tbody>
                            {checks.map((check) => (
                              <tr key={check}>
                                <td>{check}</td>
                                <td>
                                  <input
                                    value={schedule.compliance[`${check}_one`] || 'Compliant'}
                                    readOnly
                                  />
                                </td>
                                <td>
                                  <input
                                    value={schedule.compliance[`${check}_two`] || 'Compliant'}
                                    readOnly
                                  />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        <h2>Price Comparison</h2>
                        <table className="stores-table comparison-table">
                          <thead>
                            <tr>
                              <th>Description</th>
                              <th>Qty.</th>
                              <th>
                                Unit Price
                                <br />
                                USD
                              </th>
                              <th>
                                Total Price
                                <br />
                                USD
                              </th>
                              <th>
                                Unit Price
                                <br />
                                USD
                              </th>
                              <th>
                                Total Price
                                <br />
                                USD
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {schedule.items.map((item, index) => (
                              <tr key={index}>
                                <td>
                                  <input value={item.description} readOnly />
                                </td>
                                <td>
                                  <input value={item.quantity} readOnly />
                                </td>
                                <td>
                                  <input value={item.quotation_one_unit} readOnly />
                                </td>
                                <td>
                                  <input value={item.quotation_one_total} readOnly />
                                </td>
                                <td>
                                  <input value={item.quotation_two_unit} readOnly />
                                </td>
                                <td>
                                  <input value={item.quotation_two_total} readOnly />
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>

                        <section className="recommendation">
                          <h2>Recommendations:</h2>
                          <textarea value={schedule.recommendation} readOnly rows={4} />
                        </section>

                        <div className="comparison-signatures">
                          <div>
                            Compiled by: Procurement Officer:{' '}
                            <span>{employee?.full_name || 'Procurement Officer'}</span>
                          </div>
                          <div>
                            Signature <span>Electronically verified</span> Date{' '}
                            <span>{(schedule.procurement_submitted_at || schedule.created_at || '').slice(0, 10)}</span>
                          </div>
                          <div>
                            Approved by: <span>Dr. N. Sithole</span>
                          </div>
                          <div>
                            Signature <span>Approved electronically</span> Date{' '}
                            <span>{(schedule.procurement_submitted_at || schedule.created_at || '').slice(0, 10)}</span>
                          </div>
                          <strong>ZCHPC DIRECTOR</strong>
                        </div>
                      </div>
                    )}
                  </article>
                );
              })
            )}
          </section>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ComparativeSchedulesPage;
