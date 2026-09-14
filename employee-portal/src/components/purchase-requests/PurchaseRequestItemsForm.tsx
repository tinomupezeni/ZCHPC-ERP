import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ListPlus, Loader2, Package, Trash2 } from 'lucide-react';
import type { PurchaseRequestCategory } from '@/types/purchase-request.types';
import {
  createEmptyItem,
  formatCents,
  lineTotalCents,
  type DraftItem,
  type DraftItemErrors,
} from './draftItem';

interface PurchaseRequestItemsFormProps {
  items: DraftItem[];
  onChange: (items: DraftItem[]) => void;
  errors: Record<string, DraftItemErrors>;
  categories: PurchaseRequestCategory[];
  categoriesLoading: boolean;
  categoriesError: string | null;
  onRetryCategories: () => void;
  disabled?: boolean;
}

export function PurchaseRequestItemsForm({
  items,
  onChange,
  errors,
  categories,
  categoriesLoading,
  categoriesError,
  onRetryCategories,
  disabled,
}: PurchaseRequestItemsFormProps) {
  const updateItem = (key: string, patch: Partial<DraftItem>) => {
    onChange(items.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  };

  const removeItem = (key: string) => {
    onChange(items.filter((item) => item.key !== key));
  };

  const addItem = () => {
    onChange([...items, createEmptyItem()]);
  };

  const grandTotalCents = items.reduce((sum, item) => {
    const cents = lineTotalCents(item);
    return cents === null ? sum : sum + cents;
  }, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Package className="h-5 w-5" />
          Item(s) Requested
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {categoriesError && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 flex items-center justify-between gap-3 text-sm">
            <span className="text-destructive">{categoriesError}</span>
            <Button type="button" variant="outline" size="sm" onClick={onRetryCategories}>
              Retry
            </Button>
          </div>
        )}

        {items.map((item, index) => {
          const itemErrors = errors[item.key] ?? {};
          const cents = lineTotalCents(item);

          return (
            <div key={item.key} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  Item {index + 1}
                </span>
                {items.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive hover:bg-destructive/10 h-7 px-2"
                    onClick={() => removeItem(item.key)}
                    disabled={disabled}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`description-${item.key}`}>Item Description</Label>
                <Input
                  id={`description-${item.key}`}
                  placeholder="e.g. Laptop"
                  value={item.description}
                  onChange={(e) => updateItem(item.key, { description: e.target.value })}
                  disabled={disabled}
                />
                {itemErrors.description && (
                  <p className="text-sm text-destructive">{itemErrors.description}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor={`quantity-${item.key}`}>Quantity</Label>
                  <Input
                    id={`quantity-${item.key}`}
                    type="number"
                    min={1}
                    step={1}
                    value={item.quantity}
                    onChange={(e) => updateItem(item.key, { quantity: e.target.value })}
                    disabled={disabled}
                  />
                  {itemErrors.quantity && (
                    <p className="text-sm text-destructive">{itemErrors.quantity}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`delivery-${item.key}`}>Expected Delivery Period</Label>
                  <Input
                    id={`delivery-${item.key}`}
                    placeholder="e.g. 2 weeks"
                    value={item.expected_delivery_period}
                    onChange={(e) =>
                      updateItem(item.key, { expected_delivery_period: e.target.value })
                    }
                    disabled={disabled}
                  />
                  {itemErrors.expected_delivery_period && (
                    <p className="text-sm text-destructive">
                      {itemErrors.expected_delivery_period}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor={`cost-${item.key}`}>Estimated Cost (USD)</Label>
                  <Input
                    id={`cost-${item.key}`}
                    type="number"
                    min={0}
                    step="0.01"
                    placeholder="0.00"
                    value={item.estimated_cost}
                    onChange={(e) => updateItem(item.key, { estimated_cost: e.target.value })}
                    disabled={disabled}
                  />
                  {itemErrors.estimated_cost && (
                    <p className="text-sm text-destructive">{itemErrors.estimated_cost}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`category-${item.key}`}>Category</Label>
                  <Select
                    value={item.category_id}
                    onValueChange={(value) => updateItem(item.key, { category_id: value })}
                    disabled={disabled || categoriesLoading || !!categoriesError}
                  >
                    <SelectTrigger id={`category-${item.key}`}>
                      <SelectValue
                        placeholder={categoriesLoading ? 'Loading categories...' : 'Select category'}
                      />
                    </SelectTrigger>
                    <SelectContent>
                      {categories.length === 0 && !categoriesLoading ? (
                        <div className="px-3 py-2 text-sm text-muted-foreground">
                          No categories available
                        </div>
                      ) : (
                        categories.map((category) => (
                          <SelectItem key={category.id} value={category.id.toString()}>
                            {category.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  {itemErrors.category_id && (
                    <p className="text-sm text-destructive">{itemErrors.category_id}</p>
                  )}
                </div>
              </div>

              <div className="text-right text-sm text-muted-foreground">
                Line total:{' '}
                <span className="font-medium text-foreground">
                  {cents === null ? '—' : formatCents(cents)}
                </span>
              </div>
            </div>
          );
        })}

        <Button
          type="button"
          variant="outline"
          onClick={addItem}
          disabled={disabled}
          className="w-full"
        >
          <ListPlus className="h-4 w-4 mr-2" />
          Add Item
        </Button>

        <p className="text-xs text-muted-foreground">
          Provide detailed specifications for each item in its description. Attach any
          supporting documents separately if required.
        </p>

        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <span className="font-medium">Total Estimated Cost</span>
          <span className="text-lg font-semibold">
            {categoriesLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              formatCents(grandTotalCents)
            )}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default PurchaseRequestItemsForm;
