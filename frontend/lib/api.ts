import type { AutomationJob, Shipment, TrackingEvent } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

function errorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const data = payload as Record<string, unknown>;
  if (typeof data.detail === "string") return data.detail;
  if (typeof data.error_message === "string") return data.error_message;
  for (const [field, value] of Object.entries(data)) {
    const message = Array.isArray(value) ? value[0] : value;
    if (typeof message === "string") {
      const label = field.replaceAll("_", " ");
      return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${message}`;
    }
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => null);
    throw new Error(errorMessage(detail, `Request failed (${response.status})`));
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
