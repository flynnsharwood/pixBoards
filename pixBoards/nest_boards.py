import logging

from pixBoards.classes import NEST_SEPARATOR

logger = logging.getLogger(__name__)


def assign_nested_boards(boards):
    """Attach each board to its closest existing ancestor; return the roots."""
    board_map = {b.name: b for b in boards}
    logger.debug("Board Map Keys:  %s", list(board_map))
    nested = set()

    for b in boards:
        parts = b.name.split(NEST_SEPARATOR)
        for depth in range(len(parts) - 1, 0, -1):
            parent = board_map.get(NEST_SEPARATOR.join(parts[:depth]))
            if parent:
                parent.nested_boards.append(b)
                nested.add(b.name)
                break

    return [b for b in boards if b.name not in nested]
