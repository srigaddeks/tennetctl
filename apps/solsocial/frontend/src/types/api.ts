// Shared API types. One file, no scattering.

export type Envelope<T> =
  | { ok: true; data: T }
  | { ok: false; error: { code: string; message: string } };

export type ListPage<T> = { items: T[]; total: number; pagination?: { limit: number; offset: number; total: number } };

export type User = {
  id: string;
  account_type: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Session = {
  id: string;
  user_id: string;
  org_id: string | null;
  workspace_id: string | null;
  expires_at: string;
  revoked_at: string | null;
  is_valid: boolean;
};

export type AuthResponse = { token: string; user: User; session: Session };

export type Me = { user: User; session: Session };

export type ProviderCode = "linkedin" | "twitter" | "instagram";

export type Channel = {
  id: string;
  org_id: string;
  workspace_id: string;
  provider_code: ProviderCode;
  handle: string;
  display_name: string | null;
  avatar_url: string | null;
  external_id: string | null;
  connected_at: string;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PostStatus = "draft" | "queued" | "scheduled" | "publishing" | "published" | "failed";

export type MediaItem = { type: "image" | "video"; url: string; alt?: string | null };

export type Post = {
  id: string;
  org_id: string;
  workspace_id: string;
  channel_id: string;
  status: PostStatus;
  body: string;
  media: MediaItem[];
  link: string | null;
  scheduled_at: string | null;
  published_at: string | null;
  external_post_id: string | null;
  external_url: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type Idea = {
  id: string;
  org_id: string;
  workspace_id: string;
  title: string;
  notes: string | null;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceApp = {
  id: string;
  workspace_id: string;
  org_id: string;
  provider_code: ProviderCode;
  client_id: string;
  has_secret: boolean;
  redirect_uri_hint: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

// ── Social Capture (collected by the browser extension) ──────────────────────
export type CapturePlatform = "linkedin" | "x" | "twitter" | "instagram";
export type CaptureType =
  | "feed_post_seen"
  | "own_post_published"
  | "comment_seen"
  | "own_comment"
  | "profile_viewed";

export type SocialCapture = {
  id: string;
  user_id: string;
  org_id: string;
  platform: CapturePlatform;
  type: CaptureType;
  platform_post_id: string;
  observed_at: string;
  extractor_version: string;
  author_handle: string | null;
  author_name: string | null;
  text_excerpt: string | null;
  url: string | null;
  like_count: number | null;
  reply_count: number | null;
  repost_count: number | null;
  view_count: number | null;
  is_own: boolean;
  created_at: string;
};

export type CaptureStats = {
  total: number;
  by_platform: Record<string, number>;
  by_type: Record<string, number>;
  own_posts: number;
};

export type QueueSlot = { id: string; queue_id: string; day_of_week: number; hour: number; minute: number; created_at: string };
export type Queue = {
  id: string;
  channel_id: string;
  workspace_id: string;
  org_id: string;
  timezone: string;
  slots: QueueSlot[];
  created_at: string;
  updated_at: string;
};
