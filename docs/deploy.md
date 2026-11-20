# Deploying the server by hand

<!-- Writing rules: docs/writing/core_rules.md. -->

This is the checklist for putting a commit of the server on the live site. It is written from the
procedure that 72 entries of [`frontend/docs/deploy_log.md`](../frontend/docs/deploy_log.md) settled
into, with what changed on 2026-11-18 added. The same steps are meant to become the deploy job in
`.github/workflows/ci.yml`.

**Status on 2026-11-19: used once.** The server was deployed from this page at `087812dd` the
same day (the entry is in the deploy log). Every command below ran as written, with one change
made here afterwards: a step for a database dump before the migration, which the first version
lacked. One thing is still unverified: the roll-back command has not been needed.

A coding agent does none of this without the owner's word for that deploy.

## Before the day of the deploy

1. **CI is green on the commit.** For a commit on a feature branch that is the short run only.
   Open a pull request to `main` to get the full run: integration tests, slow tests, and the image
   build with its start-up check.
2. **The paid provider check has been run** (`poetry run pytest -m contract`), with the owner's
   agreement. The key check and the building of clients on a player's key changed on 2026-11-18,
   and no free test sends a real request through them.
3. **The pending migrations are known.** Step 5 reads which migration the live database is on.

## The deploy

Each step says what it protects against.

1. **Check that nothing is being played.** No room waiting and no game running. A restart stops
   running games. They are recovered afterwards, but a game on a player's key then waits until
   the player enters the key again. A deploy that finds a game running waits for it to finish.

2. **Check the disk.** `df -h /home`. A build needs several GB, and a full disk has broken
   tracing before.

3. **Build from a clean checkout of the commit**, so that uncommitted work in the working folder
   stays out of the image.

   ```bash
   SHA=$(git rev-parse --short=8 HEAD)
   git worktree add --detach ../ww-deploy "$SHA"
   cd ../ww-deploy
   docker build -t werewolf-agent-sim-wolf-server:"$SHA" --build-arg GIT_COMMIT="$SHA" .
   ```

   New on 2026-11-18: the build installs from `poetry.lock`, so it downloads packages from PyPI
   in its first stage, and `.dockerignore` limits what is sent to the build. Both files must be
   in the commit, which they are from `3793f6d2` on.

4. **Pre-flight in the new image, with the production settings, before anything is swapped.**
   The server must import and start. This is the step that would have caught the three
   undeclared packages found on 2026-11-18.

   ```bash
   docker run --rm --env-file .env.production \
     -v ~/.config/gcloud/application_default_credentials.json:/home/werewolf/.config/gcloud/application_default_credentials.json:ro \
     werewolf-agent-sim-wolf-server:"$SHA" python -c "import server.app"
   ```

5. **Read which migration the database is on, and take a dump before changing it.** No backup
   runs on a schedule, so this dump is the only copy.

   ```bash
   docker run --rm --network werewolf --env-file .env.production \
     werewolf-agent-sim-wolf-server:"$SHA" alembic current
   docker run --rm --network werewolf --env-file .env.production pgvector/pgvector:pg17 \
     sh -c 'pg_dump -Fc "$WW_POSTGRES_DSN"' > ~/backups/werewolf-pre-NNNN-$(date -u +%Y%m%d-%H%M).dump
   ```

   The `pg_dump` in that image must be the database's major version or newer (17 on
   2026-11-19). `pg_restore -l` on the file lists what it holds.

5b. **Run the migrations from inside the new image, on the `werewolf` network.** The host cannot
   resolve the database's name, and the old image does not hold the new migration files.
  

   ```bash
   docker run --rm --network werewolf --env-file .env.production \
     werewolf-agent-sim-wolf-server:"$SHA" alembic upgrade head
   ```

   A migration is the one step that cannot be undone by swapping the image back. Read what the
   pending migrations do before running them. Additive ones (a new table, a new column that may
   be empty) leave the old server working, which is what makes step 8 possible.

6. **Keep the image that is running as `:prev`, then point `:latest` at the new one.**
  

   ```bash
   docker tag werewolf-agent-sim-wolf-server:latest werewolf-agent-sim-wolf-server:prev
   docker tag werewolf-agent-sim-wolf-server:"$SHA" werewolf-agent-sim-wolf-server:latest
   ```

7. **Swap the server container only.** This form of the command is the one the deploy log
   records.

   ```bash
   cd /home/ubuntu/projects/werewolf-agent-sim
   docker compose up -d --no-build --no-deps wolf-server
   ```

8. **Smoke test, and roll back if it fails.**

   - `/api/health`, `/api/models` and `/api/replays` answer 200;
   - the site's pages load, and one replay plays in the browser;
   - the server's log has no error;
   - when the release changed how models, keys or lessons are handled: one house game is started
     and played for a few turns, one game is started on a player's key, and one memory-on game is
     started. These cost model calls, so they are the owner's to start or to approve.

   To roll back: `docker tag werewolf-agent-sim-wolf-server:prev werewolf-agent-sim-wolf-server:latest`,
   then step 7 again.

9. **Record it** in `frontend/docs/deploy_log.md`: the commit, what `:prev` now is, what was
   deployed, the smoke test's result, and the disk space left.

10. **Remove the clean checkout:** `git worktree remove ../ww-deploy`.

## What becomes the deploy job later

Steps 3 to 8, run on the server over SSH after the tests pass on `main`. Three of them need a
decision before they can run unattended:

| Step | What a job cannot decide alone |
|---|---|
| 1. Nothing is being played | Whether to wait for a running game, refuse, or deploy anyway. The server would need a way to say "no game is live" |
| 5. Migrations | Whether every migration is safe to run without a person reading it first |
| 8. Smoke test | Which checks a script can make (the three API calls) and which stay with a person (a game in the browser) |

GitHub would hold only what lets it log in to the server: the host, the user, the port and an SSH
key. The provider keys and the database password stay in `.env.production` on the server.
