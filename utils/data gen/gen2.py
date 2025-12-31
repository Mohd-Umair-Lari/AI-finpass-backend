import json
import random
import uuid
import string
from datetime import datetime
from pymongo import MongoClient

# helper: random email + password
def random_email(index):
    return f"user{index}@example.com"

def random_password(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def generate_data_entry(index):
    name = f"User{index}"
    age = random.randint(20, 50)
    status = random.choice(["Salaried", "Self-Employed", "Freelancer", "Unemployed"])
    email = random_email(index)
    password = random_password()

    goal_name = random.choice(["Buy House", "Retirement", "Vacation", "Car Purchase"])
    target_amt = random.randint(50000, 5000000)
    target_time = random.randint(1, 20)

    monthly_income = random.randint(30000, 150000)
    monthly_expenses = random.randint(10000, 80000)
    monthly_savings = monthly_income - monthly_expenses
    debt = random.choice([0, random.randint(5000, 100000)])
    em_fund_opted = random.choice([True, False])

    risk_opt = random.choice(["Low", "Moderate", "High"])
    invest_mode = random.choice(["SIP", "Lump Sum", "Stocks"])
    invest_amt = random.randint(5000, 50000)

    start_date = datetime.now().strftime("%Y-%m-%d")
    tenure = random.randint(1, 10)
    ror = round(random.uniform(5, 15), 2)
    auto_adjust = random.choice([True, False])

    return {
        "_id": str(uuid.uuid4()),
        "Name": name,
        "Age": age,
        "employement-status": status,

        # NEW login fields
        "email": email,
        "password": password,  # ⚠️ plain text for now (can hash later)

        "Goal": {
            "goal": goal_name,
            "target-amt": target_amt,
            "target-time": target_time,
        },
        "financials": {
            "monthly-income": monthly_income,
            "monthly-expenses": monthly_expenses,
            "monthly_savings": monthly_savings,
            "debt": debt,
            "em-fund-opted": em_fund_opted,
        },
        "investments": {
            "risk-opt": risk_opt,
            "prefered-mode": invest_mode,
            "invest-amt": invest_amt,
        },
        "progress": {
            "start_date": start_date,
            "tenure": tenure,
            "ROR": ror,
            "auto-adjust": auto_adjust,
        }
    }

def save_to_json(data, filename="mock_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Data saved to {filename}")

def upload_to_mongodb(data, connection_str, db_name, collection_name):
    client = MongoClient(connection_str, tls=True)
    collection = client[db_name][collection_name]
    collection.delete_many({})
    collection.insert_many(data)
    print(f"Uploaded {len(data)} records to '{db_name}.{collection_name}'")


data_list = [generate_data_entry(i) for i in range(1, 101)]
save_to_json(data_list)

# Step 3: Upload to MongoDB Atlas (Before uploading remember to add the public network acces in the Atlas cluster i.e, 0.0.0.0/0 or the current IP address of the machine hosting this script)
connection_string = "mongodb+srv://umairlari:umairlari@cluster0.waxm9nl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
upload_to_mongodb(data_list, connection_string, db_name="mockDB", collection_name="userGoals")