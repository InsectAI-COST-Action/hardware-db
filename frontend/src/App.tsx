import { useState } from "react";
import { Outlet, ScrollRestoration } from "react-router";
import styles from "./App.module.css";
import { TopBar } from "./components/TopBar/TopBar";
import type { AppContext } from "./hooks/useAppContext";
import { useDeviceFilters } from "./hooks/useDeviceFilters";
import { useDevices } from "./hooks/useDevices";
import type { ViewMode } from "./lib/types";

const App = () => {
  const [viewMode, setViewMode] = useState<ViewMode>("gallery");
  const devicesState = useDevices();
  const filtersState = useDeviceFilters(devicesState.devices);
  const context: AppContext = {
    ...devicesState,
    ...filtersState,
    setViewMode,
    viewMode,
  };

  return (
    <>
      <div className={styles.smallScreenMessage}>
        <p>Small screen layout is not yet implemented</p>
      </div>
      <div className={styles.app}>
        <TopBar />
        <Outlet context={context} />
      </div>
      <ScrollRestoration />
    </>
  );
};

export default App;
