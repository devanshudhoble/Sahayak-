"""Multi-merchant intelligence: category-specific suggestions based on shop type."""

CATEGORIES = {
    "kirana": {
        "label": "Kirana Store",
        "suggestions": {
            "Monday": "Offer a Monday morning essentials combo (oil + dal + rice) at 5% off",
            "Tuesday": "Try a buy-2-get-1 on snacks and biscuits",
            "Wednesday": "Bundle tea + sugar + milk at a small discount",
            "Thursday": "Try a tea-and-snacks bundle offer",
            "Friday": "Promote weekend cooking packs (spices + veggies combo)",
            "Saturday": "Push household items bundle (soap + detergent + cleaning)",
            "Sunday": "Offer home delivery for orders above ₹300",
        },
    },
    "vegetables": {
        "label": "Vegetable Vendor",
        "suggestions": {
            "Monday": "Offer a weekly sabzi pack subscription at a small discount",
            "Tuesday": "Try a salad-greens combo at reduced price",
            "Wednesday": "Bundle 5 vegetables for ₹100 flat",
            "Thursday": "Offer home delivery for orders above ₹200",
            "Friday": "Promote weekend special — paneer + fresh veggies combo",
            "Saturday": "Push fruit + vegetable mixed basket",
            "Sunday": "Try early bird discount — 10% off before 9 am",
        },
    },
    "salon": {
        "label": "Salon / Parlour",
        "suggestions": {
            "Monday": "Offer ₹50 off on haircuts — slow day special",
            "Tuesday": "Try a facial + haircut combo deal",
            "Wednesday": "Promote student discount — show college ID for 20% off",
            "Thursday": "Offer a grooming package at bundled price",
            "Friday": "Push pre-weekend styling packages for couples",
            "Saturday": "Try a loyalty card — 5th visit free styling",
            "Sunday": "Offer bridal trial packages at reduced rate",
        },
    },
    "chai": {
        "label": "Chai Stall",
        "suggestions": {
            "Monday": "Add a paratha + chai combo for ₹30 morning special",
            "Tuesday": "Try a bun-maska + cutting chai deal",
            "Wednesday": "Offer office delivery for 5+ cups",
            "Thursday": "Push a samosa + chai combo at ₹25",
            "Friday": "Try a special Friday masala chai at ₹5 extra",
            "Saturday": "Offer a family pack — 4 cups at ₹80",
            "Sunday": "Push weekend breakfast combo — poha + chai",
        },
    },
    "medical": {
        "label": "Medical Store",
        "suggestions": {
            "Monday": "Promote health checkup reminder service for regulars",
            "Tuesday": "Offer OTC wellness combo (vitamins + sanitizer)",
            "Wednesday": "Partner with local doctor for prescription referrals",
            "Thursday": "Try a senior citizen discount day (10% off)",
            "Friday": "Push first-aid kit bundles for families",
            "Saturday": "Offer baby care product bundles",
            "Sunday": "Partner with nearby clinic for Sunday OPD referrals",
        },
    },
    "stationery": {
        "label": "Stationery Shop",
        "suggestions": {
            "Monday": "Offer a student starter pack (pens + notebook + eraser)",
            "Tuesday": "Push craft supplies combo for kids",
            "Wednesday": "Try a buy-5-get-1 on notebooks",
            "Thursday": "Offer office supplies bundle (files + stapler + tape)",
            "Friday": "Promote weekend art kits for children",
            "Saturday": "Push gift wrapping + card combo deals",
            "Sunday": "Offer coloring book + crayon sets at bundled price",
        },
    },
}

DEFAULT_CATEGORY = "kirana"


def get_suggestion(category: str, weekday: str, cap: int = 1000) -> str:
    """Get a category-specific suggestion for the given weekday."""
    cat = CATEGORIES.get(category, CATEGORIES[DEFAULT_CATEGORY])
    base = cat["suggestions"].get(weekday, "Try a small promotional offer")
    return f"{base} on {weekday}s for three weeks. Maximum budget ₹{cap:,}."


def get_category_label(category: str) -> str:
    cat = CATEGORIES.get(category, CATEGORIES[DEFAULT_CATEGORY])
    return cat["label"]


def list_categories() -> list:
    """Return all supported categories with labels."""
    return [{"id": k, "label": v["label"]} for k, v in CATEGORIES.items()]
