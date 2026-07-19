import { useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useEnrollmentStore } from './EnrollmentStore';
import { WelcomeScreen } from './WelcomeScreen';
import { RecordingScreen } from './RecordingScreen';
import { CompletionScreen } from './CompletionScreen';

export const EnrollmentWizard = () => {
  const stage = useEnrollmentStore((state) => state.stage);
  const initializeListeners = useEnrollmentStore((state) => state.initializeListeners);

  useEffect(() => {
    return initializeListeners();
  }, [initializeListeners]);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden font-sans">
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-[#0a0a0a] to-blue-900/20" />
      
      <div className="relative z-10 w-full h-full flex items-center justify-center">
        <AnimatePresence mode="wait">
          {stage === 'welcome' && <WelcomeScreen key="welcome" />}
          {stage === 'mic_check' && <RecordingScreen key="mic_check" />}
          {stage === 'recording' && <RecordingScreen key="recording" />}
          {stage === 'completed' && <CompletionScreen key="completed" />}
        </AnimatePresence>
      </div>
    </div>
  );
};
