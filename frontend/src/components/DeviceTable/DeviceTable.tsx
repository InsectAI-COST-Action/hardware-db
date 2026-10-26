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

export const DeviceTable = ({ devices }: { devices: Device[] }) => (
  <div className={styles.container}>
    <table className={styles.table}>
      <thead>
        <tr>
          <th>Device</th>
          <th>Construction</th>
          {SPEC_COLUMNS.map((label) => (
            <th key={label}>{label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {devices.map((device) => (
          <DeviceRow key={device.slug} device={device} />
        ))}
      </tbody>
    </table>
  </div>
);

const DeviceRow = ({ device }: { device: Device }) => {
  const specs = getOverviewSpecs(device);
  const contributor = getContributor(device);

  return (
    <tr>
      <td>
        <Link className={styles.name} to={`/devices/${device.slug}`}>
          <span>{device.deviceName}</span>
          {contributor ? (
            <span className={styles.contributor}>{contributor}</span>
          ) : null}
        </Link>
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
