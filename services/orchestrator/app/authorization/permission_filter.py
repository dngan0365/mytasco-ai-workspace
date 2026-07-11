def qdrant_acl_filter(user: dict):
    from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue, MinShould

    public = FieldCondition(key="classification", match=MatchAny(any=["Public", "Internal", "public", "internal"]))
    if user.get("role", "").casefold() == "executive":
        classification = [public, FieldCondition(key="classification", match=MatchAny(any=["Confidential", "Restricted", "confidential", "restricted"]))]
    else:
        classification = [public, Filter(must=[
            FieldCondition(key="classification", match=MatchAny(any=["Confidential", "confidential"])),
            FieldCondition(key="owner_department_code", match=MatchValue(value=user.get("department_code") or user.get("department"))),
        ])]
    return Filter(must=[
        FieldCondition(key="organization_id", match=MatchValue(value=user.get("organization_id", "org-001"))),
        FieldCondition(key="is_active", match=MatchValue(value=True)),
    ], min_should=MinShould(conditions=classification, min_count=1))
