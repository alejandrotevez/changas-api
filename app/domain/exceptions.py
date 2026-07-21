class NotFound(Exception):
    def __init__(self, entity: str, id: str) -> None:
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id '{id}' not found")


class DuplicateSwipe(Exception):
    def __init__(self, user_id: str, item_id: str) -> None:
        self.user_id = user_id
        self.item_id = item_id
        super().__init__(f"User '{user_id}' already swiped on item '{item_id}'")


class InvalidTransition(Exception):
    def __init__(self, entity: str, from_state: str, to_state: str) -> None:
        self.entity = entity
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid transition for {entity}: "
            f"'{from_state}' → '{to_state}'"
        )


class Forbidden(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Forbidden: {reason}")


class AuthenticationError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Authentication error: {reason}")
