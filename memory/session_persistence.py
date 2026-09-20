import json
import os
from datetime import datetime, timezone


class SessionPersistence:
    """Handles saving and loading of HUB session state to/from JSON."""

    @staticmethod
    def save_session(state, filepath='hub/session_state.json'):
        """Serialize session state to JSON file."""
        payload = {
            'version': state.get('version', '1.0.0'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': state.get('level', 0),
            'energy': state.get('energy', 0.0),
            'phi': state.get('phi', 0.0),
            'lean_clearance': state.get('lean_clearance', False),
            'tests_passed': state.get('tests_passed', 0),
        }
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        return filepath

    @staticmethod
    def load_session(filepath='hub/session_state.json'):
        """Deserialize session state from JSON file."""
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def detect_previous_session(filepath='hub/session_state.json'):
        """Return True if a previous session file exists."""
        return os.path.exists(filepath)


if __name__ == '__main__':
    # Demo block
    demo_state = {
        'version': '1.0.0',
        'level': 5,
        'energy': 87.5,
        'phi': 1.618,
        'lean_clearance': True,
        'tests_passed': 42,
    }
    path = SessionPersistence.save_session(demo_state)
    print(f"Saved session to: {path}")
    loaded = SessionPersistence.load_session(path)
    print(f"Loaded session: {loaded}")
    print(f"Previous session detected: {SessionPersistence.detect_previous_session(path)}")
