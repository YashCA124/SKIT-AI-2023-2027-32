export const ROLE_DETAILS = {
  U: { label: 'Driver', title: 'Driver workspace' },
  M: { label: 'Merchant', title: 'Merchant workspace' },
  A: { label: 'Administrator', title: 'Administrator workspace' },
}

export const ROLE_PAGES = {
  U: [
    { id: 'parking', path: '/user/parking', label: 'Find parking', icon: '⌖', title: 'Parking search', description: 'Search parking locations and availability.' },
    { id: 'bookings', path: '/user/bookings', label: 'My bookings', icon: '▤', title: 'My bookings', description: 'View and manage your parking reservations.' },
    { id: 'payments', path: '/user/payments', label: 'Payments', icon: '₹', title: 'Payments', description: 'View payment methods and transaction history.' },
  ],
  M: [
    { id: 'locations', path: '/merchant/locations', label: 'My locations', icon: '⌖', title: 'Parking locations', description: 'Manage your parking locations.' },
    { id: 'spaces', path: '/merchant/spaces', label: 'Spaces and rates', icon: '▦', title: 'Spaces and rates', description: 'Manage floors, spaces, and pricing.' },
  ],
  A: [
    { id: 'users', path: '/admin/users', label: 'Users', icon: '♙', title: 'User management', description: 'Review and manage platform accounts.' },
    { id: 'lots', path: '/admin/lots', label: 'Parking lots', icon: '▦', title: 'Parking lot management', description: 'Review parking locations across the platform.' },
  ],
}

export function getRoleDetails(role) {
  return ROLE_DETAILS[role] || { label: role || 'Account', title: 'Account workspace' }
}

export function getRolePage(role, pageId) {
  return ROLE_PAGES[role]?.find((page) => page.id === pageId)
}
