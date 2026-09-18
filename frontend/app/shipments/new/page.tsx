"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function AddShipmentPage() {
  const router = useRouter();
  const [trackingNumber, setTrackingNumber] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const shipment = await api.createShipment({ tracking_number: trackingNumber, carrier: "DEMO_EXPRESS" });
      router.push(`/shipments/${shipment.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create shipment");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="form-page">
      <Link className="back-link" href="/">← Back to dashboard</Link>
      <div className="form-card">
        <p className="eyebrow">New shipment</p>
        <h1>Add a tracking number</h1>
        <p className="subtle">Demo Express supports VN000001, VN000002, and VN000003.</p>
        {error && <div className="alert error">{error}</div>}
        <form onSubmit={submit}>
          <label>Tracking number<input required minLength={6} value={trackingNumber} onChange={(event) => setTrackingNumber(event.target.value.toUpperCase())} placeholder="VN000001" /></label>
          <label>Carrier<select value="DEMO_EXPRESS" disabled><option value="DEMO_EXPRESS">Demo Express</option></select></label>
          <button className="button full" disabled={saving}>{saving ? "Saving…" : "Create shipment"}</button>
        </form>
      </div>
    </section>
  );
}
