import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './theme/theme.css'
import CloudBackdrop from './theme/CloudBackdrop.jsx'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <CloudBackdrop />
    <App />
  </StrictMode>,
)
