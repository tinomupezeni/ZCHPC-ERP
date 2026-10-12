import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ComingSoonTag } from '../ComingSoonTag';

/** Dashboard tiles that link to a page this version leaves out say so. */
describe('ComingSoonTag', () => {
  it.each(['/portal/payroll', '/portal/expenses', '/portal/payslips', '/portal/leave'])(
    'marks a tile linking to %s',
    (href) => {
      render(<ComingSoonTag href={href} />);
      expect(screen.getByText('Coming soon')).toBeTruthy();
    }
  );

  it.each(['/portal/purchase-requests', '/portal/purchase-requests/procurement'])(
    'leaves a tile linking to %s alone',
    (href) => {
      const { container } = render(<ComingSoonTag href={href} />);
      expect(container.textContent).toBe('');
    }
  );
});
