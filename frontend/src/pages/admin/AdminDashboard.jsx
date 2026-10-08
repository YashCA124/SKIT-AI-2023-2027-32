import { getRolePage } from '../../config/rolePages.js'
import UnavailablePage from '../UnavailablePage.jsx'

export default function AdminDashboard({ pageId }) {
  return <UnavailablePage page={getRolePage('A', pageId)} />
}
