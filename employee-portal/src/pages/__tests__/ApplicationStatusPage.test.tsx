import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ApplicationStatusResponse } from '@/types/jobs.types';

// The public status lookup returns a bare list of applications (REM-04):
// no candidate name, and an unknown ID number gives the same empty list as
// an ID with no applications.
const mockGetApplicationStatus = vi.fn();
vi.mock('@/services/jobs.service', () => ({
  jobsService: {
    getApplicationStatus: (idNumber: string) => mockGetApplicationStatus(idNumber),
  },
}));

const { ApplicationStatusPage } = await import('../ApplicationStatusPage');

async function search(idNumber: string) {
  render(<ApplicationStatusPage />);
  await userEvent.type(screen.getByPlaceholderText('Enter your National ID Number'), idNumber);
  await userEvent.click(screen.getByRole('button', { name: 'Check Status' }));
}

describe('ApplicationStatusPage', () => {
  beforeEach(() => {
    mockGetApplicationStatus.mockReset();
  });

  it('lists the applications returned for an ID number', async () => {
    const response: ApplicationStatusResponse = [
      { job_id: 7, job_title: 'Systems Engineer', status: 'Interview', applied_at: '2026-09-01T10:00:00Z' },
    ];
    mockGetApplicationStatus.mockResolvedValue(response);

    await search('63-111111A11');

    expect(mockGetApplicationStatus).toHaveBeenCalledWith('63-111111A11');
    expect(await screen.findByText('Systems Engineer')).toBeInTheDocument();
    expect(screen.getByText('Interview Stage')).toBeInTheDocument();
    expect(screen.getByText(/Applied on September 1, 2026/)).toBeInTheDocument();
    expect(screen.queryByText('No Applications Found')).not.toBeInTheDocument();
  });

  it('shows the empty state for an empty result', async () => {
    mockGetApplicationStatus.mockResolvedValue([]);

    await search('00-000000Z00');

    expect(await screen.findByText('No Applications Found')).toBeInTheDocument();
  });
});
