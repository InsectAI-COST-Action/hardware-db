import { Checkbox } from "@/components/Checkbox/Checkbox";
import { SpecList } from "@/components/SpecList/SpecList";
import { Tags } from "@/components/Tag/Tags";
import type { Device } from "@/lib/types";
import {
  getContributor,
  getOverviewSpecs,
  handleSelectableClick,
} from "@/lib/utils";
import { useMemo } from "react";
import { Link } from "react-router";
import styles from "./DeviceCard.module.css";

interface DeviceCardProps {
  device: Device;
  isSelected: boolean;
  /** When true, clicking the card toggles selection instead of navigating. */
  isSelectionMode: boolean;
  onToggle: () => void;
}

export const DeviceCard = ({
  device,
  isSelected,
  isSelectionMode,
  onToggle,
}: DeviceCardProps) => {
  const specs = useMemo(() => getOverviewSpecs(device, 3), [device]);
  const contributor = getContributor(device);

  return (
    <article
      className={`${styles.container} ${isSelected ? styles.selected : ""} ${isSelectionMode ? styles.selectionMode : ""}`}
    >
      <div className={styles.header}>
        <Tags tags={device.deviceConstruction} />
        <Checkbox
          checked={isSelected}
          className={styles.checkbox}
          label={`Select ${device.deviceName}`}
          onChange={onToggle}
          size="large"
        />
      </div>
      <div>
        <h3 className={styles.title}>
          {/* Stretched over the whole card so it stays clickable */}
          <Link
            className={styles.link}
            onClick={(e) => handleSelectableClick(e, isSelectionMode, onToggle)}
            to={`/devices/${device.slug}`}
          >
            {device.deviceName}
          </Link>
        </h3>
        {contributor ? (
          <h4 className={styles.subTitle}>{contributor}</h4>
        ) : null}
      </div>
      {device.deviceDescription ? (
        <p className={styles.description}>{device.deviceDescription}</p>
      ) : null}
      <SpecList specs={specs} />
    </article>
  );
};
