import { DEVICE_CSV_URL } from "@/lib/constants";
import type { Device, SpecGroup, TeamMember } from "@/lib/types";
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
 * How each specification is read from its column: as free text, as a `;`
 * separated list, or as a 1-5 score.
 */
type SpecFormat = "text" | "list" | "score";

type SpecGroupColumns = {
  title: string;
  specs: { label: string; column: string; format?: SpecFormat }[];
}[];

const SPEC_GROUP_COLUMNS: SpecGroupColumns = [
  {
    title: "Hardware",
    specs: [
      { label: "Construction", column: "device_construction", format: "list" },
      { label: "Processor", column: "processing_unit", format: "list" },
      { label: "Mounting", column: "mounting_system", format: "list" },
      { label: "Size, transport (mm)", column: "size_transport" },
      { label: "Size, deployed (mm)", column: "size_deployed" },
      { label: "Weight (kg)", column: "weight" },
      {
        label: "Skills & tools",
        column: "skills_tools_required",
        format: "list",
      },
      { label: "Licence", column: "device_licence", format: "list" },
    ],
  },
  {
    title: "Imaging",
    specs: [
      { label: "Capture modes", column: "capture_modes", format: "list" },
      { label: "Sensor", column: "main_optical_sensor_model_name" },
      { label: "Resolution", column: "main_sensor_resolution" },
      { label: "Frame rate", column: "main_sensor_framerate" },
      { label: "Focusing", column: "lens_focusing", format: "list" },
      { label: "Min. focal distance", column: "min_focal_distance" },
      { label: "Field of view", column: "field_of_view" },
      { label: "File types", column: "file_types", format: "list" },
    ],
  },
  {
    title: "Power & data",
    specs: [
      { label: "Power sources", column: "power_sources", format: "list" },
      { label: "Autonomy", column: "power_autonomy_continuous" },
      { label: "Image processing", column: "model_processing", format: "list" },
      { label: "Connectivity", column: "connectivity", format: "list" },
    ],
  },
  {
    title: "Cost & upkeep",
    specs: [
      { label: "Unit build cost", column: "cost_unit_build" },
      { label: "Seasonal deployment", column: "cost_deployment_seasonal" },
      { label: "Software / compute", column: "cost_software_compute" },
      { label: "Assembly time", column: "cost_assembly_time" },
      { label: "Maintenance", column: "maintenance_interval" },
      {
        label: "Repairability",
        column: "repairability_score",
        format: "score",
      },
    ],
  },
  {
    title: "Firmware",
    specs: [
      { label: "Last update", column: "last_firmware_update" },
      {
        label: "Update method",
        column: "firmware_update_method",
        format: "list",
      },
      { label: "Version / repo", column: "firmware_version_repo" },
    ],
  },
];

const ECOLOGY_GROUP_COLUMNS: SpecGroupColumns = [
  {
    title: "Target organisms",
    specs: [
      {
        label: "Classifies by",
        column: "classification_target_type",
        format: "list",
      },
      { label: "Taxonomic groups", column: "taxonomic_groups", format: "list" },
      {
        label: "Functional groups",
        column: "functional_groups",
        format: "list",
      },
      { label: "Min. subject size (mm)", column: "subject_size_min_mm" },
      { label: "Max. subject size (mm)", column: "subject_size_max_mm" },
    ],
  },
  {
    title: "Habitat & sampling",
    specs: [
      {
        label: "Environment",
        column: "operational_environment",
        format: "list",
      },
      { label: "Habitats", column: "habitat_type", format: "list" },
      { label: "Attractants", column: "attractants", format: "list" },
    ],
  },
  {
    title: "Field conditions",
    specs: [
      { label: "Weatherproofing", column: "ip_rating" },
      { label: "Min. temperature (°C)", column: "temperature_min_c" },
      { label: "Max. temperature (°C)", column: "temperature_max_c" },
    ],
  },
];

/**
 * Groups the columns for display. Empty specs are left out, and so are groups
 * with nothing left in them.
 */
const parseSpecGroups = (
  row: Record<string, string>,
  groups: SpecGroupColumns,
): SpecGroup[] =>
  groups.map(({ title, specs }) => ({
    title,
    specs: specs
      .map(({ label, column, format = "text" }) => ({
        label,
        value: formatSpec(row[column], format),
      }))
      .filter((spec) => spec.value),
  })).filter((group) => group.specs.length);

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
