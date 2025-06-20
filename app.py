# app.py
# This is the final, consolidated backend server for the Keller AI project.
# It serves the landing page, the workspace app, and the API endpoint.

import os
import json
import traceback
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from a .env file for local development
load_dotenv()

# Initialize the Flask app.
# We explicitly point to the 'static' folder where our HTML files reside.
app = Flask(__name__, static_folder='static')
CORS(app) 

# --- Configure the Gemini API ---
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("FATAL ERROR: GEMINI_API_KEY not found in environment variables or .env file.")
    genai.configure(api_key=gemini_api_key)
except Exception as e:
    print(e)
    # Exit if the API key is not configured, as the app is useless without it.
    exit()

# This is the master instruction set for the AI model.
MASTER_PROMPT = """You are Keller, a world-class AI strategist. Your sole purpose is to deconstruct a user's goal into a clear, actionable roadmap.
**CRITICAL INSTRUCTION:** You MUST respond ONLY with a valid JSON object. Do not include any introductory text, closing remarks, or markdown backticks.
The JSON object must have the structure: {"goal": "The user's goal", "milestones": [{"title": "Phase 1 title", "tasks": [{"text": "A specific task.", "completed": false, "notes": ""}]}]}.
Create 3-5 distinct milestones. Each milestone must have 3-5 specific, actionable tasks. The language should be inspiring, clear, and professional."""

# --- HTML Serving Routes ---

@app.route("/")
def serve_landing_page():
    """Serves the main landing page (index.html) from the 'static' folder."""
    return send_from_directory('static', 'index.html')

@app.route("/workspace")
def serve_workspace_page():
    """Serves the main application page (workspace.html) from the 'static' folder."""
    return send_from_directory('static', 'workspace.html')

# --- API Endpoint ---

@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    """
    Handles the API request to generate a plan using the Gemini model.
    Expects a JSON body with a "goal" key.
    """
    try:
        user_goal = request.get_json().get("goal")
        if not user_goal:
            return jsonify({"error": "Goal is required."}), 400
        
        model = genai.GenerativeModel('gemini-pro')
        full_prompt = f"{MASTER_PROMPT}\n\nMy goal is: {user_goal}"

        # Relax safety settings to prevent the API from being overly cautious
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        print(f"Sending request to Gemini for goal: '{user_goal}'...")
        response = model.generate_content(full_prompt, safety_settings=safety_settings)
        print("...Response received from Gemini.")

        # Robustly check if the response was blocked by safety filters
        if not response.parts:
            block_reason = response.prompt_feedback.block_reason
            print(f"ERROR: Gemini response was blocked. Reason: {block_reason}")
            return jsonify({"error": f"The AI blocked the request due to safety concerns ({block_reason}). Please rephrase your goal."}), 500

        # Clean up the response text to ensure it's valid JSON
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()

        # Attempt to parse the cleaned text as JSON
        try:
            plan_data = json.loads(cleaned_text)
            return jsonify(plan_data)
        except json.JSONDecodeError:
            print(f"ERROR: AI response was not valid JSON after cleaning:\n{cleaned_text}")
            return jsonify({"error": "The AI returned an unexpected text format. Please try again."}), 500

    except Exception as e:
        print(f"FATAL ERROR during plan generation: {e}")
        traceback.print_exc() # Prints the full error to your server log for debugging
        return jsonify({"error": "An unexpected internal server error occurred."}), 500

# This block allows you to run the server locally for testing
if __name__ == "__main__":
    print("Keller AI Backend starting in local development mode...")
    print("Visit http://127.0.0.1:5000 for the landing page.")
    app.run(host='127.0.0.1', port=5000, debug=True)