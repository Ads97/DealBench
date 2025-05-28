# Configuration for the Monopoly Deal Deck

# Import necessary enums from the card module
# Assume card.py is in the same directory or accessible via PYTHONPATH
from card import CardType, PropertyColor

# Define the deck as a list of dictionaries.
# Each dictionary represents a specific card type and its properties.
# 'count' specifies how many copies of this card are in the deck.

DECK_CONFIGURATION = [
    # --- Money Cards ---
    {'type': CardType.MONEY, 'name': "$10M", 'value': 10, 'count': 1},
    {'type': CardType.MONEY, 'name': "$5M", 'value': 5, 'count': 2},
    {'type': CardType.MONEY, 'name': "$4M", 'value': 4, 'count': 3},
    {'type': CardType.MONEY, 'name': "$3M", 'value': 3, 'count': 4},
    {'type': CardType.MONEY, 'name': "$2M", 'value': 2, 'count': 6},
    {'type': CardType.MONEY, 'name': "$1M", 'value': 1, 'count': 7},

    # --- Property Cards ---
    # Brown Set (2 properties, Rent: 1M, 2M)
    {'type': CardType.PROPERTY, 'name': "Old Town Rd", 'value': 1, 'set_color': PropertyColor.BROWN, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Cobblestone Way", 'value': 1, 'set_color': PropertyColor.BROWN, 'count': 1},

    # Light Blue Set (3 properties, Rent: 1M, 2M, 3M)
    {'type': CardType.PROPERTY, 'name': "Sunrise Ave", 'value': 1, 'set_color': PropertyColor.LIGHT_BLUE, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Ocean View Dr", 'value': 1, 'set_color': PropertyColor.LIGHT_BLUE, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Mountain Pass", 'value': 1, 'set_color': PropertyColor.LIGHT_BLUE, 'count': 1},

    # Pink Set (3 properties, Rent: 1M, 2M, 4M)
    {'type': CardType.PROPERTY, 'name': "Rose St", 'value': 2, 'set_color': PropertyColor.PINK, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Violet Ave", 'value': 2, 'set_color': PropertyColor.PINK, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Magenta Pl", 'value': 2, 'set_color': PropertyColor.PINK, 'count': 1},

    # Orange Set (3 properties, Rent: 1M, 3M, 5M)
    {'type': CardType.PROPERTY, 'name': "Harvest Ln", 'value': 2, 'set_color': PropertyColor.ORANGE, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Poppy Hills", 'value': 2, 'set_color': PropertyColor.ORANGE, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Sunset Blvd", 'value': 2, 'set_color': PropertyColor.ORANGE, 'count': 1},

    # Red Set (3 properties, Rent: 2M, 3M, 6M)
    {'type': CardType.PROPERTY, 'name': "Ruby Rd", 'value': 3, 'set_color': PropertyColor.RED, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Garnet Ave", 'value': 3, 'set_color': PropertyColor.RED, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Crimson Sq", 'value': 3, 'set_color': PropertyColor.RED, 'count': 1},

    # Yellow Set (3 properties, Rent: 2M, 4M, 6M)
    {'type': CardType.PROPERTY, 'name': "Gold St", 'value': 3, 'set_color': PropertyColor.YELLOW, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Lemon Ln", 'value': 3, 'set_color': PropertyColor.YELLOW, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Sunshine Way", 'value': 3, 'set_color': PropertyColor.YELLOW, 'count': 1},

    # Green Set (3 properties, Rent: 2M, 4M, 7M)
    {'type': CardType.PROPERTY, 'name': "Emerald Dr", 'value': 4, 'set_color': PropertyColor.GREEN, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Forest Rd", 'value': 4, 'set_color': PropertyColor.GREEN, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Meadow Walk", 'value': 4, 'set_color': PropertyColor.GREEN, 'count': 1},

    # Dark Blue Set (2 properties, Rent: 3M, 8M)
    {'type': CardType.PROPERTY, 'name': "Luxury Lane", 'value': 4, 'set_color': PropertyColor.DARK_BLUE, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Prestige Point", 'value': 4, 'set_color': PropertyColor.DARK_BLUE, 'count': 1},

    # Railroad Set (4 properties, Rent: 1M, 2M, 3M, 4M)
    {'type': CardType.PROPERTY, 'name': "Central Station", 'value': 2, 'set_color': PropertyColor.RAILROAD, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "East Line RR", 'value': 2, 'set_color': PropertyColor.RAILROAD, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "West Line RR", 'value': 2, 'set_color': PropertyColor.RAILROAD, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "North Line RR", 'value': 2, 'set_color': PropertyColor.RAILROAD, 'count': 1},

    # Utility Set (2 properties, Rent: 1M, 2M)
    {'type': CardType.PROPERTY, 'name': "Power Plant", 'value': 2, 'set_color': PropertyColor.UTILITY, 'count': 1},
    {'type': CardType.PROPERTY, 'name': "Water Works", 'value': 2, 'set_color': PropertyColor.UTILITY, 'count': 1},

    # --- Property Wild Cards ---
    # 2-Color Wilds (Value: Use set color value when placed? Or define here? Let's define)
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Pink/Orange)", 'value': 2, 'available_colors': [PropertyColor.PINK, PropertyColor.ORANGE], 'count': 2},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Lt.Blue/Brown)", 'value': 1, 'available_colors': [PropertyColor.LIGHT_BLUE, PropertyColor.BROWN], 'count': 1},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Lt.Blue/Railroad)", 'value': 2, 'available_colors': [PropertyColor.LIGHT_BLUE, PropertyColor.RAILROAD], 'count': 1},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Green/Railroad)", 'value': 4, 'available_colors': [PropertyColor.GREEN, PropertyColor.RAILROAD], 'count': 1},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Dk.Blue/Green)", 'value': 4, 'available_colors': [PropertyColor.DARK_BLUE, PropertyColor.GREEN], 'count': 1},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Utility/Railroad)", 'value': 2, 'available_colors': [PropertyColor.UTILITY, PropertyColor.RAILROAD], 'count': 1},
    {'type': CardType.PROPERTY_WILD, 'name': "Wild (Yellow/Red)", 'value': 3, 'available_colors': [PropertyColor.YELLOW, PropertyColor.RED], 'count': 2},
    # 4-Color Wild
    {'type': CardType.PROPERTY_WILD, 'name': "Property Wildcard (Any Color)", 'value': 0,
     'available_colors': [PropertyColor.BROWN, PropertyColor.LIGHT_BLUE, PropertyColor.PINK, PropertyColor.ORANGE,
                          PropertyColor.RED, PropertyColor.YELLOW, PropertyColor.GREEN, PropertyColor.DARK_BLUE,
                          PropertyColor.RAILROAD, PropertyColor.UTILITY], 'count': 3},

    # --- Action Cards ---
    # Rent Cards
    {'type': CardType.ACTION_RENT, 'name': "Rent (Wild - All Colors)", 'value': 3, 'colors': [PropertyColor.ALL], 'count': 3, 'wild': True},
    {'type': CardType.ACTION_RENT, 'name': "Rent (Pink/Orange)", 'value': 1, 'colors': [PropertyColor.PINK, PropertyColor.ORANGE], 'count': 3, 'wild': False},
    {'type': CardType.ACTION_RENT, 'name': "Rent (Lt.Blue/Brown)", 'value': 1, 'colors': [PropertyColor.LIGHT_BLUE, PropertyColor.BROWN], 'count': 3, 'wild': False},
    {'type': CardType.ACTION_RENT, 'name': "Rent (Green/Dk.Blue)", 'value': 1, 'colors': [PropertyColor.GREEN, PropertyColor.DARK_BLUE], 'count': 3, 'wild': False},
    {'type': CardType.ACTION_RENT, 'name': "Rent (Yellow/Red)", 'value': 1, 'colors': [PropertyColor.YELLOW, PropertyColor.RED], 'count': 3, 'wild': False},
    {'type': CardType.ACTION_RENT, 'name': "Rent (Railroad/Utility)", 'value': 1, 'colors': [PropertyColor.RAILROAD, PropertyColor.UTILITY], 'count': 3, 'wild': False},

    # Building Cards
    {'type': CardType.ACTION_BUILDING, 'card_class': 'HouseCard', 'name': "House", 'value': 3, 'count': 3},#correct
    {'type': CardType.ACTION_BUILDING, 'card_class': 'HotelCard', 'name': "Hotel", 'value': 4, 'count': 3},#correct

    # Other Action Cards (Gameplay logic handled elsewhere based on type/name)
    {'type': CardType.ACTION_DOUBLE_THE_RENT, 'card_class': 'DoubleTheRentCard', 'name': "Double The Rent", 'value': 1, 'count': 2},#correct
    {'type': CardType.ACTION_RESPONSE, 'card_class': 'JustSayNoCard', 'name': "Just Say No!", 'value': 4, 'count': 3},#correct

    {'type': CardType.ACTION_OTHER, 'action_name': 'DealBreaker', 'name': "Deal Breaker", 'value': 5, 'count': 2},#correct
    {'type': CardType.ACTION_OTHER, 'action_name': 'SlyDeal', 'name': "Sly Deal", 'value': 3, 'count': 3},#correct
    {'type': CardType.ACTION_OTHER, 'action_name': 'ForcedDeal', 'name': "Forced Deal", 'value': 3, 'count': 4},#correct
    {'type': CardType.ACTION_OTHER, 'action_name': 'DebtCollector', 'name': "Debt Collector", 'value': 3, 'count': 3},#correct
    {'type': CardType.ACTION_OTHER, 'action_name': 'ItsMyBirthday', 'name': "It's My Birthday!", 'value': 2, 'count': 3},#correct
    {'type': CardType.ACTION_OTHER, 'action_name': 'Pass Go', 'name': "Pass Go", 'value': 1, 'count': 10} #correct
]

# --- Sanity Check: Total Card Count ---
# Standard Monopoly Deal has 106 cards (sometimes listed as 110 with extra blanks/ads)
# Let's sum our counts:
total_cards = sum(item['count'] for item in DECK_CONFIGURATION)
print(f"Total cards configured: {total_cards}")

EXPECTED_TOTAL = 106
if total_cards != EXPECTED_TOTAL:
    print(f"WARNING: Configured card count ({total_cards}) does not match expected ({EXPECTED_TOTAL})!")
