import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';
import { askChatGPT } from './chatgpt.js';
import { pushMessage, handleWebhook } from './linebot.js';

const app = express();
const PORT = process.env.PORT || 3000;
const __dirname = path.dirname(fileURLToPath(import.meta.url));

app.use(express.json());
app.use(express.static('public'));

const store = [];

app.post('/upload', async (req, res) => {
  const { temperature, humidity } = req.body;
  const rec = {
    temperature,
    humidity,
    time: new Date().toLocaleTimeString('zh-TW', { hour12: false })
  };
  store.push(rec);
  if (store.length > 100) store.shift();
  console.log('sensor:', rec);

  const prompt = `目前數據：溫度${temperature}°C，濕度${humidity}%。
請用兩句繁體中文給農夫建議。`;
  const text = await askChatGPT(prompt);
  pushMessage(text);
  res.json({ status: 'ok' });
});

app.get('/data', (_, res) => res.json(store));
app.get('/dashboard', (_, res) => res.sendFile(path.join(__dirname, 'public/dashboard.html')));
app.post('/callback', handleWebhook);

app.listen(PORT, () => {
  console.log(`🚀 server on http://localhost:${PORT}`);
  import('./simauto.js').then(m => m.startSimulation());
});
