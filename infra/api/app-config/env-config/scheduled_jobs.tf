locals {
  # The `task_command` is what you want your scheduled job to run, for example: ["flask", "example-job"].
  # Schedule expression defines the frequency at which the job should run.
  # The syntax for `schedule_expression` is explained in the following documentation:
  # https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-scheduled-rule-pattern.html
  # The `state` is the state of the scheduled job. It can be either "ENABLED" or "DISABLED".

  # Below is the config for overriding the step function defaults. Environments
  # absent from this map take the module defaults; every lookup uses try(), so a
  # missing key is fine.
  #
  # To override, add an entry like:
  #   staging = {
  #     cpu = 1024
  #     mem = 4096
  #     environment_vars = [{ "Name" : "test", "Value" : "test-value" }]
  #   }
  scheduled_jobs_config = {
  }

  scheduled_jobs = {
  }
}
