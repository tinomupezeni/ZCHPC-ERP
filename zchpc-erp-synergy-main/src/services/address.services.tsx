// src/services/addressService.ts
import axios from "axios";
import { API_BASE_URL } from "./api";
import { Address } from "../types"; // Assuming you have a types file

// 1. Fixed the endpoint to match your Django urls.py
const ENDPOINT = '/api/hr/addresses/';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Removed the unused mockAddresses array

export const getAddresses = async (): Promise<Address[]> => {
  // This now correctly points to GET /api/addresses/
  const response = await apiClient.get(ENDPOINT);
  return response.data;
};

export const createAddress = async (addressData: Omit<Address, 'id'>): Promise<Address> => {
  // This now correctly points to POST /api/addresses/
  const response = await apiClient.post(ENDPOINT, addressData);
  return response.data;
};

export const updateAddress = async (addressData: Address): Promise<Address> => {
  // 2. Fixed this to use the ENDPOINT constant for consistency
  // This now correctly points to PUT /api/addresses/{id}/
  const response = await apiClient.put(`${ENDPOINT}${addressData.id}/`, addressData);
  return response.data;
};

export const deleteAddress = async (addressId: number | string): Promise<void> => {
  // 3. Fixed this to use the ENDPOINT constant
  // This now correctly points to DELETE /api/addresses/{id}/
  await apiClient.delete(`${ENDPOINT}${addressId}/`);
};