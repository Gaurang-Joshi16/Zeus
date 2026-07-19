import type { EventBridge } from '../events/EventBridge';
import type { WindowController } from '../window/WindowController';
import { eventBridge } from '../events/LocalEventBridge';
import { windowController } from '../window/TauriWindowController';

export class OverlayManager {
  private windowController: WindowController;
  private eventBridge: EventBridge;

  constructor(windowController: WindowController, eventBridge: EventBridge) {
    this.windowController = windowController;
    this.eventBridge = eventBridge;
  }

  async showOverlay(): Promise<void> {
    await this.windowController.show();
    await this.windowController.focus();
    this.eventBridge.publish('OVERLAY_OPENED');
    this.eventBridge.publish('OVERLAY_STATE_CHANGED', { state: 'VISIBLE' });
  }

  async hideOverlay(): Promise<void> {
    await this.windowController.hide();
    this.eventBridge.publish('OVERLAY_CLOSED');
    this.eventBridge.publish('OVERLAY_STATE_CHANGED', { state: 'HIDDEN' });
  }

  async toggleOverlay(): Promise<void> {
    const isVisible = await this.windowController.isVisible();
    if (isVisible) {
      await this.hideOverlay();
    } else {
      await this.showOverlay();
    }
  }
}

// Global instance for convenience
export const overlayManager = new OverlayManager(windowController, eventBridge);
