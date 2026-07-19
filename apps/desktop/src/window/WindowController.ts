export interface WindowController {
  show(): Promise<void>;
  hide(): Promise<void>;
  toggle(): Promise<void>;
  center(): Promise<void>;
  focus(): Promise<void>;
  restore(): Promise<void>;
  close(): Promise<void>;
  isVisible(): Promise<boolean>;
}
