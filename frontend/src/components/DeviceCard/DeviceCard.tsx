import { useMemo } from "react";
import type { Device } from "../../types/device";
import styles from "./DeviceCard.module.css";

export const DeviceCard = ({ device }: { device: Device }) => {
  const subTitle = useMemo(() => {
    if (device.contactInstitution?.length) {
      return `By ${device.contactInstitution}`;
    }

    return `Contributed by ${device.contactName}`;
  }, [device]);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>{device.deviceName}</h3>
      <h4 className={styles.subTitle}>{subTitle}</h4>
      {device.deviceDescription ? (
        <p className={styles.description}>{device.deviceDescription}</p>
      ) : null}
    </div>
  );
};
