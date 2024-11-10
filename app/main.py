from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent.user_interaction_agent import UserInteractionAgent
from app.agent.itinerary_agent import ItineraryGenerationAgent
from app.agent.optimization_agent import OptimizationAgent
from app.agent.memory_agent import MemoryAgent
from app.agent.weather_agent import WeatherAgent  # Import WeatherAgent
from app.agent.news_agent import NewsAgent        # Import NewsAgent
import logging

# Initialize FastAPI app
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Agents
try:
    itinerary_agent = ItineraryGenerationAgent()
    optimization_agent = OptimizationAgent()
    memory_agent = MemoryAgent(uri="neo4j://localhost:7687", user="neo4j", password="password")
    weather_agent = WeatherAgent()  # Initialize the WeatherAgent
    news_agent = NewsAgent()        # Initialize the NewsAgent
    user_agent = UserInteractionAgent(
        itinerary_agent=itinerary_agent,
        # memory_agent=memory_agent,
        weather_agent=weather_agent,  # Pass the WeatherAgent to UserInteractionAgent
        news_agent=news_agent,        # Pass the NewsAgent to UserInteractionAgent
        model_name="llama3.2:3b"
    )

    logging.info("Agents initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing agents: {e}")
    raise HTTPException(status_code=500, detail="Error initializing agents.")

# In-memory storage for conversation states (consider using a DB in production)
conversation_states = {}

# Data models for requests
class UserInput(BaseModel):
    user_id: str
    message: str

@app.get("/")
async def root():
    return {"message": "Welcome to the One-Day Tour Planner!"}

# Endpoint to get the initial question to start the conversation
@app.get("/initial_question/")
async def initial_question(user_id: str):
    try:
        # Check if the user has an existing conversation state
        if user_id not in conversation_states:
            conversation_states[user_id] = {}
            logging.info(f"New conversation state initialized for user: {user_id}")

        # Retrieve the initial question from UserInteractionAgent
        question = user_agent.ask_initial_question()
        logging.info(f"Initial question sent to user {user_id}: {question}")
        return {"question": question}
    except Exception as e:
        logging.error(f"Error in /initial_question/ for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# Weather Endpoint
@app.get("/weather/")
async def fetch_weather(city: str):
    try:
        weather_info = weather_agent.get_weather(city)  # Call weather agent directly
        return {"weather": weather_info}
    except Exception as e:
        logging.error(f"Error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching weather data")

# News Endpoint
@app.get("/news/")
async def fetch_news(city: str):
    try:
        news_info = news_agent.get_news(city)  # Call news agent directly
        return {"news": news_info}
    except Exception as e:
        logging.error(f"Error fetching news for {city}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching news data")

# Endpoint to generate a response based on user input
@app.post("/generate_response/")
async def generate_response(user_input: UserInput):
    try:
        user_id = user_input.user_id
        message = user_input.message

        # Check if the user has an existing conversation state
        if user_id not in conversation_states:
            conversation_states[user_id] = {}
            logging.info(f"New conversation state initialized for user: {user_id}")

        # Update the conversation state based on user input
        user_agent.update_conversation_state(message, conversation_states[user_id])
        logging.info(f"Conversation state updated for user {user_id}: {conversation_states[user_id]}")

        # Generate a response from the UserInteractionAgent
        response = user_agent.generate_response(message, conversation_states[user_id], user_id)

        logging.info(f"Response generated for user {user_id}: {response}")
        return {"response": response, "conversation_state": conversation_states[user_id]}
    except Exception as e:
        logging.error(f"Error in /generate_response/ for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
