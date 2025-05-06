from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from groq import Groq
import json
from flask_cors import CORS

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)  # Enable CORS for API requests

# Initialize Groq client with API key
client = Groq(
    api_key="",
)

# Store conversation history for each session
conversation_history = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('sessionId', 'default')
    user_info = data.get('userInfo', {})
    
    # Initialize session if it doesn't exist
    if session_id not in conversation_history:
        conversation_history[session_id] = []
    
    # Add user message to history
    conversation_history[session_id].append({"role": "user", "content": user_message})
    
    # Create system prompt based on user info
    system_prompt = create_system_prompt(user_info)
    
    # Prepare messages for the API call
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (limit to last 10 messages to avoid context length issues)
    messages.extend(conversation_history[session_id][-10:])
    
    try:
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama3-70b-8192",
            temperature=0.7,
            max_tokens=800,
            top_p=0.9,
        )
        
        # Extract assistant response
        response = chat_completion.choices[0].message.content
        
        # Save assistant response to history
        conversation_history[session_id].append({"role": "assistant", "content": response})
        
        return jsonify({
            "response": response,
            "success": True
        })
    
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return jsonify({
            "response": "I'm having trouble connecting right now. Please try again in a moment.",
            "success": False,
            "error": str(e)
        }), 500

def create_system_prompt(user_info):
    """Create a personalized system prompt based on user info"""
    base_prompt = """You are HealthFit AI, an expert health and fitness assistant focused on providing personalized advice on exercise, nutrition, and overall wellness. 

Your primary goals are to:
1. Provide scientifically-backed health and fitness advice
2. Tailor recommendations to the user's specific needs and goals
3. Encourage safe and sustainable fitness practices
4. Offer motivational support for health and wellness journeys

Important guidelines:
- Always prioritize safety and recommend consulting healthcare professionals for medical concerns
- Provide specific, actionable advice rather than vague suggestions
- Be supportive and motivational without being judgmental
- Recognize the complexity of health and fitness journeys
- Include references to scientific research when appropriate
- Acknowledge limitations and avoid making definitive medical diagnoses

Your expertise covers:
- Exercise routines and proper technique
- Nutrition and dietary planning
- Recovery and injury prevention
- Mental wellness related to fitness
- Sleep optimization
- Goal setting and progress tracking
- Habit formation for sustainable health
"""
    
    # Add personalization if user_info is provided
    if user_info:
        personalization = "\n\nUser information for personalized advice:"
        
        if 'name' in user_info:
            personalization += f"\n- Name: {user_info['name']}"
        
        if 'age' in user_info:
            personalization += f"\n- Age: {user_info['age']}"
        
        if 'fitness_level' in user_info:
            personalization += f"\n- Fitness level: {user_info['fitness_level']}"
        
        if 'goals' in user_info:
            personalization += f"\n- Fitness goals: {user_info['goals']}"
        
        if 'health_conditions' in user_info:
            personalization += f"\n- Health conditions to consider: {user_info['health_conditions']}"
        
        if 'dietary_preferences' in user_info:
            personalization += f"\n- Dietary preferences: {user_info['dietary_preferences']}"
        
        base_prompt += personalization
    
    return base_prompt

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    data = request.json
    session_id = data.get('sessionId', 'default')
    
    # Reset conversation for the session
    if session_id in conversation_history:
        conversation_history[session_id] = []
    
    return jsonify({"success": True, "message": "Conversation history reset"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))