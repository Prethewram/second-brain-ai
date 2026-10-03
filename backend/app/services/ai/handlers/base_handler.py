class BaseHandler:

    def __init__(
        self,
        service,
    ):

        self.service = service

    def execute(
        self,
        user_id: int,
        payload: dict,
    ):
        raise NotImplementedError("Handler must implement execute().")
