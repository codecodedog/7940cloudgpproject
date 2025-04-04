# Conversation states - User Registration
user_telegram_id = 1
user_username = 2
user_condition = 3
user_district = 4
user_confirm = 5

# Conversation states - Property Registration
prop_type_choice = 10  # Leasing or Purchasing
prop_district = 11
prop_address = 12
prop_condition = 13
prop_condition_selection = 14
prop_price_min = 15
prop_price_max = 16
prop_duration = 17
prop_confirm = 18

# Group assignment state
group_assignment = 20

# Normal conversation state
question_asked = 30
prop_search = 31

# Districts in Hong Kong
hk_districts = [
    "Central & Western", "Wan Chai", "Eastern", "Southern", 
    "Yau Tsim Mong", "Sham Shui Po", "Kowloon City", "Wong Tai Sin", 
    "Kwun Tong", "Tsuen Wan", "Tuen Mun", "Yuen Long", 
    "North", "Tai Po", "Sha Tin", "Sai Kung", "Islands"
]

# Property conditions
property_conditions = [
    "Sea View", "Transportation", "New Building", "Renovated", 
    "Pet Friendly", "Furnished", "Near MTR", "Near Schools"
]

# Group Link
group_invite_link = {
    "Central & Western": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Wan Chai": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Eastern": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Southern": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Yau Tsim Mong": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Sham Shui Po": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Kowloon City": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Wong Tai Sin": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Kwun Tong": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Tsuen Wan": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Tuen Mun": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Yuen Long": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Tai Po": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Sha Tin": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Sai Kung": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Islands": "https://t.me/+ZwF96gQ0iaIzMjdl",
}