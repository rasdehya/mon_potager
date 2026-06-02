let sessionId = null;
let chatOpen = false;
let serverStarting = false;

function toggleChat() {
    const panel = document.getElementById('chat-panel');
    if (chatOpen) {
        panel.classList.remove('open');
        chatOpen = false;
        return;
    }
    serverStarting = true;
    const status = document.getElementById('chat-status');
    status.style.display = 'block';
    status.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Connexion à l\'assistant...';

    fetch('/api/chat/health')
        .then(r => r.json())
        .then(d => {
            serverStarting = false;
            if (d.ok) {
                panel.classList.add('open');
                chatOpen = true;
                status.style.display = 'none';
                document.getElementById('chat-input').focus();
            } else {
                status.innerHTML = '⚠️ ' + (d.error || 'Impossible de contacter l\'assistant');
                setTimeout(() => { status.style.display = 'none'; }, 5000);
            }
        })
        .catch(() => {
            serverStarting = false;
            status.innerHTML = '⚠️ Erreur réseau';
        });
}

async function ensureSession() {
    try {
        const r = await fetch('/api/chat/session', { method: 'POST' });
        const d = await r.json();
        if (d.ok) {
            sessionId = d.session_id;
            return true;
        }
        return false;
    } catch { return false; }
}

function addMessage(text, role) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-msg ' + role;
    div.innerHTML = '<div class="msg-content">' + text.replace(/\n/g, '<br>') + '</div>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function sendChat() {
    if (serverStarting) return;

    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    addMessage(text, 'user');

    const status = document.getElementById('chat-status');
    status.style.display = 'block';
    status.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> L\'assistant réfléchit...';

    const ok = await ensureSession();
    if (!ok) {
        status.innerHTML = '⚠️ Impossible de contacter l\'assistant. Vérifie que le serveur opencode est lancé : `opencode serve`';
        setTimeout(() => { status.style.display = 'none'; }, 6000);
        return;
    }

    const contextEl = document.getElementById('chat-context');
    const context = contextEl ? contextEl.getAttribute('data-context') : '';

    try {
        const r = await fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, text, context }),
        });
        const d = await r.json();
        status.style.display = 'none';
        if (d.ok && d.reply) {
            addMessage(d.reply, 'ai');
        } else {
            addMessage('⚠️ ' + (d.error || 'Pas de réponse'), 'ai');
        }
    } catch (e) {
        status.style.display = 'none';
        addMessage('⚠️ Erreur de connexion à l\'assistant', 'ai');
    }
}
