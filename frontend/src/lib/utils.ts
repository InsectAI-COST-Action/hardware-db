import type { Device } from "./types";

export const getContributor = (device: Device) => {
  if (device.contactInstitution?.length) {
    return `By ${device.contactInstitution}`;
  }

  return `Contributed by ${device.contactName}`;
};

/**
 * The key specs shown for a device. Lists longer than `maxItems` are cut short
 * with a "+N more" suffix; without `maxItems` they are shown in full.
 */
export const getOverviewSpecs = (device: Device, maxItems?: number) => {
  const formatList = (items?: string[]) => {
    if (!items?.length) {
      return undefined;
    }

    if (maxItems === undefined) {
      return items.join(", ");
    }

    const shown = items.slice(0, maxItems).join(", ");
    const remaining = items.length - maxItems;

    return remaining > 0 ? `${shown} +${remaining} more` : shown;
  };

  return [
    { label: "Processor", value: device.processingUnit },
    { label: "Power", value: formatList(device.powerSources) },
    { label: "Capture", value: formatList(device.captureModes) },
    { label: "Target taxa", value: formatList(device.taxonomicGroups) },
  ].filter((spec) => spec.value);
};
