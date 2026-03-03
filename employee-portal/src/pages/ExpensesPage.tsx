import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PageHeader } from '@/components/layout';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ExpenseForm, ExpensesList } from '@/components/expenses';
import { expenseService } from '@/services/expense.service';
import { FileText, Clock, CheckCircle, DollarSign } from 'lucide-react';
import type {
  ExpenseCategory,
  ExpenseClaimListItem,
  ExpenseClaimSummary,
  ExpenseStatus,
  CreateExpenseClaimData,
} from '@/types/expense.types';

export function ExpensesPage() {
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [expenses, setExpenses] = useState<ExpenseClaimListItem[]>([]);
  const [summary, setSummary] = useState<ExpenseClaimSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittingId, setSubmittingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<ExpenseStatus | 'all'>('all');
  const [activeTab, setActiveTab] = useState('claims');

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadExpenses();
  }, [statusFilter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [categoriesData, expensesData, summaryData] = await Promise.all([
        expenseService.getCategories(),
        expenseService.getClaims(),
        expenseService.getSummary(),
      ]);

      setCategories(categoriesData);
      setExpenses(expensesData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load expense data:', error);
      toast.error('Failed to load expense data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadExpenses = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : undefined;
      const expensesData = await expenseService.getClaims(params);
      setExpenses(expensesData);
    } catch (error) {
      console.error('Failed to load expenses:', error);
    }
  };

  const handleCreateExpense = async (data: CreateExpenseClaimData) => {
    setIsSubmitting(true);
    try {
      await expenseService.createClaim(data);
      toast.success('Expense claim created successfully');

      // Refresh data
      const [expensesData, summaryData] = await Promise.all([
        expenseService.getClaims(statusFilter !== 'all' ? { status: statusFilter } : undefined),
        expenseService.getSummary(),
      ]);
      setExpenses(expensesData);
      setSummary(summaryData);

      // Switch to claims tab
      setActiveTab('claims');
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to create expense claim';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitExpense = async (id: number) => {
    setSubmittingId(id);
    try {
      await expenseService.submitClaim(id);
      toast.success('Expense claim submitted for review');

      // Refresh data
      const [expensesData, summaryData] = await Promise.all([
        expenseService.getClaims(statusFilter !== 'all' ? { status: statusFilter } : undefined),
        expenseService.getSummary(),
      ]);
      setExpenses(expensesData);
      setSummary(summaryData);
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to submit expense claim';
      toast.error(errorMessage);
    } finally {
      setSubmittingId(null);
    }
  };

  const handleDeleteExpense = async (id: number) => {
    setDeletingId(id);
    try {
      await expenseService.cancelClaim(id);
      toast.success('Expense claim cancelled');

      // Refresh data
      const [expensesData, summaryData] = await Promise.all([
        expenseService.getClaims(statusFilter !== 'all' ? { status: statusFilter } : undefined),
        expenseService.getSummary(),
      ]);
      setExpenses(expensesData);
      setSummary(summaryData);
    } catch (error) {
      const errorMessage =
        (error as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'Failed to cancel expense claim';
      toast.error(errorMessage);
    } finally {
      setDeletingId(null);
    }
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Expenses"
        description="Submit and track your expense claims"
      />

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center">
                  <FileText className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Drafts</p>
                  <p className="text-xl font-semibold">{summary.draft_claims}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <Clock className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Pending</p>
                  <p className="text-xl font-semibold">{summary.pending_claims}</p>
                  {summary.total_amount_pending > 0 && (
                    <p className="text-xs text-muted-foreground">
                      {formatCurrency(summary.total_amount_pending)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Approved</p>
                  <p className="text-xl font-semibold">{summary.approved_claims}</p>
                  {summary.total_amount_approved > 0 && (
                    <p className="text-xs text-muted-foreground">
                      {formatCurrency(summary.total_amount_approved)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Paid</p>
                  <p className="text-xl font-semibold">{summary.paid_claims}</p>
                  {summary.total_amount_paid > 0 && (
                    <p className="text-xs text-muted-foreground">
                      {formatCurrency(summary.total_amount_paid)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="claims">My Claims</TabsTrigger>
          <TabsTrigger value="new">New Claim</TabsTrigger>
        </TabsList>

        <TabsContent value="claims" className="mt-4">
          <ExpensesList
            expenses={expenses}
            isLoading={isLoading}
            statusFilter={statusFilter}
            onStatusFilter={setStatusFilter}
            onSubmit={handleSubmitExpense}
            onDelete={handleDeleteExpense}
            submittingId={submittingId}
            deletingId={deletingId}
          />
        </TabsContent>

        <TabsContent value="new" className="mt-4">
          <ExpenseForm
            categories={categories}
            onSubmit={handleCreateExpense}
            isSubmitting={isSubmitting}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default ExpensesPage;
