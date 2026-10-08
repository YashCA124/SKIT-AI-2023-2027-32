import { lazy, Suspense } from 'react'
import useAuth from '../auth/useAuth.js'

const DEMO_PAGES = import.meta.env.DEV
  ? {
    U: lazy(() => import('../pages/user/DevUserDemoPage.jsx')),
    M: lazy(() => import('../pages/merchant/DevMerchantDemoPage.jsx')),
    A: lazy(() => import('../pages/admin/DevAdminDemoPage.jsx')),
  }
  : null

export default function DevDemoRoute({ role, pageId, children }) {
  const { session } = useAuth()
  const DemoPage = DEMO_PAGES?.[role]

  if (!import.meta.env.DEV || !session?.isPreview || session.user.role !== role || !DemoPage) {
    return children
  }

  return (
    <Suspense fallback={<p role="status">Loading presentation demo…</p>}>
      <DemoPage pageId={pageId} />
    </Suspense>
  )
}
