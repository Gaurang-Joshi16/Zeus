import { create } from 'zustand';

export type ConversationState =
  | 'IDLE'
  | 'WAKE_WORD_DETECTED'
  | 'VERIFYING_SPEAKER'
  | 'LISTENING'
  | 'TRANSCRIBING'
  | 'THINKING'
  | 'GENERATING_RESPONSE'
  | 'SPEAKING'
  | 'COMPLETED'
  | 'INTERRUPTED'
  | 'FAILED'
  | 'TIMEOUT';

export type VoiceState =
  | 'IDLE'
  | 'WAKE_WORD_LISTENING'
  | 'WAKE_WORD_DETECTED'
  | 'LISTENING'
  | 'PROCESSING'
  | 'SPEAKING'
  | 'ERROR';

export interface ConversationStore {
  currentState: ConversationState;
  voiceState: VoiceState;
  conversationId: string | null;
  lastUpdate: number;
  currentTranscript: string;
  partialTranscript: string;
  confidence: number;
  recordingDuration: number;
  vadState: string;
  microphoneLevel: number;
  processingTime: number;

  aiResponse: string;
  partialResponse: string;
  provider: string;
  llmProcessingTime: number;
  tokenUsage: number;

  setState: (state: ConversationState, id: string | null) => void;
  setVoiceState: (state: VoiceState) => void;
  updateTranscript: (partial: string, final?: string, confidence?: number, time?: number) => void;
  updateStats: (recordingDuration: number, vadState: string, micLevel: number) => void;
  updateAIResponse: (partial: string, final?: string, provider?: string, llmTime?: number, tokens?: number) => void;
  reset: () => void;
}

export const useConversationStore = create<ConversationStore>((set) => ({
  currentState: 'IDLE',
  voiceState: 'IDLE',
  conversationId: null,
  lastUpdate: Date.now(),
  currentTranscript: '',
  partialTranscript: '',
  confidence: 0,
  recordingDuration: 0,
  vadState: 'SILENCE',
  microphoneLevel: 0,
  processingTime: 0,
  aiResponse: '',
  partialResponse: '',
  provider: '',
  llmProcessingTime: 0,
  tokenUsage: 0,
  
  setState: (state, id) => set({
    currentState: state,
    ...(id !== null && { conversationId: id }),
    lastUpdate: Date.now(),
  }),

  setVoiceState: (state) => set({
    voiceState: state,
    lastUpdate: Date.now(),
  }),

  updateTranscript: (partial, final, confidence, time) => set((state) => ({
    partialTranscript: partial,
    ...(final !== undefined && { currentTranscript: final }),
    ...(confidence !== undefined && { confidence }),
    ...(time !== undefined && { processingTime: time }),
    lastUpdate: Date.now(),
  })),

  updateAIResponse: (partial, final, provider, llmTime, tokens) => set((state) => ({
    partialResponse: partial,
    ...(final !== undefined && { aiResponse: final }),
    ...(provider !== undefined && { provider }),
    ...(llmTime !== undefined && { llmProcessingTime: llmTime }),
    ...(tokens !== undefined && { tokenUsage: tokens }),
    lastUpdate: Date.now(),
  })),

  updateStats: (recordingDuration, vadState, micLevel) => set({
    recordingDuration,
    vadState,
    microphoneLevel: micLevel,
    lastUpdate: Date.now(),
  }),
  
  reset: () => set({
    currentState: 'IDLE',
    voiceState: 'IDLE',
    conversationId: null,
    currentTranscript: '',
    partialTranscript: '',
    confidence: 0,
    recordingDuration: 0,
    vadState: 'SILENCE',
    microphoneLevel: 0,
    processingTime: 0,
    aiResponse: '',
    partialResponse: '',
    provider: '',
    llmProcessingTime: 0,
    tokenUsage: 0,
    lastUpdate: Date.now(),
  }),
}));
