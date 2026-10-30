import {
  DEVICE_CSV_URL,
  ECOLOGY_GROUP_COLUMNS,
  SPEC_GROUP_COLUMNS,
} from "@/lib/constants";
import type {
  Device,
  SpecFormat,
  SpecGroup,
  SpecGroupColumns,
  TeamMember,
} from "@/lib/types";
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
        contactUrl: parseContactUrl(row.contact_email),
        contactInstitution: parseText(row.contact_institution),
        documentationUrl: parseText(row.documentation_url),
        deviceConstruction: parseList(row.device_construction).map((item) =>
          item.split(":")[0].trim(),
        ),
        powerSources: parseList(row.power_sources),
        processingUnits: parseList(row.processing_unit),
        modelProcessing: parseList(row.model_processing),
        captureModes: parseList(row.capture_modes),
        taxonomicGroups: parseList(row.taxonomic_groups),
        team: parseTeam(row),
        specifications: parseSpecGroups(row, SPEC_GROUP_COLUMNS),
        ecology: parseSpecGroups(row, ECOLOGY_GROUP_COLUMNS),
        slug: slugify(deviceName),
        raw: row,
      };
    })
    .filter((device) => Boolean(device.deviceName));

  return shuffle(devices);
};

/**
 * Turns the contact field into a link. It is free text, so besides email
 * addresses it can hold a web address (e.g. a LinkedIn profile), with or
 * without the scheme. Anything else is dropped.
 */
const parseContactUrl = (value?: string) => {
  const text = parseText(value);

  if (/^[^@\s/]+@[^@\s]+\.[^@\s]+$/.test(text)) {
    return `mailto:${text}`;
  }

  if (/^(https?:\/\/)?[^@\s/]+\.[a-z]{2,}(\/\S*)?$/i.test(text)) {
    return /^https?:\/\//i.test(text) ? text : `https://${text}`;
  }

  return "";
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

const TEAM_MEMBER_COLUMNS = [1, 2, 3, 4, 5].map((n) => ({
  name: `team_member_${n}_name`,
  role: `team_member_${n}_role`,
}));

/**
 * Collects the team from the contributor, the numbered team member columns and
 * `additional_team_members` ("name; affiliation; role | ..."). The contributor
 * is only included with a role, since a contributor without one is often just
 * whoever submitted the form. People listed twice are kept once.
 */
const parseTeam = (row: Record<string, string>) => {
  const contributor = {
    name: parseText(row.contributor_name),
    role: parseText(row.contributor_role),
  };
  const members = [
    ...(contributor.role ? [contributor] : []),
    ...TEAM_MEMBER_COLUMNS.map((columns) => ({
      name: parseText(row[columns.name]),
      role: parseText(row[columns.role]),
    })),
    ...parseText(row.additional_team_members)
      .split("|")
      .map((entry) => {
        const [name, , role] = entry.split(";");

        return { name: parseText(name), role: parseText(role) };
      }),
  ];
  const team = new Map<string, TeamMember>();

  for (const member of members) {
    if (member.name && !team.has(member.name)) {
      team.set(member.name, member);
    }
  }

  return [...team.values()];
};

/**
 * Groups the columns for display. Empty specs are left out, and so are groups
 * with nothing left in them.
 */
const parseSpecGroups = (
  row: Record<string, string>,
  groups: SpecGroupColumns,
): SpecGroup[] =>
  groups
    .map(({ title, icon, specs }) => ({
      title,
      icon,
      specs: specs
        .map(({ label, column, format = "text" }) => ({
          label,
          value: formatSpec(row[column], format),
        }))
        .filter((spec) => spec.value),
    }))
    .filter((group) => group.specs.length);

/**
 * List items drop their explanation after a `:`, e.g. "Off-the-shelf:
 * Purchased and used as-is" becomes "Off-the-shelf".
 */
const formatSpec = (value: string | undefined, format: SpecFormat) => {
  if (format === "list") {
    return parseList(value)
      .map((item) => item.split(":")[0].trim())
      .join(", ");
  }

  const text = parseText(value);

  return format === "score" && text ? `${text} / 5` : text;
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
