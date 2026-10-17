import styles from "./App.module.css";
import { DeviceGallery } from "./components/DeviceGallery/DeviceGallery";
import { Filters } from "./components/Filters/Filters";
import { Input } from "./components/Input/Input";
import { Intro } from "./components/Intro/Intro";
import { Select } from "./components/Select/Select";
import { TopBar } from "./components/TopBar/TopBar";
import { SORT_OPTIONS } from "./constants";
import { useDeviceFilters } from "./hooks/useDeviceFilters";
import { useDevices } from "./hooks/useDevices";

const App = () => {
  const { devices, isLoading, error } = useDevices();
  const {
    filteredDevices,
    search,
    sections,
    setSearch,
    setSelected,
    setSort,
    sort,
  } = useDeviceFilters(devices);

  return (
    <>
      <div className={styles.smallScreenMessage}>
        <p>Small screen layout is not yet implemented</p>
      </div>
      <div className={styles.app}>
        <TopBar />
        <div className={styles.container}>
          <Intro />
          <div className={styles.main}>
            <Filters onChange={setSelected} sections={sections} />
            <div className={styles.content}>
              <div className={styles.toolbar}>
                <Input
                  className={styles.searchInput}
                  label="Search devices"
                  onChange={setSearch}
                  placeholder="Search devices..."
                  type="search"
                  value={search}
                />
                <Select
                  icon="/images/arrow-down-up.svg"
                  label="Sort devices"
                  onChange={setSort}
                  options={SORT_OPTIONS}
                  value={sort}
                />
              </div>
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
      </div>
    </>
  );
};

export default App;
