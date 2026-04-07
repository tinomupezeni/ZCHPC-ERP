import { useAuth } from '@/contexts/AuthContext';

export type RoleName =
  | 'ADMIN'
  | 'SYSTEM_ADMINISTRATOR'
  | 'HUMAN_RESOURCES'
  | 'ACCOUNTANT'
  | 'PROCUREMENT_OFFICER'
  | 'SALES_REPRESENTATIVE'
  | 'DEPARTMENT_MANAGER'
  | 'REGULAR_STAFF'
  | 'INTERN';

export type RoleGroup = 'admin' | 'hr' | 'manager' | 'accountant' | 'procurement' | 'staff';

function toRoleName(raw: string | null | undefined): RoleName {
  return (raw?.toUpperCase() ?? 'REGULAR_STAFF') as RoleName;
}

export function getRoleGroup(roleName: RoleName): RoleGroup {
  switch (roleName) {
    case 'ADMIN':
    case 'SYSTEM_ADMINISTRATOR':
      return 'admin';
    case 'HUMAN_RESOURCES':
      return 'hr';
    case 'DEPARTMENT_MANAGER':
      return 'manager';
    case 'ACCOUNTANT':
      return 'accountant';
    case 'PROCUREMENT_OFFICER':
      return 'procurement';
    default:
      return 'staff';
  }
}

export function useRole() {
  const { employee } = useAuth();
  const roleName = toRoleName(employee?.role_name);
  const roleGroup = getRoleGroup(roleName);

  return {
    roleName,
    roleGroup,
    roleDisplayName: employee?.role_display_name ?? 'Employee',
    isAdmin: roleGroup === 'admin',
    isHR: roleGroup === 'hr',
    isManager: roleGroup === 'manager',
    isAccountant: roleGroup === 'accountant',
    isProcurement: roleGroup === 'procurement',
    isStaff: roleGroup === 'staff',
    hasRole: (...roles: RoleName[]) => roles.includes(roleName),
    hasGroup: (...groups: RoleGroup[]) => groups.includes(roleGroup),
  };
}
