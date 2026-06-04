import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

os.environ["DEBUG"] = "false"

for path in (ROOT_DIR, BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.database import Base
from app.models import SensorCounter
from app.routes.sensors import get_optic_sensor_counter


class SensorsApiTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

    def tearDown(self):
        self.engine.dispose()

    def test_get_optic_sensor_counter_defaults_to_zero(self):
        session = self.session_factory()
        try:
            response = get_optic_sensor_counter(session)
        finally:
            session.close()

        self.assertEqual(response.sensor_id, "sensor-2")
        self.assertEqual(response.people_count, 0)

    def test_get_optic_sensor_counter_returns_persisted_count(self):
        session = self.session_factory()
        try:
            session.add(SensorCounter(sensor_id="sensor-2", people_count=7))
            session.commit()
        finally:
            session.close()

        session = self.session_factory()
        try:
            response = get_optic_sensor_counter(session)
        finally:
            session.close()

        self.assertEqual(response.people_count, 7)


if __name__ == "__main__":
    unittest.main()
