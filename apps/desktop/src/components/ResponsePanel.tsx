import { motion, AnimatePresence } from 'framer-motion';
import { useConversationStore } from '../store/conversationStore';

export function ResponsePanel() {
  const { currentState, currentTranscript, partialTranscript, aiResponse, partialResponse } = useConversationStore();

  const isVisible =
    currentState === 'LISTENING' ||
    currentState === 'TRANSCRIBING' ||
    currentState === 'THINKING' ||
    currentState === 'GENERATING_RESPONSE' ||
    currentState === 'SPEAKING';

  const getDisplayText = () => {
    if (currentState === 'LISTENING' || currentState === 'TRANSCRIBING') {
      return partialTranscript || currentTranscript || 'Listening...';
    }
    if (currentState === 'THINKING' || currentState === 'GENERATING_RESPONSE' || currentState === 'SPEAKING') {
      return partialResponse || aiResponse || 'Processing...';
    }
    if (currentState === 'FAILED') {
      return 'An error occurred.';
    }
    return '';
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="w-full max-w-2xl px-8 py-6 mt-8 rounded-xl bg-black/40 border border-white/10 backdrop-blur-md shadow-glass text-center"
        >
          <motion.p
            key={currentState}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xl font-light leading-relaxed text-gray-200"
          >
            {getDisplayText()}
          </motion.p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
