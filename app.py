import os
import json
import uuid
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load API key
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Initialize Gemini Model
llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash-latest",
    temperature=0.3
)

# Carbon Emission Factors (kg CO2 per unit)
EMISSION_FACTORS = {
    "car_km": 0.21,           # per km driven
    "public_transport_km": 0.05,  # per km
    "flight_km": 0.25,        # per km
    "ac_hour": 1.5,           # per hour
    "heater_hour": 2.0,       # per hour
    "meat_meal": 3.3,         # per meal
    "vegetarian_meal": 0.9,   # per meal
    "electricity_kwh": 0.5,   # per kWh
    "water_heating_hour": 1.2  # per hour
}

# Data Validator
def data_validator(state: dict) -> dict:
    """Validate and sanitize user input data"""
    try:
        state["car_km"] = float(state.get("car_km", 0))
        state["public_transport_km"] = float(state.get("public_transport_km", 0))
        state["flight_km"] = float(state.get("flight_km", 0))
        state["ac_hours"] = float(state.get("ac_hours", 0))
        state["heater_hours"] = float(state.get("heater_hours", 0))
        state["meat_meals"] = int(state.get("meat_meals", 0))
        state["vegetarian_meals"] = int(state.get("vegetarian_meals", 0))
        state["electricity_kwh"] = float(state.get("electricity_kwh", 0))
        state["water_heating_hours"] = float(state.get("water_heating_hours", 0))
    except ValueError:
        # Set default values if validation fails
        state["car_km"] = 0
        state["public_transport_km"] = 0
        state["flight_km"] = 0
        state["ac_hours"] = 0
        state["heater_hours"] = 0
        state["meat_meals"] = 0
        state["vegetarian_meals"] = 0
        state["electricity_kwh"] = 0
        state["water_heating_hours"] = 0
    
    # Validate additional info
    for key in ["additional_activities", "location", "season"]:
        if not state.get(key):
            state[key] = "Not specified"
    
    return state

# Carbon Footprint Calculator
def calculate_emissions(state: dict) -> dict:
    """Calculate total carbon emissions based on user activities"""
    emissions = 0
    breakdown = {}
    
    # Transportation emissions
    car_emissions = state["car_km"] * EMISSION_FACTORS["car_km"]
    public_emissions = state["public_transport_km"] * EMISSION_FACTORS["public_transport_km"]
    flight_emissions = state["flight_km"] * EMISSION_FACTORS["flight_km"]
    transport_total = car_emissions + public_emissions + flight_emissions
    
    breakdown["transportation"] = {
        "car": car_emissions,
        "public_transport": public_emissions,
        "flights": flight_emissions,
        "total": transport_total
    }
    
    # Energy usage emissions
    ac_emissions = state["ac_hours"] * EMISSION_FACTORS["ac_hour"]
    heater_emissions = state["heater_hours"] * EMISSION_FACTORS["heater_hour"]
    electricity_emissions = state["electricity_kwh"] * EMISSION_FACTORS["electricity_kwh"]
    water_heating_emissions = state["water_heating_hours"] * EMISSION_FACTORS["water_heating_hour"]
    energy_total = ac_emissions + heater_emissions + electricity_emissions + water_heating_emissions
    
    breakdown["energy"] = {
        "ac": ac_emissions,
        "heater": heater_emissions,
        "electricity": electricity_emissions,
        "water_heating": water_heating_emissions,
        "total": energy_total
    }
    
    # Food emissions
    meat_emissions = state["meat_meals"] * EMISSION_FACTORS["meat_meal"]
    veg_emissions = state["vegetarian_meals"] * EMISSION_FACTORS["vegetarian_meal"]
    food_total = meat_emissions + veg_emissions
    
    breakdown["food"] = {
        "meat_meals": meat_emissions,
        "vegetarian_meals": veg_emissions,
        "total": food_total
    }
    
    # Total emissions
    total_emissions = transport_total + energy_total + food_total
    
    state["total_emissions"] = round(total_emissions, 2)
    state["emissions_breakdown"] = breakdown
    
    return state

# Impact Classifier
def classify_impact(state: dict) -> dict:
    """Classify user's carbon impact level"""
    total = state["total_emissions"]
    
    if total < 5:
        impact_level = "Low Impact"
        message = "Great job! Your carbon footprint is below average."
    elif total <= 15:
        impact_level = "Moderate Impact"
        message = "Your carbon footprint is moderate. There's room for improvement."
    else:
        impact_level = "High Impact"
        message = "Your carbon footprint is above average. Consider making some changes."
    
    state["impact_level"] = impact_level
    state["impact_message"] = message
    
    return state

# Router for Agent Selection
def router(state: dict) -> str:
    """Route to appropriate agent based on impact level"""
    impact = state["impact_level"]
    
    if "Low" in impact:
        return "low_impact"
    elif "Moderate" in impact:
        return "moderate_impact"
    else:
        return "high_impact"

# Low Impact Agent
def low_impact_agent(state: dict) -> dict:
    """Agent for users with low carbon impact"""
    prompt = f"""
User has a low carbon footprint of {state['total_emissions']} kg CO2 today.
Breakdown:
- Transportation: {state['emissions_breakdown']['transportation']['total']:.2f} kg CO2
- Energy: {state['emissions_breakdown']['energy']['total']:.2f} kg CO2
- Food: {state['emissions_breakdown']['food']['total']:.2f} kg CO2

Provide encouraging feedback and 2-3 tips to maintain this excellent performance.
Keep it positive and motivating.
"""
    response = llm.invoke(prompt)
    state["recommendations"] = response.content.strip()
    state["agent_type"] = "low_impact"
    return state

# Moderate Impact Agent
def moderate_impact_agent(state: dict) -> dict:
    """Agent for users with moderate carbon impact"""
    prompt = f"""
User has a moderate carbon footprint of {state['total_emissions']} kg CO2 today.
Breakdown:
- Transportation: {state['emissions_breakdown']['transportation']['total']:.2f} kg CO2
- Energy: {state['emissions_breakdown']['energy']['total']:.2f} kg CO2
- Food: {state['emissions_breakdown']['food']['total']:.2f} kg CO2

Provide balanced feedback and 3-4 specific, actionable tips to reduce their footprint.
Focus on the highest emission categories.
"""
    response = llm.invoke(prompt)
    state["recommendations"] = response.content.strip()
    state["agent_type"] = "moderate_impact"
    return state

# High Impact Agent
def high_impact_agent(state: dict) -> dict:
    """Agent for users with high carbon impact"""
    prompt = f"""
User has a high carbon footprint of {state['total_emissions']} kg CO2 today.
Breakdown:
- Transportation: {state['emissions_breakdown']['transportation']['total']:.2f} kg CO2
- Energy: {state['emissions_breakdown']['energy']['total']:.2f} kg CO2
- Food: {state['emissions_breakdown']['food']['total']:.2f} kg CO2

Provide gentle but urgent feedback and 4-5 specific, practical tips to significantly reduce their footprint.
Focus on the biggest impact areas first. Be encouraging but emphasize the importance of change.
"""
    response = llm.invoke(prompt)
    state["recommendations"] = response.content.strip()
    state["agent_type"] = "high_impact"
    return state

# Session Logger
def session_logger(state: dict) -> dict:
    """Log the session data"""
    log = {
        "id": str(uuid.uuid4()),
        "timestamp": str(datetime.now()),
        "user_inputs": {
            "car_km": state["car_km"],
            "public_transport_km": state["public_transport_km"],
            "flight_km": state["flight_km"],
            "ac_hours": state["ac_hours"],
            "heater_hours": state["heater_hours"],
            "meat_meals": state["meat_meals"],
            "vegetarian_meals": state["vegetarian_meals"],
            "electricity_kwh": state["electricity_kwh"],
            "water_heating_hours": state["water_heating_hours"]
        },
        "total_emissions": state["total_emissions"],
        "emissions_breakdown": state["emissions_breakdown"],
        "impact_level": state["impact_level"],
        "agent_type": state["agent_type"],
        "recommendations": state["recommendations"]
    }
    
    os.makedirs("carbon_logs", exist_ok=True)
    with open(f"carbon_logs/session_{log['id']}.json", "w") as f:
        json.dump(log, f, indent=2)
    
    return state

# Final Summary Agent
def final_summary_agent(state: dict) -> dict:
    """Generate final summary and next steps"""
    prompt = f"""
Create a motivational summary for a user with {state['total_emissions']} kg CO2 emissions today.
Impact level: {state['impact_level']}
Agent type: {state['agent_type']}

Provide:
1. A brief summary of their day's impact
2. One key takeaway
3. One simple action they can take tomorrow
Keep it under 3 sentences and motivating.
"""
    response = llm.invoke(prompt)
    state["final_summary"] = response.content.strip()
    
    # Add global context
    state["global_context"] = {
        "daily_target": "5 kg CO2 (sustainable target)",
        "global_average": "12 kg CO2/day",
        "paris_agreement_target": "2.3 tons CO2/year"
    }
    
    return state

# Build and Run Carbon Track Agent
def run_carbon_agent(user_data: dict) -> dict:
    """Main function to run the carbon tracking agent"""
    
    # Build the workflow graph
    builder = StateGraph(dict)
    
    # Set entry point
    builder.set_entry_point("data_validator")
    
    # Add nodes
    builder.add_node("data_validator", data_validator)
    builder.add_node("calculate_emissions", calculate_emissions)
    builder.add_node("classify_impact", classify_impact)
    builder.add_node("low_impact", low_impact_agent)
    builder.add_node("moderate_impact", moderate_impact_agent)
    builder.add_node("high_impact", high_impact_agent)
    builder.add_node("session_logger", session_logger)
    builder.add_node("final_summary", final_summary_agent)
    
    # Add edges
    builder.add_edge("data_validator", "calculate_emissions")
    builder.add_edge("calculate_emissions", "classify_impact")
    
    # Add conditional edges based on impact level
    builder.add_conditional_edges("classify_impact", router, {
        "low_impact": "low_impact",
        "moderate_impact": "moderate_impact",
        "high_impact": "high_impact"
    })
    
    # Connect all agents to logger
    builder.add_edge("low_impact", "session_logger")
    builder.add_edge("moderate_impact", "session_logger")
    builder.add_edge("high_impact", "session_logger")
    
    # Final steps
    builder.add_edge("session_logger", "final_summary")
    builder.add_edge("final_summary", END)
    
    # Compile and run
    graph = builder.compile()
    return graph.invoke(user_data)

# User Interface Function
def collect_user_data():
    """Collect user activity data"""
    print("🌱 Welcome to CarbonTrackAgent!")
    print("Let's calculate your daily carbon footprint.\n")
    
    data = {}
    
    print("📍 Transportation:")
    data["car_km"] = input("How many km did you drive today? (0 if none): ")
    data["public_transport_km"] = input("How many km by public transport? (0 if none): ")
    data["flight_km"] = input("How many km by flight? (0 if none): ")
    
    print("\n⚡ Energy Usage:")
    data["ac_hours"] = input("How many hours did you use AC? (0 if none): ")
    data["heater_hours"] = input("How many hours did you use heater? (0 if none): ")
    data["electricity_kwh"] = input("Electricity consumption in kWh? (estimate): ")
    data["water_heating_hours"] = input("Hours of water heating? (0 if none): ")
    
    print("\n🍽️ Food:")
    data["meat_meals"] = input("How many meals with meat? (0 if none): ")
    data["vegetarian_meals"] = input("How many vegetarian meals? (0 if none): ")
    
    print("\n📝 Additional Info:")
    data["additional_activities"] = input("Any other activities? (optional): ")
    data["location"] = input("Your location (city/country): ")
    data["season"] = input("Current season (summer/winter/spring/fall): ")
    
    return data

# Main execution
if __name__ == "__main__":
    try:
        # Collect user data
        user_input = collect_user_data()
        print("\n🔄 Processing your data...")
        # Run the carbon tracking agent
        result = run_carbon_agent(user_input)
        # Display results
        print("\n" + "="*50)
        print("🌍 YOUR CARBON FOOTPRINT REPORT")
        print("="*50)
        print(f"Total Emissions: {result['total_emissions']} kg CO2")
        print(f"Impact Level: {result['impact_level']}")
        print(f"Status: {result['impact_message']}")
        print("\n📊 Breakdown:")
        breakdown = result['emissions_breakdown']
        print(f"Transportation: {breakdown['transportation']['total']:.2f} kg CO2")
        print(f"Energy Usage: {breakdown['energy']['total']:.2f} kg CO2")
        print(f"Food: {breakdown['food']['total']:.2f} kg CO2")
        print("\n💡 Recommendations:")
        print(result['recommendations'])
        print("\n🎯 Summary:")
        print(result['final_summary'])
        print("\n🌐 Global Context:")
        context = result['global_context']
        print(f"Sustainable Target: {context['daily_target']}")
        print(f"Global Average: {context['global_average']}")
        print(f"Paris Agreement: {context['paris_agreement_target']}")
        print(f"\n💾 Session saved with ID: {result.get('id', 'N/A')}")
        print("\nThank you for using CarbonTrackAgent! 🌱")
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your API key and try again.")