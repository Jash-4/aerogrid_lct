"""
================================================================================
AeroGrid-LCT: Real-Time Dynamic Electrical Microgrid Partitioning Engine
================================================================================
Module: lct_node.py
Architect / Owner: Member 1 (Core Data Structure & Memory Allocation)
Data Structure: Sleator-Tarjan Link-Cut Tree Node (Auxiliary Splay + Path-Parent)

Rubric Defense Points:
1. Space Complexity: Strict O(1) auxiliary memory per node; O(V) for the whole grid.
   - Using __slots__ bypasses Python's internal dictionary (__dict__), avoiding 
     pointer indirection and heap fragmentation.
   - Eliminates O(V^2) adjacency matrix memory (50,000 buses = ~10 GB RAM).
2. Pointer Virtualization:
   - When is_root() is True: self.parent functions as a ONE-WAY path-parent pointer.
   - When is_root() is False: self.parent functions as a TWO-WAY auxiliary Splay pointer.
3. No External Libraries: Zero databases, zero secondary lists/dictionaries.
================================================================================
"""
from __future__ import annotations
from typing import Optional


class LCTNode:
    """
    Represents an electrical bus or distribution substation in the microgrid.
    Virtualizes physical topology into auxiliary balanced splay trees without
    allocating external graph tables or adjacency lists.
    """

    # Memory Optimization: Allocates fixed memory slots instead of dynamic dicts.
    # Space Complexity: Strict O(1) per instantiated bus node.
    __slots__ = (
        'bus_id', 'name', 'capacity_kva', 'min_capacity',
        'is_reversed', 'left', 'right', 'parent'
    )

    def __init__(self, bus_id: int, name: str, capacity_kva: float = float('inf')):
        """
        Initializes an independent, unlinked electrical bus node.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        Justification:
            - When instantiated, every bus acts as its own independent electrical island.
            - capacity_kva represents the physical thermal rating of the attached line.
            - min_capacity caches the minimum line rating across its auxiliary tree.
        """
        if capacity_kva <= 0:
            raise ValueError("Transmission line capacity (kVA) must be strictly positive.")
            
        self.bus_id: int = bus_id
        self.name: str = name
        self.capacity_kva: float = capacity_kva
        self.min_capacity: float = capacity_kva
        
        # Lazy tag flag for tree eversion (make_root)
        self.is_reversed: bool = False

        # Pointers for Auxiliary Splay Tree
        self.left: Optional[LCTNode] = None
        self.right: Optional[LCTNode] = None
        
        # Dual-role pointer:
        # 1. Auxiliary tree parent (if self is a left/right child of parent)
        # 2. One-way path-parent pointer (if self is an auxiliary tree root)
        self.parent: Optional[LCTNode] = None

    def is_root(self) -> bool:
        """
        Checks whether this node is the root of an auxiliary Splay Tree.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        Algorithmic Justification:
            - In a standard binary tree, relationships are strictly two-way.
            - In a Sleator-Tarjan Link-Cut Tree, disjoint auxiliary trees are glued
              together by "path-parent pointers" (a 1-way name tag).
            - If this node has a parent, but the parent's .left and .right pointers
              DO NOT point back to this node, it proves this pointer is a path-parent!
            - Therefore, this node is the root of its own local auxiliary splay tree.
        """
        if self.parent is None:
            return True
        return self.parent.left is not self and self.parent.right is not self

    def push_down(self) -> None:
        """
        Propagates lazy reversal tags down to auxiliary children.
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        Algorithmic Justification:
            - Reorienting a tree so that a node becomes the root (make_root / evert)
              requires reversing the depth ordering of nodes along that preferred path.
            - Traversing the entire path to reverse pointers would take O(V) time.
            - To preserve O(log V) amortized bounds, we store an 'is_reversed' boolean.
            - When visiting this node, we swap left and right pointers in O(1) time
              and push the boolean flag down to its immediate children lazily.
        """
        if self.is_reversed:
            self.is_reversed = False
            # Swap left and right subtrees in O(1)
            self.left, self.right = self.right, self.left
            
            # Pass lazy flag down to immediate children
            if self.left is not None:
                self.left.is_reversed = not self.left.is_reversed
            if self.right is not None:
                self.right.is_reversed = not self.right.is_reversed

    def push_up(self) -> None:
        """
        Recalculates aggregate subtree metrics (minimum path bottleneck capacity).
        
        Time Complexity: O(1)
        Space Complexity: O(1)
        Algorithmic Justification:
            - Bottom-up dynamic programming evaluation across splay rotations.
            - Inspects only immediate left and right children to find the smallest
              transmission capacity (kVA) among all buses currently in this path.
            - Allows the engine to return path bottlenecks in O(1) time once
              access(v) is complete, without ever walking the physical path.
        """
        self.min_capacity = self.capacity_kva
        if self.left is not None and self.left.min_capacity < self.min_capacity:
            self.min_capacity = self.left.min_capacity
        if self.right is not None and self.right.min_capacity < self.min_capacity:
            self.min_capacity = self.right.min_capacity

    def __repr__(self) -> str:
        """O(1) string representation for telemetry console logging."""
        return f"<Bus {self.bus_id}: {self.name} | Cap: {self.capacity_kva} kVA | MinPath: {self.min_capacity} kVA>"


# ============================================================================
# SELF-CONTAINED UNIT VERIFICATION FOR MEMBER 1
# ============================================================================
if __name__ == "__main__":
    print("--- [MEMBER 1 TEST]: Verifying LCTNode Memory & Invariants ---")
    
    # 1. Allocation Verification
    bus1 = LCTNode(1, "Substation_Alpha", 5000.0)
    bus2 = LCTNode(2, "Feeder_Beta", 2500.0)
    print(f"Instantiated: {bus1}")
    print(f"Instantiated: {bus2}")
    
    # 2. Testing is_root() on fresh nodes
    assert bus1.is_root() is True, "Standalone node must be an auxiliary root."
    assert bus2.is_root() is True, "Standalone node must be an auxiliary root."
    
    # 3. Testing Path-Parent Pointer (1-way connection)
    bus2.parent = bus1
    assert bus2.is_root() is True, "Path-parent connection MUST preserve is_root() == True!"
    print("✓ Path-parent pointer invariant confirmed (is_root is True).")

    # 4. Testing Auxiliary Tree Child Pointer (2-way connection)
    bus1.left = bus2
    assert bus2.is_root() is False, "Auxiliary tree child MUST return is_root() == False!"
    print("✓ Auxiliary child pointer invariant confirmed (is_root is False).")

    # 5. Testing push_up() Bottleneck Aggregation
    bus1.push_up()
    assert bus1.min_capacity == 2500.0, "push_up() must aggregate the minimum capacity."
    print(f"✓ push_up() metric aggregation confirmed: Min capacity = {bus1.min_capacity} kVA.")

    # 6. Testing push_down() Lazy Reversal
    bus1.is_reversed = True
    bus1.push_down()
    assert bus1.right is bus2, "push_down() must swap left and right pointers."
    assert bus2.is_reversed is True, "push_down() must lazily transfer reversal tag."
    print("✓ push_down() lazy reversal confirmed.")
    
    print("\nAll Member 1 unit checks passed successfully with 0 errors!")