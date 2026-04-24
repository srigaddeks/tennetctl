"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ss } from "@/lib/api";

type CalItem = {
  id: string;
  channel_id: string;
  status: string;
  body: string;
  scheduled_at: string | null;
  published_at: string | null;
};

const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];

function startOfMonth(d: Date) { return new Date(d.getFullYear(), d.getMonth(), 1); }
function endOfMonth(d: Date)   { return new Date(d.getFullYear(), d.getMonth() + 1, 0); }

export default function CalendarPage() {
  const [cursor, setCursor] = useState(() => new Date());
  const start = startOfMonth(cursor);
  const end = endOfMonth(cursor);
  const q = useQuery({
    queryKey: ["calendar", start.toISOString(), end.toISOString()],
    queryFn: () => ss.get<{ items: CalItem[]; start: string; end: string }>(
      `/v1/calendar?start=${encodeURIComponent(start.toISOString())}&end=${encodeURIComponent(end.toISOString())}`
    ),
  });

  // group by day-of-month
  const byDay = new Map<number, CalItem[]>();
  (q.data?.items ?? []).forEach(it => {
    const when = it.scheduled_at ?? it.published_at;
    if (!when) return;
    const d = new Date(when);
    if (d.getMonth() !== cursor.getMonth() || d.getFullYear() !== cursor.getFullYear()) return;
    const day = d.getDate();
    const arr = byDay.get(day) ?? [];
    arr.push(it);
    byDay.set(day, arr);
  });

  const firstDow = start.getDay();
  const daysInMonth = end.getDate();
  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);

  const today = new Date();
  const isToday = (d: number) =>
    d === today.getDate() && cursor.getMonth() === today.getMonth() && cursor.getFullYear() === today.getFullYear();

  return (
    <div className="max-w-6xl mx-auto rise">
      <div className="flex items-end justify-between mb-10">
        <div>
          <p className="kicker rule mb-3">The month ahead</p>
          <h1 className="display text-[64px] leading-none" suppressHydrationWarning>
            {MONTH_NAMES[cursor.getMonth()]}{" "}
            <span className="display-italic">{cursor.getFullYear()}</span>
          </h1>
          <p className="mt-3 mono text-[11px] text-[color:var(--ink-40)] max-w-md">
            Every scheduled and published post across every channel, at a glance.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn text-[11px]"
                  onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}>← prev</button>
          <button className="btn text-[11px]" onClick={() => setCursor(new Date())}>today</button>
          <button className="btn text-[11px]"
                  onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}>next →</button>
        </div>
      </div>

      {q.isLoading ? (
        <div className="hairline overflow-hidden">
          <div className="grid grid-cols-7 bg-[color:var(--paper-deep)] border-b border-[color:var(--rule)]">
            {Array.from({ length: 7 }).map((_, i) => (
              <div key={i} className="p-3 border-l first:border-l-0 border-[color:var(--rule)] h-8" />
            ))}
          </div>
          <div className="grid grid-cols-7">
            {Array.from({ length: 35 }).map((_, i) => (
              <div key={i} className="min-h-[110px] border-l border-b border-[color:var(--rule)] first:border-l-0" />
            ))}
          </div>
        </div>
      ) : (
        <div className="hairline overflow-hidden">
          {/* Header row */}
          <div className="grid grid-cols-7 bg-[color:var(--paper-deep)] border-b border-[color:var(--rule)]">
            {DOW.map(d => (
              <div key={d} className="p-3 kicker text-center border-l first:border-l-0 border-[color:var(--rule)]">{d}</div>
            ))}
          </div>

          {/* Cells */}
          <div className="grid grid-cols-7">
            {cells.map((day, idx) => {
              const items = day ? byDay.get(day) ?? [] : [];
              const today_ = day && isToday(day);
              return (
                <div
                  key={idx}
                  className={`min-h-[110px] p-2 border-l border-b border-[color:var(--rule)] first:border-l-0
                              ${idx < 7 ? "" : ""}
                              ${today_ ? "bg-[color:var(--paper-deep)]" : ""}
                              ${!day ? "bg-[rgba(0,0,0,0.02)]" : ""}`}
                >
                  {day && (
                    <>
                      <div className={`flex items-baseline gap-2 mb-2 ${today_ ? "text-[color:var(--ember-deep)]" : ""}`}>
                        <span className="display text-[20px] leading-none">{day}</span>
                        {today_ && <span className="kicker !text-[color:var(--ember-deep)]">today</span>}
                      </div>
                      <div className="space-y-1">
                        {items.slice(0, 3).map(it => (
                          <div key={it.id} className="text-[11px] leading-tight flex gap-1">
                            <span
                              className="inline-block w-[6px] h-[6px] rounded-full mt-[5px] shrink-0"
                              style={{ background: it.published_at ? "var(--sage)" : "var(--lapis)" }}
                            />
                            <span className="truncate">{it.body.slice(0, 26) || "—"}</span>
                          </div>
                        ))}
                        {items.length > 3 && (
                          <div className="mono text-[10px] text-[color:var(--ink-40)]">+{items.length - 3} more</div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-6 flex gap-6 kicker">
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: "var(--lapis)" }}/> scheduled
        </span>
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: "var(--sage)" }}/> published
        </span>
      </div>
    </div>
  );
}
