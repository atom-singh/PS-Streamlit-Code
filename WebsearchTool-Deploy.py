# streamlit_web_tool.py
import streamlit as st
import json
import requests
from openai import OpenAI
from tavily import TavilyClient

# ----------------------------
# Initialize clients
# ----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Store your key in .streamlit/secrets.toml
#openai_client = OpenAI(api_key="enter your key")  # Replace with your OpenAI API key
tavily_client = TavilyClient(st.secrets["TAVILY_API_KEY"])    # Store your key in .streamlit/secrets.toml
#tavily_client = TavilyClient("enter your key")    # Replace with your Tavily API key
weather_api_key = st.secrets["WEATHER_API_KEY"]            # Store your key in .streamlit/secrets.toml
#weather_api_key = "enter your key"            # Replace with OpenWeatherMap API key

# ----------------------------
# Tool Functions
# ----------------------------
def web_search(query):
    response = tavily_client.search(query=query, max_results=3)
    results = response.get("results", [])
    content = "\n\n".join([r.get("content", "") for r in results])
    return content or "No results found."

def get_weather(location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api_key}&units=metric"
    response = requests.get(url).json()
    if "main" in response:
        temp = response["main"]["temp"]
        return f"The temperature in {location} is {temp}°C."
    else:
        return f"Could not fetch weather for {location}. Please check the city name."

# ----------------------------
# Streamlit App Layout
# ----------------------------
st.set_page_config(page_title="AI Web & Weather Assistant", page_icon="🌐", layout="wide")

st.title("🌐 AI Web & Weather Assistant")
st.markdown(
    "This app uses GPT-4 with **web search** and **weather tools** to provide real-time answers.\n"
    "Type a query and see results instantly!"
)

# Sidebar for selecting tool
tool_choice = st.sidebar.radio("Select Tool", ["Web Search", "Weather", "AI Smart Query"])

# User input
user_input = st.text_input("Enter your query or city:", "")

# Display results
if st.button("Get Results") and user_input:
    with st.spinner("Fetching results..."):
        if tool_choice == "Web Search":
            results = web_search(user_input)
            st.subheader("🔍 Web Search Results")
            st.write(results)
        elif tool_choice == "Weather":
            results = get_weather(user_input)
            st.subheader("🌡 Weather Info")
            st.write(results)
        elif tool_choice == "AI Smart Query":
            # Using GPT-4 with tools
            tools_to_use = [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Getting updated info from web",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current temperature",
                        "parameters": {
                            "type": "object",
                            "properties": {"location": {"type": "string"}},
                            "required": ["location"],
                            "additionalProperties": False
                        },
                        "strict": True
                    }
                }
            ]
            
            # GPT-4 tool call
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role":"user","content": user_input}],
                tools=tools_to_use
            )

            # Extract tool call
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            if tool_name == "web_search":
                result = web_search(arguments["query"])
            elif tool_name == "get_weather":
                result = get_weather(arguments["location"])
            else:
                result = "Tool not found."

            # Final GPT response with tool result
            final_response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role":"user","content": user_input},
                    {"role":"assistant","tool_calls":[tool_call]},
                    {"role":"tool","tool_call_id": tool_call.id, "name": tool_name, "content": result}
                ]
            )
            st.subheader("🤖 AI Response")
            st.write(final_response.choices[0].message.content)
else:
    st.info("Enter a query above and click 'Get Results'.")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit and GPT-4")
