import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AccountOverview from '../components/AccountOverview.jsx'
import AccountWorkspace from '../components/AccountWorkspace.jsx'
import ProtectedRoute from '../auth/ProtectedRoute.jsx'
import AdminDashboard from '../pages/admin/AdminDashboard.jsx'
import Login from '../pages/Login.jsx'
import MerchantDashboard from '../pages/merchant/MerchantDashboard.jsx'
import Register from '../pages/Register.jsx'
import UserDashboard from '../pages/user/UserDashboard.jsx'

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/account" replace />} />
          <Route path="/account" element={<AccountWorkspace><AccountOverview /></AccountWorkspace>} />
          <Route element={<ProtectedRoute requiredRole="U" />}>
            <Route path="/user/parking" element={<AccountWorkspace><UserDashboard pageId="parking" /></AccountWorkspace>} />
            <Route path="/user/bookings" element={<AccountWorkspace><UserDashboard pageId="bookings" /></AccountWorkspace>} />
            <Route path="/user/payments" element={<AccountWorkspace><UserDashboard pageId="payments" /></AccountWorkspace>} />
          </Route>
          <Route element={<ProtectedRoute requiredRole="M" />}>
            <Route path="/merchant/locations" element={<AccountWorkspace><MerchantDashboard pageId="locations" /></AccountWorkspace>} />
            <Route path="/merchant/spaces" element={<AccountWorkspace><MerchantDashboard pageId="spaces" /></AccountWorkspace>} />
          </Route>
          <Route element={<ProtectedRoute requiredRole="A" />}>
            <Route path="/admin/users" element={<AccountWorkspace><AdminDashboard pageId="users" /></AccountWorkspace>} />
            <Route path="/admin/lots" element={<AccountWorkspace><AdminDashboard pageId="lots" /></AccountWorkspace>} />
          </Route>
          <Route path="*" element={<Navigate to="/account" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
