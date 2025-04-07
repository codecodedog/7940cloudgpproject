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
    "North", "Tai Po", "Sha Tin", "Sai Kung", "Kwai Tsing", "Islands"
]

# Property conditions
property_conditions = [
    "Sea View", "Transportation", "New Building", "Renovated", 
    "Pet Friendly", "Furnished", "Near MTR", "Near Schools"
]

# Group Link
group_invite_link = {
    "Central & Western": "https://t.me/+ZwF96gQ0iaIzMjdl",
    "Wan Chai": "https://t.me/+wIhIjMvWwiY1NTg1",
    "Eastern": "https://t.me/+CYCxSOfYFcdkZDk1",
    "Southern": "https://t.me/+rmgkbnNL0QsxMzE1",
    "Yau Tsim Mong": "https://t.me/+ew9N8L2DLn83MzNl",
    "Sham Shui Po": "https://t.me/+0zh12IFOoshhY2E1",
    "Kowloon City": "https://t.me/+zimGTdRsjXs4OGRl",
    "Wong Tai Sin": "https://t.me/+tBK-j6bMxOM2MWI9",
    "Kwun Tong": "https://t.me/+8aCzLKE4kUU4Y2U1",
    "Tsuen Wan": "https://t.me/+HFMAXnTekDkxZGZl",
    "Tuen Mun": "https://t.me/+aQylrM-_s49kNzVl",
    "Yuen Long": "https://t.me/+Ihs1WvCFpVI1Yjll",
    "Tai Po": "https://t.me/+4yRBkGcWLO0xMzI1",
    "Sha Tin": "https://t.me/+o4b53BR0RsM2ZDc1",
    "Sai Kung": "https://t.me/+Mly7tHW3kRczOWRl",
    "Islands": "https://t.me/+_DJGCk7oH8ZkYTA1",
    "Kwai Tsing": "https://t.me/+hCI_shWvP09jMzJl",
    "North": "https://t.me/+hCI_shWvP09jMzJl",
}