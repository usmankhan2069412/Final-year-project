import { useEffect } from "react";
import { useLocation } from "wouter";
import { useAuth } from "../contexts/AuthContext";

/**
 * Wraps a protected page. Redirects unauthenticated users to /login.
 */
export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!isAuthenticated) {
      setLocation("/login");
    }
  }, [isAuthenticated, setLocation]);

  // Render nothing while redirecting
  if (!isAuthenticated) return null;

  return <>{children}</>;
}
