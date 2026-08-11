import pytest
from discord_role_sync.models import Role, MemberState
from discord_role_sync.diff import compute_role_diff, compute_member_diff


def test_no_changes_when_identical():
    current = [
        Role(id=1, name="Admin", color=0xFF0000, hoist=True, mentionable=False, permissions=8, position=2),
        Role(id=2, name="Member", color=0, hoist=False, mentionable=True, permissions=1024, position=1),
    ]
    desired = [
        Role(id=1, name="Admin", color=0xFF0000, hoist=True, mentionable=False, permissions=8, position=2),
        Role(id=2, name="Member", color=0, hoist=False, mentionable=True, permissions=1024, position=1),
    ]

    diff = compute_role_diff(current, desired, prune=True)
    assert not diff.to_create
    assert not diff.to_update
    assert not diff.to_delete


def test_detect_new_role():
    current = [
        Role(id=1, name="Admin", color=0xFF0000, hoist=True, mentionable=False, permissions=8, position=1)
    ]
    desired = [
        Role(id=1, name="Admin", color=0xFF0000, hoist=True, mentionable=False, permissions=8, position=2),
        Role(id=None, name="Moderator", color=0x00FF00, hoist=True, mentionable=True, permissions=4, position=1),
    ]

    diff = compute_role_diff(current, desired, prune=False)
    assert len(diff.to_create) == 1
    assert diff.to_create[0].name == "Moderator"
    assert diff.to_create[0].color == 0x00FF00
    assert not diff.to_delete


def test_detect_role_attribute_update():
    current = [
        Role(id=10, name="Dev", color=0x111111, hoist=False, mentionable=False, permissions=0, position=1)
    ]
    desired = [
        Role(id=10, name="Dev", color=0x222222, hoist=True, mentionable=False, permissions=0, position=1)
    ]

    diff = compute_role_diff(current, desired, prune=False)
    assert len(diff.to_update) == 1
    change = diff.to_update[0]
    assert change.role_id == 10
    assert change.changes == {"color": (0x111111, 0x222222), "hoist": (False, True)}


def test_prune_removes_untracked_roles():
    current = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=2),
        Role(id=2, name="Temp", color=0, hoist=False, mentionable=False, permissions=0, position=1),
    ]
    desired = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=1)
    ]

    # without prune, should not delete
    no_prune = compute_role_diff(current, desired, prune=False)
    assert not no_prune.to_delete

    # with prune enabled
    with_prune = compute_role_diff(current, desired, prune=True)
    assert len(with_prune.to_delete) == 1
    assert with_prune.to_delete[0].id == 2


def test_ignore_managed_roles_on_prune():
    # nitro booster or bot integration roles have managed=True
    current = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=2),
        Role(id=99, name="Server Booster", color=0, hoist=False, mentionable=False, permissions=0, position=1, managed=True),
    ]
    desired = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=1)
    ]

    diff = compute_role_diff(current, desired, prune=True)
    assert not diff.to_delete


def test_protected_roles_never_pruned():
    current = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=3),
        Role(id=2, name="@everyone", color=0, hoist=False, mentionable=False, permissions=0, position=0),
        Role(id=3, name="VIP-Donator", color=0, hoist=False, mentionable=False, permissions=0, position=1),
    ]
    desired = [
        Role(id=1, name="Admin", color=0, hoist=False, mentionable=False, permissions=0, position=1)
    ]

    diff = compute_role_diff(current, desired, prune=True, protected_names={"@everyone", "VIP-Donator"})
    # print(f"debug: to_delete = {[r.name for r in diff.to_delete]}")
    assert not diff.to_delete


def test_member_role_diff():
    current_members = [
        MemberState(user_id=100, role_ids={1, 2}),
        MemberState(user_id=200, role_ids={2}),
    ]
    desired_members = [
        MemberState(user_id=100, role_ids={1, 3}),
        MemberState(user_id=200, role_ids={2}),
    ]

    diff = compute_member_diff(current_members, desired_members)
    assert len(diff) == 1
    assert diff[0].user_id == 100
    assert diff[0].roles_to_add == {3}
    assert diff[0].roles_to_remove == {2}


def test_member_diff_ignores_managed_roles():
    # ensure bot doesn't attempt to strip managed roles from users
    current_members = [
        MemberState(user_id=100, role_ids={1, 99}),  # 99 is booster
    ]
    desired_members = [
        MemberState(user_id=100, role_ids={1}),
    ]

    diff = compute_member_diff(current_members, desired_members, managed_role_ids={99})
    assert not diff
