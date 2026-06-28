from typing_extensions import Self


class SharedInstance:
    """Share one instance per subclass."""

    __instance: Self | None = None

    def __new__(cls) -> Self:
        """Return the shared instance."""

        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance
