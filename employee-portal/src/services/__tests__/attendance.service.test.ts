import { describe, expect, it, vi, beforeEach } from 'vitest';
import { format } from 'date-fns';

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

import api from '../api';
import { attendanceService } from '../attendance.service';

const IN = '2026-10-13T06:05:00Z';
const OUT = '2026-10-13T14:35:00Z';
const local = (iso: string) => format(new Date(iso), 'HH:mm');

beforeEach(() => {
  vi.clearAllMocks();
});

describe('attendanceService maps the portal API shapes the page reads', () => {
  it('history: a plain list becomes { records }, newest first, cut to page_size', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        { id: 3, date: '2026-10-13', time_in: IN, time_out: null, status: 'Present' },
        { id: 2, date: '2026-10-12', time_in: IN, time_out: OUT, status: 'Present' },
        { id: 1, date: '2026-10-11', time_in: null, time_out: null, status: 'Absent' },
      ],
    });

    const result = await attendanceService.getHistory({ page_size: 2 });

    expect(api.get).toHaveBeenCalledWith('/portal/attendance/history/', {
      params: { from_date: undefined, to_date: undefined },
    });
    expect(result.total_count).toBe(3);
    expect(result.records.map((r) => r.id)).toEqual([3, 2]);
    expect(result.records[0]).toMatchObject({
      date: '2026-10-13',
      clock_in: local(IN),
      clock_out: null,
      status: 'clocked_in',
    });
    expect(result.records[1]).toMatchObject({ clock_out: local(OUT), status: 'complete' });
  });

  it('history: sends the date range under the names the API reads', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });

    const result = await attendanceService.getHistory({
      start_date: '2026-10-01',
      end_date: '2026-10-13',
    });

    expect(api.get).toHaveBeenCalledWith('/portal/attendance/history/', {
      params: { from_date: '2026-10-01', to_date: '2026-10-13' },
    });
    expect(result.records).toEqual([]);
  });

  it('status: not clocked, clocked in and clocked out', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { is_clocked_in: false, clock_in_time: null, clock_out_time: null, worked_hours: null },
    });
    expect(await attendanceService.getStatus()).toMatchObject({
      status: 'not_clocked',
      clock_in: null,
      clock_out: null,
      hours_worked: null,
    });

    vi.mocked(api.get).mockResolvedValueOnce({
      data: { is_clocked_in: true, clock_in_time: IN, clock_out_time: null, worked_hours: null },
    });
    expect(await attendanceService.getStatus()).toMatchObject({
      status: 'clocked_in',
      clock_in: local(IN),
    });

    vi.mocked(api.get).mockResolvedValueOnce({
      data: { is_clocked_in: false, clock_in_time: IN, clock_out_time: OUT, worked_hours: 8.5 },
    });
    expect(await attendanceService.getStatus()).toMatchObject({
      status: 'clocked_out',
      clock_out: local(OUT),
      hours_worked: 8.5,
    });
    expect(api.get).toHaveBeenCalledWith('/portal/attendance/status/');
  });

  it('summary: API counts land on the card fields', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        month: 10,
        year: 2026,
        total_days: 9,
        present_days: 7,
        absent_days: 1,
        leave_days: 1,
        late_days: 2,
        total_hours: 56.5,
      },
    });

    expect(await attendanceService.getSummary()).toMatchObject({
      month: 10,
      year: 2026,
      total_working_days: 9,
      days_present: 7,
      days_absent: 1,
      days_on_leave: 1,
      days_late: 2,
      total_hours_worked: 56.5,
    });
  });
});
