import { motion } from 'framer-motion';
import { useOverlayStore } from '../store/overlayStore';
import { useConversationStore } from '../store/conversationStore';

export function StatusIndicator() {
  const { voiceStatus, aiStatus } = useOverlayStore();
  const { currentState: convState } = useConversationStore();

  const getDisplayText = () => {
    switch(convState) {
      case 'WAKE_WORD_DETECTED': return 'Wake Word Detected';
      case 'VERIFYING_SPEAKER': return 'Verifying Speaker...';
      case 'LISTENING': return 'Listening...';
      case 'TRANSCRIBING': return 'Transcribing...';
      case 'THINKING': return 'Thinking...';
      case 'GENERATING_RESPONSE': return 'Generating Response...';
      case 'SPEAKING': return 'Speaking...';
      case 'INTERRUPTED': return 'Interrupted';
      case 'TIMEOUT': return 'Timeout';
      case 'FAILED': return 'Failed';
      case 'COMPLETED': return 'Completed';
      case 'IDLE':
      default: return 'Ready';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-row items-center justify-between w-full px-6 py-4"
    >
      <div className="flex flex-col">
        <span className="text-sm font-bold tracking-widest text-zeus-cyan uppercase">
          ZEUS Core
        </span>
        <span className="text-xs text-gray-400">State: {getDisplayText()}</span>
      </div>

      <div className="flex flex-row gap-4">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${voiceStatus === 'connected' ? 'bg-green-400' : 'bg-gray-500'}`}
          />
          <span className="text-xs text-gray-400">Voice: {voiceStatus}</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${aiStatus === 'online' ? 'bg-zeus-cyan' : 'bg-gray-500'}`}
          />
          <span className="text-xs text-gray-400">AI: {aiStatus}</span>
        </div>
      </div>
    </motion.div>
  );
}
