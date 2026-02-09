from flask import Flask, request, jsonify
import json
import sqlite3
import os

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('rigs.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rigs
                 (id TEXT PRIMARY KEY, type TEXT, data TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS connections
                 (id TEXT PRIMARY KEY, source TEXT, target TEXT, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Programming System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3d3d3d;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --accent: #007acc;
            --accent-hover: #0098ff;
            --border: #404040;
            --success: #4caf50;
            --warning: #ff9800;
            --error: #f44336;
        }

        [data-theme="light"] {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-tertiary: #e0e0e0;
            --text-primary: #212121;
            --text-secondary: #757575;
            --border: #d0d0d0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            overflow: hidden;
        }

        #canvas-container {
            width: 100%;
            height: calc(100vh - 60px);
            position: relative;
            overflow: hidden;
            background: linear-gradient(90deg, var(--border) 1px, transparent 1px),
                        linear-gradient(var(--border) 1px, transparent 1px);
            background-size: 20px 20px;
        }

        #canvas {
            width: 100%;
            height: 100%;
            position: absolute;
            cursor: grab;
        }

        #canvas:active {
            cursor: grabbing;
        }

        svg {
            position: absolute;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        }

        .rig {
            position: absolute;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 8px;
            min-width: 250px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10;
            transition: box-shadow 0.2s;
        }

        .rig:hover {
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }

        .rig.selected {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.3);
        }

        .rig-header {
            padding: 10px 12px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
            cursor: move;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-radius: 6px 6px 0 0;
        }

        .rig-title {
            font-weight: 600;
            font-size: 14px;
            flex: 1;
        }

        .rig-btn {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            transition: all 0.2s;
        }

        .rig-btn:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .rig-content {
            padding: 12px;
            max-height: 400px;
            overflow-y: auto;
        }

        .rig-content::-webkit-scrollbar {
            width: 8px;
        }

        .rig-content::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        .rig-content::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        .connector {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            position: absolute;
            cursor: crosshair;
            transition: all 0.2s;
            z-index: 100;
        }

        .connector.input {
            left: -6px;
            background: var(--success);
            border: 2px solid var(--bg-secondary);
        }

        .connector.output {
            right: -6px;
            background: var(--accent);
            border: 2px solid var(--bg-secondary);
        }

        .connector:hover {
            transform: scale(1.3);
            box-shadow: 0 0 10px currentColor;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }

        .data-table th,
        .data-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .data-table th {
            background: var(--bg-tertiary);
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        .data-table input {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
        }

        .function-input {
            margin-top: 8px;
        }

        .function-input input,
        .function-input select,
        .function-input textarea {
            width: 100%;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 4px;
        }

        .function-input textarea {
            resize: vertical;
            min-height: 60px;
            font-family: 'Courier New', monospace;
        }

        .function-input label {
            font-size: 11px;
            color: var(--text-secondary);
            display: block;
        }

        .execute-btn {
            width: 100%;
            margin-top: 8px;
            padding: 8px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }

        .execute-btn:hover {
            background: var(--accent-hover);
        }

        .output-area {
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 8px;
            margin-top: 8px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-height: 150px;
            overflow-y: auto;
        }

        #bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 10px;
            z-index: 1000;
            overflow-x: auto;
        }

        #bottom-nav::-webkit-scrollbar {
            height: 6px;
        }

        #bottom-nav::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 3px;
        }

        .nav-btn {
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            white-space: nowrap;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .nav-btn:hover {
            background: var(--accent);
            border-color: var(--accent);
            transform: translateY(-2px);
        }

        .mode-switcher {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            z-index: 1000;
            display: flex;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .mode-btn {
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text-primary);
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }

        .mode-btn:hover {
            background: var(--accent);
        }

        .mode-btn.active {
            background: var(--accent);
            border-color: var(--accent-hover);
        }

        .add-column-btn {
            padding: 6px 12px;
            background: var(--success);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin: 5px 5px 8px 0;
        }

        .add-column-btn:hover {
            opacity: 0.9;
        }

        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
        }

        .chat-message {
            padding: 8px 12px;
            border-radius: 6px;
            max-width: 80%;
        }

        .chat-message.user {
            background: var(--accent);
            align-self: flex-end;
            margin-left: auto;
        }

        .chat-message.assistant {
            background: var(--bg-tertiary);
            align-self: flex-start;
        }

        .chat-input-container {
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }

        .chat-input-container input {
            flex: 1;
        }

        .neural-layer {
            margin: 10px 0;
        }

        .neural-node {
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: #e74c3c;
            margin: 5px;
            position: relative;
        }

        .neural-node::after {
            content: attr(data-value);
            position: absolute;
            bottom: -20px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 10px;
            white-space: nowrap;
        }

        .context-menu {
            position: fixed;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 6px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: none;
        }

        .context-menu-item {
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 13px;
            white-space: nowrap;
        }

        .context-menu-item:hover {
            background: var(--bg-tertiary);
        }

        .type-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 8px;
            background: var(--accent);
        }

        .spinner {
            border: 3px solid var(--border);
            border-top: 3px solid var(--accent);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="mode-switcher">
        <button class="mode-btn active" onclick="setTheme('dark')">🌙 Dark</button>
        <button class="mode-btn" onclick="setTheme('light')">☀️ Light</button>
        <button class="mode-btn" onclick="toggleAutoConnect()">🔗 Auto</button>
        <button class="mode-btn" onclick="clearCanvas()">🗑️ Clear</button>
        <button class="mode-btn" onclick="saveWorkspace()">💾 Save</button>
        <button class="mode-btn" onclick="loadWorkspace()">📂 Load</button>
    </div>

    <div id="canvas-container">
        <svg id="connections-svg"></svg>
        <div id="canvas"></div>
    </div>

    <div id="bottom-nav">
        <button class="nav-btn" onclick="addRig('data')"><span>📊</span> Data</button>
        <button class="nav-btn" onclick="addRig('table')"><span>📋</span> Table</button>
        <button class="nav-btn" onclick="addRig('function')"><span>⚙️</span> Function</button>
        <button class="nav-btn" onclick="addRig('llm')"><span>🤖</span> LLM</button>
        <button class="nav-btn" onclick="addRig('neural')"><span>🧠</span> Neural</button>
        <button class="nav-btn" onclick="addRig('chart')"><span>📈</span> Chart</button>
        <button class="nav-btn" onclick="addRig('database')"><span>💾</span> Database</button>
        <button class="nav-btn" onclick="addRig('custom')"><span>✨</span> Custom</button>
    </div>

    <div id="context-menu" class="context-menu">
        <div class="context-menu-item" onclick="duplicateRig()">Duplicate</div>
        <div class="context-menu-item" onclick="deleteRig()">Delete</div>
        <div class="context-menu-item" onclick="exportRig()">Export</div>
    </div>

    <script>
        let rigs = [];
        let connections = [];
        let selectedRig = null;
        let draggedRig = null;
        let canvasOffset = { x: 0, y: 0 };
        let isPanning = false;
        let panStart = { x: 0, y: 0 };
        let connectionStart = null;
        let rigCounter = 0;
        let autoConnect = false;
        let contextMenuTarget = null;

        const canvas = document.getElementById('canvas');
        const svg = document.getElementById('connections-svg');
        const contextMenu = document.getElementById('context-menu');

        document.addEventListener('DOMContentLoaded', () => {
            loadWorkspace();
            setupEventListeners();
        });

        function setupEventListeners() {
            canvas.addEventListener('mousedown', (e) => {
                if (e.target === canvas) {
                    isPanning = true;
                    panStart = { x: e.clientX - canvasOffset.x, y: e.clientY - canvasOffset.y };
                }
            });

            document.addEventListener('mousemove', (e) => {
                if (isPanning) {
                    canvasOffset.x = e.clientX - panStart.x;
                    canvasOffset.y = e.clientY - panStart.y;
                    canvas.style.transform = `translate(${canvasOffset.x}px, ${canvasOffset.y}px)`;
                    updateConnections();
                }
            });

            document.addEventListener('mouseup', () => {
                isPanning = false;
            });

            document.addEventListener('click', (e) => {
                if (!contextMenu.contains(e.target)) {
                    contextMenu.style.display = 'none';
                }
            });

            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                    e.preventDefault();
                    saveWorkspace();
                }
                if (e.key === 'Delete' && selectedRig) {
                    deleteRig();
                }
            });
        }

        function addRig(type) {
            const rigId = `rig-${++rigCounter}`;
            const rig = {
                id: rigId,
                type: type,
                x: 100 + Math.random() * 300,
                y: 100 + Math.random() * 200,
                data: getRigDefaultData(type)
            };
            rigs.push(rig);
            createRigElement(rig);
            saveToBackend(rig);
        }

        function getRigDefaultData(type) {
            switch(type) {
                case 'table':
                    return { columns: ['Col 1', 'Col 2', 'Col 3'], rows: [['', '', ''], ['', '', '']] };
                case 'function':
                    return { functionType: 'sum', code: '// Custom function\\nreturn input;' };
                case 'neural':
                    return { layers: [4, 6, 4, 2], activation: 'relu' };
                case 'llm':
                    return { messages: [], model: 'gpt-4', temperature: 0.7 };
                case 'chart':
                    return { chartType: 'line', data: [] };
                case 'database':
                    return { tables: [], queries: [] };
                default:
                    return {};
            }
        }

        function createRigElement(rig) {
            const rigEl = document.createElement('div');
            rigEl.className = 'rig';
            rigEl.id = rig.id;
            rigEl.style.left = rig.x + 'px';
            rigEl.style.top = rig.y + 'px';

            rigEl.innerHTML = `
                <div class="rig-header">
                    <div class="rig-title">${getTypeIcon(rig.type)} ${rig.type}<span class="type-badge">${rig.type.toUpperCase()}</span></div>
                    <div><button class="rig-btn" onclick="minimizeRig('${rig.id}')">−</button>
                    <button class="rig-btn" onclick="removeRig('${rig.id}')">×</button></div>
                </div>
                <div class="rig-content" id="${rig.id}-content">${getRigContent(rig)}</div>
            `;

            const inputConnector = document.createElement('div');
            inputConnector.className = 'connector input';
            inputConnector.style.top = '20px';
            inputConnector.onclick = (e) => handleConnectorClick(e, rig.id, 'input');
            rigEl.appendChild(inputConnector);

            const outputConnector = document.createElement('div');
            outputConnector.className = 'connector output';
            outputConnector.style.top = '20px';
            outputConnector.onclick = (e) => handleConnectorClick(e, rig.id, 'output');
            rigEl.appendChild(outputConnector);

            const header = rigEl.querySelector('.rig-header');
            header.addEventListener('mousedown', (e) => startDrag(e, rig));

            rigEl.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e, rig);
            });

            rigEl.addEventListener('click', () => selectRig(rig.id));
            canvas.appendChild(rigEl);
        }

        function getRigContent(rig) {
            switch(rig.type) {
                case 'table': return createTableContent(rig);
                case 'function': return createFunctionContent(rig);
                case 'neural': return createNeuralContent(rig);
                case 'llm': return createLLMContent(rig);
                case 'chart': return createChartContent(rig);
                case 'database': return createDatabaseContent(rig);
                case 'data': return createDataContent(rig);
                default: return '<p>Custom Rig - Add your content here</p>';
            }
        }

        function createTableContent(rig) {
            let html = '<div>';
            html += `<button class="add-column-btn" onclick="addColumn('${rig.id}')">+ Column</button>`;
            html += `<button class="add-column-btn" onclick="addRow('${rig.id}')">+ Row</button></div>`;
            html += '<table class="data-table"><thead><tr>';
            rig.data.columns.forEach((col, i) => {
                html += `<th><input value="${col}" onchange="updateColumnName('${rig.id}', ${i}, this.value)" /></th>`;
            });
            html += '</tr></thead><tbody>';
            rig.data.rows.forEach((row, ri) => {
                html += '<tr>';
                row.forEach((cell, ci) => {
                    html += `<td><input value="${cell}" onchange="updateCell('${rig.id}', ${ri}, ${ci}, this.value)" /></td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            return html;
        }

        function createFunctionContent(rig) {
            return `
                <div class="function-input"><label>Function Type</label>
                <select onchange="updateFunctionType('${rig.id}', this.value)">
                    <option value="sum">Sum</option><option value="average">Average</option>
                    <option value="filter">Filter</option><option value="map">Map</option>
                    <option value="custom">Custom</option>
                </select></div>
                <div class="function-input"><label>Custom Code (JavaScript)</label>
                <textarea onchange="updateFunctionCode('${rig.id}', this.value)">${rig.data.code}</textarea></div>
                <button class="execute-btn" onclick="executeFunction('${rig.id}')">Execute Function</button>
                <div class="output-area" id="${rig.id}-output">Output will appear here...</div>
            `;
        }

        function createNeuralContent(rig) {
            let html = '<div class="function-input"><label>Network Architecture (comma-separated)</label>';
            html += `<input value="${rig.data.layers.join(',')}" onchange="updateNeuralLayers('${rig.id}', this.value)" /></div>`;
            rig.data.layers.forEach((count, i) => {
                html += `<div class="neural-layer"><small>Layer ${i + 1} (${count} nodes)</small><br>`;
                for(let j = 0; j < Math.min(count, 8); j++) {
                    html += `<div class="neural-node" data-value="${(Math.random()).toFixed(2)}"></div>`;
                }
                if(count > 8) html += `<span>... +${count - 8} more</span>`;
                html += '</div>';
            });
            html += `<button class="execute-btn" onclick="trainNetwork('${rig.id}')">Train Network</button>`;
            return html;
        }

        function createLLMContent(rig) {
            let html = `<div class="chat-container" id="${rig.id}-chat">`;
            rig.data.messages.forEach(msg => {
                html += `<div class="chat-message ${msg.role}">${msg.content}</div>`;
            });
            html += '</div><div class="chat-input-container">';
            html += `<input type="text" id="${rig.id}-input" placeholder="Type a message..." onkeypress="if(event.key==='Enter') sendLLMMessage('${rig.id}')" />`;
            html += `<button class="execute-btn" style="margin:0;width:auto;padding:6px 12px;" onclick="sendLLMMessage('${rig.id}')">Send</button></div>`;
            return html;
        }

        function createChartContent(rig) {
            return `<div class="function-input"><label>Chart Type</label>
                <select onchange="updateChartType('${rig.id}', this.value)">
                    <option value="line">Line Chart</option><option value="bar">Bar Chart</option>
                    <option value="pie">Pie Chart</option><option value="scatter">Scatter Plot</option>
                </select></div>
                <div style="width:100%;height:150px;background:var(--bg-primary);border-radius:4px;display:flex;align-items:center;justify-content:center;">
                    Chart will render here
                </div>`;
        }

        function createDatabaseContent(rig) {
            return `<div class="function-input"><label>SQL Query</label>
                <textarea placeholder="SELECT * FROM table_name"></textarea></div>
                <button class="execute-btn" onclick="executeQuery('${rig.id}')">Run Query</button>
                <div class="output-area" id="${rig.id}-query-output">Results will appear here...</div>`;
        }

        function createDataContent(rig) {
            return `<div class="function-input"><label>Data Source</label>
                <input type="text" placeholder="Enter data or URL" /></div>
                <div class="function-input"><label>Format</label>
                <select><option>JSON</option><option>CSV</option><option>XML</option></select></div>
                <button class="execute-btn" onclick="loadData('${rig.id}')">Load Data</button>`;
        }

        function startDrag(e, rig) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            draggedRig = rig;
            const rigEl = document.getElementById(rig.id);
            const rect = rigEl.getBoundingClientRect();
            draggedRig.offsetX = e.clientX - rect.left;
            draggedRig.offsetY = e.clientY - rect.top;
            document.addEventListener('mousemove', doDrag);
            document.addEventListener('mouseup', stopDrag);
        }

        function doDrag(e) {
            if (!draggedRig) return;
            const rigEl = document.getElementById(draggedRig.id);
            draggedRig.x = e.clientX - draggedRig.offsetX - canvasOffset.x;
            draggedRig.y = e.clientY - draggedRig.offsetY - canvasOffset.y;
            rigEl.style.left = draggedRig.x + 'px';
            rigEl.style.top = draggedRig.y + 'px';
            updateConnections();
        }

        function stopDrag() {
            if (draggedRig) saveToBackend(draggedRig);
            draggedRig = null;
            document.removeEventListener('mousemove', doDrag);
            document.removeEventListener('mouseup', stopDrag);
        }

        function handleConnectorClick(e, rigId, type) {
            e.stopPropagation();
            if (!connectionStart) {
                connectionStart = { rigId, type };
            } else {
                if (connectionStart.rigId !== rigId) {
                    createConnection(connectionStart.rigId, rigId);
                }
                connectionStart = null;
            }
        }

        function createConnection(sourceId, targetId) {
            const connId = `conn-${sourceId}-${targetId}`;
            if (connections.find(c => c.id === connId)) return;
            const connection = { id: connId, source: sourceId, target: targetId };
            connections.push(connection);
            updateConnections();
            saveConnectionToBackend(connection);
        }

        function updateConnections() {
            svg.innerHTML = '';
            connections.forEach(conn => {
                const sourceRig = rigs.find(r => r.id === conn.source);
                const targetRig = rigs.find(r => r.id === conn.target);
                if (!sourceRig || !targetRig) return;
                const sourceEl = document.getElementById(sourceRig.id);
                const targetEl = document.getElementById(targetRig.id);
                if (!sourceEl || !targetEl) return;
                const sourceRect = sourceEl.getBoundingClientRect();
                const targetRect = targetEl.getBoundingClientRect();
                const canvasRect = canvas.getBoundingClientRect();
                const x1 = sourceRect.right - canvasRect.left;
                const y1 = sourceRect.top - canvasRect.top + 20;
                const x2 = targetRect.left - canvasRect.left;
                const y2 = targetRect.top - canvasRect.top + 20;
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const dx = Math.abs(x2 - x1);
                const curve = `M ${x1} ${y1} C ${x1 + dx * 0.5} ${y1}, ${x2 - dx * 0.5} ${y2}, ${x2} ${y2}`;
                path.setAttribute('d', curve);
                path.setAttribute('stroke', '#007acc');
                path.setAttribute('stroke-width', '2');
                path.setAttribute('fill', 'none');
                path.setAttribute('opacity', '0.6');
                svg.appendChild(path);
            });
        }

        function removeRig(rigId) {
            const index = rigs.findIndex(r => r.id === rigId);
            if (index > -1) {
                rigs.splice(index, 1);
                document.getElementById(rigId).remove();
                connections = connections.filter(c => c.source !== rigId && c.target !== rigId);
                updateConnections();
                fetch('/api/rigs', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: rigId }) });
            }
        }

        function selectRig(rigId) {
            document.querySelectorAll('.rig').forEach(r => r.classList.remove('selected'));
            selectedRig = rigId;
            document.getElementById(rigId).classList.add('selected');
        }

        function minimizeRig(rigId) {
            const content = document.getElementById(rigId + '-content');
            content.style.display = content.style.display === 'none' ? 'block' : 'none';
        }

        function updateRigContent(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                document.getElementById(rigId + '-content').innerHTML = getRigContent(rig);
                saveToBackend(rig);
            }
        }

        function addColumn(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.columns.push(`Col ${rig.data.columns.length + 1}`);
                rig.data.rows.forEach(row => row.push(''));
                updateRigContent(rigId);
            }
        }

        function addRow(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.rows.push(new Array(rig.data.columns.length).fill(''));
                updateRigContent(rigId);
            }
        }

        function updateColumnName(rigId, colIndex, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.columns[colIndex] = value;
                saveToBackend(rig);
            }
        }

        function updateCell(rigId, rowIndex, colIndex, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.rows[rowIndex][colIndex] = value;
                saveToBackend(rig);
            }
        }

        function updateFunctionType(rigId, type) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.functionType = type;
                saveToBackend(rig);
            }
        }

        function updateFunctionCode(rigId, code) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.code = code;
                saveToBackend(rig);
            }
        }

        function executeFunction(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                const output = document.getElementById(rigId + '-output');
                output.innerHTML = '<div class="spinner"></div> Executing...';
                const inputConnections = connections.filter(c => c.target === rigId);
                const inputData = inputConnections.map(c => {
                    const sourceRig = rigs.find(r => r.id === c.source);
                    return sourceRig ? sourceRig.data : null;
                });
                try {
                    const func = new Function('input', rig.data.code);
                    const result = func(inputData);
                    output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                } catch(e) {
                    output.innerHTML = `<span style="color:var(--error)">Error: ${e.message}</span>`;
                }
            }
        }

        function updateNeuralLayers(rigId, value) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.layers = value.split(',').map(n => parseInt(n.trim()));
                updateRigContent(rigId);
            }
        }

        function trainNetwork(rigId) {
            alert('Neural network training initiated for ' + rigId);
        }

        function sendLLMMessage(rigId) {
            const rig = rigs.find(r => r.id === rigId);
            const input = document.getElementById(rigId + '-input');
            if (rig && input.value.trim()) {
                rig.data.messages.push({ role: 'user', content: input.value });
                setTimeout(() => {
                    rig.data.messages.push({ role: 'assistant', content: 'This is a simulated AI response. Connect to actual LLM API for real responses.' });
                    updateRigContent(rigId);
                }, 1000);
                updateRigContent(rigId);
                input.value = '';
            }
        }

        function updateChartType(rigId, type) {
            const rig = rigs.find(r => r.id === rigId);
            if (rig) {
                rig.data.chartType = type;
                saveToBackend(rig);
            }
        }

        function executeQuery(rigId) {
            alert('Database query executed for ' + rigId);
        }

        function loadData(rigId) {
            alert('Data loaded for ' + rigId);
        }

        function showContextMenu(e, rig) {
            contextMenuTarget = rig;
            contextMenu.style.left = e.clientX + 'px';
            contextMenu.style.top = e.clientY + 'px';
            contextMenu.style.display = 'block';
        }

        function duplicateRig() {
            if (contextMenuTarget || selectedRig) {
                const original = rigs.find(r => r.id === (contextMenuTarget?.id || selectedRig));
                if (original) {
                    const newRig = { ...original, id: `rig-${++rigCounter}`, x: original.x + 30, y: original.y + 30 };
                    rigs.push(newRig);
                    createRigElement(newRig);
                    saveToBackend(newRig);
                }
            }
            contextMenu.style.display = 'none';
        }

        function deleteRig() {
            if (contextMenuTarget || selectedRig) {
                removeRig(contextMenuTarget?.id || selectedRig);
            }
            contextMenu.style.display = 'none';
        }

        function exportRig() {
            if (contextMenuTarget) {
                const data = JSON.stringify(contextMenuTarget, null, 2);
                const blob = new Blob([data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${contextMenuTarget.id}.json`;
                a.click();
            }
            contextMenu.style.display = 'none';
        }

        function saveWorkspace() {
            localStorage.setItem('workspace', JSON.stringify({ rigs, connections }));
            rigs.forEach(saveToBackend);
            connections.forEach(saveConnectionToBackend);
            alert('Workspace saved successfully!');
        }

        function loadWorkspace() {
            fetch('/api/rigs').then(r => r.json()).then(data => {
                rigs = data;
                canvas.innerHTML = '';
                rigs.forEach(createRigElement);
                return fetch('/api/connections');
            }).then(r => r.json()).then(data => {
                connections = data;
                updateConnections();
            }).catch(err => console.log('Loading from local storage...'));
        }

        function clearCanvas() {
            if (confirm('Clear all rigs and connections?')) {
                rigs = [];
                connections = [];
                canvas.innerHTML = '';
                svg.innerHTML = '';
            }
        }

        function saveToBackend(rig) {
            fetch('/api/rigs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(rig) });
        }

        function saveConnectionToBackend(connection) {
            fetch('/api/connections', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(connection) });
        }

        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        function toggleAutoConnect() {
            autoConnect = !autoConnect;
            event.target.classList.toggle('active');
            alert(`Auto-connect ${autoConnect ? 'enabled' : 'disabled'}`);
        }

        function getTypeIcon(type) {
            const icons = { data: '📊', table: '📋', function: '⚙️', llm: '🤖', neural: '🧠', chart: '📈', database: '💾', custom: '✨' };
            return icons[type] || '📦';
        }

        setTimeout(() => {
            addRig('data');
            addRig('function');
        }, 500);
    </script>
</body>
</html>'''

@app.route('/api/rigs', methods=['GET', 'POST', 'DELETE'])
def handle_rigs():
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO rigs VALUES (?, ?, ?)',
                  (data['id'], data['type'], json.dumps(data)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    elif request.method == 'DELETE':
        rig_id = request.json.get('id')
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('DELETE FROM rigs WHERE id = ?', (rig_id,))
        c.execute('DELETE FROM connections WHERE source LIKE ? OR target LIKE ?', 
                  (f'{rig_id}%', f'{rig_id}%'))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    else:
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('SELECT data FROM rigs')
        rigs = [json.loads(row[0]) for row in c.fetchall()]
        conn.close()
        return jsonify(rigs)

@app.route('/api/connections', methods=['GET', 'POST', 'DELETE'])
def handle_connections():
    if request.method == 'POST':
        data = request.json
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO connections VALUES (?, ?, ?, ?)',
                  (data['id'], data['source'], data['target'], json.dumps(data)))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    elif request.method == 'DELETE':
        conn_id = request.json.get('id')
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('DELETE FROM connections WHERE id = ?', (conn_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    else:
        conn = sqlite3.connect('rigs.db')
        c = conn.cursor()
        c.execute('SELECT data FROM connections')
        connections = [json.loads(row[0]) for row in c.fetchall()]
        conn.close()
        return jsonify(connections)

@app.route('/api/execute', methods=['POST'])
def execute_function():
    data = request.json
    function_type = data.get('function')
    params = data.get('params', {})
    result = {'status': 'success', 'output': f'Executed {function_type} with params: {params}'}
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5550))
    app.run(host="0.0.0.0", port=port)
