/**
 * TennetCTL — Shared API types.
 *
 * ALL shared TS types live in this one file.
 * No scattered type files. No enums — use string literal unions.
 */

export type ApiSuccess<T> = {
  ok: true;
  data: T;
};

export type ApiError = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type ApiResponse<T> = ApiSuccess<T> | ApiError;

export type PaginatedResponse<T> = {
  ok: true;
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
};

// Health
export type HealthData = {
  status: string;
};
