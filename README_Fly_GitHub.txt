GitHub → Fly.io Deployment Pack (Flask)
=======================================

Files:
- Dockerfile            : Runs Flask via gunicorn on Fly
- .dockerignore         : Keeps image small
- requirements.txt      : Minimal deps (add yours if needed)
- fly.toml              : SQLite + Volume (default)
- fly-postgres.toml     : Alternative if using Managed Postgres

Quick Steps (SQLite + Volume):
1) Commit these files to your GitHub repo (root).
2) On Fly.io Dashboard: Launch from GitHub, select your repo.
3) Set App Name. After app is created, edit 'fly.toml' in your repo:
   - Replace APP_NAME_PLACEHOLDER with your actual app name.
4) Create the volume (once):
   flyctl volumes create zoom_data --size 3 --region ams --app <your-app-name>
5) Set secrets:
   flyctl secrets set SECRET_KEY='change-this' --app <your-app-name>
6) Trigger a deploy:
   flyctl deploy --app <your-app-name>
   (Or push a new commit to main branch if CI is enabled)

Switch to Managed Postgres:
- Copy fly-postgres.toml to fly.toml
- Remove the mounts block.
- Create/attach Postgres and set DATABASE_URL secret:
  flyctl postgres create
  flyctl postgres attach --app <your-app-name>
  # or: flyctl secrets set DATABASE_URL='postgres://...'

Tips:
- If your Flask app entrypoint isn't app:app, edit the CMD in Dockerfile.
- Keep secrets out of git; use Fly secrets.
- Logs: flyctl logs --app <app>
