from typing import Iterable, Optional


def evaluate_exemption(
    mode: str,
    exempt_role_id: Optional[int],
    user_role_ids: Iterable[int],
    is_moderator: bool,
) -> bool:
    if mode == "none":
        return False

    if mode == "admins_mods":
        return is_moderator

    if mode == "role":
        if exempt_role_id is None:
            return False
        return int(exempt_role_id) in {int(role_id) for role_id in user_role_ids}

    return False
