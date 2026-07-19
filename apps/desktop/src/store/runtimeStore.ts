import { create } from 'zustand';

export type ServiceState =
  | 'UNINITIALIZED'
  | 'INITIALIZING'
  | 'READY'
  | 'BUSY'
  | 'DEGRADED'
  | 'FAILED'
  | 'STOPPED';

export interface RuntimeServiceHealth {
  name: string;
  status: ServiceState;
  uptime: number;
  lastHeartbeat: number | null;
  lastError: string | null;
  dependencies: string[];
  startupDuration: number | null;
  recoveryCount: number;
  critical: boolean;
  [key: string]: any;
}

export interface RuntimeEvent {
  timestamp: number;
  service: string;
  eventType: string;
  previousState: string;
  currentState: string;
  details?: Record<string, any>;
}

export interface RuntimeState {
  services: Record<string, RuntimeServiceHealth>;
  events: RuntimeEvent[];
  isPanelOpen: boolean;
  
  updateStatus: (payload: { services: Record<string, RuntimeServiceHealth>; events: RuntimeEvent[] }) => void;
  togglePanel: () => void;
}

export const useRuntimeStore = create<RuntimeState>((set) => ({
  services: {},
  events: [],
  isPanelOpen: false,

  updateStatus: (payload) => set({
    services: payload.services,
    events: payload.events,
  }),
  
  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),
}));
