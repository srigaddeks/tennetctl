"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { apiList } from "@/lib/api";
import type { CatalogFeature, CatalogSubFeature } from "@/types/api";

export function useCatalogFeatures(): UseQueryResult<CatalogFeature[]> {
  return useQuery({
    queryKey: ["catalog", "features"],
    queryFn: async () => {
      const res = await apiList<CatalogFeature>("/v1/catalog/features");
      return res.items;
    },
  });
}

export function useCatalogSubFeatures(): UseQueryResult<CatalogSubFeature[]> {
  return useQuery({
    queryKey: ["catalog", "sub-features"],
    queryFn: async () => {
      const res = await apiList<CatalogSubFeature>("/v1/catalog/sub-features");
      return res.items;
    },
  });
}
