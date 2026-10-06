import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from config import Config
from routes.auth import login_required, get_current_user
from services.ai_service import AIService

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

ENV_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '.env')

def update_env_variable(key: str, value: str):
    """
    Updates or appends a key-value pair in .env file.
    """
    lines = []
    found = False
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(ENV_FILE_PATH, 'w') as f:
        f.writelines(new_lines)

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def settings_view():
    user = get_current_user()
    ai_service = AIService()

    if request.method == 'POST':
        provider = request.form.get('default_ai_provider', 'auto').strip()
        gemini_key = request.form.get('gemini_api_key', '').strip()
        openai_key = request.form.get('openai_api_key', '').strip()
        gemini_model = request.form.get('gemini_model', 'gemini-1.5-flash').strip()
        openai_model = request.form.get('openai_model', 'gpt-4o-mini').strip()

        # Update environment variables
        update_env_variable('DEFAULT_AI_PROVIDER', provider)
        update_env_variable('GEMINI_MODEL', gemini_model)
        update_env_variable('OPENAI_MODEL', openai_model)

        # Only overwrite keys if provided (or if user cleared them)
        if gemini_key or request.form.get('clear_gemini_key') == '1':
            update_env_variable('GEMINI_API_KEY', gemini_key)

        if openai_key or request.form.get('clear_openai_key') == '1':
            update_env_variable('OPENAI_API_KEY', openai_key)

        # Reload config in-memory
        Config.reload_env()
        flash('AI Engine settings updated successfully!', 'success')
        return redirect(url_for('settings.settings_view'))

    status_info = ai_service.get_status_info()

    # Mask keys for security
    raw_gemini = Config.GEMINI_API_KEY or ''
    masked_gemini = (raw_gemini[:6] + '...' + raw_gemini[-4:]) if len(raw_gemini) > 10 else (raw_gemini if raw_gemini else '')

    raw_openai = Config.OPENAI_API_KEY or ''
    masked_openai = (raw_openai[:6] + '...' + raw_openai[-4:]) if len(raw_openai) > 10 else (raw_openai if raw_openai else '')

    return render_template(
        'settings.html',
        user=user,
        status_info=status_info,
        default_provider=Config.DEFAULT_AI_PROVIDER or 'auto',
        gemini_model=Config.GEMINI_MODEL or 'gemini-1.5-flash',
        openai_model=Config.OPENAI_MODEL or 'gpt-4o-mini',
        has_gemini_key=bool(raw_gemini),
        masked_gemini=masked_gemini,
        has_openai_key=bool(raw_openai),
        masked_openai=masked_openai
    )

@settings_bp.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    data = request.get_json() or {}
    provider = data.get('provider', '').strip()
    api_key = data.get('api_key', '').strip()
    model_name = data.get('model_name', '').strip()

    # If key wasn't typed in the test input, fallback to saved key
    if not api_key:
        if provider == 'gemini':
            api_key = Config.GEMINI_API_KEY
        elif provider == 'openai':
            api_key = Config.OPENAI_API_KEY

    result = AIService.test_connection(provider=provider, api_key=api_key, model_name=model_name)
    return jsonify(result)
