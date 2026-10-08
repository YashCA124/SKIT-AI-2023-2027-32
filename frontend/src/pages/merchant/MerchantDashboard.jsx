import { getRolePage } from '../../config/rolePages.js'
import UnavailablePage from '../UnavailablePage.jsx'

export default function MerchantDashboard({ pageId }) {
  return <UnavailablePage page={getRolePage('M', pageId)} />
}
