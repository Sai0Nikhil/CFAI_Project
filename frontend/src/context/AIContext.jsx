import { createContext, useContext, useState } from 'react'

const AIContext = createContext(null)

export const HOSPITALS = [
  {
    id: 'charite',
    name: 'Charité Campus Mitte',
    short: 'Charité · Berlin',
    flag: '🇩🇪',
    defaultStart: 'ENTRANCE_MAIN',
    defaultGoal:  'Node_302_ICU_Tower',
  },
  {
    id: 'aiims',
    name: 'AIIMS Mangalagiri',
    short: 'AIIMS · Andhra Pradesh',
    flag: '🇮🇳',
    defaultStart: 'MAIN_GATE',
    defaultGoal:  'NICU_F3',
  },
]

export function AIProvider({ children }) {
  const [enabled,  setEnabled]  = useState(false)
  const [provider, setProvider] = useState('claude')
  const [apiKey,   setApiKey]   = useState('')
  const [model,    setModel]    = useState('claude-3-haiku-20240307')
  const [hospital, setHospital] = useState('charite')   // ← NEW
  const [blockedNodes, setBlockedNodes] = useState([])   // list of blocked node IDs

  const toggleBlockedNode = (nodeId) => {
    setBlockedNodes(prev =>
      prev.includes(nodeId)
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    )
  }

  const clearBlockedNodes = () => setBlockedNodes([])

  const MODELS = {
    claude: [
      { v:'claude-3-haiku-20240307',    l:'Haiku 3 (fastest)' },
      { v:'claude-3-5-haiku-20241022',  l:'Haiku 3.5' },
      { v:'claude-3-5-sonnet-20241022', l:'Sonnet 3.5 (best)' },
    ],
    gemini: [
      { v:'gemini-1.5-flash', l:'Flash 1.5 (fastest)' },
      { v:'gemini-1.5-pro',   l:'Pro 1.5 (best)' },
    ],
  }

  const isReady = enabled && !!apiKey.trim()
  const hospitalInfo = HOSPITALS.find(h => h.id === hospital) || HOSPITALS[0]

  return (
    <AIContext.Provider value={{
      enabled, setEnabled,
      provider, setProvider,
      apiKey, setApiKey,
      model, setModel,
      MODELS, isReady,
      hospital, setHospital,   // ← NEW
      hospitalInfo,             // ← NEW
      HOSPITALS,                // ← NEW
      blockedNodes, toggleBlockedNode, clearBlockedNodes, // ← NEW
    }}>
      {children}
    </AIContext.Provider>
  )
}

export function useAI() {
  return useContext(AIContext)
}
