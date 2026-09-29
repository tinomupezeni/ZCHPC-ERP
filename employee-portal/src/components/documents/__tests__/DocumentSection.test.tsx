import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentSection } from '../DocumentSection';

describe('DocumentSection', () => {
  it('renders the title as a labelled heading and its children', () => {
    render(
      <DocumentSection title="Requester Details">
        <p>Riley Requester</p>
      </DocumentSection>
    );
    expect(screen.getByText('Requester Details')).toBeInTheDocument();
    expect(screen.getByText('Riley Requester')).toBeInTheDocument();
  });

  it('renders the title inside a <section> element for structural grouping', () => {
    render(
      <DocumentSection title="Financial Information">
        <p>content</p>
      </DocumentSection>
    );
    expect(screen.getByText('Financial Information').closest('section')).toBeInTheDocument();
  });
});
