import { useMemo, useState } from "react";
import styles from "./App.module.css";
import { DeviceGallery } from "./components/DeviceGallery/DeviceGallery";
import { Intro } from "./components/Intro/Intro";
import { useDevices } from "./hooks/useDevices";

const App = () => {
  const { devices, isLoading, error } = useDevices();
  const [search, setSearch] = useState("");

  const filteredDevices = useMemo(() => {
    const normalizedQuery = search.trim().toLowerCase();

    if (!normalizedQuery) {
      return devices;
    }

    return devices.filter((device) =>
      [device.deviceName].some((field) =>
        field?.toLowerCase().includes(normalizedQuery),
      ),
    );
  }, [devices, search]);

  return (
    <div className={styles.container}>
      <Intro />
      <div className={styles.main}>
        <div className={styles.sidebar}>
          <h4>Filters</h4>
        </div>
        <div className={styles.content}>
          <input
            aria-label="Search devices"
            className={styles.searchInput}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search devices..."
            type="search"
            value={search}
          />
          <p className={styles.deviceCount}>
            Showing {filteredDevices.length} of {devices.length} devices
          </p>
          <DeviceGallery
            devices={filteredDevices}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
