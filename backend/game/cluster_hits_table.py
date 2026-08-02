from bisect import bisect_left

class ClusterHitsTable:
    """BattleTech Cluster Hits Table (Total Warfare, p.42).

    Rows = 2d6 roll (2-12), columns = cluster size (number of missiles/
    submunitions in the weapon, e.g. LRM-20, SRM-6, etc).
    """

    # cluster_size -> {roll: hits}
    _TABLE: dict[int, dict[int, int]] = {
        2:  {2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 2, 9: 2, 10: 2, 11: 2, 12: 2},
        3:  {2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 3, 11: 3, 12: 3},
        4:  {2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 3, 11: 4, 12: 4},
        5:  {2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 3, 8: 3, 9: 4, 10: 4, 11: 5, 12: 5},
        6:  {2: 2, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 4, 9: 5, 10: 5, 11: 6, 12: 6},
        7:  {2: 2, 3: 2, 4: 3, 5: 4, 6: 4, 7: 4, 8: 4, 9: 6, 10: 6, 11: 7, 12: 7},
        9:  {2: 3, 3: 3, 4: 4, 5: 5, 6: 5, 7: 5, 8: 5, 9: 7, 10: 7, 11: 9, 12: 9},
        10: {2: 3, 3: 3, 4: 4, 5: 6, 6: 6, 7: 6, 8: 6, 9: 8, 10: 8, 11: 10, 12: 10},
        12: {2: 4, 3: 4, 4: 5, 5: 8, 6: 8, 7: 8, 8: 8, 9: 10, 10: 10, 11: 12, 12: 12},
        15: {2: 5, 3: 5, 4: 6, 5: 9, 6: 9, 7: 9, 8: 9, 9: 12, 10: 12, 11: 15, 12: 15},
        20: {2: 6, 3: 6, 4: 9, 5: 12, 6: 12, 7: 12, 8: 12, 9: 16, 10: 16, 11: 20, 12: 20},
        30: {2: 10, 3: 10, 4: 12, 5: 18, 6: 18, 7: 18, 8: 18, 9: 24, 10: 24, 11: 30, 12: 30},
        40: {2: 12, 3: 12, 4: 18, 5: 24, 6: 24, 7: 24, 8: 24, 9: 32, 10: 32, 11: 40, 12: 40},
    }

    _SIZES = sorted(_TABLE.keys())

    @classmethod
    def get_hits(cls, max_cluster_size: int, roll: int) -> int:
        """Return number of hits for a given cluster size and 2d6 roll.

        If ``cluster_size`` doesn't exactly match a table column (e.g. a
        weapon with a non-standard missile count), it rounds UP to the
        next available column, per official rules.
        """
        if not 2 <= roll <= 12:
            raise ValueError(f"roll must be between 2 and 12, got {roll}")

        idx = bisect_left(cls._SIZES, max_cluster_size)
        if idx == len(cls._SIZES):
            # bigger than any column (e.g. 30) -> use largest column
            idx -= 1
        actual_size = cls._SIZES[idx]

        return cls._TABLE[actual_size][roll]
