from core.ipc.adapter import ipc_adapter
from services.ai.speaker.enrollment.controller import EnrollmentController


class EnrollmentWizard:
    def __init__(self, controller: EnrollmentController):
        self.controller = controller
        self.register_ipc_handlers()

    def register_ipc_handlers(self):
        ipc_adapter.register_handler(
            "start_enrollment", self.controller.start_enrollment
        )
        ipc_adapter.register_handler(
            "cancel_enrollment", self.controller.cancel_enrollment
        )
        ipc_adapter.register_handler("begin_recording", self.controller.begin_recording)
        ipc_adapter.register_handler("stop_recording", self.controller.stop_recording)
        ipc_adapter.register_handler(
            "finish_enrollment", self.controller.finish_enrollment
        )

        required_commands = [
            "start_enrollment",
            "begin_recording",
            "stop_recording",
            "finish_enrollment",
            "cancel_enrollment"
        ]

        for cmd in required_commands:
            if cmd not in ipc_adapter._handlers:
                raise RuntimeError(f"Startup Failed: Required IPC Command '{cmd}' is missing.")

        print("\nRegistered IPC Commands")
        for cmd in required_commands:
            print(f"- {cmd}")
        print("\n")
