import styles from "./App.module.css";
import { DeviceGallery } from "./components/DeviceGallery/DeviceGallery";
import { Filters } from "./components/Filters/Filters";
import { Intro } from "./components/Intro/Intro";
import { useDeviceFilters } from "./hooks/useDeviceFilters";
import { useDevices } from "./hooks/useDevices";

const App = () => {
  const { devices, isLoading, error } = useDevices();
  const { search, setSearch, filteredDevices, sections, setSelected } =
    useDeviceFilters(devices);

  return (
    <div className={styles.container}>
      <Intro />
      <div className={styles.main}>
        <Filters onChange={setSelected} sections={sections} />
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
