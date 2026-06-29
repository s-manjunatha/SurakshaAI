const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface ApiError {
  detail: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("surakshai_token", token);
      else localStorage.removeItem("surakshai_token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("surakshai_token");
    }
    return this.token;
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    if (res.status === 401) {
      this.setToken(null);
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
      throw new Error("Unauthorized");
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }

    const contentType = res.headers.get("content-type");
    if (contentType?.includes("application/pdf")) {
      return res.blob() as unknown as T;
    }
    return res.json();
  }

  get<T>(path: string) {
    return this.request<T>(path);
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
  }

  patch<T>(path: string, body?: unknown) {
    return this.request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined });
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: "DELETE" });
  }

  async upload<T>(path: string, formData: FormData) {
    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: formData });
    if (!res.ok) throw new Error("Upload failed");
    return res.json() as Promise<T>;
  }
}

export const api = new ApiClient();

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
  badge_number?: string;
}

export interface DashboardStats {
  total_firs: number;
  solved_cases: number;
  active_investigations: number;
  high_priority: number;
  last_30_days: number;
  repeat_offenders: number;
  unread_alerts: number;
}

export interface FIR {
  id: string;
  fir_number: string;
  crime_type: string;
  status: string;
  priority: string;
  title: string;
  description: string;
  incident_date: string;
  is_solved: boolean;
  district?: string;
  station_name?: string;
  latitude?: number;
  longitude?: number;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  confidence: number;
  sources: { type: string; id: string; title: string; relevance: number }[];
  actions: { type: string; label: string; resource_id?: string }[];
  structured_data?: Record<string, unknown>;
  sql_query?: string;
}

export interface Alert {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  district?: string;
  is_read: boolean;
  created_at: string;
}

export interface Criminal {
  id: string;
  name: string;
  alias?: string;
  age?: number;
  gender?: string;
  risk_score: number;
  is_repeat_offender: boolean;
  district?: string;
}
