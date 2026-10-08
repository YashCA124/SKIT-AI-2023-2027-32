import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AccountWorkspace from '../components/AccountWorkspace.jsx'
import ProtectedRoute from '../auth/ProtectedRoute.jsx'
import AdminDashboard from '../pages/admin/AdminDashboard.jsx'
import Login from '../pages/Login.jsx'
import MerchantDashboard from '../pages/merchant/MerchantDashboard.jsx'
import Register from '../pages/Register.jsx'
import UserDashboard from '../pages/user/UserDashboard.jsx'
import DevDemoRoute from './DevDemoRoute.jsx'

const DevPreviewPage = import.meta.env.DEV
  ? lazy(() => import('../pages/DevPreviewPage.jsx'))
  : null

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        {import.meta.env.DEV && (
          <Route path="/__preview" element={<Suspense fallback={null}><DevPreviewPage /></Suspense>} />
        )}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Navigate to="/account" replace />} />
          <Route path="/account" element={<AccountWorkspace />} />
          <Route element={<ProtectedRoute requiredRole="U" />}>
            <Route path="/user/parking" element={<AccountWorkspace><DevDemoRoute role="U" pageId="parking"><UserDashboard pageId="parking" /></DevDemoRoute></AccountWorkspace>} />
            <Route path="/user/bookings" element={<AccountWorkspace><DevDemoRoute role="U" pageId="bookings"><UserDashboard pageId="bookings" /></DevDemoRoute></AccountWorkspace>} />
            <Route path="/user/payments" element={<AccountWorkspace><DevDemoRoute role="U" pageId="payments"><UserDashboard pageId="payments" /></DevDemoRoute></AccountWorkspace>} />
          </Route>
          <Route element={<ProtectedRoute requiredRole="M" />}>
            <Route path="/merchant/locations" element={<AccountWorkspace><DevDemoRoute role="M" pageId="locations"><MerchantDashboard pageId="locations" /></DevDemoRoute></AccountWorkspace>} />
            <Route path="/merchant/spaces" element={<AccountWorkspace><DevDemoRoute role="M" pageId="spaces"><MerchantDashboard pageId="spaces" /></DevDemoRoute></AccountWorkspace>} />
          </Route>
          <Route element={<ProtectedRoute requiredRole="A" />}>
            <Route path="/admin/users" element={<AccountWorkspace><DevDemoRoute role="A" pageId="users"><AdminDashboard pageId="users" /></DevDemoRoute></AccountWorkspace>} />
            <Route path="/admin/lots" element={<AccountWorkspace><DevDemoRoute role="A" pageId="lots"><AdminDashboard pageId="lots" /></DevDemoRoute></AccountWorkspace>} />
          </Route>
          <Route path="*" element={<Navigate to="/account" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
