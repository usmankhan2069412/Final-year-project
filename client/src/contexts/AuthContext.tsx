import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from "react";
import { apiRequest } from "../lib/api";
import { toast } from "sonner";

export interface UserResponse {
  id: string;
  email: string;
  full_name?: string | null;
  auth_provider: string;
}

export interface OrgResponse {
  id: string;
  slug: string;
  owner_id: string;
}

export interface UserMeResponse {
  user: UserResponse;
  active_organization: OrgResponse;
}

interface AuthContextValue {
  isAuthenticated: boolean;
  userMe: UserMeResponse | null;
  isLoadingProfile: boolean;
  login: (token: string) => void;
  logout: () => void;
  fetchProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(localStorage.getItem("token"));
  });

  const [userMe, setUserMe] = useState<UserMeResponse | null>(() => {
    const cached = localStorage.getItem("aina-user-me");
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch (e) {
        console.error("Error parsing cached user profile:", e);
      }
    }
    return null;
  });

  const [isLoadingProfile, setIsLoadingProfile] = useState<boolean>(() => {
    return Boolean(localStorage.getItem("token")) && !localStorage.getItem("aina-user-me");
  });

  const fetchProfile = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setIsLoadingProfile(false);
      return;
    }

    try {
      const data = await apiRequest<UserMeResponse>("/api/v1/users/me");
      setUserMe(data);
      localStorage.setItem("aina-user-me", JSON.stringify(data));
    } catch (err) {
      console.error("Error loading user profile in AuthProvider:", err);
    } finally {
      setIsLoadingProfile(false);
    }
  }, []);

  const login = useCallback((token: string) => {
    localStorage.setItem("token", token);
    setIsAuthenticated(true);
    setIsLoadingProfile(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("aina-user-me");
    setIsAuthenticated(false);
    setUserMe(null);
    toast.success("Successfully logged out");
  }, []);

  // Fetch profile when authenticated or when login happens
  useEffect(() => {
    if (isAuthenticated) {
      fetchProfile();
    }
  }, [isAuthenticated, fetchProfile]);

  // Listen to profile updates (e.g. from ProfileTab updates)
  useEffect(() => {
    const handleProfileUpdate = () => {
      fetchProfile();
    };

    window.addEventListener("profile-updated", handleProfileUpdate);
    return () => {
      window.removeEventListener("profile-updated", handleProfileUpdate);
    };
  }, [fetchProfile]);

  // Listen to unauthorized events to automatically log out the user
  useEffect(() => {
    const handleUnauthorized = () => {
      logout();
    };

    window.addEventListener("unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("unauthorized", handleUnauthorized);
    };
  }, [logout]);

  return (
    <AuthContext.Provider value={{ isAuthenticated, userMe, isLoadingProfile, login, logout, fetchProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
