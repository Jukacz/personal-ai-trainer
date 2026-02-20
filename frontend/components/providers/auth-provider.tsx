'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api-client';
import { getAccessToken, setAccessToken, removeAccessToken } from '@/lib/auth';
import type { User } from '@/lib/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  loginWithGoogle: (code: string, redirectUri: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const userData = await authApi.getMe();
      setUser(userData);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      removeAccessToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    setAccessToken(response.access_token);
    setUser(response.user);
    router.push('/');
  };

  const register = async (email: string, password: string, name: string) => {
    const response = await authApi.register(email, password, name);
    setAccessToken(response.access_token);
    setUser(response.user);
    router.push('/');
  };

  const loginWithGoogle = async (code: string, redirectUri: string) => {
    const response = await authApi.googleAuth(code, redirectUri);
    setAccessToken(response.access_token);
    setUser(response.user);
    router.push('/');
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      removeAccessToken();
      setUser(null);
      router.push('/login');
    }
  };

  const refreshUser = async () => {
    await fetchUser();
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
