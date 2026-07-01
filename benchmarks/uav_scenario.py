"""
Dynamic Multi-UAV Task Allocation Benchmark
===========================================
A computational simulation of multi-UAV task allocation with:
  - Stochastic task arrivals (Poisson process)
  - Dynamic events (task bursts, UAV failures)
  - 3 objectives: task completion value, response time, energy efficiency

This serves as a realistic engineering benchmark for our TLE framework.
"""
import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass, field


# ============ Data Structures ============
@dataclass
class Task:
    task_id: int
    position: np.ndarray  # 2D
    task_type: str  # 'recon', 'deliver', 'strike'
    value: float
    weight: float  # payload required
    deadline: float  # seconds from arrival
    arrival_time: float
    completed: bool = False
    assigned_uav: Optional[int] = None
    completion_time: Optional[float] = None


@dataclass
class UAV:
    uav_id: int
    position: np.ndarray  # 2D
    base_position: np.ndarray  # home base
    speed: float  # m/s
    battery: float  # 0-100
    payload_capacity: float  # kg
    initial_battery: float = 100.0
    failed: bool = False


# ============ Scenario Configuration ============
@dataclass
class ScenarioConfig:
    n_uavs: int = 8
    area_size: float = 1000.0  # 1000m x 1000m
    simulation_time: float = 600.0  # 10 minutes
    dt: float = 1.0  # 1 second
    task_arrival_rate: float = 0.2  # Poisson lambda
    event_interval: float = 50.0  # dynamic event every 50s
    n_event_tasks: int = 5  # new tasks per event
    uav_failure_prob: float = 0.1  # chance per event
    seed: int = 0


# ============ Scenario Generator ============
def generate_scenario(config: ScenarioConfig) -> Dict[str, Any]:
    """Generate a dynamic multi-UAV scenario."""
    rng = np.random.default_rng(config.seed)
    area = config.area_size

    # Generate UAVs
    uavs = []
    for i in range(config.n_uavs):
        pos = rng.uniform(0, area, 2)
        uavs.append(UAV(
            uav_id=i,
            position=pos.copy(),
            base_position=pos.copy(),
            speed=rng.uniform(10, 20),
            battery=100.0,
            payload_capacity=5.0,
        ))

    # Generate tasks via Poisson process
    tasks = []
    task_id = 0
    t = 0.0
    while t < config.simulation_time:
        t += rng.exponential(1.0 / config.task_arrival_rate)
        if t >= config.simulation_time:
            break
        task_type = rng.choice(['recon', 'deliver', 'strike'],
                               p=[0.5, 0.3, 0.2])
        value = {'recon': 5, 'deliver': 10, 'strike': 20}[task_type]
        weight = {'recon': 2, 'deliver': 5, 'strike': 3}[task_type]
        deadline = rng.uniform(30, 90)
        tasks.append(Task(
            task_id=task_id,
            position=rng.uniform(0, area, 2),
            task_type=task_type,
            value=value,
            weight=weight,
            deadline=deadline,
            arrival_time=t,
        ))
        task_id += 1

    # Generate dynamic events
    events = []
    event_time = config.event_interval
    while event_time < config.simulation_time:
        event_type = rng.choice(['task_burst', 'uav_failure'],
                                p=[0.7, 0.3])
        events.append({"time": event_time, "type": event_type})
        event_time += config.event_interval

    return {
        "uavs": uavs,
        "tasks": tasks,
        "events": events,
        "config": config,
    }


# ============ Simulator ============
class UAVSimulator:
    """Simulates the multi-UAV system given a task assignment."""

    def __init__(self, scenario: Dict[str, Any]):
        self.scenario = scenario
        self.config: ScenarioConfig = scenario["config"]
        # Deep copy state
        self.uavs = [UAV(
            uav_id=u.uav_id, position=u.position.copy(),
            base_position=u.base_position.copy(), speed=u.speed,
            battery=u.battery, payload_capacity=u.payload_capacity,
            initial_battery=u.initial_battery, failed=u.failed
        ) for u in scenario["uavs"]]
        self.tasks = [Task(
            task_id=t.task_id, position=t.position.copy(),
            task_type=t.task_type, value=t.value, weight=t.weight,
            deadline=t.deadline, arrival_time=t.arrival_time,
            completed=t.completed, assigned_uav=t.assigned_uav,
            completion_time=t.completion_time
        ) for t in scenario["tasks"]]
        self.events = scenario["events"]
        # Bookkeeping
        self.completed_tasks = []
        self.failed_tasks = []
        self.uav_travel_log = []

    def assign_and_simulate(self, assignment: np.ndarray = None) -> Dict[str, Any]:
        """
        Apply assignment and run simulation.

        Args:
            assignment: shape (n_uavs, n_tasks) — assignment probability/matrix.
                        For binary: entry (u, t) = 1 if UAV u is assigned task t.
                        If None, use the already-set task.assigned_uav fields.

        Returns:
            metrics dict
        """
        cfg = self.config
        sim_time = cfg.simulation_time
        dt = cfg.dt

        # Reset state
        for u in self.uavs:
            u.battery = u.initial_battery
            u.position = u.base_position.copy()
            u.failed = False
        for t in self.tasks:
            t.completed = False
            t.completion_time = None
        self.completed_tasks = []
        self.failed_tasks = []

        # Apply assignment if provided
        if assignment is not None:
            for t_idx, task in enumerate(self.tasks):
                task.assigned_uav = None
            n_tasks = assignment.shape[1]
            for t_idx in range(min(n_tasks, len(self.tasks))):
                col = assignment[:, t_idx]
                if col.any():
                    u_idx = int(np.argmax(col))
                    if col[u_idx] > 0:
                        self.tasks[t_idx].assigned_uav = u_idx

        # Process events at their times
        event_idx = 0

        # Time-stepped simulation
        t = 0.0
        while t < sim_time:
            # Process events at this time
            while event_idx < len(self.events) and self.events[event_idx]["time"] <= t:
                ev = self.events[event_idx]
                if ev["type"] == "task_burst":
                    self._inject_task_burst(cfg)
                elif ev["type"] == "uav_failure":
                    self._maybe_fail_uav(cfg)
                event_idx += 1

            # For each UAV, move toward assigned tasks
            for ui, uav in enumerate(self.uavs):
                if uav.failed:
                    continue
                # Find tasks assigned to this UAV that are pending
                pending = [task for task in self.tasks
                           if not task.completed
                           and task.assigned_uav == uav.uav_id
                           and task.arrival_time <= t]
                if not pending:
                    # Idle: return to base slowly
                    self._move_toward(uav, uav.base_position, dt)
                    continue
                # Pick the closest task (greedy)
                pending.sort(key=lambda task: np.linalg.norm(task.position - uav.position))
                target = pending[0]
                arrived = self._move_toward(uav, target.position, dt)
                if arrived:
                    # Complete task
                    if (t - target.arrival_time) <= target.deadline and \
                       uav.battery > 0 and uav.payload_capacity >= target.weight:
                        target.completed = True
                        target.completion_time = t
                        self.completed_tasks.append(target)
                    else:
                        self.failed_tasks.append(target)

            t += dt

        # Compute metrics
        return self._compute_metrics()

    def _inject_task_burst(self, cfg: ScenarioConfig):
        """Add new tasks dynamically."""
        rng = np.random.default_rng()
        for _ in range(cfg.n_event_tasks):
            t_type = rng.choice(['recon', 'deliver', 'strike'])
            value = {'recon': 5, 'deliver': 10, 'strike': 20}[t_type]
            weight = {'recon': 2, 'deliver': 5, 'strike': 3}[t_type]
            new_task = Task(
                task_id=len(self.tasks),
                position=rng.uniform(0, cfg.area_size, 2),
                task_type=t_type,
                value=value,
                weight=weight,
                deadline=rng.uniform(30, 90),
                arrival_time=cfg.event_interval,  # treat as arrived at current event
            )
            self.tasks.append(new_task)

    def _maybe_fail_uav(self, cfg: ScenarioConfig):
        rng = np.random.default_rng()
        active = [u for u in self.uavs if not u.failed]
        if active:
            failed = rng.choice(active)
            failed.failed = True

    def _move_toward(self, uav: UAV, target: np.ndarray, dt: float) -> bool:
        """Move UAV toward target. Returns True if arrived."""
        direction = target - uav.position
        dist = np.linalg.norm(direction)
        if dist < 1e-3:
            return True
        step = min(dist, uav.speed * dt)
        uav.position += direction / dist * step
        uav.battery -= step * 0.01  # drain by distance
        return dist <= uav.speed * dt

    def _compute_metrics(self) -> Dict[str, Any]:
        """Compute 3 objective values."""
        # f1: -total completed task value (minimize negative)
        total_value = sum(t.value for t in self.completed_tasks)
        f1 = -total_value  # minimization

        # f2: -average response time (response = completion - arrival)
        if self.completed_tasks:
            response_times = [t.completion_time - t.arrival_time
                              for t in self.completed_tasks if t.completion_time is not None]
            avg_response = np.mean(response_times) if response_times else cfg_max_response
        else:
            avg_response = 600.0
        f2 = -avg_response  # minimization

        # f3: -average remaining battery
        active = [u for u in self.uavs if not u.failed]
        if active:
            avg_battery = np.mean([u.battery for u in active])
        else:
            avg_battery = 0.0
        f3 = -avg_battery  # minimization

        return {
            "f1_value": -f1,  # for reporting
            "f2_response": -f2,
            "f3_battery": -f3,
            "objectives": np.array([f1, f2, f3]),
            "completed_count": len(self.completed_tasks),
            "failed_count": len(self.failed_tasks),
            "completion_rate": len(self.completed_tasks) / max(1, len(self.tasks)),
        }


cfg_max_response = 600.0


# ============ Solution Decoder ============
def decode_chromosome_to_assignment(
    chromosome: np.ndarray,
    n_uavs: int,
    n_tasks: int,
) -> np.ndarray:
    """
    Convert a continuous chromosome into a binary assignment matrix.

    Chromosome layout (n_uavs * n_tasks values):
    - Row 0..n_uavs-1: task priority scores for each UAV
    - We use argmax to assign each task to the UAV with highest score

    Returns: shape (n_uavs, n_tasks), binary
    """
    if chromosome.size == n_uavs * n_tasks:
        scores = chromosome.reshape(n_uavs, n_tasks)
    else:
        # If sizes don't match, use random initialization as fallback
        return np.random.randint(0, 2, (n_uavs, n_tasks))

    assignment = np.zeros((n_uavs, n_tasks), dtype=int)
    # For each task, pick the UAV with highest score
    task_assignments = np.argmax(scores, axis=0)
    for t_idx, u_idx in enumerate(task_assignments):
        assignment[u_idx, t_idx] = 1
    return assignment


def evaluate_uav_solution(
    chromosome: np.ndarray,
    scenario: Dict[str, Any],
) -> np.ndarray:
    """
    Evaluate a candidate solution (chromosome) on the UAV scenario.

    Returns 3-objective fitness array.
    """
    cfg: ScenarioConfig = scenario["config"]
    n_uavs = cfg.n_uavs
    n_tasks = len(scenario["tasks"])

    assignment = decode_chromosome_to_assignment(chromosome, n_uavs, n_tasks)

    # Build task-uav map: for tasks that are not assigned, mark unassigned
    for t_idx, task in enumerate(scenario["tasks"]):
        # Reset
        task.assigned_uav = None
    for t_idx in range(n_tasks):
        assigned_uav = np.argmax(assignment[:, t_idx]) if assignment[:, t_idx].any() else -1
        if assigned_uav >= 0 and assignment[assigned_uav, t_idx] == 1:
            scenario["tasks"][t_idx].assigned_uav = assigned_uav

    sim = UAVSimulator(scenario)
    metrics = sim.assign_and_simulate(assignment)
    return metrics["objectives"]


# ============ Quick test ============
if __name__ == "__main__":
    cfg = ScenarioConfig(seed=42, simulation_time=300.0,
                         n_uavs=4, task_arrival_rate=0.3)
    scenario = generate_scenario(cfg)
    print(f"Generated scenario: {len(scenario['uavs'])} UAVs, "
          f"{len(scenario['tasks'])} tasks, "
          f"{len(scenario['events'])} events")

    # Random chromosome
    n_uavs = cfg.n_uavs
    n_tasks = len(scenario["tasks"])
    chr_size = n_uavs * n_tasks
    chrom = np.random.uniform(0, 1, chr_size)
    obj = evaluate_uav_solution(chrom, scenario)
    print(f"Random solution objectives: {obj}")
    print(f"  - Task value completed: {-obj[0]:.1f}")
    print(f"  - Avg response time: {-obj[1]:.1f}s")
    print(f"  - Avg remaining battery: {-obj[2]:.1f}%")
