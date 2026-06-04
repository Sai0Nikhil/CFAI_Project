import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/global.css'
import { AIProvider } from './context/AIContext.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AIProvider>
      <App />
    </AIProvider>
  </React.StrictMode>
)
