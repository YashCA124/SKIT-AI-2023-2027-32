import { AuthProvider } from './auth/AuthContext.jsx'
import AppRoutes from './routes/AppRoutes.jsx'
import { ThemeProvider } from './theme/ThemeContext.jsx'

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <AppRoutes />
      </ThemeProvider>
    </AuthProvider>
  )
}
