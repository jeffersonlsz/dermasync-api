"""
Comprehensive domain tests for relato creation.

This file tests the domain decision logic for creating relatos, focusing on:
- Allowed scenarios (valid actor, valid state)
- Denied scenarios (invalid actor, invalid state)
- State transitions
- Effects emitted by decisions

Architectural rules:
- DO NOT mock the domain
- DO NOT test implementation details
- Tests must reflect business rules, not technical details
"""

import pytest
from app.domain.relato.orchestrator import decide
from app.domain.relato.contracts import Actor, CreateRelato, ActorRole
from app.domain.relato.states import RelatoStatus
from app.domain.relato.effects import PersistRelatoEffect, UploadImagesEffect


# =============================================================================
# Helpers
# =============================================================================

def make_create_command(
    relato_id: str = "relato-1",
    owner_id: str = "user-123",
    conteudo: str = "Test relato content",
    image_refs: dict | None = None,
) -> CreateRelato:
    """Helper to create a valid CreateRelato command."""
    if image_refs is None:
        image_refs = {"antes": [], "durante": [], "depois": []}
    
    return CreateRelato(
        relato_id=relato_id,
        owner_id=owner_id,
        conteudo=conteudo,
        image_refs=image_refs,
    )


def make_user_actor(actor_id: str = "user-123") -> Actor:
    """Helper to create a user actor."""
    return Actor(id=actor_id, role=ActorRole.USER)


def make_admin_actor(actor_id: str = "admin-123") -> Actor:
    """Helper to create an admin actor."""
    return Actor(id=actor_id, role=ActorRole.ADMIN)


def make_collaborator_actor(actor_id: str = "colab-123") -> Actor:
    """Helper to create a collaborator actor."""
    return Actor(id=actor_id, role=ActorRole.COLLABORATOR)


# =============================================================================
# Allowed Scenarios
# =============================================================================

class TestCreateRelatoAllowed:
    """Tests for scenarios where relato creation should be allowed."""

    def test_create_relato_allowed_from_none_state(self):
        """
        Business rule: A relato can be created when no prior state exists.
        
        This is the ontological act of bringing a relato into existence.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True
        assert decision.reason is None
        assert decision.previous_state is None
        assert decision.next_state == RelatoStatus.CREATED

    def test_create_relato_allowed_for_user_role(self):
        """
        Business rule: Users can create their own relatos.
        
        Regular users (ActorRole.USER) are allowed to create relatos.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True

    def test_create_relato_allowed_for_admin_role(self):
        """
        Business rule: Admins can create relatos.
        
        Admin users have elevated privileges and can create relatos.
        """
        actor = make_admin_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True

    def test_create_relato_allowed_for_collaborator_role(self):
        """
        Business rule: Collaborators can create relatos.
        
        Collaborators (colaboradores) can create relatos.
        """
        actor = make_collaborator_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True

    def test_create_relato_allowed_with_empty_images(self):
        """
        Business rule: A relato can be created without images.
        
        Images are optional; the core content is the textual narrative.
        """
        actor = make_user_actor()
        command = make_create_command(
            image_refs={"antes": [], "durante": [], "depois": []}
        )

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True
        assert decision.next_state == RelatoStatus.CREATED

    def test_create_relato_allowed_with_images(self):
        """
        Business rule: A relato can be created with images.
        
        Images in any stage (before/during/after) are valid.
        """
        actor = make_user_actor()
        command = make_create_command(
            image_refs={
                "antes": ["img1.jpg", "img2.jpg"],
                "durante": ["img3.jpg"],
                "depois": ["img4.jpg"],
            }
        )

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.allowed is True
        assert decision.next_state == RelatoStatus.CREATED


# =============================================================================
# Denied Scenarios
# =============================================================================

class TestCreateRelatoDenied:
    """Tests for scenarios where relato creation should be denied."""

    def test_create_relato_denied_when_state_is_created(self):
        """
        Business rule: Cannot create a relato that already exists.
        
        Once a relato exists (CREATED state), attempting to create it again
        is an invalid transition.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(
            command=command, 
            actor=actor, 
            current_state=RelatoStatus.CREATED
        )

        assert decision.allowed is False
        assert decision.previous_state == RelatoStatus.CREATED
        assert decision.next_state is None
        assert decision.effects == []
        assert decision.reason is not None

    def test_create_relato_denied_when_state_is_processing(self):
        """
        Business rule: Cannot create a relato that is being processed.
        
        A relato in PROCESSING state already exists; creation is invalid.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(
            command=command,
            actor=actor,
            current_state=RelatoStatus.PROCESSING
        )

        assert decision.allowed is False
        assert decision.previous_state == RelatoStatus.PROCESSING
        assert decision.next_state is None
        assert decision.effects == []

    def test_create_relato_denied_when_state_is_processed(self):
        """
        Business rule: Cannot create a relato that has been processed.
        
        A relato in PROCESSED state already exists; creation is invalid.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(
            command=command,
            actor=actor,
            current_state=RelatoStatus.PROCESSED
        )

        assert decision.allowed is False
        assert decision.effects == []

    @pytest.mark.parametrize(
        "state",
        [
            RelatoStatus.APPROVED_PUBLIC,
            RelatoStatus.REJECTED,
            RelatoStatus.ARCHIVED,
            RelatoStatus.ERROR,
        ],
    )
    def test_create_relato_denied_from_all_existing_states(self, state: RelatoStatus):
        """
        Business rule: Creation is invalid from any existing state.
        
        Once a relato exists in any state, it cannot be "created" again.
        This is a fundamental ontological constraint.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(
            command=command,
            actor=actor,
            current_state=state
        )

        assert decision.allowed is False
        assert decision.previous_state == state
        assert decision.next_state is None
        assert decision.effects == []


# =============================================================================
# Effects Tests
# =============================================================================

class TestCreateRelatoEffects:
    """Tests for effects emitted by create relato decisions."""

    def test_create_relato_emits_persist_effect(self):
        """
        Business rule: Creating a relato must persist it.
        
        The PersistRelatoEffect ensures the relato is stored.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        effect_types = {type(e) for e in decision.effects}
        assert PersistRelatoEffect in effect_types

    def test_create_relato_emits_upload_effect(self):
        """
        Business rule: Creating a relato must handle image uploads.
        
        The UploadImagesEffect ensures images are processed (even if empty).
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        effect_types = {type(e) for e in decision.effects}
        assert UploadImagesEffect in effect_types

    def test_create_relato_effects_contain_relato_id(self):
        """
        Business rule: Effects must reference the relato they belong to.
        
        This ensures traceability and correct execution.
        """
        actor = make_user_actor()
        command = make_create_command(relato_id="test-relato-123")

        decision = decide(command=command, actor=actor, current_state=None)

        for effect in decision.effects:
            assert hasattr(effect, "relato_id")
            assert effect.relato_id == "test-relato-123"

    def test_create_relato_persist_effect_contains_owner(self):
        """
        Business rule: Persist effect must include owner information.
        
        Ownership is critical for access control and provenance.
        """
        actor = make_user_actor(actor_id="owner-456")
        command = make_create_command(owner_id="owner-456")

        decision = decide(command=command, actor=actor, current_state=None)

        persist_effects = [
            e for e in decision.effects 
            if isinstance(e, PersistRelatoEffect)
        ]
        
        assert len(persist_effects) == 1
        assert persist_effects[0].owner_id == "owner-456"

    def test_create_relato_persist_effect_contains_content(self):
        """
        Business rule: Persist effect must include relato content.
        
        The narrative content is the core of the relato.
        """
        actor = make_user_actor()
        command = make_create_command(conteudo="My dermatitis journey...")

        decision = decide(command=command, actor=actor, current_state=None)

        persist_effects = [
            e for e in decision.effects
            if isinstance(e, PersistRelatoEffect)
        ]
        
        assert len(persist_effects) == 1
        assert persist_effects[0].conteudo == "My dermatitis journey..."

    def test_create_relato_persist_effect_contains_status(self):
        """
        Business rule: Persist effect must include the new status.
        
        The status should be CREATED for a new relato.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        persist_effects = [
            e for e in decision.effects
            if isinstance(e, PersistRelatoEffect)
        ]
        
        assert len(persist_effects) == 1
        assert persist_effects[0].status == RelatoStatus.CREATED

    def test_create_relato_upload_effect_contains_image_refs(self):
        """
        Business rule: Upload effect must include image references.
        
        Image refs tell the executor which images to upload.
        """
        actor = make_user_actor()
        command = make_create_command(
            image_refs={
                "antes": ["before1.jpg"],
                "durante": [],
                "depois": ["after1.jpg"],
            }
        )

        decision = decide(command=command, actor=actor, current_state=None)

        upload_effects = [
            e for e in decision.effects
            if isinstance(e, UploadImagesEffect)
        ]
        
        assert len(upload_effects) == 1
        assert upload_effects[0].image_refs["antes"] == ["before1.jpg"]
        assert upload_effects[0].image_refs["depois"] == ["after1.jpg"]

    def test_create_relato_no_effects_when_denied(self):
        """
        Business rule: Denied decisions must not emit effects.
        
        If the domain denies a creation, no side effects should occur.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(
            command=command,
            actor=actor,
            current_state=RelatoStatus.CREATED  # Already exists
        )

        assert decision.allowed is False
        assert decision.effects == []


# =============================================================================
# State Transition Tests
# =============================================================================

class TestCreateRelatoStateTransitions:
    """Tests for state transitions during relato creation."""

    def test_create_relato_transitions_to_created(self):
        """
        Business rule: New relatos start in CREATED state.
        
        CREATED is the initial ontological state of a relato.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.next_state == RelatoStatus.CREATED

    def test_create_relato_previous_state_is_none(self):
        """
        Business rule: Creation has no previous state.
        
        This represents the transition from non-existence to existence.
        """
        actor = make_user_actor()
        command = make_create_command()

        decision = decide(command=command, actor=actor, current_state=None)

        assert decision.previous_state is None
