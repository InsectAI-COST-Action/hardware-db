import {
  BatteryCharging,
  Bug,
  Camera,
  CodeXml,
  Coins,
  Grid2x2,
  type LucideIcon,
  Moon,
  Sun,
  Table,
  Thermometer,
  Trees,
  Wrench,
} from "lucide-react";
import type {
  ListField,
  SortOption,
  SpecGroupColumns,
  Theme,
  ViewMode,
} from "./types";

export const DEVICE_CSV_URL =
  "https://raw.githubusercontent.com/InsectAI-COST-Action/hardware-db/main/data/_InsectAI_hardware-db.csv";

export const EXTERNAL_LINKS = [
  {
    label: "GitHub",
    href: "https://github.com/InsectAI-COST-Action/hardware-db",
  },
  { label: "InsectAI", href: "https://insectai.eu/" },
];

export const FILTER_DEFINITIONS: {
  field: ListField;
  title: string;
}[] = [
  { field: "deviceConstruction", title: "Construction" },
  { field: "captureModes", title: "Capture mode" },
  { field: "powerSources", title: "Power source" },
  { field: "taxonomicGroups", title: "Target taxa" },
];

export const SPEC_GROUP_COLUMNS: SpecGroupColumns = [
  {
    title: "Hardware",
    icon: Wrench,
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
    icon: Camera,
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
    icon: BatteryCharging,
    specs: [
      { label: "Power sources", column: "power_sources", format: "list" },
      { label: "Autonomy", column: "power_autonomy_continuous" },
      { label: "Image processing", column: "model_processing", format: "list" },
      { label: "Connectivity", column: "connectivity", format: "list" },
    ],
  },
  {
    title: "Cost & upkeep",
    icon: Coins,
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
    icon: CodeXml,
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

export const ECOLOGY_GROUP_COLUMNS: SpecGroupColumns = [
  {
    title: "Target organisms",
    icon: Bug,
    specs: [
      {
        label: "Functional groups",
        column: "functional_groups",
        format: "list",
      },
      { label: "Taxonomic groups", column: "taxonomic_groups", format: "list" },
      {
        label: "Classifies by",
        column: "classification_target_type",
        format: "list",
      },
      { label: "Min. subject size (mm)", column: "subject_size_min_mm" },
      { label: "Max. subject size (mm)", column: "subject_size_max_mm" },
    ],
  },
  {
    title: "Habitat & sampling",
    icon: Trees,
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
    icon: Thermometer,
    specs: [
      { label: "Min. temperature (°C)", column: "temperature_min_c" },
      { label: "Max. temperature (°C)", column: "temperature_max_c" },
      { label: "Weatherproofing", column: "ip_rating" },
    ],
  },
];

export const SORT_OPTIONS: {
  value: SortOption;
  label: string;
}[] = [
  { value: "random", label: "Random" },
  { value: "name", label: "Name (A-Z)" },
];

export const SUBMIT_LINK =
  "https://docs.google.com/forms/d/1tEs9BkqGV579_Qd8aOVvAhmVWEfLAnKxa04KMH8Pi3Q/viewform";

export const THEME_OPTIONS: {
  value: Theme;
  label: string;
  icon: LucideIcon;
}[] = [
  { value: "light", label: "Light mode", icon: Sun },
  { value: "dark", label: "Dark mode", icon: Moon },
];

export const VIEW_MODE_OPTIONS: {
  value: ViewMode;
  label: string;
  icon: LucideIcon;
}[] = [
  { value: "table", label: "Table", icon: Table },
  { value: "gallery", label: "Gallery", icon: Grid2x2 },
];
