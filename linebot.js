import axios from 'axios';
import 'dotenv/config';
import { askChatGPT } from './chatgpt.js';

const TOKEN = process.env.LINE_CHANNEL_ACCESS_TOKEN;
const USER_ID = process.env.LINE_USER_ID;

export async function pushMessage(text) {
  if (!TOKEN || !USER_ID) return console.error('LINE token/userId not set');
  try {
    await axios.post(
      'https://api.line.me/v2/bot/message/push',
      { to: USER_ID, messages: [{ type: 'text', text }] },
      { headers: { Authorization: `Bearer ${TOKEN}` } }
    );
    console.log('✅ push sent');
  } catch (e) {
    console.error('❌ push error:', e.response?.data || e.message);
  }
}

export async function handleWebhook(req, res) {
  for (const ev of req.body.events || []) {
    if (ev.type === 'message' && ev.message.type === 'text') {
      const reply = await askChatGPT(ev.message.text);
      await axios.post(
        'https://api.line.me/v2/bot/message/reply',
        {
          replyToken: ev.replyToken,
          messages: [{ type: 'text', text: reply }]
        },
        { headers: { Authorization: `Bearer ${TOKEN}` } }
      ).catch(err => console.error('reply error:', err.response?.data || err.message));
    }
  }
  res.sendStatus(200);
}
