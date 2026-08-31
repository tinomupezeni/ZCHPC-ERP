export const MIN_EMPLOYEE_AGE = 18;

/** Latest allowed date of birth (as an <input type="date"> value) for someone to be at least minAge. */
export function maxDateOfBirth(minAge: number = MIN_EMPLOYEE_AGE): string {
  const d = new Date();
  d.setFullYear(d.getFullYear() - minAge);
  return d.toISOString().split("T")[0];
}

/** Mirrors the backend's validate_age_18_plus rule (erp_project hr employee_serializers.py). */
export function isAtLeastAge(dateOfBirth: string, minAge: number = MIN_EMPLOYEE_AGE): boolean {
  if (!dateOfBirth) return true;

  const dob = new Date(dateOfBirth);
  if (isNaN(dob.getTime())) return true;

  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDiff = today.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
    age--;
  }
  return age >= minAge;
}
