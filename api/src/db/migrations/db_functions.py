GRANTOR_ORGANIZATION_PATH_SQL = """
CREATE OR REPLACE FUNCTION {schema}.set_organization_path() RETURNS TRIGGER AS $$
DECLARE
    v_parent_path ltree;
BEGIN

    -- If no parent organization, path is just the primary key
    IF NEW.parent_organization_id IS NULL THEN
        NEW.path := (NEW.grantor_organization_id::text)::ltree;
    ELSE -- Otherwise the path is the concatenation of the parents path + the primary key
        SELECT path INTO v_parent_path FROM {schema}.grantor_organization WHERE grantor_organization_id = NEW.parent_organization_id;
        NEW.path := v_parent_path || (NEW.grantor_organization_id::text)::ltree;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_set_organization_path
BEFORE INSERT ON {schema}.grantor_organization
FOR EACH ROW EXECUTE FUNCTION {schema}.set_organization_path();
"""

GRANTOR_ORGANIZATION_UPDATE_PATH_SQL = """
CREATE OR REPLACE FUNCTION {schema}.move_grantor_organization_subtree()
RETURNS TRIGGER AS $$
DECLARE
    v_old_path       LTREE;
    v_new_path       LTREE;
    v_parent_path    LTREE;
BEGIN
    -- If the update didn't change the parent, don't do anything else.
    IF NEW.parent_organization_id IS NOT DISTINCT FROM OLD.parent_organization_id THEN
        RETURN NEW;
    END IF;

    v_old_path := OLD.path;

    -- Verify that we aren't going to add any cycles when updating.
    IF NEW.parent_organization_id IS NOT NULL THEN
        IF EXISTS (
            SELECT 1 FROM {schema}.grantor_organization
            WHERE grantor_organization_id = NEW.parent_organization_id
              AND path <@ v_old_path
        ) THEN
            RAISE EXCEPTION
                'cannot reparent grantor_organization %: new parent % is a descendant of it',
                NEW.grantor_organization_id, NEW.parent_organization_id;
        END IF;
    END IF;

    IF NEW.parent_organization_id IS NULL THEN
        v_new_path := (NEW.grantor_organization_id::text)::ltree;
    ELSE
        SELECT path INTO v_parent_path FROM {schema}.grantor_organization WHERE grantor_organization_id = NEW.parent_organization_id;
        v_new_path := v_parent_path || (NEW.grantor_organization_id::text)::ltree;
    END IF;

    NEW.path := v_new_path;

    UPDATE {schema}.grantor_organization
    SET path = v_new_path || subpath(path, nlevel(v_old_path))
    WHERE path <@ v_old_path
      AND grantor_organization_id <> NEW.grantor_organization_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_move_grantor_organization_subtree
BEFORE UPDATE OF parent_organization_id ON {schema}.grantor_organization
FOR EACH ROW EXECUTE FUNCTION {schema}.move_grantor_organization_subtree();
"""


def get_grantor_organization_insert_automation_sql(schema: str) -> str:
    return GRANTOR_ORGANIZATION_PATH_SQL.format(schema=schema)


def get_grantor_organization_update_automation_sql(schema: str) -> str:
    return GRANTOR_ORGANIZATION_UPDATE_PATH_SQL.format(schema=schema)
