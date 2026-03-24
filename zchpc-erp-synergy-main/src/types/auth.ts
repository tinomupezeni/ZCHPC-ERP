export interface LoginFormData {
  email: string;
  password: string;
}

export type UserRole = "ADMIN" | "HUMAN_RESOURCES" | "ACCOUNTANT" | "SALES";

export const ROLE_ROUTES: Record<string, string> = {
  admin: "/dashboard",
  superadmin: "/dashboard",
  human_resources: "/hr",
  accountant: "/accounting",
  sales: "/sales",
};