import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import ProtectedRoute from "./components/ProtectedRoute";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AuthProvider } from "./contexts/AuthContext";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import Builder from "./pages/Builder";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import Models from "./pages/Models";

function Router() {
  return (
    <Switch>
      {/* Public routes */}
      <Route path={"/"} component={Home} />
      <Route path={"/login"} component={Login} />
      <Route path={"/signup"} component={Signup} />
      <Route path={"/forgot-password"} component={ForgotPassword} />
      <Route path={"/reset-password"} component={ResetPassword} />

      {/* Protected routes */}
      <Route path={"/dashboard"}>
        <ProtectedRoute><Dashboard /></ProtectedRoute>
      </Route>
      <Route path={"/builder"}>
        <ProtectedRoute><Builder /></ProtectedRoute>
      </Route>
      <Route path={"/analytics"}>
        <ProtectedRoute><Analytics /></ProtectedRoute>
      </Route>
      <Route path={"/settings"}>
        <ProtectedRoute><Settings /></ProtectedRoute>
      </Route>
      <Route path={"/models"}>
        <ProtectedRoute><Models /></ProtectedRoute>
      </Route>

      <Route path={"/404"} component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
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
