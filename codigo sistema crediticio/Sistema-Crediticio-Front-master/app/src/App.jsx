import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout.jsx'
import { Upload } from './pages/Upload.jsx'
import { Lookup } from './pages/Lookup.jsx'
import { Health } from './pages/Health.jsx'
import { ROUTES } from './config/constants.js'

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path={ROUTES.UPLOAD} element={<Upload />} />
          <Route path={ROUTES.LOOKUP} element={<Lookup />} />
          <Route path={ROUTES.HEALTH} element={<Health />} />
          <Route path="*" element={<Navigate to={ROUTES.UPLOAD} replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App
