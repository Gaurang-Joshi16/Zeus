class AudioPermissions:
    @staticmethod
    def check_permission() -> bool:
        # On Windows desktop, this generally returns True.
        # Future OS-specific integrations can expand this.
        return True

    @staticmethod
    def request_permission() -> bool:
        return True
