"""
AI Simulator - Mock Player Tracking (No OpenCV Required)
Generates simulated player data to test the system
"""

import time
import json
import requests
from datetime import datetime
import random


class AISimulator:
    """Simulate AI player tracking without needing OpenCV/YOLO"""

    def __init__(
        self, backend_url="http://localhost:5000", match_id=1, team_id=1, token=None
    ):
        self.backend_url = backend_url
        self.match_id = match_id
        self.team_id = team_id
        self.token = token

        # Simulate 11 players
        self.players = {}
        for i in range(1, 12):
            self.players[i] = {
                "track_id": i,
                "total_distance": random.uniform(1000, 5000),
                "avg_speed": random.uniform(3, 6),
                "max_speed": random.uniform(6, 10),
                "sprint_count": random.randint(5, 20),
                "high_speed_count": random.randint(10, 40),
                "minutes": 0,
                "performance_score": random.uniform(50, 95),
            }

    def run(self, duration_minutes=120, interval_seconds=60):
        """
        Run simulation

        Args:
            duration_minutes: How long to run (in minutes)
            interval_seconds: How often to send data (seconds)
        """
        print("=" * 50)
        print("AI Player Tracking Simulator")
        print("=" * 50)
        print(f"Backend: {self.backend_url}")
        print(f"Match ID: {self.match_id}")
        print(f"Team ID: {self.team_id}")
        print(f"Sending data every {interval_seconds} seconds")
        print("-" * 50)

        elapsed = 0
        iteration = 0

        while elapsed < duration_minutes * 60:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")
            print(f"Elapsed: {elapsed // 60} min {elapsed % 60} sec")

            # Update player stats (simulate movement)
            for player_id in self.players:
                p = self.players[player_id]
                # Add some random movement
                p["total_distance"] += random.uniform(50, 150)
                p["minutes"] = elapsed / 60.0
                # Random speed changes
                p["avg_speed"] = random.uniform(3, 7)
                p["max_speed"] = max(p["max_speed"], random.uniform(5, 11))
                # Recalculate performance
                p["performance_score"] = min(
                    100,
                    (p["total_distance"] / 100) * 30
                    + (p["avg_speed"] / 6) * 25
                    + (p["sprint_count"] / 10) * 25
                    + (p["max_speed"] / 10) * 20,
                )

            # Send to backend
            self.send_stats()

            # Wait
            if elapsed + interval_seconds < duration_minutes * 60:
                time.sleep(interval_seconds)
                elapsed += interval_seconds
            else:
                break

        print("\n" + "=" * 50)
        print("Simulation complete!")
        print("=" * 50)

    def send_stats(self):
        """Send statistics to backend"""
        # Prepare player data
        players_data = []
        for player_id, p in self.players.items():
            players_data.append(
                {
                    "track_id": p["track_id"],
                    "total_distance": round(p["total_distance"], 2),
                    "avg_speed": round(p["avg_speed"], 2),
                    "max_speed": round(p["max_speed"], 2),
                    "sprint_count": p["sprint_count"],
                    "high_speed_count": p["high_speed_count"],
                    "minutes": round(p["minutes"], 1),
                    "performance_score": round(p["performance_score"], 1),
                }
            )

        # Sort by performance
        players_data.sort(key=lambda x: x["performance_score"], reverse=True)

        # Match stats
        match_stats = {
            "total_players": len(players_data),
            "total_distance": sum(p["total_distance"] for p in players_data),
            "avg_distance": sum(p["total_distance"] for p in players_data)
            / len(players_data),
            "total_sprints": sum(p["sprint_count"] for p in players_data),
            "match_duration_minutes": round(
                players_data[0]["minutes"] if players_data else 0, 1
            ),
        }

        # Prepare request
        data = {
            "match_id": self.match_id,
            "team_id": self.team_id,
            "timestamp": datetime.now().isoformat(),
            "elapsed_minutes": match_stats["match_duration_minutes"],
            "players": players_data,
            "match_stats": match_stats,
            "events": [],
        }

        # Send to backend
        try:
            print(f"Sending stats for {len(players_data)} players...")
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            headers["Content-Type"] = "application/json"
            response = requests.post(
                f"{self.backend_url}/api/ai/stats",
                json=data,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Success: {result.get('message', 'Data sent')}")
                print(
                    f"  Top player: {players_data[0]['track_id']} (score: {players_data[0]['performance_score']:.1f})"
                )
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"  Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"✗ Could not connect to {self.backend_url}")
            print("  Make sure Flask is running!")
        except Exception as e:
            print(f"✗ Error: {e}")


def login_and_get_token(backend_url, username, password):
    """Login and get JWT token"""
    import requests

    resp = requests.post(
        f"{backend_url}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("access_token") or data.get("token")
    else:
        print(f"Login failed: {resp.status_code} - {resp.text}")
        return None


def main():
    """Run the simulator"""
    import sys

    backend_url = "http://localhost:5000"

    # Get credentials from command line or prompt
    if len(sys.argv) >= 3:
        username = sys.argv[1]
        password = sys.argv[2]
    else:
        print("Usage: python simulator.py <username> <password> [match_id] [team_id]")
        print("Example: python simulator.py admin admin123 1 1")
        print("\nOr enter credentials below:")
        username = input("Username: ")
        password = input("Password: ")

    match_id = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
    team_id = int(sys.argv[4]) if len(sys.argv) >= 5 else 1

    # Login to get token
    print(f"Logging in as {username}...")
    token = login_and_get_token(backend_url, username, password)

    if not token:
        print(
            "ERROR: Could not get auth token. Check credentials and make sure Flask is running."
        )
        return

    print("Login successful! Starting simulation...\n")

    simulator = AISimulator(
        backend_url=backend_url, match_id=match_id, team_id=team_id, token=token
    )

    # Run for 5 minutes, sending data every 30 seconds
    # (You can increase these numbers)
    simulator.run(duration_minutes=5, interval_seconds=30)


if __name__ == "__main__":
    main()
