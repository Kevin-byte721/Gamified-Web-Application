from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app) 

# --- SCENARIO DATA ---
# Define all available scenarios here

SCENARIO_PHISHING = {
    "id": 101,
    "type": "phishing",
    "title": "🚨 Action Required: Urgent Payroll Update",
    "instructions": "Review this email. Decide whether to **'Report as Phishing'** or **'Click Link (Simulated)'**.",
    "is_phishing": True, # Actual state of the email content
    # Sender is unchanged, as requested
    "email_sender": "support@paninsingen-ps.com <support@paninsingen-ps.com>", 
    "email_subject": "Dear Teacher, Please click the link below to verify your login credentials immediately to avoid payroll disruption.",
    "email_link_text": "**[VERIFY PAYROLL]**",
    # Scoring for Phishing (Correctly reporting a phishing email gives +10, falling for it gives -5)
    "score_report_correct": "✅ Correct! Phishing reported. +10 Points! You avoided a major threat.",
    "score_accept_wrong": "❌ Incorrect! Malicious link clicked. -5 Points! Check the sender address closely next time.",
}

SCENARIO_PASSWORD = {
    "id": 106,
    "type": "password",
    "title": "🔐 Mandatory Password Update",
    "instructions": "Please create a new, secure password for your staff account.",
    "result_strong": "✅ Success! Strong password created. +15 Points!",
    "result_weak": "❌ Failure. Password too weak. -5 Points! Must contain upper, lower, number, and special characters."
}

# New Scenario for Multi-Factor Authentication (MFA)
SCENARIO_MFA = {
    "id": 107,
    "type": "mfa", 
    "title": "📱 Multi-Factor Authentication Setup",
    "instructions": "Due to a recent policy change, all accounts must enable Multi-Factor Authentication (MFA). Click 'Enable MFA' to continue.",
    "action_button_text": "Enable MFA",
    "result_success": "✅ Success! MFA enabled. Your account is now much safer. +10 Points!",
}

# The order defines the flow of the game
# PHISHING -> PASSWORD -> MFA (New) -> PHISHING (Loop)
SCENARIOS = [SCENARIO_PHISHING, SCENARIO_PASSWORD, SCENARIO_MFA]


# --- SIMULATED DATABASE/SCORE STORAGE ---
user_data = {
    "teacher_user_id_1": {
        "score": 50,
        # Index 0 points to SCENARIO_PHISHING
        "current_scenario_index": 0 
    }
}
# ----------------------------------------


# 1. API route to update score
@app.route('/api/updatescore', methods=['POST'])
def update_score():
    """Receives points data from the frontend, updates the user's score, and advances the scenario index."""
    try:
        data = request.get_json()
        user_id = "teacher_user_id_1"
        points = data.get('points')
        
        if not isinstance(points, int):
            return jsonify({"success": False, "message": "Invalid points value"}), 400

        user_data[user_id]["score"] += points
        
        # Advance the scenario index, wrapping around when reaching the end
        num_scenarios = len(SCENARIOS)
        current_index = user_data[user_id]["current_scenario_index"]
        user_data[user_id]["current_scenario_index"] = (current_index + 1) % num_scenarios


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
    
    # Get the scenario data based on the user's current index
    scenario_index = user_data[user_id]["current_scenario_index"]
    scenario_data = SCENARIOS[scenario_index]
    scenario_json = json.dumps(scenario_data) 

    # --- HTML TEMPLATE GENERATION (Based on Scenario Type) ---
    if scenario_data["type"] == "password":
        
        # NOTE: Renamed 'prompt-container' to 'scenario-card' to avoid nested container confusion
        template_content = f"""
        <div class="scenario-card">
            
            <div class="global-score-display">
                Current Score: <span id="score-value">{current_score}</span> points 🏆
            </div>
            
            <h2 style="color: #007bff; margin-bottom: 10px;">{scenario_data['title']}</h2>
            <p style="font-size: 1.1em; margin-bottom: 15px;">{scenario_data['instructions']}</p>
            
            <ul class="req-list">
                <li>- Must be at least 12 characters long</li>
                <li>- Must contain **lowercase** letters</li>
                <li>- Must contain **uppercase** letters</li>
                <li>- Must contain at least one **number**</li>
                <li>- Must contain at least one **special character** (!@#$%^&*)</li>
            </ul>
            
            <div class="input-group">
                <input type="password" id="password-input" placeholder="Enter new password here..." onkeyup="updateStrength()">
                <span id="toggle-password" onclick="togglePasswordVisibility()">SHOW</span>
            </div>

            <div>
                <div id="strength-bar"></div>
                <div id="strength-text">Type to check strength...</div>

                <hr style="margin: 20px 0;">
                
                <button class="action-button btn-primary" id="check-btn" onclick="checkPasswordAction()">Submit Password</button>
                <button class="action-button btn-neutral next-scenario-btn" id="next-btn" style="display:none;">Next Scenario</button>
            </div>
            
            <p id="result-message" style="text-align: center; margin-top: 20px; font-weight: bold;"></p>
        </div>

        <script>
            function getPasswordScore(password) {{
                let score = 0;
                if (password.length >= 12) {{ score++; }}
                if (/[a-z]/.test(password)) {{ score++; }}
                if (/[A-Z]/.test(password)) {{ score++; }}
                if (/[0-9]/.test(password)) {{ score++; }}
                if (/[!@#$%^&*()]/.test(password)) {{ score++; }}
                return score;
            }}

            function checkPasswordAction() {{
                const resultMessage = document.getElementById('result-message');
                const password = document.getElementById('password-input').value;
                const score = getPasswordScore(password);
                const nextBtn = document.getElementById('next-btn');
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
                // Trigger score update, which will handle the reload
                updateScore(pointsChange);
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

            document.addEventListener('DOMContentLoaded', updateStrength);
        </script>
        """

    elif scenario_data["type"] == "phishing":
        
        template_content = f"""
        <!-- Styled to match the user's screenshot. Renamed 'prompt-container' to 'scenario-card' -->
        <div class="scenario-card email-container">
            
            <div class="global-score-display">
                Current Score: <span id="score-value">{current_score}</span> points 🏆
            </div>

            <h2 style="color: #444; margin-bottom: 20px;">
                <span style="color: #dc3545;">{scenario_data['title'].split(':')[0]}:</span> {scenario_data['title'].split(':')[1].strip()}
            </h2>
            
            <!-- UPDATED SENDER LINE for explicit formatting request -->
            <p class="email-sender-line">
                From: {scenario_data['email_sender']}
            </p>
            
            <!-- Email Body Content -->
            <div style="text-align: left; line-height: 1.4; margin-bottom: 25px;">
                <p>
                    {scenario_data['email_subject']}
                </p>
                <p>
                    Click here: <a id="phishing-target" class="phishing-link" href="#" onclick="event.preventDefault();">{{scenario_data['email_link_text']}}</a>
                </p>
            </div>

            <hr style="margin: 20px 0;">
            
            <!-- Phishing Action Buttons -->
            <button class="action-button btn-safe" id="report-btn" onclick="checkPhishingAction(true)">Report as Phishing</button>
            <button class="action-button btn-danger" id="click-btn" onclick="checkPhishingAction(false)">Click Link (Simulated)</button>
            <button class="action-button btn-neutral next-scenario-btn" style="display:none;">Next Scenario</button>

            <p id="result-message" style="text-align: center; margin-top: 20px; font-weight: bold;"></p>
        </div>

        <script>
            function checkPhishingAction(reportedPhishing) {{
                const resultMessage = document.getElementById('result-message');
                const reportBtn = document.getElementById('report-btn');
                const clickBtn = document.getElementById('click-btn');
                const phishingLink = document.getElementById('phishing-target');

                // Disable interaction elements
                reportBtn.disabled = true;
                clickBtn.disabled = true;
                phishingLink.onclick = null; // Remove link functionality

                reportBtn.style.display = 'none';
                clickBtn.style.display = 'none';
                
                let pointsChange;
                let resultText;
                let resultColor;
                
                // Actual state of the email content is Phishing (True)
                const isPhishing = scenarioData.is_phishing; 
                
                if (reportedPhishing) {{
                    // User reported it as phishing (Correct action for this scenario)
                    pointsChange = 10;
                    resultText = scenarioData.score_report_correct;
                    resultColor = 'green';
                }} else {{
                    // User clicked the link (Incorrect action for this scenario)
                    pointsChange = -5;
                    resultText = scenarioData.score_accept_wrong;
                    resultColor = 'red';
                }}

                resultMessage.textContent = resultText;
                resultMessage.style.color = resultColor;
                // Trigger score update, which will handle the reload
                updateScore(pointsChange);
            }}
        </script>
        """
    
    # NEW SCENARIO: Multi-Factor Authentication (MFA)
    elif scenario_data["type"] == "mfa":
        template_content = f"""
        <div class="scenario-card">
            
            <div class="global-score-display">
                Current Score: <span id="score-value">{current_score}</span> points 🏆
            </div>
            
            <h2 style="color: #28a745; margin-bottom: 10px;">{scenario_data['title']}</h2>
            <p style="font-size: 1.1em; margin-bottom: 25px;">{scenario_data['instructions']}</p>
            
            <!-- Placeholder to simulate setting up MFA -->
            <img src="https://placehold.co/150x150/007bff/ffffff?text=MFA%20Code" alt="MFA Code Placeholder" style="margin-bottom: 25px; border-radius: 8px;">

            <hr style="margin: 20px 0;">
            
            <button class="action-button btn-safe" id="mfa-btn" onclick="checkMFAAction()">
                {scenario_data['action_button_text']}
            </button>
            <button class="action-button btn-neutral next-scenario-btn" style="display:none;">Refresh Scenario</button>
            
            <p id="result-message" style="text-align: center; margin-top: 20px; font-weight: bold;"></p>
        </div>

        <script>
            function checkMFAAction() {{
                const resultMessage = document.getElementById('result-message');
                const mfaBtn = document.getElementById('mfa-btn');

                mfaBtn.disabled = true;
                mfaBtn.style.display = 'none';

                const pointsChange = 10; 
                resultMessage.textContent = scenarioData.result_success;
                resultMessage.style.color = 'green';
                
                updateScore(pointsChange);
            }}
        </script>
        """

    else:
        template_content = "<div class='scenario-card'><h2>Error: Scenario type not recognized.</h2></div>"


    # --- BASE HTML TEMPLATE (Includes Styles) ---
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
                margin: 0;
                /* Use padding instead of fixed margins on a wrapper div for fluid mobile experience */
                padding: 100px 10px 50px 10px; 
                display: flex;
                flex-direction: column; /* Stack content vertically */
                justify-content: flex-start; 
                align-items: center; /* Center the fluid card horizontally */
                min-height: 100vh;
            }}
            
            /* The scenario card is now the main element, NOT wrapped by an outer div. */
            .scenario-card {{ 
                padding: 30px; 
                width: 95%; /* Fluid width on mobile */
                max-width: 550px; /* Max width for desktop */
                margin: 0 auto; /* Ensures centering */
                background-color: #ffffff; 
                border-radius: 12px; 
                text-align: center; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
                box-sizing: border-box;
            }}
            
            /* GLOBAL SCORE DISPLAY */
            .global-score-display {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                color: #007bff;
                margin-bottom: 25px; 
                text-align: right;
            }}
            
            /* Phishing Email Specific Styles */
            .email-container h2 {{
                font-size: 1.5em;
                margin-top: 0;
            }}
            
            /* Custom class for the sender line */
            .email-sender-line {{
                font-size: 1.1em; 
                margin-bottom: 15px;
                text-align: left; /* Keep the sender text left-aligned */
            }}
            
            .phishing-link {{
                color: #dc3545; /* Red underline for link */
                cursor: pointer; 
                text-decoration: underline; 
                font-weight: bold;
            }}
            
            /* Password Requirement List Styles */
            .req-list {{ 
                text-align: left; 
                margin: 15px 0 25px 0; 
                padding-left: 20px; 
                font-size: 0.9em; 
            }}
            .req-list li {{ 
                list-style-type: none; 
                margin-bottom: 5px; 
                color: #444; 
            }}

            /* Password Input and Indicator */
            .input-group {{
                position: relative;
                margin-bottom: 15px; 
            }}
            #password-input {{
                box-sizing: border-box; 
                padding: 12px; 
                width: 100%; 
                padding-right: 60px; 
                margin-bottom: 0;
                border: 1px solid #ccc; 
                border-radius: 6px; 
                font-size: 1.1em;
            }}
            #toggle-password {{
                position: absolute;
                top: 50%;
                right: 15px;
                transform: translateY(-50%);
                cursor: pointer;
                font-size: 0.8em; 
                font-weight: 600;
                color: #007bff; 
                line-height: 1;
                text-transform: uppercase;
                user-select: none;
                transition: color 0.1s;
            }}
            #toggle-password:hover {{ color: #0056b3; }}

            /* Strength Bar and Text (Used only for Password Scenario) */
            #strength-bar {{
                height: 10px; 
                width: 0; 
                background-color: #ddd; 
                border-radius: 5px;
                transition: width 0.3s ease-in-out, background-color 0.3s ease-in-out;
                margin-bottom: 15px;
            }}
            #strength-text {{ 
                font-weight: bold; 
                margin-bottom: 20px; 
                min-height: 1.2em; 
                color: #666; 
            }}

            /* --- BUTTON STYLING --- */
            .action-button {{
                padding: 10px 20px; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
                font-weight: bold; 
                margin: 0 5px; 
                transition: background-color 0.2s, transform 0.1s;
                text-transform: uppercase; 
                letter-spacing: 0.5px;
            }}
            .action-button:active {{ 
                transform: translateY(1px); 
            }}
            .action-button:disabled {{ 
                opacity: 0.6; 
                cursor: not-allowed; 
            }}

            .btn-primary {{ 
                background-color: #007bff; 
                color: white; 
            }}
            .btn-primary:hover {{ 
                background-color: #0056b3; 
            }}
            
            /* Custom colors for Phishing scenario buttons */
            .btn-safe {{ 
                background-color: #28a745; 
                color: white; 
            }}
            .btn-safe:hover {{ 
                background-color: #1e7e34; 
            }}
            .btn-danger {{ 
                background-color: #dc3545; 
                color: white; 
            }}
            .btn-danger:hover {{ 
                background-color: #c82333; 
            }}
            
            .btn-neutral {{ 
                background-color: #6c757d; 
                color: white; 
            }}
            .btn-neutral:hover {{ 
                background-color: #5a6268; 
            }}
        </style>
    </head>
    <body>

    <!-- DYNAMIC SCENARIO CONTENT INJECTED HERE (No outer wrapper div) -->
    {template_content}

    <script>
        // --- EMBEDDED JAVASCRIPT LOGIC (COMMON FUNCTIONS) ---
        let currentScore = {current_score}; 
        const scenarioData = {scenario_json};
        const scoreDisplay = document.getElementById('score-value');

        // Function to handle moving to the next scenario after an action is taken
        function handleNextScenario() {{
            window.location.reload(); 
        }}
        
        // This function is called by the check*Action functions
        function updateScore(points) {{
            currentScore += points;
            scoreDisplay.textContent = currentScore;
            
            // Show the "Next Scenario" button if an action was just taken
            document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                btn.style.display = 'inline-block';
                // Attach the reload logic to the button's click event
                btn.onclick = handleNextScenario; 
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
                    // The server updated the index, now the user can click Next Scenario
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