import re
import subprocess
from datetime import datetime
from app.agent.itinerary_agent import ItineraryGenerationAgent
from app.agent.weather_agent import WeatherAgent  # Import WeatherAgent for weather queries
from app.agent.news_agent import NewsAgent  # Import NewsAgent if you decide to use it
from app.agent.memory_agent import MemoryAgent


class UserInteractionAgent:
    def __init__(self, itinerary_agent, weather_agent, news_agent, model_name="llama3.2:3b"):
        self.model_name = model_name
        self.ollama_path = r"C:\Users\Vallabh\AppData\Local\Programs\Ollama\ollama"
        # self.memory_agent = memory_agent
        self.itinerary_agent = itinerary_agent
        self.weather_agent = weather_agent  # Initialize WeatherAgent
        self.news_agent = news_agent  # Initialize NewsAgent optionally

    def generate_response(self, prompt, conversation_state, user_id):
        try:
            # Log the user_id to track which user's state is being processed
            print(f"Processing response for user: {user_id}")
            # preferences = self.memory_agent.get_preferences(user_id)
            
            # # Use preferences in your response generation, e.g.:
            # if preferences:
            #     preferred_activities = preferences.get("interests", "general interests")
            #     prompt = f"Based on your past preferences for {preferred_activities}, let's plan your day."

            # Check if the prompt is about the weather
            if "weather" in prompt.lower() or "forecast" in prompt.lower():
                city = conversation_state.get("city","Jaipur")
                
                # If city is not provided, prompt the user to specify
                if not city:
                    conversation_state["last_question"] = "city"  # Set the last question to prompt for city
                    return "Please specify the city you'd like the weather information for."
                
                # Fetch weather if city is available
                return self.weather_agent.get_weather(city)
            if "news" in prompt.lower() or "current updates" in prompt.lower():
                city = conversation_state.get("city","Paris")
                
                # If city is not provided, prompt the user to specify
                if not city:
                    conversation_state["last_question"] = "city"  # Set the last question to prompt for city
                    return "Please specify the city you'd like the  news for."
                
                # Fetch weather if city is available
                return self.news_agent.get_news(city)

            # Check if it's a generic question
            if self.is_generic_question(prompt):
                return self.handle_generic_question(prompt)

            # Handle modification request
            if conversation_state.get("modification_request"):
                response = f"Here's the modified itinerary as per your request:\n"
                response += self.itinerary_agent.generate_modified_itinerary(conversation_state)
                response += "\nIs there anything else I can help you with?"
                return response

            # Detect if the user is asking for suggestions or recommendations
            if "suggest" in prompt.lower() or "recommend" in prompt.lower() or "places to visit" in prompt.lower():
                city = conversation_state.get("city", "the selected city")
                interests = conversation_state.get("interests", "general interests")
                response = self.itinerary_agent.suggest_places_and_activities(city, interests)
                response += "\n\nShall we continue to create your itinerary?"
                return response

            # Check for missing information and prompt the user
            missing_info = self.get_missing_info(conversation_state)
            if missing_info:
                conversation_state["last_question"] = missing_info
                return self.ask_for_info(missing_info)

            # Generate and store the itinerary only if all required information is collected
            if self.all_required_information_collected(conversation_state):
                itinerary = self.itinerary_agent.generate_or_modify_itinerary(conversation_state, user_id)
                conversation_state["existing_itinerary"] = itinerary  # Store itinerary for future modifications
                return itinerary + "\nIs there anything else I can help you with?"

            # Default prompt to continue planning
            full_prompt = f"Let's continue planning your itinerary. {prompt}"
            return self.generate_complete_response(full_prompt)

        except subprocess.TimeoutExpired:
            return "The request timed out. Please try again."
        except FileNotFoundError:
            return "The Ollama executable was not found. Please check the path."
        except Exception as e:
            print("Unexpected Exception:", e)
            return f"An unexpected error occurred: {str(e)}"

    def update_conversation_state(self, user_input, conversation_state):
        # Update conversation state logic
        last_question = conversation_state.get("last_question")
        
        if last_question == "city":
            conversation_state["city"] = user_input
            conversation_state["last_question"] = None  # Reset after storing

        elif last_question == "date":
            conversation_state["date"] = user_input
            parsed_dates, start_time, end_time = self.parse_dates_and_times(user_input)
            if parsed_dates:
                conversation_state["start_date"] = parsed_dates[0]
                conversation_state["end_date"] = parsed_dates[1]
                if start_time and end_time:
                    conversation_state["start_time"] = start_time
                    conversation_state["end_time"] = end_time
                conversation_state["last_question"] = None  # Reset after successful parse
            else:
                return "Please provide a valid date format, like '10 Nov 2024' or '10 Nov to 12 Nov 2024'."

        elif last_question == "interests":
            conversation_state["interests"] = user_input
            conversation_state["last_question"] = None

        elif last_question == "budget":
            conversation_state["budget"] = user_input
            conversation_state["last_question"] = None

        elif last_question == "starting_point":
            conversation_state["starting_point"] = user_input
            conversation_state["last_question"] = None

        if "modify" in user_input.lower() or "change" in user_input.lower() or "adjust" in user_input.lower():
            conversation_state["modification_request"] = user_input

    def get_missing_info(self, conversation_state):
        """
        Returns the first missing piece of information required to complete the itinerary.

        Args:
            conversation_state (dict): The current state of the conversation.

        Returns:
            str: Key for the missing information or None if all required information is present.
        """
        for key in ["city", "date", "interests", "budget", "starting_point"]:
            if not conversation_state.get(key):
                return key
        return None

    def ask_for_info(self, info_type):
        """
        Returns a prompt asking for specific missing information.

        Args:
            info_type (str): The type of information needed.

        Returns:
            str: A prompt asking the user for the required information.
        """
        prompts = {
            "city": "Which city would you like to visit?",
            "date": "What date are you planning for, and if applicable, what start and end times?",
            "interests": "What are your interests? (e.g., historical sites, food, shopping)",
            "budget": "What is your budget for the day?",
            "starting_point": "Where would you like to start your day?"
        }
        return prompts.get(info_type, "Please provide more information.")

    def parse_dates_and_times(self, date_str):
        """
        Parses start and end dates along with start and end times from user input.

        Args:
            date_str (str): The string containing date and time information.

        Returns:
            tuple: Start and end dates, start time, and end time if available.
        """
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

        date_pattern = r"(\d{1,2}\s+\w+\s+\d{4})"
        dates = re.findall(date_pattern, date_str)

        time_pattern = r"(\d{1,2}:\d{2}\s*(?:AM|PM))"
        times = re.findall(time_pattern, date_str)

        if len(dates) == 1:
            start_date = datetime.strptime(dates[0], "%d %b %Y")
            end_date = start_date
        elif len(dates) == 2:
            start_date = datetime.strptime(dates[0], "%d %b %Y")
            end_date = datetime.strptime(dates[1], "%d %b %Y")
        else:
            return None, None, None

        start_time = times[0] if len(times) >= 1 else None
        end_time = times[1] if len(times) >= 2 else None

        return (start_date, end_date), start_time, end_time

    def all_required_information_collected(self, conversation_state):
        """
        Checks if all required information for generating an itinerary is present.

        Args:
            conversation_state (dict): The current state of the conversation.

        Returns:
            bool: True if all required information is collected, False otherwise.
        """
        required_keys = ["city", "date", "interests", "budget", "starting_point"]
        return all(key in conversation_state for key in required_keys)

    def is_generic_question(self, prompt):
        """
        Detects if the user's input is a generic question.

        Args:
            prompt (str): The user's input prompt.

        Returns:
            bool: True if the input matches a generic question, False otherwise.
        """
        generic_phrases = ["how are you", "tell me a joke", "who are you", "what's your purpose", "help"]
        return any(phrase in prompt.lower() for phrase in generic_phrases)

    def handle_generic_question(self, prompt):
        """
        Handles common generic questions.

        Args:
            prompt (str): The user's input prompt.

        Returns:
            str: The response to the generic question.
        """
        if "how are you" in prompt.lower():
            return "I'm here to help you plan your day! How can I assist you further?"
        elif "tell me a joke" in prompt.lower():
            return "Why did the tourist bring a ladder to the museum? Because they wanted to reach new heights!"
        elif "who are you" in prompt.lower():
            return "I'm your travel assistant, here to help you plan an amazing one-day itinerary!"
        elif "what's your purpose" in prompt.lower():
            return "I'm here to help you plan your day and ensure you have a great travel experience."
        elif "help" in prompt.lower():
            return "I'm here to assist you with itinerary planning. Just ask me for suggestions, recommendations, or itinerary details!"
        else:
            return "I'm here to help with your travel itinerary. Let me know how I can assist you."

    def generate_complete_response(self, prompt):
        """
        Generates a complete response using the LLM, handling potential continuation prompts.

        Args:
            prompt (str): The prompt to generate a response for.

        Returns:
            str: The generated response.
        """
        response = ""
        continuation_prompt = "Continue the response."
        
        while True:
            result = subprocess.run(
                [self.ollama_path, "run", self.model_name, prompt],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=180
            )
            if result.returncode != 0:
                print("Error details from stderr:", result.stderr.strip())
                return f"An error occurred while generating the itinerary. Details: {result.stderr.strip()}"
            
            segment = result.stdout.strip()
            response += segment
            
            if segment.endswith("...") or "Continue" in segment:
                prompt = continuation_prompt
            else:
                break

        return response

    def ask_initial_question(self):
        return "Hello! Let's plan your day. Which city would you like to visit?"
