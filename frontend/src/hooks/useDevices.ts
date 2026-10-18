import { DEVICE_CSV_URL } from "@/lib/constants";
import type { Device } from "@/lib/types";
import Papa from "papaparse";
import { useEffect, useState } from "react";

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

  const devices = result.data
    .map((row) => {
      const deviceName = parseText(row.device_name);

      return {
        deviceName,
        deviceDescription: parseText(row.device_description),
        contactName: parseText(row.contact_name),
        contactInstitution: parseText(row.contact_institution),
        documentationUrl: parseText(row.documentation_url),
        deviceConstruction: parseList(row.device_construction).map((item) =>
          item.split(":")[0].trim(),
        ),
        powerSources: parseList(row.power_sources),
        processingUnit: parseText(row.processing_unit),
        modelProcessing: parseList(row.model_processing),
        captureModes: parseList(row.capture_modes),
        taxonomicGroups: parseList(row.taxonomic_groups),
        slug: slugify(deviceName),
        raw: row,
      };
    })
    .filter((device) => Boolean(device.deviceName));

  return shuffle(devices);
};

/**
 * Splits a `;`-separated list and normalizes each value by dropping a trailing
 * parenthetical, so e.g. "Lepidoptera" and "Lepidoptera (butterflies & moths)"
 * become the same value.
 */
const parseList = (value?: string) => [
  ...new Set(
    splitList(value ?? "")
      .map((item) => item.trim().replace(/\s*\(.*\)$/, ""))
      .filter(Boolean),
  ),
];

const parseText = (value?: string) => value?.trim() ?? "";

/**
 * Fisher–Yates shuffle. Done once on load so the default "random" order stays
 * stable while filtering and when switching back from another sort.
 */
const shuffle = <T>(items: T[]) => {
  const result = [...items];

  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }

  return result;
};

/**
 * Splits on `;` outside parentheses only. Commas in option labels end up as
 * `;` in the data, e.g. "Hymenoptera (bees; wasps; ants)", and that must stay
 * one item.
 */
const splitList = (value: string) => {
  const items: string[] = [];
  let current = "";
  let depth = 0;

  for (const char of value) {
    if (char === "(") {
      depth++;
    } else if (char === ")") {
      depth = Math.max(0, depth - 1);
    }

    if (char === ";" && depth === 0) {
      items.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  items.push(current);

  return items;
};

/**
 * Turns a device name into a URL-safe slug, e.g. "Lépinoc 2" -> "lepinoc-2".
 */
const slugify = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
