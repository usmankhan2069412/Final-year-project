import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import { lazy, Suspense } from "react";
import PageLoader from "./components/PageLoader";

// Lazy-loaded pages
const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Builder = lazy(() => import("./pages/Builder"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Settings = lazy(() => import("./pages/Settings"));
const Models = lazy(() => import("./pages/Models"));
const Inbox = lazy(() => import("./pages/Inbox"));
const NotFound = lazy(() => import("./pages/NotFound"));

function Router() {
  return (
    <Switch>
      {/* Public routes */}
      <Route path={"/"}>
        <Suspense fallback={<PageLoader page="public" />}><Home /></Suspense>
      </Route>
      <Route path={"/login"}>
        <Suspense fallback={<PageLoader page="public" />}><Login /></Suspense>
      </Route>
      <Route path={"/signup"}>
        <Suspense fallback={<PageLoader page="public" />}><Signup /></Suspense>
      </Route>
      <Route path={"/forgot-password"}>
        <Suspense fallback={<PageLoader page="public" />}><ForgotPassword /></Suspense>
      </Route>
      <Route path={"/reset-password"}>
        <Suspense fallback={<PageLoader page="public" />}><ResetPassword /></Suspense>
      </Route>

      {/* Protected routes */}
      <Route path={"/dashboard"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="dashboard" />}><Dashboard /></Suspense>
        </ProtectedRoute>
      </Route>
      <Route path={"/inbox"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="inbox" />}><Inbox /></Suspense>
        </ProtectedRoute>
      </Route>
      <Route path={"/builder"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="builder" />}><Builder /></Suspense>
        </ProtectedRoute>
      </Route>
      <Route path={"/analytics"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="analytics" />}><Analytics /></Suspense>
        </ProtectedRoute>
      </Route>
      <Route path={"/settings"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="settings" />}><Settings /></Suspense>
        </ProtectedRoute>
      </Route>
      <Route path={"/models"}>
        <ProtectedRoute>
          <Suspense fallback={<PageLoader page="models" />}><Models /></Suspense>
        </ProtectedRoute>
      </Route>

      <Route path={"/404"}>
        <Suspense fallback={<PageLoader page="public" />}><NotFound /></Suspense>
      </Route>
      {/* Final fallback route */}
      <Route>
        <Suspense fallback={<PageLoader page="public" />}><NotFound /></Suspense>
      </Route>
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ThemeProvider defaultTheme="light" switchable>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </ThemeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
