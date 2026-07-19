import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useOverlayStore } from '../store/overlayStore';
import { overlayManager } from '../managers/OverlayManager';
import { register } from '@tauri-apps/plugin-global-shortcut';

interface Props {
  children: ReactNode;
}

export function OverlayContainer({ children }: Props) {
  const { isVisible, setVisible } = useOverlayStore();

  // TEMPORARY: Force the overlay to be visible on startup so the user can see it
  // without needing to press the hotkey.
  useEffect(() => {
    setVisible(true);
  }, [setVisible]);

  useEffect(() => {
    let cleanupWeb: (() => void) | void;

    const setupShortcut = async () => {
      try {
        await register('CommandOrControl+Shift+Space', (event: unknown) => {
          const ev = event as { state?: string };
          if (ev?.state === 'Pressed' || typeof event === 'string') {
            const current = useOverlayStore.getState().isVisible;
            setVisible(!current);
          }
        });
        console.log('[Zeus UI] Tauri global shortcut registered successfully.');
      } catch (err) {
        console.warn('[Zeus UI] Native shortcut registration failed (likely running in standard browser). Falling back to web listener.', err);
        
        // Web fallback for standard browser testing
        const handleKeyDown = (e: KeyboardEvent) => {
          if (e.ctrlKey && e.shiftKey && e.code === 'Space') {
            e.preventDefault();
            const current = useOverlayStore.getState().isVisible;
            useOverlayStore.getState().setVisible(!current);
          }
        };
        window.addEventListener('keydown', handleKeyDown);
        cleanupWeb = () => window.removeEventListener('keydown', handleKeyDown);
      }
    };
    
    setupShortcut();
    
    return () => {
      if (cleanupWeb) cleanupWeb();
    };
  }, [setVisible]);

  useEffect(() => {
    if (isVisible) {
      overlayManager.showOverlay();
    }
  }, [isVisible]);

  const handleAnimationComplete = () => {
    if (!isVisible) {
      overlayManager.hideOverlay();
    }
  };

  return (
    <AnimatePresence onExitComplete={handleAnimationComplete}>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
          animate={{ opacity: 1, backdropFilter: 'blur(12px)' }}
          exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-50 flex flex-col items-center justify-between w-full h-full p-8 bg-zeus-dark shadow-glass pointer-events-auto rounded-xl"
          data-tauri-drag-region
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
