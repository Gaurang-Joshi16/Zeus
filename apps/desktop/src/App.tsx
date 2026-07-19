import { OverlayContainer } from './components/OverlayContainer';
import { StatusIndicator } from './components/StatusIndicator';
import { VoiceOrb } from './components/VoiceOrb';
import { ResponsePanel } from './components/ResponsePanel';
import { RuntimePanel } from './components/RuntimePanel';
import { useEffect, useState } from 'react';
import { EnrollmentWizard } from './onboarding/EnrollmentWizard';
import { useEnrollmentStore } from './onboarding/EnrollmentStore';
import { useRuntimeStore } from './store/runtimeStore';
import { useConversationStore } from './store/conversationStore';
import { eventBridge } from './events/LocalEventBridge';

function App() {
  const [isEnrolling, setIsEnrolling] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const enrollmentStage = useEnrollmentStore((state) => state.stage);
  const { updateStatus, togglePanel } = useRuntimeStore();

  useEffect(() => {
    // Debug Tauri injection
    console.log('[Zeus UI] Window Tauri internals:', (window as any).__TAURI_INTERNALS__);
    console.log('[Zeus UI] Window Tauri IPC:', (window as any).__TAURI_IPC__);
    console.log('[Zeus UI] Window Tauri core:', (window as any).__TAURI__);
  }, []);

  useEffect(() => {
    // Track backend WebSocket connectivity
    const unsubConnect = eventBridge.subscribe('WS_CONNECTED', () => {
      console.log('[Zeus UI] Backend connected');
      setBackendConnected(true);
      // Fetch complete application state
      eventBridge.invoke('GET_APP_STATE').then((appState: any) => {
        if (appState) {
          if (appState.runtimeStatus) {
            updateStatus(appState.runtimeStatus);
          }
          if (appState.setupState === 'OWNER_NOT_FOUND') {
            setIsEnrolling(true);
          } else {
            setIsEnrolling(false);
          }
          if (appState.activeConversation) {
            const { setState, updateTranscript, updateAIResponse } = useConversationStore.getState();
            setState(appState.activeConversation.state as any, appState.activeConversation.id);
            if (appState.activeConversation.transcript) {
              updateTranscript(appState.activeConversation.transcript, appState.activeConversation.transcript);
            }
            if (appState.activeConversation.response) {
              updateAIResponse(appState.activeConversation.response, appState.activeConversation.response);
            }
          }
        }
      }).catch(console.error);
    });
    
    const unsubDisconnect = eventBridge.subscribe('WS_DISCONNECTED', () => {
      setBackendConnected(false);
    });

    const unsubRuntimeUpdate = eventBridge.subscribe('RUNTIME_UPDATE', (payload: any) => {
      if (payload) updateStatus(payload);
    });

    // Listen for OWNER_NOT_FOUND from backend to trigger enrollment.
    const unsubOwnerNotFound = eventBridge.subscribe('OWNER_NOT_FOUND', () => {
      console.log('[Zeus UI] OWNER_NOT_FOUND received — launching enrollment wizard');
      setIsEnrolling(true);
    });

    const unsubOwnerReady = eventBridge.subscribe('OWNER_READY', () => {
      console.log('[Zeus UI] OWNER_READY received — waiting for completion screen delay');
    });

    const unsubEnrolling = eventBridge.subscribe('ENROLLMENT', () => {
      console.log('[Zeus UI] ENROLLMENT state sync received');
      setIsEnrolling(true);
    });

    // Conversation state event subscriptions
    const { setState: setConversationState, updateTranscript, updateStats, updateAIResponse, microphoneLevel, recordingDuration } = useConversationStore.getState();

    const handleConvState = (state: string) => (payload: any) => {
      const convId = payload?.conversationId || null;
      setConversationState(state as any, convId);
    };

    const unsubCStart = eventBridge.subscribe('CONVERSATION_STARTED', handleConvState('IDLE')); // Starts as IDLE or we can just ignore as WAKEWORD comes right after
    const unsubWW = eventBridge.subscribe('WAKEWORD_DETECTED', handleConvState('WAKE_WORD_DETECTED'));
    const unsubSVStart = eventBridge.subscribe('SPEAKER_VERIFICATION_STARTED', handleConvState('VERIFYING_SPEAKER'));
    const unsubLStart = eventBridge.subscribe('LISTENING_STARTED', handleConvState('LISTENING'));
    const unsubTStart = eventBridge.subscribe('TRANSCRIPTION_STARTED', handleConvState('TRANSCRIBING'));
    const unsubAIStart = eventBridge.subscribe('AI_PROCESSING_STARTED', handleConvState('THINKING'));
    const unsubRGStart = eventBridge.subscribe('RESPONSE_GENERATION_STARTED', handleConvState('GENERATING_RESPONSE'));
    const unsubSStart = eventBridge.subscribe('SPEAKING_STARTED', handleConvState('SPEAKING'));
    const unsubSComp = eventBridge.subscribe('SPEAKING_COMPLETED', handleConvState('IDLE'));
    
    const unsubCInt = eventBridge.subscribe('CONVERSATION_INTERRUPTED', handleConvState('INTERRUPTED'));
    const unsubCTime = eventBridge.subscribe('CONVERSATION_TIMEOUT', handleConvState('TIMEOUT'));
    const unsubCFail = eventBridge.subscribe('CONVERSATION_FAILED', handleConvState('FAILED'));
    const unsubCComp = eventBridge.subscribe('CONVERSATION_COMPLETED', handleConvState('COMPLETED'));
    
    const unsubTPartial = eventBridge.subscribe('TRANSCRIPTION_PARTIAL', (payload: any) => {
      updateTranscript(payload.text);
    });

    const unsubTComp = eventBridge.subscribe('TRANSCRIPTION_COMPLETED', (payload: any) => {
      updateTranscript(payload.text, payload.text, payload.confidence, payload.processingTime);
    });

    const unsubVadStart = eventBridge.subscribe('VAD_SPEECH_STARTED', () => {
      updateStats(useConversationStore.getState().recordingDuration, 'SPEECH_DETECTED', useConversationStore.getState().microphoneLevel);
    });

    const unsubVadEnd = eventBridge.subscribe('VAD_SPEECH_ENDED', (payload: any) => {
      updateStats(payload.duration_ms, 'SILENCE', useConversationStore.getState().microphoneLevel);
    });

    const unsubVoiceState = eventBridge.subscribe('VOICE_STATE_CHANGED', (payload: any) => {
      console.log(`[STATE TRANSITION] ${useConversationStore.getState().voiceState} -> ${payload?.state}`);
      if (payload?.state) {
        useConversationStore.getState().setVoiceState(payload.state);
      }
    });

    const unsubLevel = eventBridge.subscribe('LEVEL_CHANGED', (payload: any) => {
      if (payload && typeof payload === 'object' && 'rms' in payload) {
        updateStats(useConversationStore.getState().recordingDuration, useConversationStore.getState().vadState, (payload as any).rms);
      }
    });

    const unsubAIDelta = eventBridge.subscribe('AI_STREAM_DELTA', (payload: any) => {
      updateAIResponse(
        useConversationStore.getState().partialResponse + (payload.delta || ''),
        undefined,
        payload.provider
      );
    });

    const unsubAIComp = eventBridge.subscribe('AI_PROCESSING_COMPLETED', (payload: any) => {
      updateAIResponse(
        payload.response,
        payload.response,
        payload.provider,
        payload.processingTime,
        payload.tokenUsage
      );
    });

    const unsubAIFail = eventBridge.subscribe('AI_PROCESSING_FAILED', (payload: any) => {
      updateAIResponse(
        `[Error: ${payload.error}]`,
        `[Error: ${payload.error}]`,
        payload.provider
      );
    });

    return () => {
      unsubConnect();
      unsubDisconnect();
      unsubRuntimeUpdate();
      unsubOwnerNotFound();
      unsubOwnerReady();
      unsubEnrolling();
      unsubCStart();
      unsubWW();
      unsubSVStart();
      unsubLStart();
      unsubTStart();
      unsubAIStart();
      unsubRGStart();
      unsubSStart();
      unsubSComp();
      unsubCInt();
      unsubCTime();
      unsubCFail();
      unsubCComp();
      unsubTPartial();
      unsubTComp();
      unsubVadStart();
      unsubVadEnd();
      unsubVoiceState();
      unsubLevel();
      unsubAIDelta();
      unsubAIComp();
      unsubAIFail();
    };
  }, []);

  // After enrollment completes, dismiss wizard after 3 seconds
  useEffect(() => {
    if (enrollmentStage === 'completed') {
      const timer = setTimeout(() => {
        setIsEnrolling(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [enrollmentStage]);

  // State 1: Enrollment mode
  if (isEnrolling) {
    return <EnrollmentWizard />;
  }

  // State 2: Waiting for backend connection
  if (!backendConnected) {
    return (
      <div className="flex flex-col items-center justify-center w-full h-screen text-white bg-gradient-to-br from-slate-900 via-[#0a0a0a] to-blue-900/20 font-sans">
        <div className="p-12 rounded-3xl bg-white/5 border border-white/10 shadow-2xl backdrop-blur-xl text-center max-w-md">
          <div className="w-12 h-12 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
          <h2 className="text-2xl font-light mb-2">Connecting to Zeus</h2>
          <p className="text-sm text-white/50">Waiting for the backend runtime...</p>
        </div>
      </div>
    );
  }

  // State 3: Normal assistant overlay
  return (
    <main className="w-full h-full min-h-screen text-white bg-transparent selection:bg-zeus-cyan/30 overflow-hidden font-sans">
      <OverlayContainer>
        <StatusIndicator />

        <div className="flex flex-col items-center justify-center flex-1 w-full">
          <VoiceOrb />
          <ResponsePanel />
        </div>

        <div className="absolute top-4 right-4 z-40">
          <button 
            onClick={togglePanel}
            className="text-xs font-mono text-gray-500 hover:text-cyan-400 transition-colors border border-gray-800 hover:border-cyan-500/50 bg-black/50 px-2 py-1 rounded"
          >
            [DEV: RUNTIME]
          </button>
        </div>
        
        <RuntimePanel />

        <div className="w-full px-6 py-4 text-center">
          <p className="text-xs text-gray-500">
            Press{' '}
            <kbd className="px-2 py-1 mx-1 bg-white/10 rounded">
              Ctrl+Shift+Space
            </kbd>{' '}
            to toggle
          </p>
        </div>
      </OverlayContainer>
    </main>
  );
}

export default App;
