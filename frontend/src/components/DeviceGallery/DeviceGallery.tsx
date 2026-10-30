import { DeviceCard } from "@/components/DeviceCard/DeviceCard";
import type { Device } from "@/lib/types";
import styles from "./DeviceGallery.module.css";

interface DeviceGalleryProps {
  devices: Device[];
  onSelectedChange: (slugs: string[]) => void;
  selected: string[];
}

export const DeviceGallery = ({
  devices,
  onSelectedChange,
  selected,
}: DeviceGalleryProps) => {
  const toggle = (slug: string) => {
    onSelectedChange(
      selected.includes(slug)
        ? selected.filter((item) => item !== slug)
        : [...selected, slug],
    );
  };

  return (
    <div className={styles.container}>
      {devices.map((device) => (
        <DeviceCard
          device={device}
          isSelected={selected.includes(device.slug)}
          isSelectionMode={selected.length > 0}
          key={device.slug}
          onToggle={() => toggle(device.slug)}
        />
      ))}
    </div>
  );
};
