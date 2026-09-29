import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';

/**
 * Test-only stand-in for '@/components/ui/select'.
 *
 * The real component is Radix's Select: its popup is portal-rendered and
 * only mounts once opened via a live pointer-event sequence, which jsdom
 * cannot simulate reliably (a documented Radix/jsdom incompatibility -
 * userEvent.click() on the trigger hangs rather than opening it). This
 * flattens the same Select/SelectTrigger/SelectContent/SelectItem
 * composition into one native <select>, built by reading the (unrendered)
 * child element descriptors, so tests can drive it with
 * userEvent.selectOptions() like any other form control.
 */

interface Marked {
  __marker: 'trigger' | 'content' | 'item';
}

function marker(node: ReactNode): Marked['__marker'] | undefined {
  if (!isValidElement(node)) return undefined;
  const type = node.type as unknown as Partial<Marked>;
  return type.__marker;
}

function findTriggerId(children: ReactNode): string | undefined {
  for (const child of Children.toArray(children)) {
    if (marker(child) === 'trigger') {
      return (child as ReactElement<{ id?: string }>).props.id;
    }
  }
  return undefined;
}

function collectOptions(children: ReactNode): { value: string; label: ReactNode }[] {
  const options: { value: string; label: ReactNode }[] = [];
  for (const child of Children.toArray(children)) {
    const kind = marker(child);
    if (kind === 'content') {
      const el = child as ReactElement<{ children?: ReactNode }>;
      options.push(...collectOptions(el.props.children));
    } else if (kind === 'item') {
      const el = child as ReactElement<{ value: string; children?: ReactNode }>;
      options.push({ value: el.props.value, label: el.props.children });
    }
  }
  return options;
}

export function Select({
  value,
  onValueChange,
  disabled,
  children,
}: {
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
  children?: ReactNode;
}) {
  return (
    <select
      id={findTriggerId(children)}
      disabled={disabled}
      value={value ?? ''}
      onChange={(e) => onValueChange?.(e.target.value)}
    >
      <option value="" disabled hidden />
      {collectOptions(children).map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function SelectTrigger({ children }: { id?: string; children?: ReactNode }) {
  return <>{children}</>;
}
(SelectTrigger as unknown as Marked).__marker = 'trigger';

export function SelectContent({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}
(SelectContent as unknown as Marked).__marker = 'content';

export function SelectItem({ children }: { value: string; children?: ReactNode }) {
  return <>{children}</>;
}
(SelectItem as unknown as Marked).__marker = 'item';

export function SelectValue() {
  return null;
}
