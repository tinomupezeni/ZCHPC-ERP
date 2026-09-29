import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Loader2, Save, Send } from 'lucide-react';
import { RequesterInfoCard } from './RequesterInfoCard';
import { PurchaseRequestItemsForm } from './PurchaseRequestItemsForm';
import {
  createEmptyItem,
  formatCents,
  itemsFromExistingRequest,
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
  /**
   * Slice 2: editing an existing DRAFT, or correcting a REJECTED request -
   * the backend transitions REJECTED -> DRAFT as part of the same save that
   * persists the correction (see UpdatePurchaseRequestItems), so both are
   * this one 'edit' mode; there is no separate correct-and-resubmit call
   * from here. 'create' (default) is the original new-request flow,
   * unchanged.
   */
  mode?: 'create' | 'edit';
  existingRequest?: PurchaseRequest;
  /** Called when a plain "Save Draft" succeeds, in either mode - saving never implies submitting. */
  onSaved?: (request: PurchaseRequest) => void;
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

export function PurchaseRequestForm({
  employee,
  onSubmitted,
  mode = 'create',
  existingRequest,
  onSaved,
}: PurchaseRequestFormProps) {
  const isEdit = mode === 'edit';

  const [items, setItems] = useState<DraftItem[]>(() =>
    isEdit && existingRequest ? itemsFromExistingRequest(existingRequest) : [createEmptyItem()]
  );
  const [errors, setErrors] = useState<Record<string, DraftItemErrors>>({});

  const [categories, setCategories] = useState<PurchaseRequestCategory[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  // The persisted request this form is currently committed to: null until
  // create succeeds (create mode), or the request being edited from the
  // start (edit mode) - kept up to date after every successful save.
  const [savedRequest, setSavedRequest] = useState<PurchaseRequest | null>(
    isEdit && existingRequest ? existingRequest : null
  );
  // True once a save has succeeded but the following submit hasn't - the
  // recovery-banner condition, for both create and edit.
  const [pendingSubmit, setPendingSubmit] = useState(false);

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

  const validateOrToast = (): boolean => {
    if (items.length === 0) {
      toast.error('Add at least one item before saving');
      return false;
    }
    const validationErrors = validateItems(items);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      toast.error('Please fix the highlighted fields');
      return false;
    }
    return true;
  };

  const buildItemPayload = () =>
    items.map((item) => ({
      ...(item.id ? { id: item.id } : {}),
      description: item.description.trim(),
      quantity: Number.parseInt(item.quantity, 10),
      expected_delivery_period: item.expected_delivery_period.trim(),
      estimated_cost: item.estimated_cost,
      category_id: Number.parseInt(item.category_id, 10),
    }));

  const handleCreateAndSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!savedRequest && !validateOrToast()) return;

    setIsSubmitting(true);

    let draft = savedRequest;
    if (!draft) {
      try {
        draft = await purchaseRequestService.createRequest({ items: buildItemPayload() });
        setSavedRequest(draft);
        setPendingSubmit(true);
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
      setSavedRequest(null);
      setPendingSubmit(false);
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

  /** Edit mode "Save Draft": persists changes to the request being edited via PATCH. */
  const handleSaveExistingDraft = async () => {
    if (isSaving || isSubmitting || !savedRequest) return;
    if (!validateOrToast()) return;

    setIsSaving(true);
    try {
      const saved = await purchaseRequestService.updateItems(savedRequest.id, {
        items: buildItemPayload(),
      });
      setSavedRequest(saved);
      setPendingSubmit(false);
      toast.success(`${saved.requisition_number} saved`);
      onSaved?.(saved);
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to save changes'));
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Create mode "Save Draft": a brand-new request has no id yet, so this
   * calls create only - never submit. On success the form hands the created
   * draft back to the caller (same as a completed submit) rather than
   * staying open in a half-created state.
   */
  const handleSaveNewDraft = async () => {
    if (isSaving || isSubmitting) return;
    if (!validateOrToast()) return;

    setIsSaving(true);
    try {
      const created = await purchaseRequestService.createRequest({ items: buildItemPayload() });
      toast.success(`Draft ${created.requisition_number} saved`);
      resetForm();
      onSaved?.(created);
    } catch (error) {
      toast.error(getPurchaseRequestErrorMessage(error, 'Failed to save draft'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveDraft = isEdit ? handleSaveExistingDraft : handleSaveNewDraft;

  const handleEditAndSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting || !savedRequest) return;

    if (!pendingSubmit && !validateOrToast()) return;

    setIsSubmitting(true);

    let current = savedRequest;
    if (!pendingSubmit) {
      try {
        current = await purchaseRequestService.updateItems(current.id, {
          items: buildItemPayload(),
        });
        setSavedRequest(current);
        setPendingSubmit(true);
      } catch (error) {
        toast.error(getPurchaseRequestErrorMessage(error, 'Failed to save changes'));
        setIsSubmitting(false);
        return;
      }
    }

    try {
      const submitted = await purchaseRequestService.submitRequest(current.id);
      toast.success(`Purchase requisition ${submitted.requisition_number} submitted`);
      setPendingSubmit(false);
      onSubmitted(submitted);
    } catch (error) {
      toast.error(
        getPurchaseRequestErrorMessage(
          error,
          'Changes were saved but the request could not be submitted. You can retry below.'
        )
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = isEdit ? handleEditAndSubmit : handleCreateAndSubmit;

  const grandTotalCents = items.reduce((sum, item) => {
    const cents = lineTotalCents(item);
    return cents === null ? sum : sum + cents;
  }, 0);
  // At least one fully-costed line item - guards against showing/submitting
  // a fake "$0.00" for a pristine or incomplete form.
  const hasValidLineItem = items.some((item) => lineTotalCents(item) !== null);

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
        disabled={isSubmitting || isSaving || (!isEdit && !!savedRequest)}
      />

      {!isEdit && savedRequest && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-orange-800">
              <p className="font-medium">
                Draft {savedRequest.requisition_number} was created but has not been submitted.
              </p>
              <p>Retry submitting below, or discard and start a new request.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {isEdit && pendingSubmit && savedRequest && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-orange-800">
              <p className="font-medium">
                Your changes to {savedRequest.requisition_number} were saved but it has not been
                submitted.
              </p>
              <p>Retry submitting below.</p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center justify-between gap-3 flex-wrap">
        {!isEdit && savedRequest ? (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setSavedRequest(null);
              setPendingSubmit(false);
              resetForm();
            }}
            disabled={isSubmitting}
          >
            Discard &amp; Start New
          </Button>
        ) : (
          <Button
            type="button"
            variant="outline"
            onClick={handleSaveDraft}
            disabled={isSaving || isSubmitting}
          >
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Draft
              </>
            )}
          </Button>
        )}

        <Button
          type="submit"
          disabled={
            isSubmitting || isSaving || categoriesLoading || (!pendingSubmit && !hasValidLineItem)
          }
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {pendingSubmit ? 'Retrying submission...' : 'Submitting...'}
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              {pendingSubmit
                ? 'Retry Submission'
                : hasValidLineItem
                  ? `Submit Purchase Requisition (${formatCents(grandTotalCents)})`
                  : 'Submit Purchase Requisition'}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

export default PurchaseRequestForm;
