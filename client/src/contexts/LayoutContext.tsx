import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";

interface LayoutContextValue {
  title: string;
  setTitle: (title: string) => void;
  searchPlaceholder: string;
  setSearchPlaceholder: (placeholder: string) => void;
  actions: ReactNode;
  setActions: (actions: ReactNode) => void;
  hideTopBar: boolean;
  setHideTopBar: (hide: boolean) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
}

const LayoutContext = createContext<LayoutContextValue | null>(null);

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [title, setTitleState] = useState("");
  const [searchPlaceholder, setSearchPlaceholderState] = useState("");
  const [actions, setActionsState] = useState<ReactNode>(null);
  const [hideTopBar, setHideTopBarState] = useState(false);
  const [sidebarOpen, setSidebarOpenState] = useState(false);

  const setTitle = useCallback((t: string) => setTitleState(t), []);
  const setSearchPlaceholder = useCallback((p: string) => setSearchPlaceholderState(p), []);
  const setActions = useCallback((a: ReactNode) => setActionsState(a), []);
  const setHideTopBar = useCallback((h: boolean) => setHideTopBarState(h), []);
  const setSidebarOpen = useCallback((open: boolean | ((prev: boolean) => boolean)) => {
    setSidebarOpenState(open);
  }, []);

  return (
    <LayoutContext.Provider
      value={{
        title,
        setTitle,
        searchPlaceholder,
        setSearchPlaceholder,
        actions,
        setActions,
        hideTopBar,
        setHideTopBar,
        sidebarOpen,
        setSidebarOpen,
      }}
    >
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayout() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error("useLayout must be used within LayoutProvider");
  return ctx;
}

interface LayoutConfigProps {
  title?: string;
  searchPlaceholder?: string;
  actions?: ReactNode;
  hideTopBar?: boolean;
}

export function useLayoutConfig({
  title = "",
  searchPlaceholder = "",
  actions = null,
  hideTopBar = false,
}: LayoutConfigProps) {
  const layout = useLayout();

  useEffect(() => {
    layout.setTitle(title);
    layout.setSearchPlaceholder(searchPlaceholder);
    layout.setActions(actions);
    layout.setHideTopBar(hideTopBar);

    return () => {
      // Reset values when component unmounts to prevent state bleeding
      layout.setTitle("");
      layout.setSearchPlaceholder("");
      layout.setActions(null);
      layout.setHideTopBar(false);
    };
  }, [title, searchPlaceholder, actions, hideTopBar, layout]);
}
