"""
Orchestration Bounded Context

This bounded context orchestrates operations between other bounded contexts,
specifically handling cross-context workflows like onboarding, tenant setup,
and other operations that require coordination between IAM and Plans.

Responsibilities:
- Orchestrate user onboarding workflow
- Coordinate tenant setup across contexts
- Handle cross-context business processes
- Maintain consistency between bounded contexts
"""

from .application import *
from .domain import *
from .infrastructure import *
from .presentation import *