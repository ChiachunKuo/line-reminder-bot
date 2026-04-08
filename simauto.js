export function startSimulation() {
  const port = process.env.PORT || 3000;
  setTimeout(() => {
    setInterval(() => {
      const data = {
        temperature: 20 + Math.floor(Math.random() * 15),
        humidity: 50 + Math.floor(Math.random() * 50)
      };
      fetch(`http://127.0.0.1:${port}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
        .then(() => console.log('🛰️ mock', data))
        .catch(err => console.error('mock fail:', err.message));
    }, 60000);
  }, 5000);
}
