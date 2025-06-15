import streamlit as st
import requests
import random
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

# -------------------------------
# DATABASE
inventory = {
    'Store A': {'Milk': 10, 'Eggs': 30, 'Bread': 15},
    'Store B': {'Milk': 40, 'Eggs': 15, 'Bread': 5},
    'Store C': {'Milk': 2, 'Eggs': 20, 'Bread': 25},
}

warehouse_limits = {
    'Store A': {'Milk': 50, 'Eggs': 60, 'Bread': 40},
    'Store B': {'Milk': 40, 'Eggs': 50, 'Bread': 30},
    'Store C': {'Milk': 35, 'Eggs': 45, 'Bread': 50},
}

# Selling price (revenue)
prices = {'Milk': 50, 'Eggs': 10, 'Bread': 20}
# Purchase price (material cost / COGS)
purchase_prices = {'Milk': 30, 'Eggs': 5, 'Bread': 12}

base_demand = {'Milk': 20, 'Eggs': 25, 'Bread': 30}

transport_cost = {
    ('Store A', 'Store B'): 5, ('Store A', 'Store C'): 8,
    ('Store B', 'Store A'): 5, ('Store B', 'Store C'): 4,
    ('Store C', 'Store A'): 8, ('Store C', 'Store B'): 4
}

API_KEY = "0488f7d2622e29811baa6dd7259a3c6f"

# -------------------------------
# WEATHER DATA
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['main']['temp']
    else:
        return None

# -------------------------------
# SMART FORECAST
def forecast_demand(temp, weekday):
    demand = {}
    for product in base_demand:
        weather_impact = 0
        weekday_impact = 0
        sales_history_noise = random.randint(-5, 5)
        if product == 'Milk':
            if temp >= 30: weather_impact = 7
            elif temp <= 15: weather_impact = -5
        if weekday in ['Saturday', 'Sunday']:
            if product == 'Eggs': weekday_impact = 5
            if product == 'Bread': weekday_impact = 10
        demand[product] = max(base_demand[product] + weather_impact + weekday_impact + sales_history_noise, 0)
    return demand

# -------------------------------
# REDISTRIBUTION LOGIC
def calculate_transfers(inventory, demand):
    transfers = []
    for product in base_demand:
        total_stock = sum(store[product] for store in inventory.values())
        total_demand = demand[product]
        target_per_store = total_demand // len(inventory)

        surplus = []
        deficit = []
        for store, stock in inventory.items():
            diff = stock[product] - target_per_store
            if diff > 0:
                surplus.append((store, diff))
            elif diff < 0:
                deficit.append((store, -diff))

        while surplus and deficit:
            surplus.sort(key=lambda x: -x[1])
            deficit.sort(key=lambda x: -x[1])

            donor, donor_amt = surplus[0]
            receiver, receiver_amt = deficit[0]

            available_space = warehouse_limits[receiver][product] - inventory[receiver][product]
            transfer_qty = min(donor_amt, receiver_amt, available_space)

            if transfer_qty > 0:
                cost = transport_cost.get((donor, receiver), 999)
                transfers.append((product, transfer_qty, donor, receiver, cost))

                donor_amt -= transfer_qty
                receiver_amt -= transfer_qty
                inventory[donor][product] -= transfer_qty
                inventory[receiver][product] += transfer_qty

            if donor_amt == 0:
                surplus.pop(0)
            else:
                surplus[0] = (donor, donor_amt)

            if receiver_amt == 0:
                deficit.pop(0)
            else:
                deficit[0] = (receiver, receiver_amt)
    return transfers

# -------------------------------
# PROFIT CALC (corrected version)
def calculate_profit(inventory, demand, transfers):
    revenue = 0
    material_cost = 0

    for store, stock in inventory.items():
        for product, qty in stock.items():
            sold = min(qty, demand[product])
            revenue += sold * prices[product]
            material_cost += sold * purchase_prices[product]

    redistribution_cost = sum(qty * cost for (_, qty, _, _, cost) in transfers)
    holding_cost = sum(qty * 2 for store in inventory.values() for qty in store.values())
    profit = revenue - material_cost - redistribution_cost - holding_cost
    return revenue, material_cost, redistribution_cost, holding_cost, profit

# -------------------------------
# AUTO SUPPLIER REPLENISH
def reorder_recommendation(inventory, forecast):
    orders = {}
    for store, stock in inventory.items():
        store_orders = {}
        for product, qty in stock.items():
            expected_demand = forecast[product]
            reorder_qty = max(expected_demand - qty, 0)
            if reorder_qty > 0:
                store_orders[product] = reorder_qty
        if store_orders:
            orders[store] = store_orders
    return orders

# -------------------------------
# STREAMLIT UI

st.title(" AI-Powered Smart Inventory Optimizer")
st.caption("Developed by Saimanvitha, Manogna and Neha")
 #ADD THE PRICING TABLE RIGHT HERE:
st.header("💰 Product Pricing Table")
pricing_df = pd.DataFrame({
    'Selling Price (₹)': prices,
    'Purchase Price (₹)': purchase_prices
})
st.dataframe(
    pricing_df
    .style
    .set_properties(**{'text-align': 'center'}),
    use_container_width=True
)


with st.expander("About the Project"):
    st.write("""
    This AI-powered Smart Inventory Optimization System predicts demand dynamically using weather data, real-time inventory levels, 
    and sales patterns. It automatically suggests redistribution plans, supplier orders, and calculates profit metrics for better decision-making.

    Features:
    -  Demand Forecasting using weather & day-of-week
    -  Smart Redistribution across stores
    -  Profitability Analysis (including material cost)
    -  Supplier Replenishment Suggestions
    -  Real-time Weather Integration via OpenWeatherMap API

    Developed by: **Saimanvitha, Manogna and Neha**
    """)

st.header("🗃️ Current Inventory Overview")
st.dataframe(
    pd.DataFrame(inventory).T
    .style
    .highlight_max(axis=1, color='lightblue')
    .set_properties(**{'text-align': 'center'}),
    use_container_width=True
)

city = st.text_input("🌦️ Enter City to Fetch Live Weather Data:")
if city:
    temperature = get_weather(city)
    if temperature is None:
        st.error("❌ Failed to retrieve weather data. Try again.")
    else:
        weekday = datetime.now().strftime('%A')
        st.write(f"🌡️ Current Temperature: {temperature}°C  |  📅 Day: {weekday}")

        forecast = forecast_demand(temperature, weekday)
        st.header("📈 Forecasted Demand (Dynamic Prediction)")
        st.dataframe(
            pd.DataFrame(forecast, index=["Forecast"]).T
            .style
            .set_properties(**{'text-align': 'center'}),
            use_container_width=True
        )

        fig = go.Figure([go.Bar(x=list(forecast.keys()), y=list(forecast.values()))])
        fig.update_layout(title="Forecasted Demand", xaxis_title="Product", yaxis_title="Units")
        st.plotly_chart(fig)

        transfers = calculate_transfers(inventory, forecast)
        st.header("🔄 Redistribution Plan Based on Forecast")
        if transfers:
            transfer_table = []
            for product, qty, donor, receiver, cost in transfers:
                transfer_table.append({"Product": product, "Qty": qty, "From": donor, "To": receiver, "Cost": qty * cost})
            st.dataframe(
                pd.DataFrame(transfer_table)
                .style
                .set_properties(**{'text-align': 'center'}),
                use_container_width=True
            )
        else:
            st.success("✅ No redistribution required!")

        revenue, material_cost, redistribution_cost, holding_cost, profit = calculate_profit(inventory, forecast, transfers)
        st.header("💸 Profitability Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Revenue", f"₹{revenue}")
        col2.metric("Material Cost", f"₹{material_cost}")
        col3.metric("Redistribution Cost", f"₹{redistribution_cost}")
        col4.metric("Holding Cost", f"₹{holding_cost}")
        col5.metric("Profit", f"₹{profit}")

        orders = reorder_recommendation(inventory, forecast)
        st.header("📦 Supplier Reorder Recommendations")
        if orders:
            reorder_table = []
            for store, products in orders.items():
                for product, qty in products.items():
                    reorder_table.append({"Store": store, "Product": product, "Order Qty": qty})
            reorder_df = pd.DataFrame(reorder_table).sort_values(by=["Store", "Product"])
            st.dataframe(
                reorder_df.style.set_properties(**{'text-align': 'center'}),
                use_container_width=True
            )
        else:
            st.success("✅ All stores sufficiently stocked!")
