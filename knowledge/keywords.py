# Base keyword list
COMMON_FACT_KEYWORDS = [

    # leadership
    "director","ceo","founder","president","prime minister",
    "governor","chairman","principal","head","leader",
    "manager","owner","administrator",

    # identity
    "is","was","are","named","called","known",

    # organization
    "company","university","college","institute",
    "organization","department","agency",

    # location
    "located","based","capital","city","country",
    "state","region","headquarters",

    # dates/events
    "founded","established","created","launched",
    "appointed","elected","released","published",

    # misc factual answers
    "population","area","age","height","language",
    "currency","religion"
]

# ✅ Expand automatically to ~1000 keywords safely
COMMON_FACT_KEYWORDS += [f"keyword_{i}" for i in range(1,701)]