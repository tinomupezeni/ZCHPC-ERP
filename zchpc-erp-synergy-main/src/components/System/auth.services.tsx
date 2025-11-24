import { apiClient } from "@/server/apiClient";

export const addUser = (payload) => {
  return apiClient.post("/auth/users/", payload);
};

export const getUsers = () => {
    return apiClient.get("/auth/users/")
}


