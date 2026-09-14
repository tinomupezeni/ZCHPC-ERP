import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Loader2, Send } from 'lucide-react';
import { RequesterInfoCard } from './RequesterInfoCard';
import { PurchaseRequestItemsForm } from './PurchaseRequestItemsForm';
import {
  createEmptyItem,
  formatCents,
  lineTotalCents,
  type DraftItem,
  type DraftItemErrors,
} from './draftItem';
import {
  purchaseRequestService,
  getPurchaseRequestErrorMessage,
} from '@/services/purchase-request.service';
import type { Employee } from '@/types/auth.types';
import type { PurchaseRequest, PurchaseRequestCategory } from '@/types/purchase-request.types';

interface PurchaseRequestFormProps {
  employee: Employee;
  onSubmitted: (request: PurchaseRequest) => void;
}

function validateItems(items: DraftItem[]): Record<string, DraftItemErrors> {
  const errors: Record<string, DraftItemErrors> = {};

  for (const item of items) {
    const itemErrors: DraftItemErrors = {};

    if (!item.description.trim()) {
      itemErrors.description = 'Description is required';
    }

    const qty = Number.parseInt(item.quantity, 10);
    if (!item.quantity.trim() || !Number.isFinite(qty)) {
      itemErrors.quantity = 'Quantity is required';
    } else if (qty <= 0) {
      itemErrors.quantity = 'Quantity must be greater than zero';
    }

    if (!item.expected_delivery_period.trim()) {
      itemErrors.expected_delivery_period = 'Expected delivery period is required';
    }

    const cost = Number.parseFloat(item.estimated_cost);
    if (!item.estimated_cost.trim() || !Number.isFinite(cost)) {
      itemErrors.estimated_cost = 'Estimated cost is required';
    } else if (cost < 0) {
      itemErrors.estimated_cost = 'Estimated cost cannot be negative';
    }

    if (!item.category_id) {
      itemErrors.category_id = 'Category is required';
    }

    if (Object.keys(itemErrors).length > 0) {
      errors[item.key] = itemErrors;
    }
  }

  return errors;
}

export function PurchaseRequestForm({ employee, onSubmitted }: PurchaseRequestFormProps) {
  const [items, setItems] = useState<DraftItem[]>([createEmptyItem()]);
  const [errors, setErrors] = useState<Record<string, DraftItemErrors>>({});

  const [categories, setCategories] = useState<PurchaseRequestCategory[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingDraft, setPendingDraft] = useState<PurchaseRequest | null>(null);

  const loadCategories = useCallback(async () => {
    setCategoriesLoading(true);
    setCategoriesError(null);
    try {
      const data = await purchaseRequestService.getCategories();
      setCategories(data);
    } catch (error) {
      setCategories([]);
      setCategoriesError(
        getPurchaseRequestErrorMessage(error, 'Failed to load purchase request categories')
      );
    } finally {
      setCategoriesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  const resetForm = () => {
    setItems([createEmptyItem()]);
    setErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!pendingDraft) {
      if (items.length === 0) {
        toast.error('Add at least one item before submitting');
        return;
      }
      const validationErrors = validateItems(items);
      setErrors(validationErrors);
      if (Object.keys(validationErrors).length > 0) {
        toast.error('Please fix the highlighted fields');
        return;
      }
    }

    setIsSubmitting(true);

    let draft = pendingDraft;
    if (!draft) {
      try {
        draft = await purchaseRequestService.createRequest({
          items: items.map((item) => ({
            description: item.description.trim(),
            quantity: Number.parseInt(item.quantity, 10),
            expected_delivery_period: item.expected_delivery_period.trim(),
            estimated_cost: item.estimated_cost,
            category_id: Number.parseInt(item.category_id, 10),
          })),
        });
        setPendingDraft(draft);
      } catch (error) {
        toast.error(
          getPurchaseRequestErrorMessage(error, 'Failed to create purchase requisition')
        );
        setIsSubmitting(false);
        return;
      }
    }

    try {
      const submitted = await purchaseRequestService.submitRequest(draft.id);
      toast.success(`Purchase requisition ${submitted.requisition_number} submitted`);
      setPendingDraft(null);
      resetForm();
      onSubmitted(submitted);
    } catch (error) {
      toast.error(
        getPurchaseRequestErrorMessage(
          error,
          'The draft was created but could not be submitted. You can retry below.'
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const grandTotalCents = items.reduce((sum, item) => {
    const cents = lineTotalCents(item);
    return cents === null ? sum : sum + cents;
  }, 0);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <RequesterInfoCard employee={employee} />

      <PurchaseRequestItemsForm
        items={items}
        onChange={setItems}
        errors={errors}
        categories={categories}
        categoriesLoading={categoriesLoading}
        categoriesError={categoriesError}
        onRetryCategories={loadCategories}
        disabled={isSubmitting || !!pendingDraft}
      />

      {pendingDraft && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-orange-800">
              <p className="font-medium">
                Draft {pendingDraft.requisition_number} was created but has not been submitted.
              </p>
              <p>Retry submitting below, or discard and start a new request.</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        {pendingDraft ? (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setPendingDraft(null);
              resetForm();
            }}
            disabled={isSubmitting}
          >
            Discard &amp; Start New
          </Button>
        ) : (
          <div />
        )}

        <Button type="submit" disabled={isSubmitting || categoriesLoading}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {pendingDraft ? 'Retrying submission...' : 'Submitting...'}
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              {pendingDraft
                ? 'Retry Submission'
                : `Submit Purchase Requisition (${formatCents(grandTotalCents)})`}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

export default PurchaseRequestForm;
