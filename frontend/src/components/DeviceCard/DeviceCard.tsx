import { SpecList } from "@/components/SpecList/SpecList";
import { Tags } from "@/components/Tag/Tags";
import type { Device } from "@/lib/types";
import { getContributor, getOverviewSpecs } from "@/lib/utils";
import { useMemo } from "react";
import { Link } from "react-router";
import styles from "./DeviceCard.module.css";

export const DeviceCard = ({ device }: { device: Device }) => {
  const specs = useMemo(() => getOverviewSpecs(device, 3), [device]);
  const contributor = getContributor(device);

  return (
    <Link className={styles.container} to={`/devices/${device.slug}`}>
      <Tags tags={device.deviceConstruction} />
      <div>
        <h3 className={styles.title}>{device.deviceName}</h3>
        {contributor ? (
          <h4 className={styles.subTitle}>{contributor}</h4>
        ) : null}
      </div>
      {device.deviceDescription ? (
        <p className={styles.description}>{device.deviceDescription}</p>
      ) : null}
      <SpecList specs={specs} />
    </Link>
  );
};
