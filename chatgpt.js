import axios from 'axios';
import 'dotenv/config';

const KEY = process.env.OPENAI_API_KEY;

export async function askChatGPT(prompt) {
  try {
    const r = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: 'gpt-3.5-turbo',
        messages: [
          { role: 'system', content: '你是一位智慧農業助理，回答請使用繁體中文。' },
          { role: 'user', content: prompt }
        ]
      },
      {
        headers: { Authorization: `Bearer ${KEY}` }
      }
    );
    return r.data.choices[0].message.content.trim();
  } catch (e) {
    console.error('ChatGPT error:', e.response?.data || e.message);
    return '⚠️ 無法取得 AI 分析';
  }
}
