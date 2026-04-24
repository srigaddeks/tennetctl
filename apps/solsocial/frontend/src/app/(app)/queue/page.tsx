"use client";
import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ss } from "@/lib/api";
import type { Channel, ListPage, Queue, QueueSlot } from "@/types/api";
import { Spinner } from "@/components/fields";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

type SlotIn = { day_of_week: number; hour: number; minute: number };

function keyFor(dow: number, h: number, m = 0): string {
  return `${dow}-${h}-${m}`;
}

export default function QueuePage() {
  const qc = useQueryClient();
  const channels = useQuery({ queryKey: ["channels"], queryFn: () => ss.get<ListPage<Channel>>("/v1/channels") });
  const [channelId, setChannelId] = useState<string>("");
  const queue = useQuery({
    queryKey: ["queue", channelId],
    queryFn: () => ss.get<Queue>(`/v1/queues?channel_id=${channelId}`),
    enabled: !!channelId,
    retry: false,
  });

  // Local editor state — a Set of "dow-hour-minute" strings. Initialized from
  // the fetched queue, mutated by click, saved via PUT.
  const [draft, setDraft] = useState<Set<string>>(new Set());
  const [tz, setTz] = useState<string>("UTC");
  const [dirty, setDirty] = useState(false);

  // Sync draft when queue loads / channel changes.
  useEffect(() => {
    if (!channelId) { setDraft(new Set()); setTz("UTC"); setDirty(false); return; }
    const slots = queue.data?.slots ?? [];
    setDraft(new Set(slots.map((s: QueueSlot) => keyFor(s.day_of_week, s.hour, s.minute))));
    setTz(queue.data?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone ?? "UTC");
    setDirty(false);
  }, [channelId, queue.data]);

  const save = useMutation({
    mutationFn: (slots: SlotIn[]) => ss.put<Queue>("/v1/queues", {
      channel_id: channelId, timezone: tz, slots,
    }),
    onSuccess: () => { setDirty(false); qc.invalidateQueries({ queryKey: ["queue", channelId] }); },
  });

  const slotList: SlotIn[] = useMemo(
    () => [...draft].map(k => {
      const [dow, h, m] = k.split("-").map(Number);
      return { day_of_week: dow, hour: h, minute: m };
    }).sort((a, b) => a.day_of_week - b.day_of_week || a.hour - b.hour || a.minute - b.minute),
    [draft],
  );

  function toggle(dow: number, h: number) {
    const k = keyFor(dow, h, 0);
    setDraft(prev => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k); else next.add(k);
      return next;
    });
    setDirty(true);
  }

  function clearAll() {
    if (!confirm("Remove all time slots for this channel?")) return;
    setDraft(new Set());
    setDirty(true);
  }

  const noQueue = !!channelId && (queue.isError || !queue.data);

  return (
    <div className="max-w-6xl mx-auto rise">
      <div className="mb-10">
        <p className="kicker rule mb-3">The timetable</p>
        <h1 className="display text-[64px] leading-none">Queue.</h1>
        <p className="mt-4 text-[color:var(--ink-70)] max-w-xl">
          Recurring weekly slots per channel. Click a cell to toggle a time slot.
          Queued posts publish in the next open slot.
        </p>
      </div>

      <div className="mb-6 flex items-center gap-4 flex-wrap">
        <span className="kicker">Channel</span>
        <select className="boxed max-w-xs" value={channelId} onChange={e => setChannelId(e.target.value)}>
          <option value="">— pick one —</option>
          {channels.data?.items.map(c => (
            <option key={c.id} value={c.id}>{c.provider_code} · {c.handle}</option>
          ))}
        </select>
        {channelId && (
          <>
            <span className="kicker">Timezone</span>
            <input
              className="boxed max-w-[200px] mono text-[12px]"
              value={tz}
              onChange={e => { setTz(e.target.value); setDirty(true); }}
              placeholder="UTC"
            />
          </>
        )}
      </div>

      {!channelId ? (
        <div className="py-6">
          <p className="display-italic text-[24px] text-[color:var(--ink-40)] mb-3">
            Choose a channel above to set its week.
          </p>
          <p className="mono text-[11px] text-[color:var(--ink-40)] max-w-md">
            Each channel has its own recurring schedule. Drafts in that channel's
            queue publish at the next open slot — no per-post time picking required.
          </p>
        </div>
      ) : (
        <>
          {noQueue && (
            <div className="paper-deep p-4 mb-6 hairline">
              <p className="mono text-[12px] text-[color:var(--ink-70)]">
                No queue yet for this channel — clicking slots + Save will create one.
              </p>
            </div>
          )}

          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="mono text-[11px] text-[color:var(--ink-40)]">
                {draft.size} slot{draft.size === 1 ? "" : "s"}
                {dirty && <span className="ml-2 text-[color:var(--ember-deep)]">· unsaved</span>}
              </p>
              {slotList.length > 0 && (
                <p className="mono text-[10px] text-[color:var(--ink-40)] mt-1">
                  Next firing: {DAYS[slotList[0].day_of_week]} {String(slotList[0].hour).padStart(2, "0")}:{String(slotList[0].minute).padStart(2, "0")} {tz}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              {draft.size > 0 && (
                <button className="btn-ghost text-[11px] mono uppercase tracking-wider" onClick={clearAll}>
                  clear all
                </button>
              )}
              <button
                className="btn btn-ember text-[11px]"
                disabled={!dirty || save.isPending}
                onClick={() => save.mutate(slotList)}
              >
                {save.isPending ? <><Spinner /> Saving…</> : "Save queue →"}
              </button>
            </div>
          </div>

          {save.isError && (
            <div className="mono text-[12px] text-[color:var(--ember-deep)] mb-4">
              × {(save.error as Error).message}
            </div>
          )}

          {/* Week grid — interactive */}
          <div className="hairline overflow-hidden">
            <div className="grid grid-cols-[60px_repeat(7,1fr)] bg-[color:var(--paper-deep)] border-b border-[color:var(--rule)]">
              <div className="p-2 kicker text-right">hr</div>
              {DAYS.map(d => (
                <div key={d} className="p-2 kicker border-l border-[color:var(--rule)] text-center">{d}</div>
              ))}
            </div>
            <div className="max-h-[560px] overflow-y-auto">
              {HOURS.map(h => (
                <div key={h} className="grid grid-cols-[60px_repeat(7,1fr)] border-b border-[color:var(--rule)] last:border-b-0">
                  <div className="p-2 mono text-[10px] text-[color:var(--ink-40)] text-right">
                    {String(h).padStart(2, "0")}:00
                  </div>
                  {DAYS.map((_, dow) => {
                    const on = draft.has(keyFor(dow, h, 0));
                    return (
                      <button
                        key={dow}
                        type="button"
                        onClick={() => toggle(dow, h)}
                        className={`p-1 border-l border-[color:var(--rule)] h-10 flex items-center justify-center transition
                                    ${on
                                      ? "bg-[color:var(--paper-deep)] hover:bg-[rgba(220,75,25,0.08)]"
                                      : "hover:bg-[color:var(--paper-deep)]"}`}
                        title={`${DAYS[dow]} ${h}:00 · ${on ? "click to remove" : "click to add"}`}
                      >
                        {on && (
                          <span className="w-3 h-3 rounded-full bg-[color:var(--ember)] hover:scale-110 transition" />
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <p className="mt-4 mono text-[10px] text-[color:var(--ink-40)]">
            Tip: slots are on the hour. Half-hour/quarter-hour granularity lives in the API but not this editor yet.
          </p>
        </>
      )}
    </div>
  );
}
