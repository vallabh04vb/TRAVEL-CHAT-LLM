from datetime import datetime, timedelta
import subprocess

class ItineraryGenerationAgent:
    def __init__(self, model_name="llama3.2:3b", ollama_path="C:\\Users\\Vallabh\\AppData\\Local\\Programs\\Ollama\\ollama"):
        self.model_name = model_name
        self.ollama_path = ollama_path

    def generate_or_modify_itinerary(self, conversation_state, user_id):
        city = conversation_state.get("city", "a selected city")
        interests = conversation_state.get("interests", "general interests")
        budget = conversation_state.get("budget", "flexible")
        start_date = conversation_state.get("start_date", datetime.now())
        end_date = conversation_state.get("end_date", start_date)
        days_count = (end_date - start_date).days + 1

        start_time = conversation_state.get("start_time", "6:00 AM")
        end_time = conversation_state.get("end_time", "11:00 PM")
        modification_request = conversation_state.get("modification_request", "")

        if modification_request:
            prompt = (
                f"Please modify the existing {days_count}-day itinerary for {city} based on user '{user_id}' preferences: "
                f"'{modification_request}'. Adjust the budget of {budget} and interests in {interests}."
            )
            conversation_state["modification_request"] = ""  # Clear modification request after processing
        else:
            prompt = (
                f"Create a {days_count}-day itinerary for {city} for user '{user_id}' with popular tourist spots, "
                f"based on interests in {interests} and a budget of {budget}. Start at {start_time} and end at {end_time}."
            )

        itinerary = self.generate_complete_response(prompt)
        conversation_state["existing_itinerary"] = itinerary  # Store the generated itinerary
        return itinerary

    def generate_modified_itinerary(self, conversation_state):
        modification_request = conversation_state.get("modification_request", "")
        existing_itinerary = conversation_state.get("existing_itinerary", "")
        
        if modification_request:
            prompt = f"Modify the following itinerary as per the user's request: '{modification_request}'.\n\nExisting Itinerary:\n{existing_itinerary}"
            return self.generate_complete_response(prompt)
        return "No modification request found. Please specify what you would like to modify in the itinerary."

    def suggest_places_and_activities(self, city, interests):
        prompt = (
            f"Suggest popular places to visit and activities in {city} for someone interested in {interests}. "
            "Include a mix of famous landmarks, cultural spots, natural attractions, and local experiences."
        )
        return self.generate_complete_response(prompt)

    def generate_complete_response(self, prompt):
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
                return f"An error occurred while generating the response. Details: {result.stderr.strip()}"
            
            segment = result.stdout.strip()
            response += segment
            
            if segment.endswith("...") or "Continue" in segment:
                prompt = continuation_prompt
            else:
                break

        return response
