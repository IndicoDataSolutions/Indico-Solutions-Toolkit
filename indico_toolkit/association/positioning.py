from math import sqrt

from indico_toolkit.errors import ToolkitInputError


class Positioning:
    """
    Class to help identify relative positions in a document using bounding box data.

    Positions are expected to contain, at a minimum, the following top-level keys: "bbTop", "bbBot",
    "bbLeft", "bbRight", "page_num".
    """

    def __init__(self):
        pass

    def positioned_above(
        self, above_pos: dict, below_pos: dict, must_be_same_page: bool = True
    ) -> bool:
        """
        Check if the location of one box is above another
        Args:
            above_pos (dict): the position expected to be above
            below_pos (dict): to position expected to be below
            must_be_same_page (bool, optional): required to be on same page. Defaults to True.

        Returns:
            bool: True if above_pos is above below_pos
        """
        if below_pos["page_num"] < above_pos["page_num"]:
            is_above = False
        elif below_pos["page_num"] != above_pos["page_num"] and must_be_same_page:
            is_above = False
        elif self.xaxis_overlap(above_pos, below_pos):
            if (
                below_pos["page_num"] == above_pos["page_num"]
            ) and not self.yaxis_above(above_pos, below_pos):
                is_above = False
            else:
                is_above = True
        else:
            is_above = False
        return is_above

    def positioned_above_overlap(
            self, above_pos: dict, below_pos: dict, min_overlap_percent: float = None
        ) -> bool:
        """
        Check if the location of one box is on the same page and above another and if the lower box's overlap is at least the given percentage.
        Args:
            above_pos (dict): the position expected to be above
            below_pos (dict): the position expected to be below
            min_overlap_percent (float, optional): the minimum amount of overlap needed. Defaults to None.

        Returns:
            bool: True if above_pos is above below_pos and below_pos' amount of overlap is at least min_overlap_percent
        """
        is_above = False
        is_min_overlap = True
        if below_pos["page_num"] != above_pos["page_num"]:
            raise ToolkitInputError(
                "Predictions are not on the same page!"
            )
        if self.xaxis_overlap(above_pos, below_pos) and self.yaxis_above(above_pos, below_pos):
            is_above = True
            horizontal_overlap_distance = abs(max(above_pos["bbLeft"], below_pos["bbLeft"]) - min(above_pos["bbRight"], below_pos["bbRight"]))
            position_width = abs(below_pos["bbLeft"] - below_pos["bbRight"])
            if min_overlap_percent and horizontal_overlap_distance / position_width < min_overlap_percent:
                is_min_overlap = False
        return is_above and is_min_overlap

    def positioned_on_same_level(
        self, pos1: dict, pos2: dict, must_be_same_page: bool = True
    ) -> bool:
        """
        Two box positions are located on the same level/row, i.e. yaxes overlap
        Args:
            pos1 (dict): first position
            pos2 (dict): second position
            must_be_same_page (bool, optional): required to be on same page. Defaults to True.

        Returns:
            bool: True if positions on same level, else False
        """
        if must_be_same_page and not self.on_same_page(pos1, pos2):
            same_level = False
        elif self.yaxis_overlap(pos1, pos2):
            same_level = True
        else:
            same_level = False
        return same_level

    def get_min_distance(
        self, pos1: dict, pos2: dict, page_height: int = None
    ) -> float:
        """
        Get the minimum distance between any two corners of two bounding boxes via the pythagorean formula.
        Args:
            page_height (int, optional): If you want to measure distances across pages, set the OCR page height
                                         otherwise locations on separate pages will raise an exception.
                                         Defaults to None.

        Returns:
            float: minimum distance
        """
        add_page_height = False
        page_difference = abs(pos1["page_num"] - pos2["page_num"])
        if page_difference > 0:
            if not page_height:
                raise ToolkitInputError(
                    "Predictions are not on the same page! Must enter a page height"
                )
            else:
                add_page_height = True
        distances = []
        corners = [
            ("bbRight", "bbTop"),
            ("bbRight", "bbBot"),
            ("bbLeft", "bbTop"),
            ("bbLeft", "bbBot"),
        ]
        for p1 in corners:
            for p2 in corners:
                distance = self._distance_between_points(
                    (pos1[p1[0]], pos1[p1[1]]), (pos2[p2[0]], pos2[p2[1]])
                )
                distances.append(distance)
        min_distance = min(distances)
        if add_page_height:
            min_distance += page_height * page_difference
        return min_distance

    @staticmethod
    def get_vertical_min_distance(
        above_pos: dict, below_pos: dict, page_height: int = None
    ) -> float:
        """
        Get the vertical minimum distance between two bounding boxes
        Args:
            above_pos (dict): the position expected to be above
            below_pos (dict): to position expected to be below
            page_height (int, optional): If you want to measure distances across pages, set the OCR page height
                                         otherwise locations on separate pages will raise an exception.
                                         Defaults to None.

        Returns:
            float: minimum distance
        """
        add_page_height = False
        page_difference = abs(above_pos["page_num"] - below_pos["page_num"])
        if page_difference > 0:
            if not page_height:
                raise ToolkitInputError(
                    "Predictions are not on the same page! Must enter a page height"
                )
            else:
                add_page_height = True
        min_distance = below_pos["bbTop"] - above_pos["bbBot"]

        if add_page_height:
            min_distance += page_height * page_difference
        return min_distance

    @staticmethod
    def get_horizontal_min_distance(pos1: dict, pos2: dict) -> float:
        """
        Get the horizontal minimum distance between two bounding boxes
        Returns:
            float: minimum distance
        """
        page_difference = abs(pos1["page_num"] - pos2["page_num"])
        if page_difference > 0:
            raise ToolkitInputError(
                "Predictions are not on the same page! Must enter a page height"
            )
    
        min_distance_1 = abs(pos1["bbLeft"] - pos2["bbRight"])
        min_distance_2 = abs(pos1["bbRight"] - pos2["bbLeft"])
        return min(min_distance_1, min_distance_2)

    @staticmethod
    def _distance_between_points(point1: tuple, point2: tuple) -> float:
        x = (point1[0] - point2[0]) ** 2
        y = (point1[1] - point2[1]) ** 2
        return sqrt(x + y)

    @staticmethod
    def manhattan_distance_between_points(point1: tuple, point2: tuple) -> float:
        x = abs(point1[0] - point2[0])
        y = abs(point1[1] - point2[1])
        return x + y

    @staticmethod
    def yaxis_overlap(x: dict, y: dict):
        """
        Two locations overlap on the yaxis, i.e. same "row"
        """
        return y["bbBot"] > x["bbTop"] and y["bbTop"] < x["bbBot"]

    @staticmethod
    def xaxis_overlap(x: dict, y: dict):
        return x["bbLeft"] < y["bbRight"] and y["bbLeft"] < x["bbRight"]

    @staticmethod
    def yaxis_above(above_pos: dict, below_pos: dict):
        return above_pos["bbBot"] < below_pos["bbTop"]

    @staticmethod
    def on_same_page(pos1: dict, pos2: dict):
        return pos1["page_num"] == pos2["page_num"]
