"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { StatCard } from "@/components/StatCard";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Shipment } from "@/types";

export default function Dashboard() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [trackingId, setTrackingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      setError("");
      setShipments(await api.listShipments());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load shipments");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const stats = useMemo(() => ({
    total: shipments.length,
    transit: shipments.filter((item) => item.current_status === "In Transit").length,
    delivered: shipments.filter((item) => item.current_status === "Delivered").length,
    failed: shipments.filter((item) => item.current_status === "Failed").length,
  }), [shipments]);

  async function track(shipment: Shipment) {
    setTrackingId(shipment.id);
    setError("");
    try {
      await api.trackShipment(shipment.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tracking failed");
    } finally {
      setTrackingId(null);
    }
  }

  return (
    <>
      <section className="hero-row">
        <div>
          <p className="eyebrow">OPERATIONS OVERVIEW</p>
          <h1>Shipment command center</h1>
          <p className="subtle">Track every handoff from one calm, reliable workspace.</p>
        </div>
        <button className="secondary" onClick={() => void load()}>Refresh data</button>
      </section>

      <section className="stats-grid">
        <StatCard label="Total shipments" value={stats.total} tone="blue" />
        <StatCard label="In transit" value={stats.transit} tone="amber" />
        <StatCard label="Delivered" value={stats.delivered} tone="green" />
        <StatCard label="Failed" value={stats.failed} tone="red" />
      </section>

      {error && <div className="alert error">{error}</div>}
      <section className="panel">
        <div className="panel-heading">
          <div><h2>Active shipments</h2><p>Latest carrier status and location</p></div>
          <Link className="button" href="/shipments/new">Add shipment</Link>
        </div>
        {loading ? <div className="empty">Loading shipments…</div> : shipments.length === 0 ? (
          <div className="empty"><strong>No shipments yet</strong><span>Add a demo tracking number such as VN000001.</span></div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Tracking number</th><th>Carrier</th><th>Status</th><th>Current location</th><th>Last updated</th><th>Actions</th></tr></thead>
              <tbody>{shipments.map((shipment) => (
                <tr key={shipment.id}>
                  <td><Link className="tracking-link" href={`/shipments/${shipment.id}`}>{shipment.tracking_number}</Link></td>
                  <td>Demo Express</td>
                  <td><StatusBadge status={shipment.current_status} /></td>
                  <td>{shipment.current_location || "—"}</td>
                  <td>{new Date(shipment.updated_at).toLocaleString()}</td>
                  <td className="actions"><button disabled={trackingId === shipment.id} onClick={() => void track(shipment)}>{trackingId === shipment.id ? "Tracking…" : "Track"}</button><Link href={`/shipments/${shipment.id}`}>Details</Link></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
