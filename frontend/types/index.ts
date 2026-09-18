export type Shipment = {
  id: number;
  tracking_number: string;
  carrier: "DEMO_EXPRESS";
  current_status: string;
  current_location: string;
  created_at: string;
  updated_at: string;
};

export type TrackingEvent = {
  id: number;
  shipment: number;
  status: string;
  location: string;
  event_time: string;
  created_at: string;
};

export type AutomationJob = {
  id: number;
  shipment: number;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
  started_at: string | null;
  finished_at: string | null;
  error_message: string;
};
