// api/procurementApi.ts
import axios from "axios";
import { API_BASE_URL } from "@/server/api";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/procurement`, // point to your backend
});

export const fetchDashboardData = () => api.get("/dashboard");
export const fetchPurchaseOrders = () => api.get("/purchase-orders");
export const fetchSuppliers = () => api.get("/suppliers");
export const fetchPurchaseRequests = () => api.get("/purchase-requests");
export const fetchBudgetCenters = () => api.get("/budget-centers");
export const fetchReports = (type: string) => api.get(`/reports?type=${type}`);
export const fetchDeliveries = () => api.get("/deliveries");

// Post actions
export const createPurchaseOrder = (data: any) => api.post("/purchase-orders", data);
export const createSupplier = (data: any) => api.post("/suppliers", data);
export const approvePurchaseRequest = (id: number, level: number) => api.post(`/purchase-requests/${id}/approve`, { level });
export const rejectPurchaseRequest = (id: number) => api.post(`/purchase-requests/${id}/reject`);
