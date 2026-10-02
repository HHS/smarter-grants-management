# Overview
Our backend setup allows for creating scripts that we can
easily run in ECS with the same  code that we run in our API.

Note that while we often call these "ECS Tasks", they're just scripts that we run.
You can fully develop, test, and run these scripts locally
the same as any other code we have. These scripts are just also
very easy to run, and schedule to in our environments by running on ECS.

We rely on Flask, which runs our API to run our code
as a [CLI command](https://flask.palletsprojects.com/en/stable/testing/#running-commands-with-the-cli-runner).
Running it in this way means that the setup we do in
our [create_app](/api/src/app.py) function is available
when running a script as well which includes setting up
the DB session, logging, and any other general app functionality. 

## Example

```python
from enum import StrEnum
from src.adapters import db
from src.adapters.db import flask_db
from src.constants.lookup_constants import JobType
from src.task.ecs_background_task import ecs_background_task
from src.task.task import Task
from src.task.task_blueprint import task_blueprint

@task_blueprint.cli.command(
    "example-task",
    help="An example task for demo purposes",
)
@flask_db.with_db_session()
@ecs_background_task(JobType.EXAMPLE_TASK)
def run_example_task(db_session: db.Session) -> None:
    ExampleTask(db_session).run()

class ExampleTask(Task):
    
    class Metrics(StrEnum):
        EXAMPLE_COUNT = "example_count"

    def run_task(self) -> None:
        with self.db_session.begin():
            self.process()

    def process(self) -> None:
        # Put the meaningful script logic here.
        self.increment(self.Metrics.EXAMPLE_COUNT)
```

Let's go through this piece by piece. The entrypoint to your logic
is the function defined at the top which has several decorators.

The `@task_blueprint.cli.command` decorator adds this CLI command
to the task_blueprint which is registered with the application. These
are the same blueprints that we use to group routes, although this one
we don't have any routes.

> [!NOTE]
> In order for Flask to know about your new CLI command, it has to be
> imported. To do that, add an import to the __init__.py file in the same
> folder as the task_blueprint (there should be a few already there).

You can specify CLI parameters as well if your scenario needs it. Flask
uses [click](https://click.palletsprojects.com/en/stable/) to define these.

> [!NOTE]
> CLI parameters should never be PII or otherwise secret information.
> Our logging always writes the exact command that started up an application out
> which would include all CLI parameters.

---

`@flask_db.with_db_session()` injects the DB session as the first parameter
in the function you create. This works identically to how it does in our API
endpoints.

---

`@ecs_background_task(JobType.EXAMPLE_TASK)` adds metadata to your task logs
and is required to get logging to fully work. When you make a new task, add
a new job type to the enum, and use that here. The metadata added includes:
* Automatically tagging ALL logs with the job type
* Automatically adding timing metrics to the job
* Giving each job a unique ID for each run
* Add information about the ECS task it is running in (if running non-locally)

---

Within the function itself you can technically run whatever you want, but
it is recommended that you extend from our [Task](/api/src/task/task.py) class
to add your implementation. See [Task Class](#task-class) for further details.

## Running a CLI command

### Locally
Locally, to run a CLI command, you can use our make command to help run it:
```shell
make cmd args="task example-task"
```

This will run something like this:
```shell
docker compose run --rm grants-management-api uv run flask task example-task
```

### Non-locally (Manually)
This requires you have AWS access and have an active AWS session in your terminal.

This uses the [run-command](/bin/run-command) shell script to call AWS and start an
ECS task with your script. Your code has to have been deployed to the environment
you are trying to run in order for it to work.

To run the same command above against dev, you could run:
```shell
bin/run-command api dev '["flask", "task", "example-task"]'
```

> [!NOTE]
> Be very careful writing and running these commands.
> One common issue I've seen is that engineers write these commands
> in non-code editing software and the quotes get replaced with smart quotes.
> AWS will get very confused by those and give errors that do not make sense.
> Do not write or copy commands from Google Docs, Word or any other similar
> text editing software.

### Non-locally (Scheduled)
If you want to setup this command to run on a regular cadence, you
can instead add to our [scheduled_jobs.tf](/infra/api/app-config/env-config/scheduled_jobs.tf)
configuration. This will allow you to define an ECS task that should
spin up at some regular cadence using AWS EventBridge & Step Functions.

```tf
    example-job = {
      task_command = ["flask", "task", "example-task"]
      # Every hour at the top of the hour
      schedule_expression = "cron(0 * * * ? *)"
      state               = "ENABLED"
      cpu                 = try(local.scheduled_jobs_config[var.environment].cpu, null)
      mem                 = try(local.scheduled_jobs_config[var.environment].mem, null)
      environment_vars    = try(local.scheduled_jobs_config[var.environment].environment_vars, null)
    }
```

Going through each of these fields:
* `task_command` is the command you want to run. Run any of these as flask + the command like above.
* `schedule_expression` is the cron schedule that you want to run at.
* `state` can be `ENABLED` or `DISABLED` - mainly useful if you configure it differently per environment.
* `cpu` / `mem` / `environment_vars` can all be overriden
* `role_override` the role to instead run the ECS task with instead of the default runner

## Task Class

We have a [Task](/api/src/task/task.py) class that we use for defining backend tasks.
While at first glance it might look like it's mirroring some behavior from the `@ecs_background_task`
decorator, the idea is that you might make a script contain several tasks that run in sequence. For example,
you might break that up into tasks that copy, transform, and then process some data in 3 distinct
steps. You can define these as 3 separate task classes within one ECS task script. You
would get the general timing metrics of the whole job, as well as more specific narrow timing metrics.

This class does a few things for you automatically:
* Adds timing metrics to the task class
* Allows you to add metrics which will all automatically be logged at run completion
* Stores a record in our `job_log` table with metrics & success status

From the above example, you can see that you simply need to add a `run_task` implementation
in order for the task class to work. When actually running it, call the `run()` function that
does a lot of the above automation for you.

For metrics, specify all named metrics in a class within the task like the example. Then you
can interact with them by doing `self.increment(self.Metrics.EXAMPLE_COUNT)`. The benefit of putting
metrics into a class like this is that it will initiate all fields to `0` when it runs, so if a metric
isn't hit, it's still recorded.