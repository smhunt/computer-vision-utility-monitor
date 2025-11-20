import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { Settings } from './pages/Settings'
import { CameraPreview } from './pages/CameraPreview'
import { MeterDetail } from './pages/MeterDetail'
import { ConfigEditor } from './pages/ConfigEditor'
import { ThemeProvider } from './contexts/ThemeContext'

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/config" element={<ConfigEditor />} />
          <Route path="/camera/:meterType" element={<CameraPreview />} />
          <Route path="/meter/:meterName" element={<MeterDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
