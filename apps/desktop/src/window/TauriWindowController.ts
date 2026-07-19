import { getCurrentWindow } from '@tauri-apps/api/window';
import type { WindowController } from './WindowController';

export class TauriWindowController implements WindowController {
  private get window() {
    try {
      return getCurrentWindow();
    } catch {
      return null; // Fallback for standard browsers
    }
  }

  async show(): Promise<void> {
    await this.window?.show();
  }

  async hide(): Promise<void> {
    await this.window?.hide();
  }

  async toggle(): Promise<void> {
    const visible = await this.isVisible();

    if (visible) {
      await this.hide();
    } else {
      await this.show();
      await this.focus();
    }
  }

  async center(): Promise<void> {
    await this.window?.center();
  }

  async focus(): Promise<void> {
    await this.window?.setFocus();
  }

  async restore(): Promise<void> {
    await this.window?.unminimize();
    await this.show();
    await this.focus();
  }

  async close(): Promise<void> {
    await this.window?.close();
  }

  async isVisible(): Promise<boolean> {
    // If we're in a browser tab without Tauri, we don't have a native window,
    // so just return true as a fallback so state management works.
    if (!this.window) return true;
    return await this.window.isVisible();
  }
}

export const windowController = new TauriWindowController();