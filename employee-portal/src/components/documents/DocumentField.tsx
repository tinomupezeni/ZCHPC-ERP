import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface DocumentFieldProps {
  label: string;
  value: ReactNode;
  className?: string;
}

/**
 * One labelled field of a document section (F20) - label above value, the
 * same "structured document information" pattern real corporate forms use
 * for particulars (Requested By, Department, etc.), replacing the ad hoc
 * `<p className="text-muted-foreground">label</p><p>{value}</p>` pairs each
 * section used to hand-roll. Reusable anywhere a document needs this pair.
 */
export function DocumentField({ label, value, className }: DocumentFieldProps) {
  return (
    <div className={cn('min-w-0', className)}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium truncate" title={typeof value === 'string' ? value : undefined}>
        {value}
      </p>
    </div>
  );
}

/** A responsive grid of DocumentFields - the common layout every section here uses. */
export function DocumentFieldGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('grid grid-cols-2 sm:grid-cols-4 gap-4', className)}>{children}</div>
  );
}

export default DocumentField;
