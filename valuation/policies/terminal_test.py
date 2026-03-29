from valuation.domain.types import PolicyOutput
from valuation.policies.terminal import ExitMultipleTerminal
from valuation.policies.terminal import GordonTerminal
from valuation.policies.terminal import TerminalParams


class TestGordonTerminal:
  """Tests for GordonTerminal policy."""

  def test_basic_usage(self):
    """Basic terminal growth policy usage."""
    policy = GordonTerminal(g_terminal=0.03)
    result = policy.compute()

    assert isinstance(result, PolicyOutput)
    assert isinstance(result.value, TerminalParams)
    assert result.value.method == 'gordon'
    assert result.value.value == 0.03
    assert result.diag['terminal_method'] == 'gordon'
    assert result.diag['g_terminal'] == 0.03

  def test_default_initialization(self):
    """Default initialization to 3%."""
    policy = GordonTerminal()
    result = policy.compute()

    assert result.value.value == 0.03

  def test_diagnostics_content(self):
    """Verify diagnostic output structure."""
    policy = GordonTerminal(g_terminal=0.025)
    result = policy.compute()

    assert 'terminal_method' in result.diag
    assert 'g_terminal' in result.diag
    assert isinstance(result.diag, dict)

class TestExitMultipleTerminal:
  """Tests for ExitMultipleTerminal policy."""

  def test_basic_usage(self):
    policy = ExitMultipleTerminal(multiple=7.5)
    result = policy.compute()

    assert isinstance(result, PolicyOutput)
    assert isinstance(result.value, TerminalParams)
    assert result.value.method == 'multiple'
    assert result.value.value == 7.5
    assert result.diag['terminal_method'] == 'exit_multiple'
    assert result.diag['exit_multiple'] == 7.5
