# Parkwise frontend

This directory contains the web client for Parkwise, a parking application.
The interface is built with **React 19** and **Vite**. It currently focuses on
user registration and sign-in, a basic signed-in account page, and backend
service health/readiness. It is a frontend client: account authentication,
registration, location storage, and token validation are handled by the
FastAPI backend.

## Table of contents

- [Frontend at a glance](#frontend-at-a-glance)
- [Screens and user journeys](#screens-and-user-journeys)
- [How the frontend is organized](#how-the-frontend-is-organized)
- [Backend API integration](#backend-api-integration)
- [Session and error handling](#session-and-error-handling)
- [Run locally](#run-locally)
- [Configure the API address](#configure-the-api-address)
- [Build and serve](#build-and-serve)
- [Accessibility and responsive layout](#accessibility-and-responsive-layout)
- [Current scope and limitations](#current-scope-and-limitations)
- [Commands](#commands)

## Frontend at a glance

| Area | Current implementation |
| --- | --- |
| UI framework | React 19 |
| Build tool and dev server | Vite |
| Language | JavaScript with JSX |
| Styling | Handwritten CSS; no component or CSS framework |
| Routing | One React application with sign-in, registration, and dashboard views; no client-side router |
| API communication | Browser `fetch` calls to FastAPI |
| Client-side session storage | `sessionStorage` for access token, refresh token, and the small account object returned at sign-in |
| Main entry point | `src/main.jsx` |
| Main application | `src/App.jsx` |

The app does not currently use a global state library, form library, or
third-party UI package. React state and browser APIs are used directly.

## Screens and user journeys

### Sign-in

The initial screen contains an email and password form. The browser performs
basic required-field and email-format checks, then sends the credentials to
`POST /auth/userlogin`.

When the API succeeds, the frontend:

1. Reads the account (`id`, `name`, and `role`) and access/refresh tokens from
   the response.
2. Displays a signed-in welcome and account summary.
3. Stores the tokens and returned account details in the current tab's
   `sessionStorage`.

If the API rejects the credentials or cannot be reached, the API error is
shown in the form rather than silently ignored.

### Registration

The create-account screen asks for:

- Full name
- Email address
- Phone number
- Password
- City
- State
- Two-letter country code
- Optional permission to use the browser's current location

The form sends the fields to `POST /auth/registration`. The server's schema
marks some address fields optional, but the frontend requires city, state,
and country because the backend uses that address to determine an approximate
location when the user does not share device coordinates.

If the user enables location sharing, the browser requests geolocation
permission. If permission is denied, unsupported, or times out, the form shows
an error and does not send a registration request with missing coordinates.
Without device location, the backend geocodes the city/state/country.

After successful registration, the frontend returns to sign-in and displays
the API's success message. It does not automatically sign the new user in.

### Signed-in account page

The current page shows:

- The user's name in the welcome message.
- Account name, account ID, and account type returned by the sign-in API.
- Service health and readiness.
- A sign-out action.

The page intentionally does not show parking availability, parking lots, or
bookings. Although a user-dashboard router exists in the backend source tree,
it is not registered by the current FastAPI `main.py`, so the frontend has no
working API endpoint for those details.

### Service status

The service panel is available both before and after sign-in. It calls
`GET /health` and `GET /ready`, and shows:

- Health status, service name, and environment from `/health`.
- Database configuration status from `/ready`.
- The time of the most recent check.
- A button to retry both checks.

“Unavailable” means a health/readiness request failed; it does not necessarily
mean the frontend itself is unavailable. For example, an HTTP 404 usually
means the request reached a server that does not serve that API path, or that
the API URL/proxy is not configured for that environment.

## How the frontend is organized

### Application startup

`index.html` provides the `#root` mount point and loads `src/main.jsx`.
`src/main.jsx` creates the React root, enables React `StrictMode`, imports the
global stylesheet, and renders `App`.

### Main application (`src/App.jsx`)

The app currently keeps the main screens in one file:

- **`Brand`** renders the Parkwise header brand.
- **`Alert`** renders accessible error/status messages.
- **`LoginForm`** renders the sign-in form and registration link.
- **`RegistrationForm`** renders account fields and optional geolocation
  consent.
- **`ServiceStatus`** renders health and readiness information.
- **`App`** owns view, session, loading, notice, and service-check state and
  connects the forms to the API.

There is no URL-based page router. The app switches between the login,
registration, loading, and signed-in dashboard views with React state.

### API helpers and state

At the top of `App.jsx`, `API_BASE_URL` chooses the API origin. `apiRequest`
uses `fetch`, sets JSON headers when needed, and passes responses to
`readResponse`. The response helper extracts FastAPI `detail` messages,
including validation errors, and produces a visible error when the response
is not successful or cannot be read.

The `App` component holds the shared state: selected view, signed-in session,
session restoration, pending form/logout action, user notices, health/readiness
results, and the last check time. The forms own only their local input state,
such as whether location permission was opted into.

### Styles (`src/App.css` and `src/index.css`)

`src/index.css` applies global box sizing, page sizing, and base typography.
`src/App.css` contains the app theme, auth and dashboard layouts, form styling,
service-status states, notices, and responsive breakpoints. On smaller screens
the two-column sign-in layout and dashboard stack into one column.

### Vite and project files

| File | Responsibility |
| --- | --- |
| `index.html` | Browser document shell and React mount point |
| `src/main.jsx` | React bootstrap and global stylesheet import |
| `src/App.jsx` | Screens, application state, API calls, session lifecycle |
| `src/App.css` | Component and responsive layout styles |
| `src/index.css` | Global styles |
| `vite.config.js` | React plugin and local development API proxy |
| `package.json` | Dependencies and npm scripts |
| `package-lock.json` | Locked JavaScript dependency versions |
| `Dockerfile` | Production build and Vite preview container |
| `.env.example` | Example API/proxy settings |

## Backend API integration

All paths below are relative to the configured API origin. Request bodies are
JSON unless noted otherwise. Authenticated requests use an
`Authorization: Bearer <token>` header.

| Method and path | Used for | Frontend behavior |
| --- | --- | --- |
| `POST /auth/userlogin` | Sign in with email and password | Stores returned account details and tokens |
| `POST /auth/registration` | Create an account | Displays success and returns to sign-in |
| `POST /auth/logoutcurrent` | Revoke the current access token | Called during sign-out with the access token |
| `POST /auth/logoutrefresh` | Revoke the refresh token | Called during sign-out with the refresh token |
| `GET /tokenauth/protected` | Validate the access token | Checks a saved session when the app loads |
| `POST /tokenauth/refresh` | Exchange a refresh token for an access token | Renews an expired access token |
| `GET /health` | Read API health/service information | Populates the health section |
| `GET /ready` | Read API readiness/database configuration | Populates the readiness section |

The frontend expects the login response to contain `access_token`,
`refresh_token`, and a `user` with `id`, `name`, and `role`. The registration
response is expected to have a success message. The refresh response contains
`access_token`.

The login payload includes `email` and `password`. Registration sends `name`,
`email`, `phone_no`, `password`, `city`, `state`, `country`,
`location_permission_granted`, and—when permission is granted—`latitude` and
`longitude`.

## Session and error handling

- Tokens are kept in `sessionStorage`, not long-lived `localStorage`.
- On startup, the app validates the stored access token. If it is expired, it
  attempts to exchange the refresh token, then verifies the new access token.
- An expired/rejected refresh token removes the stored session and asks the
  user to sign in again.
- If the backend is temporarily unreachable during restoration, the app keeps
  the saved account visible and reports that verification/refresh failed so a
  temporary network problem is not mistaken for a confirmed logout.
- Sign-out calls both revoke endpoints. If either request fails for a reason
  other than an already-rejected/expired token, the app shows a sign-out error
  and retains the local session so the user can retry.
- API validation and network errors are shown in the interface.

Client storage is not a substitute for server-side security. The backend is
responsible for validating tokens and authorizing protected actions.

## Run locally

### Prerequisites

- Node.js compatible with the versions used by this Vite project.
- npm.
- The FastAPI backend running at `http://localhost:8000` (the default proxy
  target). The backend may also require its database and Redis services.

### Start the development server

From the `frontend/` directory:

```sh
npm install
npm run dev
```

Open the local address Vite prints, usually `http://localhost:5173`.
Keep the terminal running while using the app.

In development, Vite proxies `/auth`, `/tokenauth`, `/health`, and `/ready` to
FastAPI at `http://localhost:8000`. This means the browser sends requests to
the Vite origin and does not need cross-origin CORS permission for the local
setup. The backend still needs to be running for sign-in, registration, and
real health/readiness results.

## Configure the API address

### Change the development proxy target

Create `frontend/.env.local` and set the backend origin:

```dotenv
VITE_API_PROXY_TARGET=http://localhost:8000
```

Change the value if FastAPI uses a different host or port. Restart Vite after
editing environment variables. `VITE_API_PROXY_TARGET` is used by the Vite
development server.

### Call the API directly

To bypass the development proxy, set `VITE_API_BASE_URL`:

```dotenv
VITE_API_BASE_URL=https://api.example.com
```

When this variable is set, the frontend sends requests directly to that
origin. The backend must allow the browser frontend's origin through CORS.
When it is not set, the browser client defaults to `window.location.origin`;
in development, Vite's proxy forwards API paths to FastAPI.

Vite exposes `VITE_` variables to browser code. Do not put passwords,
private keys, or other server secrets in frontend environment variables.

## Build and serve

Create a production bundle:

```sh
npm run build
```

Vite writes the static bundle to `dist/`. To serve the built frontend locally:

```sh
npm run preview
```

The Vite development proxy only runs in development; it is not included in
`dist/` or the frontend Docker image. A deployment must provide a reachable
API origin or configure a reverse proxy to route API paths to FastAPI. For a
direct API origin, set `VITE_API_BASE_URL` at **build time**, because Vite
embeds frontend environment values into the generated JavaScript bundle.

The frontend `Dockerfile` builds the app and serves the bundle with Vite's
preview server on port `5173`. It does not start the backend. The root
`docker-compose.yml` also defines the backend, database, Redis, and frontend
services; check the API routing and environment settings for the target
deployment before relying on authentication through the composed frontend.

## Accessibility and responsive layout

The forms use native labels, input types, required-field validation, and
autocomplete hints. Buttons have visible focus styles. API errors use an
alert role, status updates use a status role, and service state changes are
announced with a live region. The registration form describes the country-code
format and location behavior. The layout adapts to narrow screens by stacking
the auth and dashboard columns.

## Current scope and limitations

- This is a user-facing auth frontend, not a complete parking management UI.
- There is no Google sign-in or other third-party identity flow.
- There are no user-facing screens for parking search, availability, booking,
  payment, or booking history.
- The currently mounted backend does not provide the user-dashboard endpoint
  needed to populate real user bookings.
- The app has no client-side router; reloading returns to the app's initial
  view and then restores a valid tab session if one exists.
- The service panel depends on the backend implementing `/health` and `/ready`
  at the configured origin or proxy paths.

## Commands

Run these commands from `frontend/`:

| Command | Purpose |
| --- | --- |
| `npm install` | Install dependencies |
| `npm run dev` | Start Vite in development mode |
| `npm run lint` | Run ESLint |
| `npm run build` | Build the production bundle in `dist/` |
| `npm run preview` | Preview the production bundle locally |

## Explaining the frontend in a presentation

> The Parkwise frontend is a React application built with Vite. Its current
> user flow lets a person register with their contact and location details,
> sign in against the FastAPI backend, and view their returned account
> information. Access and refresh tokens are stored only for the browser tab's
> session, checked and refreshed through the backend, and revoked on sign-out.
> The app also displays live API health and database readiness. The frontend
> does not invent parking or booking information; those screens can be added
> when the backend exposes the corresponding user APIs.
