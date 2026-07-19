import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useOverlayStore, OverlayState } from '../store/overlayStore';
import { useRuntimeStore } from '../store/runtimeStore';
import { useConversationStore } from '../store/conversationStore';
import { eventBridge } from '../events/LocalEventBridge';

export function VoiceOrb() {
  const { voiceState, currentState: convState } = useConversationStore();
  const { services } = useRuntimeStore();
  const [level, setLevel] = useState(0);

  useEffect(() => {
    const handleLevelChange = (payload: unknown) => {
      if (payload && typeof payload === 'object' && 'rms' in payload) {
        setLevel((payload as { rms: number }).rms);
      }
    };

    eventBridge.subscribe('LEVEL_CHANGED', handleLevelChange);
    return () => {
      eventBridge.unsubscribe('LEVEL_CHANGED', handleLevelChange);
    };
  }, []);

  const getOrbAnimation = () => {
    const audioScaleBoost = level * 1.5; 
    const dynamicScale = 1 + audioScaleBoost;
    const glowIntensity = Math.min(0.3 + level * 2, 1);

    const hasFailedServices = Object.values(services).some(s => s.status === 'FAILED');
    const hasBootingServices = Object.values(services).some(s => s.status === 'UNINITIALIZED' || s.status === 'INITIALIZING');

    if (hasFailedServices || convState === 'FAILED') {
      return {
        scale: 1,
        boxShadow: '0 0 20px rgba(239,68,68,0.8)',
        backgroundColor: 'rgba(239,68,68,1)',
        transition: { duration: 0.3 }
      };
    }

    if (hasBootingServices || Object.keys(services).length === 0) {
      return {
        scale: [1, 1.1, 1],
        boxShadow: [
          '0 0 15px rgba(234,179,8,0.5)',
          '0 0 25px rgba(234,179,8,0.8)',
          '0 0 15px rgba(234,179,8,0.5)',
        ],
        backgroundColor: 'rgba(234,179,8,1)',
        transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' as const }
      };
    }

    switch (voiceState) {
      case 'WAKE_WORD_LISTENING':
        return {
          scale: 1.05,
          boxShadow: '0 0 25px rgba(6,182,212,0.6)',
          backgroundColor: 'rgba(6,182,212,1)',
          transition: { duration: 0.3 }
        };
      case 'WAKE_WORD_DETECTED':
        return {
          scale: [1, 1.3, 1.1],
          boxShadow: [
            '0 0 15px rgba(59,130,246,0.5)',
            '0 0 40px rgba(59,130,246,1)',
            '0 0 20px rgba(59,130,246,0.8)'
          ],
          backgroundColor: 'rgba(59,130,246,1)',
          transition: { duration: 0.4 }
        };
      case 'LISTENING':
        return {
          scale: dynamicScale,
          boxShadow: `0 0 ${15 + level * 50}px rgba(6,182,212,${glowIntensity})`,
          backgroundColor: 'rgba(6,182,212,1)',
          transition: { duration: 0.05, ease: 'linear' as const }
        };
      case 'PROCESSING':
        return {
          scale: 1,
          rotate: [0, 360],
          borderRadius: ['50%', '30%', '50%'],
          boxShadow: '0 0 20px rgba(139,92,246,0.7)',
          backgroundColor: 'rgba(139,92,246,1)',
          transition: { duration: 2, repeat: Infinity, ease: 'linear' as const }
        };
      case 'SPEAKING':
        return {
          scale: [1, 1.15, 1],
          boxShadow: [
            '0 0 15px rgba(34,197,94,0.5)',
            '0 0 35px rgba(34,197,94,0.8)',
            '0 0 15px rgba(34,197,94,0.5)',
          ],
          backgroundColor: 'rgba(34,197,94,1)',
          transition: { duration: 1, repeat: Infinity }
        };
      case 'ERROR':
        return {
          scale: [1, 1.2, 1],
          boxShadow: [
            '0 0 15px rgba(249,115,22,0.5)',
            '0 0 30px rgba(249,115,22,0.9)',
            '0 0 15px rgba(249,115,22,0.5)'
          ],
          backgroundColor: 'rgba(249,115,22,1)',
          transition: { duration: 0.5, repeat: Infinity }
        };
      case 'IDLE':
      default:
        // Slow breathing animation (pulse every 2-3 seconds)
        return {
          scale: [1, 1.05, 1],
          boxShadow: [
            '0 0 10px rgba(6,182,212,0.2)',
            '0 0 20px rgba(6,182,212,0.4)',
            '0 0 10px rgba(6,182,212,0.2)'
          ],
          backgroundColor: 'rgba(6,182,212,0.8)',
          transition: { duration: 2.5, repeat: Infinity, ease: 'easeInOut' as const },
        };
    }
  };

  return (
    <div className="flex items-center justify-center w-48 h-48">
      <motion.div
        animate={getOrbAnimation()}
        className="w-24 h-24 rounded-full bg-zeus-cyan"
      />
    </div>
  );
}
