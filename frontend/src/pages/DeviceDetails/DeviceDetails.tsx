import { LinkButton } from "@/components/LinkButton/LinkButton";
import { SpecGroups } from "@/components/SpecGroups/SpecGroups";
import { SpecList } from "@/components/SpecList/SpecList";
import { Tabs } from "@/components/Tabs/Tabs";
import { Tags } from "@/components/Tag/Tags";
import { TeamList } from "@/components/TeamList/TeamList";
import { useAppContext } from "@/hooks/useAppContext";
import type { Device } from "@/lib/types";
import { getContributor, getOverviewSpecs } from "@/lib/utils";
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";
import styles from "./DeviceDetails.module.css";

type Tab = "overview" | "specifications" | "raw";

const TABS: { value: Tab; label: string }[] = [
  { value: "overview", label: "Overview" },
  { value: "specifications", label: "Specifications" },
  { value: "raw", label: "Raw data" },
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
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Uh oh, could not load devices. Try again later.</p>;
  }

  if (!device) {
    return <p>Device not found.</p>;
  }

  return <DeviceView device={device} />;
};

const DeviceView = ({ device }: { device: Device }) => {
  const [tab, setTab] = useState<Tab>("overview");
  const specs = useMemo(() => getOverviewSpecs(device), [device]);
  const rawJson = useMemo(() => JSON.stringify(device.raw, null, 2), [device]);
  const contributor = getContributor(device);
  const isEmail = device.contactUrl.startsWith("mailto:");

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
          <Tags className={styles.tags} tags={device.deviceConstruction} />
          <h1 className={styles.title}>{device.deviceName}</h1>
          {contributor ? <p>{contributor}</p> : null}
        </div>
        <div className={styles.actions}>
          {device.contactUrl ? (
            <LinkButton
              external={!isEmail}
              href={device.contactUrl}
              icon={isEmail ? "/images/mail.svg" : undefined}
              variant="outline"
            >
              Contact
            </LinkButton>
          ) : null}
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
          <SpecList specs={specs} variant="table" />
          {device.team.length ? (
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Team</h2>
              <TeamList members={device.team} />
            </section>
          ) : null}
        </div>
      )}
      {tab === "specifications" && (
        <div aria-label="Specifications" role="tabpanel">
          {device.specifications.length ? (
            <SpecGroups groups={device.specifications} />
          ) : (
            <p>No specifications listed for this device.</p>
          )}
        </div>
      )}
      {tab === "raw" && (
        <div aria-label="Raw data" className={styles.panel} role="tabpanel">
          <pre className={styles.code}>
            <code>{rawJson}</code>
          </pre>
        </div>
      )}
    </>
  );
};
