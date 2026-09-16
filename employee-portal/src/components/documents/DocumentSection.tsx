import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface DocumentSectionProps {
  /** Section heading, e.g. "Requester Details" - rendered as a restrained, labelled divider rather than a card title. */
  title: string;
  children: ReactNode;
  className?: string;
}

/**
 * A labelled section of an official ERP document (F20). Deliberately not a
 * Card - a corporate document reads top-to-bottom as one continuous sheet
 * with labelled sections, not a stack of separate boxes. Reusable beyond
 * Purchase Requests wherever the same "digital form" treatment applies
 * (Leave, Stores, Fuel), though only Purchase Requests adopts it for now.
 */
export function DocumentSection({ title, children, className }: DocumentSectionProps) {
  return (
    <section className={cn('space-y-3', className)}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </h3>
      {children}
    </section>
  );
}

export default DocumentSection;
