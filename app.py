from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import random 

app = Flask(__name__)
CORS(app) 

# --- SCENARIO DATA (Used ONLY for score tracking and game state) ---
SCENARIOS = [
    {
        "id": 101,
        "is_phishing": True # The hardcoded content is always phishing
    },
    {
        "id": 102,
        "is_phishing": True 
    },
    # You can add more IDs here, but the visible email won't change.
]

# --- SIMULATED DATABASE/SCORE STORAGE ---
user_data = {
    "teacher_user_id_1": {
        "score": 50,
        "current_scenario_index": 0 
    }
}
# ----------------------------------------


# 1. API route to update score
@app.route('/api/updatescore', methods=['POST'])
def update_score():
    """Receives points data from the frontend and updates the user's score."""
    try:
        data = request.get_json()
        user_id = "teacher_user_id_1"
        points = data.get('points')
        
        if not isinstance(points, int):
            return jsonify({"success": False, "message": "Invalid points value"}), 400

        # Update the score
        user_data[user_id]["score"] += points
        
        print(f"User {user_id} scored {points}. New Score: {user_data[user_id]['score']}")

        # Set the next scenario index for the next page load (for scoring persistence)
        current_index = user_data[user_id]["current_scenario_index"]
        available_indices = [i for i in range(len(SCENARIOS)) if i != current_index]
        if available_indices:
             new_index = random.choice(available_indices)
             user_data[user_id]["current_scenario_index"] = new_index

        return jsonify({
            "success": True, 
            "new_score": user_data[user_id]["score"],
            "message": "Score updated successfully."
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500


# 2. Main route to serve the page
@app.route('/')
def index():
    user_id = "teacher_user_id_1"
    
    current_score = user_data[user_id]["score"]
    scenario_index = user_data[user_id]["current_scenario_index"]
    scenario_data = SCENARIOS[scenario_index] # Used only for its ID and is_phishing status

    # This template has the email content hardcoded to meet your requirement.
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cybersecurity Simulation</title>
        <style>
            /* --- LAYOUT AND CORE STYLES --- */
            .score-display {{ text-align: right; margin-bottom: 20px; font-size: 1.2em; font-weight: bold; color: #007bff; }}
            .email-container {{ border: 1px solid #ccc; padding: 20px; max-width: 600px; margin: 20px auto; background-color: #f9f9f9; border-radius: 8px; }}
            .phishing-link {{ color: red; cursor: pointer; text-decoration: underline; }}

            /* --- BUTTON STYLING --- */
            .action-button {{
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin-right: 10px;
                transition: background-color 0.2s, transform 0.1s;
                text-transform: uppercase; 
                letter-spacing: 0.5px;
            }}
            .action-button:active {{ transform: translateY(1px); }}
            .action-button:disabled {{ opacity: 0.6; cursor: not-allowed; }}

            .btn-safe {{ background-color: #28a745; color: white; }}
            .btn-safe:hover {{ background-color: #218838; }}

            .btn-danger {{ background-color: #dc3545; color: white; }}
            .btn-danger:hover {{ background-color: #c82333; }}
            
            .btn-neutral {{ background-color: #6c757d; color: white; }}
            .btn-neutral:hover {{ background-color: #5a6268; }}
        </style>
    </head>
    <body>

    <div class="email-container">
        
        <div class="score-display">
            Current Score: <span id="score-value">{current_score}</span> points 🏆
        </div>
        
        <h2>🚨 Action Required: Urgent Payroll Update</h2>
        
        <p>From: IT Support &lt;support@paninsingen-ps.com&gt;</p>

        <p>Dear Teacher, Please click the link below to verify your login credentials immediately to avoid payroll disruption.</p>
        
        <p>Click here: <a id="phishing-target" class="phishing-link" href="#">**[VERIFY PAYROLL]**</a></p>
        <hr>
        
        <button class="action-button btn-safe" onclick="checkAction('safe')">Report as Phishing</button>
        <button class="action-button btn-danger" onclick="checkAction('click')">Click Link (Simulated)</button>
        <button class="action-button btn-neutral" onclick="window.location.reload()">New Scenario</button>
    </div>

    <p id="result-message" style="text-align: center; margin-top: 20px; font-weight: bold;"></p>

    <script>
        // --- EMBEDDED JAVASCRIPT LOGIC ---
        let currentScore = {current_score}; 
        const phishingScenarioID = {scenario_data['id']}; 
        // We know the hardcoded email is always phishing: True
        const isCurrentScenarioPhishing = 'true';
        
        const scoreDisplay = document.getElementById('score-value');

        function checkAction(action) {{
            const resultMessage = document.getElementById('result-message');
            const isPhishing = isCurrentScenarioPhishing === 'true'; 

            // Disable action buttons after user makes a choice
            document.querySelectorAll('.action-button').forEach(btn => {{
                if (!btn.classList.contains('btn-neutral')) {{
                    btn.disabled = true;
                }}
            }});

            if (isPhishing) {{
                if (action === 'click') {{
                    resultMessage.textContent = "❌ Incorrect! Malicious link clicked. -5 Points! Check the sender address closely next time.";
                    resultMessage.style.color = 'red';
                    updateScore(-5); 
                }} else if (action === 'safe') {{
                    resultMessage.textContent = "✅ Correct! Phishing reported. +10 Points! You avoided a major threat.";
                    resultMessage.style.color = 'green';
                    updateScore(10); 
                }}
            }} else {{ 
                // This path is technically not reached since isPhishing is hardcoded to 'true' in this version.
                if (action === 'click') {{
                    resultMessage.textContent = "✅ Correct. This was a safe link in a legitimate email. +5 Points!";
                    resultMessage.style.color = 'green';
                    updateScore(5); 
                }} else if (action === 'safe') {{
                    resultMessage.textContent = "⚠️ Caution. This email was actually legitimate, but good job checking the sender. +1 Point.";
                    resultMessage.style.color = 'orange';
                    updateScore(1); 
                }}
            }}
        }}

        function updateScore(points) {{
            currentScore += points;
            scoreDisplay.textContent = currentScore;
            
            // API CALL TO PYTHON BACKEND to persist the score
            fetch('/api/updatescore', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ 
                    scenario: phishingScenarioID, 
                    points: points 
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    currentScore = data.new_score;
                    scoreDisplay.textContent = currentScore;
                }} else {{
                    console.error('Score update failed on server:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error:', error);
            }});
        }}
        // --- End of JavaScript Code ---
    </script>
    </body>
    </html>
    """
    return render_template_string(template)

# --- 3. RUN THE APPLICATION ---
if __name__ == '__main__':
    app.run(debug=True)