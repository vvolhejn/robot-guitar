import pytest

from autoguitar.virtual_string import Envelope


def test_envelope():
    env = Envelope(attack_sec=0.25, decay_halftime_sec=0.75)
    env.pluck(1)
    assert env(0.5) == 0
    assert 0.1 < env(1.1) < 0.9
    assert env(1.25) == pytest.approx(1)
    assert env(2.0) == pytest.approx(0.5)
    assert env(2.75) == pytest.approx(0.25)

    # Let's go back and say we plucked the string at 2s.
    # The attack shouldn't start from 0.
    env.pluck(2)
    assert env(2.0) == pytest.approx(0.5)
    assert 0.1 < env(2.1) < 0.9
    assert env(2.25) == pytest.approx(1.0)
