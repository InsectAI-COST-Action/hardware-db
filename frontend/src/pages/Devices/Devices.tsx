import { DeviceGallery } from "@/components/DeviceGallery/DeviceGallery";
import { Filters } from "@/components/Filters/Filters";
import { Input } from "@/components/Input/Input";
import { Intro } from "@/components/Intro/Intro";
import { Select } from "@/components/Select/Select";
import { Switch } from "@/components/Switch/Switch";
import { useAppContext } from "@/hooks/useAppContext";
import { SORT_OPTIONS, VIEW_MODE_OPTIONS } from "@/lib/constants";
import styles from "./Devices.module.css";
import type { Device } from "@/lib/types";

export const Devices = () => {
  const {
    devices,
    error,
    filteredDevices,
    isLoading,
    search,
    sections,
    setSearch,
    setSelected,
    setSort,
    setViewMode,
    sort,
    viewMode,
  } = useAppContext();

  return (
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
            <Switch
              label="View mode"
              onChange={setViewMode}
              options={VIEW_MODE_OPTIONS}
              showLabels
              value={viewMode}
            />
          </div>
          <p className={styles.deviceCount}>
            Showing {filteredDevices.length} of {devices.length} devices
          </p>
          <Content
            devices={filteredDevices}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
};

const Content = ({
  devices,
  isLoading,
  error,
}: {
  devices: Device[];
  isLoading: boolean;
  error: Error | null;
}) => {
  if (isLoading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Uh oh, could not load devices. Try again later.</p>;
  }

  if (devices.length === 0) {
    return <p>No devices match the current filtering.</p>;
  }

  return <DeviceGallery devices={devices} />;
};
