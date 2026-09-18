"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { StatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import type { Shipment, TrackingEvent } from "@/types";

export default function ShipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [events, setEvents] = useState<TrackingEvent[]>([]);
  const [error, setError] = useState("");
  const [tracking, setTracking] = useState(false);

  const load = useCallback(async () => {
    try {
      const [shipmentData, eventData] = await Promise.all([api.getShipment(params.id), api.getEvents(params.id)]);
      setShipment(shipmentData);
      setEvents(eventData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load shipment");
    }
  }, [params.id]);

  useEffect(() => { void load(); }, [load]);

  async function track() {
    setTracking(true);
    setError("");
    try { await api.trackShipment(params.id); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : "Tracking failed"); }
    finally { setTracking(false); }
  }

  if (!shipment) return <div className="empty">{error || "Loading shipment…"}</div>;

  return (
    <>
      <Link className="back-link" href="/">← Back to dashboard</Link>
      {error && <div className="alert error">{error}</div>}
      <section className="detail-hero">
        <div><p className="eyebrow">DEMO EXPRESS</p><h1>{shipment.tracking_number}</h1><StatusBadge status={shipment.current_status} /></div>
        <button className="button" onClick={() => void track()} disabled={tracking}>{tracking ? "Tracking…" : "Run tracking"}</button>
      </section>
      <section className="detail-grid">
        <article><span>Current location</span><strong>{shipment.current_location || "Waiting for first scan"}</strong></article>
        <article><span>Carrier</span><strong>Demo Express</strong></article>
        <article><span>Last updated</span><strong>{new Date(shipment.updated_at).toLocaleString()}</strong></article>
      </section>
      <section className="panel timeline-panel"><div className="panel-heading"><div><h2>Tracking history</h2><p>Every status recorded by the automation service</p></div></div>
        {events.length === 0 ? <div className="empty">No tracking events yet.</div> : <ol className="timeline">{events.map((event) => <li key={event.id}><span className="timeline-dot" /><div><StatusBadge status={event.status} /><h3>{event.location || "Location unavailable"}</h3><p>{new Date(event.event_time).toLocaleString()}</p></div></li>)}</ol>}
      </section>
    </>
  );
}
