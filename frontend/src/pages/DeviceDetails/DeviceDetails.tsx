import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import { LinkButton } from "../../components/LinkButton/LinkButton";
import { Tabs } from "../../components/Tabs/Tabs";
import { Tag } from "../../components/Tag/Tag";
import { useAppContext } from "../../hooks/useAppContext";
import type { Device } from "../../lib/types";
import { getContributor, getOverviewSpecs } from "../../lib/utils";
import styles from "./DeviceDetails.module.css";

const TABS: { value: string; label: string }[] = [
  { value: "overview", label: "Overview" },
];

export const DeviceDetails = () => (
  <div className={styles.container}>
    <Content />
  </div>
);

const Content = () => {
  const { slug } = useParams();
  const { devices, isLoading, error } = useAppContext();
  const device = devices.find((device) => device.slug === slug);

  if (isLoading) {
    return <p>Loading device...</p>;
  }

  if (error) {
    return <p>Uh oh, could not load devices. Try again later.</p>;
  }

  if (!device) {
    return <p>Device not found.</p>;
  }

  return <Device device={device} />;
};

const Device = ({ device }: { device: Device }) => {
  const [tab, setTab] = useState<string>("overview");
  const specs = useMemo(() => getOverviewSpecs(device), [device]);

  return (
    <>
      <nav aria-label="Breadcrumb" className={styles.breadcrumb}>
        <Link className={styles.backLink} to="/">
          Devices
        </Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{device.deviceName}</span>
      </nav>
      <div className={styles.header}>
        <div>
          {device.deviceConstruction?.length ? (
            <div className={styles.tags}>
              {device.deviceConstruction.map((type) => (
                <Tag key={type}>{type}</Tag>
              ))}
            </div>
          ) : null}
          <h1 className={styles.title}>{device.deviceName}</h1>
          <p>{getContributor(device)}</p>
        </div>
        <div className={styles.actions}>
          {device.documentationUrl ? (
            <LinkButton
              external
              href={device.documentationUrl}
              variant="outline"
            >
              Documentation
            </LinkButton>
          ) : null}
        </div>
      </div>
      <Tabs label="Device details" onChange={setTab} tabs={TABS} value={tab} />
      {tab === "overview" && (
        <div aria-label="Overview" className={styles.panel} role="tabpanel">
          {device.deviceDescription ? <p>{device.deviceDescription}</p> : null}
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
      )}
    </>
  );
};
