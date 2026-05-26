import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { toast } from "sonner";
import { useAuth } from "./AuthContext";

export interface NotificationItem {
  id: string;
  user_id: string;
  title: string;
  details: string;
  read: boolean;
  created_at: string; // ISO String
}

interface NotificationContextValue {
  notifications: NotificationItem[];
  unreadCount: number;
  isLoading: boolean;
  fetchNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  dismissNotification: (id: string) => Promise<void>;
  clearAllNotifications: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch("http://localhost:8000/api/v1/notifications", {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const data: NotificationItem[] = await res.json();
        
        // Compare with current state to trigger toast notifications for new unread entries
        setNotifications((prev) => {
          // If we had notifications, check if there are new unread ones
          if (prev.length > 0) {
            const prevIds = new Set(prev.map((n) => n.id));
            const newUnread = data.filter((n) => !n.read && !prevIds.has(n.id));
            
            newUnread.forEach((notif) => {
              toast.info(notif.title, {
                description: notif.details,
              });
            });
          }
          return data;
        });
      }
    } catch (e) {
      console.error("Error fetching notifications from DB:", e);
    }
  }, [isAuthenticated]);

  // Load notifications on mount / auth change and setup WebSocket
  useEffect(() => {
    if (isAuthenticated) {
      setIsLoading(true);
      fetchNotifications().finally(() => setIsLoading(false));

      // Setup WebSocket connection for real-time notifications
      const token = localStorage.getItem("token");
      let ws: WebSocket | null = null;
      
      if (token) {
        ws = new WebSocket(`ws://localhost:8000/api/v1/notifications/ws?token=${token}`);
        
        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            
            // Intercept custom events that are not standard user notifications
            if (parsed.type === "knowledge_update") {
              window.dispatchEvent(new CustomEvent("knowledge_update", { detail: { chatbotId: parsed.chatbot_id } }));
              return;
            }

            const data = parsed as NotificationItem;
            setNotifications((prev) => {
              // Ensure we don't duplicate if already fetched
              if (!prev.find((n) => n.id === data.id)) {
                // Show toast for new live notification
                toast.info(data.title, {
                  description: data.details,
                });
                return [data, ...prev];
              }
              return prev;
            });
          } catch (e) {
            console.error("Error parsing websocket message:", e);
          }
        };

        ws.onerror = (error) => {
          console.error("Notification WebSocket error:", error);
        };
      }

      return () => {
        if (ws) {
          ws.close();
        }
      };
    } else {
      setNotifications([]);
    }
  }, [isAuthenticated, fetchNotifications]);

  // Listen to legacy window custom events for backward compatibility
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleNewNotif = async (e: Event) => {
      const customEvent = e as CustomEvent<{ title: string; details: string }>;
      if (customEvent.detail) {
        const { title, details } = customEvent.detail;
        const token = localStorage.getItem("token");
        if (!token) return;

        try {
          // Transparently forward legacy frontend custom events to the database
          const res = await fetch("http://localhost:8000/api/v1/notifications", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`,
            },
            body: JSON.stringify({ title, details }),
          });
          if (res.ok) {
            fetchNotifications();
          }
        } catch (err) {
          console.error("Error upgrading custom event notification to database:", err);
        }
      }
    };

    window.addEventListener("new-notification", handleNewNotif);
    return () => {
      window.removeEventListener("new-notification", handleNewNotif);
    };
  }, [isAuthenticated, fetchNotifications]);

  const markAsRead = useCallback(async (id: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/notifications/${id}/read`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const updated = await res.json();
        setNotifications((prev) => prev.map((n) => (n.id === id ? updated : n)));
      }
    } catch (e) {
      console.error("Error marking notification as read:", e);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/notifications/read-all`, {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (res.ok) {
        const updatedList = await res.json();
        setNotifications(updatedList);
      }
    } catch (e) {
      console.error("Error marking all notifications as read:", e);
    }
  }, []);

  const dismissNotification = useCallback(async (id: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/notifications/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (res.ok) {
        setNotifications((prev) => prev.filter((n) => n.id !== id));
      }
    } catch (e) {
      console.error("Error dismissing notification:", e);
    }
  }, []);

  const clearAllNotifications = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const res = await fetch(`http://localhost:8000/api/v1/notifications`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });
      if (res.ok) {
        setNotifications([]);
      }
    } catch (e) {
      console.error("Error clearing notifications:", e);
    }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        isLoading,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        dismissNotification,
        clearAllNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error("useNotifications must be used within NotificationProvider");
  }
  return context;
}
