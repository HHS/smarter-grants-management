# Overview
This document details how to setup data for various scenarios.


# Local
In almost all cases, if you want to setup data locally, you almost
always want to use our DB factories as they're far more convenient
than interacting with the database directly.

The easiest way to interact with the database is using our `make console`
command which will open a REPL that lets you run our python code directly

Our factories will handle setting up dependent data (ie. foreign keys)
and populating all the various fields in the table.

For example, if you wanted to create an opportunity with a particular
opportunity title, you could do this in the python console:

TODO - replace example
```py
f.UserFactory.create()
# will echo out
MgmtUser(
│   mgmt_user_id=UUID('e4a6dc60-6557-48c7-a22b-f849d1dae6d6'),
│   user_type=<MgmtUserType.STANDARD: 'standard'>,
│   created_at=datetime.datetime(2026, 7, 29, 20, 9, 15, 8312, tzinfo=datetime.timezone.utc),
│   updated_at=datetime.datetime(2026, 7, 29, 20, 9, 15, 8312, tzinfo=datetime.timezone.utc)
)
```

If you want the factories to be able to create a lot of data
in a common pattern, we have a seed script that we can put
common data scenarios into. This script just uses the factories
the same as above.

# Non-local
Our factories only work locally, setting up data elsewhere likely
requires writing SQL directly or taking advantage of one of our backend
processes.
