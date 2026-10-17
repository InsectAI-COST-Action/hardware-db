import { DeviceCard } from "@/components/DeviceCard/DeviceCard";
import type { Device } from "@/lib/types";
import styles from "./DeviceGallery.module.css";

export const DeviceGallery = ({
  devices,
  isLoading,
  error,
}: {
  devices: Device[];
  isLoading: boolean;
  error: Error | null;
}) => {
  if (isLoading) {
    return <p>Loading devices...</p>;
  }

  if (error) {
    return <p>Uh oh, could not load devices. Try again later.</p>;
  }

  if (devices.length === 0) {
    return <p>No devices match the current filtering.</p>;
  }

  return (
    <div className={styles.container}>
      {devices.map((device, index) => (
        <DeviceCard key={device.deviceName ?? index} device={device} />
      ))}
    </div>
  );
};
