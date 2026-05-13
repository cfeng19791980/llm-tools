# -*- coding: utf-8 -*-
html_content = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM-Tools | AI Chat Interface</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #111827;
            --bg-tertiary: #1a2234;
            --bg-card: rgba(26, 34, 52, 0.7);
            --bg-card-hover: rgba(36, 48, 72, 0.8);
            --gradient-primary: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #db2777 100%);
            --gradient-accent: linear-gradient(135deg, #00d4ff 0%, #00ff88 100%);
            --gradient-bg: linear-gradient(135deg, #0a0e17 0%, #1a1a2e 50%, #16213e 100%);
            --neon-cyan: #00d4ff;
            --neon-purple: #7c3aed;
            --neon-pink: #db2777;
            --neon-green: #00ff88;
            --neon-gold: #fbbf24;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: rgba(0, 212, 255, 0.15);
            --border-glow: rgba(0, 212, 255, 0.3);
            --shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4);
            --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.2);
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--gradient-bg); color: var(--text-primary); height: 100vh; overflow: hidden; position: relative; }
        body::before { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: radial-gradient(ellipse at 20% 20%, rgba(0, 212, 255, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(124, 58, 237, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(219, 39, 119, 0.05) 0%, transparent 70%); pointer-events: none; z-index: 0; }
        body::after { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-image: linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px); background-size: 50px 50px; pointer-events: none; z-index: 0; }
        .app-container { display: flex; height: 100vh; position: relative; z-index: 1; }
        .sidebar { width: 320px; min-width: 320px; background: var(--bg-card); backdrop-filter: blur(20px); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; overflow-y: auto; position: relative; }
        .sidebar::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient-primary); }
        .sidebar-header { padding: var(--spacing-lg); text-align: center; border-bottom: 1px solid var(--border-color); position: relative; }
        .sidebar-logo { display: flex; align-items: center; justify-content: center; gap: var(--spacing-sm); margin-bottom: var(--spacing-xs); }
        .sidebar-logo-icon { width: 40px; height: 40px; background: var(--gradient-primary); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; box-shadow: var(--shadow-glow); }
        .sidebar-title { font-size: 22px; font-weight: 700; background: var(--gradient-accent); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; letter-spacing: 1px; }
        .sidebar-subtitle { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 2px; }
        .card { background: var(--bg-card); border-radius: 16px; padding: var(--spacing-lg); margin: var(--spacing-md); margin-bottom: 0; border: 1px solid var(--border-color); transition: all 0.3s ease; position: relative; overflow: hidden; }
        .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent); opacity: 0.5; }
        .card:hover { background: var(--bg-card-hover); border-color: var(--border-glow); transform: translateY(-2px); box-shadow: var(--shadow-card); }
        .card-header { display: flex; align-items: center; gap: var(--spacing-sm); margin-bottom: var(--spacing-md); padding-bottom: var(--spacing-md); border-bottom: 1px solid var(--border-color); }
        .card-icon { width: 32px; height: 32px; background: var(--gradient-primary); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); letter-spacing: 0.5px; text-transform: uppercase; }
        .form-group { margin-bottom: var(--spacing-md); }
        .form-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: var(--spacing-sm); font-weight: 500; }
        .form-input, .form-select { width: 100%; padding: 12px 16px; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-color); border-radius: 10px; color: var(--text-primary); font-size: 14px; font-family: inherit; transition: all 0.3s ease; outline: none; }
        .form-input:focus, .form-select:focus { border-color: var(--neon-cyan); box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1), var(--shadow-glow); }
        .form-select { cursor: pointer; appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2300d4ff' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px; }
        .form-select option { background: var(--bg-secondary); color: var(--text-primary); }
        .switch-row { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-sm) 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        .switch-row:last-child { border-bottom: none; }
        .switch-label { font-size: 13px; color: var(--text-secondary); }
        .switch { position: relative; width: 48px; height: 26px; background: rgba(0, 0, 0, 0.4); border-radius: 13px; cursor: pointer; border: 1px solid var(--border-color); transition: all 0.3s ease; }
        .switch-knob { position: absolute; width: 20px; height: 20px; background: var(--text-muted); border-radius: 50%; top: 2px; left: 3px; transition: all 0.3s ease; }
        .switch.active { background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple)); border-color: var(--neon-cyan); box-shadow: 0 0 15px rgba(0, 212, 255, 0.3); }
        .switch.active .switch-knob { left: 23px; background: #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
        .btn { padding: 12px 20px; border: none; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase; letter-spacing: 0.5px; font-family: inherit; display: inline-flex; align-items: center; justify-content: center; gap: var(--spacing-sm); }
        .btn:active { transform: scale(0.95); }
        .btn-primary { background: var(--gradient-primary); color: #fff; box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4); }
        .btn-danger { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3); }
        .btn-danger:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4); }
        .btn-secondary { background: rgba(255, 255, 255, 0.1); color: var(--text-secondary); border: 1px solid var(--border-color); }
        .btn-secondary:hover { background: rgba(255, 255, 255, 0.15); color: var(--text-primary); border-color: var(--neon-cyan); }
        .btn-group { display: flex; gap: var(--spacing-sm); margin-top: var(--spacing-md); }
        .btn-group .btn { flex: 1; }
        .btn-full { width: 100%; margin-top: var(--spacing-md); }
        .main-area { flex: 1; display: flex; flex-direction: column; position: relative; overflow: hidden; }
        .header { background: var(--bg-card); backdrop-filter: blur(20px); padding: var(--spacing-md) var(--spacing-xl); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; position: relative; }
        .header::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent); opacity: 0.5; }
        .header-title { font-size: 18px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: var(--spacing-sm); }
        .header-title::before { content: '✨'; }
        .status-bar { display: flex; align-items: center; gap: var(--spacing-lg); }
        .status-item { display: flex; align-items: center; gap: var(--spacing-sm); font-size: 12px; color: var(--text-secondary); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-muted); animation: pulse 2s infinite; }
        .status-dot.active { background: var(--neon-green); box-shadow: 0 0 10px var(--neon-green); }
        .status-dot.warning { background: var(--neon-gold); box-shadow: 0 0 10px var(--neon-gold); }
        .status-dot.error { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .status-link { color: var(--neon-cyan); text-decoration: none; transition: all 0.3s ease; }
        .status-link:hover { color: var(--neon-green); text-shadow: 0 0 10px var(--neon-green); }
        .chat-container { flex: 1; padding: var(--spacing-xl); overflow-y: auto; scroll-behavior: smooth; }
        .chat-container::-webkit-scrollbar { width: 6px; }
        .chat-container::-webkit-scrollbar-track { background: transparent; }
        .chat-container::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }
        .chat-container::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
        .message { margin-bottom: var(--spacing-lg); padding: var(--spacing-md) var(--spacing-lg); border-radius: 16px; max-width: 80%; position: relative; animation: messageIn 0.4s ease; line-height: 1.7; }
        @keyframes messageIn { from { opacity: 0; transform: translateY(20px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .message-header { display: flex; align-items: center; gap: var(--spacing-sm); margin-bottom: var(--spacing-sm); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
        .user-message { margin-left: auto; background: linear-gradient(135deg, rgba(124, 58, 237, 0.3), rgba(219, 39, 119, 0.2)); border: 1px solid rgba(124, 58, 237, 0.3); border-bottom-right-radius: 4px; }
        .user-message .message-header { color: var(--neon-pink); }
        .assistant-message { margin-right: auto; background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(124, 58, 237, 0.1)); border: 1px solid rgba(0, 212, 255, 0.2); border-bottom-left-radius: 4px; }
        .assistant-message .message-header { color: var(--neon-cyan); }
        .input-area { background: var(--bg-card); backdrop-filter: blur(20px); padding: var(--spacing-lg) var(--spacing-xl); border-top: 1px solid var(--border-color); position: relative; }
        .input-area::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--neon-purple), transparent); opacity: 0.5; }
        .input-wrapper { display: flex; gap: var(--spacing-md); align-items: flex-end; }
        .input-box { flex: 1; position: relative; }
        .input-textarea { width: 100%; min-height: 70px; max-height: 200px; padding: 16px 20px; background: rgba(0, 0, 0, 0.4); border: 1px solid var(--border-color); border-radius: 14px; color: var(--text-primary); font-size: 14px; font-family: inherit; resize: none; outline: none; transition: all 0.3s ease; line-height: 1.6; }
        .input-textarea:focus { border-color: var(--neon-cyan); box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1), var(--shadow-glow); }
        .input-textarea::placeholder { color: var(--text-muted); }
        .input-actions { display: flex; gap: var(--spacing-sm); }
        .btn-send { width: 56px; height: 56px; border-radius: 14px; padding: 0; font-size: 20px; }
        .btn-stop { width: 56px; height: 56px; border-radius: 14px; padding: 0; font-size: 18px; }
        .model-status-card { display: flex; align-items: center; gap: var(--spacing-md); padding: var(--spacing-md); background: rgba(0, 0, 0, 0.2); border-radius: 12px; margin-bottom: var(--spacing-md); }
        .model-status-indicator { width: 14px; height: 14px; border-radius: 50%; background: var(--text-muted); flex-shrink: 0; }
        .model-status-indicator.running { background: var(--neon-green); box-shadow: 0 0 15px var(--neon-green); animation: pulse 1.5s infinite; }
        .model-status-text { font-size: 13px; color: var(--text-secondary); }
        *:focus-visible { outline: 2px solid var(--neon-cyan); outline-offset: 2px; }
        ::selection { background: rgba(0, 212, 255, 0.3); color: #fff; }
        .tool-info { background: rgba(0, 0, 0, 0.3); border: 1px solid var(--neon-purple); border-radius: 10px; padding: var(--spacing-md); margin-bottom: var(--spacing-md); }
        .tool-info-title { color: var(--neon-purple); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: var(--spacing-sm); }
        .tool-info-item { font-size: 13px; color: var(--text-secondary); margin: var(--spacing-xs) 0; }
        .tool-info-item span { color: var(--neon-cyan); }
        .tool-result { color: var(--text-primary) !important; padding-top: var(--spacing-md); border-top: 1px solid rgba(255, 255, 255, 0.1); }
        @media (max-width: 900px) { .sidebar { width: 280px; min-width: 280px; } }
        @media (max-width: 768px) { .app-container { flex-direction: column; } .sidebar { width: 100%; min-width: 100%; max-height: 50vh; } .message { max-width: 95%; } }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-logo"><div class="sidebar-logo-icon">🧠</div></div>
                <div class="sidebar-title">LLM-Tools</div>
                <div class="sidebar-subtitle">AI Chat Interface</div>
            </div>
            <div class="card">
                <div class="card-header"><div class="card-icon">⚡</div><div class="card-title">Model Management</div></div>
                <div class="model-status-card"><div class="model-status-indicator" id="statusIndicator"></div><div class="model-status-text" id="modelInfoText">No model running</div></div>
                <div class="form-group"><label class="form-label">Model</label><select id="modelSelect" class="form-select" onchange="refreshModels()"><option value="">-- Select Model --</option></select></div>
                <div class="form-group"><label class="form-label">Port</label><input type="number" id="portInput" class="form-input" value="1235"></div>
                <div class="btn-group"><button class="btn btn-primary" id="startBtn" onclick="startModel()">▶ Start</button><button class="btn btn-danger" id="stopBtn" onclick="stopModel()">⬛ Stop</button></div>
            </div>
            <div class="card">
                <div class="card-header"><div class="card-icon">⚙️</div><div class="card-title">Parameters</div></div>
                <div class="form-group"><label class="form-label">GPU Layers (ngl)</label><input type="number" id="nglInput" class="form-input" value="99" min="1" max="99"></div>
                <div class="form-group"><label class="form-label">Context Length</label><input type="number" id="ctxInput" class="form-input" value="32000"></div>
                <div class="form-group"><label class="form-label">Threads</label><input type="number" id="threadsInput" class="form-input" value="8"></div>
                <div class="form-group"><label class="form-label">Temperature</label><input type="number" id="tempInput" class="form-input" value="0.05" step="0.01"></div>
                <div class="form-group"><label class="form-label">Seed</label><input type="number" id="seedInput" class="form-input" value="42"></div>
                <div class="switch-row"><span class="switch-label">Flash Attention</span><div class="switch active" id="flashAttnSwitch" onclick="toggleSwitch(this)"><div class="switch-knob"></div></div></div>
                <div class="switch-row"><span class="switch-label">Thinking Chain</span><div class="switch" id="thinkingSwitch" onclick="toggleSwitch(this)"><div class="switch-knob"></div></div></div>
            </div>
            <div class="card">
                <div class="card-header"><div class="card-icon">📁</div><div class="card-title">Config Files</div></div>
                <div class="form-group"><label class="form-label">Config Name</label><input type="text" id="configNameInput" class="form-input" value="default"></div>
                <div class="btn-group"><button class="btn btn-secondary" id="saveBtn" onclick="saveConfig()">💾 Save</button><button class="btn btn-secondary" id="loadBtn" onclick="loadConfig()">📂 Load</button></div>
                <div class="form-group" style="margin-top: var(--spacing-md);"><label class="form-label">Saved Configs</label><select id="configListSelect" class="form-select" onchange="selectConfig()"><option value="">-- Select --</option></select></div>
            </div>
            <div class="card" style="margin-bottom: var(--spacing-lg);"><button class="btn btn-secondary btn-full" id="clearBtn" onclick="clearChat()">🗑️ Clear Chat</button></div>
        </div>
        <div class="main-area">
            <div class="header">
                <div class="header-title">LLM-Tools AI Assistant</div>
                <div class="status-bar">
                    <div class="status-item"><div class="status-dot" id="backendStatus"></div><span>Backend</span></div>
                    <div class="status-item"><span>Server:</span><span id="serverPortText" style="color: var(--neon-cyan);">port 1235</span></div>
                    <div class="status-item"><span>Speed:</span><span id="speedText" style="color: var(--neon-green);">--</span></div>
                </div>
            </div>
            <div class="chat-container" id="chatContainer">
                <div class="message assistant-message">
                    <div class="message-header">🤖 Assistant</div>
                    <div class="message-content">Welcome to <strong style="color: var(--neon-cyan);">LLM-Tools</strong>! ✨<br><br>I am your AI assistant, ready to help you with various tasks.<br><br><strong style="color: var(--neon-purple);">Getting Started:</strong><br>1. Select a model from the sidebar<br>2. Click <strong style="color: var(--neon-green);">Start</strong> to launch it<br>3. Type your message below and press <strong style="color: var(--neon-cyan);">Enter</strong> to send<br><br>Feel free to explore the features! 🚀</div>
                </div>
            </div>
            <div class="input-area">
                <div class="input-wrapper">
                    <div class="input-box"><textarea id="inputBox" class="input-textarea" placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"></textarea></div>
                    <div class="input-actions"><button class="btn btn-primary btn-send" id="sendBtn" onclick="sendMessage()">➤</button><button class="btn btn-danger btn-stop" id="stopInferenceBtn" onclick="stopInference()">⬛</button></div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const BACKEND_API = 'http://127.0.0.1:5003';
        const LLAMA_SERVER = 'http://127.0.0.1:1235';
        let isStreaming = false;
        let currentController = null;
        function toggleSwitch(switchElement) { switchElement.classList.toggle('active'); }
        async function refreshModels() { try { const response = await fetch('/models_list.json'); const data = await response.json(); if (data.success) { const select = document.getElementById('modelSelect'); select.innerHTML = '<option value="">-- Select Model --</option>'; data.models.forEach(model => { const option = document.createElement('option'); option.value = model.name; option.textContent = model.name + ' (' + model.size + ')'; select.appendChild(option); }); } } catch (error) { console.log('models_list.json加载失败:', error); } }
        async function checkStatus() { try { const response = await fetch(BACKEND_API + '/api/status'); const data = await response.json(); const indicator = document.getElementById('statusIndicator'); const infoText = document.getElementById('modelInfoText'); if (data.running) { indicator.classList.add('running'); infoText.textContent = data.model + ' (PID: ' + data.pid + ', Port: ' + data.port + ')'; document.getElementById('serverPortText').textContent = 'port ' + data.port; } else { indicator.classList.remove('running'); infoText.textContent = 'No model running'; } } catch (error) { console.log('Backend not reachable'); } }
        async function startModel() { const model = document.getElementById('modelSelect').value; if (!model) { alert('Please select a model first'); return; } const params = { model: model, port: parseInt(document.getElementById('portInput').value), ngl: parseInt(document.getElementById('nglInput').value), ctx: parseInt(document.getElementById('ctxInput').value), threads: parseInt(document.getElementById('threadsInput').value), temp: parseFloat(document.getElementById('tempInput').value), seed: parseInt(document.getElementById('seedInput').value), flash_attn: document.getElementById('flashAttnSwitch').classList.contains('active') }; try { const response = await fetch(BACKEND_API + '/api/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) }); const data = await response.json(); if (data.success) { alert('Model started: ' + model + '\\nPID: ' + data.pid + '\\nPort: ' + data.port); checkStatus(); } else { alert('Error: ' + data.message); } } catch (error) { alert('Backend not running. Please start model_manager.py first.\\nRun: 启动_ModelManager.bat'); } }
        async function stopModel() { try { const response = await fetch(BACKEND_API + '/api/stop', { method: 'POST' }); const data = await response.json(); if (data.success) { alert(data.message); checkStatus(); } else { alert('Error: ' + data.message); } } catch (error) { alert('Backend not running'); } }
        async function saveConfig() { const configName = document.getElementById('configNameInput').value; if (!configName) { alert('Please enter config name'); return; } const params = { name: configName, model: document.getElementById('modelSelect').value, port: parseInt(document.getElementById('portInput').value), ngl: parseInt(document.getElementById('nglInput').value), ctx: parseInt(document.getElementById('ctxInput').value), threads: parseInt(document.getElementById('threadsInput').value), temp: parseFloat(document.getElementById('tempInput').value), seed: parseInt(document.getElementById('seedInput').value), flash_attn: document.getElementById('flashAttnSwitch').classList.contains('active') }; try { const response = await fetch(BACKEND_API + '/api/save_config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) }); const data = await response.json(); if (data.success) { alert('Config saved: ' + configName + '.bat\\nPath: ' + data.path); refreshConfigs(); } else { alert('Error: ' + data.message); } } catch (error) { alert('Backend not running'); } }
        async function loadConfig() { const configName = document.getElementById('configListSelect').value; if (!configName) { alert('Please select a config'); return; } try { const response = await fetch(BACKEND_API + '/api/load_config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: configName }) }); const data = await response.json(); if (data.success) { alert('Config loaded: ' + configName + '\\nCheck parameters in sidebar'); } else { alert('Error: ' + data.message); } } catch (error) { alert('Backend not running'); } }
        async function refreshConfigs() { try { const response = await fetch(BACKEND_API + '/api/list_configs'); const data = await response.json(); if (data.success) { const select = document.getElementById('configListSelect'); select.innerHTML = '<option value="">-- Select --</option>'; data.configs.forEach(config => { const option = document.createElement('option'); option.value = config.name; option.textContent = config.name + ' (' + config.mtime + ')'; select.appendChild(option); }); } } catch (error) { console.log('Backend not running'); } }
        function selectConfig() { const configName = document.getElementById('configListSelect').value; document.getElementById('configNameInput').value = configName; }
        async function sendMessage() { const input = document.getElementById('inputBox').value; if (!input.trim()) return; addMessage('user', input); document.getElementById('inputBox').value = ''; const aiMessageDiv = addMessage('assistant', ''); const contentDiv = aiMessageDiv.querySelector('.message-content'); try { const response = await fetch(BACKEND_API + '/api/stream_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ input: input, port: 1235 }) }); const reader = response.body.getReader(); const decoder = new TextDecoder(); let fullContent = ''; while (true) { const { done, value } = await reader.read(); if (done) break; const chunk = decoder.decode(value); const lines = chunk.split('\\n'); for (const line of lines) { if (line.startsWith('data: ')) { const dataStr = line.substring(6); try { const data = JSON.parse(dataStr); if (data.content) { fullContent += data.content; contentDiv.textContent = fullContent; document.getElementById('chatContainer').scrollTop = document.getElementById('chatContainer').scrollHeight; } if (data.done) { console.log('Stream completed:', data.full_content); } if (data.error) { contentDiv.textContent = '❌ 错误: ' + data.error; } } catch (e) { console.log('Parse error:', e); } } } } if (!fullContent) { contentDiv.textContent = '⚠️ 无响应内容'; } } catch (error) { contentDiv.textContent = '❌ 网络错误: ' + error.message; } }
        async function sendMessageWithTool() { const input = document.getElementById('inputBox').value; if (!input.trim()) return; addMessage('user', input); document.getElementById('inputBox').value = ''; const aiMessageDiv = addMessage('assistant', '正在处理...'); try { const response = await fetch(BACKEND_API + '/api/tool_chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ input: input, port: 1235 }) }); const data = await response.json(); if (data.success) { aiMessageDiv.querySelector('.message-content').textContent = ''; if (data.tool_used) { const toolInfo = document.createElement('div'); toolInfo.className = 'tool-info'; toolInfo.innerHTML = '<div class="tool-info-title">🔧 工具调用</div><div class="tool-info-item">工具: <span>' + data.tool + '</span></div><div class="tool-info-item">参数: <span>' + JSON.stringify(data.arguments) + '</span></div>'; aiMessageDiv.appendChild(toolInfo); const resultDiv = document.createElement('div'); resultDiv.className = 'tool-result'; resultDiv.textContent = data.result || '执行成功'; aiMessageDiv.appendChild(resultDiv); } else { aiMessageDiv.querySelector('.message-content').textContent = data.llm_output || '无法理解'; } } else { aiMessageDiv.querySelector('.message-content').textContent = '❌ 错误: ' + (data.message || '请求失败'); } } catch (error) { aiMessageDiv.querySelector('.message-content').textContent = '❌ 网络错误: ' + error.message; } }
        function stopInference() { if (isStreaming && currentController) { currentController.abort(); isStreaming = false; } }
        function addMessage(role, content) { const div = document.createElement('div'); div.className = 'message ' + role + '-message'; const label = document.createElement('div'); label.className = 'message-header'; label.textContent = role === 'user' ? '👤 You' : '🤖 Assistant