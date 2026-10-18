# Contributing

This guide covers how we pick up tasks, share code, and avoid stepping on each other's work. If you haven't yet, follow [Setup in the README](README.md#setup) first.

## Workflow

`main` only changes through pull requests.

1. **Pick a task.** First check [My Assigned Tasks](https://github.com/users/nghilbert/projects/6/views/5). If you have none, pick one from [Available Tasks](https://github.com/users/nghilbert/projects/6/views/9) and assign yourself. Set its Status to **In progress**. Its "Done when" list says exactly what to build.
2. **Create a branch from the task's issue.** In the issue's sidebar under **Development**, click **Create a branch**, keep the suggested name, and click **Create branch**. Then get it locally:

   ```sh
   git fetch origin
   git switch <branch-name>
   uv sync
   uv run python manage.py migrate
   ```

   `uv sync` installs any new project dependencies, and `migrate` updates your database to match the latest models.

3. **Test it by hand** with `uv run python manage.py runserver`, checking each item in the task's "Done when" list.
4. **Push and open a PR** when it's done. The PR is linked to the task automatically, so merging it closes the task and moves it to Done.

Stuck or unsure? Ask in a comment on the task's issue so the whole team can see the answer.

## Working at the same time

Several tasks run at once, so branches sometimes touch the same files.

1. **Before opening a PR, update your branch:**

   ```sh
   git fetch origin
   git merge origin/main
   uv sync
   uv run python manage.py migrate
   ```

2. **Migrations:** if `migrate` says "Conflicting migrations detected", `main` got a new migration since you started. Delete the migration file you made, then make it again so yours comes after theirs. Your local database still has your old migration applied, so delete `db.sqlite3` and rebuild it too (you'll need to run `createsuperuser` again).

   ```sh
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   ```

   **Never edit or delete someone else's migration.** Once it's on `main`, everyone's database has already run it, so changing it breaks their databases.

3. **Small conflicts:** if `urls.py`, `admin.py`, `models/__init__.py`, or a template conflicts because two people added lines in the same spot, keep both changes.
