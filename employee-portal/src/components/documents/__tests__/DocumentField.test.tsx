import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentField, DocumentFieldGrid } from '../DocumentField';

describe('DocumentField', () => {
  it('renders the label above the value', () => {
    render(<DocumentField label="Requested By" value="Riley Requester" />);
    expect(screen.getByText('Requested By')).toBeInTheDocument();
    expect(screen.getByText('Riley Requester')).toBeInTheDocument();
  });

  it('accepts a ReactNode value, not just a string', () => {
    render(<DocumentField label="Status" value={<strong>Approved</strong>} />);
    expect(screen.getByText('Approved').tagName).toBe('STRONG');
  });
});

describe('DocumentFieldGrid', () => {
  it('renders every field it wraps', () => {
    render(
      <DocumentFieldGrid>
        <DocumentField label="Requested By" value="Riley Requester" />
        <DocumentField label="Department" value="IT Department" />
      </DocumentFieldGrid>
    );
    expect(screen.getByText('Riley Requester')).toBeInTheDocument();
    expect(screen.getByText('IT Department')).toBeInTheDocument();
  });
});
