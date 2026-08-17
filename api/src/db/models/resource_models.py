import uuid
from typing import TYPE_CHECKING

from grants_shared.adapters.db.type_decorators.postgres_type_decorators import LookupColumn
from grants_shared.db.models.base import TimestampMixin
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.lookup_constants import Privilege, ResourceType
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkPrivilege, LkResourceType
from src.db.models.user_models import User

if TYPE_CHECKING:
    # Imported for the relationship annotations below only - the grantor organization
    # models import this module at runtime, so a real import would be circular.
    from src.db.models.grantor_organization_models import GrantorOrganization, Partner, Program

########################
# Core Resource Table
########################


class Resource(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "resource"

    resource_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    resource_type: Mapped[ResourceType] = mapped_column(
        "resource_type_id",
        LookupColumn(LkResourceType),
        ForeignKey(LkResourceType.resource_type_id),
    )

    internal_resource: Mapped[InternalResource | None] = relationship(
        "InternalResource", viewonly=True
    )
    partner: Mapped[Partner | None] = relationship("Partner", viewonly=True)
    grantor_organization: Mapped[GrantorOrganization | None] = relationship(
        "GrantorOrganization", viewonly=True
    )
    program: Mapped[Program | None] = relationship("Program", viewonly=True)

    @property
    def concrete_resource(self) -> AbstractResourceTableMixin:
        """The row in the table that this resource stands for.

        Anything that needs to act on the entity itself - rather than on the resource
        row - goes through here, so callers holding a resource don't each have to map
        the type back to a table themselves.
        """
        concrete_resource: AbstractResourceTableMixin | None

        if self.resource_type == ResourceType.INTERNAL:
            concrete_resource = self.internal_resource
        elif self.resource_type == ResourceType.PARTNER:
            concrete_resource = self.partner
        elif self.resource_type == ResourceType.GRANTOR_ORGANIZATION:
            concrete_resource = self.grantor_organization
        elif self.resource_type == ResourceType.PROGRAM:
            concrete_resource = self.program
        else:
            # A valid resource type that has no table yet - opportunity, today.
            raise ValueError(f"Resource type {self.resource_type} has no table behind it")

        if concrete_resource is None:
            # The resource row and its concrete row are created together, so one
            # without the other means something has gone wrong upstream.
            raise ValueError(
                f"Resource {self.resource_id} has no {self.resource_type} row behind it"
            )

        return concrete_resource


class AbstractResourceTableMixin:
    """
    An abstract mixin that you can add to any resource tables

    To do this, define your table with a primary key pointing
    to the resource table and return that value from the get_resource_id function
    and return a static resource type from get_resource_type.

    NOTE: We don't implement this as an abstract class because
          that uses a metaclass. SQLAlchemy also uses a metaclass,
          and you can't define a class with two metaclasses in
          the hierarchy - so instead make this pseudo-abstract approach.
    """

    def get_resource_id(self) -> uuid.UUID:
        raise NotImplementedError

    def get_resource_type(self) -> ResourceType:
        raise NotImplementedError

    def set_resource(self, resource: Resource) -> None:
        self.resource = resource

    @property
    def resource_name(self) -> str | None:
        """A human-readable name for the resource, when it has one.

        Every resource table names its own column differently (partner_name,
        organization_name, and so on), so this gives callers that only know they have
        a resource one place to ask. Defaults to None rather than raising - a resource
        type without a name is a fine thing to be, and callers surface it as null.
        """
        return None


########################
# Specific Resources
#
# We might want to move some of these in the future
# depending on what we add resource models over time.
########################


class InternalResource(GrantorSchemaTable, TimestampMixin, AbstractResourceTableMixin):
    __tablename__ = "internal_resource"

    internal_resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), primary_key=True, default=uuid.uuid4
    )
    resource: Mapped[Resource] = relationship(
        Resource, single_parent=True, cascade="all, delete-orphan"
    )

    internal_resource_name: Mapped[str]

    def get_resource_id(self) -> uuid.UUID:
        return self.internal_resource_id

    def get_resource_type(self) -> ResourceType:
        return ResourceType.INTERNAL

    @property
    def resource_name(self) -> str | None:
        return self.internal_resource_name


########################
# Role / authZ related tables
########################


class ResourceUser(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "resource_user"

    resource_user_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), index=True
    )
    resource: Mapped[Resource] = relationship(Resource)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id), index=True)
    user: Mapped[User] = relationship(User)

    resource_user_roles: Mapped[list[ResourceUserRole]] = relationship(
        back_populates="resource_user",
        uselist=True,
        cascade="all, delete-orphan",
        lazy="selectin",  # preload roles
    )

    @property
    def roles(self) -> list[Role]:
        return [resource_user_role.role for resource_user_role in self.resource_user_roles]


class Role(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "role"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    role_name: Mapped[str]
    is_core: Mapped[bool] = mapped_column(default=False)

    link_privileges: Mapped[list[LinkRolePrivilege]] = relationship(
        back_populates="role",
        uselist=True,
        cascade="all, delete-orphan",
        lazy="selectin",  # always load the privileges
    )

    link_role_resource_types: Mapped[list[LinkRoleResourceType]] = relationship(
        back_populates="role",
        uselist=True,
        cascade="all, delete-orphan",
        lazy="selectin",  # Preload resource types
    )

    privileges: AssociationProxy[set[Privilege]] = association_proxy(
        "link_privileges",
        "privilege",
        creator=lambda obj: LinkRolePrivilege(privilege=obj),
    )

    resource_types: AssociationProxy[set[ResourceType]] = association_proxy(
        "link_role_resource_types",
        "resource_type",
        creator=lambda obj: LinkRoleResourceType(resource_type=obj),
    )


class ResourceUserRole(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "resource_user_role"

    resource_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(ResourceUser.resource_user_id), primary_key=True
    )
    resource_user: Mapped[ResourceUser] = relationship(ResourceUser)

    role_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Role.role_id), primary_key=True)
    role: Mapped[Role] = relationship(Role, lazy="selectin")  # always preload role


class LinkRolePrivilege(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_role_privilege"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Role.role_id), primary_key=True)
    role: Mapped[Role] = relationship(Role)

    privilege: Mapped[Privilege] = mapped_column(
        "privilege_id",
        LookupColumn(LkPrivilege),
        ForeignKey(LkPrivilege.privilege_id),
        primary_key=True,
    )


class LinkRoleResourceType(GrantorSchemaTable, TimestampMixin):
    __tablename__ = "link_role_resource_type"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(Role.role_id), primary_key=True)
    role: Mapped[Role] = relationship(Role)

    resource_type: Mapped[ResourceType] = mapped_column(
        "resource_type_id",
        LookupColumn(LkResourceType),
        ForeignKey(LkResourceType.resource_type_id),
        primary_key=True,
    )
