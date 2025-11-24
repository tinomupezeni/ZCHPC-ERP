import { apiClient } from './apiClient';
import { User } from '../types'; // Make sure you have a User type
import { toast } from 'sonner'; // 1. Import toast

interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export const getProfile = async (): Promise<User> => {
  const response = await apiClient.get<any>('/auth/users/me/');
  if (Array.isArray(response.data)) {
      return response.data[0];
  }
  return response.data;
};


export const login = async (email: string, password: string): Promise<User> => {
  try {
    const response = await apiClient.post<AuthResponse>('/auth/token/', {
      email: email,
      password: password,
    });

    console.log(response);

    const { access, refresh } = response.data;
    
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
    
    const user = await getProfile();

    // 3. Show a success toast
    toast.success("Login Successful!", {
      description: `Welcome!`,
    });

    // Return user data to the app
    return user;

  } catch (error: any) { 

    // Show an appropriate error toast
    if (error.response && (error.response.status === 401 || error.response.status === 400)) {
      toast.error("Invalid Credentials", {
        description: "Please check your email and password.",
      });
    } else if (error.request) {
      toast.error("Network Error", {
        description: "Could not connect to the server.",
      });
    } else {
      toast.error("Login Failed", {
        description: "An unexpected error occurred. Please try again.",
      });
    }
    
    // Re-throw the error for the component's catch block
    throw error;
  }
};

export const logout = () => {
  // Remove tokens from localStorage
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  
  // Redirect to login page
  window.location.href = '/login';
  location.reload()
};