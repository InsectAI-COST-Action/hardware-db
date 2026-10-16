import Papa from "papaparse";
import { useEffect, useState } from "react";
import { DEVICE_CSV_URL } from "../constants";
import type { Device } from "../types";

export const useDevices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchDevices()
      .then((data) => {
        if (cancelled) {
          return;
        }

        setDevices(data);
        setIsLoading(false);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        setError(error);
        setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { devices, isLoading, error };
};

const fetchDevices = async () => {
  const res = await fetch(DEVICE_CSV_URL);

  if (!res.ok) {
    throw new Error();
  }

  const csvText = await res.text();
  const result = Papa.parse<Record<string, string>>(csvText, {
    header: true,
    skipEmptyLines: true,
  });

  if (result.errors.length > 0) {
    console.warn(result.errors);
  }

  return result.data
    .map((row) => ({
      haveDeviceId: row.have_deviceID,
      deviceName: row.device_name,
      deviceDescription: row.device_description,
      contactName: row.contact_name,
      contactInstitution: row.contact_institution,
      documentationUrl: row.documentation_url,
      deviceConstruction: parseDeviceConstruction(row.device_construction),
      powerSources: parseList(row.power_sources),
      processingUnit: row.processing_unit,
      modelProcessing: parseList(row.model_processing),
      captureModes: parseList(row.capture_modes),
      mainOpticalSensorModelName: row.main_optical_sensor_model_name,
      classificationTargetType: row.classification_target_type,
      taxonomicGroups: parseList(row.taxonomic_groups),
      functionalGroups: parseList(row.functional_groups),
      habitatType: parseList(row.habitat_type),
      operationalEnvironment: parseList(row.operational_environment),
      costUnitBuild: row.cost_unit_build,
      weight: row.weight,
      connectivity: parseList(row.connectivity),
      ipRating: row.ip_rating,
    }))
    .filter((device) => Boolean(device.deviceName));
};

/**
 * Splits a `;`-separated list and normalizes each value by dropping a trailing
 * parenthetical, so e.g. "Lepidoptera" and "Lepidoptera (butterflies & moths)"
 * become the same value.
 */
const parseList = (value?: string) => [
  ...new Set(
    (value ?? "")
      .split(";")
      .map((item) => item.trim().replace(/\s*\(.*\)$/, ""))
      .filter(Boolean),
  ),
];

const parseDeviceConstruction = (value?: string) => [
  ...new Set(
    parseList(value)
      .map((item) => item.split(":")[0].trim())
      .filter((item) => item[0] === item[0].toUpperCase()),
  ),
];
