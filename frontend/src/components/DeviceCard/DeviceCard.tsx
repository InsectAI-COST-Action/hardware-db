import { Tag } from "@/components/Tag/Tag";
import type { Device } from "@/lib/types";
import { getContributor, getOverviewSpecs } from "@/lib/utils";
import { useMemo } from "react";
import { Link } from "react-router";
import styles from "./DeviceCard.module.css";

export const DeviceCard = ({ device }: { device: Device }) => {
  const specs = useMemo(() => getOverviewSpecs(device, 3), [device]);

  return (
    <Link className={styles.container} to={`/devices/${device.slug}`}>
      {device.deviceConstruction?.length ? (
        <div className={styles.tags}>
          {device.deviceConstruction.map((type) => (
            <Tag key={type}>{type}</Tag>
          ))}
        </div>
      ) : null}
      <div>
        <h3 className={styles.title}>{device.deviceName}</h3>
        <h4 className={styles.subTitle}>{getContributor(device)}</h4>
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
    </Link>
  );
};
