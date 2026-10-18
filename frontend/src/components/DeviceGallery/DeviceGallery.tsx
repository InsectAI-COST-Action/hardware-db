import { DeviceCard } from "@/components/DeviceCard/DeviceCard";
import type { Device } from "@/lib/types";
import styles from "./DeviceGallery.module.css";

export const DeviceGallery = ({ devices }: { devices: Device[] }) => (
  <div className={styles.container}>
    {devices.map((device) => (
      <DeviceCard key={device.slug} device={device} />
    ))}
  </div>
);
