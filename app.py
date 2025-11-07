from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)

# --- SCENARIO DATA DEFINITIONS ---

# 1. Phishing Email Scenario (ID 101)
SCENARIO_PHISHING = {
    "id": 101,
    "type": "phishing",
    "title": "🚨 Action Required: Urgent Payroll Update",
    "instructions": "Review this email. Decide whether to 'Report as Phishing' or 'Click Link (Simulated)'.",
    "is_phishing": True, # Actual state of the email content
    "email_sender": "support@paninsinge-ps.com", #"IT Support <support@paninsinge-ps.com>"
    "email_subject": "Dear Teacher, Please click the link below to verify your login credentials immediately to avoid payroll disruption.",
    "email_link_text": "[VERIFY PAYROLL]",
    # Scoring for Phishing (Correctly reporting a phishing email gives +10, falling for it gives -5)
    "score_report_correct": "✅ Correct! Phishing reported. +10 Points! You avoided a major threat.",
    "score_accept_wrong": "❌ Incorrect! Malicious link clicked. -5 Points! Check the sender address closely next time.",
    "score_report_wrong": "⚠️ Caution. This email was actually legitimate, but good job checking the sender. +1 Point.",
    "score_accept_correct": "✅ Correct. This was a safe link in a legitimate email. +5 Points!"
}

# 2. Multi-Factor Authentication Scenario (ID 102)
SCENARIO_MFA = {
    "id": 102,
    "type": "mfa",
    "title": "📱 Multi-Factor Authentication Challenge",
    "instructions": "You've attempted to log in from a new location. Enter the 6-digit code displayed on your authenticator app (or sent to your phone).",
    "correct_code": "123456", # Simulated correct code for training purposes
    "result_success": "✅ Success! MFA verified. +10 Points! Layered security is crucial.",
    "result_failure": "❌ Failure. Incorrect code entered. -5 Points! Always verify the code carefully and be wary of unusual login attempts."
}

# 3. Password Strength Scenario (ID 106)
SCENARIO_PASSWORD = {
    "id": 106,
    "type": "password",
    "title": "🔐 Mandatory Password Update",
    "instructions": "Please create a new, secure password for your staff account.",
    "result_strong": "✅ Success! Strong password created. +15 Points!",
    "result_weak": "❌ Failure. Password too weak. -5 Points! Must contain upper, lower, number, and special characters."
}

# 4. Final Score Scenario (ID 999) - NEW: Passive scenario to show results
SCENARIO_FINAL_SCORE = {
    "id": 999,
    "type": "final_score",
    "title": "🎉 Simulation Complete!",
    "instructions": "You have successfully finished all training modules. Review your performance below."
}

# The main list defining the game flow
SCENARIOS = [SCENARIO_PHISHING, SCENARIO_MFA, SCENARIO_PASSWORD, SCENARIO_FINAL_SCORE]
NUM_SCENARIOS = len(SCENARIOS)

# --- SIMULATED DATABASE/SCORE STORAGE ---
user_data = {
    "teacher_user_id_1": {
        "score": 0, # SCORE STARTS AT ZERO
        "current_scenario_index": 0
    }
}
# ----------------------------------------


# 1. API route to update score and advance scenario
@app.route('/api/updatescore', methods=['POST'])
def update_score():
    """
    Receives points data from the frontend, updates the user's score, and conditionally 
    advances the scenario index if it's not the last scenario (the final_score screen).
    """
    try:
        data = request.get_json()
        user_id = "teacher_user_id_1"
        points = data.get('points')

        if not isinstance(points, int):
            return jsonify({"success": False, "message": "Invalid points value"}), 400

        # Update the score
        user_data[user_id]["score"] += points

        # Advance the scenario index ONLY if it's not the last one (the new final_score page)
        current_index = user_data[user_id]["current_scenario_index"]

        if current_index < NUM_SCENARIOS - 1:
            # Advance to the next index (This will advance from Password to Final Score)
            user_data[user_id]["current_scenario_index"] += 1
        else:
            # If it's the final score scenario, keep the index the same
            pass

        return jsonify({
            "success": True,
            "new_score": user_data[user_id]["score"],
            "message": "Score updated successfully."
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# 2. API route to reset score and scenario
@app.route('/api/resetgame', methods=['POST'])
def reset_game():
    """Resets the user's score to 0 and the scenario index to 0."""
    user_id = "teacher_user_id_1"

    # Reset the data
    user_data[user_id]["score"] = 0
    user_data[user_id]["current_scenario_index"] = 0

    return jsonify({
        "success": True,
        "new_score": 0,
        "message": "Game reset successfully."
    })


# 3. Main route to serve the page
@app.route('/')
def index():
    user_id = "teacher_user_id_1"

    current_score = user_data[user_id]["score"]

    # Get the scenario data based on the user's current index
    scenario_index = user_data[user_id]["current_scenario_index"]
    scenario_data = SCENARIOS[scenario_index]
    scenario_json = json.dumps(scenario_data)

    # Detection logic for button labels
    is_final_results_screen = scenario_data["type"] == "final_score"
    is_pre_final_scenario = scenario_index == NUM_SCENARIOS - 2

    if is_final_results_screen:
        next_button_label = "Simulation Complete" # Not displayed but defined
    elif is_pre_final_scenario:
        next_button_label = "Proceed to Results"
    else:
        next_button_label = "Next Scenario"

    # --- DYNAMIC HTML CONTENT GENERATION (Inner part of the scenario card) ---
    template_content = ""

    if scenario_data["type"] == "phishing":

        template_content = f"""
        <div class="scenario-content email-container">

            <h2 style="color: #dc3545; margin-bottom: 10px;">{scenario_data['title']}</h2>

            <p style="font-size: 1.1em; margin-bottom: 15px;">{scenario_data['instructions']}</p>

            <div class="email-body">
                <p>From: {scenario_data['email_sender']}</p>
                <p>{scenario_data['email_subject']}</p>

                <p>
                    Click here: <a id="phishing-target" class="phishing-link" href="#" onclick="event.preventDefault();">{{scenario_data['email_link_text']}}</a>
                </p>
            </div>
            <hr style="margin: 15px 0;"> <div class="button-group" style="margin-top: 15px;"> <button class="action-button btn-safe" id="report-btn" onclick="checkPhishingAction(true)">Report as Phishing</button>
                <button class="action-button btn-danger" id="click-btn" onclick="checkPhishingAction(false)">Click Link (Simulated)</button>
                <button class="action-button btn-neutral next-scenario-btn" id="next-btn" style="display:none;">{next_button_label}</button>
            </div>

            <p id="result-message" class="result-message"></p>
        </div>

        <script>
            function checkPhishingAction(reportedPhishing) {{
                const resultMessage = document.getElementById('result-message');
                const reportBtn = document.getElementById('report-btn');
                const clickBtn = document.getElementById('click-btn');

                // Disable interaction elements
                reportBtn.disabled = true;
                clickBtn.disabled = true;

                reportBtn.style.display = 'none';
                clickBtn.style.display = 'none';

                let pointsChange;
                let resultText;
                let resultColor;

                const isPhishing = scenarioData.is_phishing;

                // --- SCORING LOGIC ---
                if (isPhishing) {{
                    // Scenario is PHISHING (User should report)
                    if (reportedPhishing) {{
                        pointsChange = 10;
                        resultText = scenarioData.score_report_correct;
                        resultColor = 'green';
                    }} else {{
                        pointsChange = -5;
                        resultText = scenarioData.score_accept_wrong;
                        resultColor = 'red';
                    }}
                }} else {{
                    // Scenario is LEGITIMATE
                    if (!reportedPhishing) {{
                        pointsChange = 5;
                        resultText = scenarioData.score_accept_correct;
                        resultColor = 'green';
                    }} else {{
                        pointsChange = -1;
                        resultText = scenarioData.score_report_wrong;
                        resultColor = 'orange';
                    }}
                }}
                // --- END SCORING LOGIC ---

                resultMessage.textContent = resultText;
                resultMessage.style.color = resultColor;

                // Trigger score update
                updateScore(pointsChange);
            }}
        </script>
        """

    elif scenario_data["type"] == "mfa":

        template_content = f"""
        <div class="scenario-content mfa-container">

            <h2 style="color: #6f42c1; margin-bottom: 10px;">{scenario_data['title']}</h2>

            <p style="font-size: 1.1em; margin-bottom: 15px;">{scenario_data['instructions']}</p>

            <div class="input-group" style="justify-content: center; display: flex;">
                <input type="text" id="mfa-input" maxlength="6" pattern="\\d{{6}}" placeholder="Enter 6-digit code"
                       style="width: 150px; text-align: center; font-size: 1.2em; padding: 10px; border: 2px solid #ccc;">
            </div>

            <p style="font-size: 0.9em; color: #888; margin-top: 15px;">
                The correct code is {scenario_data['correct_code']} for simulation purposes.
            </p>

            <hr style="margin: 20px 0;">

            <div class="button-group">
                <button class="action-button btn-mfa" id="verify-btn" onclick="checkMFAAction()">Verify Code</button>
                <button class="action-button btn-neutral next-scenario-btn" id="next-btn" style="display:none;">{next_button_label}</button>
            </div>

            <p id="result-message" class="result-message"></p>
        </div>

        <script>
            // --- MFA SCENARIO FUNCTIONS ---
            function checkMFAAction() {{
                const resultMessage = document.getElementById('result-message');
                const mfaInput = document.getElementById('mfa-input');
                const verifyBtn = document.getElementById('verify-btn');

                mfaInput.disabled = true;
                verifyBtn.style.display = 'none';

                const enteredCode = mfaInput.value.trim();
                const correctCode = scenarioData.correct_code;

                let pointsChange;
                let resultText;
                let resultColor;

                if (enteredCode === correctCode) {{
                    pointsChange = 10;
                    resultText = scenarioData.result_success;
                    resultColor = 'green';
                }} else {{
                    pointsChange = -5;
                    resultText = scenarioData.result_failure;
                    resultColor = 'red';
                }}

                resultMessage.textContent = resultText;
                resultMessage.style.color = resultColor;

                // Trigger score update
                updateScore(pointsChange);
            }}
        </script>
        """

    elif scenario_data["type"] == "password":

        template_content = f"""
        <div class="scenario-content password-container">

            <h2 style="color: #007bff; margin-bottom: 10px;">{scenario_data['title']}</h2>

            <p style="font-size: 1.1em; margin-bottom: 15px;">{scenario_data['instructions']}</p>

            <ul class="req-list">
                <li>- Must be at least 12 characters long</li>
                <li>- Must contain lowercase letters</li>
                <li>- Must contain UPPERCASE letters</li>
                <li>- Must contain at least one number</li>
                <li>- Must contain at least one special character (!@#$%^&*)</li>
            </ul>

            <div class="input-group">
                <input type="password" id="password-input" placeholder="Enter new password here..." onkeyup="updateStrength()">
                <span id="toggle-password" onclick="togglePasswordVisibility()">SHOW</span>
            </div>

            <div>
                <div id="strength-bar"></div>
                <div id="strength-text">Type to check strength...</div>

                <hr style="margin: 20px 0;">

                <div class="button-group">
                    <button class="action-button btn-primary" id="check-btn" onclick="checkPasswordAction()">Submit Password</button>
                    <button class="action-button btn-neutral next-scenario-btn" id="next-btn" style="display:none;">{next_button_label}</button>
                </div>
            </div>

            <p id="result-message" class="result-message"></p>
        </div>

        <script>
            // --- PASSWORD SCENARIO FUNCTIONS ---
            function getPasswordScore(password) {{
                let score = 0;
                if (password.length >= 12) {{ score++; }}
                if (/[a-z]/.test(password)) {{ score++; }}
                if (/[A-Z]/.test(password)) {{ score++; }}
                if (/[0-9]/.test(password)) {{ score++; }}
                if (/[!@#$%^&*()]/.test(password)) {{ score++; }}
                return score;
            }}

            function updateStrength() {{
                const password = document.getElementById('password-input').value;
                const score = getPasswordScore(password);
                const scorePercentage = (score / 5) * 100;

                const strengthBar = document.getElementById('strength-bar');
                const strengthText = document.getElementById('strength-text');

                strengthBar.style.width = scorePercentage + '%';

                let color = '#ddd';
                let text = 'Type to check strength...';

                if (score === 5) {{ color = '#28a745'; text = 'STRONG'; }}
                else if (score >= 3) {{ color = '#ffc107'; text = 'MEDIUM'; }}
                else if (score >= 1) {{ color = '#dc3545'; text = 'WEAK'; }}
                else if (password.length > 0) {{ text = 'Very Weak'; }}

                strengthBar.style.backgroundColor = color;
                strengthText.textContent = text;
            }}

            function togglePasswordVisibility() {{
                const input = document.getElementById('password-input');
                const icon = document.getElementById('toggle-password');
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                icon.textContent = type === 'password' ? 'SHOW' : 'HIDE';
            }}

            function checkPasswordAction() {{
                const resultMessage = document.getElementById('result-message');
                const password = document.getElementById('password-input').value;
                const score = getPasswordScore(password);
                const checkBtn = document.getElementById('check-btn');

                let pointsChange;
                let resultText;
                let resultColor;

                if (score === 5) {{
                    pointsChange = 15;
                    resultText = scenarioData.result_strong;
                    resultColor = 'green';
                }} else {{
                    pointsChange = -5;
                    resultText = scenarioData.result_weak;
                    resultColor = 'red';
                }}

                resultMessage.textContent = resultText;
                resultMessage.style.color = resultColor;

                document.getElementById('password-input').disabled = true;
                checkBtn.style.display = 'none';

                // Trigger score update
                updateScore(pointsChange);
            }}

            document.addEventListener('DOMContentLoaded', updateStrength);
        </script>
        """

    elif scenario_data["type"] == "final_score": # Final score page update

        template_content = f"""
        <div class="scenario-content final-score-container">

            <h2 style="color: #28a745; margin-bottom: 20px; font-size: 2em;">{scenario_data['title']}</h2>

            <p style="font-size: 1.2em; margin-bottom: 30px; color: #333;">{scenario_data['instructions']}</p>


<div style="font-size: 3.5em; font-weight: 900; color: #007bff; margin-bottom: 30px; padding: 20px; border: 2px solid #007bff; border-radius: 8px; background-color: #e9f5ff;">
                <div style="font-size: 0.4em; font-weight: 600; color: #666; margin-bottom: 10px;">Your Total Score</div>
                <span id="final-score-value">{current_score}</span> 
                <span style="font-size: 0.3em; font-weight: 600;">Points</span>
            </div>

            <p style="font-style: italic; color: #6c757d; font-size: 0.9em;">
                Click the "Restart Simulation" button above to begin a new training session.
            </p>


</div>
        """

    else:
        template_content = "<div class='scenario-content'><h2>Error: Scenario type not recognized.</h2></div>"


    # --- BASE HTML TEMPLATE (Includes Styles and Common JS) ---
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cybersecurity Simulation</title>
        <style>
            /* --- GLOBAL LAYOUT AND CORE STYLES --- */
            body {{
                font-family: sans-serif;
                background-color: #f0f2f5;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
            }}

            /* Main Card Wrapper */
            .scenario-card {{
                padding: 30px;
                width: 95%;
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                box-sizing: border-box;
                /* Set a minimum height for consistency across scenarios */
                min-height: 450px;
            }}

            /* Score Header inside the card */
            .score-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                border-bottom: 1px solid #eee; /* Visual separator */
                padding-bottom: 15px;
            }}

            .score-display {{
                font-size: 1.2em;
                font-weight: bold;
                color: #007bff;
                text-align: left;
                margin-bottom: 0;
            }}

            .reset-button {{
                padding: 8px 15px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.2s;
                font-size: 0.9em;
            }}
            .reset-button:hover {{ background-color: #5a6268; }}

            /* --- Mobile Layout Adjustments (Score Header) --- */
            @media (max-width: 500px) {{
                .score-header {{
                    flex-direction: column; /* Stack vertically on small screens */
                    align-items: stretch;
                }}
                .score-display {{
                    text-align: center; /* Center the score text */
                    margin-bottom: 15px; /* Add space below score before button */
                }}
            }}


            .scenario-content {{
                text-align: center;
            }}

            .email-body p {{ text-align: left; line-height: 1.4; margin-bottom: 10px; }}
            .phishing-link {{ color: #dc3545; cursor: pointer; text-decoration: underline; font-weight: bold; }}
            .result-message {{ text-align: center; margin-top: 20px; font-weight: bold; min-height: 1.2em; }}

            /* Password Requirement List Styles */
            .req-list {{ text-align: left; margin: 15px 0 25px 0; padding-left: 20px; font-size: 0.9em; }}
            .req-list li {{ list-style-type: none; margin-bottom: 5px; color: #444; }}

            /* Password Input and Indicator */
            .input-group {{ position: relative; margin-bottom: 15px; }}
            #password-input {{ box-sizing: border-box; padding: 12px; width: 100%; padding-right: 60px; border: 1px solid #ccc; border-radius: 6px; font-size: 1.0em; }}
            #toggle-password {{ position: absolute; top: 50%; right: 15px; transform: translateY(-50%); cursor: pointer; font-size: 0.8em; font-weight: 600; color: #007bff; user-select: none; }}
            #strength-bar {{ height: 10px; width: 0; background-color: #ddd; border-radius: 5px; transition: width 0.3s ease-in-out, background-color 0.3s ease-in-out; margin-bottom: 15px; }}
            #strength-text {{ font-weight: bold; margin-bottom: 20px; min-height: 1.2em; color: #666; }}


            /* --- RESPONSIVE BUTTON CONTAINER --- */
            .button-group {{
                display: flex;
                flex-direction: column; /* MOBILE FIRST: Stack buttons vertically */
                gap: 10px; /* Spacing between stacked buttons */
                margin-top: 20px;
            }}

            /* --- BUTTON STYLING --- */
            .action-button {{
                padding: 12px 15px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                width: 100%; /* Full width on mobile */
                transition: background-color 0.2s, transform 0.1s;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0;
            }}
            .action-button:active {{ transform: translateY(1px); }}
            .action-button:disabled {{ opacity: 0.6; cursor: not-allowed; }}

            /* Desktop/Tablet Layout (Screen width > 500px) */
            @media (min-width: 500px) {{
                .button-group {{
                    flex-direction: row; /* Switch to horizontal layout */
                    justify-content: space-around;
                }}
                .action-button {{
                    width: auto;
                    flex-grow: 1;
                    margin: 0 5px;
                    max-width: 45%; /* Prevent buttons from getting too wide */
                }}
            }}

            .btn-primary {{ background-color: #007bff; color: white; }}
            .btn-primary:hover {{ background-color: #0056b3; }}
            .btn-safe {{ background-color: #28a745; color: white; }}
            .btn-safe:hover {{ background-color: #1e7e34; }}
            .btn-danger {{ background-color: #dc3545; color: white; }}
            .btn-danger:hover {{ background-color: #c82333; }}
            .btn-neutral {{ background-color: #6c757d; color: white; }}
            .btn-neutral:hover {{ background-color: #5a6268; }}
            .btn-mfa {{ background-color: #6f42c1; color: white; }}
            .btn-mfa:hover {{ background-color: #5a3598; }}
        </style>
    </head>
    <body>

    <div class="scenario-card">
        <div class="score-header">
            <div class="score-display">
                Current Score: <span id="score-value">{current_score}</span> points 🏆
            </div>
            <button class="reset-button" onclick="resetGame()">Restart Simulation</button>
        </div>

        {template_content}
    </div>


    <script>
        // --- COMMON JAVASCRIPT LOGIC ---
        let currentScore = {current_score};
        const scenarioData = {scenario_json};
        const scoreDisplay = document.getElementById('score-value');

        // Function to handle the "Next Scenario" button click (reloads page)
        function handleNextScenario() {{
            // Since the backend has already advanced the index in updateScore(),
            // we just need to reload the page to load the next scenario state (which will be the final score page).
            window.location.reload();
        }}

        // Function to handle the "Restart Simulation" button click (resets score and reloads)
        function resetGame() {{
            // API CALL TO PYTHON BACKEND to reset the game state
            fetch('/api/resetgame', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }}
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    // Force a full reload to show the first scenario and new score
                    window.location.reload();
                }} else {{
                    console.error('Game reset failed on server:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error during reset:', error);
            }});
        }}


        document.addEventListener('DOMContentLoaded', () => {{
             // Find all elements with the next-scenario-btn class and attach the click handler
             document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                btn.onclick = handleNextScenario;
             }});
        }});

        function updateScore(points) {{
            currentScore += points;
            scoreDisplay.textContent = currentScore;

            // Show the next scenario button after scoring
            document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                btn.style.display = 'block';
            }});

            // API CALL TO PYTHON BACKEND to persist the score and advance the index
            fetch('/api/updatescore', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    scenario: scenarioData.id,
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
        // --- End of Common JavaScript Code ---
    </script>

    </body>
    </html>
    """
    return render_template_string(template)

# --- 4. RUN THE APPLICATION ---
if __name__ == '__main__':
    app.run(debug=True)