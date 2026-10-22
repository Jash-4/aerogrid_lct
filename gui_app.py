"""
================================================================================
AeroGrid-LCT: Real-Time Interactive Microgrid GUI
================================================================================
File: gui_app.py
Description: A Tkinter-based interactive GUI for AeroGrid-LCT.
Zero changes to core logic: directly imports LCTNode, AeroGridEngine,
and Design Pattern commands.
================================================================================
"""
import tkinter as tk
from tkinter import ttk, messagebox
from lct_node import LCTNode
from grid_engine import AeroGridEngine
from grid_patterns import (
    IGridObserver,
    CloseBreakerCommand,
    TripBreakerCommand,
    IBreakerCommand
)


class GUISafetyRelay(IGridObserver):
    """Custom GUI observer to direct telemetry alerts directly to the UI log box."""
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def on_islanding(self, bus_a: LCTNode, bus_b: LCTNode, island_root: LCTNode) -> None:
        msg = (
            f"⚠️ [ISLANDING ALERT] Line severed between '{bus_a.name}' and '{bus_b.name}'!\n"
            f"   -> Electrical island formed around root: '{island_root.name}'\n"
            f"   -> Shedding non-critical loads; inverters switched to grid-forming."
        )
        self.log_callback(msg, alert=True)

    def on_grid_restored(self, bus_a: LCTNode, bus_b: LCTNode) -> None:
        msg = (
            f"✅ [GRID RESTORED] Breaker closed between '{bus_a.name}' and '{bus_b.name}'.\n"
            f"   -> Power synchronism verified. Grids re-unified."
        )
        self.log_callback(msg, alert=False)


class AeroGridGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AeroGrid-LCT | Dynamic Microgrid Topology Engine")
        self.root.geometry("980x720")
        self.root.configure(bg="#1e1e2e")

        # 1. Initialize Engine & Observer
        self.engine = AeroGridEngine()
        self.observer = GUISafetyRelay(self.append_log)
        self.engine.set_observer(self.observer)

        # 2. Instantiate the 5 Microgrid Buses (Pure LCTNodes)
        self.buses = {
            1: LCTNode(1, "Main Substation", 5000.0),
            2: LCTNode(2, "Industrial Feeder", 2500.0),
            3: LCTNode(3, "Solar Park", 1200.0),
            4: LCTNode(4, "Battery BESS", 800.0),
            5: LCTNode(5, "Hospital (Critical)", 1500.0),
        }

        # Positions on Canvas (x, y)
        self.coords = {
            1: (150, 150),  # Substation
            2: (400, 150),  # Feeder
            3: (400, 340),  # Solar
            4: (650, 340),  # Battery
            5: (650, 150),  # Hospital
        }

        # Visual Edge definitions: (u_id, v_id) -> active status (True/False)
        self.active_edges = {
            (1, 2): False,
            (2, 3): False,
            (3, 4): False,
            (2, 5): False,
        }

        self.last_command: IBreakerCommand = None

        self._build_ui()
        self._initialize_default_grid()

    def _build_ui(self):
        # Header Title
        title_frame = tk.Frame(self.root, bg="#1e1e2e")
        title_frame.pack(fill=tk.X, pady=10)
        tk.Label(
            title_frame,
            text="⚡ AeroGrid-LCT In-Memory Topology Visualizer",
            font=("Segoe UI", 16, "bold"),
            fg="#89b4fa",
            bg="#1e1e2e"
        ).pack()
        tk.Label(
            title_frame,
            text="Strictly One Advanced Data Structure: Sleator-Tarjan Link-Cut Tree (Amortized O(log V))",
            font=("Segoe UI", 10, "italic"),
            fg="#a6adc8",
            bg="#1e1e2e"
        ).pack()

        # Main Layout Container
        main_pane = tk.Frame(self.root, bg="#1e1e2e")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Left: Canvas Visualizer
        canvas_frame = tk.LabelFrame(main_pane, text=" Real-Time Grid Canvas ", font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#181825")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.canvas = tk.Canvas(canvas_frame, bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right: Control Panel & Telemetry Logs
        control_frame = tk.Frame(main_pane, bg="#1e1e2e", width=340)
        control_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        # Controls Section
        act_box = tk.LabelFrame(control_frame, text=" Breaker Control & Analytics ", font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#181825")
        act_box.pack(fill=tk.X, pady=(0, 10))

        # Bus Selectors
        sel_frame = tk.Frame(act_box, bg="#181825")
        sel_frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(sel_frame, text="Bus A:", fg="#cdd6f4", bg="#181825").grid(row=0, column=0, sticky="w")
        self.combo_a = ttk.Combobox(sel_frame, values=[f"{bid}: {b.name}" for bid, b in self.buses.items()], state="readonly", width=22)
        self.combo_a.current(0)
        self.combo_a.grid(row=0, column=1, pady=3, padx=5)

        tk.Label(sel_frame, text="Bus B:", fg="#cdd6f4", bg="#181825").grid(row=1, column=0, sticky="w")
        self.combo_b = ttk.Combobox(sel_frame, values=[f"{bid}: {b.name}" for bid, b in self.buses.items()], state="readonly", width=22)
        self.combo_b.current(1)
        self.combo_b.grid(row=1, column=1, pady=3, padx=5)

        # Action Buttons
        btn_grid = tk.Frame(act_box, bg="#181825")
        btn_grid.pack(fill=tk.X, padx=10, pady=5)

        tk.Button(btn_grid, text="⚡ Close Breaker (Link)", bg="#a6e3a1", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.action_link).grid(row=0, column=0, sticky="ew", padx=2, pady=3)
        tk.Button(btn_grid, text="❌ Trip Breaker (Cut)", bg="#f38ba8", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.action_cut).grid(row=0, column=1, sticky="ew", padx=2, pady=3)
        tk.Button(btn_grid, text="🔍 Check Connectivity", bg="#89b4fa", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.action_connectivity).grid(row=1, column=0, sticky="ew", padx=2, pady=3)
        tk.Button(btn_grid, text="📊 Query Bottleneck", bg="#fab387", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.action_bottleneck).grid(row=1, column=1, sticky="ew", padx=2, pady=3)
        tk.Button(btn_grid, text="🔄 Undo Last Breaker Action", bg="#cba6f7", fg="#11111b", font=("Segoe UI", 9, "bold"), command=self.action_undo).grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=6)

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        # Telemetry / Protection Log Box
        log_box = tk.LabelFrame(control_frame, text=" SCADA Telemetry & Protection Log ", font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#181825")
        log_box.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_box, bg="#11111b", fg="#a6adc8", font=("Consolas", 8), wrap=tk.WORD, height=14)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _initialize_default_grid(self):
        """Sets up default initial topology: 1-2, 2-3, 3-4, 2-5"""
        default_pairs = [(1, 2), (2, 3), (3, 4), (2, 5)]
        for u_id, v_id in default_pairs:
            cmd = CloseBreakerCommand(self.engine, self.buses[u_id], self.buses[v_id])
            if cmd.execute():
                self.active_edges[(u_id, v_id)] = True
        self.append_log("Initial microgrid feeder topology energized and connected.")
        self.redraw_grid()

    def _get_selected_ids(self):
        u_id = int(self.combo_a.get().split(":")[0])
        v_id = int(self.combo_b.get().split(":")[0])
        return u_id, v_id

    def action_link(self):
        u_id, v_id = self._get_selected_ids()
        cmd = CloseBreakerCommand(self.engine, self.buses[u_id], self.buses[v_id])
        if cmd.execute():
            self.last_command = cmd
            edge_key = (min(u_id, v_id), max(u_id, v_id))
            self.active_edges[edge_key] = True
            self.append_log(f"Manual Close: Breaker connected between {self.buses[u_id].name} and {self.buses[v_id].name}.")
        else:
            messagebox.showwarning("Connection Blocked", "Operation rejected! Action violates radial tree topology (cycle creation or self-loop).")
        self.redraw_grid()

    def action_cut(self):
        u_id, v_id = self._get_selected_ids()
        cmd = TripBreakerCommand(self.engine, self.buses[u_id], self.buses[v_id])
        if cmd.execute():
            self.last_command = cmd
            edge_key = (min(u_id, v_id), max(u_id, v_id))
            self.active_edges[edge_key] = False
            self.append_log(f"Manual Trip: Breaker opened between {self.buses[u_id].name} and {self.buses[v_id].name}.")
        else:
            messagebox.showwarning("Trip Rejected", "Operation rejected! No direct physical transmission line exists between these two buses.")
        self.redraw_grid()

    def action_connectivity(self):
        u_id, v_id = self._get_selected_ids()
        connected = self.engine.is_connected(self.buses[u_id], self.buses[v_id])
        status = "CONNECTED (Same Island)" if connected else "DISCONNECTED (Separate Islands)"
        color = "#a6e3a1" if connected else "#f38ba8"
        self.append_log(f"Connectivity Check: {self.buses[u_id].name} <---> {self.buses[v_id].name} is {status}.")
        messagebox.showinfo("Connectivity Result", f"Status: {status}\n\nEvaluated dynamically in amortized O(log V) time.")

    def action_bottleneck(self):
        u_id, v_id = self._get_selected_ids()
        cap = self.engine.query_bottleneck(self.buses[u_id], self.buses[v_id])
        self.append_log(f"Path Query: Minimum line capacity between {self.buses[u_id].name} and {self.buses[v_id].name} = {cap} kVA.")
        messagebox.showinfo("Path Bottleneck Result", f"Path Capacity: {cap} kVA\n\n(Weakest transmission line along dynamic path)")

    def action_undo(self):
        if self.last_command is not None:
            if self.last_command.undo():
                self.append_log(f"UNDO Executed: Reversible breaker command successfully rolled back.")
                # Re-sync edge visual statuses
                for (u_id, v_id) in list(self.active_edges.keys()):
                    # Direct check if direct edge is intact
                    self.active_edges[(u_id, v_id)] = self.engine.is_connected(self.buses[u_id], self.buses[v_id])
                self.last_command = None
                self.redraw_grid()
            else:
                messagebox.showerror("Undo Error", "Failed to undo last command.")
        else:
            messagebox.showinfo("Undo", "No previous reversible action available.")

    def append_log(self, text, alert=False):
        tag = "alert" if alert else "normal"
        self.log_text.insert(tk.END, text + "\n\n", tag)
        if alert:
            self.log_text.tag_config("alert", foreground="#f38ba8", font=("Consolas", 8, "bold"))
        else:
            self.log_text.tag_config("normal", foreground="#a6adc8")
        self.log_text.see(tk.END)

    def redraw_grid(self):
        self.canvas.delete("all")

        # 1. Draw Wires (Edges)
        for (u_id, v_id), is_active in self.active_edges.items():
            x1, y1 = self.coords[u_id]
            x2, y2 = self.coords[v_id]
            if is_active:
                self.canvas.create_line(x1, y1, x2, y2, fill="#a6e3a1", width=4)
                # Draw small status dot
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_oval(mx-5, my-5, mx+5, my+5, fill="#a6e3a1", outline="")
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill="#45475a", width=2, dash=(4, 4))
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_oval(mx-5, my-5, mx+5, my+5, fill="#f38ba8", outline="")

        # 2. Draw Buses (Nodes)
        for bid, (x, y) in self.coords.items():
            bus = self.buses[bid]
            root_node = self.engine.find_root(bus)
            is_island_root = (root_node is bus)

            # Outline color: Gold if it is its own island root, blue otherwise
            node_color = "#fab387" if is_island_root else "#89b4fa"

            # Outer glow / circle
            r = 30
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#313244", outline=node_color, width=3)

            # Node label
            self.canvas.create_text(x, y-8, text=f"Bus {bid}", fill="#cdd6f4", font=("Segoe UI", 9, "bold"))
            self.canvas.create_text(x, y+8, text=f"{bus.capacity_kva:.0f} kVA", fill="#a6adc8", font=("Segoe UI", 7))
            self.canvas.create_text(x, y+42, text=bus.name, fill="#cdd6f4", font=("Segoe UI", 8, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = AeroGridGUI(root)
    root.mainloop()