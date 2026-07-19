
import { motion } from 'framer-motion';

export const CompletionScreen = () => {
  return (
    <motion.div 
      className="flex flex-col items-center justify-center h-screen w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 1 } }}
    >
      <motion.div 
        className="p-12 rounded-[2rem] bg-white/10 border border-white/20 shadow-[0_0_50px_rgba(16,185,129,0.3)] backdrop-blur-2xl text-center max-w-lg relative overflow-hidden"
        initial={{ scale: 0.9, y: 30 }}
        animate={{ scale: 1, y: 0 }}
        transition={{ type: "spring", damping: 20, stiffness: 100 }}
      >
        {/* Dynamic background glow */}
        <div className="absolute inset-0 bg-gradient-to-tr from-green-500/10 to-blue-500/10 opacity-50" />
        
        <div className="relative z-10 flex flex-col items-center">
          <motion.div 
            className="w-28 h-28 bg-green-500/20 border-2 border-green-400 rounded-full mb-8 flex items-center justify-center text-green-400 shadow-[0_0_30px_rgba(74,222,128,0.5)]"
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", damping: 15, stiffness: 200, delay: 0.2 }}
          >
            <svg className="w-14 h-14" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <motion.path 
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.8, delay: 0.6 }}
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2.5} 
                d="M5 13l4 4L19 7" 
              />
            </svg>
          </motion.div>
          
          <motion.h1 
            className="text-4xl font-light mb-4 text-white"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            Voice successfully enrolled.
          </motion.h1>
          
          <motion.p 
            className="text-xl text-white/80 font-light"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            Welcome to Zeus.
          </motion.p>
        </div>
      </motion.div>
    </motion.div>
  );
};
