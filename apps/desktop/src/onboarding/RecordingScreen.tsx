import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEnrollmentStore } from './EnrollmentStore';
import { eventBridge } from '../events/LocalEventBridge';

export const RecordingScreen = () => {
  const phrase = useEnrollmentStore((state) => state.phrase);
  const isRecording = useEnrollmentStore((state) => state.isRecording);
  const beginRecording = useEnrollmentStore((state) => state.beginRecording);
  const stopRecording = useEnrollmentStore((state) => state.stopRecording);
  const currentSample = useEnrollmentStore((state) => state.currentSample);
  const requiredSamples = useEnrollmentStore((state) => state.requiredSamples);
  const overallProgress = useEnrollmentStore((state) => state.overallProgress);
  const recordingState = useEnrollmentStore((state) => state.recordingState);
  const rejectionReason = useEnrollmentStore((state) => state.rejectionReason);

  const [rmsLevel, setRmsLevel] = useState(0);

  useEffect(() => {
    const handleLevelChange = (payload: unknown) => {
      if (payload && typeof payload === 'object' && 'rms' in payload) {
        setRmsLevel((payload as { rms: number }).rms);
      }
    };
    eventBridge.subscribe('LEVEL_CHANGED', handleLevelChange);
    return () => {
      eventBridge.unsubscribe('LEVEL_CHANGED', handleLevelChange);
    };
  }, []);

  const getStatusMessage = () => {
    switch (recordingState) {
      case 'listening': return '🎤 Listening...';
      case 'speech_detected': return 'Voice detected ✓';
      case 'analyzing': return 'Analyzing sample...';
      case 'accepted': return 'Sample Accepted ✓';
      case 'rejected': return rejectionReason || 'Sample rejected.';
      default: return 'Ready to record';
    }
  };

  const getOrbAnimation = () => {
    if (!isRecording) return { scale: 1, opacity: 0.5 };
    const audioScaleBoost = rmsLevel * 1.5; 
    const dynamicScale = 1 + audioScaleBoost;
    return {
      scale: dynamicScale,
      opacity: 1,
      boxShadow: `0 0 ${15 + rmsLevel * 50}px rgba(59,130,246,0.8)`,
      transition: { duration: 0.05, ease: 'linear' as const }
    };
  };

  return (
    <motion.div 
      className="flex flex-col items-center justify-center h-screen w-full"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="p-10 rounded-3xl bg-white/5 border border-white/10 shadow-2xl backdrop-blur-2xl text-center max-w-2xl w-full relative overflow-hidden">
        
        <div className="mb-8 flex justify-between items-center text-sm text-white/50 px-2 pt-2">
          <span>Voice Identity</span>
          <span>Sample {currentSample + 1} of {requiredSamples}</span>
        </div>
        
        <h2 className="text-xl font-light text-white/70 mb-2">Please read the following phrase:</h2>
        <div className="py-8 min-h-[120px] flex items-center justify-center">
          <p className="text-4xl font-medium tracking-wide text-white leading-tight">"{phrase}"</p>
        </div>

        <div className="h-12 flex items-center justify-center mb-6">
          <AnimatePresence mode="wait">
            <motion.p
              key={recordingState}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`text-lg ${recordingState === 'rejected' ? 'text-red-400' : 'text-blue-300'}`}
            >
              {getStatusMessage()}
            </motion.p>
          </AnimatePresence>
        </div>

        <div className="mt-4 flex justify-center h-40 items-center relative">
          {/* Progress Ring */}
          <div className="absolute inset-0 flex justify-center items-center pointer-events-none">
            <svg width="160" height="160" className="transform -rotate-90">
              <circle cx="80" cy="80" r="70" fill="transparent" stroke="rgba(255,255,255,0.1)" strokeWidth="4" />
              <motion.circle 
                cx="80" cy="80" r="70" 
                fill="transparent" 
                stroke="#3b82f6" 
                strokeWidth="4" 
                strokeDasharray="439.8"
                initial={{ strokeDashoffset: 439.8 - (439.8 * overallProgress) / 100 }}
                animate={{ strokeDashoffset: 439.8 - (439.8 * overallProgress) / 100 }}
                transition={{ duration: 0.5 }}
              />
            </svg>
          </div>
          {!isRecording && recordingState !== 'analyzing' ? (
            <motion.button 
              onClick={beginRecording}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="w-20 h-20 bg-blue-500 hover:bg-blue-600 rounded-full flex items-center justify-center transition-colors shadow-[0_0_30px_rgba(59,130,246,0.5)] z-10"
            >
              <div className="w-8 h-8 rounded-full bg-white" />
            </motion.button>
          ) : (
            <div className="relative flex items-center justify-center w-32 h-32">
              <motion.div
                animate={getOrbAnimation()}
                className="absolute w-20 h-20 rounded-full bg-blue-500/30"
              />
              <button 
                onClick={recordingState !== 'analyzing' ? stopRecording : undefined}
                disabled={recordingState === 'analyzing'}
                className="w-20 h-20 bg-red-500/20 border-2 border-red-500 rounded-full flex items-center justify-center transition-all duration-300 z-10 hover:bg-red-500/40"
              >
                {recordingState === 'analyzing' ? (
                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <div className="w-6 h-6 rounded-sm bg-red-500" />
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
