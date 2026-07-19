import { eventBridge } from '../events/LocalEventBridge';

export class EnrollmentService {
  static async startEnrollment() {
    console.log("[Frontend] EnrollmentService.startEnrollment() called");
    return eventBridge.invoke('start_enrollment');
  }

  static async beginRecording() {
    return eventBridge.invoke('begin_recording');
  }

  static async stopRecording() {
    return eventBridge.invoke('stop_recording');
  }

  static async finishEnrollment() {
    return eventBridge.invoke('finish_enrollment');
  }
  
  static async cancelEnrollment() {
    return eventBridge.invoke('cancel_enrollment');
  }
}
