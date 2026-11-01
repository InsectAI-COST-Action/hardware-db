import { Checkbox } from "@/components/Checkbox/Checkbox";
import { Tags } from "@/components/Tag/Tags";
import type { Device } from "@/lib/types";
import { getContributor, getOverviewSpecs } from "@/lib/utils";
import { Link } from "react-router";
import styles from "./DeviceTable.module.css";

/** Labels of the overview specs, in column order. */
const SPEC_COLUMNS = [
  "Processor",
  "Capture mode",
  "Power source",
  "Target taxa",
];

interface DeviceTableProps {
  devices: Device[];
  onSelectedChange: (slugs: string[]) => void;
  selected: string[];
}

export const DeviceTable = ({
  devices,
  onSelectedChange,
  selected,
}: DeviceTableProps) => {
  const toggle = (slug: string) => {
    onSelectedChange(
      selected.includes(slug)
        ? selected.filter((item) => item !== slug)
        : [...selected, slug],
    );
  };

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th className={styles.checkboxCell} />
            <th>Device</th>
            <th>Construction</th>
            {SPEC_COLUMNS.map((label) => (
              <th key={label}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => (
            <DeviceRow
              device={device}
              isSelected={selected.includes(device.slug)}
              key={device.slug}
              onToggle={() => toggle(device.slug)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
};

interface DeviceRowProps {
  device: Device;
  isSelected: boolean;
  onToggle: () => void;
}

const DeviceRow = ({ device, isSelected, onToggle }: DeviceRowProps) => {
  const specs = getOverviewSpecs(device);
  const contributor = getContributor(device);

  return (
    <tr className={isSelected ? styles.selected : undefined}>
      <td className={styles.checkboxCell}>
        <Checkbox
          checked={isSelected}
          className={styles.checkbox}
          label={`Select ${device.deviceName}`}
          onChange={onToggle}
        />
      </td>
      <td>
        {/* Stretched over the whole row so it stays clickable */}
        <Link className={styles.name} to={`/devices/${device.slug}`}>
          {device.deviceName}
        </Link>
        {contributor ? (
          <p className={styles.contributor}>{contributor}</p>
        ) : null}
      </td>
      <td>
        <Tags tags={device.deviceConstruction} />
      </td>
      {SPEC_COLUMNS.map((label) => {
        const value = specs.find((spec) => spec.label === label)?.value;

        return (
          <td className={styles.spec} key={label}>
            {value ?? <span className={styles.empty}>–</span>}
          </td>
        );
      })}
    </tr>
  );
};
