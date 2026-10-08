import { getRolePage } from '../../config/rolePages.js'
import UnavailablePage from '../UnavailablePage.jsx'

export default function UserDashboard({ pageId }) {
  return <UnavailablePage page={getRolePage('U', pageId)} />
}
