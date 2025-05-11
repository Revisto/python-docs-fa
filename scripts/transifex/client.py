from transifex.api import transifex_api
from .config import PROJECT, LANGUAGE, ORGANISATION

_api_cache = {}


def _fetch_from_api(cache_key, api_call_func, *args, **kwargs):
    if cache_key not in _api_cache:
        _api_cache[cache_key] = api_call_func(*args, **kwargs)
    return _api_cache[cache_key]


def get_all_resources():
    """Fetches all resources for the configured project, with caching."""
    cache_key = "all_resources"
    return _fetch_from_api(
        cache_key, transifex_api.Resource.filter, project=PROJECT
    ).all()


def get_resource_language_stats():
    """Fetches language statistics for all resources, with caching."""
    cache_key = "resource_language_stats"
    return _fetch_from_api(
        cache_key,
        transifex_api.ResourceLanguageStats.filter,
        project=PROJECT,
        language=LANGUAGE,
    ).all()


def get_team_members():
    """Fetches all team members, with caching."""
    cache_key = "team_members"
    # Fetching with 'user' include to get user details like username
    return (
        _fetch_from_api(
            cache_key,
            transifex_api.TeamMembership.filter,
            organization=ORGANISATION,
            language=LANGUAGE,
        )
        .include("user")
        .all()
    )


def get_resource_translations(resource):
    """Fetches translations for a given resource, with caching per resource."""
    resource_id = resource.id if hasattr(resource, "id") else str(resource)
    cache_key = f"resource_translations_{resource_id}"
    return _fetch_from_api(
        cache_key,
        transifex_api.ResourceTranslation.filter,
        resource=resource,
        language=LANGUAGE,
    ).all()
