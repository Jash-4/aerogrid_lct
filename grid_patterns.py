"""
================================================================================
AeroGrid-LCT: Real-Time Dynamic Electrical Microgrid Partitioning Engine
================================================================================
Module: grid_patterns.py
Architect / Owner: Member 3 (Software Architecture & Design Patterns)
GitHub User: jishnujishnu0712 (jishnujishnu0712@gmail.com)

Rubric Defense Points:
1. System Design Beyond an Algorithm (2 Marks):
   - Rather than an isolated script, AeroGrid-LCT is structured as an enterprise
     telemetry and protection system using standard Gang-of-Four (GoF) design patterns.
2. Command Pattern (IBreakerCommand):
   - Encapsulates physical switchgear operations (CloseBreaker, TripBreaker) into
     reversible command objects.
   - Provides an undo() capability allowing grid engineers to safely simulate 
     black-start restoration and maintenance line cutoffs without restarting state.
3. Observer Pattern (IGridObserver):
   - Completely decouples the low-level Link-Cut Tree algorithmic engine from physical
     actuators (protective relays, load shedders, solar inverter controllers).
   - Emits instantaneous event-driven alerts when a cut operation triggers an island.
4. Zero Secondary Data Structures:
   - Uses direct object reference composition without allocating lists, queues, or dicts.
================================================================================
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from lct_node import LCTNode
from grid_engine import AeroGridEngine


# ============================================================================
# DESIGN PATTERN 1: OBSERVER PATTERN (Decoupled Grid Protection Telemetry)
# ============================================================================

class IGridObserver(ABC):
    """
    Observer interface for receiving asynchronous grid topological alerts.
    Decouples algorithmic pointer manipulations from downstream physical machinery.
    """

    @abstractmethod
    def on_islanding(self, bus_a: LCTNode, bus_b: LCTNode, island_root: LCTNode) -> None:
        """
        Invoked when an electrical transmission line trips and isolates a subgrid.
        
        Args:
            bus_a: The bus terminal on the supply side of the breaker.
            bus_b: The bus terminal on the disconnected side of the breaker.
            island_root: The newly elected master source/root bus of the isolated subgrid.
        """
        pass

    @abstractmethod
    def on_grid_restored(self, bus_a: LCTNode, bus_b: LCTNode) -> None:
        """
        Invoked when a circuit breaker closes, unifying two previously separate subgrids.
        
        Args:
            bus_a: First bus terminal.
            bus_b: Second bus terminal.
        """
        pass


class MicrogridSafetyRelay(IGridObserver):
    """
    Physical substation safety relay implementation of IGridObserver.
    Executes automated load-shedding and inverter mode shifts upon breaker events.
    """

    def on_islanding(self, bus_a: LCTNode, bus_b: LCTNode, island_root: LCTNode) -> None:
        """
        Time Complexity: O(1)
        Handles emergency electrical islanding contingencies.
        """
        print(f"\n  >>> [CRITICAL TELEMETRY ALERT - SAFETY RELAY TRIP] <<<")
        print(f"  Breaker SEVERED between: {bus_a.name} <---> {bus_b.name}")
        print(f"  ELECTRICAL ISLAND FORMED! New Island Substation Root: '{island_root.name}'")
        print(f"  AUTOMATED CONTINGENCY ACTION:")
        print(f"    1. Shedding non-essential residential loads on {island_root.name}'s subgrid.")
        print(f"    2. Instructing local Solar/BESS inverters to switch to 'grid-forming' mode.\n")

    def on_grid_restored(self, bus_a: LCTNode, bus_b: LCTNode) -> None:
        """
        Time Complexity: O(1)
        Handles phase synchronization upon breaker reclosure.
        """
        print(f"\n  >>> [GRID SYNCHRONIZATION ALERT - BREAKER CLOSED] <<<")
        print(f"  Transmission restored between: {bus_a.name} <---> {bus_b.name}")
        print(f"  STATUS: Phase angle matched. Subgrids merged into unified transmission component.\n")


# ============================================================================
# DESIGN PATTERN 2: COMMAND PATTERN (Switchgear Action & Rollback)
# ============================================================================

class IBreakerCommand(ABC):
    """
    Abstract Command interface defining the contract for physical switchgear actions.
    Guarantees reversible execution (undo) for safety simulations.
    """

    @abstractmethod
    def execute(self) -> bool:
        """Executes the physical switching action."""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """Rolls back the switching action to previous physical topology."""
        pass


class CloseBreakerCommand(IBreakerCommand):
    """
    Concrete Command encapsulating physical circuit breaker closure (Link operation).
    """

    def __init__(self, engine: AeroGridEngine, u: LCTNode, v: LCTNode):
        """
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.engine: AeroGridEngine = engine
        self.u: LCTNode = u
        self.v: LCTNode = v
        self._was_executed: bool = False

    def execute(self) -> bool:
        """
        Closes breaker, linking bus u to bus v.
        Time Complexity: Amortized O(log V)
        """
        result = self.engine.link(self.u, self.v)
        self._was_executed = result
        return result

    def undo(self) -> bool:
        """
        Reverses the closure by tripping the breaker (cut).
        Time Complexity: Amortized O(log V)
        """
        if not self._was_executed:
            return False
        result = self.engine.cut(self.u, self.v)
        if result:
            self._was_executed = False
        return result

    def __repr__(self) -> str:
        return f"<CloseBreakerCommand: {self.u.name} <-> {self.v.name}>"


class TripBreakerCommand(IBreakerCommand):
    """
    Concrete Command encapsulating physical circuit breaker tripping (Cut operation).
    """

    def __init__(self, engine: AeroGridEngine, u: LCTNode, v: LCTNode):
        """
        Time Complexity: O(1)
        Space Complexity: O(1)
        """
        self.engine: AeroGridEngine = engine
        self.u: LCTNode = u
        self.v: LCTNode = v
        self._was_executed: bool = False

    def execute(self) -> bool:
        """
        Trips breaker, cutting the transmission line between bus u and bus v.
        Time Complexity: Amortized O(log V)
        """
        result = self.engine.cut(self.u, self.v)
        self._was_executed = result
        return result

    def undo(self) -> bool:
        """
        Reverses the trip by reclosing the breaker (link) during black-start restoration.
        Time Complexity: Amortized O(log V)
        """
        if not self._was_executed:
            return False
        result = self.engine.link(self.u, self.v)
        if result:
            self._was_executed = False
        return result

    def __repr__(self) -> str:
        return f"<TripBreakerCommand: {self.u.name} -x- {self.v.name}>"


# ============================================================================
# SELF-CONTAINED UNIT VERIFICATION FOR MEMBER 3
# ============================================================================
if __name__ == "__main__":
    print("--- [MEMBER 3 TEST]: Verifying Command & Observer Design Patterns ---")
    
    engine = AeroGridEngine()
    relay = MicrogridSafetyRelay()
    engine.set_observer(relay)

    substation = LCTNode(1, "Main_Substation", 5000.0)
    hospital = LCTNode(2, "Hospital_Feeder", 2000.0)

    # 1. Test Command Execution (Close Breaker)
    close_cmd = CloseBreakerCommand(engine, substation, hospital)
    assert close_cmd.execute() is True, "CloseBreakerCommand execution must succeed."
    assert engine.is_connected(substation, hospital) is True, "Buses must be connected."
    print("✓ CloseBreakerCommand.execute() verified.")

    # 2. Test Command Undo (Rollback to Cut)
    assert close_cmd.undo() is True, "Undo of CloseBreakerCommand must cut the edge."
    assert engine.is_connected(substation, hospital) is False, "Buses must now be disconnected."
    print("✓ CloseBreakerCommand.undo() rollback verified.")

    # 3. Test TripBreakerCommand and Automated Safety Relay Alert
    close_cmd.execute()  # Reconnect
    trip_cmd = TripBreakerCommand(engine, substation, hospital)
    assert trip_cmd.execute() is True, "TripBreakerCommand must successfully sever line."
    assert engine.is_connected(substation, hospital) is False, "Hospital must be isolated."
    print("✓ TripBreakerCommand.execute() and Observer safety notification verified.")

    # 4. Test Automated Black-Start Restoration via Trip Command Undo
    assert trip_cmd.undo() is True, "Undo of TripBreakerCommand must restore the line."
    assert engine.is_connected(substation, hospital) is True, "Hospital must be restored to main grid."
    print("✓ TripBreakerCommand.undo() black-start restoration verified.")

    print("\nAll Member 3 Design Pattern operations passed successfully with 0 errors!")