import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

os.environ["DEBUG"] = "false"

for path in (ROOT_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import Base
from app.models import SensorCounter
from ML import notebook_sensor_optic


class OpticSensorNotebookTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self.original_session_local = notebook_sensor_optic.SessionLocal
        notebook_sensor_optic.SessionLocal = self.session_factory

    def tearDown(self):
        notebook_sensor_optic.SessionLocal = self.original_session_local
        self.engine.dispose()

    def get_count(self):
        session = self.session_factory()
        try:
            counter = (
                session.query(SensorCounter)
                .filter(SensorCounter.sensor_id == notebook_sensor_optic.OPTIC_SENSOR_ID)
                .first()
            )
            return None if not counter else counter.people_count
        finally:
            session.close()

    def test_entrada_increments_counter(self):
        result = notebook_sensor_optic.process_payload({"event": "entrada"})

        self.assertEqual(result, 1)
        self.assertEqual(self.get_count(), 1)

    def test_saida_decrements_counter(self):
        notebook_sensor_optic.process_payload({"event": "entrada"})
        notebook_sensor_optic.process_payload({"event": "entrada"})

        result = notebook_sensor_optic.process_payload({"event": "saida"})

        self.assertEqual(result, 1)
        self.assertEqual(self.get_count(), 1)

    def test_saida_at_zero_stays_zero(self):
        result = notebook_sensor_optic.process_payload({"event": "saida"})

        self.assertEqual(result, 0)
        self.assertEqual(self.get_count(), 0)

    def test_invalid_event_does_not_change_counter(self):
        result = notebook_sensor_optic.process_payload({"event": "parado"})

        self.assertIsNone(result)
        self.assertIsNone(self.get_count())


if __name__ == "__main__":
    unittest.main()
