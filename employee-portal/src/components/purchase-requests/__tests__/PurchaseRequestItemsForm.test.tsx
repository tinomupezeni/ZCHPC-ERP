import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PurchaseRequestItemsForm } from '../PurchaseRequestItemsForm';
import { createEmptyItem, type DraftItem } from '../draftItem';
import type { PurchaseRequestCategory } from '@/types/purchase-request.types';

const categories: PurchaseRequestCategory[] = [
  { id: 1, name: 'IT Consumables' },
  { id: 2, name: 'Stationery & Printing' },
];

function twoItems(): DraftItem[] {
  return [createEmptyItem(), createEmptyItem()];
}

function baseProps(items: DraftItem[]) {
  return {
    items,
    onChange: vi.fn(),
    errors: {},
    categories,
    categoriesLoading: false,
    categoriesError: null,
    onRetryCategories: vi.fn(),
  };
}

describe('PurchaseRequestItemsForm', () => {
  it('renders one field group per item: description, quantity, delivery, cost, category', () => {
    render(<PurchaseRequestItemsForm {...baseProps([createEmptyItem()])} />);

    expect(screen.getByLabelText('Item Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Quantity')).toBeInTheDocument();
    expect(screen.getByLabelText('Expected Delivery Period')).toBeInTheDocument();
    expect(screen.getByLabelText('Estimated Unit Cost (USD)')).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
  });

  it('makes the per-unit meaning of the cost field explicit, distinct from the line total', () => {
    render(<PurchaseRequestItemsForm {...baseProps([createEmptyItem()])} />);

    expect(screen.getByText(/cost per unit/i)).toBeInTheDocument();
    expect(screen.getByText('Line total:')).toBeInTheDocument();
    expect(screen.queryByText('Estimated Cost (USD)')).not.toBeInTheDocument();
  });

  it('displays the selected category by name only - never a raw AccountChart id or GL code', () => {
    // Radix's Select popup is portal-rendered and only mounts once opened via
    // real pointer events, which jsdom cannot simulate reliably (a documented
    // Radix/jsdom limitation) - so this drives it as a controlled component
    // instead of trying to click the popup open. SelectValue always renders
    // the chosen item's label in the trigger itself, open or closed, so this
    // still proves the employee sees a name, never an id or GL code.
    const item = { ...createEmptyItem(), category_id: '1' };
    render(<PurchaseRequestItemsForm {...baseProps([item])} />);

    expect(screen.getByText('IT Consumables')).toBeInTheDocument();
    expect(screen.queryByText(/budget_code_id/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/account_chart/i)).not.toBeInTheDocument();
    expect(screen.queryByText('1')).not.toBeInTheDocument();
  });

  it('supports multiple independent line items', () => {
    render(<PurchaseRequestItemsForm {...baseProps(twoItems())} />);

    expect(screen.getAllByLabelText('Item Description')).toHaveLength(2);
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('calls onChange with an additional item when "Add Item" is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const items = [createEmptyItem()];
    render(<PurchaseRequestItemsForm {...baseProps(items)} onChange={onChange} />);

    await user.click(screen.getByRole('button', { name: /add item/i }));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0][0]).toHaveLength(2);
  });

  it('does not offer a remove control when only one item remains', () => {
    render(<PurchaseRequestItemsForm {...baseProps([createEmptyItem()])} />);
    // Only "Add Item" should be present - no icon-only remove button.
    expect(screen.getAllByRole('button')).toHaveLength(1);
    expect(screen.getByRole('button', { name: /add item/i })).toBeInTheDocument();
  });

  it('removes only the targeted item, leaving the other untouched', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const items = twoItems();
    const secondItemKey = items[1].key;
    render(<PurchaseRequestItemsForm {...baseProps(items)} onChange={onChange} />);

    const itemBlocks = screen
      .getAllByText(/^Item \d$/)
      .map((el) => el.closest<HTMLElement>('div.rounded-lg')!);
    const removeButtonInFirstItem = within(itemBlocks[0]).getByRole('button');
    await user.click(removeButtonInFirstItem);

    expect(onChange).toHaveBeenCalledTimes(1);
    const remaining = onChange.mock.calls[0][0] as DraftItem[];
    expect(remaining).toHaveLength(1);
    expect(remaining[0].key).toBe(secondItemKey);
  });

  it('shows a loading placeholder while categories are loading and disables the category field', () => {
    render(
      <PurchaseRequestItemsForm
        {...baseProps([createEmptyItem()])}
        categoriesLoading
        categories={[]}
      />
    );
    expect(screen.getByText(/loading categories/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeDisabled();
  });

  it('shows an error and a working retry action when the category API fails', async () => {
    const user = userEvent.setup();
    const onRetryCategories = vi.fn();
    render(
      <PurchaseRequestItemsForm
        {...baseProps([createEmptyItem()])}
        categories={[]}
        categoriesError="Failed to load purchase request categories"
        onRetryCategories={onRetryCategories}
      />
    );

    expect(screen.getByText('Failed to load purchase request categories')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetryCategories).toHaveBeenCalledTimes(1);
  });

  it('handles an empty category response without crashing', () => {
    render(
      <PurchaseRequestItemsForm
        {...baseProps([createEmptyItem()])}
        categories={[]}
        categoriesError={null}
        categoriesLoading={false}
      />
    );

    // No throw, a usable (enabled, empty) selector, and no phantom category.
    const trigger = screen.getByLabelText('Category');
    expect(trigger).toBeInTheDocument();
    expect(trigger).not.toBeDisabled();
  });

  it('surfaces per-field validation errors passed in via props', () => {
    const item = createEmptyItem();
    render(
      <PurchaseRequestItemsForm
        {...baseProps([item])}
        errors={{ [item.key]: { description: 'Description is required' } }}
      />
    );
    expect(screen.getByText('Description is required')).toBeInTheDocument();
  });
});
