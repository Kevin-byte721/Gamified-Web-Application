from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Needed if you scale to separate deployment, but good practice.

# NOTE: Simulated database/score storage
user_scores = {
    "teacher_user_id_1": 50,
}

# --- 1. PYTHON FUNCTION TO HANDLE API REQUESTS ---
@app.route('/api/updatescore', methods=['POST'])
def update_score():
    """Receives points data from the frontend and updates the user's score."""
    try:
        data = request.get_json()
        user_id = "teacher_user_id_1"
        points = data.get('points')
        
        # Update the score
        user_scores[user_id] += points
        
        print(f"User {user_id} scored {points}. New Score: {user_scores[user_id]}")

        return jsonify({
            "success": True, 
            "new_score": user_scores[user_id],
            "message": "Score updated successfully."
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# --- 2. PYTHON FUNCTION TO SERVE THE HTML/JS PAGE ---
@app.route('/')
def index():
    """
    Renders the main application page by embedding HTML and JavaScript 
    as a single string (template).
    """
    
    # We use Jinja templating here to allow Python variables (like the initial score)
    # to be inserted directly into the HTML/JS.
    current_score = user_scores.get("teacher_user_id_1", 0)
    
    # This entire block of content is a single Python string (the template)
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Cybersecurity Simulation (Python-Embedded)</title>
        <style>
            /* Basic styling */
            .score-display {{ text-align: right; margin-bottom: 20px; font-size: 1.2em; font-weight: bold; color: #007bff; }}
            .email-container {{ border: 1px solid #ccc; padding: 20px; max-width: 600px; margin: 20px auto; background-color: #f9f9f9; }}
            .phishing-link {{ color: red; cursor: pointer; text-decoration: underline; }}
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
        <button onclick="checkAction('safe')">Report as Phishing</button>
        <button onclick="checkAction('click')">Click Link (Simulated)</button>
        <button onclick="window.location.reload()">Refresh Scenario</button>
    </div>

    <p id="result-message" style="text-align: center; margin-top: 20px; font-weight: bold;"></p>

    <script>
        // --- JavaScript Code Embedded Here ---
        let currentScore = {current_score};
        const phishingScenarioID = 101; 
        const scoreDisplay = document.getElementById('score-value');

        function checkAction(action) {{
            const resultMessage = document.getElementById('result-message');
            const isPhishing = true; 

            if (isPhishing) {{
                if (action === 'click') {{
                    resultMessage.textContent = "❌ Incorrect! Malicious link clicked. -5 Points!";
                    resultMessage.style.color = 'red';
                    updateScore(-5); 
                }} else if (action === 'safe') {{
                    resultMessage.textContent = "✅ Correct! Phishing reported. +10 Points!";
                    resultMessage.style.color = 'green';
                    updateScore(10); 
                }}
            }}
            // ... (You could add the legitimate path logic here too)
        }}

        function updateScore(points) {{
            currentScore += points;
            scoreDisplay.textContent = currentScore;
            
            // API CALL TO PYTHON BACKEND
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
                    console.log(`Server Confirmed! New Score: ${{data.new_score}}`);
                    // Ensure local score matches server score
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
    print("Running Flask app. Access the application at: http://127.0.0.1:5000/")
    app.run(debug=True)