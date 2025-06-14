import streamlit as st
import json
import requests

# Title
st.title("🛒 Smart Inventory Rebalancer")
st.subheader("A Walmart-scale Inventory Redistribution Prototype")

# Load mock inventory data
with open('inventory.json') as f:
    inventory = json.load(f)

# Show current inventory
st.header("Current Inventory Levels")
for store in inventory:
    st.write(f"**{store['store']}**: {store['products']}")

# Weather API integration
st.header("External Factor: Weather Impact")
city = st.text_input("Enter city name for weather forecast:", "Hyderabad")

if st.button("Fetch Weather & Calculate Redistribution"):
    api_key = "0488f7d2622e29811baa6dd7259a3c6f"  # your key

    # Call OpenWeatherMap API
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    if data.get("cod") != 200:
        st.error("City not found. Please enter a valid city.")
    else:
        weather = data['weather'][0]['main']
        temperature = data['main']['temp']
        st.success(f"Weather: {weather}, Temperature: {temperature}°C")

        # Adjust demand based on weather
        demand_multiplier = 1.0
        if weather.lower() in ['clear', 'hot'] or temperature > 30:
            demand_multiplier = 1.2  # Higher demand for milk in hot weather
        elif weather.lower() in ['rain', 'thunderstorm']:
            demand_multiplier = 1.1  # Higher demand for bread on rainy days

        # Redistribution Logic (simplified)
        st.header("Suggested Redistribution")
        product = "Milk"
        threshold = 10
        total_stock = sum([store['products'][product] for store in inventory])
        ideal_stock = total_stock / len(inventory) * demand_multiplier

        for store in inventory:
            current_stock = store['products'][product]
            difference = round(ideal_stock - current_stock)
            if abs(difference) > threshold:
                if difference > 0:
                    st.write(f"📦 {store['store']} needs +{difference} units of {product}")
                else:
                    st.write(f"📦 {store['store']} has surplus {-difference} units of {product}")
            else:
                st.write(f"✅ {store['store']} is balanced for {product}")

        # Simple savings calculation
        cost_per_unit = 2  # dollars
        total_savings = round((threshold * len(inventory)) * cost_per_unit)
        st.success(f"Estimated potential savings: ${total_savings}")

