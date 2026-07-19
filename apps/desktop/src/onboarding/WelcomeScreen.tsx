import { motion } from 'framer-motion';
import { useEnrollmentStore } from './EnrollmentStore';

export const WelcomeScreen = () => {
  const startEnrollment = useEnrollmentStore((state) => state.startEnrollment);
  const error = useEnrollmentStore((state) => state.error);

  const handleStart = () => {
    console.log('[Zeus UI] Begin Enrollment clicked');
    startEnrollment();
  };

  return (
    <motion.div 
      className="flex flex-col items-center justify-center h-screen bg-black/40 backdrop-blur-md text-white"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <div className="p-12 rounded-3xl bg-white/5 border border-white/10 shadow-2xl backdrop-blur-xl text-center max-w-lg">
        <h1 className="text-4xl font-light mb-4">Hello.</h1>
        <p className="text-lg text-white/70 mb-10">I need to learn your voice to build a secure identity.</p>
        
        {error && (
          <div className="mb-6 p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm">
            {error}
          </div>
        )}
        
        <button 
          onClick={handleStart}
          className="px-8 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.1)]"
        >
          Begin Enrollment
        </button>
      </div>
    </motion.div>
  );
};
