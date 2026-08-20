import pytest


def test_create_profile(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    profile = mgr.create_profile(
        user_id="alice",
        name="Alice Smith",
        role="user",
        language="hi-IN",
        tts_voice_gender="female",
        can_shutdown_pc=True,
        email="alice@example.com",
    )
    assert profile["id"] == "alice"
    assert profile["name"] == "Alice Smith"
    assert profile["role"] == "user"
    assert profile["language"] == "hi-IN"
    assert profile["tts_voice_gender"] == "female"
    assert profile["can_shutdown_pc"] is True
    assert profile["can_delete_files"] is False
    assert profile["email"] == "alice@example.com"
    assert profile["created_at"] is not None


def test_create_profile_with_extra(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    profile = mgr.create_profile(
        user_id="bob",
        name="Bob",
        extra={"favorite_color": "blue", "age": 30},
    )
    assert profile["favorite_color"] == "blue"
    assert profile["age"] == 30


def test_get_profile_exists(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(user_id="charlie", name="Charlie")
    p = mgr.get_profile("charlie")
    assert p is not None
    assert p["name"] == "Charlie"


def test_get_profile_missing(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    assert mgr.get_profile("nobody") is None
    default = mgr.get_profile("default")
    assert default is not None
    assert default["name"] == "Guest"


def test_update_profile(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(user_id="dave", name="Dave")
    result = mgr.update_profile("dave", name="David", language="fr-FR", can_delete_files=True)
    assert result is True
    p = mgr.get_profile("dave")
    assert p["name"] == "David"
    assert p["language"] == "fr-FR"
    assert p["can_delete_files"] is True


def test_update_profile_nonexistent(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    assert mgr.update_profile("ghost", name="nope") is False


def test_list_profiles(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(user_id="eve", name="Eve", role="admin")
    mgr.create_profile(user_id="frank", name="Frank", role="user")
    listing = mgr.list_profiles()
    assert isinstance(listing, list)
    ids = {p["id"] for p in listing}
    assert "default" in ids
    assert "eve" in ids
    assert "frank" in ids
    for p in listing:
        assert "id" in p
        assert "name" in p
        assert "role" in p


def test_has_permission_admin_has_all(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(user_id="admin1", name="Super Admin", role="admin")
    assert mgr.has_permission("admin1", "can_shutdown_pc") is True
    assert mgr.has_permission("admin1", "can_delete_files") is True
    assert mgr.has_permission("admin1", "anything_else") is True


def test_has_permission_user_checks_flags(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(
        user_id="gina",
        name="Gina",
        can_shutdown_pc=True,
        can_delete_files=False,
    )
    assert mgr.has_permission("gina", "can_shutdown_pc") is True
    assert mgr.has_permission("gina", "can_delete_files") is False
    assert mgr.has_permission("gina", "nonexistent_flag") is False


def test_has_permission_default_fallback(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    assert mgr.has_permission("nonexistent_user", "can_shutdown_pc") is False


def test_delete_profile(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr.create_profile(user_id="henry", name="Henry")
    assert mgr.get_profile("henry") is not None
    result = mgr.delete_profile("henry")
    assert result is True
    assert mgr.get_profile("henry") is None


def test_delete_profile_cannot_delete_default(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    result = mgr.delete_profile("default")
    assert result is False
    assert mgr.get_profile("default") is not None


def test_delete_profile_nonexistent(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    assert mgr.delete_profile("no_such_user") is False


def test_profiles_persist_after_reload(tmp_profiles_path, tmp_encodings_path):
    from assistant.identity.user_profiles import UserProfileManager
    mgr1 = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    mgr1.create_profile(user_id="ivy", name="Ivy", language="es-ES", email="ivy@ivy.com")
    mgr2 = UserProfileManager(profiles_path=tmp_profiles_path, encodings_path=tmp_encodings_path)
    p = mgr2.get_profile("ivy")
    assert p is not None
    assert p["name"] == "Ivy"
    assert p["language"] == "es-ES"
    assert p["email"] == "ivy@ivy.com"
