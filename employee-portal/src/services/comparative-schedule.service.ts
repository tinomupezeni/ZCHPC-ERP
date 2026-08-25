import api from './api';
import type { ComparativeSchedule, CreateComparativeScheduleData } from '@/types/comparative-schedule.types';

export const comparativeScheduleService = {
  async getSchedules(): Promise<ComparativeSchedule[]> {
    const response = await api.get<ComparativeSchedule[]>('/portal/comparative-schedules/');
    return response.data;
  },
  async createSchedule(data: CreateComparativeScheduleData): Promise<ComparativeSchedule> {
    const response = await api.post<ComparativeSchedule>('/portal/comparative-schedules/', data);
    return response.data;
  },
};
export default comparativeScheduleService;
