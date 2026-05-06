import streamlit as st 
import requests 


st.title("Travel Planner")
city=st.text_input("Enter the city you want to visit:")
interest=st.text_input("Enter your interest (e.g., culture, food, nature):")
budget_mapping = {
    "🎒 Backpacker (~$25 / 3,000 BDT per day)": "Backpacker (Max $25 USD per day)",
    "🧳 Standard (~$75 / 9,000 BDT per day)": "Standard (Around $75 USD per day)",
    "🥂 Luxury (~$250+ / 30,000+ BDT per day)": "Luxury ($250+ USD per day)"
}

# 2. Update the selectbox to show the detailed keys
selected_display = st.selectbox(
    "What is your budget style?", 
    options=list(budget_mapping.keys())
)

if st.button("Plan My Trip"):
    if city and interest:
        with st.spinner("Planning your trip..."):
            budget_for_llm=budget_mapping[selected_display]  
            response=requests.post("http://localhost:8002/plan_trip",json={"city":city,"interest":interest,"budget":budget_for_llm})
            if response.status_code==200:
                itenary=response.json().get('itenary','No itenary found')
                st.subheader("Your Trip Itenary:")
                st.write(itenary)
            else:
                st.error("Failed to plan the trip. Please try again.")
    else:
        st.warning("Please enter both city and interest to plan your trip.")