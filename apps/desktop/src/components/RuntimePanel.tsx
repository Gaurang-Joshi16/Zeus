import React from 'react';
import { useRuntimeStore } from '../store/runtimeStore';
import { useConversationStore } from '../store/conversationStore';

export const RuntimePanel: React.FC = () => {
  const { services, events, isPanelOpen, togglePanel } = useRuntimeStore();
  const convStore = useConversationStore();

  if (!isPanelOpen) return null;

  return (
    <div className="absolute right-0 top-0 h-full w-96 bg-black/80 backdrop-blur-md border-l border-white/10 p-6 flex flex-col text-white font-mono text-sm z-50 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold tracking-widest text-cyan-400">ZEUS RUNTIME</h2>
        <button onClick={togglePanel} className="text-gray-400 hover:text-white">
          [X]
        </button>
      </div>

      <div className="mb-8">
        <h3 className="text-xs uppercase text-gray-500 mb-3 border-b border-white/10 pb-1">Services</h3>
        <div className="space-y-4">
          {Object.entries(services).map(([name, service]) => {
            let statusColor = 'text-gray-400';
            if (service.status === 'READY') statusColor = 'text-green-400';
            if (service.status === 'FAILED') statusColor = 'text-red-500';
            if (service.status === 'BUSY') statusColor = 'text-yellow-400';
            if (service.status === 'INITIALIZING') statusColor = 'text-blue-400';

            return (
              <div key={name} className="bg-white/5 p-3 rounded border border-white/5">
                <div className="flex justify-between mb-1">
                  <span className="font-bold">{name}</span>
                  <span className={statusColor}>{service.status}</span>
                </div>
                <div className="text-xs text-gray-400 grid grid-cols-2 gap-1">
                  <div>Uptime: {service.uptime.toFixed(1)}s</div>
                  <div>Recov: {service.recoveryCount}</div>
                  {service.lastError && (
                    <div className="col-span-2 text-red-400 truncate" title={service.lastError}>
                      Err: {service.lastError}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-xs uppercase text-gray-500 mb-3 border-b border-white/10 pb-1">Speech Pipeline</h3>
        <div className="bg-white/5 p-3 rounded border border-white/5 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">VAD Status</span>
            <span className={convStore.vadState === 'SPEECH_DETECTED' ? 'text-green-400' : 'text-gray-500'}>
              {convStore.vadState}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Mic Amplitude</span>
            <span className="text-cyan-300">{convStore.microphoneLevel.toFixed(3)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Rec. Duration</span>
            <span className="text-cyan-300">{convStore.recordingDuration}ms</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">STT Confidence</span>
            <span className="text-cyan-300">{(convStore.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">STT Time</span>
            <span className="text-cyan-300">{convStore.processingTime}ms</span>
          </div>
          <div className="mt-2 pt-2 border-t border-white/10">
            <span className="text-gray-400 block mb-1">Current Transcript:</span>
            <span className="text-white italic">"{convStore.currentTranscript || convStore.partialTranscript || '...'}"</span>
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h3 className="text-xs uppercase text-gray-500 mb-3 border-b border-white/10 pb-1">AI Pipeline</h3>
        <div className="bg-white/5 p-3 rounded border border-white/5 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">Provider</span>
            <span className="text-cyan-300">{convStore.provider || 'None'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Processing Time</span>
            <span className="text-cyan-300">
              {convStore.llmProcessingTime > 0 ? `${convStore.llmProcessingTime.toFixed(2)}s` : '0s'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Token Usage</span>
            <span className="text-cyan-300">{convStore.tokenUsage}</span>
          </div>
          <div className="mt-2 pt-2 border-t border-white/10">
            <span className="text-gray-400 block mb-1">Live Response:</span>
            <span className="text-white italic">"{convStore.aiResponse || convStore.partialResponse || '...'}"</span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xs uppercase text-gray-500 mb-3 border-b border-white/10 pb-1">Recent Events</h3>
        <div className="space-y-2 flex-1 overflow-y-auto max-h-64 pr-2">
          {events.slice().reverse().map((ev, i) => (
            <div key={i} className="text-xs border-l-2 border-cyan-500/30 pl-2 py-1">
              <div className="text-gray-500">
                {new Date(ev.timestamp * 1000).toLocaleTimeString()}
              </div>
              <div className="text-gray-300">
                <span className="text-cyan-300">{ev.service}</span>
                <span className="text-gray-500 mx-1">→</span>
                <span>{ev.eventType}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
