# Contributing

This guide covers how we pick up tasks, share code, and avoid stepping on each other's work. If you haven't yet, follow [Setup in the README](README.md#setup) first.

## Workflow

`main` only changes through pull requests.

1. **Pick a task.** First check [My Assigned Tasks](https://github.com/users/nghilbert/projects/6/views/5). If you have none, pick one from [Available Tasks](https://github.com/users/nghilbert/projects/6/views/9) and assign yourself. Set its Status to **In progress**. Its "Done when" list describes what to build.
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

## Generated files

Some files are generated with commands. Never write or edit them manually, and commit the generated files with the change that made them:

- **Migrations** (`skill_matchmaker/migrations/`): run `uv run python manage.py makemigrations` after changing a model. Never edit or delete a migration that's already on `main`, because everyone may have already migrated it to their database. If two migrations on `main` conflict, fix it with `makemigrations --merge`.
- **`uv.lock` and the dependencies in `pyproject.toml`**: run `uv add <package>` or `uv remove <package>`.

## Working at the same time

Several tasks run at once, so branches sometimes touch the same files.

1. **Before opening a PR, update your branch:**

   ```sh
   git fetch origin
   git merge origin/main
   uv sync
   uv run python manage.py migrate
   ```

2. **Migrations:** if `migrate` says "Conflicting migrations detected" or `InconsistentMigrationHistory`, your migrations or database are out of date with `main`. Delete `db.sqlite3` and any migration you made that isn't on `main` yet, then run:

   ```sh
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   uv run python manage.py createsuperuser
   ```

3. **Small conflicts:** if `urls.py`, `admin.py`, `models/__init__.py`, or a template conflicts because two people added lines in the same spot, you usually want to keep both changes.
