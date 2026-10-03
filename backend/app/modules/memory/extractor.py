class MemoryExtractor:

    KEYWORDS = [
        "remember",
        "my name is",
        "i work at",
        "my company is",
        "my favorite",
        "i prefer",
    ]

    @staticmethod
    def should_store(text: str):

        text = text.lower()

        return any(keyword in text for keyword in MemoryExtractor.KEYWORDS)
