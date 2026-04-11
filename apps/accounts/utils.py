from django.contrib.auth.models import Group


CHW_ROLE_ALIASES = (
    "chw",
    "community health worker",
    "communityhealthworker",
    "community_health_worker",
    "community health volunteer",
    "communityhealthvolunteer",
)

ADMIN_ROLE_ALIASES = (
    "admin",
    "administrator",
    "superadmin",
    "super admin",
    "super_admin",
)


def normalize_role_name(value):
    return "".join(ch.lower() for ch in (value or "") if ch.isalnum())


def user_has_role_alias(user, aliases):
    if not getattr(user, "is_authenticated", False):
        return False

    normalized_aliases = [normalize_role_name(alias) for alias in aliases]
    for group in user.groups.all():
        normalized_group_name = normalize_role_name(group.name)
        if any(alias in normalized_group_name for alias in normalized_aliases):
            return True
    return False


def is_chw_user(user):
    return user_has_role_alias(user, CHW_ROLE_ALIASES)


def is_admin_user(user):
    return bool(getattr(user, "is_superuser", False)) or user_has_role_alias(
        user, ADMIN_ROLE_ALIASES
    )


def resolve_group_by_aliases(aliases, create_name=None):
    normalized_aliases = [normalize_role_name(alias) for alias in aliases]
    for group in Group.objects.order_by("name"):
        normalized_group_name = normalize_role_name(group.name)
        if any(alias in normalized_group_name for alias in normalized_aliases):
            return group

    if create_name:
        group, _ = Group.objects.get_or_create(name=create_name)
        return group
    return None
