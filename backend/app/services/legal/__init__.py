# Copyright (C) 2026 Idea To Fact LLC
# SPDX-License-Identifier: AGPL-3.0-only

"""Legal Services Proxy delegating to packages.contract_intelligence."""
import sys
import os

# Ensure packages is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from packages.contract_intelligence.enums import RiskLevel, DetectionMethod, ClauseCategory, ObligationParty
from packages.contract_intelligence.plugin_sdk import CapabilityRegistry, RiskRule, RuleFinding
