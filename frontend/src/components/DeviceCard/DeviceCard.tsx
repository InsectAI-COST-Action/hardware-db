import { useMemo } from "react";
import type { Device } from "../../types";
import { Tag } from "../Tag/Tag";
import styles from "./DeviceCard.module.css";

const MAX_LIST_ITEMS = 3;

export const DeviceCard = ({ device }: { device: Device }) => {
  const subTitle = useMemo(() => {
    if (device.contactInstitution?.length) {
      return `By ${device.contactInstitution}`;
    }

    return `Contributed by ${device.contactName}`;
  }, [device]);

  const specs = useMemo(() => {
    const formatList = (items?: string[]) => {
      if (!items?.length) {
        return undefined;
      }

      const shown = items.slice(0, MAX_LIST_ITEMS).join(", ");
      const remaining = items.length - MAX_LIST_ITEMS;

      return remaining > 0 ? `${shown} +${remaining} more` : shown;
    };

    return [
      { label: "Processor", value: device.processingUnit },
      { label: "Power", value: formatList(device.powerSources) },
      { label: "Capture", value: formatList(device.captureModes) },
      { label: "Target taxa", value: formatList(device.taxonomicGroups) },
    ].filter((spec) => spec.value);
  }, [device]);

  return (
    <div className={styles.container}>
      {device.deviceConstruction?.length ? (
        <div className={styles.tags}>
          {device.deviceConstruction.map((type) => (
            <Tag key={type}>{type}</Tag>
          ))}
        </div>
      ) : null}
      <div>
        <h3 className={styles.title}>{device.deviceName}</h3>
        <h4 className={styles.subTitle}>{subTitle}</h4>
      </div>
      {device.deviceDescription ? (
        <p className={styles.description}>{device.deviceDescription}</p>
      ) : null}
      {specs.length ? (
        <dl className={styles.specs}>
          {specs.map(({ label, value }) => (
            <div className={styles.spec} key={label}>
              <dt className={styles.specLabel}>{label}</dt>
              <dd className={styles.specValue}>{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  );
};
