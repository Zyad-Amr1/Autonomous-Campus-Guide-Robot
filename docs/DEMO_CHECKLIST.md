# ECU Guidance Robot Demo Checklist

## Run The App

```bash
python -m apps.public_app
```

For headless test runs, the test suite sets `QT_QPA_PLATFORM=offscreen` where needed.

## Required Local Setup

- Install project dependencies from `requirements.txt`.
- Initialize or provide the local SQLite database used by the app.
- Keep map assets available under `assets/maps/`.
- For Gemini-backed chatbot responses, set `GEMINI_API_KEY` in `.env`.
- Do not put API keys or private credentials in screenshots, commits, or demo notes.

## Before The Demo

- Confirm the app launches without import errors.
- Confirm the language screen appears.
- Choose English.
- Confirm the home screen shows the three main choices:
  - University Information
  - Ask Chatbot
  - Campus Map

## Chatbot Demo Flow

Open Ask Chatbot and try:

- `hello`
- `Who are the professors?`
- `talk about cafeteria`
- `Tell me about engineering`
- `What is Messi?`

Expected behavior:

- Greeting questions should answer politely or at least not crash.
- ECU-related questions should use ECU records, ECU website context, or campus landmark knowledge.
- Unrelated questions should say there is not enough ECU context.
- The UI should remain responsive.
- The source/status indicator should appear when an answer is shown.

## Campus Map Demo Flow

Open Campus Map and verify:

- The campus map image appears.
- Search for `Building A`.
- Select `Building A` as the start and `Cafeteria` as the destination.
- Click Find Route.
- Confirm the route appears and stays aligned with the map.
- Confirm route shadow and walker shadow are subtle.
- Confirm the "You are here" pulse appears at the route start.
- Click Start Walk.
- Confirm the walker dot moves without freezing.
- Click Pause Walk.
- Click Reset Walk.
- Click Reset Route and confirm the route and start pulse disappear.
- Use zoom in, zoom out, and reset view.
- Confirm markers and route remain aligned after zoom.
- Click a static landmark and confirm the info panel updates.
- Click a database room marker if visible and confirm the info panel updates.
- Confirm no popup windows appear and no crash occurs.

## Protected Data Demo Flow

- Confirm the Protected Data button exists.
- Open the password screen.
- Enter an incorrect password and confirm a friendly error appears.
- Enter `admin123` and confirm the Data screen opens.

## Known Limitations

- Chatbot answers are limited to ECU database records, ECU website content, and campus landmark knowledge.
- If relevant ECU data is missing, the chatbot may say there is not enough ECU information.
- Campus map routing is a kiosk campus simulation, not real GPS navigation.
- Website fallback requires an internet connection.
- Gemini-backed answers require `GEMINI_API_KEY`.
- Do not demo unfinished legacy public shell shortcuts or old quick-ask tile tests unless they have been intentionally restored.

## Do Not Demo If Unfinished

- Any feature that requires missing private credentials.
- Any admin workflow unrelated to the professor/demo story unless it has been checked immediately before the demo.
- Legacy home shortcuts or quick-ask chips if they are not visible in the current UI.
