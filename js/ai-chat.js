// Unrestricted AI Chat Component
class UnrestrictedAIChat {
  constructor(containerId) {
    this.containerId = containerId;
    this.messages = [];
    this.isLoading = false;
    this.apiUrl = 'https://3000-i3ojomrzbqt0ixbfydiyw-b41da9b2.us2.manus.computer/api/trpc/chat.sendMessage';
    this.init();
  }

  init() {
    this.createChatUI();
    this.attachEventListeners();
    this.loadMessages();
  }

  createChatUI() {
    const container = document.getElementById(this.containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="ai-chat-container">
        <div class="ai-chat-header">
          <h2>Unrestricted AI Assistant</h2>
          <button class="ai-chat-close" onclick="aiChat.toggleMinimize()">−</button>
        </div>
        <div class="ai-chat-messages" id="aiChatMessages">
          <div class="ai-chat-welcome">
            <h3>Welcome to Unrestricted AI</h3>
            <p>Ask me anything - I'm here to help with no restrictions.</p>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">Type /imagine [description] to generate images</p>
          </div>
        </div>
        <div class="ai-chat-input-area">
          <input 
            type="text" 
            id="aiChatInput" 
            class="ai-chat-input" 
            placeholder="Type your message... (/imagine for images)"
            autocomplete="off"
          />
          <button class="ai-chat-send" onclick="aiChat.sendMessage()">Send</button>
        </div>
      </div>
    `;
  }

  attachEventListeners() {
    const input = document.getElementById('aiChatInput');
    if (input) {
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.sendMessage();
        }
      });
    }
  }

  async sendMessage() {
    const input = document.getElementById('aiChatInput');
    const message = input.value.trim();
    
    if (!message) return;

    // Add user message to UI
    this.addMessageToUI('user', message);
    input.value = '';

    // Check if it's an /imagine command
    if (message.startsWith('/imagine ')) {
      const prompt = message.substring(9);
      await this.generateImage(prompt);
      return;
    }

    // Send regular message to AI
    await this.sendToAI(message);
  }

  addMessageToUI(role, content) {
    const messagesContainer = document.getElementById('aiChatMessages');
    
    // Remove welcome message if it exists
    const welcome = messagesContainer.querySelector('.ai-chat-welcome');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-chat-message ai-chat-message-${role}`;
    
    if (role === 'assistant') {
      messageDiv.innerHTML = `
        <div class="ai-chat-message-content">
          <div class="ai-chat-message-text">${this.escapeHtml(content)}</div>
        </div>
      `;
    } else {
      messageDiv.innerHTML = `
        <div class="ai-chat-message-content">
          <div class="ai-chat-message-text">${this.escapeHtml(content)}</div>
        </div>
      `;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async sendToAI(message) {
    this.isLoading = true;
    this.addMessageToUI('assistant', 'Thinking...');

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversationId: this.getConversationId(),
          message: message
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response from AI');
      }

      const data = await response.json();
      
      // Remove "Thinking..." message
      const messagesContainer = document.getElementById('aiChatMessages');
      const lastMessage = messagesContainer.lastChild;
      if (lastMessage && lastMessage.textContent.includes('Thinking...')) {
        lastMessage.remove();
      }

      // Add AI response
      const aiMessage = data.result?.data?.response || 'No response received';
      this.addMessageToUI('assistant', aiMessage);

    } catch (error) {
      console.error('Error:', error);
      this.addMessageToUI('assistant', 'Sorry, I encountered an error. Please try again.');
    } finally {
      this.isLoading = false;
    }
  }

  async generateImage(prompt) {
    this.addMessageToUI('assistant', 'Generating image... This may take a moment.');

    try {
      const response = await fetch('https://3000-i3ojomrzbqt0ixbfydiyw-b41da9b2.us2.manus.computer/api/trpc/chat.generateImage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversationId: this.getConversationId(),
          prompt: prompt
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate image');
      }

      const data = await response.json();
      const imageUrl = data.result?.data?.url;

      if (imageUrl) {
        const messagesContainer = document.getElementById('aiChatMessages');
        const lastMessage = messagesContainer.lastChild;
        if (lastMessage) lastMessage.remove();

        const imageDiv = document.createElement('div');
        imageDiv.className = 'ai-chat-message ai-chat-message-assistant';
        imageDiv.innerHTML = `
          <div class="ai-chat-message-content">
            <img src="${imageUrl}" alt="Generated image" class="ai-chat-image" />
            <p style="font-size: 12px; color: #999; margin-top: 5px;">Prompt: ${this.escapeHtml(prompt)}</p>
          </div>
        `;
        messagesContainer.appendChild(imageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    } catch (error) {
      console.error('Error generating image:', error);
      const messagesContainer = document.getElementById('aiChatMessages');
      const lastMessage = messagesContainer.lastChild;
      if (lastMessage) lastMessage.remove();
      this.addMessageToUI('assistant', 'Failed to generate image. Please try again.');
    }
  }

  getConversationId() {
    let conversationId = localStorage.getItem('aiChatConversationId');
    if (!conversationId) {
      conversationId = 'conv_' + Date.now();
      localStorage.setItem('aiChatConversationId', conversationId);
    }
    return conversationId;
  }

  loadMessages() {
    // Load previous messages from localStorage if available
    const savedMessages = localStorage.getItem('aiChatMessages');
    if (savedMessages) {
      try {
        this.messages = JSON.parse(savedMessages);
        const messagesContainer = document.getElementById('aiChatMessages');
        messagesContainer.innerHTML = '';
        this.messages.forEach(msg => {
          this.addMessageToUI(msg.role, msg.content);
        });
      } catch (e) {
        console.error('Error loading messages:', e);
      }
    }
  }

  toggleMinimize() {
    const container = document.querySelector('.ai-chat-container');
    if (container) {
      container.classList.toggle('minimized');
    }
  }

  escapeHtml(text) {
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
}

// Initialize chat when page loads
let aiChat;
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('aiChatWidget')) {
    aiChat = new UnrestrictedAIChat('aiChatWidget');
  }
});
