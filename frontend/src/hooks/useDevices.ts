import Papa from "papaparse";
import { useEffect, useState } from "react";
import { DEVICE_CSV_URL } from "../constants";
import type { Device } from "../types/device";

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
      powerSources: row.power_sources,
      processingUnit: row.processing_unit,
      modelProcessing: row.model_processing,
      captureModes: row.capture_modes,
      mainOpticalSensorModelName: row.main_optical_sensor_model_name,
      classificationTargetType: row.classification_target_type,
      taxonomicGroups: row.taxonomic_groups,
      functionalGroups: row.functional_groups,
      habitatType: row.habitat_type,
      operationalEnvironment: row.operational_environment,
      costUnitBuild: row.cost_unit_build,
      weight: row.weight,
      connectivity: row.connectivity,
      ipRating: row.ip_rating,
    }))
    .filter((device) => Boolean(device.deviceName));
};

const parseDeviceConstruction = (value?: string) =>
  value
    ?.split(";")
    .map((value) => value?.split(":")?.[0].trim())
    .filter((value) => value[0] === value[0].toUpperCase());
