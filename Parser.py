

#
# intended to be a base class for other more specific child parser classes
#
class Parser:

    # ctor
    def __init__(self):
        pass

    async def process_line(self, line: str) -> None:
        """
        Check the current line for damage related items

        Args:
            line: complete line from the EQ logfile
        """
        pass
