"use client";

/**
 * Re-exports alert-rule hooks from use-alerts (co-located). Split into this
 * file per the sub-feature layout convention so components can import from a
 * focused module.
 */

export {
  useAlertRule,
  useAlertRules,
  useCreateAlertRule,
  useDeleteAlertRule,
  usePauseAlertRule,
  useUnpauseAlertRule,
  useUpdateAlertRule,
} from "./use-alerts";
