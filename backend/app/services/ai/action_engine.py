from app.core.logger import logger
from app.services.ai.registry import HandlerRegistry


class ActionEngine:

    def __init__(
        self,
        db,
        registry=None,
    ):

        self.db = db
        self.registry = registry if registry is not None else HandlerRegistry(db)

    def execute(
        self,
        user_id: int,
        actions,
    ):

        executed = 0
        failed = 0
        skipped = 0

        for action in actions:

            handler = self.registry.get(action.type)

            if handler is None:

                skipped += 1

                logger.warning(
                    "No handler registered for action '%s'",
                    action.type,
                )

                continue

            try:

                handler.execute(
                    user_id=user_id,
                    payload=action.payload,
                )

                executed += 1

                logger.info(
                    "Executed action '%s' successfully",
                    action.type,
                )

            except Exception:

                failed += 1

                logger.exception(
                    "Failed executing action '%s'",
                    action.type,
                )

                if self.db is not None:
                    try:
                        self.db.rollback()
                    except Exception:
                        logger.exception(
                            "Database rollback failed after action '%s'", action.type
                        )
                        # Continuing with an unrecovered session cannot execute safely.
                        raise

        logger.info(
            "Action execution completed " "(executed=%s, failed=%s, skipped=%s)",
            executed,
            failed,
            skipped,
        )

        return {
            "executed": executed,
            "failed": failed,
            "skipped": skipped,
        }
