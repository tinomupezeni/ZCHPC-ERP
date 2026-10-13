export const ATTENDANCE_TIME_ZONE = "Africa/Harare";

const harareClock = new Intl.DateTimeFormat("en-GB", {
  timeZone: ATTENDANCE_TIME_ZONE,
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/**
 * Attendance times come from the API as UTC wall time ("06:20:00") on the record's date
 * (the backend stores UTC). Show them as Harare time ("08:20"), as the employee portal does.
 * Anything that is not an HH:MM[:SS] time is returned unchanged.
 */
export function attendanceTimeInHarare(recordDate: string | null | undefined, utcTime: string | null | undefined): string | null {
  if (!utcTime) return null;
  const m = String(utcTime).match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?/);
  if (!recordDate || !m) return utcTime;
  const instant = new Date(`${recordDate}T${m[1].padStart(2, "0")}:${m[2]}:${m[3] ?? "00"}Z`);
  if (isNaN(instant.getTime())) return utcTime;
  return harareClock.format(instant);
}
