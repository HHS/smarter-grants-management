locals {
  # Renaming something in here might make terraform try (and fail) to re-create the buckets.
  # So just assuming you can't ever rename anything in here!
  # (except the environment variables eg. `env_var` those are always safe)
  #
  # s3_buckets[key].paths[index].env_var must:
  #  - Start with the same prefix as it's parent bucket, minus the "BUCKET" suffix
  #  - Include the name of the path in some way, doesn't have to be verbatim
  #  - End with PATH
  #
  # s3_buckets[key].paths[index].path must start with a forward slash
  s3_buckets = {
    # s3_buckets[key].env_var must:
    #  - Start with the same prefix as the object key
    #  - End with BUCKET
    draft-files = {
      env_var = "DRAFT_FILES_BUCKET"
      public  = false
      paths   = []
    }
    file-scan = {
      env_var = "FILE_SCAN_BUCKET"
      public  = false
      paths   = []
    }
  }
}
