import { create } from 'zustand';

export const OverlayState = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  THINKING: 'THINKING',
  RESPONDING: 'RESPONDING',
  ERROR: 'ERROR',
  LOADING: 'LOADING',
} as const;

export type OverlayState = (typeof OverlayState)[keyof typeof OverlayState];

interface OverlayStore {
  isVisible: boolean;
  currentState: OverlayState;

  voiceStatus: string;
  aiStatus: string;

  setVisible: (visible: boolean) => void;
  setState: (state: OverlayState) => void;
}

export const useOverlayStore = create<OverlayStore>((set) => ({
  isVisible: false,
  currentState: OverlayState.IDLE,
  voiceStatus: 'disconnected',
  aiStatus: 'offline',

  setVisible: (visible) => set({ isVisible: visible }),
  setState: (state) => set({ currentState: state }),
}));
