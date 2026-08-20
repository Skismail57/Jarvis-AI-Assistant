import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
          });

          const data = await response.json();

          if (response.ok) {
            set({
              user: data.user,
              token: data.token,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true };
          } else {
            set({
              error: data.message || 'Login failed',
              isLoading: false,
            });
            return { success: false, error: data.message };
          }
        } catch (error) {
          set({
            error: 'Network error. Please try again.',
            isLoading: false,
          });
          return { success: false, error: 'Network error' };
        }
      },

      biometricLogin: async (username) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/biometric', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username }),
          });

          const data = await response.json();

          if (response.ok) {
            set({
              user: data.user,
              token: data.token,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true };
          } else {
            set({
              error: data.message || 'Biometric authentication failed',
              isLoading: false,
            });
            return { success: false, error: data.message };
          }
        } catch (error) {
          set({
            error: 'Biometric authentication error. Please try again.',
            isLoading: false,
          });
          return { success: false, error: 'Network error' };
        }
      },

      signup: async (username, password, email) => {
        set({ isLoading: true, error: null });
        try {
          const response = await fetch('/api/auth/signup', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password, email }),
          });

          const data = await response.json();

          if (response.ok) {
            set({
              user: data.user,
              token: data.token,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            localStorage.setItem('authToken', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            return { success: true };
          } else {
            set({
              error: data.message || 'Signup failed',
              isLoading: false,
            });
            return { success: false, error: data.message };
          }
        } catch (error) {
          set({
            error: 'Network error. Please try again.',
            isLoading: false,
          });
          return { success: false, error: 'Network error' };
        }
      },

      logout: async () => {
        set({ isLoading: true, error: null });
        try {
          const token = get().token;
          await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
          });

          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          return { success: true };
        } catch (error) {
          // Even if logout API fails, clear local state
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          return { success: true };
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('authToken');
        const user = JSON.parse(localStorage.getItem('user') || 'null');

        if (token && user) {
          try {
            const response = await fetch('/api/auth/verify', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            });

            if (response.ok) {
              set({
                user: user,
                token: token,
                isAuthenticated: true,
                isLoading: false,
              });
              return true;
            } else {
              // Token invalid, clear local storage
              localStorage.removeItem('authToken');
              localStorage.removeItem('user');
              set({
                user: null,
                token: null,
                isAuthenticated: false,
                isLoading: false,
              });
              return false;
            }
          } catch (error) {
            // Network error, but we have local token
            set({
              user: user,
              token: token,
              isAuthenticated: true,
              isLoading: false,
            });
            return true;
          }
        }

        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
        return false;
      },

      updateUser: (userData) => {
        const currentUser = get().user;
        set({
          user: { ...currentUser, ...userData },
        });
        localStorage.setItem('user', JSON.stringify({ ...currentUser, ...userData }));
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
