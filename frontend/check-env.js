console.log('Environment check:');
console.log('VITE_API_URL:', process.env.VITE_API_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('All VITE_ vars:', Object.keys(process.env).filter(key => key.startsWith('VITE_')));