import type { AutomationJob, Shipment, TrackingEvent } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.error_message || detail.detail || JSON.stringify(detail) || "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  listShipments: () => request<Shipment[]>("/shipments/"),
  getShipment: (id: string) => request<Shipment>(`/shipments/${id}/`),
  createShipment: (payload: { tracking_number: string; carrier: string }) =>
    request<Shipment>("/shipments/", { method: "POST", body: JSON.stringify(payload) }),
  trackShipment: (id: number | string) => request<AutomationJob>(`/shipments/${id}/track/`, { method: "POST" }),
  getEvents: (id: string) => request<TrackingEvent[]>(`/shipments/${id}/events/`),
};
