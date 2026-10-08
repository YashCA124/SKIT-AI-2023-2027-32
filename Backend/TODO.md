# Backend TODO

These APIs are not currently mounted by `Backend/main.py`; the router modules
are not part of the live API:

- Driver dashboard: `routers/dashboard/userdashboard/userdashboard.py`
- Merchant management: `routers/dashboard/merchantdashboard/merchantdashboard.py`,
  `addfloor.py`, `addspots.py`, `blockfloor.py`, `blocklot.py`, `blockspot.py`,
  `createlot.py`, `deletefloor.py`, `deletelot.py`, `deletespot.py`, and
  `updateprice.py`
- Administrator dashboard: `routers/dashboard/admindashboard/admindashboard.py`,
  `searchlot.py`, `searchuser.py`, `viewlots.py`, and `viewusers.py`

There is no booking API router/endpoint in `Backend/routers`. The existing
`ParkingBooking` model and the driver's dashboard source do not provide a
working booking API.
