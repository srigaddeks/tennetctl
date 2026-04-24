"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createRider, listRiderRoles } from "@/lib/api";
import type { RiderRole, RiderStatus } from "@/types/api";

export default function NewRiderPage() {
  const router = useRouter();
  const [roles, setRoles] = useState<RiderRole[]>([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [roleId, setRoleId] = useState<string>("");
  const [vehicleType, setVehicleType] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [userId, setUserId] = useState("");
  const [status, setStatus] = useState<RiderStatus>("active");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    listRiderRoles().then(setRoles).catch(() => setRoles([]));
  }, []);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await createRider({
        name,
        phone: phone || null,
        role_id: Number(roleId),
        vehicle_type: vehicleType || null,
        license_number: licenseNumber || null,
        user_id: userId || null,
        status,
      });
      router.push("/delivery/riders");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>New Rider</h1>
      </div>

      <form
        onSubmit={onSubmit}
        className="max-w-2xl space-y-4 rounded border p-6" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="Sri"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Phone</span>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
            placeholder="+91 98765 43210"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Role</span>
          <select
            required
            value={roleId}
            onChange={(e) => setRoleId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">Select role…</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">
            Vehicle type
          </span>
          <input
            value={vehicleType}
            onChange={(e) => setVehicleType(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            placeholder="scooter / bike / van / walking"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">
            License number
          </span>
          <input
            value={licenseNumber}
            onChange={(e) => setLicenseNumber(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">
            tennetctl user_id (optional)
          </span>
          <input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono"
            placeholder="uuid — leave blank for contractors without account"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium ">Status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as RiderStatus)}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </label>

        {err && (
          <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            {err}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Link
            href="/delivery/riders"
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold  hover:bg-slate-50"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-400"
          >
            {submitting ? "Creating…" : "Create Rider"}
          </button>
        </div>
      </form>
    </div>
  );
}
