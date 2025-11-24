import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx'
import './index.css'
import { AuthProvider } from './contexts/AuthContext.tsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Step 1: Place BrowserRouter at the top level */}
    <BrowserRouter>
      <AuthProvider> {/* 2. Wrap your app */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
