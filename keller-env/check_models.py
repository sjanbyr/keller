# This script inspects your API key and lists the available Gemini models.
import os
import google.generativeai as genai
from dotenv import load_dotenv

print("--- Keller AI Model Inspector ---")

try:
    # Load the .env file to get your key
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")

    # Configure the Gemini client
    genai.configure(api_key=api_key)

    print("\nSuccessfully connected to Google AI with your key.")
    print("Checking for available models that support content generation...")
    print("---------------------------------------------------------")
    
    found_models = False
    for m in genai.list_models():
      # We only care about models that can actually do what we need.
      if 'generateContent' in m.supported_generation_methods:
        print(f"-> {m.name}")
        found_models = True

    if not found_models:
        print("\nWARNING: No models supporting 'generateContent' were found.")
        print("This might indicate a permission or billing issue with your Google Cloud project.")
        
    print("---------------------------------------------------------")
    print("Diagnosis complete.")

except Exception as e:
    print(f"\nFATAL ERROR during inspection: {e}")