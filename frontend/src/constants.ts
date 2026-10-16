import type { ListField } from "./types";

export const DEVICE_CSV_URL =
  "https://raw.githubusercontent.com/InsectAI-COST-Action/hardware-db/main/data/_InsectAI_hardware-db.csv";

export const FILTER_DEFINITIONS: {
  field: ListField;
  title: string;
}[] = [
  { field: "deviceConstruction", title: "Construction" },
  { field: "taxonomicGroups", title: "Target taxa" },
  { field: "captureModes", title: "Capture mode" },
  { field: "powerSources", title: "Power source" },
  { field: "modelProcessing", title: "Image processing" },
];
