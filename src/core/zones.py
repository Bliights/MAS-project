from __future__ import annotations

import random
from abc import ABC


class Zone(ABC):
    min_radioactivity: float
    max_radioactivity: float

    @classmethod
    def contains(cls, radioactivity: float) -> bool:
        """
        Check whether a given radioactivity value belongs to this zone

        Parameters
        ----------
        radioactivity : float
            The radioactivity value to test

        Returns
        -------
        bool
            True if the value falls within the zone range, False otherwise
        """
        return cls.min_radioactivity <= radioactivity < cls.max_radioactivity

    @classmethod
    def random_radioactivity(cls) -> float:
        """
        Generate a random radioactivity value within the zone range

        Returns
        -------
        float
            A random value sampled uniformly in the zone interval
        """
        return random.uniform(cls.min_radioactivity, cls.max_radioactivity)


class Z1(Zone):
    """
    Low radioactivity zone
    """

    min_radioactivity = 0.0
    max_radioactivity = 0.33


class Z2(Zone):
    """
    Medium radioactivity zone
    """

    min_radioactivity = 0.33
    max_radioactivity = 0.66


class Z3(Zone):
    """
    High radioactivity zone.
    """

    min_radioactivity = 0.66
    max_radioactivity = 1.0


class Zones:
    ALL = [Z1, Z2, Z3]

    @staticmethod
    def get_zone_from_radioactivity(value: float) -> type[Zone] | None:
        """
        Retrieve the zone corresponding to a given radioactivity value

        Parameters
        ----------
        value : float
            The radioactivity value to classify

        Returns
        -------
        type[Zone] | None
            The matching zone class if found, otherwise None
        """
        for zone_cls in Zones.ALL:
            if zone_cls.contains(value):
                return zone_cls
        return None
