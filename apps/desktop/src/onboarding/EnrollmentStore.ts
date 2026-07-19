import { create } from 'zustand';
import { EnrollmentService } from './EnrollmentService';
import { eventBridge } from '../events/LocalEventBridge';

interface EnrollmentState {
  stage: 'welcome' | 'mic_check' | 'recording' | 'completed';
  recordingState: 'idle' | 'listening' | 'speech_detected' | 'analyzing' | 'accepted' | 'rejected';
  rejectionReason: string | null;
  phrase: string;
  currentSample: number;
  requiredSamples: number;
  overallProgress: number;
  estimatedRemainingTime: number;
  isRecording: boolean;
  error: string | null;
  
  setStage: (stage: EnrollmentState['stage']) => void;
  startEnrollment: () => Promise<void>;
  beginRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  initializeListeners: () => () => void;
}

export const useEnrollmentStore = create<EnrollmentState>((set) => ({
  stage: 'welcome',
  recordingState: 'idle',
  rejectionReason: null,
  phrase: '',
  currentSample: 0,
  requiredSamples: 10,
  overallProgress: 0,
  estimatedRemainingTime: 0,
  isRecording: false,
  error: null,

  setStage: (stage) => set({ stage }),
  
  startEnrollment: async () => {
    try {
      console.log('[Zeus UI] startEnrollment() called');
      set({ error: null });
      await EnrollmentService.startEnrollment();
      // State transition happens via ENROLLMENT_STARTED event from backend
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error starting enrollment';
      console.error('[Zeus UI] startEnrollment failed:', msg);
      set({ error: msg });
    }
  },
  
  beginRecording: async () => {
    try {
      set({ error: null, rejectionReason: null });
      await EnrollmentService.beginRecording();
      // State transition happens via ENROLLMENT_RECORDING_STARTED event
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error starting recording';
      console.error('[Zeus UI] beginRecording failed:', msg);
      set({ error: msg });
    }
  },
  
  stopRecording: async () => {
    try {
      set({ recordingState: 'analyzing', error: null });
      await EnrollmentService.stopRecording();
      // State transition happens via sample accepted/rejected events
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Unknown error stopping recording';
      console.error('[Zeus UI] stopRecording failed:', msg);
      set({ error: msg, recordingState: 'idle', isRecording: false });
    }
  },

  initializeListeners: () => {
    const unsubs: Array<() => void> = [];

    unsubs.push(eventBridge.subscribe('ENROLLMENT_STARTED', (p: unknown) => {
      const payload = p as { phrase: string; current_sample: number; required_samples: number };
      console.log('[Zeus UI] ENROLLMENT_STARTED event received', payload);
      set({ 
        stage: 'mic_check',
        phrase: payload?.phrase || '',
        currentSample: payload?.current_sample || 0,
        requiredSamples: payload?.required_samples || 10,
        error: null,
      });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_RECORDING_STARTED', () => {
      set({ isRecording: true, recordingState: 'listening', rejectionReason: null });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_SPEECH_DETECTED', () => {
      set({ recordingState: 'speech_detected' });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_SAMPLE_ACCEPTED', (p: unknown) => {
      const payload = p as { sample_number: number; total_required: number; progress_percentage: number; estimated_remaining_time: number };
      set({ 
        recordingState: 'accepted',
        currentSample: payload?.sample_number || 0,
        requiredSamples: payload?.total_required || 10,
        overallProgress: payload?.progress_percentage || 0,
        estimatedRemainingTime: payload?.estimated_remaining_time || 0,
        isRecording: false,
      });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_SAMPLE_REJECTED', (p: unknown) => {
      let friendlyMessage = 'Please try again.';
      const payload = p as { reason: string };
      const reason = payload?.reason;
      if (reason === 'MICROPHONE_TOO_QUIET') friendlyMessage = 'Speak a little louder.';
      else if (reason === 'NO_SPEECH_DETECTED') friendlyMessage = 'No speech detected. Please try again.';
      else if (reason === 'TOO_MUCH_BACKGROUND_NOISE') friendlyMessage = "Too much background noise. Let's record that phrase again.";
      else if (reason === 'AUDIO_CLIPPING') friendlyMessage = 'Audio clipping detected. Try speaking a bit softer.';
      else if (reason === 'RECORDING_TOO_SHORT') friendlyMessage = 'Recording too short. Please speak the entire phrase.';
      else if (reason === 'RECORDING_TOO_LONG') friendlyMessage = 'Recording too long. Please speak clearly.';
      else if (reason === 'CONFIDENCE_TOO_LOW') friendlyMessage = 'Voice mismatch detected. Please speak clearly in your own voice.';
      
      set({ recordingState: 'rejected', rejectionReason: friendlyMessage, isRecording: false });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_NEXT_PHRASE', (p: unknown) => {
      const payload = p as { current_phrase: string };
      set({ 
        phrase: payload?.current_phrase || '',
        recordingState: 'idle',
        isRecording: false,
        stage: 'recording',
      });
    }));

    unsubs.push(eventBridge.subscribe('ENROLLMENT_PROGRESS_UPDATED', (p: unknown) => {
      const payload = p as { accepted_samples: number; required_samples: number; completion_percentage: number; estimated_remaining_time: number };
      set({
        currentSample: payload?.accepted_samples || 0,
        requiredSamples: payload?.required_samples || 10,
        overallProgress: payload?.completion_percentage || 0,
        estimatedRemainingTime: payload?.estimated_remaining_time || 0,
      });
    }));

    unsubs.push(eventBridge.subscribe('OWNER_PROFILE_CREATED', () => {
      // Profile created — waiting for verification sample
    }));

    unsubs.push(eventBridge.subscribe('OWNER_VERIFICATION_FAILED', () => {
      set({ 
        recordingState: 'rejected', 
        rejectionReason: 'Verification failed. Please try saying the phrase again.', 
        isRecording: false, 
      });
    }));

    unsubs.push(eventBridge.subscribe('OWNER_READY', () => {
      set({ stage: 'completed' });
    }));

    return () => {
      unsubs.forEach(unsub => unsub());
    };
  }
}));
