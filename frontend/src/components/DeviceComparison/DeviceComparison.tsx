import { ECOLOGY_GROUP_COLUMNS, SPEC_GROUP_COLUMNS } from "@/lib/constants";
import type { Device } from "@/lib/types";
import { Link } from "react-router";
import styles from "./DeviceComparison.module.css";

const GROUPS = [
  ...SPEC_GROUP_COLUMNS.map((group) => ({
    ...group,
    field: "specifications" as const,
  })),
  ...ECOLOGY_GROUP_COLUMNS.map((group) => ({
    ...group,
    field: "ecology" as const,
  })),
];

/**
 * Devices side by side, one column each. Rows follow the spec group
 * definitions; rows no compared device has a value for are left out.
 */
export const DeviceComparison = ({ devices }: { devices: Device[] }) => {
  const groups = GROUPS.map(({ title, icon, specs, field }) => ({
    title,
    icon,
    rows: specs
      .map(({ label }) => ({
        label,
        values: devices.map(
          (device) =>
            device[field]
              .find((group) => group.title === title)
              ?.specs.find((spec) => spec.label === label)?.value,
        ),
      }))
      .filter((row) => row.values.some(Boolean)),
  })).filter((group) => group.rows.length);

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            <td className={styles.labelCell} />
            {devices.map((device) => (
              <th className={styles.deviceCell} key={device.slug} scope="col">
                <Link className={styles.name} to={`/devices/${device.slug}`}>
                  {device.deviceName}
                </Link>
              </th>
            ))}
          </tr>
        </thead>
        {groups.map(({ title, icon: Icon, rows }) => (
          <tbody key={title}>
            <tr>
              <th
                className={styles.groupCell}
                colSpan={devices.length + 1}
                scope="colgroup"
              >
                <span className={styles.groupTitle}>
                  <Icon aria-hidden="true" size={16} />
                  {title}
                </span>
              </th>
            </tr>
            {rows.map(({ label, values }) => (
              <tr key={label}>
                <th className={styles.labelCell} scope="row">
                  {label}
                </th>
                {values.map((value, i) => (
                  <td className={styles.valueCell} key={devices[i].slug}>
                    {value ?? <span className={styles.empty}>–</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
};
