/**
 * Port type to Tailwind color mapping for canvas node handles.
 * Plan 44-01 implementation — pure, exhaustive over all 10 port types.
 */

import type { PortType } from "@/types/api";

export type PortColorScheme = {
  bg: string;
  ring: string;
  text: string;
};

export function colorFor(portType: PortType): PortColorScheme {
  switch (portType) {
    case "any":
      return {
        bg: "bg-slate-400",
        ring: "ring-slate-500",
        text: "text-slate-900",
      };
    case "string":
      return {
        bg: "bg-blue-400",
        ring: "ring-blue-500",
        text: "text-blue-900",
      };
    case "number":
      return {
        bg: "bg-amber-400",
        ring: "ring-amber-500",
        text: "text-amber-900",
      };
    case "boolean":
      return {
        bg: "bg-green-400",
        ring: "ring-green-500",
        text: "text-green-900",
      };
    case "object":
      return {
        bg: "bg-violet-400",
        ring: "ring-violet-500",
        text: "text-violet-900",
      };
    case "array":
      return {
        bg: "bg-rose-400",
        ring: "ring-rose-500",
        text: "text-rose-900",
      };
    case "uuid":
      return {
        bg: "bg-cyan-400",
        ring: "ring-cyan-500",
        text: "text-cyan-900",
      };
    case "datetime":
      return {
        bg: "bg-teal-400",
        ring: "ring-teal-500",
        text: "text-teal-900",
      };
    case "binary":
      return {
        bg: "bg-stone-400",
        ring: "ring-stone-500",
        text: "text-stone-900",
      };
    case "error":
      return {
        bg: "bg-red-400",
        ring: "ring-red-500",
        text: "text-red-900",
      };
    default: {
      const _exhaustive: never = portType;
      return _exhaustive;
    }
  }
}
