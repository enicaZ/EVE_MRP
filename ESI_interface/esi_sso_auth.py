import base64
import random
import requests
import string
import urllib.parse
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import hashlib
import secrets

# Flask用于Web服务器（安装: pip install flask）
from flask import Flask, request, redirect, session, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # 用于会话安全

# Eve Online SSO配置 - 请从EVE开发者门户获取
client_id = "your_client_id_here"  # 从 https://developers.eveonline.com/ 获取
client_secret = "your_client_secret_here"  # 从 https://developers.eveonline.com/ 获取
redirect_uri = "http://localhost:5000/callback"  # 必须在开发者门户注册的回调URL

# 确保client_id和client_secret已正确设置
if client_id == "your_client_id_here" or client_secret == "your_client_secret_here":
    print("=" * 80)
    print("错误：请先配置您的client_id和client_secret！")
    print("1. 访问 https://developers.eveonline.com/")
    print("2. 登录您的EVE账户")
    print("3. 创建新应用或使用现有应用")
    print("4. 将获得的client_id和client_secret填入代码中")
    print("=" * 80)
    exit(1)


class EVESSO:
    """EVE Online SSO 客户端类 - 更新为最新ESI端点"""
    
    # ESI 端点
    AUTH_URL = "https://login.eveonline.com/v2/oauth/authorize"
    TOKEN_URL = "https://login.eveonline.com/v2/oauth/token"
    VERIFY_URL = "https://login.eveonline.com/oauth/verify"
    REVOKE_URL = "https://login.eveonline.com/v2/oauth/revoke"
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def generate_state(self, length: int = 32) -> str:
        """生成安全的state参数防止CSRF攻击"""
        return secrets.token_urlsafe(length)
    
    def get_authorization_url(self, scopes: list = None) -> Tuple[str, str]:
        """
        生成重定向到SSO的URL
        
        :param scopes: 请求的权限范围列表
        :return: (授权URL, state参数)
        """
        if scopes is None:
            scopes = ["publicData","esi-calendar.respond_calendar_events.v1","esi-calendar.read_calendar_events.v1","esi-location.read_location.v1","esi-mail.organize_mail.v1","esi-mail.read_mail.v1","esi-skills.read_skills.v1","esi-skills.read_skillqueue.v1","esi-wallet.read_corporation_wallet.v1","esi-search.search_structures.v1","esi-clones.read_clones.v1","esi-characters.read_contacts.v1","esi-killmails.read_killmails.v1","esi-corporations.read_corporation_membership.v1","esi-assets.read_assets.v1","esi-planets.manage_planets.v1","esi-fleets.write_fleet.v1","esi-ui.open_window.v1","esi-characters.write_contacts.v1","esi-fittings.read_fittings.v1","esi-fittings.write_fittings.v1","esi-markets.structure_markets.v1","esi-corporations.read_structures.v1","esi-characters.read_loyalty.v1","esi-characters.read_chat_channels.v1","esi-characters.read_medals.v1","esi-characters.read_standings.v1","esi-characters.read_agents_research.v1","esi-industry.read_character_jobs.v1","esi-markets.read_character_orders.v1","esi-characters.read_blueprints.v1","esi-characters.read_corporation_roles.v1","esi-location.read_online.v1","esi-contracts.read_character_contracts.v1","esi-clones.read_implants.v1","esi-characters.read_fatigue.v1","esi-killmails.read_corporation_killmails.v1","esi-corporations.track_members.v1","esi-wallet.read_corporation_wallets.v1","esi-characters.read_notifications.v1","esi-corporations.read_divisions.v1","esi-corporations.read_contacts.v1","esi-assets.read_corporation_assets.v1","esi-corporations.read_titles.v1","esi-corporations.read_blueprints.v1","esi-corporations.read_standings.v1","esi-industry.read_corporation_jobs.v1","esi-markets.read_corporation_orders.v1","esi-corporations.read_container_logs.v1","esi-industry.read_character_mining.v1","esi-industry.read_corporation_mining.v1","esi-planets.read_customs_offices.v1","esi-corporations.read_facilities.v1","esi-corporations.read_medals.v1","esi-characters.read_titles.v1","esi-alliances.read_contacts.v1","esi-corporations.read_fw_stats.v1","esi-corporations.read_projects.v1","esi-corporations.read_freelance_jobs.v1","esi-characters.read_freelance_jobs.v1","esi-location.read_ship_type.v1","esi-mail.send_mail.v1","esi-wallet.read_character_wallet.v1","esi-universe.read_structures.v1","esi-fleets.read_fleet.v1","esi-ui.write_waypoint.v1","esi-contracts.read_corporation_contracts.v1","esi-corporations.read_starbases.v1","esi-characters.read_fw_stats.v1"]
        
        state = self.generate_state()
        params = {
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "scope": " ".join(scopes),
            "state": state,
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.AUTH_URL}?{query_string}", state
    
    def get_token(self, authorization_code: str) -> Dict:
        """
        使用授权码获取访问令牌
        
        :param authorization_code: 从回调获取的授权码
        :return: 令牌响应字典
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        basic_auth = base64.urlsafe_b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "login.eveonline.com"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
        }
        
        # 添加重定向URI
        if self.redirect_uri:
            data["redirect_uri"] = self.redirect_uri
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            
            # 如果遇到404错误，尝试备用端点
            if response.status_code == 404:
                print("尝试备用令牌端点...")
                # 尝试不同的端点格式
                alt_token_url = "https://login.eveonline.com/oauth/token"
                response = requests.post(
                    alt_token_url,
                    headers=headers,
                    data=data,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"获取令牌时出错: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"响应状态码: {e.response.status_code}")
                print(f"响应内容: {e.response.text}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """使用刷新令牌获取新的访问令牌"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        basic_auth = base64.urlsafe_b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        response = requests.post(
            self.TOKEN_URL,
            headers=headers,
            data=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def verify_token(self, access_token: str) -> Dict:
        """验证访问令牌并获取角色信息"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": f"EVE-SSO-Python-Client/{client_id}"
        }
        
        response = requests.get(
            self.VERIFY_URL,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def revoke_token(self, token: str, token_type_hint: str = "access_token") -> bool:
        """撤销令牌"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        basic_auth = base64.urlsafe_b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data = {
            "token": token,
            "token_type_hint": token_type_hint,
        }
        
        response = requests.post(
            self.REVOKE_URL,
            headers=headers,
            data=data,
            timeout=30
        )
        return response.status_code == 200


# 初始化EVE SSO客户端
eve_sso = EVESSO(client_id, client_secret, redirect_uri)


# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>EVE Online SSO Example</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #0a0a1a; color: #c8c8ff; }
        .container { max-width: 800px; margin: 0 auto; background: #1a1a2e; padding: 30px; border-radius: 10px; border: 1px solid #2a2a4a; }
        .btn { background: linear-gradient(45deg, #4a00e0, #8e2de2); color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; font-size: 16px; display: inline-block; margin: 10px 5px; }
        .btn:hover { background: linear-gradient(45deg, #8e2de2, #4a00e0); }
        .info { background: #16213e; padding: 20px; border-radius: 8px; border-left: 4px solid #4a00e0; margin: 20px 0; }
        .error { background: #2d0000; padding: 20px; border-radius: 8px; border-left: 4px solid #ff3333; margin: 20px 0; }
        .success { background: #002d00; padding: 20px; border-radius: 8px; border-left: 4px solid #33ff33; margin: 20px 0; }
        h1 { color: #8e2de2; border-bottom: 2px solid #4a00e0; padding-bottom: 10px; }
        h3 { color: #c8c8ff; }
        .token-info { background: #0f3460; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 12px; overflow-x: auto; }
        .character-card { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 20px; border-radius: 10px; border: 1px solid #4a00e0; margin: 20px 0; }
        .character-name { font-size: 24px; color: #8e2de2; margin-bottom: 10px; }
        .scope-badge { background: #4a00e0; color: white; padding: 4px 8px; border-radius: 4px; margin: 2px; font-size: 12px; display: inline-block; }
        .debug { background: #1a1a1a; color: #00ff00; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 11px; margin: 10px 0; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 EVE Online SSO Demo</h1>
        
        {% if error %}
        <div class="error">
            <strong>❌ Error:</strong> {{ error }}
            {% if debug_info %}
            <div class="debug">
                <strong>Debug Info:</strong><br>
                {{ debug_info }}
            </div>
            {% endif %}
        </div>
        {% endif %}
        
        {% if success %}
        <div class="success">
            <strong>✅ Success:</strong> {{ success }}
        </div>
        {% endif %}
        
        {% if character_info %}
        <div class="character-card">
            <div class="character-name">👤 {{ character_info.CharacterName }}</div>
            <p><strong>Character ID:</strong> {{ character_info.CharacterID }}</p>
            <p><strong>Token Type:</strong> {{ character_info.TokenType }}</p>
            <p><strong>Expires:</strong> {{ character_info.ExpiresOn }}</p>
            <p><strong>Scopes:</strong><br>
                {% for scope in character_info.Scopes %}
                <span class="scope-badge">{{ scope }}</span>
                {% endfor %}
            </p>
        </div>
        
        <div class="info">
            <h3>📊 Token Information</h3>
            <div class="token-info">
                Access Token: {{ token_info.access_token[:50] }}...<br>
                Expires: {{ token_info.expires_at.strftime('%Y-%m-%d %H:%M:%S') if token_info.expires_at else 'Unknown' }}<br>
                Token Type: {{ token_info.token_type }}
            </div>
            
            <div style="margin-top: 20px;">
                <a href="/verify" class="btn">🔄 Verify Token</a>
                <a href="/test_esi" class="btn">🌐 Test ESI API</a>
                <a href="/logout" class="btn">🚪 Logout</a>
            </div>
        </div>
        
        {% elif not logged_in %}
        <div class="info">
            <h3>🔑 Authentication Required</h3>
            <p>To access EVE Online data, you need to authenticate with your EVE Online account.</p>
            
            <div style="margin: 20px 0;">
                <strong>Select Scopes:</strong><br>
                <label><input type="checkbox" name="scopes" value="publicData" checked> publicData (Basic character info)</label><br>
                <label><input type="checkbox" name="scopes" value="esi-wallet.read_character_wallet.v1"> Wallet Access</label><br>
                <label><input type="checkbox" name="scopes" value="esi-skills.read_skills.v1"> Skills</label><br>
                <label><input type="checkbox" name="scopes" value="esi-assets.read_assets.v1"> Assets</label>
            </div>
            
            <a href="/login" class="btn" id="loginBtn">🚀 Login with EVE Online</a>
            
            <div style="margin-top: 30px; font-size: 12px; color: #888;">
                <strong>Note:</strong> Make sure you have registered your application at 
                <a href="https://developers.eveonline.com" style="color: #8e2de2;">developers.eveonline.com</a>
                with the callback URL: <code>{{ redirect_uri }}</code>
            </div>
        </div>
        {% endif %}
        
        {% if api_test_result %}
        <div class="info">
            <h3>🌐 ESI API Test Result</h3>
            <div class="token-info">{{ api_test_result|tojson(indent=2) }}</div>
        </div>
        {% endif %}
    </div>
    
    <script>
        document.getElementById('loginBtn')?.addEventListener('click', function(e) {
            const selectedScopes = Array.from(document.querySelectorAll('input[name="scopes"]:checked'))
                .map(cb => cb.value);
            
            if (selectedScopes.length > 0) {
                this.href = '/login?scopes=' + selectedScopes.join(',');
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """主页"""
    token_info = session.get('token_info')
    character_info = session.get('character_info')
    
    return render_template_string(
        HTML_TEMPLATE,
        logged_in=token_info is not None,
        token_info=token_info if token_info else {},
        character_info=character_info,
        redirect_uri=redirect_uri,
        error=session.pop('error', None),
        success=session.pop('success', None),
        api_test_result=session.pop('api_test_result', None)
    )


@app.route('/login')
def login():
    """发起SSO登录"""
    try:
        # 获取请求的权限范围
        scopes_param = request.args.get('scopes', 'publicData')
        scopes_list = scopes_param.split(',') if scopes_param else ['publicData']
        
        print(f"请求的权限范围: {scopes_list}")
        
        # 生成授权URL
        auth_url, state = eve_sso.get_authorization_url(scopes_list)
        
        # 保存state到session
        session['oauth_state'] = state
        session['requested_scopes'] = scopes_list
        
        print(f"重定向到: {auth_url}")
        
        return redirect(auth_url)
        
    except Exception as e:
        session['error'] = f"Login initialization failed: {str(e)}"
        return redirect('/')


@app.route('/callback')
def callback():
    """处理SSO回调"""
    print(f"回调参数: {dict(request.args)}")
    
    # 检查错误
    if 'error' in request.args:
        error = request.args.get('error')
        error_description = request.args.get('error_description', '')
        session['error'] = f"{error}: {error_description}"
        return redirect('/')
    
    # 验证state参数防止CSRF攻击
    state = request.args.get('state')
    stored_state = session.get('oauth_state')
    
    if not state or state != stored_state:
        session['error'] = "Invalid state parameter. Possible CSRF attack."
        return redirect('/')
    
    # 获取授权码
    authorization_code = request.args.get('code')
    if not authorization_code:
        session['error'] = "No authorization code received"
        return redirect('/')
    
    try:
        print("获取访问令牌...")
        
        # 获取访问令牌
        token_response = eve_sso.get_token(authorization_code)
        print(f"令牌响应: {token_response.keys()}")
        
        # 验证令牌并获取角色信息
        verify_response = eve_sso.verify_token(token_response['access_token'])
        print(f"验证响应: {verify_response}")
        
        # 保存到session
        session['token_info'] = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response.get('refresh_token'),
            'expires_in': token_response['expires_in'],
            'expires_at': datetime.now() + timedelta(seconds=token_response['expires_in']),
            'token_type': token_response['token_type']
        }
        
        session['character_info'] = {
            'CharacterID': verify_response['CharacterID'],
            'CharacterName': verify_response['CharacterName'],
            'ExpiresOn': verify_response['ExpiresOn'],
            'Scopes': verify_response.get('Scopes', '').split(' '),
            'TokenType': verify_response['TokenType'],
            'CharacterOwnerHash': verify_response['CharacterOwnerHash']
        }
        
        # 清理临时数据
        session.pop('oauth_state', None)
        
        session['success'] = "Authentication successful!"
        
        print("认证成功！")
        
        return redirect('/')
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error {e.response.status_code}: {e.response.text[:200]}"
        session['error'] = error_msg
        print(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        return redirect('/')
    except Exception as e:
        import traceback
        debug_info = traceback.format_exc()
        session['error'] = f"Authentication failed: {str(e)}"
        session['debug_info'] = debug_info
        print(f"认证失败: {str(e)}")
        print(f"Traceback: {debug_info}")
        return redirect('/')


@app.route('/verify')
def verify():
    """验证当前令牌"""
    token_info = session.get('token_info')
    if not token_info:
        session['error'] = "Not authenticated"
        return redirect('/')
    
    try:
        # 检查令牌是否过期
        expires_at = token_info.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        if datetime.now() > expires_at:
            # 尝试刷新令牌
            refresh_token = token_info.get('refresh_token')
            if refresh_token:
                print("令牌已过期，尝试刷新...")
                new_token = eve_sso.refresh_token(refresh_token)
                session['token_info'] = {
                    'access_token': new_token['access_token'],
                    'refresh_token': new_token.get('refresh_token'),
                    'expires_in': new_token['expires_in'],
                    'expires_at': datetime.now() + timedelta(seconds=new_token['expires_in']),
                    'token_type': new_token['token_type']
                }
                token_info = session['token_info']
                session['success'] = "Token refreshed successfully!"
            else:
                session['error'] = "Token expired and no refresh token available"
                return redirect('/logout')
        
        # 验证令牌
        verify_response = eve_sso.verify_token(token_info['access_token'])
        
        # 更新角色信息
        session['character_info'] = {
            'CharacterID': verify_response['CharacterID'],
            'CharacterName': verify_response['CharacterName'],
            'ExpiresOn': verify_response['ExpiresOn'],
            'Scopes': verify_response.get('Scopes', '').split(' '),
            'TokenType': verify_response['TokenType'],
            'CharacterOwnerHash': verify_response['CharacterOwnerHash']
        }
        
        session['success'] = f"Token valid! Character: {verify_response['CharacterName']}"
        
    except Exception as e:
        session['error'] = f"Token verification failed: {str(e)}"
    
    return redirect('/')


@app.route('/test_esi')
def test_esi():
    """测试ESI API"""
    token_info = session.get('token_info')
    if not token_info:
        session['error'] = "Not authenticated"
        return redirect('/')
    
    try:
        # 获取角色信息
        headers = {
            "Authorization": f"Bearer {token_info['access_token']}",
            "User-Agent": f"EVE-SSO-Python-Client/{client_id}"
        }
        
        # 测试不同的ESI端点
        character_id = session.get('character_info', {}).get('CharacterID')
        
        if character_id:
            # 获取角色公开信息
            response = requests.get(
                f"https://esi.evetech.net/latest/characters/{character_id}/",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                character_data = response.json()
                session['api_test_result'] = {
                    'character': character_data,
                    'endpoint': f'characters/{character_id}/',
                    'status': 'success'
                }
            else:
                session['api_test_result'] = {
                    'error': f"ESI API returned {response.status_code}",
                    'response': response.text[:500],
                    'status': 'failed'
                }
        else:
            # 获取服务器状态
            response = requests.get(
                "https://esi.evetech.net/latest/status/",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                status_data = response.json()
                session['api_test_result'] = {
                    'server_status': status_data,
                    'endpoint': 'status/',
                    'status': 'success'
                }
            else:
                session['api_test_result'] = {
                    'error': f"ESI API returned {response.status_code}",
                    'response': response.text[:500],
                    'status': 'failed'
                }
        
        session['success'] = "ESI API test completed"
        
    except Exception as e:
        session['error'] = f"ESI API test failed: {str(e)}"
    
    return redirect('/')


@app.route('/logout')
def logout():
    """登出并撤销令牌"""
    token_info = session.get('token_info')
    
    if token_info:
        try:
            # 尝试撤销访问令牌
            if 'access_token' in token_info:
                eve_sso.revoke_token(token_info['access_token'], 'access_token')
            
            # 尝试撤销刷新令牌
            if 'refresh_token' in token_info:
                eve_sso.revoke_token(token_info.get('refresh_token'), 'refresh_token')
        except Exception as e:
            print(f"撤销令牌时出错（可能已经过期）: {e}")
    
    # 清理会话
    session.clear()
    
    session['success'] = "Logged out successfully"
    
    return redirect('/')


@app.route('/debug')
def debug():
    """调试页面"""
    debug_info = {
        'client_id': client_id[:10] + '...' if client_id else 'Not set',
        'client_secret': 'Set' if client_secret and client_secret != 'your_client_secret_here' else 'Not set',
        'redirect_uri': redirect_uri,
        'session_keys': list(session.keys()),
        'token_info': session.get('token_info', {}).keys() if session.get('token_info') else None,
        'character_info': session.get('character_info'),
    }
    
    return jsonify(debug_info)


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 EVE Online SSO Demo")
    print("=" * 80)
    print(f"📝 Client ID: {client_id[:20]}...")
    print(f"📍 Redirect URI: {redirect_uri}")
    print("=" * 80)
    print("📋 配置检查:")
    print(f"  1. 确保已在 https://developers.eveonline.com/ 注册应用")
    print(f"  2. 回调URL必须设置为: {redirect_uri}")
    print(f"  3. 确保client_id和client_secret已正确配置")
    print("=" * 80)
    print("🌐 在浏览器中访问: http://localhost:5000")
    print("=" * 80)
    
    # 在开发环境中运行Flask应用
    app.run(debug=True, port=5000, host='0.0.0.0')