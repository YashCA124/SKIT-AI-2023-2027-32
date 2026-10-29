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

The live API includes booking creation, listing, and completion in
`routers/parking_api.py`. Ending a booking creates a pending `DEMO` payment
for the final time-based total; the owner can simulate success or failure with
`POST /api/payments/{payment_id}/simulate`. This mock flow does not connect to
a payment provider or collect payment credentials.
