import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import { lazy, Suspense } from "react";
import PageLoader from "./components/PageLoader";
import { LayoutProvider } from "./contexts/LayoutContext";
import DashboardLayout from "./components/DashboardLayout";

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

function ProtectedRoutes() {
  return (
    <ProtectedRoute>
      <LayoutProvider>
        <DashboardLayout>
          <Switch>
            <Route path="/dashboard">
              <Suspense fallback={<PageLoader page="dashboard" contentOnly />}><Dashboard /></Suspense>
            </Route>
            <Route path="/inbox">
              <Suspense fallback={<PageLoader page="inbox" contentOnly />}><Inbox /></Suspense>
            </Route>
            <Route path="/builder">
              <Suspense fallback={<PageLoader page="builder" contentOnly />}><Builder /></Suspense>
            </Route>
            <Route path="/analytics">
              <Suspense fallback={<PageLoader page="analytics" contentOnly />}><Analytics /></Suspense>
            </Route>
            <Route path="/settings">
              <Suspense fallback={<PageLoader page="settings" contentOnly />}><Settings /></Suspense>
            </Route>
            <Route path="/models">
              <Suspense fallback={<PageLoader page="models" contentOnly />}><Models /></Suspense>
            </Route>
            {/* Fallback inside Layout */}
            <Route>
              <Suspense fallback={<PageLoader page="public" />}><NotFound /></Suspense>
            </Route>
          </Switch>
        </DashboardLayout>
      </LayoutProvider>
    </ProtectedRoute>
  );
}

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

      {/* Protected routes wrapped in common component for mounting persistence */}
      <Route path="/dashboard" component={ProtectedRoutes} />
      <Route path="/inbox" component={ProtectedRoutes} />
      <Route path="/builder" component={ProtectedRoutes} />
      <Route path="/analytics" component={ProtectedRoutes} />
      <Route path="/settings" component={ProtectedRoutes} />
      <Route path="/models" component={ProtectedRoutes} />

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
