import axios from 'axios';
import { API_BASE_URL } from './api'; // Your existing base URL
import { logout } from './auth.services'; // Import logout to use on failure

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});


apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


apiClient.interceptors.response.use(
  (response) => {
    // If the request was successful, just return the response
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Check if the error is 401 (Unauthorized) and it's not a retry
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Mark this request as retried
      
      const refreshToken = localStorage.getItem('refreshToken');

      if (refreshToken) {
        try {
          // Attempt to refresh the token
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const newAccessToken = response.data.access;
          
          // Update the token in localStorage
          localStorage.setItem('accessToken', newAccessToken);
          
          // Update the authorization header for the original request
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
          
          // Resend the original request with the new token
          return apiClient(originalRequest);
          
        } catch (refreshError) {
          // If the refresh token is also invalid, log the user out
          console.error("Refresh token failed", refreshError);
          logout();
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token found, log out
        console.error("No refresh token available");
        logout();
        return Promise.reject(error);
      }
    }

    // For all other errors, just pass them along
    return Promise.reject(error);
  }
);

export { apiClient };