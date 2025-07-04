import pyautogui
from typing import Optional, Tuple

from src import config


def locate_copy_icon(region=None) -> Optional[Tuple[int, int, int, int]]:
    """Locate the ChatGPT Desktop Copy button on screen.

    Parameters
    ----------
    region : tuple, optional
        A region tuple (left, top, width, height) to restrict the search.

    Returns
    -------
    tuple or None
        Bounding box of the located icon or None if not found.
    """
    for path in config.load_config().get("copy_icon_templates", []):
        box = pyautogui.locateOnScreen(path, region=region)
        if box:
            return box
    return None


def click_copy_icon() -> bool:
    """Move the mouse to the Copy icon and click if found."""
    box = locate_copy_icon()
    if box:
        center_x, center_y = pyautogui.center(box)
        pyautogui.moveTo(center_x, center_y)
        pyautogui.click()
        return True
    return False


def detect_login_screen() -> bool:
    """Return ``True`` if the ChatGPT login screen is visible."""
    for path in config.load_config().get("login_screen_templates", []):
        if pyautogui.locateOnScreen(path) is not None:
            return True
    return False
