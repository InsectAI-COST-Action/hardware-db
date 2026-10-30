import { Button } from "@/components/Button/Button";
import { DeviceComparison } from "@/components/DeviceComparison/DeviceComparison";
import { DeviceGallery } from "@/components/DeviceGallery/DeviceGallery";
import { DeviceTable } from "@/components/DeviceTable/DeviceTable";
import { Filters } from "@/components/Filters/Filters";
import { Input } from "@/components/Input/Input";
import { Intro } from "@/components/Intro/Intro";
import { Select } from "@/components/Select/Select";
import { Sheet } from "@/components/Sheet/Sheet";
import { Switch } from "@/components/Switch/Switch";
import { useAppContext } from "@/hooks/useAppContext";
import { SORT_OPTIONS, VIEW_MODE_OPTIONS } from "@/lib/constants";
import { ArrowDownUp, Scale } from "lucide-react";
import { useState } from "react";
import styles from "./Devices.module.css";
import type { Device, ViewMode } from "@/lib/types";

export const Devices = () => {
  const {
    devices,
    error,
    filteredDevices,
    isLoading,
    search,
    sections,
    selectedDevices,
    setSearch,
    setSelected,
    setSelectedDevices,
    setSort,
    setViewMode,
    sort,
    viewMode,
  } = useAppContext();
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const comparedDevices = devices.filter((device) =>
    selectedDevices.includes(device.slug),
  );
  const showSelectionBar = selectedDevices.length > 0;

  return (
    <div className={styles.container}>
      <Intro />
      <div className={styles.main}>
        <Filters onChange={setSelected} sections={sections} />
        <div
          className={`${styles.content} ${showSelectionBar ? styles.withSelectionBar : ""}`}
        >
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
              icon={ArrowDownUp}
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
            onSelectedChange={setSelectedDevices}
            selected={selectedDevices}
            viewMode={viewMode}
          />
        </div>
      </div>
      {showSelectionBar ? (
        <div
          className={styles.selectionBar}
          role="region"
          aria-label="Selection"
        >
          <p className={styles.selectionCount}>
            {selectedDevices.length} selected
          </p>
          <Button
            disabled={selectedDevices.length < 2}
            icon={Scale}
            onClick={() => setIsCompareOpen(true)}
          >
            Compare
          </Button>
          <Button onClick={() => setSelectedDevices([])} variant="ghost">
            Clear
          </Button>
        </div>
      ) : null}
      <Sheet
        onClose={() => setIsCompareOpen(false)}
        open={isCompareOpen}
        title="Compare devices"
      >
        <DeviceComparison devices={comparedDevices} />
      </Sheet>
    </div>
  );
};

const Content = ({
  devices,
  isLoading,
  error,
  onSelectedChange,
  selected,
  viewMode,
}: {
  devices: Device[];
  isLoading: boolean;
  error: Error | null;
  onSelectedChange: (slugs: string[]) => void;
  selected: string[];
  viewMode: ViewMode;
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

  if (viewMode === "table") {
    return (
      <DeviceTable
        devices={devices}
        onSelectedChange={onSelectedChange}
        selected={selected}
      />
    );
  }

  return (
    <DeviceGallery
      devices={devices}
      onSelectedChange={onSelectedChange}
      selected={selected}
    />
  );
};
