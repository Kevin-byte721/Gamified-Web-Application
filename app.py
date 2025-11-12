from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import random 

app = Flask(__name__)
CORS(app) 

# --- GLOBAL CONSTANTS FOR FLOW CONTROL ---
FINAL_SCORE_INDEX = 999

# --- SCENARIO DATA DEFINITIONS ---

# 1. Phishing Email Scenario (ID 101)
SCENARIO_PHISHING = {
    "id": 101,
    "type": "phishing",
    "title": "🚨 Action Required: Urgent Payroll Update",
    "instructions": "Review this email. Decide whether to 'Report as Phishing' or 'Click Link (Simulated)'.",
    "is_phishing": True, # Actual state of the email content
    "email_sender": "IT Support <support@paninsinge-ps.com>", 
    "email_subject": "Dear Teacher, Please click the link below to verify your login credentials immediately to avoid payroll disruption.",
    "email_link_text": "[VERIFY PAYROLL]",
    # Scoring for Phishing (Correctly reporting a phishing email gives +10, falling for it gives -5)
    "score_report_correct": "✅ Correct! Phishing reported. +10 Points! You avoided a major threat.",
    "score_accept_wrong": "❌ Incorrect! Malicious link clicked. -5 Points! Check the sender address closely next time.",
    "score_report_wrong": "⚠️ Caution. This email was actually legitimate, but good job checking the sender. +1 Point.",
    "score_accept_correct": "✅ Correct. This was a legitimate request. +5 Points!",
}

# 2. Password Strength Scenario (ID 106)
SCENARIO_PASSWORD = {
    "id": 106,
    "type": "password",
    "title": "🔐 Mandatory Password Update",
    "instructions": "Create a new password that meets all modern security requirements.",
    "result_strong": "✅ Success! Strong password created. +15 Points!",
    "result_weak": "❌ Failure. Password too weak. -5 Points! Must contain upper, lower, number, and special characters.",
}

# 3. Multi-Factor Authentication Scenario (ID 108)
SCENARIO_MFA = {
    "id": 108,
    "type": "mfa",
    "title": "🛡️ Choose the Strongest MFA Method",
    "instructions": "Which Multi-Factor Authentication method provides the highest level of security against phishing and credential theft?",
    "options": [
        {"text": "SMS Text Message Code (Least Secure)", "is_correct": False, "points": -5, "message": "❌ Incorrect. SMS codes can be intercepted (SIM-swap attacks). Avoid using text messages for MFA."},
        {"text": "Authenticator App Code (e.g., Google Authenticator, Authy)", "is_correct": True, "points": 10, "message": "✅ Correct! App-generated codes (TOTP) are localized to your device and are much harder to steal than SMS."},
        {"text": "Email Verification Link (Weak)", "is_correct": False, "points": -10, "message": "❌ Incorrect. This relies solely on email security, which is often the first thing attackers target. This isn't true multi-factor authentication."},
    ]
}


# List of all assessment scenarios in order
ALL_SCENARIOS = [
    SCENARIO_PHISHING, # Index 0
    SCENARIO_PASSWORD, # Index 1
    SCENARIO_MFA       # Index 2 (NEW FINAL SCENARIO)
]
TOTAL_SCENARIOS = len(ALL_SCENARIOS)

# --- SIMULATED DATABASE/SCORE STORAGE ---
user_data = {
    "teacher_user_id_1": {
        "score": 0,
        "current_scenario_index": -1 # -1 means Module/Start Page
    }
}
# ----------------------------------------


# 1. API route to update score
@app.route('/api/updatescore', methods=['POST'])
def update_score():
    """Receives points data from the frontend and updates the user's score, advancing the scenario index."""
    try:
        data = request.get_json()
        user_id = "teacher_user_id_1" # Hardcoded user for this single-user demo
        points = data.get('points')
        
        if not isinstance(points, int):
            return jsonify({"success": False, "message": "Invalid points value"}), 400

        # Update the score
        user_data[user_id]['score'] += points
        new_score = user_data[user_id]['score']
        
        # Update the scenario index for the next step
        current_index = user_data[user_id]['current_scenario_index']
        
        if current_index == (TOTAL_SCENARIOS - 1):
            # This was the last assessment scenario. Set to final score state.
            new_index = FINAL_SCORE_INDEX
        else:
            # Move to the next scenario
            new_index = current_index + 1
            
        user_data[user_id]['current_scenario_index'] = new_index

        return jsonify({
            "success": True, 
            "new_score": new_score,
            "new_index": new_index
        })
    except Exception as e:
        print(f"Error updating score: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# 2. API route to advance from Module to first assessment
@app.route('/api/advancescenario', methods=['POST'])
def advance_scenario():
    """Advances the scenario index, typically from Module (-1) to first scenario (0)."""
    user_id = "teacher_user_id_1"
    
    if user_data[user_id]['current_scenario_index'] == -1:
        user_data[user_id]['current_scenario_index'] = 0
        return jsonify({"success": True, "new_index": 0})
    
    return jsonify({"success": False, "message": "Not in a state to advance"}), 400


# --- TEMPLATE DEFINITIONS ---

# FIXED: Escaped curly braces in CSS (lines 191, 192)
MODULE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Module</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #f7f7f7; }}
        .module-container {{ max-width: 800px; }}
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="module-container bg-white shadow-2xl rounded-xl p-8 md:p-12 w-full">
        <div class="flex justify-between items-center mb-6 border-b pb-4">
            <h1 class="text-3xl font-bold text-indigo-700">Cybersecurity Training Module: Introduction</h1>
            <div class="text-xl font-semibold text-gray-700">
                Score: <span id="score-display">{current_score}</span>
            </div>
        </div>
        
        <div class="text-gray-600 space-y-4 text-justify">
            <h2 class="text-2xl font-semibold text-gray-800 mt-6">What is Phishing?</h2>
            <p>
Phishing is a prevalent type of cyber-attack that targets individuals through various communication channels, including email, text messages, and phone calls. Fundamentally, these threats rely on social engineering, exploiting human psychology and deception rather than technical vulnerabilities. In a phishing attack, a threat actor masquerades as a reputable or trusted entity, such as a company, to trick the recipient into performing a desired action. This action is usually designed to steal sensitive information, like financial data, system login credentials, or other private details. Phishing messages often inject a sense of urgency, for example, by threatening account suspension or loss of money, to compel users to act quickly without scrutinizing the demand or the source's legitimacy (Proofpoint, n.d.).

Phishing attacks have evolved since the mid-1990s and are now categorized into different types based on their method and channel, including spear phishing (highly targeted), smishing (via text message), vishing (via voice call), and whaling (targeting high-profile executives). The core goal, however, remains to steal personal information or credentials. These attacks are a critical security challenge because they often serve as the initial entry point for a larger data breach, with research indicating that a large percentage of targeted attacks begin with a phishing email. Because of this focus on manipulating human behavior, training and advanced technical defenses are crucial for mitigating the risk associated with these constantly evolving threats (Proofpoint, n.d.).            </p>
            
            <h2 class="text-2xl font-semibold text-gray-800 mt-6">What is Password Security & Protection?</h2>
            <p>
Password security and protection are the essential practices, policies, and technologies designed to verify a user’s identity and safeguard digital accounts, devices, and sensitive data against unauthorized access (Cisco, n.d.). This framework is often referred to as the first line of defense in cybersecurity. A core component of this defense is creating strong, resilient passwords. A strong password must meet minimum criteria, typically being long (at least 12 characters is recommended) and complex, incorporating a mix of uppercase and lowercase letters, numbers, and symbols. Crucially, a secure password must also be unique to each account, as reusing credentials enables a hacker who compromises one account to access all others belonging to the user (Cisco, n.d.).

Effective password protection extends beyond the password itself to include additional security controls. The most vital supplemental measure is enabling Multi-Factor Authentication (MFA), which requires a user to provide two or more verification factors—such as a password and a one-time code sent to a mobile device—to log in, effectively blocking unauthorized access even if the password is stolen. Other best practices involve using a password manager to securely generate, encrypt, and store complex, unique credentials for all accounts, which mitigates the risk of human error or forgetfulness. By implementing these layered security measures, individuals and organizations can significantly reduce their vulnerability, as compromised credentials remain the leading cause of successful cyberattacks (Cisco, n.d.).
            </p>
            <h2 class="text-2xl font-semibold text-gray-800 mt-6">What is Multifactor-Authentication?</h2>
            <p>
            Multi-Factor Authentication (MFA) is a security method that verifies a user's identity by requiring at least two distinct forms of proof before granting access to an account, asset, or system (IBM, n.d.). This process provides extra security layers beyond what a single password can offer. The required forms of evidence are called "authentication factors," and a true MFA system mandates factors from two or more different categories. These categories include knowledge factors (something the user knows, like a password or PIN), possession factors (something the user has, like a smartphone receiving a one-time passcode or a physical security key), and inherent factors (something the user is, like a fingerprint or face scan) (IBM, n.d.). The user is only granted access if every required factor checks out.

MFA is critically important because standard single-factor authentication methods, which rely only on usernames and passwords, are easily compromised through attacks like phishing or brute-force hacking. With compromised credentials being a leading cause of data breaches, MFA provides a necessary defense: even if an attacker steals a user's password (a knowledge factor), they still lack the second, distinct factor—such as the user's mobile phone or biometric data—to gain unauthorized access (IBM, n.d.). The most common form of MFA is Two-Factor Authentication (2FA), which requires exactly two factors; however, some sensitive systems may require three or more factors to implement an even stronger defense, sometimes referred to as Adaptive MFA, which dynamically adjusts the required factors based on the risk level of the login attempt. 
            </p>
        </div>
        
        <div class="mt-8 pt-6 border-t flex justify-end">
            <button id="start-assessment-btn" class="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300">
                Start Assessment Scenarios ({TOTAL_SCENARIOS} Total)
            </button>
        </div>
    </div>

    <script>
        document.getElementById('start-assessment-btn').addEventListener('click', function() {{
            const button = this;
            button.disabled = true;
            button.textContent = 'Starting...';

            // API Call to advance index from -1 (Module) to 0 (First Scenario)
            fetch('/api/advancescenario', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{}}) // Empty body is fine
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    // Reload the page, which will now load the first scenario (index 0)
                    window.location.reload();
                }} else {{
                    console.error('Could not start assessment:', data.message);
                    button.disabled = false;
                    button.textContent = 'Start Assessment Scenarios';
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error:', error);
                button.disabled = false;
                button.textContent = 'Start Assessment Scenarios';
            }});
        }});
    </script>
</body>
</html>
"""

SCORE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Final Score</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #f0f4f8; }}
        .score-card {{ 
            max-width: 450px; /* Reduced max width from 600px */
            background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        }}
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="score-card text-white shadow-2xl rounded-xl p-8 md:p-10 w-full text-center"> <h1 class="text-4xl font-extrabold mb-3">Assessment Complete!</h1> <p class="text-lg mb-6">You have successfully finished all {total_scenarios} cybersecurity scenarios.</p> <div class="my-8 p-6 bg-white/20 rounded-lg backdrop-blur-sm"> <p class="text-xl font-semibold mb-2">Your Final Score:</p> <p class="text-6xl font-black" id="final-score">{final_score}</p> <p class="text-base mt-2">Points Earned</p> </div>
        
        <p class="text-base mb-6"> This score reflects your performance in identifying threats, creating secure credentials, and understanding modern authentication.
            You can restart the assessment to try again.
        </p>
        
        <button onclick="window.location.href='/'" class="bg-white text-purple-700 hover:bg-gray-100 font-bold py-3 px-8 rounded-lg shadow-xl transition duration-300 transform hover:scale-105">
            Restart Assessment
        </button>
    </div>
</body>
</html>
"""

# --- SCENARIO TEMPLATE GENERATION FUNCTIONS ---

def get_phishing_template(scenarioData):
    """Generates the HTML for the Phishing scenario."""
    
    # Check if the email is actually phishing to determine the correct score messages
    is_phishing = 'true' if scenarioData.get('is_phishing', False) else 'false'
    
    # Determine points for correct/incorrect action
    if scenarioData.get('is_phishing', False):
        # The correct action is 'report'
        report_points = 10
        accept_points = -5
        report_msg = scenarioData['score_report_correct']
        accept_msg = scenarioData['score_accept_wrong']
    else:
        # The correct action is 'accept/click'
        report_points = 1
        accept_points = 5
        report_msg = scenarioData['score_report_wrong']
        accept_msg = scenarioData['score_accept_correct']


    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phishing Scenario</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #e2e8f0; }}
        .email-container {{ max-width: 700px; }}
        .action-button {{ padding: 0.75rem 1.5rem; font-weight: 600; border-radius: 0.5rem; transition: background-color 0.3s, transform 0.1s; }}
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen p-4">
    <div class="w-full email-container bg-white shadow-2xl rounded-xl p-6 md:p-8">
        <div class="flex justify-between items-center border-b pb-4 mb-4">
            <h1 class="text-2xl font-bold text-gray-800">{scenarioData['title']}</h1>
            <div class="text-lg font-semibold text-gray-700">
                Score: <span id="score-display"></span>
            </div>
        </div>
        
        <p class="text-sm font-medium text-gray-500 mb-4 border-b pb-4">{scenarioData['instructions']}</p>

        <div class="bg-gray-50 p-6 rounded-lg border border-gray-200 shadow-inner space-y-3">
            <p class="text-sm text-gray-600">
                <span class="font-bold">From:</span> {scenarioData['email_sender']}
            </p>
            <p class="text-sm text-gray-600">
                <span class="font-bold">Subject:</span> {scenarioData['email_subject']}
            </p>
            <hr class="my-2 border-gray-200">
            <p class="text-base text-gray-800">
                This is an urgent security notification. We have detected a potential compromise 
                of your personnel account. Failure to act immediately may result in suspension 
                of your payroll access.
            </p>
            <div class="text-center py-4">
                <a href="#" id="email-link" class="text-blue-600 hover:text-blue-800 font-bold text-lg underline">
                    {scenarioData['email_link_text']}
                </a>
            </div>
            <p class="text-xs text-gray-500 italic mt-2">
                This message will self-destruct if not clicked within 2 hours.
            </p>
        </div>
        <div id="result-message" class="mt-6 p-4 text-center rounded-lg font-bold text-base" style="display: none;"></div>

        <div id="action-buttons" class="mt-6 flex justify-center space-x-4">
            <button id="report-btn" class="action-button bg-red-600 hover:bg-red-700 text-white">
                Report as Phishing
            </button>
            <button id="click-btn" class="action-button bg-green-600 hover:bg-green-700 text-white">
                Click Link (Simulated)
            </button>
        </div>

        <div class="mt-6 pt-4 border-t flex justify-end">
            <button class="next-scenario-btn action-button bg-indigo-600 hover:bg-indigo-700 text-white" style="display: none;">
                Next Scenario
            </button>
        </div>

    </div>

    <script>
        // --- Common JavaScript Code ---
        let currentScore = parseInt(document.getElementById('score-display').textContent) || 0;
        const scoreDisplay = document.getElementById('score-display');
        const resultMessage = document.getElementById('result-message');
        const actionButtons = document.getElementById('action-buttons');
        const phishingScenarioID = {scenarioData['id']};
        const TOTAL_SCENARIOS = {TOTAL_SCENARIOS};

        function handleNextScenario() {{
            window.location.reload(); 
        }}

        // Attach the handleNextScenario to the Next Scenario button
        document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
            btn.onclick = handleNextScenario; 
        }});

        function updateScore(points) {{
            // API CALL TO PYTHON BACKEND to persist the score and advance the index
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
                    
                    // Show the next scenario button after scoring
                    document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                        btn.textContent = data.new_index === {FINAL_SCORE_INDEX} ? 'View Final Score' : 'Next Scenario';
                        btn.style.display = 'block';
                    }});
                }} else {{
                    console.error('Score update failed on server:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error:', error);
            }});
        }}
        // --- End of Common JavaScript Code ---

        // --- Phishing Scenario Specific JavaScript ---
        const isPhishing = {is_phishing};

        document.getElementById('report-btn').addEventListener('click', () => {{
            handleAction('report');
        }});

        document.getElementById('click-btn').addEventListener('click', () => {{
            handleAction('click');
        }});
        
        document.getElementById('email-link').addEventListener('click', (e) => {{
            e.preventDefault(); 
            handleAction('click');
        }});


        function handleAction(action) {{
            // Disable buttons after action
            document.getElementById('report-btn').disabled = true;
            document.getElementById('click-btn').disabled = true;
            actionButtons.style.display = 'none';

            let message = "";
            let points = 0;

            if (action === 'report') {{
                points = {report_points};
                message = "{report_msg}";
                resultMessage.style.backgroundColor = points > 0 ? '#d1e7dd' : (points < 0 ? '#f8d7da' : '#fff3cd');
                resultMessage.style.color = points > 0 ? '#0f5132' : (points < 0 ? '#842029' : '#664d03');
            }} else if (action === 'click') {{
                points = {accept_points};
                message = "{accept_msg}";
                resultMessage.style.backgroundColor = points > 0 ? '#d1e7dd' : (points < 0 ? '#f8d7da' : '#fff3cd');
                resultMessage.style.color = points > 0 ? '#0f5132' : (points < 0 ? '#842029' : '#664d03');
            }}
            
            resultMessage.innerHTML = message;
            resultMessage.style.display = 'block';
            
            updateScore(points);
        }}
        // --- End of Phishing Scenario Specific JavaScript ---
    </script>
    </body>
    </html>
    """

def get_password_template(scenarioData):
    """Generates the HTML for the Password scenario."""
    
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Scenario</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #f0f4f8; }}
        .password-container {{ max-width: 500px; }}
        .requirement-met {{ color: #10b981; }} /* green-500 */
        .requirement-unmet {{ color: #f87171; }} /* red-400 */
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen p-4">
    <div class="w-full password-container bg-white shadow-2xl rounded-xl p-8">
        <div class="flex justify-between items-center border-b pb-4 mb-6">
            <h1 class="text-2xl font-bold text-gray-800">{scenarioData['title']}</h1>
            <div class="text-lg font-semibold text-gray-700">
                Score: <span id="score-display"></span>
            </div>
        </div>
        
        <p class="text-sm font-medium text-gray-500 mb-6">Enter a password and click 'Submit' to test its strength against our security standards.</p>

        <div class="space-y-4">
            <input type="password" id="password-input" 
                   class="w-full p-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-lg" 
                   placeholder="Enter new password" oninput="updateStrength()">
                   
            <div id="strength-bar" class="w-full h-3 rounded-full bg-gray-200">
                <div id="strength-indicator" class="h-full rounded-full transition-all duration-300" style="width: 0%; background-color: #f87171;"></div>
            </div>
            <p id="strength-text" class="text-sm font-medium text-gray-500 text-center">Strength: Very Weak</p>
        </div>

        <div id="requirements-list" class="mt-6 space-y-2">
            <div id="req-length" class="text-gray-600 flex items-center">
                <span class="mr-2">❌</span> Minimum 10 characters
            </div>
            <div id="req-upper" class="text-gray-600 flex items-center">
                <span class="mr-2">❌</span> At least one uppercase letter (A-Z)
            </div>
            <div id="req-lower" class="text-gray-600 flex items-center">
                <span class="mr-2">❌</span> At least one lowercase letter (a-z)
            </div>
            <div id="req-number" class="text-gray-600 flex items-center">
                <span class="mr-2">❌</span> At least one number (0-9)
            </div>
            <div id="req-special" class="text-gray-600 flex items-center">
                <span class="mr-2">❌</span> At least one special character (!@#$...)
            </div>
        </div>
        
        <div id="result-message" class="mt-6 p-4 text-center rounded-lg font-bold text-base" style="display: none;"></div>

        <div class="mt-8 pt-4 border-t flex justify-between items-center">
            <button id="submit-btn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300">
                Submit Password
            </button>
            <button class="next-scenario-btn bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300" style="display: none;">
                Next Scenario
            </button>
        </div>
    </div>

    <script>
        // --- Common JavaScript Code ---
        let currentScore = parseInt(document.getElementById('score-display').textContent) || 0;
        const scoreDisplay = document.getElementById('score-display');
        const passwordInput = document.getElementById('password-input');
        const strengthIndicator = document.getElementById('strength-indicator');
        const strengthText = document.getElementById('strength-text');
        const resultMessage = document.getElementById('result-message');
        const submitBtn = document.getElementById('submit-btn');
        const scenarioData = {json.dumps(scenarioData)};
        const TOTAL_SCENARIOS = {TOTAL_SCENARIOS};

        function handleNextScenario() {{
            window.location.reload(); 
        }}

        // Attach the handleNextScenario to the Next Scenario button
        document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
            btn.onclick = handleNextScenario; 
        }});

        function updateScore(points) {{
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
                    
                    // Show the next scenario button after scoring
                    document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                        btn.textContent = data.new_index === {FINAL_SCORE_INDEX} ? 'View Final Score' : 'Next Scenario';
                        btn.style.display = 'block';
                    }});
                }} else {{
                    console.error('Score update failed on server:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error:', error);
            }});
        }}
        // --- End of Common JavaScript Code ---

        // --- Password Scenario Specific JavaScript ---
        const reqs = {{
            length: document.getElementById('req-length'),
            upper: document.getElementById('req-upper'),
            lower: document.getElementById('req-lower'),
            number: document.getElementById('req-number'),
            special: document.getElementById('req-special')
        }};

        function checkRequirement(el, condition) {{
            if (condition) {{
                el.classList.remove('requirement-unmet');
                el.classList.add('requirement-met');
                el.innerHTML = '<span class="mr-2">✅</span>' + el.textContent.substring(el.textContent.indexOf(' '));
            }} else {{
                el.classList.remove('requirement-met');
                el.classList.add('requirement-unmet');
                el.innerHTML = '<span class="mr-2">❌</span>' + el.textContent.substring(el.textContent.indexOf(' '));
            }}
            return condition;
        }}

        function updateStrength() {{
            const password = passwordInput.value;
            let score = 0;

            const meetsLength = checkRequirement(reqs.length, password.length >= 10);
            const meetsUpper = checkRequirement(reqs.upper, /[A-Z]/.test(password));
            const meetsLower = checkRequirement(reqs.lower, /[a-z]/.test(password));
            const meetsNumber = checkRequirement(reqs.number, /[0-9]/.test(password));
            const meetsSpecial = checkRequirement(reqs.special, /[^A-Za-z0-9]/.test(password));

            const totalRequirements = 5;
            let metCount = [meetsLength, meetsUpper, meetsLower, meetsNumber, meetsSpecial].filter(b => b).length;
            
            let percentage = (metCount / totalRequirements) * 100;

            let color = '#f87171'; // Red (Very Weak/Weak)
            let text = 'Very Weak';
            
            if (metCount >= 2) {{
                color = '#fbbf24'; // Amber (Moderate)
                text = 'Moderate';
            }}
            if (metCount >= 4) {{
                color = '#3b82f6'; // Blue (Strong)
                text = 'Strong';
            }}
            if (metCount === totalRequirements) {{
                color = '#10b981'; // Green (Very Strong)
                text = 'Very Strong';
            }}

            strengthIndicator.style.width = percentage + '%';
            strengthIndicator.style.backgroundColor = color;
            strengthText.textContent = 'Strength: ' + text;
        }}

        submitBtn.addEventListener('click', () => {{
            submitBtn.disabled = true;
            passwordInput.disabled = true;
            
            const password = passwordInput.value;
            const isStrong = password.length >= 10 &&
                             /[A-Z]/.test(password) &&
                             /[a-z]/.test(password) &&
                             /[0-9]/.test(password) &&
                             /[^A-Za-z0-9]/.test(password);

            let message = "";
            let pointsChange = 0;

            if (isStrong) {{
                message = scenarioData.result_strong;
                pointsChange = 15;
                resultMessage.style.backgroundColor = '#d1e7dd'; // Light Green
                resultMessage.style.color = '#0f5132'; // Dark Green
            }} else {{
                message = scenarioData.result_weak;
                pointsChange = -5;
                resultMessage.style.backgroundColor = '#f8d7da'; // Light Red
                resultMessage.style.color = '#842029'; // Dark Red
            }}

            resultMessage.innerHTML = message;
            resultMessage.style.display = 'block';

            // Send final calculated points to the server
            updateScore(pointsChange);
        }});
        
        // Ensure strength updates on initial load/typing
        document.addEventListener('DOMContentLoaded', updateStrength);


        // --- End of Password Scenario Specific JavaScript ---
    </script>
    </body>
    </html>
    """

def get_mfa_template(scenarioData):
    """Generates the HTML for the Multi-Factor Authentication (MFA) scenario."""
    
    options_html = ""
    for i, option in enumerate(scenarioData['options']):
        # Encode the option data for use in the onclick handler
        option_json = json.dumps(option)
        
        options_html += f"""
        <button onclick='handleSelection({option_json}, this)'
                class="option-btn w-full text-left p-4 mb-3 border-2 border-indigo-300 bg-white hover:bg-indigo-50 rounded-lg transition duration-200 shadow-md focus:outline-none focus:ring-4 focus:ring-indigo-200 disabled:opacity-75 disabled:cursor-not-allowed">
            <span class="font-semibold text-lg text-gray-800">{option['text']}</span>
        </button>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MFA Scenario</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #e5e7eb; }}
        .mfa-container {{ max-width: 600px; }}
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen p-4">
    <div class="w-full mfa-container bg-white shadow-2xl rounded-xl p-8">
        <div class="flex justify-between items-center border-b pb-4 mb-6">
            <h1 class="text-2xl font-bold text-gray-800">{scenarioData['title']}</h1>
            <div class="text-lg font-semibold text-gray-700">
                Score: <span id="score-display"></span>
            </div>
        </div>
        
        <p class="text-base text-gray-600 mb-8 font-medium">{scenarioData['instructions']}</p>

        <div id="options-container" class="space-y-3">
            {options_html}
        </div>
        
        <div id="result-message" class="mt-8 p-4 text-center rounded-lg font-bold text-base" style="display: none;"></div>

        <div class="mt-8 pt-4 border-t flex justify-end">
            <button class="next-scenario-btn bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg transition duration-300" style="display: none;">
                Next Scenario
            </button>
        </div>
    </div>

    <script>
        // --- Common JavaScript Code ---
        let currentScore = parseInt(document.getElementById('score-display').textContent) || 0;
        const scoreDisplay = document.getElementById('score-display');
        const resultMessage = document.getElementById('result-message');
        const optionsContainer = document.getElementById('options-container');
        const scenarioData = {json.dumps(scenarioData)};
        const TOTAL_SCENARIOS = {TOTAL_SCENARIOS};

        function handleNextScenario() {{
            window.location.reload(); 
        }}

        // Attach the handleNextScenario to the Next Scenario button
        document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
            btn.onclick = handleNextScenario; 
        }});

        function updateScore(points, new_index) {{
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
                    
                    // Show the next scenario button after scoring
                    document.querySelectorAll('.next-scenario-btn').forEach(btn => {{
                        btn.textContent = data.new_index === {FINAL_SCORE_INDEX} ? 'View Final Score' : 'Next Scenario';
                        btn.style.display = 'block';
                    }});
                }} else {{
                    console.error('Score update failed on server:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('Network or Fetch Error:', error);
            }});
        }}
        // --- End of Common JavaScript Code ---

        // --- MFA Scenario Specific JavaScript ---
        function handleSelection(option, button) {{
            // Disable all buttons to prevent double-clicking
            document.querySelectorAll('.option-btn').forEach(btn => {{
                btn.disabled = true;
                btn.classList.remove('hover:bg-indigo-50');
                btn.classList.remove('focus:ring-4');
            }});

            const message = option.message;
            const points = option.points;
            const isCorrect = option.is_correct;

            // Apply color to the selected button
            if (isCorrect) {{
                button.classList.add('border-green-500', 'bg-green-100', 'shadow-xl');
                resultMessage.style.backgroundColor = '#d1e7dd'; // Light Green
                resultMessage.style.color = '#0f5132'; // Dark Green
            }} else {{
                button.classList.add('border-red-500', 'bg-red-100', 'shadow-xl');
                resultMessage.style.backgroundColor = '#f8d7da'; // Light Red
                resultMessage.style.color = '#842029'; // Dark Red
                
                // Highlight the correct answer
                document.querySelectorAll('.option-btn').forEach(btn => {{
                    const btnOption = JSON.parse(btn.getAttribute('onclick').match(/\((.*), this\)/)[1]);
                    if (btnOption.is_correct) {{
                        btn.classList.add('border-green-500', 'bg-green-100');
                    }}
                }});
            }}
            
            resultMessage.innerHTML = message;
            resultMessage.style.display = 'block';

            updateScore(points);
        }}
        // --- End of MFA Scenario Specific JavaScript ---
    </script>
    </body>
    </html>
    """
# --- 3. MAIN ROUTE LOGIC ---

@app.route('/')
def index():
    user_id = "teacher_user_id_1" # Hardcoded user for this single-user demo
    
    # Check if user data exists, initialize if not (for robustness)
    if user_id not in user_data:
        user_data[user_id] = {"score": 0, "current_scenario_index": -1}
        
    current_index = user_data[user_id]['current_scenario_index']
    current_score = user_data[user_id]['score']
    
    if current_index == -1:
        # Render Module Page
        return render_template_string(MODULE_TEMPLATE.format(current_score=current_score, TOTAL_SCENARIOS=TOTAL_SCENARIOS))
        
    elif current_index == FINAL_SCORE_INDEX:
        # Render Final Score Page
        final_score_value = current_score
        
        # Reset user data for next playthrough
        user_data[user_id]['score'] = 0
        user_data[user_id]['current_scenario_index'] = -1
        
        return render_template_string(SCORE_TEMPLATE.format(final_score=final_score_value, total_scenarios=TOTAL_SCENARIOS))
        
    elif 0 <= current_index < TOTAL_SCENARIOS:
        # Render a specific Assessment Scenario
        scenario_data = ALL_SCENARIOS[current_index]
        
        if scenario_data['type'] == 'phishing':
            template = get_phishing_template(scenario_data)
        elif scenario_data['type'] == 'password':
            template = get_password_template(scenario_data)
        elif scenario_data['type'] == 'mfa':
            template = get_mfa_template(scenario_data)
        else:
            return "Scenario type not found.", 404
        
        # Inject common data into the template
        template = template.replace(
            '<!-- CURRENT_SCORE_PLACEHOLDER -->', str(current_score)
        )
        return render_template_string(template)
        
    else:
        # Fallback to the start
        user_data[user_id]['current_scenario_index'] = -1
        return render_template_string(MODULE_TEMPLATE.format(current_score=current_score, TOTAL_SCENARIOS=TOTAL_SCENARIOS))

# --- 4. RUN THE APPLICATION ---
if __name__ == '__main__':
    app.run(debug=True)