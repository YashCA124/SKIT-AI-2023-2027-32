const PARKING_LOTS = [
  { id: 1, name: 'Central Plaza Parking', address: '14 MI Road', city: 'Jaipur', rate: 40, available: 18, total: 80, status: 'Open', isListed: true, floor: 3 },
  { id: 2, name: 'Pink City Hub', address: 'Station Road', city: 'Jaipur', rate: 30, available: 7, total: 45, status: 'Open', isListed: true, floor: 2 },
  { id: 3, name: 'Bapu Bazaar Garage', address: 'Bapu Bazaar', city: 'Jaipur', rate: 25, available: 0, total: 32, status: 'Full', isListed: true, floor: 1 },
  { id: 4, name: 'C-Scheme Secure Park', address: 'Ashok Marg', city: 'Jaipur', rate: 50, available: 26, total: 60, status: 'Open', isListed: true, floor: 4 },
]

const USERS = [
  { id: 'DEMO-U1048', name: 'Aarav Sharma', email: 'aarav@example.test', role: 'Driver', status: 'Active' },
  { id: 'DEMO-M0214', name: 'Priya Mehta', email: 'priya@example.test', role: 'Merchant', status: 'Active' },
  { id: 'DEMO-U1032', name: 'Isha Patel', email: 'isha@example.test', role: 'Driver', status: 'Active' },
  { id: 'DEMO-M0208', name: 'Rohan Kapoor', email: 'rohan@example.test', role: 'Merchant', status: 'Pending' },
  { id: 'DEMO-U1011', name: 'Kabir Singh', email: 'kabir@example.test', role: 'Driver', status: 'Active' },
]

export function createDemoData() {
  return {
    lots: PARKING_LOTS.map((lot) => ({ ...lot })),
    users: USERS.map((user) => ({ ...user })),
    bookings: [
      { id: 'DEMO-B2048', lotId: 1, lotName: 'Central Plaza Parking', spot: 'B-14', time: 'Today, 10:30 AM', until: 'Today, 1:30 PM', amount: 120, status: 'Active' },
      { id: 'DEMO-B1982', lotId: 2, lotName: 'Pink City Hub', spot: 'A-07', time: 'Yesterday, 4:00 PM', until: 'Yesterday, 6:00 PM', amount: 60, status: 'Completed' },
    ],
    payments: [
      { id: 'DEMO-T8871', date: '08 Oct 2026', description: 'Central Plaza Parking', method: 'UPI (sample)', amount: 120, status: 'Paid' },
      { id: 'DEMO-T8814', date: '07 Oct 2026', description: 'Pink City Hub', method: 'Card (sample)', amount: 60, status: 'Paid' },
    ],
    nextBookingNumber: 1,
  }
}
